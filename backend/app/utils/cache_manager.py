"""缓存管理器。"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

from loguru import logger

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None


class CacheManager:
    """统一缓存访问接口，优先使用 Redis，不可用时自动降级。"""

    def __init__(self, redis_url: Optional[str] = None, prefix: str = "autoscholar", ttl_seconds: int = 3600):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds
        self._client = None

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

    async def get(self, key: str) -> Optional[Any]:
        client = await self._get_client()
        if client is None:
            return None
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
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
            return True
        except Exception as exc:
            logger.warning(f"缓存写入失败({key}): {exc}")
            return False


cache_manager = CacheManager()
