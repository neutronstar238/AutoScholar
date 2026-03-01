import pytest

from app.engines.search_engine import SearchEngine
from app.utils.cache_manager import CacheManager
from app.utils.keyword_expander import expand_keywords, translate_keyword


class InMemoryRedis:
    def __init__(self):
        self.data = {}

    async def ping(self):
        return True

    async def get(self, key):
        return self.data.get(key)

    async def setex(self, key, ttl, payload):
        self.data[key] = payload
        return True


@pytest.mark.asyncio
async def test_cache_roundtrip(monkeypatch):
    fake = InMemoryRedis()

    class DummyRedis:
        @staticmethod
        def from_url(*args, **kwargs):
            return fake

    monkeypatch.setattr("app.utils.cache_manager.redis", DummyRedis)

    manager = CacheManager(redis_url="redis://fake")
    key = manager.generate_key("k", {"q": "ai"})
    assert await manager.set(key, {"ok": 1}) is True
    assert await manager.get(key) == {"ok": 1}


def test_keyword_expansion_translation():
    terms = expand_keywords(["人工智能", "llm"])
    assert "artificial intelligence" in [t.lower() for t in terms]
    assert any("large language model" in t.lower() for t in terms)
    assert translate_keyword("机器学习") == "machine learning"


@pytest.mark.asyncio
async def test_search_engine_fallback_individual(monkeypatch):
    engine = SearchEngine(min_results=3)

    async def fake_search(query, limit, source="arxiv", sort_by="submittedDate"):
        if query == "a AND b":
            return []
        return [
            {"id": f"{query}-1", "title": "t1", "published": "2025-01-01", "authors": []},
            {"id": f"{query}-2", "title": "t2", "published": "2025-01-02", "authors": []},
            {"id": f"{query}-3", "title": "t3", "published": "2025-01-03", "authors": []},
        ]

    async def fake_get(_):
        return None

    async def fake_set(*_args, **_kwargs):
        return True

    monkeypatch.setattr("app.engines.search_engine.search_literature", fake_search)
    monkeypatch.setattr("app.engines.search_engine.cache_manager.get", fake_get)
    monkeypatch.setattr("app.engines.search_engine.cache_manager.set", fake_set)

    papers, is_fallback, strategy = await engine.search_with_fallback(["a", "b"], limit=5)
    assert len(papers) >= 3
    assert is_fallback is True
    assert strategy == "individual"


@pytest.mark.asyncio
async def test_search_engine_fallback_to_similar_cache(monkeypatch):
    engine = SearchEngine(min_results=3)

    async def fake_search(*_args, **_kwargs):
        return []

    async def fake_set(*_args, **_kwargs):
        return True

    async def fake_get(key):
        if "search_term" in key:
            return [
                {"id": "cache-1", "title": "cached paper", "published": "2025-01-01", "authors": []},
                {"id": "cache-2", "title": "cached paper2", "published": "2025-01-02", "authors": []},
                {"id": "cache-3", "title": "cached paper3", "published": "2025-01-03", "authors": []},
            ]
        return None

    monkeypatch.setattr("app.engines.search_engine.search_literature", fake_search)
    monkeypatch.setattr("app.engines.search_engine.cache_manager.get", fake_get)
    monkeypatch.setattr("app.engines.search_engine.cache_manager.set", fake_set)

    papers, is_fallback, strategy = await engine.search_with_fallback(["a"], limit=3)
    assert len(papers) == 3
    assert is_fallback is True
    assert strategy == "similar_cache"


@pytest.mark.asyncio
async def test_search_engine_fallback_to_trending(monkeypatch):
    engine = SearchEngine(min_results=3)

    async def fake_set(*_args, **_kwargs):
        return True

    async def fake_get(_key):
        return None

    async def fake_search(query, limit, source="arxiv", sort_by="submittedDate"):
        if query in {"machine learning", "large language model"}:
            return [
                {"id": f"{query}-1", "title": "trend1", "published": "2025-01-01", "authors": []},
                {"id": f"{query}-2", "title": "trend2", "published": "2025-01-02", "authors": []},
            ]
        return []

    monkeypatch.setattr("app.engines.search_engine.search_literature", fake_search)
    monkeypatch.setattr("app.engines.search_engine.cache_manager.get", fake_get)
    monkeypatch.setattr("app.engines.search_engine.cache_manager.set", fake_set)

    papers, is_fallback, strategy = await engine.search_with_fallback(["very-special-topic"], limit=4)
    assert len(papers) >= 3
    assert is_fallback is True
    assert strategy == "trending_fallback"
