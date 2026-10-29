# -*- coding: utf-8 -*-
"""
==============================================================================
【业务服务】：backend/app/services/moderation_service.py
【业务定位】：DFA 确定有限状态机实时敏感词风控拦截引擎（DFAModerationService）
【前端链路对接】：
  1. 页面来源：
     - frontend/src/views/PlayerView.vue（播放器观众发送弹幕、发表评论）
     - frontend/src/views/AdminView.vue（管理后台 -> 敏感词库配置与审核工单审核）
  2. 触发时机与调用链：
     - 用户在播放器底部弹幕栏输入文字并点击【发送】 -> POST /api/v1/danmaku/send；
     - 用户在评论区点击【发表评论】 -> POST /api/v1/comments/create；
     - 路由在入库前调用 moderation_service.check_text(text)；
     - 若命中 HIGH 级别高危词汇：立即拦截抛出 400 错误，并调用 log_violation() 生成 ContentReview 人工审核工单；
     - 若命中 MEDIUM 级别中危词汇：自动进行星号（***）脱敏替换后正常放行入库；
     - 管理员在 AdminView.vue 新增敏感词后调用 POST /api/v1/review/sensitive-words/reload，触发 reload_from_db() 热重载。
【核心功能】：
  1. O(N) 极速前缀树匹配：基于 DFA 算法构建敏感词 Trie 字典树，单次文本检测耗时始终只与输入文本长度成正比，微秒级响应；
  2. 分级拦截与脱敏：HIGH 级直接拦截，MEDIUM 级星号替换；
  3. 动态热重载（reload_from_db）：管理员在后台增删敏感词后即刻生效，无需重启服务；
  4. 违规工单入库（log_violation）：自动写入 content_reviews 表供审核员查验。
==============================================================================
"""

import uuid
import logging
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.review import ContentReview

logger = logging.getLogger(__name__)


class DFAModerationService:
    """
    【DFA 确定有限状态机敏感词风控引擎】
    基于字典树（Trie）实现多模式字符串高速匹配算法，
    能够在毫秒级内完成成千上万敏感词的检测、分级判定与脱敏替换。
    """
    def __init__(self):
        # DFA 字典树根节点
        self.root: Dict[str, Any] = {}
        # 词尾标识键名（布尔值表示该节点为一个敏感词的终点）
        self.end_key = "__is_end__"
        # 风险等级标识键名（"HIGH" 或 "MEDIUM"）
        self.level_key = "__level__"
        # 初始化默认预置敏感词
        self._init_default_sensitive_dict()

    def _init_default_sensitive_dict(self):
        """初始化系统默认内置的高风险与中风险词库"""
        high_risk = [
            "违禁", "涉赌", "诈骗", "洗钱", "反动", "暴恐",
            "毒品", "代孕", "暗网", "政治献金", "敏感词测试", "色情直播"
        ]
        medium_risk = [
            "傻逼", "脑残", "滚蛋", "弱智", "垃圾玩意", "骗子"
        ]
        for w in high_risk:
            self.add_word(w, level="HIGH")
        for w in medium_risk:
            self.add_word(w, level="MEDIUM")

    def reload_from_db(self, db: Optional[Session] = None):
        """
        从数据库的 `sensitive_words` 表全量重新加载敏感词，并在内存中重建 DFA 字典树。
        管理员在后台添加或删除敏感词后调用此方法，实现零停机热更新。
        
        【参数说明】：
        - db (Optional[Session]): 数据库连接会话。若为空则仅保留默认内置词库。
        """
        self.root = {}
        self._init_default_sensitive_dict()
        if db is None:
            return
        try:
            from app.models.review import SensitiveWord
            words = db.query(SensitiveWord).all()
            for item in words:
                self.add_word(item.word, level=item.level)
            logger.info(f"DFAModerationService 成功从数据库热重载了 {len(words)} 条自定义敏感词")
        except Exception as e:
            logger.warning(f"从数据库加载自定义敏感词异常: {e}")

    def add_word(self, word: str, level: str = "HIGH"):
        """
        向 DFA 前缀字典树中插入一个敏感词及其对应的风险等级。
        
        【参数说明】：
        - word (str): 敏感词文本（如“违禁”）。
        - level (str, 默认 "HIGH"): 风险等级，"HIGH"（直接拦截）或 "MEDIUM"（脱敏替换）。
        """
        word = word.strip().lower()
        if not word:
            return
        node = self.root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node[self.end_key] = True
        node[self.level_key] = level

    def check_text(self, text: str) -> Tuple[bool, str, List[str], str]:
        """
        使用 DFA 字典树对输入文本进行全量敏感词扫描与过滤脱敏。
        
        【参数大白话详解】：
        - text (str): 观众输入的弹幕内容、评论内容或短剧标题。
        
        【返回值元组 (Tuple) 4 个字段大白话详解】：
        - has_violation (bool): 是否命中了任何违规词汇（True 表示有违规，False 表示安全）。
        - sanitized_text (str): 脱敏后的安全文本（命中的敏感词被替换为等长星号，如“这个***真难看”）。
        - matched_words (List[str]): 命中的敏感词列表（如 ["脑残", "骗子"]）。
        - max_risk_level (str): 命中的最高风险级别（"HIGH", "MEDIUM" 或 "NONE"）。
        """
        if not text:
            return False, "", [], "NONE"

        text_lower = text.lower()
        n = len(text)
        matched_words = []
        max_level = "NONE"
        sanitized_chars = list(text)

        i = 0
        while i < n:
            curr_node = self.root
            match_len = 0
            found_word = ""
            found_level = "NONE"

            # 沿着 DFA 树向下深探匹配
            for j in range(i, n):
                char = text_lower[j]
                if char not in curr_node:
                    break
                curr_node = curr_node[char]
                if curr_node.get(self.end_key):
                    match_len = j - i + 1
                    found_word = text[i:j + 1]
                    found_level = curr_node.get(self.level_key, "HIGH")

            if match_len > 0:
                matched_words.append(found_word)
                if found_level == "HIGH" or max_level != "HIGH":
                    max_level = found_level
                # 用星号替换敏感词
                for k in range(i, i + match_len):
                    sanitized_chars[k] = "*"
                i += match_len
            else:
                i += 1

        has_violation = len(matched_words) > 0
        sanitized_text = "".join(sanitized_chars)
        return has_violation, sanitized_text, matched_words, max_level

    def log_violation(
        self,
        db: Session,
        video_id: str,
        target_type: str,
        target_id: str,
        content: str,
        matched_words: List[str],
        risk_level: str
    ) -> ContentReview:
        """
        当检测到违规时，在数据库 `content_reviews` 表中生成一条审核工单记录，供后台审核员复核。
        
        【参数大白话详解】：
        - db (Session): 数据库会话。
        - video_id (str): 关联的短剧 ID。
        - target_type (str): 违规目标类型（例如："COMMENT" 评论，"DANMAKU" 弹幕，"VIDEO_TITLE" 剧名）。
        - target_id (str): 违规对象的具体主键 ID。
        - content (str): 违规的原始文本内容。
        - matched_words (List[str]): 命中的敏感词清单。
        - risk_level (str): 风险评级（"HIGH" 或 "MEDIUM"）。
        
        【返回值说明】：
        - ContentReview: 数据库新插入的审核工单记录对象。
        """
        violation_reason = f"触发敏感词: {', '.join(matched_words)} (原文: '{content}')"
        review_entry = ContentReview(
            id=str(uuid.uuid4()),
            video_id=video_id,
            review_status="PENDING",
            auto_check_result={
                "target_type": target_type,
                "target_id": target_id,
                "matched_words": matched_words,
                "risk_level": risk_level,
                "raw_content": content
            },
            reject_reason=violation_reason
        )
        db.add(review_entry)
        db.commit()
        db.refresh(review_entry)
        logger.warning(f"[风控拦截] 短剧={video_id}, 目标={target_type}:{target_id}, 原因={violation_reason}")
        return review_entry


# 全局单例敏感词风控引擎
moderation_service = DFAModerationService()
