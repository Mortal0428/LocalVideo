import uuid
import logging
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.review import ContentReview

logger = logging.getLogger(__name__)

class DFAModerationService:
    """
    Deterministic Finite Automaton (DFA) based real-time content moderation engine.
    Performs O(N) multi-pattern matching to detect forbidden words and dispatch auto-reviews.
    """
    def __init__(self):
        self.root: Dict[str, Any] = {}
        self.end_key = "__is_end__"
        self.level_key = "__level__"
        self._init_default_sensitive_dict()

    def _init_default_sensitive_dict(self):
        # Default fallback sensitive words dictionary
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
        """Reload all sensitive words from database and reset DFA tree."""
        self.root = {}
        self._init_default_sensitive_dict()
        if db is None:
            return
        try:
            from app.models.review import SensitiveWord
            words = db.query(SensitiveWord).all()
            for item in words:
                self.add_word(item.word, level=item.level)
            logger.info(f"DFAModerationService reloaded {len(words)} custom sensitive words from DB.")
        except Exception as e:
            logger.warning(f"Could not load custom sensitive words from DB: {e}")

    def add_word(self, word: str, level: str = "HIGH"):
        """Insert a sensitive word into the DFA prefix tree."""
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
        Check input text against DFA tree.
        Returns:
            (has_violation, sanitized_text, matched_words, max_risk_level)
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
                # Sanitize with asterisks
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
        """Create a ContentReview entry in database for reviewer auditing."""
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
        logger.warning(f"[Moderation Intercepted] Video={video_id}, Target={target_type}:{target_id}, Reason={violation_reason}")
        return review_entry

moderation_service = DFAModerationService()
