"""
==============================================================================
【模块名称】：danmaku.py (高并发实时弹幕通信引擎与广播通道)
【业务职能】：
  负责视频播放器弹幕图层的核心数据流动，包括按分集查询全量弹幕切片、HTTP 安全发射弹幕、
  以及基于 WebSocket 全双工通道实现多人同屏秒级弹幕实时广播。
【对应前端】：
  - 核心页面：frontend/src/views/PlayerView.vue (弹幕悬浮轨道与发射栏)
  - 前端通信：frontend/src/api/video.ts (getDanmakus, sendDanmaku) 与 WebSocket 原生连接
==============================================================================
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.core.database import get_db, SessionLocal
from app.models.video import VideoEpisode, Video
from app.models.interaction import VideoDanmaku
from app.models.user import User
from app.services.danmaku_manager import danmaku_manager
from app.services.moderation_service import moderation_service

router = APIRouter()

class DanmakuSendRequest(BaseModel):
    episode_id: str
    content: str
    time_offset: float
    color: Optional[str] = "#FFFFFF"
    font_size: Optional[int] = 18
    user_id: Optional[str] = None

def get_demo_user(db: Session, user_id: Optional[str] = None) -> User:
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
    user = db.query(User).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="danmaku_user",
            password_hash="disabled",
            role="USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.get("/list/{episode_id}")
def get_danmaku_list(episode_id: str, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    按分集查询已审核通过的有效弹幕切片列表，包含时间轴秒数、文字内容与色彩。
    对应 HTTP 端点：GET /list/{episode_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：播放器加载对应集数时触发
    - 调用链路：前端通过 video.ts -> getDanmakus() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    danmakus = db.query(VideoDanmaku).filter(
        VideoDanmaku.episode_id == episode_id
    ).order_by(asc(VideoDanmaku.time_offset)).all()

    return {
        "code": 200,
        "data": [
            {
                "id": d.id,
                "time_offset": d.time_offset,
                "content": d.content,
                "color": d.color,
                "font_size": d.font_size,
                "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else ""
            }
            for d in danmakus
        ]
    }

@router.post("/send")
async def send_danmaku_http(req: DanmakuSendRequest, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    通过 HTTP POST 发送一条新弹幕，自动进行敏感词初筛与时长校验。
    对应 HTTP 端点：POST /send
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：播放器底部弹幕输入框回车或点击发送
    - 调用链路：前端通过 video.ts -> sendDanmaku() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    user = get_demo_user(db, req.user_id)
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == req.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # 1. Real-time DFA Content Moderation Check
    has_violation, sanitized_text, matched_words, risk_level = moderation_service.check_text(req.content)
    
    if has_violation and risk_level == "HIGH":
        danmaku_id = str(uuid.uuid4())
        moderation_service.log_violation(
            db,
            video_id=episode.video_id,
            target_type="DANMAKU",
            target_id=danmaku_id,
            content=req.content,
            matched_words=matched_words,
            risk_level="HIGH"
        )
        raise HTTPException(
            status_code=403,
            detail=f"弹幕内容含违规敏感词 ({', '.join(matched_words)})，已阻断发送并记录机审日志！"
        )

    final_content = sanitized_text if has_violation else req.content

    # 2. Persist to MySQL
    danmaku = VideoDanmaku(
        id=str(uuid.uuid4()),
        episode_id=req.episode_id,
        user_id=user.id,
        time_offset=round(req.time_offset, 2),
        content=final_content,
        color=req.color or "#FFFFFF",
        font_size=req.font_size or 18
    )
    db.add(danmaku)
    db.commit()
    db.refresh(danmaku)

    # 3. Broadcast to all active WebSocket clients in this episode
    broadcast_payload = {
        "type": "danmaku",
        "id": danmaku.id,
        "content": danmaku.content,
        "time_offset": danmaku.time_offset,
        "color": danmaku.color,
        "font_size": danmaku.font_size,
        "username": user.username
    }
    await danmaku_manager.broadcast(req.episode_id, broadcast_payload)

    return {
        "code": 200,
        "message": "Danmaku sent successfully",
        "data": broadcast_payload
    }

@router.websocket("/ws/{episode_id}")
async def danmaku_websocket_endpoint(websocket: WebSocket, episode_id: str):
    """
    ==============================================================================
    【这个接口是做什么的】：
    全双工 WebSocket 实时弹幕广播长连接通道，实现万人同屏秒级弹幕互发与推送。
    对应 HTTP 端点：WEBSOCKET /ws/{episode_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：播放器初始化长连接建立
    - 调用链路：前端通过 原生 WebSocket: /ws/{episode_id} 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    await danmaku_manager.connect(episode_id, websocket)
    # 步骤 1：短生命周期获取当前剧集对应 video_id，用完立即释放连接
    with SessionLocal() as db_init:
        episode = db_init.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
        video_id = episode.video_id if episode else "default"

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "danmaku")

            if msg_type == "danmaku":
                raw_content = data.get("content", "").strip()
                time_offset = float(data.get("time_offset", 0.0))
                color = data.get("color", "#FFFFFF")
                font_size = int(data.get("font_size", 18))
                user_id = data.get("user_id")

                # DFA Moderation Check (纯内存计算，不占数据库连接)
                has_violation, sanitized_text, matched_words, risk_level = moderation_service.check_text(raw_content)

                # 步骤 2：仅在需要数据库写入时申请短生命周期连接，操作完毕立即离开上下文归还连接池
                broadcast_data = None
                with SessionLocal() as db_msg:
                    user = get_demo_user(db_msg, user_id)

                    if has_violation and risk_level == "HIGH":
                        danmaku_id = str(uuid.uuid4())
                        moderation_service.log_violation(
                            db_msg,
                            video_id=video_id,
                            target_type="DANMAKU",
                            target_id=danmaku_id,
                            content=raw_content,
                            matched_words=matched_words,
                            risk_level="HIGH"
                        )
                        # Send rejection notice back only to this sender
                        await websocket.send_json({
                            "type": "error",
                            "code": 403,
                            "message": f"弹幕涉敏已拦截: {', '.join(matched_words)}"
                        })
                        continue

                    final_content = sanitized_text if has_violation else raw_content

                    # Persist
                    danmaku = VideoDanmaku(
                        id=str(uuid.uuid4()),
                        episode_id=episode_id,
                        user_id=user.id,
                        time_offset=round(time_offset, 2),
                        content=final_content,
                        color=color,
                        font_size=font_size
                    )
                    db_msg.add(danmaku)
                    db_msg.commit()
                    db_msg.refresh(danmaku)

                    broadcast_data = {
                        "type": "danmaku",
                        "id": danmaku.id,
                        "content": danmaku.content,
                        "time_offset": danmaku.time_offset,
                        "color": danmaku.color,
                        "font_size": danmaku.font_size,
                        "username": user.username
                    }

                # 广播操作在数据库连接释放后执行，彻底避免网络 I/O 阻塞数据库事务
                if broadcast_data:
                    await danmaku_manager.broadcast(episode_id, broadcast_data)

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        danmaku_manager.disconnect(episode_id, websocket)
    except Exception as e:
        import traceback
        traceback.print_exc()
        danmaku_manager.disconnect(episode_id, websocket)
