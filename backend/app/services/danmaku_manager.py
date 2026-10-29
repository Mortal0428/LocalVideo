# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/danmaku_manager.py
【业务定位】：全双工 WebSocket 实时弹幕连接管理器与广播引擎（ConnectionManager）
【前端链路对接】：
  1. 页面来源：frontend/src/views/PlayerView.vue（视频播放器主页面）
  2. 建立长连接：
     - 观众打开视频播放器 -> 触发 mounted 钩子；
     - 建立 WebSocket：new WebSocket(`${wsBaseUrl}/api/v1/danmaku/ws/${episode_id}`)；
     - 后端路由：backend/app/api/endpoints/danmaku.py -> @router.websocket('/ws/{episode_id}')；
     - 路由调用 danmaku_manager.connect(episode_id, websocket) 将连接加入当前分集的在线房间集合；
  3. 发送与同屏广播：
     - 观众在弹幕输入框敲入文字点击【发送】 -> 通过 WebSocket 发送 JSON 或调用 HTTP 发送接口；
     - 后端经过敏感词过滤后，调用 danmaku_manager.broadcast(episode_id, message)；
     - 同一分集房间下的所有在线观众 WebSocket 几乎同时收到消息，播放器在对应秒数将弹幕从右向左平滑飘过屏幕！
【核心功能】：
  1. 按视频分集（episode_id）对 WebSocket 客户端连接进行分组隔离与房间维护；
  2. 客户端建立连接时（connect）：自动接受握手并将连接加入该集活跃集合；
  3. 客户端断开连接时（disconnect）：将连接从集合安全移除，若该集已无人观看则清理键名；
  4. 毫秒级同屏广播（broadcast）：向同一分集下的所有在线观众并发推送 JSON 数据包，自动剔除死连接。
==============================================================================
"""

import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    【弹幕长连接管理引擎】
    基于内存哈希表维护全局 WebSocket 会话，实现房间化分集广播。
    """
    def __init__(self):
        # 键为 episode_id (分集UUID)，值为该集下所有在线客户端的 WebSocket 对象集合 Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, episode_id: str, websocket: WebSocket):
        """
        新观众进入播放器页面，建立 WebSocket 弹幕信道。
        
        【参数大白话详解】：
        - episode_id (str): 分集主键 UUID，代表当前观众进的是哪个分集的播放房间。
        - websocket (WebSocket): FastAPI 原生长连接对象句柄。
        
        【执行步骤】：
          第 1 步：调用 websocket.accept() 完成 HTTP 协议升级为 WebSocket 握手；
          第 2 步：如果该 episode_id 还没有在线房间，为其初始化一个空 set 集合；
          第 3 步：把当前客户端的 websocket 句柄加入集合，记录日志。
        """
        await websocket.accept()
        if episode_id not in self.active_connections:
            self.active_connections[episode_id] = set()
        self.active_connections[episode_id].add(websocket)
        logger.info(f"WebSocket 客户端已连接到分集 {episode_id} 房间，当前在线客户端总数: {len(self.active_connections[episode_id])}")

    def disconnect(self, episode_id: str, websocket: WebSocket):
        """
        观众退出播放器、关闭浏览器标签页或网络断开。
        
        【参数说明】：
        - episode_id (str): 分集主键 ID。
        - websocket (WebSocket): 待注销断开的客户端连接句柄。
        
        【执行步骤】：
          第 1 步：从对应分集的连接集合中安全移除（discard）该 websocket 句柄；
          第 2 步：如果移除后该分集已经没有其他在线观众，则把该 episode_id 从字典中释放，释放服务器内存。
        """
        if episode_id in self.active_connections:
            self.active_connections[episode_id].discard(websocket)
            if not self.active_connections[episode_id]:
                del self.active_connections[episode_id]
        logger.info(f"WebSocket 客户端已离开分集 {episode_id} 房间。")

    async def broadcast(self, episode_id: str, message: dict):
        """
        同屏弹幕实时群发广播。
        
        【参数大白话详解】：
        - episode_id (str): 目标分集 ID，仅群发给同一集短剧的观众房间，互不串台干扰。
        - message (dict): 推送给所有客户端的弹幕 JSON 数据包。
          【字典结构大白话说明】：
          {
              "id": str,          # 弹幕唯一记录 UUID
              "text": str,        # 弹幕正文内容（如 "前方高能！"、"男主太帅了"）
              "time": float,      # 弹幕绑定的视频播放进度秒数（如 45.2），播放器据此在第 45.2 秒飘过屏幕
              "color": str,       # 弹幕颜色十六进制值（如 "#FFFFFF" 白色，"#FF4D4F" 醒目红）
              "user_id": str,     # 发送者用户 ID
              "user_name": str,   # 发送者昵称
              "created_at": str   # 发送时间字符串
          }
          
        【执行步骤】：
          第 1 步：检查该分集是否有任何在线观众，若没有直接返回；
          第 2 步：遍历该房间内的所有客户端连接，调用 send_json 逐一并发推送新弹幕；
          第 3 步：若某客户端因网络断开导致发送失败，记录为死连接（dead_connections）；
          第 4 步：遍历结束后，批量断开清理死连接，防止内存泄漏和无效重试。
        """
        if episode_id not in self.active_connections:
            return

        dead_connections = set()
        for connection in list(self.active_connections[episode_id]):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"向弹幕客户端广播失败，标记为死连接清除: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self.disconnect(episode_id, dead)


# 全局单例弹幕连接管理器
danmaku_manager = ConnectionManager()
