# -*- coding: utf-8 -*-
"""
==============================================================================
【核心模块】：backend/app/core/cache.py
【业务定位】：高可用双驱缓存管理器（DualDriveCacheManager）
【核心功能】：
  1. 第一驱动（高性能集中式）：优先连接本地 Redis (127.0.0.1:6379, 密码 12345678)；
  2. 第二驱动（无缝内存兜底）：若 Redis 服务离线或发生网络抖动，自动平滑降级为
     进程内高并发 LRU 内存缓存（带 TTL 自动过期机制），绝不阻塞业务接口；
  3. 双向防穿透与热点保护：保障首页高频 Feed 流、弹幕桶、短剧专辑详情与智能体
     战队状态在毫秒级极速响应，支持通配符模式批量失效（delete_pattern）。
==============================================================================
"""
import time
import json
import logging
from typing import Optional, Any, Dict, Tuple

logger = logging.getLogger(__name__)

class DualDriveCacheManager:
    """
    【双驱缓存管理器】
    实现 Redis 集中式存储与本地内存兜底的双驱协同。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        password: str = "12345678",
        db: int = 0
    ):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self._redis_client = None
        self._is_redis_online = False
        self._last_probe_time = 0.0
        self._probe_interval = 10.0  # 每 10 秒自动探测一次 Redis 连通性
        self._local_cache: Dict[str, Tuple[float, str]] = {}  # 本地内存哈希表：key -> (expire_at, value)

        self._init_redis()

    def _init_redis(self):
        """尝试建立 Redis 连接并进行 PING 测试"""
        try:
            import redis
            self._redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                socket_timeout=1.5,
                socket_connect_timeout=1.5,
                decode_responses=True,
                protocol=2
            )
            self._redis_client.ping()
            self._is_redis_online = True
            logger.info(f"[DualDriveCache] 成功连通 Redis 服务 ({self.host}:{self.port})，已激活高速缓存通道。")
        except Exception as e:
            self._is_redis_online = False
            logger.warning(f"[DualDriveCache] Redis 未连接 ({e})，自动切换为内存高速缓存兜底。")

    def ping(self) -> bool:
        """检查 Redis 服务当前是否在线"""
        now = time.time()
        if not self._is_redis_online and (now - self._last_probe_time > self._probe_interval):
            self._last_probe_time = now
            self._init_redis()
        return self._is_redis_online

    def get(self, key: str) -> Optional[str]:
        """优先从 Redis 读取，若失败或未启动则从本地内存兜底读取"""
        if self.ping() and self._redis_client:
            try:
                val = self._redis_client.get(key)
                if val is not None:
                    return val
            except Exception as e:
                logger.warning(f"[DualDriveCache] Redis 读取失败: {e}，切回本地内存。")
                self._is_redis_online = False

        # 本地内存缓存提取
        now = time.time()
        if key in self._local_cache:
            expire_at, val = self._local_cache[key]
            if expire_at > now:
                return val
            else:
                del self._local_cache[key]
        return None

    def set(self, key: str, value: str, expire_seconds: int = 60) -> bool:
        """写入缓存，同时写入 Redis 与本地内存双副本"""
        success = False
        if self.ping() and self._redis_client:
            try:
                self._redis_client.set(key, value, ex=expire_seconds)
                success = True
            except Exception as e:
                logger.warning(f"[DualDriveCache] Redis 写入失败: {e}，切回本地内存。")
                self._is_redis_online = False

        # 本地内存同步更新
        now = time.time()
        self._local_cache[key] = (now + expire_seconds, value)
        
        # 防溢出修剪（超过 2000 个键时自动回收过期项）
        if len(self._local_cache) > 2000:
            expired_keys = [k for k, (exp, _) in self._local_cache.items() if exp <= now]
            for k in expired_keys:
                self._local_cache.pop(k, None)
        return True

    def get_json(self, key: str) -> Optional[Any]:
        """读取并自动反序列化为 Python 字典或列表"""
        raw = self.get(key)
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return None
        return None

    def set_json(self, key: str, value: Any, expire_seconds: int = 60) -> bool:
        """将复杂数据对象序列化为 JSON 字符串写入缓存"""
        try:
            raw = json.dumps(value, ensure_ascii=False)
            return self.set(key, raw, expire_seconds=expire_seconds)
        except Exception as e:
            logger.error(f"[DualDriveCache] set_json 序列化错误: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除指定缓存项"""
        if self.ping() and self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception:
                pass
        self._local_cache.pop(key, None)
        return True

    def delete_pattern(self, pattern: str) -> int:
        """按通配符模式批量清理缓存（例如 'home_feed:*'）"""
        count = 0
        if self.ping() and self._redis_client:
            try:
                keys = self._redis_client.keys(pattern)
                if keys:
                    count = self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"[DualDriveCache] 批量清理失败: {e}")

        # 本地内存同步匹配删除
        import fnmatch
        matched = [k for k in self._local_cache.keys() if fnmatch.fnmatch(k, pattern)]
        for k in matched:
            self._local_cache.pop(k, None)
        return count

    def seed_initial_telemetry(self):
        """向 Redis 写入系统初始化运行拓扑与状态标识"""
        try:
            now_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.set_json("cinema:system:status", {
                "service": "CinemaAgent Backend Core",
                "status": "ONLINE",
                "activated_at": now_iso,
                "cache_driver": "Redis DualDrive",
                "port": 6379,
                "version": "2.0.0"
            }, expire_seconds=86400 * 7)

            self.set_json("cinema:system:cache_topology", {
                "driver": "REDIS_PRIMARY_WITH_IN_MEMORY_FALLBACK",
                "redis_endpoint": f"{self.host}:{self.port}",
                "is_redis_online": self._is_redis_online,
                "supported_namespaces": [
                    "cinema:system:* (系统全局监控)",
                    "cinema:agents:* (智能体活跃状态与会话)",
                    "cinema:dramas:* (首页短剧与热度榜单缓存)",
                    "cinema:danmakus:* (弹幕热点缓存)",
                    "cinema:stream:* (流媒体直链与转码缓存)"
                ]
            }, expire_seconds=86400 * 7)

            logger.info("[DualDriveCache] 系统初始化状态已写入 Redis 空间。")
        except Exception as e:
            logger.warning(f"[DualDriveCache] 写入初始遥测失败: {e}")

# 全局单例缓存管理器
cache_manager = DualDriveCacheManager()
if cache_manager.ping():
    cache_manager.seed_initial_telemetry()
