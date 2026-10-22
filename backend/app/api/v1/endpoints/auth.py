import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
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
    """Get profile of current authenticated user."""
    return current_user

@router.post("/quick-switch/{role}", response_model=TokenResponse)
def quick_switch_test_account(role: str, db: Session = Depends(get_db)):
    """Convenient one-click switch among predefined test roles (USER, CREATOR, REVIEWER, ADMIN)."""
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
