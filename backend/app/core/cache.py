import time
import json
import logging
from typing import Optional, Any, Dict, Tuple

logger = logging.getLogger(__name__)

class DualDriveCacheManager:
    """
    双驱高性能缓存管理器：
    1. 优先尝试连通位于 E 盘的 Redis 本地服务（127.0.0.1:6379, 密码 12345678）；
    2. 若 Redis 离线或异常，则自动无缝降级为进程内高并发 LRU 内存缓存（带 TTL 自动淘汰机制）；
    3. 杜绝因 Redis 故障导致系统或接口不可用，同时保证全局首页与高频数据毫秒级秒开。
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
        self._probe_interval = 10.0  # 每 10 秒自动重连探测一次
        self._local_cache: Dict[str, Tuple[float, str]] = {}  # key -> (expire_at, value)

        self._init_redis()

    def _init_redis(self):
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
            logger.info(f"[DualDriveCache] 成功连通 E 盘本地 Redis 服务 ({self.host}:{self.port})，已激活高速缓存通道。")
        except Exception as e:
            self._is_redis_online = False
            logger.warning(f"[DualDriveCache] Redis 未连接或离线 ({e})，已自动切换至进程内内存高速缓存兜底。")

    def ping(self) -> bool:
        """检查 Redis 是否在线"""
        now = time.time()
        if not self._is_redis_online and (now - self._last_probe_time > self._probe_interval):
            self._last_probe_time = now
            self._init_redis()
        return self._is_redis_online

    def get(self, key: str) -> Optional[str]:
        """优先从 Redis 读取，失败则从内存兜底缓存读取"""
        if self.ping() and self._redis_client:
            try:
                val = self._redis_client.get(key)
                if val is not None:
                    return val
            except Exception as e:
                logger.warning(f"[DualDriveCache] Redis 读取失败: {e}，降级至本地内存")
                self._is_redis_online = False

        # 本地内存兜底
        now = time.time()
        if key in self._local_cache:
            expire_at, val = self._local_cache[key]
            if expire_at > now:
                return val
            else:
                del self._local_cache[key]
        return None

    def set(self, key: str, value: str, expire_seconds: int = 60) -> bool:
        """写入缓存，同时维护 Redis 与本地内存"""
        success = False
        if self.ping() and self._redis_client:
            try:
                self._redis_client.set(key, value, ex=expire_seconds)
                success = True
            except Exception as e:
                logger.warning(f"[DualDriveCache] Redis 写入失败: {e}，降级至本地内存")
                self._is_redis_online = False

        # 本地内存同步维护
        now = time.time()
        self._local_cache[key] = (now + expire_seconds, value)
        # 清理超期内存键
        if len(self._local_cache) > 2000:
            expired_keys = [k for k, (exp, _) in self._local_cache.items() if exp <= now]
            for k in expired_keys:
                self._local_cache.pop(k, None)
        return True

    def get_json(self, key: str) -> Optional[Any]:
        raw = self.get(key)
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return None
        return None

    def set_json(self, key: str, value: Any, expire_seconds: int = 60) -> bool:
        try:
            raw = json.dumps(value, ensure_ascii=False)
            return self.set(key, raw, expire_seconds=expire_seconds)
        except Exception as e:
            logger.error(f"[DualDriveCache] set_json 序列化错误: {e}")
            return False

    def delete(self, key: str) -> bool:
        if self.ping() and self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception:
                pass
        self._local_cache.pop(key, None)
        return True

    def delete_pattern(self, pattern: str) -> int:
        """根据通配符模式清理相关键（如 'home_feed:*'）"""
        count = 0
        if self.ping() and self._redis_client:
            try:
                keys = self._redis_client.keys(pattern)
                if keys:
                    count = self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"[DualDriveCache] Redis 批量删除错误: {e}")

        # 本地匹配删除
        import fnmatch
        local_matched = [k for k in self._local_cache.keys() if fnmatch.fnmatch(k, pattern)]
        for k in local_matched:
            self._local_cache.pop(k, None)
            count += 1
        return count


    def seed_initial_telemetry(self):
        """
        向 Redis 写入系统运行时心跳与命名空间标识，
        确保管理员在 AnotherRedisDesktopManager 等可视化工具中即刻看到活跃状态与拓扑键值。
        """
        try:
            now_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.set_json("cinema:system:status", {
                "service": "CinemaAgent Backend Core",
                "status": "ONLINE",
                "activated_at": now_iso,
                "cache_driver": "Redis 5.0 DualDrive",
                "port": 6379,
                "version": "2.0.0"
            }, expire_seconds=86400 * 7)

            self.set_json("cinema:system:cache_topology", {
                "driver": "REDIS_PRIMARY_WITH_IN_MEMORY_FALLBACK",
                "redis_endpoint": f"{self.host}:{self.port}",
                "is_redis_online": self._is_redis_online,
                "supported_namespaces": [
                    "cinema:system:* (系统健康与配置拓扑)",
                    "cinema:agents:* (九大智能体活跃状态与物理隔离滑动记忆)",
                    "cinema:dramas:* (首页短剧与焦点轮播高频只读缓存)",
                    "cinema:danmakus:* (弹幕热词与防刷限流令牌桶)",
                    "cinema:stream:* (流媒体直链租约与免转码防雪崩缓存)"
                ]
            }, expire_seconds=86400 * 7)

            logger.info("[DualDriveCache] 系统初始拓扑与心跳键已持久化写入 Redis 命名空间。")
        except Exception as e:
            logger.warning(f"[DualDriveCache] 写入初始心跳失败: {e}")


# 全局单例
cache_manager = DualDriveCacheManager()
# 自动初始化写入一次
if cache_manager.ping():
    cache_manager.seed_initial_telemetry()

