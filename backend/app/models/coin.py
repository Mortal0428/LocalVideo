# -*- coding: utf-8 -*-
"""
==============================================================================
【模型文件】：backend/app/models/coin.py
【业务定位】：虚拟金币经济系统、收支流水、短剧打赏与兑换卡密模型
【对应表名】：user_coin_wallets, user_coin_transactions, video_coin_tips, redemption_codes
【核心功能】：
  支撑全站激励闭环与虚拟消费：
  - UserCoinWallet: 个人金币钱包（余额、累计赚取、累计消费、签到防重）
  - UserCoinTransaction: 严格的双向收支明细流水账（充值、看广告、投币、兑换VIP）
  - VideoCoinTip: 短剧投币打赏记录（每剧上限 2 枚币，联动短剧热度值）
  - RedemptionCode: 管理员生成的口令卡密（支持兑换金币或直接激活 VIP 会员）
【对应前端】：
  - 个人中心钱包与卡片：frontend/src/views/UserProfileView.vue
  - 播放器投币打赏：frontend/src/views/PlayerView.vue
  - 管理后台卡密管理：frontend/src/views/AdminView.vue
==============================================================================
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class UserCoinWallet(Base):
    """
    【用户虚拟金币钱包实体】
    记录用户的金币余额。新注册用户默认自动获赠 50 枚体验金币。
    """
    __tablename__ = "user_coin_wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # 当前可用金币余额（新注册默认初始化 50 枚）
    balance: Mapped[int] = mapped_column(Integer, default=50)
    
    # 历史累计获得的金币总额
    total_earned: Mapped[int] = mapped_column(Integer, default=50)
    
    # 历史累计消费支出的金币总额
    total_spent: Mapped[int] = mapped_column(Integer, default=0)
    
    # 最后一次签到的自然日日期（格式 YYYY-MM-DD，用于防止单日多次签到领币）
    last_sign_in_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User")

class UserCoinTransaction(Base):
    """
    【金币收支明细流水实体】
    记录每一笔金币变动，保证账户资金安全可审计可溯源。
    """
    __tablename__ = "user_coin_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 变动数值：正数表示收入入账（+10），负数表示支出扣款（-2）
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 变动后的瞬时钱包余额快照
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 业务类型枚举：
    # REGISTER_BONUS(注册奖励), SIGN_IN(签到奖励), AD_REWARD(看广告奖励),
    # TIP_VIDEO(短剧投币打赏), VIP_EXCHANGE(兑换VIP卡), ADMIN_ADJUST(管理调整), REDEEM_CODE(卡密兑换)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    
    # 人类可读明细说明：例如“每日签到奖励 +10 币”、“给短剧《逆袭》投币 -2 币”
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 关联业务主键（例如关联的短剧 ID、兑换码 ID 等）
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class VideoCoinTip(Base):
    """
    【短剧投币打赏记录实体】
    记录观众对某部短剧的投币支持。
    每人每部剧上限投 2 枚金币（模仿 B 站硬币机制），投币会实时增加短剧全站热度值。
    """
    __tablename__ = "video_coin_tips"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_coin_tip"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 累计投币枚数（取值 1 或 2）
    tip_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RedemptionCode(Base):
    """
    【兑换卡密口令实体】
    运营管理人员在后台批量生成的一次性兑换口令码，供活动推广、社群营销时发放给观众兑换。
    """
    __tablename__ = "redemption_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 唯一口令码：如 VIP-7D-8F92A 或 COIN-100-XYZ
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    
    # 口令类型：COIN(兑换虚拟金币) 或 VIP(兑换会员天数)
    code_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # 奖励额度：金币数量（如 100 币）或 VIP 天数（如 7 天）
    reward_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 卡密状态：ACTIVE(待核销), USED(已兑换核销), EXPIRED(已过期), REVOKED(已作废)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    
    # 备注说明：如“国庆粉丝福利群专属卡密”
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 创建者管理员 ID
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # 核销使用者 ID 与用户名
    used_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    used_by_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # 核销时间与过期失效时间
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
