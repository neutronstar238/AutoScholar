"""带降级策略的搜索引擎。"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.tools.literature_search import search_literature
from app.utils.cache_manager import cache_manager
from app.utils.keyword_expander import expand_keywords
from app.utils.trending_manager import trending_manager


TRENDING_QUERIES = [
    "machine learning",
    "large language model",
    "computer vision",
    "natural language processing",
    "reinforcement learning",
]


class SearchEngine:
    def __init__(self, min_results: int = 3):
        self.min_results = min_results

    async def _search_with_retry(self, query: str, limit: int) -> List[Dict[str, Any]]:
        delay = 0.5
        for attempt in range(3):
            try:
                return await search_literature(query=query, limit=limit, source="arxiv", sort_by="submittedDate")
            except Exception as exc:
                logger.warning(f"搜索失败 attempt={attempt + 1} query={query}: {exc}")
                if attempt == 2:
                    return []
                await asyncio.sleep(delay)
                delay *= 2
        return []

    @staticmethod
    def _deduplicate(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        by_id = {}
        for paper in papers:
            key = paper.get("id") or paper.get("url") or paper.get("title")
            if key:
                by_id[key] = paper
        return list(by_id.values())

    async def _read_term_cache(self, terms: List[str], limit: int) -> List[Dict[str, Any]]:
        cached_results: List[Dict[str, Any]] = []
        for term in terms:
            key = cache_manager.generate_key("search_term", {"term": term, "limit": limit})
            term_cached = await cache_manager.get(key)
            if term_cached:
                cached_results.extend(term_cached)
        return self._deduplicate(cached_results)

    async def _write_term_cache(self, term: str, papers: List[Dict[str, Any]], limit: int) -> None:
        key = cache_manager.generate_key("search_term", {"term": term, "limit": limit})
        await cache_manager.set(key, papers)

    async def _fetch_trending_fallback(self, limit: int) -> List[Dict[str, Any]]:
        """获取热门论文作为降级策略。
        
        优先从数据库的TrendingPaper表获取，如果数据库为空，则搜索预定义的热门查询。
        
        Args:
            limit: 返回的论文数量限制
            
        Returns:
            热门论文列表
        """
        # 策略1：从数据库获取热门论文（过去7天推荐的）
        try:
            db_trending = await trending_manager.get_trending_papers(limit=limit, days=7)
            if db_trending and len(db_trending) >= self.min_results:
                logger.info(f"从数据库获取到 {len(db_trending)} 篇热门论文")
                return db_trending
        except Exception as e:
            logger.warning(f"从数据库获取热门论文失败: {e}")
        
        # 策略2：搜索预定义的热门查询（降级）
        logger.info("数据库热门论文不足，使用预定义查询搜索")
        result: List[Dict[str, Any]] = []
        for query in TRENDING_QUERIES:
            papers = await self._search_with_retry(query, max(3, limit // 2))
            if papers:
                result.extend(papers)
            if len(self._deduplicate(result)) >= self.min_results:
                break
        return self._deduplicate(result)[:limit]

    async def search_with_fallback(self, interests: List[str], limit: int = 10) -> Tuple[List[Dict[str, Any]], bool, str]:
        """返回 papers, is_fallback, strategy。
        
        实现缓存失败优雅降级：所有缓存操作都包裹在try-except中，
        确保缓存失败不会影响搜索功能。
        """
        terms = [t.strip() for t in interests if t and t.strip()]
        if not terms:
            trending = await self._fetch_trending_fallback(limit)
            return trending, True, "trending_fallback"

        # 尝试生成缓存键（如果失败，继续执行搜索）
        query_cache_key = None
        try:
            query_cache_key = cache_manager.generate_key("search", {"interests": terms, "limit": limit})
        except Exception as e:
            logger.warning(f"生成缓存键失败，继续执行搜索: {e}")
        
        # 尝试读取缓存（如果失败，继续执行搜索）
        if query_cache_key:
            try:
                cached_query = await cache_manager.get(query_cache_key)
                if cached_query:
                    return cached_query, True, "cache_hit"
            except Exception as e:
                logger.warning(f"读取缓存失败，继续执行搜索: {e}")

        all_results: List[Dict[str, Any]] = []

        # 策略1：组合搜索
        combined_query = " AND ".join(terms)
        combined_results = await self._search_with_retry(combined_query, limit)
        all_results.extend(combined_results)
        if len(self._deduplicate(all_results)) >= self.min_results:
            final = self._deduplicate(all_results)[:limit]
            # 尝试写入缓存（如果失败，不影响返回结果）
            if query_cache_key:
                try:
                    await cache_manager.set(query_cache_key, final)
                except Exception as e:
                    logger.warning(f"写入缓存失败，但搜索成功: {e}")
            return final, False, "combined"

        # 策略2：逐个关键词
        for term in terms:
            term_results = await self._search_with_retry(term, limit)
            if term_results:
                # 尝试写入term缓存（如果失败，不影响搜索）
                try:
                    await self._write_term_cache(term, term_results, limit)
                except Exception as e:
                    logger.warning(f"写入term缓存失败: {e}")
            all_results.extend(term_results)
        if len(self._deduplicate(all_results)) >= self.min_results:
            final = self._deduplicate(all_results)[:limit]
            # 尝试写入缓存（如果失败，不影响返回结果）
            if query_cache_key:
                try:
                    await cache_manager.set(query_cache_key, final)
                except Exception as e:
                    logger.warning(f"写入缓存失败，但搜索成功: {e}")
            return final, True, "individual"

        # 策略3：关键词扩展
        expanded = expand_keywords(terms)
        for term in expanded[:8]:
            term_results = await self._search_with_retry(term, max(3, limit // 2))
            if term_results:
                # 尝试写入term缓存（如果失败，不影响搜索）
                try:
                    await self._write_term_cache(term, term_results, limit)
                except Exception as e:
                    logger.warning(f"写入term缓存失败: {e}")
            all_results.extend(term_results)
        unique_results = self._deduplicate(all_results)
        if len(unique_results) >= self.min_results:
            final = unique_results[:limit]
            # 尝试写入缓存（如果失败，不影响返回结果）
            if query_cache_key:
                try:
                    await cache_manager.set(query_cache_key, final)
                except Exception as e:
                    logger.warning(f"写入缓存失败，但搜索成功: {e}")
            return final, True, "expanded"

        # 策略4：相似缓存降级
        try:
            cached_similar = await self._read_term_cache(terms + expanded[:8], limit)
            if cached_similar:
                final = cached_similar[:limit]
                # 尝试写入缓存（如果失败，不影响返回结果）
                if query_cache_key:
                    try:
                        await cache_manager.set(query_cache_key, final)
                    except Exception as e:
                        logger.warning(f"写入缓存失败，但搜索成功: {e}")
                return final, True, "similar_cache"
        except Exception as e:
            logger.warning(f"读取相似缓存失败，继续降级策略: {e}")

        # 策略5：热门论文降级
        trending = await self._fetch_trending_fallback(limit)
        if trending:
            # 尝试写入缓存（如果失败，不影响返回结果）
            if query_cache_key:
                try:
                    await cache_manager.set(query_cache_key, trending)
                except Exception as e:
                    logger.warning(f"写入缓存失败，但搜索成功: {e}")
            return trending, True, "trending_fallback"

        return [], True, "all_failed"


search_engine = SearchEngine()
