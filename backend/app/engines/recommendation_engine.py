"""推荐引擎核心逻辑。

负责协调各组件生成研究方向推荐，支持四种推荐模式：
1. 用户主动输入兴趣
2. 用户画像辅助推荐
3. 纯画像推荐
4. 通用热门推荐

Requirements: 5.1, 5.3
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from app.engines.search_engine import search_engine
from app.engines.trend_analyzer import trend_analyzer
from app.engines.user_profile_manager import user_profile_manager, InterestSuggestion
from app.utils.feedback_collector import feedback_collector
from app.utils.trending_manager import trending_manager


class RecommendationEngine:
    """推荐引擎核心类。
    
    协调各组件生成研究方向推荐，支持四种模式：
    - 模式1：用户主动输入兴趣
    - 模式2：用户画像辅助推荐  
    - 模式3：纯画像推荐
    - 模式4：通用热门推荐
    """
    
    def __init__(self):
        self.min_results = 3
        self.max_results = 10
    
    async def generate_recommendations(
        self,
        interests: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """生成研究方向推荐。
        
        实现四种推荐模式的核心逻辑：
        1. 用户主动输入：使用提供的兴趣关键词
        2. 用户画像辅助：用户提供部分兴趣，系统从用户画像补充
        3. 纯画像推荐：用户未提供兴趣但有user_id，系统从用户画像提取
        4. 通用推荐：新用户无输入无画像，返回通用热门推荐
        
        Args:
            interests: 用户研究兴趣关键词列表（可选）
            user_id: 用户ID（用于个性化推荐和自动提取兴趣）
            limit: 推荐数量（3-10之间）
            
        Returns:
            推荐结果字典，包含推荐内容、论文列表、置信度等
            
        Validates: Requirements 5.1, 5.3
        """
        try:
            # 限制推荐数量在合理范围内
            safe_limit = max(self.min_results, min(self.max_results, limit))
            
            # 阶段1：兴趣获取（四种模式）
            final_interests, mode, profile_interests = await self._determine_interests_mode(
                interests, user_id
            )
            
            logger.info(f"推荐模式: {mode}, 最终兴趣: {final_interests}")
            
            # 阶段2：论文检索（带降级策略）
            papers, is_fallback, strategy = await search_engine.search_with_fallback(
                final_interests, limit=safe_limit
            )
            
            # 阶段3：评分排序（如果有足够论文）
            if papers:
                papers = await self._score_and_rank_papers(papers, final_interests, user_id)
            
            # 阶段4：个性化调整（如果有用户画像）
            if user_id and profile_interests:
                papers = await self._apply_personalization(papers, profile_interests)
            
            # 阶段5：更新用户画像（如果有用户ID）
            if user_id:
                await self._update_user_profile(user_id, final_interests, papers)
            
            # 阶段6：更新热门论文表
            if papers:
                await self._update_trending_papers(papers)
            
            # 计算整体置信度
            confidence = self._calculate_overall_confidence(papers, is_fallback, mode)
            
            return {
                "papers": papers,
                "profile_interests": [interest.to_dict() for interest in profile_interests],
                "merged_interests": final_interests,
                "is_fallback": is_fallback,
                "fallback_strategy": strategy,
                "mode": mode,
                "confidence": confidence,
                "source": "primary" if not is_fallback else "fallback"
            }
            
        except Exception as e:
            logger.error(f"生成推荐失败: {e}")
            # 返回空结果而不是抛出异常
            return {
                "papers": [],
                "profile_interests": [],
                "merged_interests": interests or [],
                "is_fallback": True,
                "fallback_strategy": "error_fallback",
                "mode": "error",
                "confidence": 0.0,
                "source": "error"
            }
    
    async def _determine_interests_mode(
        self,
        interests: Optional[List[str]],
        user_id: Optional[int]
    ) -> tuple[List[str], str, List[Any]]:
        """确定推荐模式并获取最终兴趣列表。
        
        Returns:
            (final_interests, mode, profile_interests)
        """
        profile_interests = []
        
        # 如果有用户ID，尝试获取用户画像
        if user_id:
            try:
                profile_interests = await user_profile_manager.extract_interests(
                    user_id, limit=10
                )
            except Exception as e:
                logger.warning(f"获取用户画像失败: {e}")
        
        # 模式1：用户主动输入兴趣
        if interests and len(interests) > 0:
            # 过滤空字符串
            clean_interests = [i.strip() for i in interests if i and i.strip()]
            if clean_interests:
                if profile_interests:
                    # 模式2：用户画像辅助推荐
                    profile_keywords = [interest.keyword for interest in profile_interests[:5]]
                    merged = self._merge_interests(clean_interests, profile_keywords)
                    return merged, "user_input_with_profile", profile_interests
                else:
                    # 纯用户输入
                    return clean_interests, "user_input_only", profile_interests
        
        # 模式3：纯画像推荐
        if user_id and profile_interests:
            profile_keywords = [interest.keyword for interest in profile_interests[:8]]
            return profile_keywords, "profile_only", profile_interests
        
        # 模式4：通用热门推荐
        trending_keywords = [
            "machine learning",
            "deep learning", 
            "artificial intelligence",
            "computer vision",
            "natural language processing"
        ]
        return trending_keywords, "general_trending", profile_interests
    
    def _merge_interests(
        self, 
        user_interests: List[str], 
        profile_interests: List[str],
        max_total: int = 8
    ) -> List[str]:
        """合并用户输入兴趣和画像兴趣。
        
        优先用户输入，然后补充画像兴趣，避免重复。
        """
        merged = []
        seen = set()
        
        # 优先添加用户输入的兴趣
        for interest in user_interests:
            normalized = interest.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(interest.strip())
        
        # 补充画像兴趣
        for interest in profile_interests:
            normalized = interest.lower().strip()
            if normalized and normalized not in seen and len(merged) < max_total:
                seen.add(normalized)
                merged.append(interest.strip())
        
        return merged[:max_total]
    
    async def _score_and_rank_papers(
        self,
        papers: List[Dict[str, Any]],
        interests: List[str],
        user_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """评分和排序论文。
        
        如果有足够论文，调用趋势分析器计算评分。
        """
        if not papers:
            return papers
        
        try:
            # 调用趋势分析器计算趋势评分
            trend_scored = trend_analyzer.analyze_papers(papers)
            
            # 计算相关性评分并合并
            scored_papers = []
            for paper in trend_scored:
                relevance_score = self._calculate_relevance_score(paper, interests)
                trend_score = paper.get("trend_score", 0.0)
                
                # 综合评分：相关性65% + 趋势35%
                final_score = 0.65 * relevance_score + 0.35 * trend_score
                
                paper_copy = dict(paper)
                paper_copy["confidence"] = round(final_score, 4)
                paper_copy["relevance_score"] = round(relevance_score, 4)
                scored_papers.append(paper_copy)
            
            # 按综合评分排序
            return sorted(scored_papers, key=lambda x: x.get("confidence", 0.0), reverse=True)
            
        except Exception as e:
            logger.warning(f"评分排序失败，使用简单相关性排序: {e}")
            # 降级到简单相关性排序
            for paper in papers:
                paper["confidence"] = self._calculate_relevance_score(paper, interests)
            return sorted(papers, key=lambda x: x.get("confidence", 0.0), reverse=True)
    
    def _calculate_relevance_score(
        self, 
        paper: Dict[str, Any], 
        interests: List[str]
    ) -> float:
        """计算论文与兴趣的相关性评分。
        
        基于标题和摘要中关键词匹配度，结合时间衰减。
        """
        if not interests:
            return 0.5
        
        # 获取论文文本
        title = (paper.get("title", "") or "").lower()
        abstract = (paper.get("abstract", "") or "").lower()
        
        # 计算关键词匹配度
        matches = 0
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in title:
                matches += 2  # 标题匹配权重更高
            elif interest_lower in abstract:
                matches += 1  # 摘要匹配
        
        # 标准化匹配分数
        max_possible_matches = len(interests) * 2  # 假设所有关键词都在标题中匹配
        match_score = min(1.0, matches / max_possible_matches) if max_possible_matches > 0 else 0.0
        
        # 计算时间衰减因子
        recency_score = self._calculate_recency_score(paper.get("published", ""))
        
        # 综合评分：匹配度70% + 时间因子30%
        return 0.7 * match_score + 0.3 * recency_score
    
    def _calculate_recency_score(self, published_date: str) -> float:
        """计算论文时间新近度评分。
        
        最近的论文得分更高，按年衰减。
        """
        if not published_date:
            return 0.2  # 默认分数
        
        try:
            # 提取年份
            year = int(published_date[:4])
            current_year = datetime.utcnow().year
            age_years = max(0, current_year - year)
            
            # 指数衰减：每年衰减8%
            return max(0.1, 1.0 - age_years * 0.08)
            
        except (ValueError, IndexError):
            return 0.2  # 解析失败时的默认分数
    
    async def _apply_personalization(
        self,
        papers: List[Dict[str, Any]],
        profile_interests: List[Any]
    ) -> List[Dict[str, Any]]:
        """根据用户画像调整推荐排序。
        
        提升匹配用户兴趣的论文排序。
        """
        if not profile_interests:
            return papers
        
        try:
            # 提取用户兴趣关键词和权重
            interest_weights = {}
            for interest in profile_interests:
                interest_weights[interest.keyword.lower()] = interest.weight
            
            # 调整论文评分
            for paper in papers:
                title = (paper.get("title", "") or "").lower()
                abstract = (paper.get("abstract", "") or "").lower()
                
                # 计算个性化加权
                personalization_boost = 0.0
                for keyword, weight in interest_weights.items():
                    if keyword in title:
                        personalization_boost += weight * 0.3  # 标题匹配
                    elif keyword in abstract:
                        personalization_boost += weight * 0.1  # 摘要匹配
                
                # 应用个性化提升（最多提升20%）
                current_confidence = paper.get("confidence", 0.0)
                boost = min(0.2, personalization_boost)
                paper["confidence"] = round(current_confidence + boost, 4)
                paper["personalization_boost"] = round(boost, 4)
            
            # 重新排序
            return sorted(papers, key=lambda x: x.get("confidence", 0.0), reverse=True)
            
        except Exception as e:
            logger.warning(f"个性化调整失败: {e}")
            return papers
    
    async def _update_user_profile(
        self,
        user_id: int,
        interests: List[str],
        papers: List[Dict[str, Any]]
    ) -> None:
        """更新用户画像。
        
        从搜索行为和推荐结果更新用户兴趣。
        """
        try:
            # 更新搜索兴趣
            for interest in interests:
                await user_profile_manager.update_interest_from_search(user_id, interest)
            
            # 记录查看行为（用于反馈收集）
            feedback_collector.record_view(user_id)
            
        except Exception as e:
            logger.warning(f"更新用户画像失败: {e}")
    
    def _calculate_overall_confidence(
        self,
        papers: List[Dict[str, Any]],
        is_fallback: bool,
        mode: str
    ) -> float:
        """计算整体推荐置信度。"""
        if not papers:
            return 0.0
        
        # 基础置信度：论文平均置信度
        paper_confidences = [p.get("confidence", 0.0) for p in papers]
        avg_confidence = sum(paper_confidences) / len(paper_confidences)
        
        # 模式调整
        mode_multiplier = {
            "user_input_only": 1.0,
            "user_input_with_profile": 1.1,  # 画像辅助提升置信度
            "profile_only": 0.9,  # 纯画像稍微降低
            "general_trending": 0.7,  # 通用推荐置信度较低
            "error": 0.0
        }.get(mode, 0.8)
        
        # 降级调整
        fallback_multiplier = 0.8 if is_fallback else 1.0
        
        final_confidence = avg_confidence * mode_multiplier * fallback_multiplier
        return round(min(1.0, max(0.0, final_confidence)), 4)
    
    async def suggest_interests(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[InterestSuggestion]:
        """基于用户画像推荐研究兴趣关键词。
        
        从用户的搜索历史、阅读记录、反馈行为中提取和推荐兴趣关键词。
        
        Args:
            user_id: 用户ID
            limit: 推荐的兴趣关键词数量
            
        Returns:
            推荐的兴趣关键词列表，按权重排序
        """
        try:
            # 直接调用用户画像管理器的建议方法
            suggestions = await user_profile_manager.suggest_interests_for_input(
                user_id=user_id,
                current_input="",  # 空输入，获取所有建议
                limit=limit
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"获取兴趣建议失败: {e}")
            return []
    
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

    @staticmethod
    def _is_survey_paper(paper: Dict[str, Any]) -> bool:
        """判断是否为综述论文。"""
        title = (paper.get("title", "") or "").lower()
        return any(k in title for k in ["survey", "review", "overview", "综述"])

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

    async def record_recommendation_feedback(
        self, 
        user_id: int, 
        paper: Dict[str, Any], 
        feedback: str
    ) -> Dict[str, float]:
        """记录推荐反馈并更新用户画像。"""
        try:
            # 记录反馈
            feedback_collector.record_feedback(user_id, feedback)
            
            # 从论文中提取关键词并更新用户兴趣
            title = paper.get("title", "")
            categories = paper.get("categories", [])
            
            # 从标题提取关键词
            title_keywords = user_profile_manager._tokenize(title)
            all_keywords = title_keywords + categories
            
            # 更新用户兴趣权重
            await user_profile_manager.update_interest_from_feedback(
                user_id=user_id,
                keywords=all_keywords,
                feedback_type=feedback
            )
            
            # 计算并返回指标
            return feedback_collector.calculate_metrics(user_id)
            
        except Exception as e:
            logger.error(f"记录推荐反馈失败: {e}")
            return {"click_through_rate": 0.0, "helpfulness_ratio": 0.0}


# 全局实例
recommendation_engine = RecommendationEngine()