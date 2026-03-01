"""带降级策略的搜索引擎。"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.tools.literature_search import search_literature
from app.utils.cache_manager import cache_manager
from app.utils.keyword_expander import expand_keywords


class SearchEngine:
    def __init__(self, min_results: int = 3):
        self.min_results = min_results

    async def _search_with_retry(self, query: str, limit: int) -> List[Dict[str, Any]]:
        delay = 0.5
        for attempt in range(3):
            try:
                return await search_literature(query=query, limit=limit, source="arxiv", sort_by="submittedDate")
            except Exception as exc:
                logger.warning(f"搜索失败 attempt={attempt+1} query={query}: {exc}")
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

    async def search_with_fallback(self, interests: List[str], limit: int = 10) -> Tuple[List[Dict[str, Any]], bool, str]:
        """返回 papers, is_fallback, strategy。"""
        terms = [t.strip() for t in interests if t and t.strip()]
        if not terms:
            return [], True, "empty_query"

        cache_key = cache_manager.generate_key("search", {"interests": terms, "limit": limit})
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached, True, "cache_hit"

        all_results: List[Dict[str, Any]] = []

        # 策略1：组合搜索
        combined_query = " AND ".join(terms)
        all_results.extend(await self._search_with_retry(combined_query, limit))
        if len(self._deduplicate(all_results)) >= self.min_results:
            final = self._deduplicate(all_results)[:limit]
            await cache_manager.set(cache_key, final)
            return final, False, "combined"

        # 策略2：逐个关键词
        for term in terms:
            all_results.extend(await self._search_with_retry(term, limit))
        if len(self._deduplicate(all_results)) >= self.min_results:
            final = self._deduplicate(all_results)[:limit]
            await cache_manager.set(cache_key, final)
            return final, True, "individual"

        # 策略3：关键词扩展
        expanded = expand_keywords(terms)
        for term in expanded[:8]:
            all_results.extend(await self._search_with_retry(term, max(3, limit // 2)))
        unique_results = self._deduplicate(all_results)
        if len(unique_results) >= self.min_results:
            final = unique_results[:limit]
            await cache_manager.set(cache_key, final)
            return final, True, "expanded"

        # 策略4：相似缓存降级（简化：直接使用当前缓存键）
        if cached:
            return cached, True, "similar_cache"

        # 策略5：热门论文降级（由调用方提供）
        return unique_results[:limit], True, "trending_fallback"


search_engine = SearchEngine()
