"""搜索历史管理（P2）。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List


class SearchHistoryManager:
    def __init__(self):
        self._history: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    def record(self, user_id: int, query: str) -> None:
        if not query.strip():
            return
        self._history[user_id].append({"query": query.strip(), "timestamp": datetime.utcnow().isoformat()})
        self.cleanup(user_id=user_id)

    def get_recent(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        self.cleanup(user_id=user_id)
        return list(reversed(self._history[user_id][-limit:]))

    def clear(self, user_id: int) -> int:
        removed = len(self._history[user_id])
        self._history[user_id] = []
        return removed

    def cleanup(self, user_id: int | None = None, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        removed = 0

        user_ids = [user_id] if user_id is not None else list(self._history.keys())
        for uid in user_ids:
            keep = []
            for item in self._history[uid]:
                try:
                    ts = datetime.fromisoformat(item["timestamp"])
                except Exception:
                    ts = datetime.utcnow()
                if ts >= cutoff:
                    keep.append(item)
                else:
                    removed += 1
            self._history[uid] = keep

        return removed


search_history_manager = SearchHistoryManager()
