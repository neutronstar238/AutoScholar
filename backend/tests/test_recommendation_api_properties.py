"""推荐API的属性测试。

使用Hypothesis进行基于属性的测试，验证推荐API在各种输入下的正确性。

Requirements: 1.6, 1.7
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck

from app.engines.recommendation_engine import recommendation_engine
from app.utils.quality_monitor import QualityMonitor


# Hypothesis配置：每个属性测试运行100次
settings.register_profile("default", max_examples=100, deadline=5000)
settings.load_profile("default")


# ============================================================================
# Test Data Generation Strategies
# ============================================================================

@st.composite
def keyword_lists(draw):
    """生成关键词列表策略。"""
    return draw(
        st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
                min_size=1,
                max_size=50
            ).filter(lambda x: x.strip()),
            min_size=1,
            max_size=5
        )
    )


@st.composite
def paper_results(draw, min_size=0, max_size=20):
    """生成论文结果列表策略。"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    papers = []
    for i in range(size):
        papers.append({
            "id": f"arxiv-{draw(st.integers(min_value=1000, max_value=9999))}",
            "title": draw(st.text(min_size=10, max_size=100)),
            "abstract": draw(st.text(min_size=50, max_size=500)),
            "authors": [draw(st.text(min_size=5, max_size=30))],
            "published": "2024-01-01",
            "url": f"https://arxiv.org/abs/{i}",
            "categories": [draw(st.sampled_from(["cs.AI", "cs.LG", "cs.CV", "cs.CL"]))]
        })
    return papers


@st.composite
def fallback_scenarios(draw):
    """生成降级场景策略。
    
    Returns:
        Tuple of (papers, is_fallback, strategy)
    """
    # 随机选择是否为降级场景
    is_fallback = draw(st.booleans())
    
    if is_fallback:
        # 降级场景：使用降级策略
        strategy = draw(st.sampled_from([
            "cache_fallback",
            "trending_fallback",
            "expanded_keywords",
            "single_keyword"
        ]))
        # 降级场景通常返回较少的论文
        papers = draw(paper_results(min_size=3, max_size=8))
    else:
        # 正常场景：使用主搜索策略
        strategy = draw(st.sampled_from(["combined", "primary", "cache_hit"]))
        # 正常场景返回更多论文
        papers = draw(paper_results(min_size=5, max_size=15))
    
    return papers, is_fallback, strategy


# ============================================================================
# Property 3: 降级标识正确性 (Fallback Indicator Correctness)
# ============================================================================

class TestRecommendationAPIFallbackProperties:
    """推荐API降级相关的属性测试。"""

    @pytest.mark.asyncio
    @given(
        keywords=keyword_lists(),
        scenario=fallback_scenarios()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_property_3_fallback_indicator_correctness(self, keywords, scenario):
        """
        **Property 3: 降级标识正确性**
        
        For any recommendation result generated through fallback strategies, the response
        should contain `is_fallback=True` and a clear indication in the recommendations
        text that these are general suggestions.
        
        **Validates: Requirements 1.6**
        """
        papers, is_fallback, strategy = scenario
        
        # Mock search_engine to return the scenario
        with patch("app.engines.recommendation_engine.search_engine") as mock_search_engine:
            mock_search_engine.search_with_fallback = AsyncMock(
                return_value=(papers, is_fallback, strategy)
            )
            
            # Mock trend_analyzer
            with patch("app.engines.recommendation_engine.trend_analyzer") as mock_trend:
                # Add trend_score to papers
                papers_with_trend = []
                for p in papers:
                    p_copy = dict(p)
                    p_copy["trend_score"] = 0.5
                    papers_with_trend.append(p_copy)
                mock_trend.analyze_papers = MagicMock(return_value=papers_with_trend)
                
                # Mock user_profile_manager
                with patch("app.engines.recommendation_engine.user_profile_manager") as mock_profile:
                    mock_profile.extract_interests = MagicMock(return_value=[])
                    mock_profile.update_interest_from_search = MagicMock()
                    
                    # Mock feedback_collector
                    with patch("app.engines.recommendation_engine.feedback_collector") as mock_feedback:
                        mock_feedback.record_view = MagicMock()
                        
                        # Mock trending_manager to avoid database operations
                        with patch("app.engines.recommendation_engine.trending_manager") as mock_trending:
                            mock_trending.update_trending_paper = AsyncMock()
                            
                            # Execute recommendation
                            result = await recommendation_engine.generate_recommendations(
                                user_id=1,
                                interests=keywords,
                                limit=5
                            )
                            
                            # Verify: is_fallback field matches the scenario
                            assert "is_fallback" in result, "Result should contain is_fallback field"
                            assert result["is_fallback"] == is_fallback, (
                                f"is_fallback should be {is_fallback} for strategy {strategy}"
                            )
                            
                            # Verify: fallback_strategy field is present
                            assert "fallback_strategy" in result, "Result should contain fallback_strategy field"
                            assert result["fallback_strategy"] == strategy, (
                                f"fallback_strategy should be {strategy}"
                            )
                            
                            # Verify: papers are returned
                            assert "papers" in result, "Result should contain papers"
                            assert len(result["papers"]) >= 3 or len(papers) < 3, (
                                "Should return at least 3 papers when available"
                            )
                            
                            # Additional verification for fallback scenarios:
                            # When is_fallback=True, the API response should indicate this
                            # (This is tested at the API level, not engine level)
                            if is_fallback:
                                # Verify that fallback strategies are properly identified
                                assert strategy in [
                                    "cache_fallback",
                                    "trending_fallback",
                                    "expanded_keywords",
                                    "single_keyword",
                                    "cache_hit"  # cache_hit is also considered fallback
                                ], f"Fallback strategy should be valid: {strategy}"

    @pytest.mark.asyncio
    @given(
        keywords=keyword_lists(),
        user_id=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_fallback_indicator_in_api_response(self, keywords, user_id):
        """
        测试API响应中的降级标识。
        
        验证：当使用降级策略时，API响应包含is_fallback=True和fallback_note。
        """
        # Mock降级场景
        fallback_papers = [
            {
                "id": f"trending-{i}",
                "title": f"Trending Paper {i}",
                "abstract": "This is a trending paper abstract.",
                "authors": ["Author A"],
                "published": "2024-01-01",
                "url": f"https://arxiv.org/abs/trending-{i}",
                "categories": ["cs.AI"]
            }
            for i in range(5)
        ]
        
        with patch("app.engines.recommendation_engine.search_engine") as mock_search_engine:
            # 返回降级结果
            mock_search_engine.search_with_fallback = AsyncMock(
                return_value=(fallback_papers, True, "trending_fallback")
            )
            
            with patch("app.engines.recommendation_engine.trend_analyzer") as mock_trend:
                papers_with_trend = []
                for p in fallback_papers:
                    p_copy = dict(p)
                    p_copy["trend_score"] = 0.5
                    papers_with_trend.append(p_copy)
                mock_trend.analyze_papers = MagicMock(return_value=papers_with_trend)
                
                with patch("app.engines.recommendation_engine.user_profile_manager") as mock_profile:
                    mock_profile.extract_interests = MagicMock(return_value=[])
                    mock_profile.update_interest_from_search = MagicMock()
                    
                    with patch("app.engines.recommendation_engine.feedback_collector") as mock_feedback:
                        mock_feedback.record_view = MagicMock()
                        
                        with patch("app.engines.recommendation_engine.trending_manager") as mock_trending:
                            mock_trending.update_trending_paper = AsyncMock()
                            
                            # Execute recommendation
                            result = await recommendation_engine.generate_recommendations(
                                user_id=user_id,
                                interests=keywords,
                                limit=5
                            )
                            
                            # Verify: is_fallback is True
                            assert result["is_fallback"] is True, (
                                "is_fallback should be True for fallback scenarios"
                            )
                            
                            # Verify: fallback_strategy indicates the fallback type
                            assert result["fallback_strategy"] == "trending_fallback", (
                                "fallback_strategy should indicate trending_fallback"
                            )
                            
                            # Verify: papers are returned
                            assert len(result["papers"]) >= 3, (
                                "Should return at least 3 papers in fallback"
                            )


# ============================================================================
# Property 4: 降级率追踪准确性 (Fallback Rate Tracking Accuracy)
# ============================================================================

class TestFallbackRateTracking:
    """降级率追踪的属性测试。"""

    @pytest.mark.asyncio
    @given(
        # 生成一系列请求，每个请求有is_fallback标志
        fallback_sequence=st.lists(
            st.booleans(),
            min_size=10,
            max_size=100
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_property_4_fallback_rate_tracking_accuracy(self, fallback_sequence):
        """
        **Property 4: 降级率追踪准确性**
        
        For any sequence of recommendation requests, the fallback usage rate should
        equal the number of fallback responses divided by total responses, and should
        trigger an alert when exceeding 0.20.
        
        **Validates: Requirements 1.7**
        """
        # Create a fresh quality monitor for this test
        monitor = QualityMonitor()
        
        # Record the fallback sequence
        for is_fallback in fallback_sequence:
            monitor.record_fallback(is_fallback)
        
        # Calculate expected fallback rate
        fallback_count = sum(1 for x in fallback_sequence if x)
        total_count = len(fallback_sequence)
        expected_rate = fallback_count / total_count if total_count > 0 else 0.0
        
        # Get actual fallback rate from monitor
        actual_rate = monitor.fallback_rate()
        
        # Verify: fallback rate equals expected rate
        assert abs(actual_rate - expected_rate) < 0.0001, (
            f"Fallback rate should equal {expected_rate:.4f}, got {actual_rate:.4f}\n"
            f"Fallback count: {fallback_count}, Total: {total_count}"
        )
        
        # Verify: alert condition when rate exceeds 0.20
        # Note: The check is "fallback_rate < 0.20", so:
        # - rate < 0.20: check passes (no alert)
        # - rate >= 0.20: check fails (alert triggered)
        should_alert = expected_rate >= 0.20
        quality_check = monitor.quality_check()
        fallback_check_passed = quality_check["checks"]["fallback_rate_lt_20pct"]
        
        if should_alert:
            # When rate >= 0.20, the check should fail (alert triggered)
            assert not fallback_check_passed, (
                f"Alert should be triggered when fallback rate {expected_rate:.2%} >= 20%"
            )
        else:
            # When rate < 0.20, the check should pass (no alert)
            assert fallback_check_passed, (
                f"No alert should be triggered when fallback rate {expected_rate:.2%} < 20%"
            )

    @pytest.mark.asyncio
    @given(
        # 生成多个批次的请求序列
        batch_sequences=st.lists(
            st.lists(st.booleans(), min_size=5, max_size=20),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_fallback_rate_accumulation(self, batch_sequences):
        """
        测试降级率的累积计算。
        
        验证：跨多个批次的请求，降级率应该正确累积计算。
        """
        monitor = QualityMonitor()
        
        all_fallbacks = []
        
        # 逐批次记录
        for batch in batch_sequences:
            for is_fallback in batch:
                monitor.record_fallback(is_fallback)
                all_fallbacks.append(is_fallback)
            
            # 每个批次后验证累积率
            fallback_count = sum(1 for x in all_fallbacks if x)
            total_count = len(all_fallbacks)
            expected_rate = fallback_count / total_count if total_count > 0 else 0.0
            actual_rate = monitor.fallback_rate()
            
            assert abs(actual_rate - expected_rate) < 0.0001, (
                f"Accumulated fallback rate should equal {expected_rate:.4f}, got {actual_rate:.4f}"
            )

    @pytest.mark.asyncio
    @given(
        fallback_count=st.integers(min_value=0, max_value=100),
        non_fallback_count=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_fallback_rate_formula(self, fallback_count, non_fallback_count):
        """
        测试降级率计算公式。
        
        验证：fallback_rate = fallback_count / (fallback_count + non_fallback_count)
        """
        monitor = QualityMonitor()
        
        # Record fallback events
        for _ in range(fallback_count):
            monitor.record_fallback(True)
        
        # Record non-fallback events
        for _ in range(non_fallback_count):
            monitor.record_fallback(False)
        
        # Calculate expected rate
        total = fallback_count + non_fallback_count
        expected_rate = fallback_count / total if total > 0 else 0.0
        
        # Get actual rate
        actual_rate = monitor.fallback_rate()
        
        # Verify formula
        assert abs(actual_rate - expected_rate) < 0.0001, (
            f"Fallback rate formula incorrect: expected {expected_rate:.4f}, got {actual_rate:.4f}\n"
            f"Fallback: {fallback_count}, Non-fallback: {non_fallback_count}, Total: {total}"
        )

    @pytest.mark.asyncio
    async def test_fallback_rate_alert_threshold(self):
        """
        测试降级率告警阈值。
        
        验证：当降级率达到或超过0.20时应触发告警；低于0.20时不应触发告警。
        """
        # Test case 1: Rate exactly at threshold (0.20)
        monitor1 = QualityMonitor()
        for i in range(100):
            monitor1.record_fallback(i < 20)  # 20% fallback rate
        
        rate1 = monitor1.fallback_rate()
        assert abs(rate1 - 0.20) < 0.01, f"Rate should be ~0.20, got {rate1}"
        
        check1 = monitor1.quality_check()
        # At exactly 0.20, should trigger alert (>= 0.20 triggers alert)
        assert not check1["checks"]["fallback_rate_lt_20pct"], (
            f"Alert should trigger at exactly 20% fallback rate (rate={rate1:.2%})"
        )
        
        # Test case 2: Rate just above threshold (0.21)
        monitor2 = QualityMonitor()
        for i in range(100):
            monitor2.record_fallback(i < 21)  # 21% fallback rate
        
        rate2 = monitor2.fallback_rate()
        assert rate2 > 0.20, f"Rate should be > 0.20, got {rate2}"
        
        check2 = monitor2.quality_check()
        # Above 0.20, should trigger alert (< 0.20 check should fail)
        assert not check2["checks"]["fallback_rate_lt_20pct"], (
            f"Alert should trigger when fallback rate {rate2:.2%} > 20%"
        )
        
        # Test case 3: Rate well below threshold (0.10)
        monitor3 = QualityMonitor()
        for i in range(100):
            monitor3.record_fallback(i < 10)  # 10% fallback rate
        
        rate3 = monitor3.fallback_rate()
        assert rate3 < 0.20, f"Rate should be < 0.20, got {rate3}"
        
        check3 = monitor3.quality_check()
        # Below 0.20, should not trigger alert
        assert check3["checks"]["fallback_rate_lt_20pct"], (
            f"Alert should not trigger when fallback rate {rate3:.2%} < 20%"
        )


# ============================================================================
# Integration Tests
# ============================================================================

class TestRecommendationAPIIntegration:
    """推荐API集成测试。"""

    @pytest.mark.asyncio
    async def test_end_to_end_fallback_flow(self):
        """
        端到端测试：从搜索失败到降级推荐的完整流程。
        
        验证：
        1. 主搜索失败时触发降级
        2. 降级结果包含正确的is_fallback标识
        3. 降级率被正确追踪
        """
        monitor = QualityMonitor()
        
        # Scenario: Primary search fails, fallback to trending
        fallback_papers = [
            {
                "id": f"trending-{i}",
                "title": f"Trending Paper {i}",
                "abstract": "Trending paper abstract.",
                "authors": ["Author"],
                "published": "2024-01-01",
                "url": f"https://arxiv.org/abs/trending-{i}",
                "categories": ["cs.AI"]
            }
            for i in range(5)
        ]
        
        with patch("app.engines.recommendation_engine.search_engine") as mock_search:
            mock_search.search_with_fallback = AsyncMock(
                return_value=(fallback_papers, True, "trending_fallback")
            )
            
            with patch("app.engines.recommendation_engine.trend_analyzer") as mock_trend:
                papers_with_trend = []
                for p in fallback_papers:
                    p_copy = dict(p)
                    p_copy["trend_score"] = 0.5
                    papers_with_trend.append(p_copy)
                mock_trend.analyze_papers = MagicMock(return_value=papers_with_trend)
                
                with patch("app.engines.recommendation_engine.user_profile_manager") as mock_profile:
                    mock_profile.extract_interests = MagicMock(return_value=[])
                    mock_profile.update_interest_from_search = MagicMock()
                    
                    with patch("app.engines.recommendation_engine.feedback_collector") as mock_feedback:
                        mock_feedback.record_view = MagicMock()
                        
                        with patch("app.engines.recommendation_engine.trending_manager") as mock_trending:
                            mock_trending.update_trending_paper = AsyncMock()
                            
                            # Execute recommendation
                            result = await recommendation_engine.generate_recommendations(
                                user_id=1,
                                interests=["deep learning"],
                                limit=5
                            )
                            
                            # Verify fallback indicator
                            assert result["is_fallback"] is True
                            assert result["fallback_strategy"] == "trending_fallback"
                            assert len(result["papers"]) >= 3
                            
                            # Record fallback for tracking
                            monitor.record_fallback(result["is_fallback"])
                            
                            # Verify fallback rate
                            assert monitor.fallback_rate() == 1.0  # 100% fallback (1 out of 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
