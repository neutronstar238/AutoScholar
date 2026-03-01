import pytest

from app.engines.recommendation_engine import RecommendationEngine
from app.engines.user_profile_manager import UserProfileManager
from app.engines.trend_analyzer import TrendAnalyzer
from app.utils.feedback_collector import FeedbackCollector


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
                "citations": 50,
            },
            {
                "id": "p2",
                "title": "Vision-Language Models",
                "abstract": "vlm and multimodal representation",
                "published": "2024-12-10",
                "authors": ["b"],
                "citations": 30,
            },
            {
                "id": "p3",
                "title": "Prompt Optimization",
                "abstract": "prompt engineering methods",
                "published": "2023-12-10",
                "authors": ["c"],
                "citations": 10,
            },
        ], True, "expanded"

    monkeypatch.setattr("app.engines.recommendation_engine.search_engine.search_with_fallback", fake_search_with_fallback)

    result = await engine.generate_recommendations(user_id=7, interests=["llm", "alignment"], limit=5)

    assert result["is_fallback"] is True
    assert result["fallback_strategy"] == "expanded"
    assert 3 <= len(result["papers"]) <= 10
    assert all("confidence" in p for p in result["papers"])
    assert all("trend_score" in p for p in result["papers"])


def test_trend_analyzer_scores_and_topics():
    analyzer = TrendAnalyzer()
    papers = [
        {"title": "Survey of LLM Alignment", "published": "2025-01-01", "citations": 100},
        {"title": "Efficient RAG Training", "published": "2024-01-01", "citations": 60},
        {"title": "Agent Planning with Tools", "published": "2023-01-01", "citations": 20},
    ]

    scored = analyzer.analyze_papers(papers)
    assert len(scored) == 3
    assert scored[0]["trend_score"] >= scored[-1]["trend_score"]

    topics = analyzer.get_trending_topics(papers, top_k=3)
    assert len(topics) > 0


def test_feedback_collector_metrics():
    collector = FeedbackCollector()
    collector.record_view(1)
    collector.record_view(1)
    collector.record_feedback(1, "helpful")
    collector.record_feedback(1, "not_helpful")

    metrics = collector.calculate_metrics(1)
    assert metrics["views"] == 2.0
    assert 0.0 <= metrics["ctr"] <= 1.0
    assert 0.0 <= metrics["helpfulness_ratio"] <= 1.0


def test_learning_path_generation_stage_bounds():
    engine = RecommendationEngine()
    papers = [
        {"title": "A Survey on LLM", "published": "2021-01-01"},
        {"title": "Foundational NLP Model", "published": "2022-01-01"},
        {"title": "Instruction Tuning", "published": "2023-01-01"},
        {"title": "Tool-Augmented Agent", "published": "2024-01-01"},
        {"title": "Advanced Multimodal Agent", "published": "2025-01-01"},
    ]

    path = engine.generate_learning_path(papers)
    assert 3 <= len(path["stages"]) <= 5
    assert path["total_papers"] <= 15
    first_titles = [p["title"].lower() for p in path["stages"][0]["papers"]]
    assert any("survey" in t for t in first_titles)
