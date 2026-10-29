# -*- coding: utf-8 -*-
"""
==============================================================================
【核心模块】：backend/app/core/security.py
【业务定位】：系统安全凭据、单向哈希加盐加密与 JWT 鉴权令牌守卫
【核心功能】：
  1. 密码散列（Hash）：使用行业标准的 bcrypt 算法，单向加盐哈希（10 轮加盐计算），
     杜绝明文密码泄露隐患；
  2. 密码比对（Verify）：安全核验明文输入与数据库散列串是否一致，防止时序攻击；
  3. JWT 访问令牌签发（create_access_token）：基于 HS256 算法对用户身份（sub: user_id）
     签名打包，默认有效期 7 天，返回给前端本地持久化（localStorage）；
  4. JWT 令牌解密与过期核验（decode_access_token）：在每次 API 请求到达时，
     解码 Authorization 头，还原当前请求的真实用户身份。
【对应前端】：
  - 登录发起：frontend/src/views/LoginView.vue
  - 令牌持久化与全局拦截器：frontend/src/utils/request.ts (Axios 请求拦截器自动附带 Bearer Token)
==============================================================================
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from app.core.config import settings

# JWT 签名私钥（优先读取系统环境变量或配置文件，未配置时使用平台预设私钥）
SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "cinema_agent_super_secret_jwt_key_2026")

# 签名算法采用对称散列签名 HS256
ALGORITHM = "HS256"

# Access Token 默认有效期：7 天 (60 * 24 * 7 分钟)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

def get_password_hash(password: str) -> str:
    """
    【大白话功能】：将用户输入的明文密码通过 bcrypt 单向加密成密文。
    【执行步骤】：
      第 1 步：生成随机盐值（rounds=10），每次即使相同密码生成的哈希密文也截然不同；
      第 2 步：计算散列字节并解码为 utf-8 字符串；
      第 3 步：返回长为 60 位的哈希串，存入 MySQL 数据库的 users 表。
    """
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    【大白话功能】：验证用户登录时输入的明文密码与数据库里的密文是否吻合。
    【执行步骤】：
      第 1 步：将输入的明文字符串编码为字节；
      第 2 步：调用 bcrypt.checkpw 比对；
      第 3 步：匹配成功返回 True，密码错误或密文损坏返回 False。
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    【大白话功能】：为成功登录的用户签发一张具有数字签名的电子通行证 (JWT Token)。
    【执行步骤】：
      第 1 步：复制要打包的数据字典（通常包含用户 ID sub 与角色 role）；
      第 2 步：注入通行证过期截止时间戳 exp；
      第 3 步：使用服务端私钥 SECRET_KEY 签发并生成加密 Token 字符串。
    【返回数据】：一段形如 eyJhbGciOiJIUzI1Ni... 的紧凑字符串，前端将其保存在浏览器中。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    【大白话功能】：核验前端请求头带过来的通行证是否真实有效且未过期。
    【执行步骤】：
      第 1 步：使用服务端私钥 SECRET_KEY 和指定算法尝试解码 Token；
      第 2 步：若通行证被篡改、过期或伪造，解码器自动抛出异常；
      第 3 步：正常解码则返回包含 sub(user_id) 的原始载荷字典。
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
