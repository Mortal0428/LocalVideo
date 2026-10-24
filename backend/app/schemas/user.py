from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    role: Optional[str] = Field("USER", description="角色: USER, CREATOR, REVIEWER, ADMIN")

class UserLoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class UserResponse(BaseModel):
    id: str
    username: str
    nickname: Optional[str] = None
    role: str
    is_creator: bool = False
    is_reviewer: bool = False
    status: str = "ACTIVE"
    creator_application_status: Optional[str] = None
    creator_bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
