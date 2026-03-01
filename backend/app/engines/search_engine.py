"""带降级策略的搜索引擎。"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.tools.literature_search import search_literature
from app.utils.cache_manager import cache_manager
from app.utils.keyword_expander import expand_keywords


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
        result: List[Dict[str, Any]] = []
        for query in TRENDING_QUERIES:
            papers = await self._search_with_retry(query, max(3, limit // 2))
            if papers:
                result.extend(papers)
            if len(self._deduplicate(result)) >= self.min_results:
                break
        return self._deduplicate(result)[:limit]

    async def search_with_fallback(self, interests: List[str], limit: int = 10) -> Tuple[List[Dict[str, Any]], bool, str]:
        """返回 papers, is_fallback, strategy。"""
        terms = [t.strip() for t in interests if t and t.strip()]
        if not terms:
            trending = await self._fetch_trending_fallback(limit)
            return trending, True, "trending_fallback"

        query_cache_key = cache_manager.generate_key("search", {"interests": terms, "limit": limit})
        cached_query = await cache_manager.get(query_cache_key)
        if cached_query:
            return cached_query, True, "cache_hit"

        all_results: List[Dict[str, Any]] = []

        # 策略1：组合搜索
        combined_query = " AND ".join(terms)
        combined_results = await self._search_with_retry(combined_query, limit)
        all_results.extend(combined_results)
        if len(self._deduplicate(all_results)) >= self.min_results:
            final = self._deduplicate(all_results)[:limit]
            await cache_manager.set(query_cache_key, final)
            return final, False, "combined"

        # 策略2：逐个关键词
        for term in terms:
            term_results = await self._search_with_retry(term, limit)
            if term_results:
                await self._write_term_cache(term, term_results, limit)
            all_results.extend(term_results)
        if len(self._deduplicate(all_results)) >= self.min_results:
            final = self._deduplicate(all_results)[:limit]
            await cache_manager.set(query_cache_key, final)
            return final, True, "individual"

        # 策略3：关键词扩展
        expanded = expand_keywords(terms)
        for term in expanded[:8]:
            term_results = await self._search_with_retry(term, max(3, limit // 2))
            if term_results:
                await self._write_term_cache(term, term_results, limit)
            all_results.extend(term_results)
        unique_results = self._deduplicate(all_results)
        if len(unique_results) >= self.min_results:
            final = unique_results[:limit]
            await cache_manager.set(query_cache_key, final)
            return final, True, "expanded"

        # 策略4：相似缓存降级
        cached_similar = await self._read_term_cache(terms + expanded[:8], limit)
        if cached_similar:
            final = cached_similar[:limit]
            await cache_manager.set(query_cache_key, final)
            return final, True, "similar_cache"

        # 策略5：热门论文降级
        trending = await self._fetch_trending_fallback(limit)
        if trending:
            await cache_manager.set(query_cache_key, trending)
            return trending, True, "trending_fallback"

        return [], True, "all_failed"


search_engine = SearchEngine()
