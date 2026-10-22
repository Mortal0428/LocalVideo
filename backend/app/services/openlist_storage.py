import httpx
import logging
from typing import Optional, Dict, Any, Tuple, AsyncIterator
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenListStorageService:
    def __init__(self):
        self.base_url = settings.OPENLIST_BASE_URL.rstrip("/")
        self.username = settings.OPENLIST_USERNAME
        self.password = settings.OPENLIST_PASSWORD
        self.mount_path = settings.OPENLIST_MOUNT_PATH.rstrip("/")
        self._cached_token: Optional[str] = None

    async def get_token(self) -> str:
        """Log in to OpenList and return session token, auto-refreshing when needed."""
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
                    logger.info("OpenList authentication token acquired successfully.")
                    return self._cached_token
                else:
                    raise RuntimeError(f"OpenList login failed: {data.get('message')}")
            else:
                raise RuntimeError(f"OpenList returned HTTP {resp.status_code}: {resp.text}")

    async def list_files(self, path: Optional[str] = None, per_page: int = 500) -> list:
        """List files in the mounted China Unicom Cloud Disk folder."""
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
                    # Token expired, clear cache and retry once
                    self._cached_token = None
                    token = await self.get_token()
                    resp = await client.post(url, json=payload, headers={"Authorization": token})
                    return resp.json().get("data", {}).get("content") or []
                else:
                    raise RuntimeError(f"Failed to list OpenList files: {data.get('message')}")
            raise RuntimeError(f"OpenList list HTTP error: {resp.status_code}")

    async def get_stream_url(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Get the direct high-speed raw stream URL for a file in Unicom Cloud Disk."""
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
                        raise ValueError(f"No raw_url returned for file {file_path}")
                    return raw_url, file_info
                elif data.get("code") == 401:
                    self._cached_token = None
                    token = await self.get_token()
                    resp = await client.post(url, json=payload, headers={"Authorization": token})
                    file_info = resp.json().get("data", {})
                    return file_info.get("raw_url"), file_info
                else:
                    raise RuntimeError(f"Failed to get file info: {data.get('message')}")
            raise RuntimeError(f"OpenList get HTTP error: {resp.status_code}")

    async def upload_file(self, remote_path: str, content: bytes) -> bool:
        """Upload raw binary data to China Unicom Cloud Disk via OpenList /api/fs/put."""
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
                    logger.info(f"Successfully uploaded file to OpenList: {remote_path}")
                    return True
                elif data.get("code") == 401:
                    self._cached_token = None
                    token = await self.get_token()
                    headers["Authorization"] = token
                    retry_resp = await client.put(url, content=content, headers=headers)
                    if retry_resp.status_code == 200 and retry_resp.json().get("code") == 200:
                        return True
                    raise RuntimeError(f"OpenList retry upload failed: {retry_resp.text}")
                else:
                    raise RuntimeError(f"OpenList upload error: {data.get('message')}")
            raise RuntimeError(f"OpenList upload HTTP status {resp.status_code}: {resp.text}")

    async def mkdir(self, path: str) -> bool:
        """Create a new folder in cloud disk via OpenList /api/fs/mkdir."""
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/mkdir"
        payload = {"path": path}
        headers = {"Authorization": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    logger.info(f"OpenList mkdir succeeded: {path}")
                    return True
                elif data.get("code") == 401:
                    self._cached_token = None
                    token = await self.get_token()
                    headers["Authorization"] = token
                    retry_resp = await client.post(url, json=payload, headers=headers)
                    return retry_resp.json().get("code") == 200
                else:
                    raise RuntimeError(f"OpenList mkdir error: {data.get('message')}")
            raise RuntimeError(f"OpenList mkdir HTTP error: {resp.status_code}")

    async def remove(self, dir_path: str, names: list) -> bool:
        """Delete files or folders in cloud disk via OpenList /api/fs/remove."""
        token = await self.get_token()
        url = f"{self.base_url}/api/fs/remove"
        payload = {"dir": dir_path, "names": names}
        headers = {"Authorization": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("code") == 200
            raise RuntimeError(f"OpenList remove HTTP error: {resp.status_code}")

    async def list_files_with_failover(self, path: Optional[str] = None) -> Tuple[list, str]:
        """List files in target path or fallback to available cloud storage if 403 occurs."""
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
                logger.warning(f"Failed to list OpenList path '{candidate}': {e}, trying next candidate...")
                last_error = e
        
        # If all fail, return empty list rather than crashing
        logger.error(f"All OpenList paths failed. Last error: {last_error}")
        return [], candidates[0] if candidates else "/"

    async def upload_file_from_path(self, remote_path: str, local_file_path: str) -> bool:
        """Read a local file and upload it to Cloud Disk."""
        with open(local_file_path, "rb") as f:
            content = f.read()
        return await self.upload_file(remote_path, content)

openlist_storage = OpenListStorageService()
