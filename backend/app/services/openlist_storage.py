# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/openlist_storage.py
【业务定位】：OpenList 网盘网关客户端适配器（OpenListStorageService）
【前端链路对接】：
  1. 页面来源：
     - frontend/src/views/CreatorStudioView.vue（创作者工作台 -> 云端网盘目录树与资源挑选）
     - frontend/src/views/PlayerView.vue（视频播放器加载高清播放流）
     - frontend/src/views/AdminView.vue（管理后台短剧资源一键扫描同步）
  2. 触发与路由链路：
     - 播放器拉流：PlayerView.vue 请求 GET /api/v1/videos/stream/{episode_id}（进入 stream.py）；
       -> stream.py 调用 openlist_storage.get_stream_url(remote_path) 获取高速直链；
       -> 以 HTTP 302 临时重定向形式将浏览器导向网盘 CDN 高速节点，实现极致秒开与零服务器带宽消耗；
     - 创作者云盘浏览：CreatorStudioView.vue 请求 GET /api/v1/creator/cloud-files（进入 creator.py）；
       -> creator.py 调用 openlist_storage.list_files(path) 获取网盘文件目录结构；
     - 转码上传同步：transcode_service.py 调用 upload_file_from_path() 将切片推入网盘。
【核心功能】：
  1. 自动化会话认证（get_token）：请求 OpenList /api/auth/login 获取鉴权 Token，
     具备过期探测与单例静默自动刷新机制；
  2. 目录树遍历（list_files）：拉取夸克网盘或联通沃家云盘挂载目录下的所有文件切片；
  3. 极速直链解析（get_stream_url）：解析视频文件的原始高速直链，用于播放器 302 加速重定向；
  4. 云端文件上传（upload_file）：通过 /api/fs/put 将本地短剧切片或海报直接推送到网盘；
  5. 路径故障转移（list_files_with_failover）：当默认目录受限或无权时，平滑降级到备选目录。
==============================================================================
"""

import httpx
import logging
from typing import Optional, Dict, Any, Tuple, AsyncIterator
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenListStorageService:
    """
    【OpenList 网盘网关适配服务类】
    基于 OpenList 统一聚合网关，抹平百度网盘、阿里云盘、夸克网盘、联通沃家云盘的底层协议差异，
    对外暴露统一的标准文件列表读取、直链提取与文件上传接口。
    """
    def __init__(self):
        self.base_url = settings.OPENLIST_BASE_URL.rstrip("/")
        self.username = settings.OPENLIST_USERNAME
        self.password = settings.OPENLIST_PASSWORD
        self.mount_path = settings.OPENLIST_MOUNT_PATH.rstrip("/")
        self._cached_token: Optional[str] = None

    async def get_token(self) -> str:
        """
        向 OpenList 网关发起鉴权登录请求并返回会话 Token，具备内存缓存与静默热刷新能力。
        
        【返回值说明】：
        - str: 有效的鉴权令牌字符串（如 "eyJhbGciOiJIUzI1NiIsInR5cCI6..."）。
        """
        if self._cached_token:
            return self._cached_token

        login_url = f"{self.base_url}/api/auth/login"
        payload = {"username": self.username, "password": self.password}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(login_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    self._cached_token = data.get("data", {}).get("token")
                    logger.info("OpenList 鉴权令牌成功获取并写入内存缓存")
                    return self._cached_token
                else:
                    raise RuntimeError(f"OpenList 登录失败: {data.get('message')}")
            else:
                raise RuntimeError(f"OpenList 返回 HTTP 错误码 {resp.status_code}: {resp.text}")

    async def list_files(self, path: Optional[str] = None, per_page: int = 500) -> list:
        """
        遍历并列出指定网盘挂载目录下的所有文件与子文件夹。
        
        【参数大白话详解】：
        - path (Optional[str]): 目标网盘目录路径（例如 "/kuake/红果项目资源目录" 或 "/wopan/视频资源"）。
          若不传，则默认读取 settings.OPENLIST_MOUNT_PATH 挂载根目录。
        - per_page (int, 默认 500): 分页每页拉取数量上限（短剧多集需设置较大值以一次性拉齐所有分集）。
        
        【返回值说明】：
        - list: 包含文件或目录字典的列表，每个元素包含：
          - "name": 文件名（如 "第01集.mp4"）
          - "size": 文件字节大小
          - "is_dir": 是否为文件夹布尔值
          - "modified": 最后修改时间
        """
        target_path = path or self.mount_path
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/list"
        payload = {"path": target_path, "page": 1, "per_page": per_page, "refresh": True}
        headers = {"Authorization": token}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    return data.get("data", {}).get("content") or []
                elif data.get("code") == 401:
                    # Token 过期失效，清空缓存并自动重试一次
                    self._cached_token = None
                    token = await self.get_token()
                    resp = await client.post(url, json=payload, headers={"Authorization": token})
                    return resp.json().get("data", {}).get("content") or []
                else:
                    raise RuntimeError(f"列出 OpenList 文件失败: {data.get('message')}")
            raise RuntimeError(f"OpenList 文件列表接口 HTTP 异常: {resp.status_code}")

    async def get_stream_url(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        解析视频文件在网盘端的原始高速直读链接（Raw Stream URL）。
        
        【前端与后端消费方式】：
        播放器请求 `/api/v1/videos/stream/{episode_id}` 时，后端提取到分集的 `raw_file_path`，
        调用本函数取得直链后，直接返回 `RedirectResponse(url=raw_url, status_code=302)`，
        观众端浏览器直接从网盘 CDN 拉流，播放极致流畅且不占自身服务器任何带宽。
        
        【参数说明】：
        - file_path (str): 目标文件在网盘里的全路径（如 "/wopan/视频资源/ep-12345.mp4"）。
        
        【返回值说明】：
        - Tuple[str, Dict[str, Any]]: 
          - 第 1 个元素为高速可播放的直链 URL（如 "https://...unicom.com/download?token=..."）；
          - 第 2 个元素为文件完整元信息字典（包含 name, size, thumb, hash 等）。
        """
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/get"
        payload = {"path": file_path}
        headers = {"Authorization": token}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    file_info = data.get("data", {})
                    raw_url = file_info.get("raw_url")
                    if not raw_url:
                        raise ValueError(f"OpenList 未返回文件 {file_path} 的有效直链 (raw_url)")
                    return raw_url, file_info
                elif data.get("code") == 401:
                    # 令牌过期，自动重试
                    self._cached_token = None
                    token = await self.get_token()
                    resp = await client.post(url, json=payload, headers={"Authorization": token})
                    file_info = resp.json().get("data", {})
                    return file_info.get("raw_url"), file_info
                else:
                    raise RuntimeError(f"获取文件信息失败: {data.get('message')}")
            raise RuntimeError(f"OpenList 获取文件接口 HTTP 异常: {resp.status_code}")

    async def upload_file(self, remote_path: str, content: bytes) -> bool:
        """
        通过 OpenList 的 `/api/fs/put` 接口将二进制数据直接上传至云盘。
        
        【参数说明】：
        - remote_path (str): 目标上传在云盘中的绝对存储路径（如 "/wopan/视频资源/abc.mp4"）。
        - content (bytes): 文件对应的原始二进制字节数据。
        
        【返回值说明】：
        - bool: True 表示上传并持久化成功。
        """
        import urllib.parse
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/put"
        headers = {
            "Authorization": token,
            "File-Path": urllib.parse.quote(remote_path)
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.put(url, content=content, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    logger.info(f"成功将文件上传至 OpenList 网盘: {remote_path}")
                    return True
                elif data.get("code") == 401:
                    self._cached_token = None
                    token = await self.get_token()
                    headers["Authorization"] = token
                    retry_resp = await client.put(url, content=content, headers=headers)
                    if retry_resp.status_code == 200 and retry_resp.json().get("code") == 200:
                        return True
                    raise RuntimeError(f"OpenList 重试上传失败: {retry_resp.text}")
                else:
                    raise RuntimeError(f"OpenList 上传失败: {data.get('message')}")
            raise RuntimeError(f"OpenList 上传接口返回 HTTP 状态码 {resp.status_code}: {resp.text}")

    async def mkdir(self, path: str) -> bool:
        """
        在云盘中创建新的子文件夹目录。
        
        【参数说明】：
        - path (str): 需要创建的目标文件夹绝对路径（如 "/wopan/视频资源/短剧第一季"）。
        """
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/mkdir"
        payload = {"path": path}
        headers = {"Authorization": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    logger.info(f"OpenList 文件夹创建成功: {path}")
                    return True
                elif data.get("code") == 401:
                    self._cached_token = None
                    token = await self.get_token()
                    headers["Authorization"] = token
                    retry_resp = await client.post(url, json=payload, headers=headers)
                    return retry_resp.json().get("code") == 200
                else:
                    raise RuntimeError(f"OpenList 创建文件夹失败: {data.get('message')}")
            raise RuntimeError(f"OpenList 创建文件夹接口 HTTP 异常: {resp.status_code}")

    async def remove(self, dir_path: str, names: list) -> bool:
        """
        批量删除云盘中指定目录下的文件或子文件夹。
        
        【参数说明】：
        - dir_path (str): 目标所在的父目录路径。
        - names (list): 需要删除的文件或文件夹名称列表（如 ["test.mp4", "temp_dir"]）。
        """
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/remove"
        payload = {"dir": dir_path, "names": names}
        headers = {"Authorization": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("code") == 200
            raise RuntimeError(f"OpenList 删除接口 HTTP 异常: {resp.status_code}")

    async def list_files_with_failover(self, path: Optional[str] = None) -> Tuple[list, str]:
        """
        具备多候选路径故障转移机制的文件列表遍历。
        当优先路径报错（如权限不足或目录不存在）时，按顺序探测候选备选路径，确保前端页面不崩溃。
        
        【返回值说明】：
        - Tuple[list, str]: 第 1 项为成功获取到的文件列表；第 2 项为实际生效的目录路径。
        """
        candidates = []
        if path:
            candidates.append(path)
        candidates.append(self.mount_path)
        fallback_str = getattr(settings, "OPENLIST_FALLBACK_PATHS", "")
        for p in fallback_str.split(","):
            p = p.strip()
            if p and p not in candidates:
                candidates.append(p)

        last_error = None
        for candidate in candidates:
            try:
                files = await self.list_files(candidate)
                return files, candidate
            except Exception as e:
                logger.warning(f"读取 OpenList 路径 '{candidate}' 失败: {e}，正在尝试下一个备选路径...")
                last_error = e
        
        logger.error(f"所有配置的 OpenList 候选路径全部探测失败，最后错误: {last_error}")
        return [], candidates[0] if candidates else "/"

    async def upload_file_from_path(self, remote_path: str, local_file_path: str) -> bool:
        """
        读取服务器本地物理文件并将其完整推送上传至云盘。
        
        【参数说明】：
        - remote_path (str): 目标云盘中的存储路径。
        - local_file_path (str): 本地待上传文件的绝对物理路径。
        """
        with open(local_file_path, "rb") as f:
            content = f.read()
        return await self.upload_file(remote_path, content)


# 全局单例 OpenList 存储服务实例
openlist_storage = OpenListStorageService()
