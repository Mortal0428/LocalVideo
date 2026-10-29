"""
==============================================================================
【模块名称】：notifications.py (全能毛玻璃通知天窗与用户消息中心)
【业务职能】：
  处理用户的所有消息提醒，包括系统全员公告、评论被回复、点赞被触发三分类通知，
  支持查询未读红点计数、单条已读标记以及一键全部已读。
【对应前端】：
  - 核心页面：frontend/src/components/NotificationSkylight.vue (顶栏毛玻璃通知抽屉)
  - 顶栏挂载：frontend/src/components/GlobalHeader.vue (小铃铛红点徽标)
  - 前端通信：frontend/src/api/user.ts
==============================================================================
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.notification import UserNotification

router = APIRouter()

class MarkReadAllRequest(BaseModel):
    category: Optional[str] = None

@router.get("")
@router.get("/")
def list_user_notifications(
    category: Optional[str] = Query(None, description="分类过滤: ANNOUNCEMENT, REPLY, LIKE, MENTION"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    分页拉取当前用户的通知消息，支持按全部、系统公告、回复我的、收到的赞进行分类筛选。
    对应 HTTP 端点：GET 
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：点击顶栏小铃铛展开通知天窗
    - 调用链路：前端通过 user.ts -> listUserNotifications() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    query = db.query(UserNotification).filter(UserNotification.user_id == current_user.id)
    if category and category.strip():
        cat_upper = category.strip().upper()
        if cat_upper in ("REPLY", "REPLY_AND_MENTION"):
            # 聚合评论回复与@提及互动流
            query = query.filter(UserNotification.category.in_(["REPLY", "MENTION"]))
        else:
            query = query.filter(UserNotification.category == cat_upper)

    total = query.count()
    items = query.order_by(desc(UserNotification.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": [
                {
                    "id": n.id,
                    "category": n.category,
                    "title": n.title,
                    "content": n.content,
                    "sender_id": n.sender_id,
                    "sender_name": n.sender.nickname or n.sender.username if n.sender else "系统",
                    "sender_avatar": n.sender.avatar_url if n.sender else "",
                    "video_id": n.video_id,
                    "episode_id": n.episode_id,
                    "comment_id": n.comment_id,
                    "announcement_id": n.announcement_id,
                    "is_read": n.is_read,
                    "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else ""
                }
                for n in items
            ]
        }
    }

@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    统计当前用户各分类下的未读消息总数，驱动顶栏小铃铛红点徽标。
    对应 HTTP 端点：GET /unread-count
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：页面载入后全局轮询或路由跳转时更新
    - 调用链路：前端通过 user.ts -> getUnreadNotificationCount() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    base_query = db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id,
        UserNotification.is_read == False
    )

    total = base_query.count()
    announcements = base_query.filter(UserNotification.category == "ANNOUNCEMENT").count()
    # replies 计数包含直接回复与 @ 提及
    replies = base_query.filter(UserNotification.category.in_(["REPLY", "MENTION"])).count()
    likes = base_query.filter(UserNotification.category == "LIKE").count()
    mentions = base_query.filter(UserNotification.category == "MENTION").count()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "announcements": announcements,
            "replies": replies,
            "likes": likes,
            "mentions": mentions
        }
    }

@router.post("/{notification_id}/read")
def mark_single_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    将单条通知标记为已读状态，实时消除对应的红点计数。
    对应 HTTP 端点：POST /{notification_id}/read
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：在通知天窗中点击单条通知
    - 调用链路：前端通过 user.ts -> markNotificationRead() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    item = db.query(UserNotification).filter(
        UserNotification.id == notification_id,
        UserNotification.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")

    item.is_read = True
    db.commit()

    return {
        "code": 200,
        "message": "已标记为已读",
        "data": {"id": item.id, "is_read": True}
    }

@router.post("/read-all")
def mark_all_read(
    req: Optional[MarkReadAllRequest] = None,
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    一键将当前用户的所有未读通知标记为全部已读。
    对应 HTTP 端点：POST /read-all
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：通知天窗右上角点击全部已读按钮
    - 调用链路：前端通过 user.ts -> markAllNotificationsRead() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    target_category = category or (req.category if req else None)

    query = db.query(UserNotification).filter(
        UserNotification.user_id == current_user.id,
        UserNotification.is_read == False
    )
    if target_category and target_category.strip():
        cat_upper = target_category.strip().upper()
        if cat_upper in ("REPLY", "REPLY_AND_MENTION"):
            query = query.filter(UserNotification.category.in_(["REPLY", "MENTION"]))
        else:
            query = query.filter(UserNotification.category == cat_upper)

    unread_items = query.all()
    count = len(unread_items)
    for item in unread_items:
        item.is_read = True

    db.commit()

    return {
        "code": 200,
        "message": "全部已读成功",
        "data": {
            "updated_count": count
        }
    }
