"""相关性评分器（P2）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


class RelevanceScorer:
    def calculate_relevance(self, paper: Dict[str, Any], query_terms: List[str]) -> float:
        if not query_terms:
            return 0.0

        title = (paper.get("title", "") or "").lower()
        abstract = (paper.get("abstract", "") or "").lower()

        title_hits = sum(title.count(t.lower()) for t in query_terms)
        abstract_hits = sum(abstract.count(t.lower()) for t in query_terms)

        base_score = 3.0 * title_hits + 1.5 * abstract_hits

        published = paper.get("published", "")
        decay = 1.0
        if published:
            try:
                year = int(published[:4])
                years = max(0, datetime.utcnow().year - year)
                decay = 0.95 ** years
            except Exception:
                decay = 1.0

        raw = base_score * decay
        return max(0.0, min(1.0, raw / 10.0))

    def score_and_sort(self, papers: List[Dict[str, Any]], query_terms: List[str]) -> List[Dict[str, Any]]:
        scored = []
        for p in papers:
            item = dict(p)
            item["relevance_score"] = round(self.calculate_relevance(item, query_terms), 4)
            scored.append(item)
        return sorted(scored, key=lambda x: x.get("relevance_score", 0.0), reverse=True)


relevance_scorer = RelevanceScorer()
