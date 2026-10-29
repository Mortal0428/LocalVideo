"""
==============================================================================
【模块名称】：admin.py (超级管理中台核心路由集)
【业务职能】：
  本模块是全平台管理中台的心脏，汇集了运营 BI 统计指标、全量审计日志流、用户全生命周期
  CRUD 治理、短剧与海报编目运营、内容弹幕与评论风控、系统全员公告、兑换码批量生成
  以及登录页动态壁纸配置等 46 个超级管理员核心端点。
【对应前端】：
  - 核心页面：frontend/src/views/AdminView.vue (超级管理中台)
  - 中台顶栏：frontend/src/components/AdminHeader.vue
  - 前端通信：frontend/src/api/admin.ts 与 frontend/src/api/mcp.ts
==============================================================================
"""
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
from app.models.system_config import SystemConfig
from app.services.openlist_storage import openlist_storage
from app.services.bi_analytics import bi_analytics
from app.services.audit_service import audit_service

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

class BatchDeleteAnnouncementsRequest(BaseModel):
    announcement_ids: List[str]

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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_admin_bi_metrics] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /bi-metrics
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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

    bi_meta = bi_analytics.get_overview(db)

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
            "rag_center": bi_meta.get("rag_center", {}),
            "agent_fleet": bi_meta.get("agent_fleet", {}),
            "user_operations": bi_meta.get("user_operations", {}),
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

@router.get("/audit-logs")
def get_system_audit_logs(
    page: int = Query(1, ge=1, description="当前页码"),
    page_size: int = Query(15, ge=1, le=100, description="每页条数"),
    module: Optional[str] = Query(None, description="按功能模块过滤"),
    action: Optional[str] = Query(None, description="按操作动作过滤"),
    status: Optional[str] = Query(None, description="按状态过滤 SUCCESS/FAILED/WARNING"),
    user_role: Optional[str] = Query(None, description="按操作角色过滤 admin/creator/user/visitor"),
    keyword: Optional[str] = Query(None, description="关键词搜索(摘要/用户名/IP/目标ID)"),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_system_audit_logs] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /audit-logs
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    audit_service.seed_baseline_logs_if_empty(db)
    result = audit_service.get_logs(
        db=db,
        page=page,
        page_size=page_size,
        module=module,
        action=action,
        status=status,
        user_role=user_role,
        keyword=keyword
    )
    return {
        "code": 200,
        "message": "success",
        "data": result
    }

@router.get("/audit-logs/stats")
def get_system_audit_stats(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_system_audit_stats] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /audit-logs/stats
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    audit_service.seed_baseline_logs_if_empty(db)
    stats = audit_service.get_stats(db)
    return {
        "code": 200,
        "message": "success",
        "data": stats
    }

@router.get("/bi-trends")
def get_admin_bi_trends(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_admin_bi_trends] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /bi-trends
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_admin_overview] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /overview
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_all_users] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /users
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [create_user_by_admin] 业务，负责新建并录入相关系统资产与数据状态。
    对应 HTTP 端点：POST /users
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_user_by_admin] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /users/{user_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_user_by_admin] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /users/{user_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [batch_delete_users_by_admin] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：POST /users/batch-delete
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [adjust_user_coins_by_admin] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /users/{user_id}/adjust-coins
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_user_role] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：POST /users/{user_id}/role
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_user_status] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：POST /users/{user_id}/status
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_pending_applications] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /applications
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [review_creator_application] 业务，负责合规审核与风控判定相关系统资产与数据状态。
    对应 HTTP 端点：POST /creators/review
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [review_reviewer_application] 业务，负责合规审核与风控判定相关系统资产与数据状态。
    对应 HTTP 端点：POST /reviewers/review
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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

def seed_baseline_danmakus_if_empty(db: Session) -> None:
    """
    【基线数据注入函数】：当弹幕表为空时自动注入演示与风控测试弹幕
    入参：
    - db (Session): 数据库会话
    返回值：
    - None
    业务定位：
    保证后台弹幕机审列表具备完整初始数据，同时包含正常互动与涉敏/引流/侮辱样本，
    以供 4号内容安全智能体执行真实的巡检、DFA 过滤与人机回环判定。
    """
    if db.query(VideoDanmaku).count() > 0:
        return

    first_ep = db.query(VideoEpisode).first()
    if not first_ep:
        return

    first_user = db.query(User).first()
    user_id = first_user.id if first_user else "default_viewer"

    sample_danmakus = [
        {"content": "第一集高能反转太爽了！", "time_offset": 3.2, "color": "#0071E3"},
        {"content": "这男主隐藏战神身份太有压迫感了", "time_offset": 8.5, "color": "#34C759"},
        {"content": "女主眼神全是戏，智商在线！", "time_offset": 14.1, "color": "#FFFFFF"},
        {"content": "第2分30秒伏笔回收，神作预定", "time_offset": 22.0, "color": "#FF9500"},
        {"content": "导演这 9:16 竖屏运镜运得真好", "time_offset": 31.5, "color": "#AF52DE"},
        {"content": "一口气追完停不下来，求加更！", "time_offset": 45.0, "color": "#FFFFFF"},
        {"content": "名场面打卡！二刷依然震撼", "time_offset": 58.2, "color": "#30B0C7"},
        {"content": "哈哈哈哈笑死我了，打脸太快了", "time_offset": 72.0, "color": "#FFFFFF"},
        {"content": "背景音乐响起的一瞬间起鸡皮疙瘩", "time_offset": 86.4, "color": "#FF2D55"},
        {"content": "前面的等等我，我也注意到了这个细节", "time_offset": 95.0, "color": "#FFFFFF"},
        {"content": "这反派演得让人咬牙切齿，演技真绝", "time_offset": 105.2, "color": "#FFFFFF"},
        {"content": "全程无尿点，比院线电影还刺激", "time_offset": 118.0, "color": "#0071E3"},
        {"content": "这就是短剧的黄金前三秒魅力吗", "time_offset": 130.5, "color": "#34C759"},
        {"content": "逆袭反转太解压了，爽！", "time_offset": 142.0, "color": "#FFFFFF"},
        {"content": "加微信号领未删减版高清全集资源", "time_offset": 12.0, "color": "#FF3B30"},
        {"content": "代刷短剧播放量低价冲榜加QQ群", "time_offset": 28.5, "color": "#FF3B30"},
        {"content": "这破烂剧情真恶心，女主赶紧滚粗别演了", "time_offset": 60.0, "color": "#FF3B30"},
        {"content": "日入五百正规兼职加微聊包赚不赔", "time_offset": 78.0, "color": "#FF3B30"},
        {"content": "私聊我免费发原片百度网盘无水印", "time_offset": 99.5, "color": "#FF3B30"},
        {"content": "垃圾脑残片去死吧，编剧脑子进水了", "time_offset": 112.0, "color": "#FF3B30"},
    ]

    for item in sample_danmakus:
        dm = VideoDanmaku(
            id=str(uuid.uuid4()),
            episode_id=first_ep.id,
            user_id=user_id,
            time_offset=item["time_offset"],
            content=item["content"],
            color=item["color"],
            font_size=18,
            created_at=datetime.utcnow()
        )
        db.add(dm)
    db.commit()

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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_danmakus_governance] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /contents/danmakus
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    seed_baseline_danmakus_if_empty(db)
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [batch_delete_danmakus] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：POST /contents/danmakus/batch-delete
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_danmaku_item] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /contents/danmakus/{danmaku_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_comments_governance] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /contents/comments
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_comment_item] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /contents/comments/{comment_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_drama_collections] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /dramas
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_drama_options] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /dramas/options
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_drama_item] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /dramas/{video_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [batch_delete_dramas_by_admin] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：POST /dramas/batch-delete
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [toggle_drama_status] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /dramas/{video_id}/status
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_drama_cover] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /dramas/{video_id}/cover
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_drama_posters] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /dramas/{video_id}/posters
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_drama_item] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /dramas/{video_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [sync_all_pan_dramas] 业务，负责数据同频同步相关系统资产与数据状态。
    对应 HTTP 端点：POST /pan/sync-all
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
        f"{mode_text}完成！识别到 {dramas_count} 部短剧（已跳过 {skipped} 部无需重复入库），"
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_system_carousels] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /carousels
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [create_system_carousel] 业务，负责新建并录入相关系统资产与数据状态。
    对应 HTTP 端点：POST /carousels
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_system_carousel] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /carousels/{carousel_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_system_carousel] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /carousels/{carousel_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_system_announcements] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /announcements
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [create_system_announcement] 业务，负责新建并录入相关系统资产与数据状态。
    对应 HTTP 端点：POST /announcements
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_system_announcement] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /announcements/{announcement_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [retract_system_announcement] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /announcements/{announcement_id}/retract
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
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
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_system_announcement] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /announcements/{announcement_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    a = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")

    db.query(UserNotification).filter(UserNotification.announcement_id == announcement_id).delete()
    db.delete(a)
    db.commit()
    return {"code": 200, "message": "公告删除成功", "data": {"id": announcement_id}}

@router.post("/announcements/batch-delete")
def batch_delete_announcements_by_admin(
    req: BatchDeleteAnnouncementsRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [batch_delete_announcements_by_admin] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：POST /announcements/batch-delete
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    deleted_count = 0
    for aid in req.announcement_ids:
        a = db.query(SystemAnnouncement).filter(SystemAnnouncement.id == aid).first()
        if a:
            db.query(UserNotification).filter(UserNotification.announcement_id == aid).delete(synchronize_session=False)
            db.delete(a)
            deleted_count += 1
    db.commit()
    return {
        "code": 200,
        "message": f"已成功批量删除 {deleted_count} 条系统公告",
        "data": {"deleted_count": deleted_count}
    }


# ---------------------------------------------------------
# 9. Gold Coin & VIP Redemption Code Asset Management
# ---------------------------------------------------------
import secrets
from app.models.coin import RedemptionCode

class GenerateRedemptionCodesRequest(BaseModel):
    code_type: str = Field(..., description="兑换码类型: COIN (金币) 或 VIP (会员天数)")
    reward_amount: int = Field(..., ge=1, le=100000, description="面额: 金币枚数 或 VIP天数")
    count: int = Field(1, ge=1, le=100, description="生成数量 (1~100)")
    expires_days: Optional[int] = Field(None, ge=1, le=3650, description="有效天数 (为空则永久有效)")
    remark: Optional[str] = Field(None, max_length=200, description="批次备注说明")

class BatchRedemptionActionRequest(BaseModel):
    code_ids: List[str] = Field(..., min_length=1, description="兑换码 ID 列表")
    action: str = Field(..., description="操作类型: revoke (作废) 或 delete (物理删除)")

def _generate_unique_voucher_code(prefix: str) -> str:
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    part1 = "".join(secrets.choice(alphabet) for _ in range(4))
    part2 = "".join(secrets.choice(alphabet) for _ in range(4))
    part3 = "".join(secrets.choice(alphabet) for _ in range(4))
    return f"{prefix}-{part1}-{part2}-{part3}"

@router.get("/redemption-codes")
def list_redemption_codes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    code_type: Optional[str] = Query(None, description="筛选类型: COIN / VIP"),
    status: Optional[str] = Query(None, description="筛选状态: ACTIVE / USED / EXPIRED / REVOKED"),
    keyword: Optional[str] = Query(None, description="搜索兑换码或备注或核销人"),
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [list_redemption_codes] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /redemption-codes
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    now = datetime.utcnow()
    # 自动将已过期的 ACTIVE 兑换码刷新为 EXPIRED
    db.query(RedemptionCode).filter(
        RedemptionCode.status == "ACTIVE",
        RedemptionCode.expires_at.isnot(None),
        RedemptionCode.expires_at < now
    ).update({RedemptionCode.status: "EXPIRED"}, synchronize_session=False)
    db.commit()

    query = db.query(RedemptionCode)
    if code_type and code_type in ("COIN", "VIP"):
        query = query.filter(RedemptionCode.code_type == code_type)
    if status and status in ("ACTIVE", "USED", "EXPIRED", "REVOKED"):
        query = query.filter(RedemptionCode.status == status)
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query = query.filter(
            (RedemptionCode.code.ilike(kw)) |
            (RedemptionCode.remark.ilike(kw)) |
            (RedemptionCode.used_by_username.ilike(kw))
        )

    total = query.count()
    items = query.order_by(RedemptionCode.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    # 全局汇总统计
    total_active = db.query(RedemptionCode).filter(RedemptionCode.status == "ACTIVE").count()
    total_used = db.query(RedemptionCode).filter(RedemptionCode.status == "USED").count()
    used_coin_rows = db.query(RedemptionCode).filter(RedemptionCode.status == "USED", RedemptionCode.code_type == "COIN").all()
    used_vip_rows = db.query(RedemptionCode).filter(RedemptionCode.status == "USED", RedemptionCode.code_type == "VIP").all()
    total_coins_redeemed = sum(r.reward_amount for r in used_coin_rows)
    total_vip_days_redeemed = sum(r.reward_amount for r in used_vip_rows)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "summary": {
                "total_active": total_active,
                "total_used": total_used,
                "total_coins_redeemed": total_coins_redeemed,
                "total_vip_days_redeemed": total_vip_days_redeemed
            },
            "items": [
                {
                    "id": item.id,
                    "code": item.code,
                    "code_type": item.code_type,
                    "reward_amount": item.reward_amount,
                    "status": item.status,
                    "remark": item.remark or "",
                    "created_by": item.created_by,
                    "used_by": item.used_by,
                    "used_by_username": item.used_by_username or "",
                    "used_at": item.used_at.strftime("%Y-%m-%d %H:%M:%S") if item.used_at else "",
                    "expires_at": item.expires_at.strftime("%Y-%m-%d %H:%M:%S") if item.expires_at else "永久有效",
                    "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else ""
                }
                for item in items
            ]
        }
    }

@router.post("/redemption-codes/generate")
def generate_redemption_codes(
    req: GenerateRedemptionCodesRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [generate_redemption_codes] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /redemption-codes/generate
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ctype = req.code_type.strip().upper()
    if ctype not in ("COIN", "VIP"):
        raise HTTPException(status_code=400, detail="兑换码类型仅支持 COIN (金币) 或 VIP (会员)")

    now = datetime.utcnow()
    expires_at = (now + timedelta(days=req.expires_days)) if req.expires_days else None
    prefix = "COIN" if ctype == "COIN" else "VIP"
    default_remark = f"{req.reward_amount}{'金币兑换卡' if ctype == 'COIN' else '天VIP会员卡'}"
    remark_str = (req.remark.strip() if req.remark and req.remark.strip() else default_remark)

    created_codes = []
    for _ in range(req.count):
        for _attempt in range(10):
            candidate = _generate_unique_voucher_code(prefix)
            exists = db.query(RedemptionCode).filter(RedemptionCode.code == candidate).first()
            if not exists:
                break
        rc = RedemptionCode(
            id=str(uuid.uuid4()),
            code=candidate,
            code_type=ctype,
            reward_amount=req.reward_amount,
            status="ACTIVE",
            remark=remark_str,
            created_by=current_user.id,
            expires_at=expires_at,
            created_at=now
        )
        db.add(rc)
        created_codes.append({
            "id": rc.id,
            "code": rc.code,
            "code_type": rc.code_type,
            "reward_amount": rc.reward_amount,
            "status": rc.status,
            "remark": rc.remark,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S") if expires_at else "永久有效"
        })

    db.commit()
    type_label = f"{req.reward_amount} 金币" if ctype == "COIN" else f"{req.reward_amount} 天 VIP 会员"
    return {
        "code": 200,
        "message": f"成功生成 {len(created_codes)} 张【{type_label}】兑换码",
        "data": {
            "count": len(created_codes),
            "codes": created_codes
        }
    }

@router.post("/redemption-codes/batch-action")
def batch_redemption_codes_action(
    req: BatchRedemptionActionRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [batch_redemption_codes_action] 业务，负责批量治理相关系统资产与数据状态。
    对应 HTTP 端点：POST /redemption-codes/batch-action
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    act = req.action.strip().lower()
    if act not in ("revoke", "delete"):
        raise HTTPException(status_code=400, detail="操作类型仅支持 revoke 或 delete")

    affected = 0
    for cid in req.code_ids:
        rc = db.query(RedemptionCode).filter(RedemptionCode.id == cid).first()
        if not rc:
            continue
        if act == "revoke":
            if rc.status == "ACTIVE":
                rc.status = "REVOKED"
                affected += 1
        elif act == "delete":
            db.delete(rc)
            affected += 1

    db.commit()
    action_label = "作废" if act == "revoke" else "删除"
    return {
        "code": 200,
        "message": f"已成功批量{action_label} {affected} 条兑换码记录",
        "data": {"affected_count": affected}
    }

@router.delete("/redemption-codes/{code_id}")
def delete_redemption_code(
    code_id: str,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [delete_redemption_code] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /redemption-codes/{code_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    rc = db.query(RedemptionCode).filter(RedemptionCode.id == code_id).first()
    if not rc:
        raise HTTPException(status_code=404, detail="兑换码记录不存在")
    db.delete(rc)
    db.commit()
    return {"code": 200, "message": "兑换码已删除", "data": {"id": code_id}}


class AdminWallpaperConfigRequest(BaseModel):
    mode: str = Field("gaoleng_qianjin", description="壁纸模式: default_aurora, gaoleng_qianjin, custom_url")
    custom_url: Optional[str] = Field("", description="自定义壁纸直链URL")
    dark_opacity: Optional[float] = Field(0.45, description="暗色模式遮罩透明度 0.0 - 0.9")
    light_opacity: Optional[float] = Field(0.18, description="浅色模式遮罩透明度 0.0 - 0.9")
    blur_px: Optional[int] = Field(0, description="毛玻璃高斯模糊像素 0 - 20")
    title: Optional[str] = Field("高冷千金的贴身高手 (Wallpaper Engine)", description="壁纸展示标题")


@router.get("/system/wallpaper-config")
def get_admin_wallpaper_config(
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [get_admin_wallpaper_config] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /system/wallpaper-config
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    default_config = {
        "mode": "gaoleng_qianjin",
        "custom_url": "",
        "dark_opacity": 0.45,
        "light_opacity": 0.18,
        "blur_px": 0,
        "title": "高冷千金的贴身高手 (Wallpaper Engine)",
    }
    rec = db.query(SystemConfig).filter(SystemConfig.config_key == "login_wallpaper_config").first()
    if rec and rec.config_value:
        try:
            return {"code": 200, "data": {**default_config, **json.loads(rec.config_value)}}
        except Exception:
            pass
    return {"code": 200, "data": default_config}


@router.put("/system/wallpaper-config")
def update_admin_wallpaper_config(
    req: AdminWallpaperConfigRequest,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [admin] 模块中的 [update_admin_wallpaper_config] 业务，负责修改并更新相关系统资产与数据状态。
    对应 HTTP 端点：PUT /system/wallpaper-config
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/admin.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    val_dict = req.model_dump()
    val_json = json.dumps(val_dict, ensure_ascii=False)
    rec = db.query(SystemConfig).filter(SystemConfig.config_key == "login_wallpaper_config").first()
    if not rec:
        rec = SystemConfig(
            config_key="login_wallpaper_config",
            config_value=val_json,
            description="登录主页背景壁纸配置",
            updated_by=current_user.username
        )
        db.add(rec)
    else:
        rec.config_value = val_json
        rec.updated_by = current_user.username
    db.commit()

    audit_service.log_action(
        db=db,
        module="admin_bi",
        action="update_wallpaper_config",
        summary=f"管理员 {current_user.username} 更新了登录主页背景壁纸为模式 [{req.mode}]",
        user_id=current_user.id,
        username=current_user.username,
        user_role="admin",
        detail_json=val_dict
    )

    return {"code": 200, "message": "登录主页壁纸配置更新成功", "data": val_dict}

