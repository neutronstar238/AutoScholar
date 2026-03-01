import pytest

from app.engines.recommendation_engine import RecommendationEngine
from app.engines.user_profile_manager import UserProfileManager


def test_user_profile_manager_update_and_extract():
    mgr = UserProfileManager(max_keywords=10)
    mgr.update_interest_from_search(1, "large language model safety")
    mgr.update_interest_from_reading(1, "Scaling Laws for Language Models", "model scaling and training", feedback="helpful")

    interests = mgr.extract_interests(1, top_k=5)
    assert len(interests) > 0
    assert any("language" in i["keyword"] or "model" in i["keyword"] for i in interests)


def test_user_profile_suggest_for_input():
    mgr = UserProfileManager()
    suggestions = mgr.suggest_interests_for_input("研究多模态大模型和计算机视觉结合")
    assert len(suggestions) > 0


@pytest.mark.asyncio
async def test_recommendation_engine_generate(monkeypatch):
    engine = RecommendationEngine()

    async def fake_search_with_fallback(interests, limit):
        return [
            {
                "id": "p1",
                "title": "Large Language Model Alignment",
                "abstract": "alignment and safety for llm",
                "published": "2025-01-10",
                "authors": ["a"],
            },
            {
                "id": "p2",
                "title": "Vision-Language Models",
                "abstract": "vlm and multimodal representation",
                "published": "2024-12-10",
                "authors": ["b"],
            },
            {
                "id": "p3",
                "title": "Prompt Optimization",
                "abstract": "prompt engineering methods",
                "published": "2023-12-10",
                "authors": ["c"],
            },
        ], True, "expanded"

    monkeypatch.setattr("app.engines.recommendation_engine.search_engine.search_with_fallback", fake_search_with_fallback)

    result = await engine.generate_recommendations(user_id=7, interests=["llm", "alignment"], limit=5)

    assert result["is_fallback"] is True
    assert result["fallback_strategy"] == "expanded"
    assert 3 <= len(result["papers"]) <= 10
    assert all("confidence" in p for p in result["papers"])
