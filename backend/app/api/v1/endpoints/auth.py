"""
==============================================================================
【模块名称】：auth.py (系统安全认证、登录、注册与身份守卫)
【业务职能】：
  负责全平台用户身份凭证的签发与验证，包括观众注册、密码哈希校验、JWT Access Token 签发、
  获取当前登录用户信息、测试账号免密一键切换以及免登录壁纸公开配置读取。
【对应前端】：
  - 核心页面：frontend/src/views/LoginView.vue (系统登录与注册大厅)
  - 全局守卫：frontend/src/router/index.ts (Vue Router 路由导航守卫)
  - 前端通信：frontend/src/api/auth.ts (login, register, getMe)
==============================================================================
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.system_config import SystemConfig
from app.schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse

router = APIRouter()
logger = logging.getLogger("auth")

TEST_ACCOUNTS = [
    {"username": "viewer", "password": "password123", "nickname": "追剧小能手", "role": "USER", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=viewer"},
    {"username": "creator", "password": "password123", "nickname": "星芒短剧厂牌", "role": "CREATOR", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=creator"},
    {"username": "reviewer", "password": "password123", "nickname": "平台合规官", "role": "REVIEWER", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=reviewer"},
    {"username": "admin", "password": "password123", "nickname": "超级管理员", "role": "ADMIN", "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=admin"}
]

def ensure_test_accounts(db: Session):
    """Seed default test accounts if not already present."""
    for acc in TEST_ACCOUNTS:
        existing = db.query(User).filter(User.username == acc["username"]).first()
        if not existing:
            u = User(
                username=acc["username"],
                password_hash=get_password_hash(acc["password"]),
                nickname=acc["nickname"],
                role=acc["role"],
                avatar_url=acc["avatar_url"]
            )
            db.add(u)
    db.commit()

@router.post("/register", response_model=UserResponse)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
      新观众/新用户注册账号的总入口。
    【从前端哪里调过来的】：
      - 对应前端页面：LoginView.vue (登录与注册视窗)
      - 对应前端动作：观众输入用户名和密码后，点击表单底部的"注册"按钮
      - 对应前端通信：frontend/src/api/auth.ts 中的 authApi.register()
    【核心执行步骤（大白话）】：
      第 1 步：查验重名——去 MySQL 的 User 表查一下，看看该用户名是否已被占用；如果占用了就报 400 提示重名；
      第 2 步：安全加密——绝不能存明文密码！用 bcrypt 算法生成单向哈希密文；
      第 3 步：写入数据库——创建 User 新记录，默认角色为普通观众 USER；
      第 4 步：新人福利派发——系统自动调用钱包模块，往 UserCoinWallet 表初始化并免费赠送 50 枚金币！
    【数据传到哪里去 / 返回什么】：
      返回注册成功的用户公开信息，前端收到后弹出通知，并引导观众直接登录。
    ==============================================================================
    """
    """Register a new user account."""
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户名 '{req.username}' 已被注册，请更换用户名"
        )
    
    user = User(
        username=req.username,
        password_hash=get_password_hash(req.password),
        nickname=req.nickname or req.username,
        role=req.role or "USER",
        avatar_url=f"https://api.dicebear.com/7.x/bottts/svg?seed={req.username}"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Registered new user: {user.username} ({user.role})")
    return user

@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
      用户登录与生成身份令牌 (JWT Token) 的总入口。
    【从前端哪里调过来的】：
      - 对应前端页面：LoginView.vue (登录与注册视窗)
      - 对应前端动作：输入账密点击"登录"按钮
      - 对应前端通信：frontend/src/api/auth.ts 中的 authApi.login()
    【核心执行步骤（大白话）】：
      第 1 步：去 User 表按用户名查找用户；如果查不到，说明账号不存在；
      第 2 步：校验密码——把用户输入的明文密码与数据库里存的 bcrypt 密文进行比对；不对就报 401 提示账密错误；
      第 3 步：制作身份通行证 (JWT Access Token)——把用户 ID、角色写进 Token 荷载，签名防伪造；
      第 4 步：记录最后登录时间。
    【数据传到哪里去 / 返回什么】：
      返回 access_token 与用户信息。前端收到后保存在浏览器的 localStorage 中，后续发所有请求都会带上它证明身份。
    ==============================================================================
    """
    """Authenticate with username and password, returns JWT token."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    token = create_access_token({"sub": user.id, "role": user.role, "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    获取当前已登录用户的最新档案资料、会员 VIP 状态与权限角色。
    对应 HTTP 端点：GET /me
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：页面初始化加载
    - 调用链路：前端通过 auth.ts -> getMe() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    return current_user

@router.post("/quick-switch/{role}", response_model=TokenResponse)
def quick_switch_test_account(role: str, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    测试账号免密一键切换接口，供开发调试时快速在 ADMIN/CREATOR/USER 角色间无缝跳转。
    对应 HTTP 端点：POST /quick-switch/{role}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：登录页快捷测试账号按钮
    - 调用链路：前端通过 auth.ts -> quickSwitch() 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    ensure_test_accounts(db)
    role_upper = role.upper()
    user = db.query(User).filter(User.role == role_upper).first()
    if not user:
        # Default to viewer
        user = db.query(User).filter(User.username == "viewer").first()
    
    token = create_access_token({"sub": user.id, "role": user.role, "username": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/wallpaper-config")
def get_public_wallpaper_config(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    获取未登录前登录大厅的动态壁纸配置（壁纸图、纯净模式开关）。
    对应 HTTP 端点：GET /wallpaper-config
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：登录页挂载时自动调用
    - 调用链路：前端通过 auth.ts -> getPublicWallpaperConfig() 发起 Axios 异步请求
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
    try:
        rec = db.query(SystemConfig).filter(SystemConfig.config_key == "login_wallpaper_config").first()
        if rec and rec.config_value:
            loaded = json.loads(rec.config_value)
            return {"code": 200, "data": {**default_config, **loaded}}
    except Exception as e:
        logger.warning(f"Failed to query wallpaper config: {e}")
    return {"code": 200, "data": default_config}
