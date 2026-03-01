"""用户画像管理器（P1）。"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


class UserProfileManager:
    """管理用户兴趣画像与搜索历史（当前使用内存存储，后续可接DB）。"""

    def __init__(self, max_keywords: int = 30):
        self.max_keywords = max_keywords
        self._interest_weights: Dict[int, Dict[str, float]] = defaultdict(dict)
        self._search_history: Dict[int, List[Tuple[str, datetime]]] = defaultdict(list)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        if not text:
            return []
        tokens = re.split(r"[^\w\u4e00-\u9fff]+", text.lower())
        return [t for t in tokens if len(t) >= 2]

    def _trim_keywords(self, user_id: int) -> None:
        items = sorted(self._interest_weights[user_id].items(), key=lambda x: x[1], reverse=True)
        self._interest_weights[user_id] = dict(items[: self.max_keywords])

    def extract_interests(self, user_id: int, top_k: int = 8) -> List[Dict[str, float]]:
        interests = sorted(self._interest_weights[user_id].items(), key=lambda x: x[1], reverse=True)
        return [{"keyword": k, "weight": round(w, 4)} for k, w in interests[:top_k]]

    def suggest_interests_for_input(self, text: str, top_k: int = 5) -> List[str]:
        weights: Dict[str, float] = {}
        for tok in self._tokenize(text):
            weights[tok] = weights.get(tok, 0.0) + 1.0
        ranked = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        return [k for k, _ in ranked[:top_k]]

    def update_interest_from_search(self, user_id: int, query: str) -> None:
        self._search_history[user_id].append((query, datetime.utcnow()))
        for tok in self._tokenize(query):
            self._interest_weights[user_id][tok] = self._interest_weights[user_id].get(tok, 0.0) + 1.0
        self._trim_keywords(user_id)

    def update_interest_from_reading(self, user_id: int, title: str, abstract: str = "", feedback: str = "view") -> None:
        feedback_gain = {
            "helpful": 1.5,
            "view": 1.0,
            "ignore": 0.7,
            "not_helpful": 0.4,
        }.get(feedback, 1.0)

        text = f"{title} {abstract}"
        for tok in self._tokenize(text):
            self._interest_weights[user_id][tok] = self._interest_weights[user_id].get(tok, 0.0) + 0.3 * feedback_gain
        self._trim_keywords(user_id)


user_profile_manager = UserProfileManager()
