"""自动补全服务（P2）。"""

from __future__ import annotations

from typing import List

from app.utils.cache_manager import cache_manager
from app.utils.search_history_manager import search_history_manager

ACADEMIC_TERMS = [
    "machine learning",
    "deep learning",
    "large language model",
    "retrieval augmented generation",
    "computer vision",
    "reinforcement learning",
    "graph neural network",
    "multimodal",
    "federated learning",
]


class AutocompleteService:
    async def get_suggestions(self, user_id: int, prefix: str, limit: int = 10) -> List[str]:
        p = (prefix or "").strip().lower()
        if not p:
            return []

        suggestions: List[str] = []
        seen = set()

        recent = [item["query"] for item in search_history_manager.get_recent(user_id, limit=80)]
        hot = await cache_manager.get_hot_searches(limit=50)

        for source in [recent, hot, ACADEMIC_TERMS]:
            for item in source:
                value = item.strip()
                if value.lower().startswith(p) and value.lower() not in seen:
                    seen.add(value.lower())
                    suggestions.append(value)
                    if len(suggestions) >= limit:
                        return suggestions

        return suggestions


autocomplete_service = AutocompleteService()
