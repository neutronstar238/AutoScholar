"""趋势分析器（P1）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple


class TrendAnalyzer:
    """对论文进行趋势与热度分析。"""

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except Exception:
            return default

    @staticmethod
    def _year_from_published(published: str) -> int:
        if not published:
            return datetime.utcnow().year
        try:
            return int(published[:4])
        except Exception:
            return datetime.utcnow().year

    def _citation_score(self, paper: Dict[str, Any], max_citations: int) -> float:
        citations = self._safe_int(paper.get("citations", 0))
        if max_citations <= 0:
            return 0.0
        return min(1.0, citations / max_citations)

    def _growth_score(self, paper: Dict[str, Any], current_year: int) -> float:
        citations = max(0, self._safe_int(paper.get("citations", 0)))
        year = self._year_from_published(paper.get("published", ""))
        age = max(1, current_year - year + 1)
        yearly = citations / age
        return min(1.0, yearly / 20.0)

    def _recency_score(self, paper: Dict[str, Any], current_year: int) -> float:
        year = self._year_from_published(paper.get("published", ""))
        age = max(0, current_year - year)
        return max(0.1, 1.0 - age * 0.12)

    def analyze_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not papers:
            return []

        current_year = datetime.utcnow().year
        max_citations = max([self._safe_int(p.get("citations", 0)) for p in papers] + [1])

        scored: List[Dict[str, Any]] = []
        for paper in papers:
            citation_score = self._citation_score(paper, max_citations)
            growth_score = self._growth_score(paper, current_year)
            recency_score = self._recency_score(paper, current_year)
            trend_score = round(0.5 * citation_score + 0.3 * growth_score + 0.2 * recency_score, 4)

            item = dict(paper)
            item["trend_score"] = trend_score
            item["is_top_cited"] = citation_score >= 0.9
            scored.append(item)

        return sorted(scored, key=lambda x: x.get("trend_score", 0.0), reverse=True)

    def get_trending_topics(self, papers: List[Dict[str, Any]], top_k: int = 5) -> List[Tuple[str, float]]:
        keyword_scores: Dict[str, float] = {}
        for paper in self.analyze_papers(papers):
            score = paper.get("trend_score", 0.0)
            title = (paper.get("title", "") or "").lower()
            for token in [t.strip() for t in title.split() if len(t.strip()) >= 4]:
                keyword_scores[token] = keyword_scores.get(token, 0.0) + score

        ranked = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


trend_analyzer = TrendAnalyzer()
