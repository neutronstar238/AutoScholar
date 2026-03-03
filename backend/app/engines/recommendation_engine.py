"""推荐引擎（P1/P2）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from loguru import logger

from app.engines.search_engine import search_engine
from app.engines.trend_analyzer import trend_analyzer
from app.engines.user_profile_manager import user_profile_manager
from app.utils.feedback_collector import feedback_collector
from app.utils.trending_manager import trending_manager


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

    @staticmethod
    def _is_survey_paper(paper: Dict[str, Any]) -> bool:
        title = (paper.get("title", "") or "").lower()
        return any(k in title for k in ["survey", "review", "overview", "综述"])

    async def generate_recommendations(self, user_id: int, interests: List[str], limit: int = 5) -> Dict[str, Any]:
        for term in interests:
            user_profile_manager.update_interest_from_search(user_id, term)

        profile_interests = user_profile_manager.extract_interests(user_id, top_k=8)
        merged_interests = self._merge_interests(interests, profile_interests, top_k=8)

        safe_limit = max(3, min(10, limit))
        papers, is_fallback, strategy = await search_engine.search_with_fallback(merged_interests, limit=safe_limit)

        trend_scored = trend_analyzer.analyze_papers(papers)
        scored = []
        for p in trend_scored:
            relevance_score = self._paper_score(p, merged_interests)
            trend_score = p.get("trend_score", 0.0)
            item = dict(p)
            item["confidence"] = round(0.65 * relevance_score + 0.35 * trend_score, 4)
            scored.append(item)

        feedback_collector.record_view(user_id)
        scored = sorted(scored, key=lambda x: x.get("confidence", 0.0), reverse=True)[:safe_limit]

        # 更新热门论文表（异步，不阻塞响应）
        await self._update_trending_papers(scored)

        return {
            "papers": scored,
            "profile_interests": profile_interests,
            "merged_interests": merged_interests,
            "is_fallback": is_fallback,
            "fallback_strategy": strategy,
        }

    async def _update_trending_papers(self, papers: List[Dict[str, Any]]) -> None:
        """更新热门论文表。
        
        将推荐的论文记录到TrendingPaper表中，增加推荐计数。
        
        Args:
            papers: 推荐的论文列表
        """
        for paper in papers:
            try:
                paper_id = paper.get("id", "")
                if not paper_id:
                    continue
                
                # 提取分类（取第一个）
                categories = paper.get("categories", [])
                category = categories[0] if categories else "general"
                
                # 提取作者（转换为逗号分隔的字符串）
                authors = paper.get("authors", [])
                authors_str = ", ".join(authors) if isinstance(authors, list) else str(authors)
                
                await trending_manager.update_trending_paper(
                    paper_id=paper_id,
                    title=paper.get("title", ""),
                    abstract=paper.get("abstract", ""),
                    url=paper.get("url", ""),
                    authors=authors_str,
                    category=category
                )
            except Exception as e:
                # 不阻塞推荐流程，只记录错误
                logger.warning(f"更新热门论文失败 paper_id={paper.get('id')}: {e}")

    def generate_learning_path(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """将推荐论文组织为 3-5 阶段学习路径。"""
        if not papers:
            return {"stages": [], "total_papers": 0}

        limited = papers[:15]
        sorted_papers = sorted(limited, key=lambda x: x.get("published", "9999-12-31"))
        survey = [p for p in sorted_papers if self._is_survey_paper(p)]
        non_survey = [p for p in sorted_papers if not self._is_survey_paper(p)]
        ordered = survey + non_survey

        stage_count = 3
        if len(ordered) >= 9:
            stage_count = 4
        if len(ordered) >= 13:
            stage_count = 5

        chunks: List[List[Dict[str, Any]]] = [[] for _ in range(stage_count)]
        for idx, paper in enumerate(ordered):
            chunks[min(stage_count - 1, idx * stage_count // max(1, len(ordered)))].append(paper)

        stage_names = ["基础构建", "核心方法", "进阶专题", "前沿探索", "研究产出"]
        stages = []
        for i, stage_papers in enumerate(chunks):
            if not stage_papers:
                continue
            stages.append(
                {
                    "stage": i + 1,
                    "name": stage_names[i],
                    "goal": f"完成{stage_names[i]}阶段并形成阶段笔记",
                    "papers": stage_papers,
                }
            )

        return {"stages": stages, "total_papers": len(ordered)}

    def find_cross_domain_opportunities(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别跨领域研究机会（优先近24个月）。"""
        opportunities: List[Dict[str, Any]] = []
        current_year = datetime.utcnow().year

        for paper in papers:
            categories = list({c.lower() for c in (paper.get("categories") or []) if c})
            if len(categories) < 2:
                continue

            published = paper.get("published", "")
            try:
                year = int(published[:4])
            except Exception:
                year = current_year
            if current_year - year > 2:
                continue

            opportunities.append(
                {
                    "paper_id": paper.get("id"),
                    "title": paper.get("title"),
                    "domains": categories[:3],
                    "connection": f"该论文连接了 {categories[0]} 与 {categories[1]}，可探索跨领域迁移与联合建模。",
                }
            )

        return opportunities[:10]

    def record_recommendation_feedback(self, user_id: int, paper: Dict[str, Any], feedback: str) -> Dict[str, float]:
        feedback_collector.record_feedback(user_id, feedback)
        user_profile_manager.update_interest_from_reading(
            user_id=user_id,
            title=paper.get("title", ""),
            abstract=paper.get("abstract", ""),
            feedback=feedback,
        )
        return feedback_collector.calculate_metrics(user_id)

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
