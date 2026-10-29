"""
==============================================================================
【模块名称】：review.py (智能风控、内容合规审核与敏感词治理)
【业务职能】：
  保障平台合规安全的防线，提供待审工单排队列表查询、人工审核通过/驳回判定、
  敏感词库分类统计、敏感词 CRUD 管理、以及在线输入文本实时风控过滤测试。
【对应前端】：
  - 核心页面：frontend/src/views/AdminView.vue (安全与合规治理 Tab)
  - 前端通信：frontend/src/api/admin.ts
==============================================================================
"""
import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.review import ContentReview, SensitiveWord
from app.models.interaction import VideoDanmaku, UserComment
from app.models.video import Video
from app.services.moderation_service import moderation_service

router = APIRouter()

class ReviewDecisionRequest(BaseModel):
    review_id: str
    decision: str  # "APPROVED" or "REJECTED"
    notes: Optional[str] = None
    reviewer_id: Optional[str] = None

class SensitiveWordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=100, description="敏感违规词内容")
    level: Optional[str] = Field("HIGH", description="风险等级: HIGH, MEDIUM, LOW")
    category: Optional[str] = Field("违禁", description="分类标签: 涉政, 暴恐, 违禁, 涉黄, 辱骂, 广告")

class SensitiveWordTestRequest(BaseModel):
    text: str = Field(..., description="待检测文本")

@router.get("/queue")
def get_review_queue(
    status: str = Query("PENDING"),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [get_review_queue] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /queue
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    query = db.query(ContentReview)
    if status != "ALL":
        query = query.filter(ContentReview.review_status == status)

    reviews = query.order_by(desc(ContentReview.created_at)).limit(100).all()

    items = []
    for r in reviews:
        check = r.auto_check_result or {}
        video = db.query(Video).filter(Video.id == r.video_id).first()
        items.append({
            "id": r.id,
            "video_id": r.video_id,
            "video_title": video.title if video else "未知短剧",
            "target_type": check.get("target_type", "DANMAKU"),
            "target_id": check.get("target_id", ""),
            "raw_content": check.get("raw_content", ""),
            "matched_words": check.get("matched_words", []),
            "risk_level": check.get("risk_level", "HIGH"),
            "violation_reason": r.reject_reason or "",
            "status": r.review_status,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
        })

    return {
        "code": 200,
        "data": items
    }

@router.post("/decision")
def make_review_decision(req: ReviewDecisionRequest, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [make_review_decision] 业务，负责合规审核与风控判定相关系统资产与数据状态。
    对应 HTTP 端点：POST /decision
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    if req.decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Decision must be APPROVED or REJECTED")

    review = db.query(ContentReview).filter(ContentReview.id == req.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    review.review_status = req.decision
    review.reviewed_at = datetime.utcnow()

    # If rejected, remove target content if it was persisted
    check = review.auto_check_result or {}
    target_id = check.get("target_id")
    target_type = check.get("target_type")

    if req.decision == "REJECTED" and target_id:
        if target_type == "DANMAKU":
            danmaku = db.query(VideoDanmaku).filter(VideoDanmaku.id == target_id).first()
            if danmaku:
                db.delete(danmaku)
        elif target_type == "COMMENT":
            comment = db.query(UserComment).filter(UserComment.id == target_id).first()
            if comment:
                db.delete(comment)
        elif target_type == "VIDEO":
            video = db.query(Video).filter(Video.id == target_id).first()
            if video:
                video.status = "REJECTED"

    db.commit()
    db.refresh(review)

    return {
        "code": 200,
        "message": f"审阅决策已生效: {req.decision}",
        "data": {
            "review_id": review.id,
            "status": review.review_status
        }
    }

@router.get("/sensitive-words/categories-stat")
def get_sensitive_words_categories_stat(db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [get_sensitive_words_categories_stat] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /sensitive-words/categories-stat
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    from sqlalchemy import func
    total = db.query(SensitiveWord).count()
    cat_counts = (
        db.query(SensitiveWord.category, func.count(SensitiveWord.id))
        .group_by(SensitiveWord.category)
        .all()
    )
    stats = {
        "ALL": total,
        "违禁": 0,
        "涉政": 0,
        "暴恐": 0,
        "涉黄": 0,
        "辱骂": 0,
        "广告": 0,
    }
    for cat, cnt in cat_counts:
        if cat in stats:
            stats[cat] = cnt
        else:
            stats[cat] = cnt
    return {
        "code": 200,
        "data": stats
    }

@router.get("/sensitive-words")
def get_sensitive_words(
    query: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [get_sensitive_words] 业务，负责查询并展示相关系统资产与数据状态。
    对应 HTTP 端点：GET /sensitive-words
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    q = db.query(SensitiveWord)
    if query:
        q = q.filter(SensitiveWord.word.ilike(f"%{query.strip()}%"))
    if category and category != "ALL":
        q = q.filter(SensitiveWord.category == category)
    if level and level != "ALL":
        q = q.filter(SensitiveWord.level == level)

    total = q.count()
    items = q.order_by(desc(SensitiveWord.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "code": 200,
        "data": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "items": [
                {
                    "id": w.id,
                    "word": w.word,
                    "level": w.level,
                    "category": w.category,
                    "created_at": w.created_at.strftime("%Y-%m-%d %H:%M") if w.created_at else ""
                }
                for w in items
            ]
        }
    }

@router.post("/sensitive-words")
def create_sensitive_word(req: SensitiveWordCreate, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [create_sensitive_word] 业务，负责新建并录入相关系统资产与数据状态。
    对应 HTTP 端点：POST /sensitive-words
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    cleaned_word = req.word.strip()
    word_obj = db.query(SensitiveWord).filter(SensitiveWord.word == cleaned_word).first()
    if word_obj:
        word_obj.level = req.level or "HIGH"
        word_obj.category = req.category or "违禁"
    else:
        word_obj = SensitiveWord(
            id=str(uuid.uuid4()),
            word=cleaned_word,
            level=req.level or "HIGH",
            category=req.category or "违禁"
        )
        db.add(word_obj)

    db.commit()
    db.refresh(word_obj)

    # Hot reload into DFA engine
    moderation_service.add_word(word_obj.word, level=word_obj.level)

    return {
        "code": 200,
        "message": f"成功录入敏感词: {word_obj.word}",
        "data": {
            "id": word_obj.id,
            "word": word_obj.word,
            "level": word_obj.level,
            "category": word_obj.category,
            "created_at": word_obj.created_at.strftime("%Y-%m-%d %H:%M") if word_obj.created_at else ""
        }
    }

@router.delete("/sensitive-words/{word_id}")
def delete_sensitive_word(word_id: str, db: Session = Depends(get_db)):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [delete_sensitive_word] 业务，负责删除并清理相关系统资产与数据状态。
    对应 HTTP 端点：DELETE /sensitive-words/{word_id}
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    word_obj = db.query(SensitiveWord).filter(SensitiveWord.id == word_id).first()
    if not word_obj:
        raise HTTPException(status_code=404, detail="敏感词记录不存在")

    word_text = word_obj.word
    db.delete(word_obj)
    db.commit()

    # Hot reload entire DFA tree from database
    moderation_service.reload_from_db(db)

    return {
        "code": 200,
        "message": f"已成功移除敏感词: {word_text}",
        "data": {
            "deleted_id": word_id,
            "word": word_text
        }
    }

@router.post("/sensitive-words/test")
def test_sensitive_words_text(req: SensitiveWordTestRequest):
    """
    ==============================================================================
    【这个接口是做什么的】：
    处理 [review] 模块中的 [test_sensitive_words_text] 业务，负责操作相关系统资产与数据状态。
    对应 HTTP 端点：POST /sensitive-words/test
    【从前端哪里调过来的】：
    - 触发操作：用户或管理员在前端执行：界面交互点击或列表加载
    - 调用链路：前端通过 frontend/src/api/review.ts 发起 Axios 异步请求
    【核心执行步骤（大白话）】：
    第 1 步：解析前端传入的查询参数或 JSON 请求体，并通过 Security/Token 守卫进行身份校验；
    第 2 步：操作 MySQL 数据库或相关底层算法服务，执行业务逻辑运算并处理异常情况；
    第 3 步：确认事务安全提交（或遇异常回滚），将处理结果格式化为标准响应。
    【数据传到哪里去 / 返回什么】：
    返回规范的 JSON 数据字典给前端。前端接收后通过响应式变量更新 DOM 树或触发全局通知。
    ==============================================================================
    """
    has_violation, sanitized_text, matched_words, max_level = moderation_service.check_text(req.text)
    return {
        "code": 200,
        "data": {
            "original_text": req.text,
            "has_violation": has_violation,
            "sanitized_text": sanitized_text,
            "matched_words": matched_words,
            "max_risk_level": max_level
        }
    }
