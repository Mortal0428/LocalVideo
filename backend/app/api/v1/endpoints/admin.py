import uuid
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.security import get_password_hash
from app.api.deps import require_role
from app.models.user import User
from app.models.video import Video, VideoEpisode, SystemCarousel
from app.models.interaction import VideoDanmaku, UserComment, UserLike, CommentLike, UserWatchHistory
from app.models.coin import UserCoinWallet, UserCoinTransaction, VideoCoinTip
from app.models.notification import SystemAnnouncement, UserNotification
from app.models.favorite import FavoriteFolder, FavoriteItem
from app.services.openlist_storage import openlist_storage
from app.services.bi_analytics import bi_analytics

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------
class CreateUserRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="登录密码")
    nickname: Optional[str] = Field(None, description="用户昵称")
    role: Optional[str] = Field("USER", description="系统角色: USER, CREATOR, REVIEWER, ADMIN")
    coins: Optional[int] = Field(50, description="初始金币余额")
    vip_days: Optional[int] = Field(0, description="初始VIP天数")

class AdminUpdateUserRequest(BaseModel):
    nickname: Optional[str] = Field(None, description="用户昵称")
    password: Optional[str] = Field(None, description="新登录密码 (可选)")
    role: Optional[str] = Field(None, description="系统角色")
    status: Optional[str] = Field(None, description="状态: ACTIVE 或 BANNED")
    coins: Optional[int] = Field(None, description="设置金币余额")
    coins_adjustment: Optional[int] = Field(None, description="增减金币数")
    vip_expire_at: Optional[str] = Field(None, description="VIP到期时间 ISO字符串")
    vip_days: Optional[int] = Field(None, description="增加VIP天数")

class CreateAnnouncementRequest(BaseModel):
    title: str = Field(..., description="公告标题")
    content: str = Field(..., description="公告内容")
    tag: Optional[str] = Field("系统公告", description="分类标签")

class UpdateAnnouncementRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tag: Optional[str] = None
    is_published: Optional[bool] = None

class UpdateUserStatusRequest(BaseModel):
    status: str = Field(..., description="目标状态: ACTIVE 或 BANNED")

class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="新系统角色: USER, CREATOR, REVIEWER, ADMIN")

class ReviewCreatorRequest(BaseModel):
    user_id: str
    action: str = Field(..., description="审批动作: APPROVE 或 REJECT")
    remarks: Optional[str] = Field(None, description="审批意见")

class ReviewReviewerRequest(BaseModel):
    user_id: str
    action: str = Field(..., description="审批动作: APPROVE 或 REJECT")
    remarks: Optional[str] = Field(None, description="审批意见")

class UpdateDramaRequest(BaseModel):
    title: Optional[str] = Field(None, description="短剧名称")
    category: Optional[str] = Field(None, description="短剧分类")
    summary: Optional[str] = Field(None, description="短剧简介")
    cover_url: Optional[str] = Field(None, description="封面图片链接")
    status: Optional[str] = Field(None, description="发布状态: PUBLISHED, DRAFT, HIDDEN")
    extra_images: Optional[List[str]] = Field(None, description="多海报图片URL列表")

class ToggleDramaStatusRequest(BaseModel):
    status: str = Field(..., description="PUBLISHED 或 HIDDEN")

class UpdateDramaCoverRequest(BaseModel):
    cover_url: str = Field(..., description="新封面图片链接")

class CreateCarouselRequest(BaseModel):
    title: str = Field(..., description="主标题")
    subtitle: Optional[str] = Field(None, description="副标题说明")
    tag: str = Field("今日焦点推荐", description="标签角标")
    cover_url: str = Field(..., description="轮播大图链接")
    video_id: Optional[str] = Field(None, description="绑定的短剧作品ID")
    sort_order: int = Field(1, description="排序优先级")
    is_active: bool = Field(True, description="是否启用显示")
    duration_seconds: Optional[int] = Field(5, description="停留展示秒数")

class UpdateCarouselRequest(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    tag: Optional[str] = None
    cover_url: Optional[str] = None
    video_id: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    duration_seconds: Optional[int] = None

class BatchDeleteUsersRequest(BaseModel):
    user_ids: List[str] = Field(..., description="待删除的用户ID列表")

class AdjustUserCoinsRequest(BaseModel):
    amount: int = Field(..., description="变动金币数量，可正可负")
    reason: Optional[str] = Field("管理员中台手动调整", description="变动理由")
    vip_days: Optional[int] = Field(0, description="变动VIP天数，可正可负")

class BatchDeleteDramasRequest(BaseModel):
    drama_ids: List[str] = Field(..., description="待删除的短剧ID列表")

class SyncPanRequest(BaseModel):
    mode: Optional[str] = Field("incremental", description="同步模式: incremental(增量推荐) 或 full(全量重算)")

class BatchDeleteDanmakusRequest(BaseModel):
    ids: List[str] = Field(default_factory=list, description="需要批量删除的弹幕ID数组")

class UpdateDramaPostersRequest(BaseModel):
    extra_images: List[str] = Field(default_factory=list, description="多海报图片URL列表")

# ---------------------------------------------------------
# 1. BI Metrics & System Overview
# ---------------------------------------------------------
# ---------------------------------------------------------
@router.get("/bi-metrics")
async def get_admin_bi_metrics(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Get full BI metrics & telemetry indicators for Admin Dashboard.
    """
    total_users = db.query(User).count()
    active_creators = db.query(User).filter((User.is_creator == True) | (User.role == "CREATOR")).count()
    active_reviewers = db.query(User).filter((User.is_reviewer == True) | (User.role == "REVIEWER")).count()
    banned_users = db.query(User).filter(User.status == "BANNED").count()
    pending_creators = db.query(User).filter(User.creator_application_status == "PENDING").count()
    pending_reviewers = db.query(User).filter(User.reviewer_application_status == "PENDING").count()
    
    total_dramas = db.query(Video).count()
    total_episodes = db.query(VideoEpisode).count()
    
    total_views = db.query(func.sum(Video.view_count)).scalar() or 0
    total_danmakus = db.query(VideoDanmaku).count()
    total_comments = db.query(UserComment).count()
    total_likes = db.query(UserLike).count()

    # Category breakdown
    cat_counts = (
        db.query(Video.category, func.count(Video.id))
        .group_by(Video.category)
        .all()
    )
    categories_distribution = [{"name": c[0] or "未分类", "count": c[1]} for c in cat_counts]

    # Cloud disk status check
    cloud_status = "ONLINE"
    cloud_items_count = 0
    try:
        files = await openlist_storage.list_files("/kuake/红果项目资源目录")
        cloud_items_count = len(files) if isinstance(files, list) else 0
    except Exception as e:
        cloud_status = f"WARNING: {str(e)[:30]}"

    return {
        "code": 200,
        "message": "success",
        "data": {
            "bi_cards": {
                "total_views": int(total_views),
                "total_danmakus": total_danmakus,
                "total_comments": total_comments,
                "total_likes": total_likes,
                "total_users": total_users,
                "active_creators": active_creators,
                "active_reviewers": active_reviewers,
                "banned_users": banned_users,
                "pending_applications": pending_creators + pending_reviewers,
                "total_dramas": total_dramas,
                "total_episodes": total_episodes
            },
            "categories_distribution": categories_distribution,
            "cloud_storage": {
                "status": cloud_status,
                "mount_path": "/kuake/红果项目资源目录",
                "items_count": cloud_items_count
            },
            "ai_engine": {
                "active_model": "qwen2.5:latest",
                "rag_status": "ONLINE",
                "temperature": 0.7
            }
        }
    }

@router.get("/bi-trends")
def get_admin_bi_trends(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Get 14-day history, 7-day Holt-Winters predictive time series,
    and Bass diffusion viral potential rankings.
    """
    data = bi_analytics.get_time_series_and_predictions(db)
    return {
        "code": 200,
        "message": "success",
        "data": data
    }

@router.get("/overview")
async def get_admin_overview(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Compatible overview endpoint.
    """
    total_users = db.query(User).count()
    active_creators = db.query(User).filter((User.is_creator == True) | (User.role == "CREATOR")).count()
    banned_users = db.query(User).filter(User.status == "BANNED").count()
    pending_creators = db.query(User).filter(User.creator_application_status == "PENDING").count()
    pending_reviewers = db.query(User).filter(User.reviewer_application_status == "PENDING").count()
    total_dramas = db.query(Video).count()
    total_episodes = db.query(VideoEpisode).count()

    cloud_status = "ONLINE"
    try:
        await openlist_storage.list_files("/kuake")
    except Exception as e:
        cloud_status = f"WARNING: {str(e)[:40]}"

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_users": total_users,
            "active_creators": active_creators,
            "banned_users": banned_users,
            "pending_creators": pending_creators,
            "pending_reviewers": pending_reviewers,
            "total_dramas": total_dramas,
            "total_episodes": total_episodes,
            "cloud_disk_status": cloud_status,
            "active_mount": "/kuake/红果项目资源目录"
        }
    }

# ---------------------------------------------------------
# 2. Users & RBAC Role Governance
# ---------------------------------------------------------
@router.get("/users")
def list_all_users(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    List all platform users with role, qualifications, coins, VIP, and moderation state.
    """
    query = db.query(User)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.username.like(s)) | (User.nickname.like(s)))
    if role:
        query = query.filter(User.role == role.upper())
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    user_ids = [u.id for u in users]
    wallets = db.query(UserCoinWallet).filter(UserCoinWallet.user_id.in_(user_ids)).all() if user_ids else []
    wallet_map = {w.user_id: w.balance for w in wallets}

    result = []
    for u in users:
        vip_expire_str = u.vip_expire_at.isoformat() if getattr(u, "vip_expire_at", None) else None
        is_vip = bool(u.vip_expire_at and u.vip_expire_at > datetime.utcnow())
        result.append({
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "role": u.role,
            "coins": wallet_map.get(u.id, 50),
            "vip_expire_at": vip_expire_str,
            "is_vip": is_vip,
            "is_creator": bool(u.is_creator or u.role == "CREATOR"),
            "is_reviewer": bool(getattr(u, "is_reviewer", False) or u.role == "REVIEWER"),
            "status": getattr(u, "status", "ACTIVE") or "ACTIVE",
            "creator_application_status": getattr(u, "creator_application_status", None),
            "creator_bio": getattr(u, "creator_bio", None),
            "reviewer_application_status": getattr(u, "reviewer_application_status", None),
            "reviewer_bio": getattr(u, "reviewer_bio", None),
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": result
        }
    }

@router.post("/users")
def create_user_by_admin(
    req: CreateUserRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin creates a new user with initial credentials, coins, and VIP status."""
    existing = db.query(User).filter(User.username == req.username.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"用户名 '{req.username}' 已被占用")

    user_role = (req.role or "USER").upper()
    if user_role not in ["USER", "CREATOR", "REVIEWER", "ADMIN"]:
        raise HTTPException(status_code=400, detail="角色类型必须为 USER, CREATOR, REVIEWER, ADMIN")

    vip_expire = None
    if req.vip_days and req.vip_days > 0:
        vip_expire = datetime.utcnow() + timedelta(days=req.vip_days)

    new_user = User(
        id=str(uuid.uuid4()),
        username=req.username.strip(),
        password_hash=get_password_hash(req.password),
        nickname=req.nickname.strip() if req.nickname else req.username.strip(),
        role=user_role,
        is_creator=(user_role in ["CREATOR", "ADMIN"]),
        is_reviewer=(user_role in ["REVIEWER", "ADMIN"]),
        status="ACTIVE",
        vip_expire_at=vip_expire
    )
    db.add(new_user)
    db.flush()

    init_coins = req.coins if req.coins is not None else 50
    wallet = UserCoinWallet(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        balance=init_coins,
        total_earned=init_coins,
        total_spent=0
    )
    db.add(wallet)

    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=new_user.id,
        amount=init_coins,
        balance_after=init_coins,
        transaction_type="ADMIN_ADJUST",
        description="管理员新建用户初始金币"
    )
    db.add(tx)
    db.commit()
    db.refresh(new_user)

    return {
        "code": 200,
        "message": f"用户 @{new_user.username} 创建成功",
        "data": {
            "id": new_user.id,
            "username": new_user.username,
            "nickname": new_user.nickname,
            "role": new_user.role,
            "coins": wallet.balance,
            "vip_expire_at": new_user.vip_expire_at.isoformat() if new_user.vip_expire_at else None,
            "status": new_user.status
        }
    }

@router.put("/users/{user_id}")
def update_user_by_admin(
    user_id: str,
    req: AdminUpdateUserRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin updates user profile, password, role, status, coins, and VIP expiration."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    if req.nickname is not None and req.nickname.strip():
        target.nickname = req.nickname.strip()

    if req.password is not None and req.password.strip():
        target.password_hash = get_password_hash(req.password.strip())

    if req.role is not None and req.role.strip():
        r = req.role.strip().upper()
        if r in ["USER", "CREATOR", "REVIEWER", "ADMIN"]:
            target.role = r
            if r == "CREATOR":
                target.is_creator = True
            elif r == "REVIEWER":
                target.is_reviewer = True
            elif r == "ADMIN":
                target.is_creator = True
                target.is_reviewer = True
            elif r == "USER":
                target.is_creator = False
                target.is_reviewer = False

    if req.status is not None and req.status.strip():
        s = req.status.strip().upper()
        if s in ["ACTIVE", "BANNED"]:
            if user_id == current_user.id and s == "BANNED":
                raise HTTPException(status_code=400, detail="管理员不能封禁自己的账号")
            target.status = s

    # Handle VIP adjustment
    if req.vip_days is not None and req.vip_days != 0:
        now = datetime.utcnow()
        base = target.vip_expire_at if (target.vip_expire_at and target.vip_expire_at > now) else now
        target.vip_expire_at = base + timedelta(days=req.vip_days)
    elif req.vip_expire_at is not None:
        if req.vip_expire_at == "":
            target.vip_expire_at = None
        else:
            try:
                target.vip_expire_at = datetime.fromisoformat(req.vip_expire_at.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                pass

    # Handle Coins adjustment
    wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == target.id).first()
    if not wallet:
        wallet = UserCoinWallet(id=str(uuid.uuid4()), user_id=target.id, balance=50, total_earned=50, total_spent=0)
        db.add(wallet)
        db.flush()

    if req.coins is not None:
        diff = req.coins - wallet.balance
        wallet.balance = max(0, req.coins)
        tx = UserCoinTransaction(
            id=str(uuid.uuid4()),
            user_id=target.id,
            amount=diff,
            balance_after=wallet.balance,
            transaction_type="ADMIN_ADJUST",
            description=f"管理员调整金币余额至 {wallet.balance}"
        )
        db.add(tx)
    elif req.coins_adjustment is not None and req.coins_adjustment != 0:
        wallet.balance = max(0, wallet.balance + req.coins_adjustment)
        tx = UserCoinTransaction(
            id=str(uuid.uuid4()),
            user_id=target.id,
            amount=req.coins_adjustment,
            balance_after=wallet.balance,
            transaction_type="ADMIN_ADJUST",
            description=f"管理员增减金币 {req.coins_adjustment}"
        )
        db.add(tx)

    db.commit()
    db.refresh(target)
    db.refresh(wallet)

    return {
        "code": 200,
        "message": f"用户 @{target.username} 资料更新成功",
        "data": {
            "id": target.id,
            "username": target.username,
            "nickname": target.nickname,
            "role": target.role,
            "status": target.status,
            "coins": wallet.balance,
            "vip_expire_at": target.vip_expire_at.isoformat() if target.vip_expire_at else None,
            "is_vip": bool(target.vip_expire_at and target.vip_expire_at > datetime.utcnow())
        }
    }

def _cascade_delete_single_user(db: Session, user_id: str, operator_id: str) -> str:
    """Helper to cascade delete a single user and associated records."""
    if user_id == operator_id:
        raise HTTPException(status_code=400, detail="管理员不能删除当前登录的管理员账号")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return ""

    db.query(UserCoinTransaction).filter(UserCoinTransaction.user_id == user_id).delete(synchronize_session=False)
    db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).delete(synchronize_session=False)
    db.query(VideoCoinTip).filter(VideoCoinTip.user_id == user_id).delete(synchronize_session=False)
    db.query(CommentLike).filter(CommentLike.user_id == user_id).delete(synchronize_session=False)
    db.query(UserLike).filter(UserLike.user_id == user_id).delete(synchronize_session=False)
    db.query(UserWatchHistory).filter(UserWatchHistory.user_id == user_id).delete(synchronize_session=False)
    db.query(UserNotification).filter((UserNotification.user_id == user_id) | (UserNotification.sender_id == user_id)).delete(synchronize_session=False)
    db.query(FavoriteItem).filter(FavoriteItem.user_id == user_id).delete(synchronize_session=False)
    db.query(FavoriteFolder).filter(FavoriteFolder.user_id == user_id).delete(synchronize_session=False)

    user_root_comment_rows = db.query(UserComment.id).filter(
        UserComment.user_id == user_id,
        UserComment.root_id.is_(None)
    ).all()
    user_root_comment_ids = [r[0] for r in user_root_comment_rows]

    if user_root_comment_ids:
        child_rows = db.query(UserComment.id).filter(
            UserComment.root_id.in_(user_root_comment_ids)
        ).all()
        child_ids = [r[0] for r in child_rows]
        if child_ids:
            db.query(CommentLike).filter(CommentLike.comment_id.in_(child_ids)).delete(synchronize_session=False)
        db.query(UserComment).filter(UserComment.root_id.in_(user_root_comment_ids)).delete(synchronize_session=False)

    user_authored_rows = db.query(UserComment.id).filter(UserComment.user_id == user_id).all()
    user_authored_ids = [r[0] for r in user_authored_rows]
    if user_authored_ids:
        db.query(CommentLike).filter(CommentLike.comment_id.in_(user_authored_ids)).delete(synchronize_session=False)

    db.query(UserComment).filter(UserComment.user_id == user_id).delete(synchronize_session=False)
    db.query(VideoDanmaku).filter(VideoDanmaku.user_id == user_id).delete(synchronize_session=False)

    deleted_username = target.username
    db.delete(target)
    return deleted_username

@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin hard deletes a user account with cascading cleanup of associated records."""
    deleted_username = _cascade_delete_single_user(db, user_id, current_user.id)
    if not deleted_username:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    db.commit()

    return {
        "code": 200,
        "message": f"用户 @{deleted_username} 已成功物理删除",
        "data": {"id": user_id, "username": deleted_username}
    }

@router.post("/users/batch-delete")
def batch_delete_users_by_admin(
    req: BatchDeleteUsersRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin batch hard deletes multiple selected user accounts."""
    deleted_names = []
    for uid in req.user_ids:
        if uid == current_user.id:
            continue
        uname = _cascade_delete_single_user(db, uid, current_user.id)
        if uname:
            deleted_names.append(uname)
    db.commit()

    return {
        "code": 200,
        "message": f"已成功批量删除 {len(deleted_names)} 个用户账号",
        "data": {"deleted_count": len(deleted_names), "deleted_users": deleted_names}
    }

@router.post("/users/{user_id}/adjust-coins")
def adjust_user_coins_by_admin(
    user_id: str,
    req: AdjustUserCoinsRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin manually adjusts user coins and VIP days with audit log."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).with_for_update().first()
    if not wallet:
        wallet = UserCoinWallet(user_id=user_id, balance=50)
        db.add(wallet)

    old_bal = wallet.balance
    new_bal = max(0, old_bal + req.amount)
    wallet.balance = new_bal

    # Record transaction
    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        amount=req.amount,
        balance_after=new_bal,
        tx_type="ADMIN_ADJUST",
        description=f"{req.reason} (操作员: @{current_user.username})"
    )
    db.add(tx)

    # Adjust VIP if provided
    if req.vip_days and req.vip_days != 0:
        base_time = target.vip_expire_at if (target.vip_expire_at and target.vip_expire_at > datetime.utcnow()) else datetime.utcnow()
        target.vip_expire_at = base_time + timedelta(days=req.vip_days)

    db.commit()

    return {
        "code": 200,
        "message": f"已成功为 @{target.username} 调整资产，金币变动 {req.amount:+d}，当前余额: {new_bal}",
        "data": {
            "user_id": user_id,
            "coins": new_bal,
            "vip_expire_at": target.vip_expire_at.isoformat() if target.vip_expire_at else None
        }
    }


@router.post("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    req: UpdateUserRoleRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Admin directly updates a user's system role and syncs qualifications.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    target_role = req.role.upper()
    if target_role not in ["USER", "CREATOR", "REVIEWER", "ADMIN"]:
        raise HTTPException(status_code=400, detail="角色类型必须为 USER, CREATOR, REVIEWER, ADMIN")

    target.role = target_role
    if target_role == "CREATOR":
        target.is_creator = True
        target.creator_application_status = "APPROVED"
    elif target_role == "REVIEWER":
        target.is_reviewer = True
        target.reviewer_application_status = "APPROVED"
    elif target_role == "ADMIN":
        target.is_creator = True
        target.is_reviewer = True
    elif target_role == "USER":
        # Reset specific elevated privileges if explicitly demoted to ordinary user
        target.is_creator = False
        target.is_reviewer = False

    db.commit()
    db.refresh(target)

    return {
        "code": 200,
        "message": f"已成功将用户 @{target.username} 角色更新为 {target.role}",
        "data": {
            "id": target.id,
            "username": target.username,
            "role": target.role,
            "is_creator": target.is_creator,
            "is_reviewer": target.is_reviewer
        }
    }

@router.post("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    req: UpdateUserStatusRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Ban or unban a user. Admins cannot ban their own account.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="管理员不能封禁自己的账号")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    new_status = req.status.upper()
    if new_status not in ["ACTIVE", "BANNED"]:
        raise HTTPException(status_code=400, detail="状态值必须为 ACTIVE 或 BANNED")

    target.status = new_status
    db.commit()
    db.refresh(target)

    action_label = "封禁" if new_status == "BANNED" else "解除封禁"
    return {
        "code": 200,
        "message": f"已成功将用户 @{target.username} {action_label}",
        "data": {
            "id": target.id,
            "username": target.username,
            "status": target.status
        }
    }

# ---------------------------------------------------------
# 3. Application Approval Center (Creator & Reviewer)
# ---------------------------------------------------------
@router.get("/applications")
def list_pending_applications(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Get all pending creator and reviewer applications for admin review.
    """
    creator_apps = (
        db.query(User)
        .filter(User.creator_application_status == "PENDING")
        .order_by(User.created_at.desc())
        .all()
    )
    reviewer_apps = (
        db.query(User)
        .filter(User.reviewer_application_status == "PENDING")
        .order_by(User.created_at.desc())
        .all()
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "creators": [
                {
                    "user_id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "bio": u.creator_bio,
                    "status": u.creator_application_status,
                    "applied_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
                }
                for u in creator_apps
            ],
            "reviewers": [
                {
                    "user_id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "bio": getattr(u, "reviewer_bio", None),
                    "status": getattr(u, "reviewer_application_status", None),
                    "applied_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
                }
                for u in reviewer_apps
            ]
        }
    }

@router.post("/creators/review")
def review_creator_application(
    req: ReviewCreatorRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Approve or reject a user's creator application.
    """
    target = db.query(User).filter(User.id == req.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    action = req.action.upper()
    if action == "APPROVE":
        target.is_creator = True
        target.role = "CREATOR"
        target.creator_application_status = "APPROVED"
        msg = f"已通过用户 @{target.username} 的创作者资质审核，已赋予 CREATOR 角色"
    elif action == "REJECT":
        target.is_creator = False
        target.creator_application_status = "REJECTED"
        msg = f"已驳回用户 @{target.username} 的创作者申请"
    else:
        raise HTTPException(status_code=400, detail="操作类型必须为 APPROVE 或 REJECT")

    db.commit()
    db.refresh(target)

    return {
        "code": 200,
        "message": msg,
        "data": {
            "id": target.id,
            "username": target.username,
            "is_creator": target.is_creator,
            "role": target.role,
            "creator_application_status": target.creator_application_status
        }
    }

@router.post("/reviewers/review")
def review_reviewer_application(
    req: ReviewReviewerRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Approve or reject a user's reviewer application.
    """
    target = db.query(User).filter(User.id == req.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    action = req.action.upper()
    if action == "APPROVE":
        target.is_reviewer = True
        target.role = "REVIEWER"
        target.reviewer_application_status = "APPROVED"
        msg = f"已通过用户 @{target.username} 的审核员资质审核，已赋予 REVIEWER 角色并解锁审核中台"
    elif action == "REJECT":
        target.is_reviewer = False
        target.reviewer_application_status = "REJECTED"
        msg = f"已驳回用户 @{target.username} 的审核员申请"
    else:
        raise HTTPException(status_code=400, detail="操作类型必须为 APPROVE 或 REJECT")

    db.commit()
    db.refresh(target)

    return {
        "code": 200,
        "message": msg,
        "data": {
            "id": target.id,
            "username": target.username,
            "is_reviewer": target.is_reviewer,
            "role": target.role,
            "reviewer_application_status": target.reviewer_application_status
        }
    }

# ---------------------------------------------------------
# 4. Content Moderation (Danmaku & Comments Governance)
# ---------------------------------------------------------
@router.get("/contents/danmakus")
def list_danmakus_governance(
    page: int = 1,
    per_page: int = 30,
    search: Optional[str] = None,
    keyword: Optional[str] = None,
    time_min: Optional[float] = None,
    time_max: Optional[float] = None,
    video_id: Optional[str] = None,
    episode_id: Optional[str] = None,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    List danmakus for admin moderation with multi-dimensional filtering.
    """
    q = db.query(VideoDanmaku)
    kw = (keyword or search or "").strip()
    if kw:
        q = q.filter(VideoDanmaku.content.like(f"%{kw}%"))
    
    if episode_id:
        q = q.filter(VideoDanmaku.episode_id == episode_id)
    elif video_id:
        q = q.join(VideoEpisode, VideoDanmaku.episode_id == VideoEpisode.id).filter(VideoEpisode.video_id == video_id)
    
    if time_min is not None:
        q = q.filter(VideoDanmaku.time_offset >= time_min)
    if time_max is not None:
        q = q.filter(VideoDanmaku.time_offset <= time_max)
    
    total = q.count()
    items = q.order_by(VideoDanmaku.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for d in items:
        user_name = d.user.username if d.user else "匿名剧迷"
        ep = db.query(VideoEpisode).filter(VideoEpisode.id == d.episode_id).first()
        ep_title = f"第 {ep.episode_num} 集" if ep else "未知分集"
        vid_title = ep.video.title if ep and ep.video else "短剧"
        result.append({
            "id": d.id,
            "content": d.content,
            "color": d.color or "#FFFFFF",
            "track": getattr(d, "track", 1),
            "speed": getattr(d, "speed", 6),
            "timestamp": getattr(d, "time_offset", 0.0),
            "time_offset": getattr(d, "time_offset", 0.0),
            "user_id": d.user_id,
            "user_name": user_name,
            "video_title": vid_title,
            "episode_title": ep_title,
            "created_at": d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {"total": total, "page": page, "per_page": per_page, "items": result}
    }

@router.post("/contents/danmakus/batch-delete")
def batch_delete_danmakus(
    req: BatchDeleteDanmakusRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Atomic batch deletion of violating danmakus.
    """
    if not req.ids:
        return {"code": 200, "message": "无需删除", "deleted_count": 0, "success": True}
    
    deleted_count = db.query(VideoDanmaku).filter(VideoDanmaku.id.in_(req.ids)).delete(synchronize_session=False)
    db.commit()
    return {
        "code": 200,
        "message": f"成功批量下架 {deleted_count} 条违规弹幕",
        "deleted_count": deleted_count,
        "success": True
    }

@router.delete("/contents/danmakus/{danmaku_id}")
def delete_danmaku_item(
    danmaku_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Delete a violating danmaku.
    """
    item = db.query(VideoDanmaku).filter(VideoDanmaku.id == danmaku_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="弹幕不存在")
    
    db.delete(item)
    db.commit()
    return {"code": 200, "message": "弹幕已成功删除下架"}

@router.get("/contents/comments")
def list_comments_governance(
    page: int = 1,
    per_page: int = 30,
    search: Optional[str] = None,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    List user comments for admin moderation.
    """
    q = db.query(UserComment)
    if search:
        q = q.filter(UserComment.content.like(f"%{search.strip()}%"))
    
    total = q.count()
    items = q.order_by(UserComment.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for c in items:
        user_name = c.user.username if c.user else "匿名用户"
        v = db.query(Video).filter(Video.id == c.video_id).first()
        v_title = v.title if v else "关联作品"
        result.append({
            "id": c.id,
            "content": c.content,
            "user_id": c.user_id,
            "user_name": user_name,
            "video_title": v_title,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {"total": total, "page": page, "per_page": per_page, "items": result}
    }

@router.delete("/contents/comments/{comment_id}")
def delete_comment_item(
    comment_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Delete a violating comment.
    """
    item = db.query(UserComment).filter(UserComment.id == comment_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    db.delete(item)
    db.commit()
    return {"code": 200, "message": "评论已成功删除下架"}

# ---------------------------------------------------------
# 5. Short Drama Collections Catalog Management
# ---------------------------------------------------------
@router.get("/dramas")
def list_drama_collections(
    page: int = 1,
    per_page: int = 30,
    search: Optional[str] = None,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    List all short drama collections in library for admin management.
    """
    q = db.query(Video)
    if search:
        q = q.filter(Video.title.like(f"%{search.strip()}%"))
    
    total = q.count()
    videos = q.order_by(Video.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for v in videos:
        ep_count = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).count()
        first_ep = db.query(VideoEpisode).filter(VideoEpisode.video_id == v.id).first()
        storage_path = first_ep.raw_file_path if first_ep else "/kuake/红果项目资源目录"
        extra_imgs = []
        if v.extra_images:
            try:
                extra_imgs = json.loads(v.extra_images)
            except Exception:
                extra_imgs = []
        effective_cover = v.custom_cover_url or v.cover_url or ""
        items.append({
            "id": v.id,
            "title": v.title,
            "category": v.category or "微短剧",
            "summary": v.summary or "",
            "cover_url": v.cover_url or "",
            "custom_cover_url": v.custom_cover_url or "",
            "effective_cover": effective_cover,
            "extra_images": extra_imgs,
            "status": v.status or "PUBLISHED",
            "total_episodes": ep_count or v.total_episodes or 1,
            "view_count": v.view_count or 0,
            "like_count": v.like_count or 0,
            "storage_path": storage_path,
            "created_at": v.created_at.strftime("%Y-%m-%d %H:%M") if v.created_at else ""
        })

    return {
        "code": 200,
        "message": "success",
        "data": {"total": total, "page": page, "per_page": per_page, "items": items}
    }

@router.get("/dramas/options")
def get_drama_options(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Lightweight list of dramas for carousel dropdown and poster management.
    """
    dramas = db.query(Video).order_by(desc(Video.created_at)).all()
    return {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": d.id,
                "title": d.title,
                "category": d.category or "短剧",
                "cover_url": d.cover_url or "",
                "extra_images": d.extra_images or "[]"
            }
            for d in dramas
        ]
    }

@router.put("/dramas/{video_id}")
def update_drama_item(
    video_id: str,
    req: UpdateDramaRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Update short drama title, category, summary, cover_url, or status.
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="短剧作品不存在")
    
    if req.title is not None and req.title.strip():
        v.title = req.title.strip()
    if req.category is not None and req.category.strip():
        v.category = req.category.strip()
    if req.summary is not None:
        v.summary = req.summary.strip()
    if req.cover_url is not None:
        v.cover_url = req.cover_url.strip()
        v.custom_cover_url = req.cover_url.strip()
    if req.status is not None and req.status.strip():
        v.status = req.status.strip().upper()
    if req.extra_images is not None:
        v.extra_images = json.dumps(req.extra_images, ensure_ascii=False)
    
    db.commit()
    db.refresh(v)
    return {
        "code": 200,
        "message": "短剧信息更新成功",
        "data": {
            "id": v.id,
            "title": v.title,
            "category": v.category,
            "summary": v.summary,
            "cover_url": v.custom_cover_url or v.cover_url,
            "extra_images": json.loads(v.extra_images) if v.extra_images else [],
            "status": v.status
        }
    }

@router.post("/dramas/batch-delete")
def batch_delete_dramas_by_admin(
    req: BatchDeleteDramasRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin batch deletes multiple short dramas and their episodes."""
    deleted_count = 0
    for vid in req.drama_ids:
        v = db.query(Video).filter(Video.id == vid).first()
        if v:
            db.delete(v)
            deleted_count += 1
    db.commit()
    return {
        "code": 200,
        "message": f"已成功批量删除 {deleted_count} 部短剧作品",
        "data": {"deleted_count": deleted_count}
    }

@router.post("/dramas/{video_id}/status")
def toggle_drama_status(
    video_id: str,
    req: ToggleDramaStatusRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Toggle or update drama visibility status (PUBLISHED vs HIDDEN).
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="短剧作品不存在")
    target_status = req.status.upper()
    if target_status not in ["PUBLISHED", "HIDDEN", "DRAFT"]:
        target_status = "PUBLISHED" if v.status == "HIDDEN" else "HIDDEN"
    v.status = target_status
    db.commit()
    db.refresh(v)
    return {
        "code": 200,
        "message": f"短剧状态已变更为: {v.status}",
        "data": {"id": v.id, "status": v.status}
    }

@router.put("/dramas/{video_id}/cover")
def update_drama_cover(
    video_id: str,
    req: UpdateDramaCoverRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Update custom cover URL of short drama.
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="短剧作品不存在")
    v.custom_cover_url = req.cover_url.strip()
    db.commit()
    db.refresh(v)
    return {
        "code": 200,
        "message": "封面更新成功",
        "data": {"id": v.id, "cover_url": v.custom_cover_url}
    }

@router.put("/dramas/{video_id}/posters")
def update_drama_posters(
    video_id: str,
    req: UpdateDramaPostersRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Update multi-cover poster array for short drama.
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="短剧作品不存在")
    
    v.extra_images = json.dumps(req.extra_images, ensure_ascii=False)
    db.commit()
    db.refresh(v)
    return {
        "code": 200,
        "message": "剧集多海报更新成功",
        "data": {
            "id": v.id,
            "extra_images": req.extra_images
        }
    }

@router.delete("/dramas/{video_id}")
def delete_drama_item(
    video_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Delete a short drama collection and its episodes.
    """
    v = db.query(Video).filter(Video.id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="短剧作品不存在")
    db.delete(v)
    db.commit()
    return {"code": 200, "message": "短剧及对应剧集已成功彻底删除"}

# ---------------------------------------------------------
# 6. Cloud Disk Drama Synchronization (Incremental & Full)
# ---------------------------------------------------------
@router.post("/pan/sync-all")
async def sync_all_pan_dramas(
    mode: Optional[str] = Query("incremental", description="同步模式: incremental(增量推荐) 或 full(全量扫描)"),
    req: Optional[SyncPanRequest] = None,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Admin triggers synchronization of Quark Cloud Disk dramas into MySQL.
    Supports incremental (fast, skip already-synced) or full re-sync.
    """
    sync_mode = (req.mode if req and req.mode else mode) or "incremental"
    from app.services.cloud_drama_sync import cloud_drama_sync
    res = await cloud_drama_sync.scan_and_sync_all(db=db, mode=sync_mode)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "同步短剧失败"))
    
    dramas_list = res.get("dramas", [])
    total_episodes = res.get("total_episodes", sum(d.get("total_episodes", 0) for d in dramas_list))
    dramas_count = res.get("total_synced_dramas", len(dramas_list))
    new_eps = res.get("new_episodes_added", 0)
    skipped = res.get("skipped_dramas", 0)

    mode_text = "增量优化同步" if sync_mode == "incremental" else "全量覆盖同步"
    msg = (
        f"✅ {mode_text}完成！识别到 {dramas_count} 部短剧（已跳过 {skipped} 部无需重复入库），"
        f"共 {total_episodes} 集（本次新增入库 {new_eps} 集），已即刻对全站用户广播！"
    )

    return {
        "code": 200,
        "message": msg,
        "data": {
            "success": True,
            "mode": sync_mode,
            "dramas_found": dramas_count,
            "total_synced_dramas": dramas_count,
            "total_episodes": total_episodes,
            "new_episodes_added": new_eps,
            "skipped_dramas": skipped,
            "dramas": dramas_list
        }
    }

# ---------------------------------------------------------
# 7. Hero Carousels Management
# ---------------------------------------------------------
@router.get("/carousels")
def list_system_carousels(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    List all home hero carousels for admin management.
    """
    items = db.query(SystemCarousel).order_by(SystemCarousel.sort_order.asc()).all()
    res = []
    for sc in items:
        drama_title = ""
        if sc.video_id:
            v = db.query(Video).filter(Video.id == sc.video_id).first()
            if v:
                drama_title = v.title
        res.append({
            "id": sc.id,
            "title": sc.title,
            "subtitle": sc.subtitle or "",
            "tag": sc.tag or "今日焦点",
            "cover_url": sc.cover_url,
            "video_id": sc.video_id,
            "drama_title": drama_title,
            "sort_order": sc.sort_order,
            "is_active": sc.is_active,
            "duration_seconds": getattr(sc, "duration_seconds", 5) or 5,
            "created_at": sc.created_at.strftime("%Y-%m-%d %H:%M") if sc.created_at else ""
        })
    return {"code": 200, "message": "success", "data": res}

@router.post("/carousels")
def create_system_carousel(
    req: CreateCarouselRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Create a new hero carousel item.
    """
    sc = SystemCarousel(
        title=req.title.strip(),
        subtitle=req.subtitle.strip() if req.subtitle else None,
        tag=req.tag.strip() if req.tag else "今日焦点推荐",
        cover_url=req.cover_url.strip(),
        video_id=req.video_id,
        sort_order=req.sort_order,
        is_active=req.is_active,
        duration_seconds=req.duration_seconds or 5
    )
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return {"code": 200, "message": "轮播图创建成功", "data": {"id": sc.id, "title": sc.title}}

@router.put("/carousels/{carousel_id}")
def update_system_carousel(
    carousel_id: str,
    req: UpdateCarouselRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Update a hero carousel item.
    """
    sc = db.query(SystemCarousel).filter(SystemCarousel.id == carousel_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    if req.title is not None and req.title.strip():
        sc.title = req.title.strip()
    if req.subtitle is not None:
        sc.subtitle = req.subtitle.strip()
    if req.tag is not None:
        sc.tag = req.tag.strip()
    if req.cover_url is not None and req.cover_url.strip():
        sc.cover_url = req.cover_url.strip()
    if req.video_id is not None:
        sc.video_id = req.video_id
    if req.sort_order is not None:
        sc.sort_order = req.sort_order
    if req.is_active is not None:
        sc.is_active = req.is_active
    if req.duration_seconds is not None:
        sc.duration_seconds = max(2, min(30, req.duration_seconds))
    db.commit()
    db.refresh(sc)
    return {"code": 200, "message": "轮播图更新成功", "data": {"id": sc.id, "title": sc.title, "duration_seconds": sc.duration_seconds}}

@router.delete("/carousels/{carousel_id}")
def delete_system_carousel(
    carousel_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Delete a hero carousel item.
    """
    sc = db.query(SystemCarousel).filter(SystemCarousel.id == carousel_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    db.delete(sc)
    db.commit()
    return {"code": 200, "message": "轮播图已删除"}

# ---------------------------------------------------------
# 8. System Announcements Management
# ---------------------------------------------------------
@router.get("/announcements")
def list_system_announcements(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin retrieves list of all system announcements."""
    query = db.query(SystemAnnouncement).order_by(desc(SystemAnnouncement.created_at))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": [
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
                    "tag": a.tag,
                    "is_published": a.is_published,
                    "creator_id": a.creator_id,
                    "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
                    "updated_at": a.updated_at.strftime("%Y-%m-%d %H:%M:%S") if a.updated_at else ""
                }
                for a in items
            ]
        }
    }

@router.post("/announcements")
def create_system_announcement(
    req: CreateAnnouncementRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin creates and publishes a new system announcement, broadcasting to users."""
    announcement = SystemAnnouncement(
        id=str(uuid.uuid4()),
        title=req.title.strip(),
        content=req.content.strip(),
        tag=req.tag.strip() if req.tag else "系统公告",
        is_published=True,
        creator_id=current_user.id
    )
    db.add(announcement)
    db.flush()

    # Broadcast notification to all active users
    users = db.query(User).filter(User.status == "ACTIVE").all()
    for u in users:
        notif = UserNotification(
            id=str(uuid.uuid4()),
            user_id=u.id,
            sender_id=current_user.id,
            category="ANNOUNCEMENT",
            title=f"【{announcement.tag}】{announcement.title}",
            content=announcement.content,
            announcement_id=announcement.id
        )
        db.add(notif)

    db.commit()
    db.refresh(announcement)
    return {
        "code": 200,
        "message": "全员系统公告发布成功",
        "data": {
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "tag": announcement.tag,
            "is_published": announcement.is_published,
            "created_at": announcement.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

@router.put("/announcements/{announcement_id}")
def update_system_announcement(
    announcement_id: str,
    req: UpdateAnnouncementRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin updates announcement details and publication status."""
    a = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")

    if req.title is not None and req.title.strip():
        a.title = req.title.strip()
    if req.content is not None and req.content.strip():
        a.content = req.content.strip()
    if req.tag is not None and req.tag.strip():
        a.tag = req.tag.strip()
    if req.is_published is not None:
        a.is_published = req.is_published
    a.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(a)
    return {
        "code": 200,
        "message": "公告更新成功",
        "data": {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "tag": a.tag,
            "is_published": a.is_published
        }
    }

@router.post("/announcements/{announcement_id}/retract")
def retract_system_announcement(
    announcement_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin retracts a published announcement."""
    a = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")
    a.is_published = False
    a.updated_at = datetime.utcnow()
    db.commit()
    return {"code": 200, "message": "公告已成功撤回", "data": {"id": a.id, "is_published": False}}

@router.delete("/announcements/{announcement_id}")
def delete_system_announcement(
    announcement_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Admin hard deletes an announcement and cleans up related notifications."""
    a = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")

    db.query(UserNotification).filter(UserNotification.announcement_id == announcement_id).delete()
    db.delete(a)
    db.commit()
    return {"code": 200, "message": "公告删除成功", "data": {"id": announcement_id}}

