"""缓存管理器。"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, OrderedDict
from typing import Any, Optional

from loguru import logger

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None


class CacheManager:
    """统一缓存访问接口，优先使用 Redis，不可用时自动降级。"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        prefix: str = "autoscholar",
        ttl_seconds: int = 3600,
        max_local_keys: int = 1000,
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds
        self._client = None

        self._hits = 0
        self._misses = 0
        self._write_ok = 0
        self._local_lru: OrderedDict[str, bool] = OrderedDict()
        self._max_local_keys = max_local_keys
        self._hot_queries: Counter[str] = Counter()

    async def _get_client(self):
        if self._client is not None:
            return self._client

        if redis is None:
            logger.warning("redis 依赖不可用，缓存降级为无缓存模式")
            return None

        try:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            await self._client.ping()
            return self._client
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Redis 不可用，缓存降级为无缓存模式: {exc}")
            self._client = None
            return None

    def generate_key(self, namespace: str, payload: Any) -> str:
        """根据命名空间和载荷生成稳定缓存键。"""
        if isinstance(payload, str):
            normalized = payload.strip().lower()
        else:
            normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
        return f"{self.prefix}:{namespace}:{digest}"

    def _touch_lru(self, key: str) -> None:
        self._local_lru[key] = True
        self._local_lru.move_to_end(key)
        while len(self._local_lru) > self._max_local_keys:
            self._local_lru.popitem(last=False)

    async def get(self, key: str) -> Optional[Any]:
        client = await self._get_client()
        if client is None:
            self._misses += 1
            return None
        try:
            value = await client.get(key)
            if value:
                self._hits += 1
                self._touch_lru(key)
            else:
                self._misses += 1
            return json.loads(value) if value else None
        except Exception as exc:
            self._misses += 1
            logger.warning(f"缓存读取失败({key}): {exc}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        client = await self._get_client()
        if client is None:
            return False
        try:
            ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
            payload = json.dumps(value, ensure_ascii=False, default=str)
            await client.setex(key, ttl, payload)
            self._write_ok += 1
            self._touch_lru(key)
            return True
        except Exception as exc:
            logger.warning(f"缓存写入失败({key}): {exc}")
            return False

    def record_search_query(self, query: str) -> None:
        q = (query or "").strip().lower()
        if len(q) < 3:
            return
        self._hot_queries[q] += 1

    async def get_hot_searches(self, limit: int = 10) -> list[str]:
        items = self._hot_queries.most_common(limit)
        return [k for k, _ in items]

    def get_stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = 0.0 if total == 0 else self._hits / total
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "writes": self._write_ok,
            "tracked_keys": len(self._local_lru),
            "hot_queries": len(self._hot_queries),
            "max_local_keys": self._max_local_keys,
        }

    async def clear(self) -> dict:
        client = await self._get_client()
        deleted = 0
        if client is not None:
            try:
                keys = await client.keys(f"{self.prefix}:*")
                if keys:
                    deleted = await client.delete(*keys)
            except Exception as exc:
                logger.warning(f"缓存清理失败: {exc}")

        self._local_lru.clear()
        self._hot_queries.clear()
        self._hits = 0
        self._misses = 0
        self._write_ok = 0
        return {"deleted": int(deleted)}


cache_manager = CacheManager()
