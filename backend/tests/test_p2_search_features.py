import pytest

from app.utils.autocomplete_service import AutocompleteService
from app.utils.cache_manager import CacheManager
from app.utils.filter_manager import FilterManager
from app.utils.query_parser import QueryParser
from app.utils.relevance_scorer import RelevanceScorer
from app.utils.search_history_manager import SearchHistoryManager


def test_query_parser_precedence_and_parentheses():
    parser = QueryParser()
    ast = parser.parse_query("llm OR vision AND NOT robotics")
    query = parser.to_search_query(ast)
    assert "AND" in query and "OR" in query and "NOT" in query


def test_filter_manager_intersection():
    mgr = FilterManager()
    papers = [
        {"title": "A", "published": "2024-01-01", "authors": ["Alice"], "categories": ["cs.AI"]},
        {"title": "B", "published": "2022-01-01", "authors": ["Bob"], "categories": ["cs.CL"]},
    ]
    out = mgr.apply_filters(papers, start_date="2023-01-01", author="alice", category="cs.ai")
    assert len(out) == 1
    assert out[0]["title"] == "A"


def test_relevance_scorer_weighted():
    scorer = RelevanceScorer()
    p = {"title": "LLM for Vision", "abstract": "llm llm in multimodal", "published": "2025-01-01"}
    s = scorer.calculate_relevance(p, ["llm", "vision"])
    assert 0.0 <= s <= 1.0


def test_search_history_limit_and_clear():
    mgr = SearchHistoryManager()
    for i in range(60):
        mgr.record(1, f"q{i}")
    recent = mgr.get_recent(1, limit=50)
    assert len(recent) == 50
    removed = mgr.clear(1)
    assert removed == 60


@pytest.mark.asyncio
async def test_hot_searches_and_stats(monkeypatch):
    fake = CacheManager()

    class DummyRedis:
        @staticmethod
        def from_url(*_args, **_kwargs):
            class _Client:
                async def ping(self):
                    return True

                async def get(self, _):
                    return None

                async def setex(self, *_):
                    return True

                async def keys(self, _):
                    return []

                async def delete(self, *_):
                    return 0

            return _Client()

    monkeypatch.setattr("app.utils.cache_manager.redis", DummyRedis)

    fake.record_search_query("llm")
    fake.record_search_query("llm")
    fake.record_search_query("vision")
    hot = await fake.get_hot_searches(limit=2)
    assert hot[0] == "llm"
    assert "hit_rate" in fake.get_stats()


@pytest.mark.asyncio
async def test_autocomplete_prefers_history_and_hot(monkeypatch):
    service = AutocompleteService()

    from app.utils import autocomplete_service as ac_mod

    ac_mod.search_history_manager.record(9, "machine learning ops")
    ac_mod.cache_manager.record_search_query("machine translation")

    suggestions = await service.get_suggestions(user_id=9, prefix="mach", limit=5)
    assert len(suggestions) > 0
    assert suggestions[0].lower().startswith("mach")
