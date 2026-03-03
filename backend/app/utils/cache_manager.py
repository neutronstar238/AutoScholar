"""缓存管理器。

支持三种缓存模式：
1. Redis（生产环境）
2. 本地文件缓存（开发环境，默认）
3. 内存缓存（测试环境）
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Optional

from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except Exception:  # pragma: no cover
    redis = None
    REDIS_AVAILABLE = False


class LocalFileCache:
    """基于本地文件系统的缓存实现。
    
    特点：
    - 持久化存储，重启不丢失
    - 自动过期清理
    - LRU淘汰策略
    - 线程安全
    """
    
    def __init__(self, cache_dir: str = ".cache", max_size_mb: int = 100):
        """初始化本地文件缓存。
        
        Args:
            cache_dir: 缓存目录路径
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        logger.info(f"本地文件缓存已启用: {self.cache_dir.absolute()}")
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径。"""
        # 使用key的hash作为文件名，避免特殊字符问题
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def _get_meta_path(self, key: str) -> Path:
        """获取元数据文件路径。"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.meta"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值。"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_meta_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            # 检查是否过期
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                expire_at = meta.get("expire_at", 0)
                if expire_at > 0 and time.time() > expire_at:
                    # 已过期，删除文件
                    cache_path.unlink(missing_ok=True)
                    meta_path.unlink(missing_ok=True)
                    return None
                
                # 更新访问时间（用于LRU）
                meta["last_access"] = time.time()
                meta_path.write_text(json.dumps(meta), encoding="utf-8")
            
            # 读取缓存值
            value = json.loads(cache_path.read_text(encoding="utf-8"))
            return value
        
        except Exception as e:
            logger.warning(f"读取本地缓存失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """设置缓存值。"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_meta_path(key)
        
        try:
            # 写入缓存值
            cache_path.write_text(
                json.dumps(value, ensure_ascii=False, default=str),
                encoding="utf-8"
            )
            
            # 写入元数据
            meta = {
                "key": key,
                "created_at": time.time(),
                "last_access": time.time(),
                "expire_at": time.time() + ttl_seconds if ttl_seconds > 0 else 0,
                "size": cache_path.stat().st_size
            }
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            
            # 检查缓存大小，必要时清理
            await self._cleanup_if_needed()
            
            return True
        
        except Exception as e:
            logger.warning(f"写入本地缓存失败 {key}: {e}")
            return False
    
    async def keys(self, pattern: str) -> list[str]:
        """获取匹配模式的所有键。
        
        注意：由于使用hash作为文件名，这里返回的是所有键，
        需要在上层进行模式匹配。
        """
        keys = []
        for meta_file in self.cache_dir.glob("*.meta"):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                key = meta.get("key", "")
                if key:
                    keys.append(key)
            except Exception:
                continue
        return keys
    
    async def delete(self, *keys: str) -> int:
        """删除指定的键。"""
        deleted = 0
        for key in keys:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_meta_path(key)
            
            if cache_path.exists():
                cache_path.unlink()
                deleted += 1
            if meta_path.exists():
                meta_path.unlink()
        
        return deleted
    
    async def _cleanup_if_needed(self):
        """检查缓存大小，必要时清理旧文件。"""
        try:
            # 计算总大小
            total_size = sum(
                f.stat().st_size 
                for f in self.cache_dir.glob("*.json")
            )
            
            if total_size <= self.max_size_bytes:
                return
            
            # 需要清理，按LRU策略删除
            logger.info(f"缓存大小超限 ({total_size / 1024 / 1024:.2f}MB)，开始清理...")
            
            # 收集所有缓存文件及其访问时间
            files_info = []
            for meta_file in self.cache_dir.glob("*.meta"):
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    files_info.append({
                        "key": meta.get("key", ""),
                        "last_access": meta.get("last_access", 0),
                        "size": meta.get("size", 0)
                    })
                except Exception:
                    continue
            
            # 按访问时间排序（最旧的在前）
            files_info.sort(key=lambda x: x["last_access"])
            
            # 删除最旧的文件，直到大小降到80%以下
            target_size = self.max_size_bytes * 0.8
            current_size = total_size
            deleted_count = 0
            
            for file_info in files_info:
                if current_size <= target_size:
                    break
                
                key = file_info["key"]
                await self.delete(key)
                current_size -= file_info["size"]
                deleted_count += 1
            
            logger.info(f"清理完成，删除了 {deleted_count} 个缓存文件")
        
        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")
    
    async def ping(self) -> bool:
        """测试缓存是否可用。"""
        return self.cache_dir.exists()
    
    def get_cache_size(self) -> dict:
        """获取缓存统计信息。"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            file_count = len(list(self.cache_dir.glob("*.json")))
            
            return {
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "file_count": file_count,
                "max_size_mb": self.max_size_bytes / 1024 / 1024,
                "usage_percent": round(total_size / self.max_size_bytes * 100, 2)
            }
        except Exception:
            return {
                "total_size_mb": 0,
                "file_count": 0,
                "max_size_mb": self.max_size_bytes / 1024 / 1024,
                "usage_percent": 0
            }


class CacheManager:
    """统一缓存访问接口。
    
    优先级：
    1. Redis（如果配置且可用）
    2. 本地文件缓存（默认）
    3. 内存缓存（降级）
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        prefix: str = "autoscholar",
        ttl_seconds: int = 3600,
        max_local_keys: int = 1000,
        cache_dir: str = ".cache",
        use_redis: bool = False,  # 默认不使用Redis
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds
        self._redis_client = None
        
        # 只有明确启用时才尝试连接Redis
        self._use_redis = use_redis and REDIS_AVAILABLE
        
        # 本地文件缓存（默认启用）
        self._file_cache = LocalFileCache(cache_dir=cache_dir)
        self._cache_mode = "file"  # file, redis, memory
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._write_ok = 0
        self._local_lru: OrderedDict[str, bool] = OrderedDict()
        self._max_local_keys = max_local_keys
        self._hot_queries: Counter[str] = Counter()
        
        if self._use_redis:
            logger.info(f"缓存管理器初始化: 尝试连接Redis, 前缀={prefix}")
        else:
            logger.info(f"缓存管理器初始化: 使用本地文件缓存, 前缀={prefix}")

    async def _get_redis_client(self):
        """获取Redis客户端（如果可用）。"""
        if not self._use_redis:
            return None
            
        if self._redis_client is not None:
            return self._redis_client

        if redis is None:
            return None

        try:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis_client.ping()
            self._cache_mode = "redis"
            logger.success(f"Redis连接成功: {self.redis_url}")
            return self._redis_client
        except Exception as exc:
            logger.warning(f"Redis不可用，使用本地文件缓存: {exc}")
            self._redis_client = None
            self._cache_mode = "file"
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
        """获取缓存值。"""
        # 尝试Redis
        redis_client = await self._get_redis_client()
        if redis_client is not None:
            try:
                value = await redis_client.get(key)
                if value:
                    self._hits += 1
                    self._touch_lru(key)
                    return json.loads(value)
                else:
                    self._misses += 1
                    return None
            except Exception as exc:
                logger.warning(f"Redis读取失败，降级到文件缓存: {exc}")
                self._cache_mode = "file"
        
        # 使用本地文件缓存
        value = await self._file_cache.get(key)
        if value:
            self._hits += 1
            self._touch_lru(key)
        else:
            self._misses += 1
        return value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """设置缓存值。"""
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        
        # 尝试Redis
        redis_client = await self._get_redis_client()
        if redis_client is not None:
            try:
                payload = json.dumps(value, ensure_ascii=False, default=str)
                await redis_client.setex(key, ttl, payload)
                self._write_ok += 1
                self._touch_lru(key)
                return True
            except Exception as exc:
                logger.warning(f"Redis写入失败，降级到文件缓存: {exc}")
                self._cache_mode = "file"
        
        # 使用本地文件缓存
        success = await self._file_cache.set(key, value, ttl)
        if success:
            self._write_ok += 1
            self._touch_lru(key)
        return success

    def record_search_query(self, query: str) -> None:
        q = (query or "").strip().lower()
        if len(q) < 3:
            return
        self._hot_queries[q] += 1

    async def get_hot_searches(self, limit: int = 10) -> list[str]:
        items = self._hot_queries.most_common(limit)
        return [k for k, _ in items]

    async def get_cached_results(self, cache_key: str) -> Optional[list[dict]]:
        """获取缓存的搜索结果（设计文档接口）。"""
        return await self.get(cache_key)

    async def set_cached_results(
        self, cache_key: str, results: list[dict], ttl: int = 3600
    ) -> bool:
        """存储搜索结果到缓存（设计文档接口）。"""
        return await self.set(cache_key, results, ttl)

    def generate_cache_key(
        self, keywords: list[str], filters: Optional[dict] = None
    ) -> str:
        """
        生成缓存键（设计文档接口）。
        
        格式：search:{sorted_keywords}:{filter_hash}
        """
        sorted_keywords = "_".join(sorted(k.lower().strip() for k in keywords))
        if filters:
            filter_str = json.dumps(filters, sort_keys=True, default=str)
            filter_hash = hashlib.sha256(filter_str.encode("utf-8")).hexdigest()[:8]
            return f"{self.prefix}:search:{sorted_keywords}:{filter_hash}"
        return f"{self.prefix}:search:{sorted_keywords}"

    async def get_similar_results(
        self, keywords: list[str], threshold: float = 0.7
    ) -> list[dict]:
        """获取相似查询的缓存结果（用于降级策略）。"""
        # 尝试Redis
        redis_client = await self._get_redis_client()
        if redis_client is not None:
            try:
                pattern = f"{self.prefix}:search:*"
                keys = await redis_client.keys(pattern)
                
                if keys:
                    return await self._find_similar_in_keys(keys, keywords, threshold, redis_client.get)
            except Exception as exc:
                logger.warning(f"Redis相似查询失败，降级到文件缓存: {exc}")
        
        # 使用本地文件缓存
        try:
            pattern = f"{self.prefix}:search:*"
            keys = await self._file_cache.keys(pattern)
            
            if keys:
                return await self._find_similar_in_keys(keys, keywords, threshold, self._file_cache.get)
        except Exception as exc:
            logger.warning(f"获取相似缓存结果失败: {exc}")
        
        return []
    
    async def _find_similar_in_keys(
        self, keys: list[str], keywords: list[str], threshold: float, get_func
    ) -> list[dict]:
        """在给定的键列表中查找相似的缓存结果。"""
        query_keywords = set(k.lower().strip() for k in keywords)
        
        for key in keys:
            parts = key.split(":")
            if len(parts) < 3:
                continue
            
            cached_keywords_str = parts[2]
            cached_keywords = set(cached_keywords_str.split("_"))
            
            if not cached_keywords:
                continue
            
            # 计算 Jaccard 相似度
            intersection = query_keywords & cached_keywords
            union = query_keywords | cached_keywords
            similarity = len(intersection) / len(union) if union else 0.0
            
            if similarity >= threshold:
                value = await get_func(key)
                if value:
                    if isinstance(value, str):
                        results = json.loads(value)
                    else:
                        results = value
                    
                    logger.info(
                        f"找到相似缓存结果，相似度: {similarity:.2f}, "
                        f"查询: {keywords}, 缓存: {list(cached_keywords)}"
                    )
                    return results if isinstance(results, list) else []
        
        return []

    def get_stats(self) -> dict:
        """获取缓存统计信息。"""
        total = self._hits + self._misses
        hit_rate = 0.0 if total == 0 else self._hits / total
        
        stats = {
            "mode": self._cache_mode,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "writes": self._write_ok,
            "tracked_keys": len(self._local_lru),
            "hot_queries": len(self._hot_queries),
            "max_local_keys": self._max_local_keys,
        }
        
        # 添加文件缓存统计
        if self._cache_mode == "file":
            file_stats = self._file_cache.get_cache_size()
            stats.update({
                "file_cache": file_stats
            })
        
        return stats

    async def clear(self) -> dict:
        """清空所有缓存。"""
        deleted = 0
        
        # 清理Redis
        redis_client = await self._get_redis_client()
        if redis_client is not None:
            try:
                keys = await redis_client.keys(f"{self.prefix}:*")
                if keys:
                    deleted = await redis_client.delete(*keys)
            except Exception as exc:
                logger.warning(f"Redis缓存清理失败: {exc}")
        
        # 清理文件缓存
        try:
            file_keys = await self._file_cache.keys(f"{self.prefix}:*")
            if file_keys:
                file_deleted = await self._file_cache.delete(*file_keys)
                deleted += file_deleted
        except Exception as exc:
            logger.warning(f"文件缓存清理失败: {exc}")
        
        # 清理内存统计
        self._local_lru.clear()
        self._hot_queries.clear()
        self._hits = 0
        self._misses = 0
        self._write_ok = 0
        
        return {"deleted": int(deleted), "mode": self._cache_mode}


# 全局缓存管理器实例
# 默认使用本地文件缓存（backend/.cache目录）
# 如果需要使用Redis，设置环境变量 USE_REDIS=true
cache_manager = CacheManager(
    cache_dir="backend/.cache" if os.path.exists("backend") else ".cache",
    use_redis=os.getenv("USE_REDIS", "false").lower() == "true"
)
