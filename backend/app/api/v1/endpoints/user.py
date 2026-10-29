"""
==============================================================================
【模块名称】：user.py (个人中心主页、观众资产与社交主页端点)
【业务职能】：
  为普通观众和创作者提供个人空间数据支撑，包括个人资料查询与修改、创作者/审核员资格申请、
  历史足迹、点赞短剧、我的评论与删除、以及用户间相互关注与社交主页名片。
【对应前端】：
  - 核心页面：frontend/src/views/UserProfileView.vue (个人空间主页)
  - 顶栏下拉：frontend/src/components/GlobalHeader.vue (用户资料浮层)
  - 前端通信：frontend/src/api/user.ts
==============================================================================
"""
import uuid
import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.user import User
from app.models.video import Video, VideoEpisode
from app.models.interaction import UserWatchHistory, UserLike, UserComment, UserFollow
from app.models.coin import UserCoinWallet
from app.models.notification import UserNotification

logger = logging.getLogger(__name__)

router = APIRouter()

class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="用户昵称")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像地址")
    bio: Optional[str] = Field(None, max_length=255, description="个人简介")

class ApplyCreatorRequest(BaseModel):
    creator_name: Optional[str] = Field(None, max_length=50, description="创作者称呼")
    bio: Optional[str] = Field(None, max_length=255, description="创作方向与规划")

class ApplyReviewerRequest(BaseModel):
    reviewer_name: Optional[str] = Field(None, max_length=50, description="审核员称呼")
    bio: Optional[str] = Field(None, max_length=255, description="审核经验与专业背景")

@router.get("/profile")
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
      个人中心展示当前用户的综合资产、特权与资料面板。
    【从前端哪里调过来的】：
      - 对应前端页面：UserProfileView.vue (个人中心视窗)
      - 对应前端动作：观众点击顶栏头像进入"个人空间"
      - 对应前端通信：frontend/src/api/user.ts 中的 userApi.getProfile()
    【核心执行步骤（大白话）】：
      第 1 步：查 User 表提取用户的昵称、个性签名、VIP 到期时间；
      第 2 步：查 UserCoinWallet 表查出金币余额，查签到表判断今天是否已签过到；
      第 3 步：聚合统计该用户收藏的短剧数、获赞数与关注数，打包成完整的资产卡片数据。
    ==============================================================================
    """
    history_count = db.query(UserWatchHistory).filter(UserWatchHistory.user_id == current_user.id).count()
    likes_count = db.query(UserLike).filter(UserLike.user_id == current_user.id).count()
    following_count = db.query(UserFollow).filter(UserFollow.follower_id == current_user.id).count()
    followers_count = db.query(UserFollow).filter(UserFollow.following_id == current_user.id).count()

    # Creator stats if applicable
    creator_videos_count = 0
    if current_user.is_creator or current_user.role == "CREATOR":
        creator_videos_count = db.query(Video).filter(Video.creator_id == current_user.id).count()

    # User coins and VIP status
    wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == current_user.id).first()
    coins = wallet.balance if wallet else 50
    vip_expire_str = current_user.vip_expire_at.isoformat() if getattr(current_user, "vip_expire_at", None) else None
    is_vip = bool(current_user.vip_expire_at and current_user.vip_expire_at > datetime.utcnow())

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname or current_user.username,
            "avatar_url": current_user.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={current_user.username}",
            "role": current_user.role,
            "coins": coins,
            "vip_expire_at": vip_expire_str,
            "is_vip": is_vip,
            "is_creator": current_user.is_creator,
            "creator_application_status": current_user.creator_application_status or "NONE",
            "creator_bio": current_user.creator_bio or "",
            "is_reviewer": getattr(current_user, "is_reviewer", False),
            "reviewer_application_status": getattr(current_user, "reviewer_application_status", None) or "NONE",
            "reviewer_bio": getattr(current_user, "reviewer_bio", None) or "",
            "status": current_user.status,
            "created_at": current_user.created_at.strftime("%Y-%m-%d %H:%M") if current_user.created_at else "",
            "stats": {
                "history_count": history_count,
                "likes_count": likes_count,
                "creator_videos_count": creator_videos_count,
                "following_count": following_count,
                "followers_count": followers_count
            }
        }
    }

@router.put("/profile")
def update_user_profile(
    req: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [update_user_profile] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /profile
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    if req.nickname is not None and req.nickname.strip():
        user_obj.nickname = req.nickname.strip()
    if req.avatar_url is not None:
        user_obj.avatar_url = req.avatar_url.strip()
    if req.bio is not None:
        user_obj.creator_bio = req.bio.strip()

    db.commit()
    db.refresh(user_obj)
    return {
        "code": 200,
        "message": "个人资料更新成功",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "nickname": user_obj.nickname,
            "avatar_url": user_obj.avatar_url,
            "role": user_obj.role
        }
    }

@router.post("/apply-creator")
def apply_creator_qualification(
    req: ApplyCreatorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [apply_creator_qualification] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /apply-creator
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    user_obj.creator_application_status = "PENDING"
    if req.bio:
        user_obj.creator_bio = req.bio
    if req.creator_name and req.creator_name.strip():
        user_obj.nickname = req.creator_name.strip()

    db.commit()
    db.refresh(user_obj)
    return {
        "code": 200,
        "message": "创作者资质申请已成功提交！请等待管理员在管理中台审核通过。",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "nickname": user_obj.nickname,
            "role": user_obj.role,
            "is_creator": user_obj.is_creator,
            "creator_application_status": user_obj.creator_application_status
        }
    }

@router.post("/apply-reviewer")
def apply_reviewer_qualification(
    req: ApplyReviewerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [apply_reviewer_qualification] 业务，负责合规审核与风控判定相关系统资产与数据状态。
    对应 HTTP 端点：POST /apply-reviewer
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    user_obj.reviewer_application_status = "PENDING"
    if req.bio:
        user_obj.reviewer_bio = req.bio
    if req.reviewer_name and req.reviewer_name.strip():
        user_obj.nickname = req.reviewer_name.strip()

    db.commit()
    db.refresh(user_obj)
    return {
        "code": 200,
        "message": "审核员资质申请已成功提交！请等待管理员在管理中台审核通过。",
        "data": {
            "id": user_obj.id,
            "username": user_obj.username,
            "nickname": user_obj.nickname,
            "role": user_obj.role,
            "is_reviewer": getattr(user_obj, "is_reviewer", False),
            "reviewer_application_status": user_obj.reviewer_application_status
        }
    }

@router.get("/history")
def get_user_watch_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_user_watch_history] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /history
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    histories = (
        db.query(UserWatchHistory)
        .filter(UserWatchHistory.user_id == current_user.id)
        .order_by(desc(UserWatchHistory.updated_at))
        .limit(30)
        .all()
    )

    result = []
    for h in histories:
        ep = db.query(VideoEpisode).filter(VideoEpisode.id == h.last_episode_id).first()
        if not ep:
            continue
        v = db.query(Video).filter(Video.id == ep.video_id).first()
        
        duration = ep.duration_seconds or 120
        progress_pct = min(100, int((h.progress_seconds / duration) * 100)) if duration > 0 else 0

        result.append({
            "history_id": h.id,
            "episode_id": ep.id,
            "video_id": v.id if v else "",
            "drama_title": v.title if v else "微短剧",
            "cover_url": v.cover_url if v else "",
            "episode_num": ep.episode_num,
            "episode_title": ep.title,
            "progress_seconds": h.progress_seconds,
            "duration_seconds": duration,
            "progress_pct": progress_pct,
            "updated_at": h.updated_at.strftime("%Y-%m-%d %H:%M") if h.updated_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": result
    }

@router.get("/likes")
def get_user_likes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_user_likes] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /likes
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    likes = (
        db.query(UserLike)
        .filter(UserLike.user_id == current_user.id)
        .order_by(desc(UserLike.created_at))
        .limit(30)
        .all()
    )

    result = []
    for l in likes:
        v = db.query(Video).filter(Video.id == l.video_id).first()
        if not v:
            continue
        ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).order_by(VideoEpisode.episode_num.asc()).first()
        result.append({
            "like_id": l.id,
            "episode_id": ep.id if ep else "",
            "video_id": v.id,
            "drama_title": v.title,
            "cover_url": v.cover_url or "",
            "episode_num": ep.episode_num if ep else 1,
            "episode_title": ep.title if ep else "第1集",
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": result
    }

@router.get("/comments")
def get_user_comments(
    page: int = 1,
    size: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_user_comments] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /comments
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    offset = max(0, (page - 1) * size)
    comments = (
        db.query(UserComment)
        .filter(UserComment.user_id == current_user.id)
        .order_by(desc(UserComment.created_at))
        .offset(offset)
        .limit(size)
        .all()
    )
    total_count = db.query(UserComment).filter(UserComment.user_id == current_user.id).count()

    result = []
    for c in comments:
        v = db.query(Video).filter(Video.id == c.video_id).first()
        first_ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == c.video_id).order_by(VideoEpisode.episode_num.asc()).first()
        reply_to_name = None
        if c.reply_to_user_id:
            ru = db.query(User).filter(User.id == c.reply_to_user_id).first()
            if ru:
                reply_to_name = ru.nickname or ru.username

        result.append({
            "comment_id": c.id,
            "video_id": c.video_id,
            "episode_id": first_ep.id if first_ep else "",
            "drama_title": v.title if v else "已下架短剧",
            "cover_url": v.cover_url if v else "",
            "content": c.content,
            "like_count": c.like_count or 0,
            "is_reply": bool(c.root_id or c.parent_id),
            "reply_to_user_name": reply_to_name,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total_count,
            "page": page,
            "size": size,
            "items": result
        }
    }

@router.delete("/comments/{comment_id}")
def delete_user_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [delete_user_comment] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /comments/{comment_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    comment = db.query(UserComment).filter(UserComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在或已被删除")

    if current_user.role != "ADMIN" and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除非本人发表的评论")

    # If this is a root comment, also cascade delete its nested replies
    if not comment.root_id and not comment.parent_id:
        db.query(UserComment).filter(UserComment.root_id == comment.id).delete()

    db.delete(comment)
    db.commit()

    return {
        "code": 200,
        "message": "评论已成功删除",
        "data": {"comment_id": comment_id}
    }

@router.post("/follow/{target_user_id}")
def toggle_user_follow(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [toggle_user_follow] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /follow/{target_user_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    existing = db.query(UserFollow).filter(
        UserFollow.follower_id == current_user.id,
        UserFollow.following_id == target_user_id
    ).first()

    if existing:
        db.delete(existing)
        is_following = False
        msg = f"已取消关注 @{target_user.nickname or target_user.username}"
    else:
        new_follow = UserFollow(
            id=str(uuid.uuid4()),
            follower_id=current_user.id,
            following_id=target_user_id
        )
        db.add(new_follow)
        is_following = True
        msg = f"已成功关注 @{target_user.nickname or target_user.username}"

        # Send in-app notification to the target user
        notif = UserNotification(
            id=str(uuid.uuid4()),
            user_id=target_user_id,
            sender_id=current_user.id,
            category="FOLLOW",
            title="新粉丝关注",
            content=f"用户 @{current_user.nickname or current_user.username} 关注了您"
        )
        db.add(notif)

    db.commit()

    followers_count = db.query(UserFollow).filter(UserFollow.following_id == target_user_id).count()

    return {
        "code": 200,
        "message": msg,
        "data": {
            "target_user_id": target_user_id,
            "is_following": is_following,
            "followers_count": followers_count
        }
    }

@router.get("/follow-status/{target_user_id}")
def get_user_follow_status(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_user_follow_status] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /follow-status/{target_user_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    is_following = bool(
        db.query(UserFollow).filter(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == target_user_id
        ).first()
    )
    followers_count = db.query(UserFollow).filter(UserFollow.following_id == target_user_id).count()
    following_count = db.query(UserFollow).filter(UserFollow.follower_id == target_user_id).count()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "target_user_id": target_user_id,
            "is_following": is_following,
            "followers_count": followers_count,
            "following_count": following_count
        }
    }

@router.get("/followings")
def get_my_followings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_my_followings] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /followings
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    follow_records = (
        db.query(UserFollow, User)
        .join(User, UserFollow.following_id == User.id)
        .filter(UserFollow.follower_id == current_user.id)
        .order_by(desc(UserFollow.created_at))
        .all()
    )

    items = []
    for f, u in follow_records:
        items.append({
            "follow_id": f.id,
            "user_id": u.id,
            "username": u.username,
            "nickname": u.nickname or u.username,
            "avatar_url": u.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={u.username}",
            "role": u.role,
            "bio": u.creator_bio or "",
            "followed_at": f.created_at.strftime("%Y-%m-%d %H:%M") if f.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": len(items),
            "items": items
        }
    }


@router.get("/followers")
def get_my_followers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_my_followers] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /followers
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    follow_records = (
        db.query(UserFollow, User)
        .join(User, UserFollow.follower_id == User.id)
        .filter(UserFollow.following_id == current_user.id)
        .order_by(desc(UserFollow.created_at))
        .all()
    )

    # Check which followers the current user also follows back
    following_ids = {
        r[0] for r in db.query(UserFollow.following_id).filter(UserFollow.follower_id == current_user.id).all()
    }

    items = []
    for f, u in follow_records:
        items.append({
            "follow_id": f.id,
            "user_id": u.id,
            "username": u.username,
            "nickname": u.nickname or u.username,
            "avatar_url": u.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={u.username}",
            "role": u.role,
            "is_following_back": u.id in following_ids,
            "followed_at": f.created_at.strftime("%Y-%m-%d %H:%M") if f.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": len(items),
            "items": items
        }
    }


@router.get("/public-card/{target_user_id}")
def get_user_public_card(
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [user] 模块中的 [get_user_public_card] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /public-card/{target_user_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/user.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    following_count = db.query(UserFollow).filter(UserFollow.follower_id == target.id).count()
    followers_count = db.query(UserFollow).filter(UserFollow.following_id == target.id).count()
    creator_videos_count = db.query(Video).filter(Video.creator_id == target.id).count()

    is_following = False
    if current_user:
        is_following = db.query(UserFollow).filter(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == target.id
        ).first() is not None

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": target.id,
            "username": target.username,
            "nickname": target.nickname or target.username,
            "avatar_url": target.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={target.username}",
            "role": target.role,
            "bio": target.creator_bio or "这位剧迷很神秘，暂无个人简介~",
            "following_count": following_count,
            "followers_count": followers_count,
            "creator_videos_count": creator_videos_count,
            "is_following": is_following,
            "is_self": bool(current_user and current_user.id == target.id)
        }
    }


