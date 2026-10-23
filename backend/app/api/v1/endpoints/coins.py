import uuid
from datetime import datetime, timedelta, time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.coin import UserCoinWallet, UserCoinTransaction

router = APIRouter()

class ExchangeVipRequest(BaseModel):
    days: int = Field(..., description="兑换天数: 7 或 30")
    cost: Optional[int] = Field(None, description="消耗金币数 (可选)")

def get_or_create_wallet(db: Session, user_id: str) -> UserCoinWallet:
    wallet = db.query(UserCoinWallet).filter(UserCoinWallet.user_id == user_id).first()
    if not wallet:
        wallet = UserCoinWallet(
            id=str(uuid.uuid4()),
            user_id=user_id,
            balance=50,
            total_earned=50,
            total_spent=0,
            last_sign_in_date=None
        )
        db.add(wallet)
        tx = UserCoinTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=50,
            balance_after=50,
            transaction_type="REGISTER_BONUS",
            description="新用户注册奖励金币"
        )
        db.add(tx)
        db.commit()
        db.refresh(wallet)
    return wallet

@router.get("/wallet")
def get_user_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户金币钱包信息与今日任务状态"""
    wallet = get_or_create_wallet(db, current_user.id)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    has_signed_today = (wallet.last_sign_in_date == today_str)

    # 计算今日广告观看次数
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    ad_count_today = db.query(UserCoinTransaction).filter(
        UserCoinTransaction.user_id == current_user.id,
        UserCoinTransaction.transaction_type == "AD_REWARD",
        UserCoinTransaction.created_at >= today_start
    ).count()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
            "total_spent": wallet.total_spent,
            "has_signed_today": has_signed_today,
            "ad_watch_count_today": ad_count_today
        }
    }

@router.get("/transactions")
def get_coin_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户金币变动明细流水"""
    get_or_create_wallet(db, current_user.id)
    query = db.query(UserCoinTransaction).filter(UserCoinTransaction.user_id == current_user.id)
    total = query.count()
    txs = query.order_by(desc(UserCoinTransaction.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": [
                {
                    "id": t.id,
                    "amount": t.amount,
                    "balance_after": t.balance_after,
                    "transaction_type": t.transaction_type,
                    "description": t.description,
                    "reference_id": t.reference_id,
                    "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
                }
                for t in txs
            ]
        }
    }

@router.post("/sign-in")
def daily_sign_in(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """每日签到领金币 (+10枚)"""
    wallet = get_or_create_wallet(db, current_user.id)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Pessimistic row-level lock on the wallet
    wallet = db.query(UserCoinWallet).filter(
        UserCoinWallet.id == wallet.id
    ).execution_options(populate_existing=True).with_for_update().first()

    if wallet.last_sign_in_date == today_str:
        raise HTTPException(status_code=400, detail="今日已签到，请明天再来")

    # Atomic conditional update as secondary defense
    rows_affected = db.query(UserCoinWallet).filter(
        UserCoinWallet.id == wallet.id,
        (UserCoinWallet.last_sign_in_date.is_(None)) | (UserCoinWallet.last_sign_in_date != today_str)
    ).update({
        UserCoinWallet.balance: UserCoinWallet.balance + 10,
        UserCoinWallet.total_earned: UserCoinWallet.total_earned + 10,
        UserCoinWallet.last_sign_in_date: today_str
    }, synchronize_session=False)

    if rows_affected == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="今日已签到，请明天再来")

    db.refresh(wallet)
    reward = 10

    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=reward,
        balance_after=wallet.balance,
        transaction_type="SIGN_IN",
        description="每日签到奖励",
        reference_id=today_str
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)

    return {
        "code": 200,
        "message": "签到成功，获得10枚金币！",
        "data": {
            "balance": wallet.balance,
            "reward": reward,
            "has_signed_today": True
        }
    }

@router.post("/watch-ad")
def watch_ad_reward(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """模拟观看激励视频广告领金币 (+5枚)"""
    wallet = get_or_create_wallet(db, current_user.id)
    reward = 5
    wallet.balance += reward
    wallet.total_earned += reward

    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=reward,
        balance_after=wallet.balance,
        transaction_type="AD_REWARD",
        description="观看激励视频广告奖励"
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)

    return {
        "code": 200,
        "message": "观看广告成功，获得5枚金币！",
        "data": {
            "balance": wallet.balance,
            "reward": reward
        }
    }

@router.post("/exchange-vip")
def exchange_vip(
    req: ExchangeVipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """金币兑换 VIP 会员体验卡 (100币=7天, 200币=30天)"""
    if req.days == 7:
        cost = 100
    elif req.days == 30:
        cost = 200
    else:
        raise HTTPException(status_code=400, detail="仅支持兑换 7 天 (100金币) 或 30 天 (200金币) VIP体验卡")

    wallet = get_or_create_wallet(db, current_user.id)
    if wallet.balance < cost:
        raise HTTPException(status_code=400, detail=f"金币不足，需要 {cost} 金币，当前余额为 {wallet.balance}")

    wallet.balance -= cost
    wallet.total_spent += cost

    now = datetime.utcnow()
    user_obj = db.query(User).filter(User.id == current_user.id).first()
    current_expire = user_obj.vip_expire_at if user_obj else None
    if current_expire and current_expire > now:
        new_expire = current_expire + timedelta(days=req.days)
    else:
        new_expire = now + timedelta(days=req.days)

    if user_obj:
        user_obj.vip_expire_at = new_expire

    tx = UserCoinTransaction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        amount=-cost,
        balance_after=wallet.balance,
        transaction_type="VIP_EXCHANGE",
        description=f"金币兑换 {req.days} 天 VIP 会员"
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    if user_obj:
        db.refresh(user_obj)

    expire_str = user_obj.vip_expire_at.isoformat() if (user_obj and user_obj.vip_expire_at) else ""
    return {
        "code": 200,
        "message": f"成功兑换 {req.days} 天 VIP 会员！",
        "data": {
            "balance": wallet.balance,
            "vip_expire_at": expire_str,
            "days_added": req.days
        }
    }


class RedeemCodeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=64, description="金币或会员兑换码")

@router.post("/redeem")
def redeem_code(
    req: RedeemCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户核销金币兑换码或VIP会员兑换码（行级排他锁原子防重，已兑换的码严禁二次使用）"""
    from app.models.coin import RedemptionCode

    normalized_code = req.code.strip().upper()
    if not normalized_code:
        raise HTTPException(status_code=400, detail="请输入有效的兑换码")

    now = datetime.utcnow()

    # 1. 行级悲观锁锁定该兑换码记录，防止并发重复核销
    voucher = db.query(RedemptionCode).filter(
        RedemptionCode.code == normalized_code
    ).execution_options(populate_existing=True).with_for_update().first()

    if not voucher:
        raise HTTPException(status_code=404, detail="兑换码不存在，请核对后重新输入")

    if voucher.status == "USED":
        raise HTTPException(status_code=400, detail="该兑换码已被使用，无法重复兑换")

    if voucher.status == "REVOKED":
        raise HTTPException(status_code=400, detail="该兑换码已被管理员作废，无法使用")

    if voucher.status == "EXPIRED" or (voucher.expires_at and voucher.expires_at < now):
        if voucher.status != "EXPIRED":
            voucher.status = "EXPIRED"
            db.commit()
        raise HTTPException(status_code=400, detail="该兑换码已过期，无法使用")

    if voucher.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="该兑换码当前状态不可用")

    # 2. 二次原子条件更新防御，确保只有 ACTIVE 状态的兑换码能被置为 USED
    user_display = current_user.nickname or current_user.username
    rows_updated = db.query(RedemptionCode).filter(
        RedemptionCode.id == voucher.id,
        RedemptionCode.status == "ACTIVE"
    ).update({
        RedemptionCode.status: "USED",
        RedemptionCode.used_by: current_user.id,
        RedemptionCode.used_by_username: user_display,
        RedemptionCode.used_at: now
    }, synchronize_session=False)

    if rows_updated == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="该兑换码已被使用，无法重复兑换")

    # 3. 发放对应奖励（金币 或 VIP会员天数）
    wallet = get_or_create_wallet(db, current_user.id)
    user_obj = db.query(User).filter(User.id == current_user.id).with_for_update().first()

    reward_amount = voucher.reward_amount
    code_type = voucher.code_type

    if code_type == "COIN":
        wallet.balance += reward_amount
        wallet.total_earned += reward_amount
        tx = UserCoinTransaction(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            amount=reward_amount,
            balance_after=wallet.balance,
            transaction_type="REDEEM_CODE",
            description=f"使用兑换码 [{normalized_code}] 兑换 {reward_amount} 枚金币",
            reference_id=voucher.id
        )
        db.add(tx)
        reward_msg = f"兑换成功！已为您入账 {reward_amount} 枚金币"
    elif code_type == "VIP":
        current_expire = user_obj.vip_expire_at if user_obj else None
        if current_expire and current_expire > now:
            new_expire = current_expire + timedelta(days=reward_amount)
        else:
            new_expire = now + timedelta(days=reward_amount)
        if user_obj:
            user_obj.vip_expire_at = new_expire
        tx = UserCoinTransaction(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            amount=0,
            balance_after=wallet.balance,
            transaction_type="REDEEM_VIP",
            description=f"使用兑换码 [{normalized_code}] 激活/顺延 {reward_amount} 天 VIP 会员",
            reference_id=voucher.id
        )
        db.add(tx)
        reward_msg = f"兑换成功！已为您激活/延长 {reward_amount} 天 VIP 尊享会员"
    else:
        db.rollback()
        raise HTTPException(status_code=400, detail="未知的兑换码类型")

    db.commit()
    db.refresh(wallet)
    if user_obj:
        db.refresh(user_obj)

    expire_str = user_obj.vip_expire_at.isoformat() if (user_obj and user_obj.vip_expire_at) else ""
    return {
        "code": 200,
        "message": reward_msg,
        "data": {
            "code": normalized_code,
            "code_type": code_type,
            "reward_amount": reward_amount,
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
            "vip_expire_at": expire_str
        }
    }
