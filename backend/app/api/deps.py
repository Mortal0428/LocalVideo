# -*- coding: utf-8 -*-
"""
==============================================================================
【核心依赖守卫】：backend/app/api/deps.py
【业务定位】：FastAPI 依赖注入（Dependency Injection）、身份验证守卫与角色权限门禁
【核心功能】：
  1. get_db: 数据库事务会话生成器，自动分配并在请求结束时妥善关闭连接；
  2. get_optional_user: 可选用户解析（游客或已登录用户），常用于播放器（游客也能看，但登录才能发弹幕和投币）；
  3. get_current_user: 严格登录守卫，从请求头 Authorization: Bearer <Token> 中解码
     用户身份，核对是否被封禁，未登录或凭证过期自动拦截并返回 401 Unauthorized；
  4. require_role: 基于角色的访问控制（RBAC 门禁），如 require_role(["ADMIN"]) 保护管理后台；
  5. require_creator: 创作者权限守卫，允许 CREATOR 与 ADMIN 访问创作者工作台。
【对应前端】：
  - 前端请求拦截器：frontend/src/utils/request.ts (自动注入 Bearer Token)
  - 路由权限守卫：frontend/src/router/index.ts (前端页面路由权限拦截)
==============================================================================
"""
from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

# HTTP Bearer 认证方案配置（auto_error=False 允许游客无 Token 访问非强制接口）
security_scheme = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """
    【大白话功能】：为每个 HTTP 请求派发一个独立的事务级数据库 Session。
    请求结束时自动进入 finally 块关闭 Session，归还连接到数据库连接池。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    【大白话功能】：尝试提取当前访问用户。
    如果客户端带了有效 Token，返回该 User 对象；如果是游客未登录，则优雅返回 None。
    适用于：视频播放页面（游客也可以免费观看，但登录用户能记录历史和点赞）。
    """
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
    """
    【大白话功能】：强制要求用户必须已经登录。
    【拦截场景】：
      1. 未携带 Token：抛出 401 Unauthorized（提示：“请先登录后再进行此操作”）；
      2. Token 过期或被篡改：抛出 401 Unauthorized（提示：“登录凭证已过期或无效，请重新登录”）；
      3. 用户在数据库中被删除：抛出 401 Unauthorized（提示：“用户不存在或已被注销”）；
      4. 账号状态为 BANNED 封禁：抛出 403 Forbidden（提示：“账号已被系统管理员封禁，无法继续操作”）。
    【返回数据】：校验通过后返回完整的当前登录 User ORM 实体对象。
    """
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
            detail="账号已被系统管理员封禁，无法继续操作",
        )
    return user

def require_role(allowed_roles: List[str]):
    """
    【大白话功能】：权限角色高阶守卫工厂函数（RBAC 拦截器）。
    用法示例：@router.get('/admin-only', dependencies=[Depends(require_role(['ADMIN']))])
    若当前用户的 role 不在 allowed_roles 列表中，立刻抛出 403 阻断操作。
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无操作权限，需要角色权限: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def require_creator(current_user: User = Depends(get_current_user)) -> User:
    """
    【大白话功能】：创作者专属功能门禁守卫。
    只有激活了创作者身份（is_creator=True）或者拥有 CREATOR / ADMIN 角色的用户方可通行。
    """
    if current_user.is_creator or current_user.role in ["CREATOR", "ADMIN"]:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="您尚未开通创作者权限，请前往个人空间提交创作者资格申请"
    )
