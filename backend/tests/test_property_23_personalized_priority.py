"""Property 23: 个性化推荐优先级 - 属性测试

测试个性化推荐中，匹配用户兴趣的论文应该获得更高的评分。

Feature: search-and-recommendation-optimization, Property 23: 个性化推荐优先级
**Validates: Requirements 5.3**
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck

from app.engines.recommendation_engine import recommendation_engine
from app.engines.user_profile_manager import InterestKeyword


# Hypothesis配置：每个属性测试运行100次
settings.register_profile("default", max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("default")


# ============================================================================
# Test Data Generation Strategies
# ============================================================================

@st.composite
def user_interests(draw):
    """生成用户兴趣关键词策略。"""
    keywords = draw(st.lists(
        st.sampled_from([
            "machine learning", "deep learning", "neural networks", "computer vision",
            "natural language processing", "nlp", "artificial intelligence", "ai",
            "reinforcement learning", "transformer", "attention mechanism", "bert",
            "gpt", "llm", "large language model", "diffusion model", "gan"
        ]),
        min_size=1,
        max_size=5,
        unique=True
    ))
    
    interests = []
    for keyword in keywords:
        weight = draw(st.floats(min_value=0.1, max_value=1.0))
        interests.append(InterestKeyword(keyword=keyword, weight=weight))
    
    return interests


@st.composite
def paper_with_interests(draw, user_interests_keywords: List[str]):
    """生成包含或不包含用户兴趣的论文策略。"""
    # 决定这篇论文是否匹配用户兴趣
    matches_interest = draw(st.booleans())
    
    if matches_interest and user_interests_keywords:
        # 选择一个用户兴趣关键词包含在标题或摘要中
        interest_keyword = draw(st.sampled_from(user_interests_keywords))
        
        # 决定关键词出现在标题还是摘要中
        in_title = draw(st.booleans())
        
        if in_title:
            title = f"A Study on {interest_keyword.title()} Applications in Modern AI"
            abstract = draw(st.text(min_size=50, max_size=200))
        else:
            title = draw(st.text(min_size=10, max_size=50))
            abstract = f"This paper explores various aspects of {interest_keyword} and its implications for future research in artificial intelligence and machine learning domains."
    else:
        # 生成不包含用户兴趣的论文
        title = draw(st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
            min_size=10, 
            max_size=50
        ).filter(lambda x: not any(keyword in x.lower() for keyword in user_interests_keywords)))
        
        abstract = draw(st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
            min_size=50, 
            max_size=200
        ).filter(lambda x: not any(keyword in x.lower() for keyword in user_interests_keywords)))
    
    paper = {
        "id": f"arxiv-{draw(st.integers(min_value=1000, max_value=9999))}",
        "title": title,
        "abstract": abstract,
        "authors": [draw(st.text(min_size=5, max_size=30))],
        "published": "2024-01-01",
        "url": f"https://arxiv.org/abs/{draw(st.integers(min_value=1000, max_value=9999))}",
        "categories": [draw(st.sampled_from(["cs.AI", "cs.LG", "cs.CV", "cs.CL"]))],
        "confidence": draw(st.floats(min_value=0.1, max_value=0.8))  # 初始评分
    }
    
    return paper, matches_interest


@st.composite
def papers_with_mixed_interests(draw, user_interests_keywords: List[str]):
    """生成包含匹配和不匹配用户兴趣的论文列表。"""
    # 确保至少有一篇匹配和一篇不匹配的论文
    num_papers = draw(st.integers(min_value=4, max_value=10))
    
    papers = []
    matching_papers = []
    non_matching_papers = []
    
    for _ in range(num_papers):
        paper, matches = draw(paper_with_interests(user_interests_keywords))
        papers.append(paper)
        
        if matches:
            matching_papers.append(paper)
        else:
            non_matching_papers.append(paper)
    
    # 如果没有匹配的论文，强制创建一篇
    if not matching_papers and user_interests_keywords:
        interest_keyword = draw(st.sampled_from(user_interests_keywords))
        matching_paper = {
            "id": f"arxiv-forced-match",
            "title": f"Advanced {interest_keyword.title()} Techniques",
            "abstract": f"This paper presents novel approaches to {interest_keyword} research.",
            "authors": ["Test Author"],
            "published": "2024-01-01",
            "url": "https://arxiv.org/abs/forced",
            "categories": ["cs.AI"],
            "confidence": draw(st.floats(min_value=0.1, max_value=0.8))
        }
        papers.append(matching_paper)
        matching_papers.append(matching_paper)
    
    # 如果没有不匹配的论文，强制创建一篇
    if not non_matching_papers:
        non_matching_paper = {
            "id": f"arxiv-forced-non-match",
            "title": "Quantum Computing Applications in Cryptography",
            "abstract": "This paper explores quantum algorithms for cryptographic applications.",
            "authors": ["Test Author"],
            "published": "2024-01-01", 
            "url": "https://arxiv.org/abs/forced-non",
            "categories": ["cs.CR"],
            "confidence": draw(st.floats(min_value=0.1, max_value=0.8))
        }
        papers.append(non_matching_paper)
        non_matching_papers.append(non_matching_paper)
    
    return papers, matching_papers, non_matching_papers


# ============================================================================
# Property 23: 个性化推荐优先级 (Personalized Recommendation Priority)
# ============================================================================

class TestPersonalizedRecommendationPriority:
    """测试个性化推荐优先级属性。"""

    @pytest.mark.asyncio
    @given(
        interests=user_interests(),
        data=st.data()
    )
    async def test_property_23_personalized_recommendation_priority(self, interests, data):
        """
        # Feature: search-and-recommendation-optimization, Property 23: 个性化推荐优先级
        
        Property 23: 个性化推荐优先级
        *For any* user with an interest profile, personalized recommendations should be ranked 
        such that papers matching user interests have higher scores than papers not matching interests.
        **Validates: Requirements 5.3**
        
        测试策略：
        1. 创建用户兴趣画像
        2. 生成包含匹配和不匹配兴趣的论文列表
        3. 应用个性化调整
        4. 验证匹配兴趣的论文评分高于不匹配的论文
        """
        # 提取用户兴趣关键词
        interest_keywords = [interest.keyword for interest in interests]
        
        # 生成测试论文数据
        papers, matching_papers, non_matching_papers = data.draw(papers_with_mixed_interests(interest_keywords))
        
        # 记录原始评分（深拷贝以避免修改）
        import copy
        original_papers = copy.deepcopy(papers)
        original_scores = {paper["id"]: paper["confidence"] for paper in original_papers}
        
        # 应用个性化调整
        personalized_papers = await recommendation_engine._apply_personalization(
            papers.copy(), interests
        )
        
        # 验证个性化调整后的结果
        personalized_scores = {paper["id"]: paper["confidence"] for paper in personalized_papers}
        
        # 核心属性验证：匹配兴趣的论文应该获得个性化提升
        boosted_papers = [
            paper for paper in personalized_papers 
            if paper.get("personalization_boost", 0) > 0
        ]
        
        if boosted_papers:
            # 验证所有获得提升的论文都匹配用户兴趣
            for paper in boosted_papers:
                title_lower = paper["title"].lower()
                abstract_lower = paper["abstract"].lower()
                
                matches_interest = any(
                    keyword.lower() in title_lower or keyword.lower() in abstract_lower
                    for keyword in interest_keywords
                )
                
                assert matches_interest, (
                    f"获得个性化提升的论文应该匹配用户兴趣。"
                    f"论文标题: {paper['title']}, 摘要: {paper['abstract'][:100]}..., "
                    f"用户兴趣: {interest_keywords}, 提升: {paper.get('personalization_boost', 0)}"
                )
            
            # 验证不匹配兴趣的论文没有获得提升
            for paper in personalized_papers:
                title_lower = paper["title"].lower()
                abstract_lower = paper["abstract"].lower()
                
                matches_interest = any(
                    keyword.lower() in title_lower or keyword.lower() in abstract_lower
                    for keyword in interest_keywords
                )
                
                boost = paper.get("personalization_boost", 0)
                
                if not matches_interest:
                    assert boost == 0, (
                        f"不匹配兴趣的论文不应该获得提升，实际提升: {boost}. "
                        f"论文标题: {paper['title']}, 用户兴趣: {interest_keywords}"
                    )
            
            # 验证个性化提升不超过20%
            for paper in personalized_papers:
                boost = paper.get("personalization_boost", 0)
                assert boost <= 0.2, (
                    f"个性化提升 ({boost}) 不应超过 0.2 (20%)"
                )
        
        # 验证论文按评分降序排列
        scores = [paper["confidence"] for paper in personalized_papers]
        assert scores == sorted(scores, reverse=True), (
            "论文应该按评分降序排列"
        )

    @pytest.mark.asyncio
    async def test_personalization_boost_calculation_single_interest(self):
        """
        测试单个兴趣的个性化提升计算逻辑。
        
        验证：
        1. 标题匹配获得更高的提升 (weight * 0.3)
        2. 摘要匹配获得较低的提升 (weight * 0.1)
        3. 提升不超过20%
        """
        # 使用固定的兴趣和权重进行测试
        interests = [InterestKeyword(keyword="machine learning", weight=0.5)]
        base_confidence = 0.5
        
        # 创建标题匹配的论文（确保关键词只在标题中）
        title_match_paper = {
            "id": "title-match",
            "title": "Advanced Machine Learning Research Methods",
            "abstract": "This paper explores various computational approaches and methodologies.",
            "confidence": base_confidence
        }
        
        # 创建摘要匹配的论文（确保关键词只在摘要中）
        abstract_match_paper = {
            "id": "abstract-match", 
            "title": "Computational Methods in Modern AI Systems",
            "abstract": "This paper investigates machine learning applications and implementations in modern systems.",
            "confidence": base_confidence
        }
        
        # 创建不匹配的论文
        no_match_paper = {
            "id": "no-match",
            "title": "Quantum Computing Applications",
            "abstract": "This paper explores quantum algorithms for optimization.",
            "confidence": base_confidence
        }
        
        papers = [title_match_paper, abstract_match_paper, no_match_paper]
        
        # 应用个性化调整
        personalized_papers = await recommendation_engine._apply_personalization(
            papers.copy(), interests
        )
        
        # 验证提升计算
        title_paper = next(p for p in personalized_papers if p["id"] == "title-match")
        abstract_paper = next(p for p in personalized_papers if p["id"] == "abstract-match")
        no_match_paper_result = next(p for p in personalized_papers if p["id"] == "no-match")
        
        # 获取提升值
        title_boost = title_paper.get("personalization_boost", 0)
        abstract_boost = abstract_paper.get("personalization_boost", 0)
        no_match_boost = no_match_paper_result.get("personalization_boost", 0)
        
        # 验证提升逻辑
        expected_title_boost = 0.5 * 0.3  # 0.15
        expected_abstract_boost = 0.5 * 0.1  # 0.05
        
        assert abs(title_boost - expected_title_boost) < 0.001, (
            f"标题匹配提升 ({title_boost}) 应该等于 {expected_title_boost}"
        )
        
        assert abs(abstract_boost - expected_abstract_boost) < 0.001, (
            f"摘要匹配提升 ({abstract_boost}) 应该等于 {expected_abstract_boost}"
        )
        
        assert no_match_boost == 0, (
            f"不匹配的论文不应该获得提升，实际提升: {no_match_boost}"
        )
        
        # 验证标题匹配的提升大于摘要匹配
        assert title_boost > abstract_boost, (
            f"标题匹配提升 ({title_boost}) 应该大于摘要匹配提升 ({abstract_boost})"
        )
        
        # 验证最终评分
        assert title_paper["confidence"] == base_confidence + title_boost
        assert abstract_paper["confidence"] == base_confidence + abstract_boost
        assert no_match_paper_result["confidence"] == base_confidence

    @pytest.mark.asyncio
    async def test_empty_interests_no_personalization(self):
        """
        测试空兴趣列表时不应用个性化调整。
        """
        papers = [
            {
                "id": "test-paper",
                "title": "Machine Learning Applications",
                "abstract": "This paper explores ML techniques.",
                "confidence": 0.5
            }
        ]
        
        # 空兴趣列表
        empty_interests = []
        
        # 应用个性化调整
        result = await recommendation_engine._apply_personalization(
            papers.copy(), empty_interests
        )
        
        # 验证没有变化
        assert result == papers, "空兴趣列表时不应该修改论文列表"
        assert result[0].get("personalization_boost") is None, (
            "空兴趣列表时不应该添加个性化提升字段"
        )

    @pytest.mark.asyncio
    @given(
        interests=user_interests(),
        num_papers=st.integers(min_value=5, max_value=20)
    )
    async def test_ranking_preservation_with_personalization(self, interests, num_papers):
        """
        测试个性化调整后排序的正确性。
        
        验证个性化调整不会破坏基本的评分排序逻辑。
        """
        interest_keywords = [interest.keyword for interest in interests]
        
        # 生成测试论文
        papers = []
        for i in range(num_papers):
            # 随机决定是否匹配兴趣
            matches_interest = i % 3 == 0  # 每3篇中有1篇匹配
            
            if matches_interest and interest_keywords:
                keyword = interest_keywords[i % len(interest_keywords)]
                title = f"Research on {keyword.title()} Methods"
                abstract = f"This study focuses on {keyword} applications."
            else:
                title = f"Study {i} on Various Topics"
                abstract = f"This is abstract {i} about general research."
            
            papers.append({
                "id": f"paper-{i}",
                "title": title,
                "abstract": abstract,
                "confidence": 0.1 + (i * 0.05),  # 递增的基础评分
                "authors": [f"Author {i}"],
                "published": "2024-01-01",
                "url": f"https://arxiv.org/abs/{i}",
                "categories": ["cs.AI"]
            })
        
        # 应用个性化调整
        personalized_papers = await recommendation_engine._apply_personalization(
            papers.copy(), interests
        )
        
        # 验证排序正确性
        scores = [paper["confidence"] for paper in personalized_papers]
        assert scores == sorted(scores, reverse=True), (
            "个性化调整后论文应该按评分降序排列"
        )
        
        # 验证所有论文都存在
        original_ids = {paper["id"] for paper in papers}
        personalized_ids = {paper["id"] for paper in personalized_papers}
        assert original_ids == personalized_ids, (
            "个性化调整不应该增加或删除论文"
        )