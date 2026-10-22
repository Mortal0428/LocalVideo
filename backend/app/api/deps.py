from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Retrieve current user if valid token is provided, otherwise return None (Guest)."""
    if not auth or not auth.credentials:
        return None
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None
    user_id = payload["sub"]
    return db.query(User).filter(User.id == user_id).first()

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Retrieve current user or raise 401 Unauthorized."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录后再进行此操作",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录凭证已过期或无效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被注销",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if getattr(user, "status", "ACTIVE") == "BANNED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该账号已被系统管理员封禁，无法执行操作",
        )
    return user

def require_role(allowed_roles: List[str]):
    """Enforce role-based access control."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无操作权限，需要角色: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_creator(current_user: User = Depends(get_current_user)) -> User:
    """Allow creators and admins to access creator features."""
    if current_user.is_creator or current_user.role in ["CREATOR", "ADMIN"]:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="您尚未开通创作者权限，请先在创作者中心提交申请"
    )
