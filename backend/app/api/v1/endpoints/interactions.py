import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.api.deps import get_optional_user, get_current_user
from app.models.video import Video, VideoEpisode
from app.models.interaction import VideoDanmaku, UserLike, UserComment, UserWatchHistory, CommentLike
from app.models.user import User
from app.models.coin import UserCoinWallet, UserCoinTransaction, VideoCoinTip
from app.models.notification import UserNotification

router = APIRouter()

# --- Pydantic Schemas ---
class HeartbeatRequest(BaseModel):
    progress_seconds: float
    user_id: Optional[str] = None

class LikeRequest(BaseModel):
    user_id: Optional[str] = None

class CommentCreateRequest(BaseModel):
    content: str
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    reply_to_user_id: Optional[str] = None
    user_id: Optional[str] = None

class TipVideoRequest(BaseModel):
    coin_amount: int = Field(..., ge=1, le=2, description="投币数量 (1 或 2)")
    user_id: Optional[str] = None

def get_or_create_default_user(db: Session, user_id: Optional[str] = None) -> User:
    """Helper to ensure a valid user entity exists for interaction operations."""
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
            
    # Default active demo user
    user = db.query(User).filter(User.username == "demo_viewer").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            username="demo_viewer",
            password_hash="disabled",
            role="USER",
            avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=demo_viewer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def resolve_user(db: Session, opt_user: Optional[User], explicit_user_id: Optional[str]) -> User:
    if opt_user:
        return opt_user
    return get_or_create_default_user(db, explicit_user_id)

def recalculate_heat_score(db: Session, video: Video) -> float:
    danmaku_count = (
        db.query(VideoDanmaku)
        .join(VideoEpisode, VideoDanmaku.episode_id == VideoEpisode.id)
        .filter(VideoEpisode.video_id == video.id)
        .count()
    )
    coin_count = getattr(video, "coin_count", 0) or 0
    like_count = video.like_count or 0
    view_count = video.view_count or 0

    score = round(view_count * 1.0 + like_count * 5.0 + coin_count * 10.0 + danmaku_count * 2.0, 2)
    video.heat_score = score
    return score

@router.get("/album/{video_id}")
def get_video_album(
    video_id: str = "latest",
    opt_user: Optional[User] = Depends(get_optional_user),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Fetch video album details along with all episodes and user like status."""
    if video_id == "latest":
        video = db.query(Video).order_by(desc(Video.created_at)).first()
    else:
        video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video album not found")

    episodes = db.query(VideoEpisode).filter(VideoEpisode.video_id == video.id).order_by(VideoEpisode.episode_num.asc()).all()

    # Determine user like status
    effective_user_id = opt_user.id if opt_user else user_id
    is_liked = False
    if effective_user_id:
        existing_like = db.query(UserLike).filter(
            UserLike.user_id == effective_user_id,
            UserLike.video_id == video.id
        ).first()
        is_liked = bool(existing_like)

    return {
        "code": 200,
        "data": {
            "id": video.id,
            "title": video.title,
            "summary": video.summary or "",
            "cover_url": video.cover_url or "",
            "category": video.category or "短剧",
            "like_count": video.like_count or 0,
            "view_count": video.view_count or 0,
            "coin_count": getattr(video, "coin_count", 0) or 0,
            "heat_score": getattr(video, "heat_score", 0.0) or 0.0,
            "is_liked": is_liked,
            "total_episodes": len(episodes),
            "episodes": [
                {
                    "id": ep.id,
                    "episode_num": ep.episode_num,
                    "title": ep.title,
                    "duration_seconds": ep.duration_seconds,
                    "transcode_status": ep.transcode_status,
                    "stream_url": f"/api/v1/videos/stream/{ep.id}",
                    "created_at": ep.created_at.isoformat() if ep.created_at else ""
                }
                for ep in episodes
            ]
        }
    }

@router.get("/episodes/{episode_id}/history")
def get_watch_history(
    episode_id: str,
    user_id: Optional[str] = Query(None),
    opt_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Retrieve last playback position in seconds for resume prompt."""
    user = resolve_user(db, opt_user, user_id)
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    history = db.query(UserWatchHistory).filter(
        UserWatchHistory.user_id == user.id,
        UserWatchHistory.video_id == episode.video_id
    ).first()

    progress = history.progress_seconds if (history and history.last_episode_id == episode_id) else 0.0

    return {
        "code": 200,
        "data": {
            "episode_id": episode_id,
            "progress_seconds": progress,
            "last_episode_id": history.last_episode_id if history else episode_id
        }
    }

@router.get("/user/histories")
def get_user_all_histories(
    user_id: Optional[str] = Query(None),
    opt_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Retrieve full watch history list for current user."""
    user = resolve_user(db, opt_user, user_id)
    histories = (
        db.query(UserWatchHistory, Video, VideoEpisode)
        .join(Video, UserWatchHistory.video_id == Video.id)
        .join(VideoEpisode, UserWatchHistory.last_episode_id == VideoEpisode.id)
        .filter(UserWatchHistory.user_id == user.id)
        .order_by(desc(UserWatchHistory.updated_at))
        .all()
    )
    return {
        "code": 200,
        "data": [
            {
                "video_id": v.id,
                "video_title": v.title,
                "cover_url": v.cover_url,
                "episode_id": ep.id,
                "episode_num": ep.episode_num,
                "episode_title": ep.title,
                "progress_seconds": h.progress_seconds,
                "updated_at": h.updated_at.strftime("%Y-%m-%d %H:%M") if h.updated_at else ""
            }
            for h, v, ep in histories
        ]
    }

@router.post("/episodes/{episode_id}/heartbeat")
def record_watch_heartbeat(
    episode_id: str,
    req: HeartbeatRequest,
    opt_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Record periodically streamed playback seconds."""
    user = resolve_user(db, opt_user, req.user_id)
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    history = db.query(UserWatchHistory).filter(
        UserWatchHistory.user_id == user.id,
        UserWatchHistory.video_id == episode.video_id
    ).first()

    if not history:
        history = UserWatchHistory(
            user_id=user.id,
            video_id=episode.video_id,
            last_episode_id=episode_id,
            progress_seconds=req.progress_seconds
        )
        db.add(history)
    else:
        history.last_episode_id = episode_id
        history.progress_seconds = req.progress_seconds
        history.updated_at = datetime.utcnow()

    db.commit()
    return {"code": 200, "message": "Heartbeat updated", "data": {"progress_seconds": req.progress_seconds}}

@router.get("/episodes/{episode_id}/like-status")
def get_like_status(
    episode_id: str,
    opt_user: Optional[User] = Depends(get_optional_user),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Query whether the user liked the parent drama of this episode."""
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    video = db.query(Video).filter(Video.id == episode.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Parent video not found")

    effective_user_id = opt_user.id if opt_user else user_id
    is_liked = False
    if effective_user_id:
        existing = db.query(UserLike).filter(
            UserLike.user_id == effective_user_id,
            UserLike.video_id == video.id
        ).first()
        is_liked = bool(existing)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "is_liked": is_liked,
            "like_count": video.like_count or 0,
            "heat_score": getattr(video, "heat_score", 0.0) or 0.0
        }
    }

@router.post("/episodes/{episode_id}/like")
def toggle_like(
    episode_id: str,
    req: Optional[LikeRequest] = None,
    opt_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Toggle user like on the parent video of this episode, recalculate heat score and notify creator."""
    req_user_id = req.user_id if req else None
    user = resolve_user(db, opt_user, req_user_id)
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    video = db.query(Video).filter(Video.id == episode.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Parent video not found")

    existing_like = db.query(UserLike).filter(
        UserLike.user_id == user.id,
        UserLike.video_id == video.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        video.like_count = max(0, (video.like_count or 0) - 1)
        is_liked = False
    else:
        new_like = UserLike(user_id=user.id, video_id=video.id)
        db.add(new_like)
        video.like_count = (video.like_count or 0) + 1
        is_liked = True

        # Send notification to video creator
        if video.creator_id and video.creator_id != user.id:
            notif = UserNotification(
                id=str(uuid.uuid4()),
                user_id=video.creator_id,
                sender_id=user.id,
                category="LIKE",
                title="短剧收到点赞",
                content=f"用户 @{user.nickname or user.username} 点赞了您的短剧《{video.title}》",
                video_id=video.id,
                episode_id=episode_id
            )
            db.add(notif)

    # Recalculate heat score
    heat_score = recalculate_heat_score(db, video)
    db.commit()

    return {
        "code": 200,
        "message": "点赞成功" if is_liked else "已取消点赞",
        "data": {
            "is_liked": is_liked,
            "like_count": video.like_count,
            "heat_score": heat_score
        }
    }

@router.post("/comments/{comment_id}/like")
def toggle_comment_like(
    comment_id: str,
    req: Optional[LikeRequest] = None,
    opt_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Toggle like on a specific comment (with deduplication) and notify author."""
    req_user_id = req.user_id if req else None
    user = resolve_user(db, opt_user, req_user_id)

    comment = db.query(UserComment).filter(UserComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    existing_like = db.query(CommentLike).filter(
        CommentLike.user_id == user.id,
        CommentLike.comment_id == comment.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        comment.like_count = max(0, (comment.like_count or 0) - 1)
        is_liked = False
    else:
        new_like = CommentLike(user_id=user.id, comment_id=comment.id)
        db.add(new_like)
        comment.like_count = (comment.like_count or 0) + 1
        is_liked = True

        # Send notification to comment author
        if comment.user_id and comment.user_id != user.id:
            snippet = comment.content[:30] + ("..." if len(comment.content) > 30 else "")
            notif = UserNotification(
                id=str(uuid.uuid4()),
                user_id=comment.user_id,
                sender_id=user.id,
                category="LIKE",
                title="评论收到赞",
                content=f"用户 @{user.nickname or user.username} 点赞了您的评论: \"{snippet}\"",
                comment_id=comment.id,
                video_id=comment.video_id
            )
            db.add(notif)

    db.commit()
    return {
        "code": 200,
        "message": "评论点赞成功" if is_liked else "已取消评论点赞",
        "data": {
            "is_liked": is_liked,
            "like_count": comment.like_count
        }
    }

@router.get("/episodes/{episode_id}/comments")
def get_comments(
    episode_id: str,
    opt_user: Optional[User] = Depends(get_optional_user),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Fetch two-tier comment tree for the drama of this episode.
    Returns root comments with nested replies array and reply_to user info.
    """
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Fetch all comments for this drama
    all_comments = (
        db.query(UserComment)
        .filter(UserComment.video_id == episode.video_id)
        .order_by(UserComment.created_at.asc())
        .all()
    )

    # Determine liked comments by current user
    effective_user_id = opt_user.id if opt_user else user_id
    liked_comment_ids = set()
    if effective_user_id:
        liked_records = db.query(CommentLike.comment_id).filter(CommentLike.user_id == effective_user_id).all()
        liked_comment_ids = {r[0] for r in liked_records}

    # Fetch user metadata mapping
    user_ids = {c.user_id for c in all_comments} | {c.reply_to_user_id for c in all_comments if c.reply_to_user_id}
    users_map: Dict[str, User] = {}
    if user_ids:
        users = db.query(User).filter(User.id.in_(list(user_ids))).all()
        users_map = {u.id: u for u in users}

    # Separate roots and replies
    root_comments: List[UserComment] = []
    replies_by_root: Dict[str, List[Dict[str, Any]]] = {}

    for c in all_comments:
        u = users_map.get(c.user_id)
        u_name = u.username if u else "用户"
        u_nick = u.nickname if (u and u.nickname) else u_name
        u_avatar = (u.avatar_url if (u and u.avatar_url) else f"https://api.dicebear.com/7.x/bottts/svg?seed={u_name}")

        is_reply = bool(c.root_id or (c.parent_id and c.parent_id != c.id))

        if not is_reply:
            root_comments.append(c)
        else:
            root_key = c.root_id or c.parent_id
            if root_key not in replies_by_root:
                replies_by_root[root_key] = []

            # Reply to user info
            reply_to_user = users_map.get(c.reply_to_user_id) if c.reply_to_user_id else None

            replies_by_root[root_key].append({
                "id": c.id,
                "root_id": c.root_id or root_key,
                "parent_id": c.parent_id or root_key,
                "user_id": c.user_id,
                "username": u_name,
                "nickname": u_nick,
                "avatar_url": u_avatar,
                "reply_to_user_id": c.reply_to_user_id,
                "reply_to_username": reply_to_user.username if reply_to_user else None,
                "reply_to_nickname": (reply_to_user.nickname or reply_to_user.username) if reply_to_user else None,
                "content": c.content,
                "like_count": c.like_count or 0,
                "is_liked": c.id in liked_comment_ids,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
            })

    # Sort root comments descending by creation time
    root_comments.sort(key=lambda x: x.created_at, reverse=True)

    items = []
    for rc in root_comments:
        u = users_map.get(rc.user_id)
        u_name = u.username if u else "用户"
        u_nick = u.nickname if (u and u.nickname) else u_name
        u_avatar = (u.avatar_url if (u and u.avatar_url) else f"https://api.dicebear.com/7.x/bottts/svg?seed={u_name}")

        replies = replies_by_root.get(rc.id, [])
        items.append({
            "id": rc.id,
            "user_id": rc.user_id,
            "username": u_name,
            "nickname": u_nick,
            "avatar_url": u_avatar,
            "content": rc.content,
            "like_count": rc.like_count or 0,
            "is_liked": rc.id in liked_comment_ids,
            "created_at": rc.created_at.strftime("%Y-%m-%d %H:%M") if rc.created_at else "",
            "replies": replies,
            "reply_count": len(replies)
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "total": len(items)
        }
    }

@router.post("/episodes/{episode_id}/comments")
def create_comment(
    episode_id: str,
    req: CommentCreateRequest,
    opt_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Post a new comment or nested two-tier reply on the episode's drama.
    Automatically links root_id and dispatches reply notification.
    """
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")

    user = resolve_user(db, opt_user, req.user_id)
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    actual_root_id = req.root_id
    actual_parent_id = req.parent_id
    actual_reply_to_user_id = req.reply_to_user_id

    # Defensive two-tier tree normalization:
    if actual_parent_id:
        parent_comment = db.query(UserComment).filter(UserComment.id == actual_parent_id).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent_comment.root_id:
            # Parent is already a reply, collapse root_id to top-level comment
            actual_root_id = parent_comment.root_id
        else:
            actual_root_id = parent_comment.id

        if not actual_reply_to_user_id:
            actual_reply_to_user_id = parent_comment.user_id

    new_comment = UserComment(
        id=str(uuid.uuid4()),
        video_id=episode.video_id,
        user_id=user.id,
        parent_id=actual_parent_id,
        root_id=actual_root_id,
        reply_to_user_id=actual_reply_to_user_id,
        content=req.content.strip(),
        like_count=0
    )
    db.add(new_comment)

    # Dispatch notification for reply
    target_user_id = actual_reply_to_user_id
    if not target_user_id and actual_root_id:
        root_c = db.query(UserComment).filter(UserComment.id == actual_root_id).first()
        if root_c:
            target_user_id = root_c.user_id

    if target_user_id and target_user_id != user.id:
        snippet = new_comment.content[:30] + ("..." if len(new_comment.content) > 30 else "")
        notif = UserNotification(
            id=str(uuid.uuid4()),
            user_id=target_user_id,
            sender_id=user.id,
            category="REPLY",
            title="收到新的评论回复",
            content=f"用户 @{user.nickname or user.username} 回复了您的评论: \"{snippet}\"",
            video_id=episode.video_id,
            episode_id=episode_id,
            comment_id=new_comment.id
        )
        db.add(notif)

    db.commit()
    db.refresh(new_comment)

    # Fetch reply_to user info if applicable
    reply_to_user = None
    if actual_reply_to_user_id:
        reply_to_user = db.query(User).filter(User.id == actual_reply_to_user_id).first()

    return {
        "code": 200,
        "message": "Comment posted successfully",
        "data": {
            "id": new_comment.id,
            "root_id": new_comment.root_id,
            "parent_id": new_comment.parent_id,
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname or user.username,
            "avatar_url": user.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={user.username}",
            "reply_to_user_id": new_comment.reply_to_user_id,
            "reply_to_username": reply_to_user.username if reply_to_user else None,
            "reply_to_nickname": (reply_to_user.nickname or reply_to_user.username) if reply_to_user else None,
            "content": new_comment.content,
            "like_count": 0,
            "is_liked": False,
            "replies": [],
            "reply_count": 0,
            "created_at": new_comment.created_at.strftime("%Y-%m-%d %H:%M")
        }
    }

# ---------------------------------------------------------
# Video Coin Tipping Endpoints
# ---------------------------------------------------------
@router.post("/episodes/{episode_id}/tip")
def tip_video(
    episode_id: str,
    req: TipVideoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tip coins to the parent drama of this episode.
    Max 2 coins per user per drama. Deducts wallet, updates tip counter and heat score.
    Strictly authenticated: uses current_user.id for wallet deduction and tipping limits.
    """
    user = current_user
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    video = db.query(Video).filter(Video.id == episode.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Parent video not found")

    # Lock and get user wallet (auto initialize with 50 coins if not created yet)
    wallet = db.query(UserCoinWallet).filter(
        UserCoinWallet.user_id == user.id
    ).execution_options(populate_existing=True).with_for_update().first()
    if not wallet:
        from app.api.v1.endpoints.coins import get_or_create_wallet
        wallet = get_or_create_wallet(db, user.id)
        wallet = db.query(UserCoinWallet).filter(
            UserCoinWallet.id == wallet.id
        ).execution_options(populate_existing=True).with_for_update().first()

    if wallet.balance < req.coin_amount:
        raise HTTPException(
            status_code=400,
            detail=f"金币余额不足，需要 {req.coin_amount} 金币，当前余额为 {wallet.balance}"
        )

    # Check existing tip limit (max 2 per drama per user) with pessimistic lock
    tip = db.query(VideoCoinTip).filter(
        VideoCoinTip.user_id == user.id,
        VideoCoinTip.video_id == video.id
    ).execution_options(populate_existing=True).with_for_update().first()

    already_tipped = tip.tip_count if tip else 0
    if already_tipped + req.coin_amount > 2:
        raise HTTPException(
            status_code=400,
            detail=f"每部短剧每人最多打赏2枚金币(已达上限)，您已打赏 {already_tipped} 枚，本次无法再打赏 {req.coin_amount} 枚"
        )

    # Deduct wallet
    wallet.balance -= req.coin_amount
    wallet.total_spent += req.coin_amount

    # Write transaction record
    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=user.id,
        amount=-req.coin_amount,
        balance_after=wallet.balance,
        transaction_type="TIP_VIDEO",
        description=f"为短剧《{video.title}》打赏 {req.coin_amount} 金币",
        reference_id=video.id
    )
    db.add(tx)

    # Update or create tip
    if tip:
        tip.tip_count += req.coin_amount
        tip.updated_at = datetime.utcnow()
    else:
        tip = VideoCoinTip(
            id=str(uuid.uuid4()),
            user_id=user.id,
            video_id=video.id,
            tip_count=req.coin_amount
        )
        db.add(tip)

    # Update video coin_count and heat score
    video.coin_count = (getattr(video, "coin_count", 0) or 0) + req.coin_amount
    heat_score = recalculate_heat_score(db, video)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="打赏冲突或已达单剧上限2枚")

    return {
        "code": 200,
        "message": f"成功为短剧《{video.title}》投递 {req.coin_amount} 枚金币！",
        "data": {
            "tipped_count": tip.tip_count,
            "max_allowed": 2,
            "video_coin_count": video.coin_count,
            "heat_score": heat_score,
            "wallet_balance": wallet.balance
        }
    }

@router.get("/episodes/{episode_id}/tip-status")
def get_tip_status(
    episode_id: str,
    opt_user: Optional[User] = Depends(get_optional_user),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Query current user's tip count and total video tip count."""
    episode = db.query(VideoEpisode).filter(VideoEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    video = db.query(Video).filter(Video.id == episode.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Parent video not found")

    effective_user_id = opt_user.id if opt_user else user_id
    tipped_count = 0
    if effective_user_id:
        tip = db.query(VideoCoinTip).filter(
            VideoCoinTip.user_id == effective_user_id,
            VideoCoinTip.video_id == video.id
        ).first()
        if tip:
            tipped_count = tip.tip_count

    return {
        "code": 200,
        "message": "success",
        "data": {
            "tipped_count": tipped_count,
            "max_allowed": 2,
            "video_coin_count": getattr(video, "coin_count", 0) or 0,
            "heat_score": getattr(video, "heat_score", 0.0) or 0.0
        }
    }
