"""推荐引擎（P1 启动版本）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.engines.search_engine import search_engine
from app.engines.user_profile_manager import user_profile_manager


class RecommendationEngine:
    def _merge_interests(self, explicit: List[str], profile: List[Dict[str, float]], top_k: int = 8) -> List[str]:
        merged: List[str] = []
        seen = set()

        for term in explicit:
            normalized = term.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(term.strip())

        for item in profile:
            keyword = item["keyword"].strip().lower()
            if keyword and keyword not in seen:
                seen.add(keyword)
                merged.append(keyword)

        return merged[:top_k]

    @staticmethod
    def _paper_score(paper: Dict[str, Any], interests: List[str]) -> float:
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        overlap = sum(1 for i in interests if i.lower() in text)
        overlap_score = min(1.0, overlap / max(1, len(interests)))

        pub = paper.get("published", "")
        recency_score = 0.2
        if pub:
            try:
                year = int(pub[:4])
                age = max(0, datetime.utcnow().year - year)
                recency_score = max(0.1, 1.0 - age * 0.08)
            except Exception:
                recency_score = 0.2

        return round(0.7 * overlap_score + 0.3 * recency_score, 4)

    async def generate_recommendations(self, user_id: int, interests: List[str], limit: int = 5) -> Dict[str, Any]:
        for term in interests:
            user_profile_manager.update_interest_from_search(user_id, term)

        profile_interests = user_profile_manager.extract_interests(user_id, top_k=8)
        merged_interests = self._merge_interests(interests, profile_interests, top_k=8)

        safe_limit = max(3, min(10, limit))
        papers, is_fallback, strategy = await search_engine.search_with_fallback(merged_interests, limit=safe_limit)

        scored = []
        for p in papers:
            score = self._paper_score(p, merged_interests)
            item = dict(p)
            item["confidence"] = score
            scored.append(item)

        scored = sorted(scored, key=lambda x: x.get("confidence", 0.0), reverse=True)[:safe_limit]

        return {
            "papers": scored,
            "profile_interests": profile_interests,
            "merged_interests": merged_interests,
            "is_fallback": is_fallback,
            "fallback_strategy": strategy,
        }

    def suggest_interests(self, user_id: int, text: str) -> List[str]:
        base = user_profile_manager.suggest_interests_for_input(text)
        profile = [i["keyword"] for i in user_profile_manager.extract_interests(user_id, top_k=5)]
        merged = []
        seen = set()
        for item in base + profile:
            n = item.strip().lower()
            if n and n not in seen:
                seen.add(n)
                merged.append(item)
        return merged[:8]


recommendation_engine = RecommendationEngine()
