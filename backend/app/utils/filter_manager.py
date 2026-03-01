"""高级过滤管理器（P2）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


class FilterManager:
    @staticmethod
    def _in_date_range(paper_date: str, start_date: Optional[str], end_date: Optional[str]) -> bool:
        if not paper_date:
            return True
        try:
            pd = datetime.fromisoformat(paper_date[:10])
        except Exception:
            return True

        if start_date:
            try:
                if pd < datetime.fromisoformat(start_date[:10]):
                    return False
            except Exception:
                pass
        if end_date:
            try:
                if pd > datetime.fromisoformat(end_date[:10]):
                    return False
            except Exception:
                pass
        return True

    def apply_filters(
        self,
        papers: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        author: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filtered: List[Dict[str, Any]] = []
        author_l = (author or "").strip().lower()
        category_l = (category or "").strip().lower()

        for paper in papers:
            if not self._in_date_range(paper.get("published", ""), start_date, end_date):
                continue

            if author_l:
                authors = [a.lower() for a in (paper.get("authors") or [])]
                if not any(author_l in a for a in authors):
                    continue

            if category_l:
                cats = [c.lower() for c in (paper.get("categories") or [])]
                primary = (paper.get("category") or "").lower()
                if category_l not in cats and category_l not in primary:
                    continue

            filtered.append(paper)

        return filtered


filter_manager = FilterManager()
