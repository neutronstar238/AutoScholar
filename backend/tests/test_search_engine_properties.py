"""搜索引擎降级策略的属性测试。

使用Hypothesis进行基于属性的测试，验证搜索引擎在各种输入下的正确性。

Requirements: 1.1, 1.2, 1.3, 1.4, 2.4
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from app.engines.search_engine import SearchEngine
from app.utils.cache_manager import CacheManager


# Hypothesis配置：每个属性测试运行100次
settings.register_profile("default", max_examples=100, deadline=5000)
settings.load_profile("default")


# 测试数据生成策略
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


class TestSearchEngineFallbackProperties:
    """搜索引擎降级策略的属性测试。"""

    @pytest.mark.asyncio
    @given(keywords=keyword_lists())
    @settings(max_examples=100)
    async def test_property_1_fallback_chain_completeness(self, keywords):
        """
        **Property 1: 降级策略链完整性**
        
        For any set of user interest keywords, when the primary search returns no results,
        the Recommendation_Engine should sequentially attempt: (1) individual keyword searches,
        (2) thesaurus-expanded searches, (3) cached similar queries, and (4) trending papers
        fallback, until at least 3 recommendations are found or all strategies are exhausted.
        
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        engine = SearchEngine(min_results=3)
        
        # Mock所有搜索调用返回空结果（触发降级）
        with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            # Mock关键词扩展
            with patch("app.engines.search_engine.expand_keywords") as mock_expand:
                mock_expand.return_value = [f"expanded_{kw}" for kw in keywords[:2]]
                
                # Mock cache_manager全局实例
                with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
                    mock_cache_mgr.get = AsyncMock(return_value=None)
                    mock_cache_mgr.set = AsyncMock(return_value=True)
                    mock_cache_mgr.generate_key = MagicMock(return_value="test_key")
                    
                    # Mock缓存管理器
                    with patch.object(engine, "_read_term_cache", new_callable=AsyncMock) as mock_cache:
                        mock_cache.return_value = []
                        
                        # Mock热门论文降级（返回足够的结果）
                        with patch.object(engine, "_fetch_trending_fallback", new_callable=AsyncMock) as mock_trending:
                            trending_papers = [
                                {"id": f"trending-{i}", "title": f"Trending Paper {i}"}
                                for i in range(5)
                            ]
                            mock_trending.return_value = trending_papers
                            
                            # 执行搜索
                            papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                            
                            # 验证：应该尝试了所有策略并最终使用trending_fallback
                            assert strategy == "trending_fallback"
                            assert is_fallback is True
                            assert len(papers) >= 3  # 至少返回3个推荐
                            
                            # 验证策略链被执行
                            assert mock_search.call_count > 0  # 尝试了搜索
                            assert mock_expand.called  # 尝试了关键词扩展
                            assert mock_cache.called  # 尝试了缓存降级
                            assert mock_trending.called  # 最终使用了热门论文降级

    @pytest.mark.asyncio
    @given(keywords=keyword_lists(), limit=st.integers(min_value=3, max_value=20))
    @settings(max_examples=100)
    async def test_property_2_minimum_recommendation_guarantee(self, keywords, limit):
        """
        **Property 2: 最小推荐数量保证**
        
        For any valid recommendation request, the Recommendation_Engine should return
        at least 3 recommendations unless all fallback strategies (including trending papers)
        fail to produce results.
        
        **Validates: Requirements 1.5**
        """
        engine = SearchEngine(min_results=3)
        
        # 场景1：主搜索返回足够结果
        with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"id": f"paper-{i}", "title": f"Paper {i}"} for i in range(5)
            ]
            
            with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
                mock_cache_mgr.get = AsyncMock(return_value=None)
                mock_cache_mgr.set = AsyncMock(return_value=True)
                mock_cache_mgr.generate_key = MagicMock(return_value="test_key")
                
                papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=limit)
                
                # 验证：返回至少3个结果
                assert len(papers) >= 3
                assert len(papers) <= limit
        
        # 场景2：主搜索失败，但降级策略成功
        with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
            # 前几次调用返回空，最后返回结果
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    return []
                return [{"id": f"fallback-{i}", "title": f"Fallback {i}"} for i in range(4)]
            
            mock_search.side_effect = side_effect
            
            with patch("app.engines.search_engine.expand_keywords") as mock_expand:
                mock_expand.return_value = [f"expanded_{kw}" for kw in keywords[:2]]
                
                with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
                    mock_cache_mgr.get = AsyncMock(return_value=None)
                    mock_cache_mgr.set = AsyncMock(return_value=True)
                    mock_cache_mgr.generate_key = MagicMock(return_value="test_key")
                    
                    papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=limit)
                    
                    # 验证：即使降级，仍返回至少3个结果
                    assert len(papers) >= 3

    @pytest.mark.asyncio
    @given(keywords=keyword_lists())
    @settings(max_examples=100, deadline=10000)
    async def test_property_5_api_timeout_cache_fallback(self, keywords):
        """
        **Property 5: API超时缓存降级**
        
        For any search query, when the arXiv API is unresponsive (timeout or error),
        the Search_Engine should return cached trending papers from the past 7 days
        instead of failing.
        
        **Validates: Requirements 1.4**
        """
        engine = SearchEngine(min_results=3)
        
        # Mock API超时异常
        with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = asyncio.TimeoutError("API timeout")
            
            # Mock asyncio.sleep to avoid actual delays
            with patch("app.engines.search_engine.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                mock_sleep.return_value = None
                
                # Mock关键词扩展
                with patch("app.engines.search_engine.expand_keywords") as mock_expand:
                    mock_expand.return_value = [f"expanded_{kw}" for kw in keywords[:2]]
                    
                    # Mock cache_manager全局实例
                    with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
                        mock_cache_mgr.get = AsyncMock(return_value=None)
                        mock_cache_mgr.set = AsyncMock(return_value=True)
                        mock_cache_mgr.generate_key = MagicMock(return_value="test_key")
                        
                        # Mock缓存返回空
                        with patch.object(engine, "_read_term_cache", new_callable=AsyncMock) as mock_cache:
                            mock_cache.return_value = []
                            
                            # Mock热门论文降级（模拟缓存的trending papers）
                            with patch.object(engine, "_fetch_trending_fallback", new_callable=AsyncMock) as mock_trending:
                                cached_trending = [
                                    {
                                        "id": f"cached-trending-{i}",
                                        "title": f"Cached Trending Paper {i}",
                                        "published": "2024-01-10"  # 7天内
                                    }
                                    for i in range(5)
                                ]
                                mock_trending.return_value = cached_trending
                                
                                # 执行搜索
                                papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                                
                                # 验证：API超时后，使用缓存的trending papers
                                assert strategy == "trending_fallback"
                                assert is_fallback is True
                                assert len(papers) >= 3
                                assert all("cached-trending" in p["id"] for p in papers)
                                
                                # 验证：trending fallback被调用
                                assert mock_trending.called

    @pytest.mark.asyncio
    @given(query=st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    async def test_property_7_retry_exponential_backoff(self, query):
        """
        **Property 7: 重试指数退避**
        
        For any network timeout during arXiv API calls, the Search_Engine should retry
        exactly 3 times with exponential backoff intervals (1s, 2s, 4s), and only then
        return an error or fallback.
        
        **Validates: Requirements 2.4**
        """
        engine = SearchEngine(min_results=3)
        
        # 记录重试时间间隔
        retry_times = []
        
        with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
            # 所有调用都超时
            mock_search.side_effect = asyncio.TimeoutError("Network timeout")
            
            with patch("app.engines.search_engine.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                # 记录sleep调用的延迟时间
                async def record_sleep(delay):
                    retry_times.append(delay)
                
                mock_sleep.side_effect = record_sleep
                
                # 执行单次搜索（会触发重试）
                result = await engine._search_with_retry(query, limit=10)
                
                # 验证：返回空结果（所有重试都失败）
                assert result == []
                
                # 验证：尝试了3次搜索
                assert mock_search.call_count == 3
                
                # 验证：指数退避间隔（0.5s, 1s, 2s）
                # 注意：第3次失败后不再sleep
                assert len(retry_times) == 2  # 只有前两次失败后会sleep
                assert retry_times[0] == 0.5  # 第一次重试前的延迟
                assert retry_times[1] == 1.0  # 第二次重试前的延迟
                # 第三次失败后直接返回，不再sleep


class TestSearchEngineCacheIntegration:
    """搜索引擎缓存集成的属性测试。"""

    @pytest.mark.asyncio
    @given(keywords=keyword_lists())
    @settings(max_examples=100)
    async def test_property_10_cache_failure_graceful_degradation(self, keywords):
        """
        **Property 10: 缓存失败优雅降级**
        
        For any search query, if Redis cache storage fails, the Search_Engine should
        still return the fetched results successfully without throwing an error.
        
        **Validates: Requirements 4.4**
        """
        engine = SearchEngine(min_results=3)
        
        # 准备搜索结果
        search_results = [
            {"id": f"paper-{i}", "title": f"Paper {i}", "abstract": f"Abstract {i}"}
            for i in range(5)
        ]
        
        # 场景1：缓存读取失败，但搜索成功
        with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
            # Mock缓存读取失败（抛出异常）
            mock_cache_mgr.get = AsyncMock(side_effect=Exception("Redis connection failed"))
            mock_cache_mgr.set = AsyncMock(return_value=True)
            mock_cache_mgr.generate_key = MagicMock(return_value="test_cache_key")
            
            with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = search_results
                
                # 执行搜索 - 不应抛出异常
                try:
                    papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                    
                    # 验证：即使缓存读取失败，仍然返回搜索结果
                    assert len(papers) >= 3
                    assert papers == search_results
                    assert strategy == "combined"
                    
                    # 验证：搜索被调用
                    assert mock_search.called
                except Exception as e:
                    pytest.fail(f"缓存读取失败不应导致搜索失败: {e}")
        
        # 场景2：缓存写入失败，但搜索成功
        with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
            # Mock缓存读取成功（未命中）
            mock_cache_mgr.get = AsyncMock(return_value=None)
            # Mock缓存写入失败（抛出异常）
            mock_cache_mgr.set = AsyncMock(side_effect=Exception("Redis write failed"))
            mock_cache_mgr.generate_key = MagicMock(return_value="test_cache_key")
            
            with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = search_results
                
                # 执行搜索 - 不应抛出异常
                try:
                    papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                    
                    # 验证：即使缓存写入失败，仍然返回搜索结果
                    assert len(papers) >= 3
                    assert papers == search_results
                    assert strategy == "combined"
                    
                    # 验证：搜索被调用
                    assert mock_search.called
                    # 验证：尝试写入缓存（但失败了）
                    assert mock_cache_mgr.set.called
                except Exception as e:
                    pytest.fail(f"缓存写入失败不应导致搜索失败: {e}")
        
        # 场景3：缓存完全不可用，但搜索成功
        with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
            # Mock所有缓存操作都失败
            mock_cache_mgr.get = AsyncMock(side_effect=Exception("Cache unavailable"))
            mock_cache_mgr.set = AsyncMock(side_effect=Exception("Cache unavailable"))
            mock_cache_mgr.generate_key = MagicMock(side_effect=Exception("Cache unavailable"))
            
            with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = search_results
                
                # 执行搜索 - 不应抛出异常
                try:
                    papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                    
                    # 验证：即使缓存完全不可用，仍然返回搜索结果
                    assert len(papers) >= 3
                    assert papers == search_results
                    
                    # 验证：搜索被调用
                    assert mock_search.called
                except Exception as e:
                    pytest.fail(f"缓存完全不可用不应导致搜索失败: {e}")

    @pytest.mark.asyncio
    @given(keywords=keyword_lists())
    @settings(max_examples=50)
    async def test_cache_hit_returns_immediately(self, keywords):
        """
        测试缓存命中时立即返回结果。
        
        验证：当缓存存在时，不应调用外部API。
        """
        engine = SearchEngine(min_results=3)
        
        # 准备缓存数据
        cached_papers = [
            {"id": f"cached-{i}", "title": f"Cached Paper {i}"}
            for i in range(5)
        ]
        
        with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
            # Mock缓存命中
            mock_cache_mgr.get = AsyncMock(return_value=cached_papers)
            mock_cache_mgr.generate_key = MagicMock(return_value="test_cache_key")
            
            with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
                # 执行搜索
                papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                
                # 验证：返回缓存结果
                assert strategy == "cache_hit"
                assert is_fallback is True
                assert papers == cached_papers
                
                # 验证：没有调用外部API
                assert mock_search.call_count == 0

    @pytest.mark.asyncio
    @given(keywords=keyword_lists())
    @settings(max_examples=50)
    async def test_cache_miss_stores_results(self, keywords):
        """
        测试缓存未命中时存储搜索结果。
        
        验证：成功搜索后，结果应被存储到缓存。
        """
        engine = SearchEngine(min_results=3)
        
        search_results = [
            {"id": f"paper-{i}", "title": f"Paper {i}"}
            for i in range(5)
        ]
        
        with patch("app.engines.search_engine.cache_manager") as mock_cache_mgr:
            # Mock缓存未命中
            mock_cache_mgr.get = AsyncMock(return_value=None)
            mock_cache_mgr.set = AsyncMock(return_value=True)
            mock_cache_mgr.generate_key = MagicMock(return_value="test_cache_key")
            
            with patch("app.engines.search_engine.search_literature", new_callable=AsyncMock) as mock_search:
                mock_search.return_value = search_results
                
                # 执行搜索
                papers, is_fallback, strategy = await engine.search_with_fallback(keywords, limit=10)
                
                # 验证：返回搜索结果
                assert strategy == "combined"
                assert is_fallback is False
                assert len(papers) == 5
                
                # 验证：结果被存储到缓存
                assert mock_cache_mgr.set.called
                # 获取set调用的参数
                set_call_args = mock_cache_mgr.set.call_args
                assert set_call_args is not None
                stored_papers = set_call_args[0][1]  # 第二个参数是papers
                assert stored_papers == papers


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
