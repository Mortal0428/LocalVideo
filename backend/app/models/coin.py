import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class UserCoinWallet(Base):
    """用户金币钱包主表"""
    __tablename__ = "user_coin_wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    balance: Mapped[int] = mapped_column(Integer, default=50)  # 新注册默认获赠 50 金币
    total_earned: Mapped[int] = mapped_column(Integer, default=50)
    total_spent: Mapped[int] = mapped_column(Integer, default=0)
    last_sign_in_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User")


class UserCoinTransaction(Base):
    """金币账本明细流水表"""
    __tablename__ = "user_coin_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 正数为入账，负数为支出
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # REGISTER_BONUS, SIGN_IN, AD_REWARD, TIP_VIDEO, VIP_EXCHANGE, ADMIN_ADJUST
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VideoCoinTip(Base):
    """用户对短剧的投币打赏记录 (每人每剧上限2枚)"""
    __tablename__ = "video_coin_tips"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_coin_tip"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    tip_count: Mapped[int] = mapped_column(Integer, default=0)  # 累计已投枚数 (1 或 2)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
