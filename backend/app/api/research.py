"""研究方向 API 路由"""
from time import perf_counter
from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.engines.recommendation_engine import recommendation_engine
from app.utils.model_client import model_client
from app.utils.quality_monitor import quality_monitor

router = APIRouter()


class ResearchRecommendRequest(BaseModel):
    """研究方向推荐请求"""

    user_id: int = 0
    interests: List[str]
    limit: int = 5


class InterestSuggestRequest(BaseModel):
    user_id: int = 0
    text: str


class LearningPathRequest(BaseModel):
    user_id: int = 0
    interests: List[str]
    limit: int = 10


class RecommendationFeedbackRequest(BaseModel):
    user_id: int
    paper: dict
    feedback: str


class CrossDomainRequest(BaseModel):
    user_id: int = 0
    interests: List[str]
    limit: int = 10



def _build_troubleshooting_message(interests: List[str]) -> str:
    joined = "、".join(interests[:3])
    return (
        f"未检索到与“{joined}”高度匹配的论文，已返回通用推荐。"
        "建议尝试更广泛关键词，如 machine learning / NLP / computer vision。"
    )


def _build_prompt(interests: List[str], merged_interests: List[str], papers_summary: str, fallback_strategy: str) -> List[dict]:
    system_prompt = """
你是 AutoScholar 的首席学术顾问，擅长将文献证据转化为可执行研究计划。

请严格按以下要求输出：
1) 使用 Markdown，结构必须包含：
   - ## 研究方向总览
   - ## 热点方向（3-5个）
   - ## 机会点（至少3个）
   - ## 推荐论文解读（逐篇）
   - ## 4周行动计划
   - ## 风险与规避建议
2) 每个“热点方向”需包含：方向名、价值、可行性、适合初学者/进阶者。
3) 每篇推荐论文需包含：为何推荐、可复现性、潜在改进点。
4) 行动计划按“第1-4周”给出具体任务与产出物。
5) 如果是降级结果（fallback），请在总览里明确提示并提供缩小/改写关键词建议。
6) 语言为中文，术语可保留英文。
""".strip()

    user_prompt = f"""
用户兴趣：{', '.join(interests)}
画像增强兴趣：{', '.join(merged_interests)}
fallback策略：{fallback_strategy}

候选论文：
{papers_summary}

请基于以上信息输出研究方向建议。
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


@router.post("/recommend")
async def recommend(request: ResearchRecommendRequest):
    """基于研究兴趣推荐研究方向（P1/P2）。"""
    try:
        start_ts = perf_counter()
        logger.info(f"推荐研究方向，user_id={request.user_id}, 兴趣：{request.interests}")

        safe_limit = max(3, min(10, request.limit))
        rec = await recommendation_engine.generate_recommendations(
            interests=request.interests,
            user_id=request.user_id,
            limit=safe_limit,
        )

        papers = rec["papers"]
        is_fallback = rec["is_fallback"]
        strategy = rec["fallback_strategy"]

        if not papers:
            fallback_msg = _build_troubleshooting_message(request.interests)
            quality_monitor.record_fallback(True)
            quality_monitor.record_recommend_latency((perf_counter() - start_ts) * 1000)
            return {
                "success": True,
                "is_fallback": True,
                "fallback_strategy": "empty_general_suggestion",
                "fallback_rate": quality_monitor.fallback_rate(),
                "recommendations": fallback_msg,
                "papers": [],
                "profile_interests": rec.get("profile_interests", []),
            }

        papers_summary = "\n\n".join(
            [
                f"标题：{p.get('title', '')}\n"
                f"作者：{', '.join(p.get('authors', [])[:3])}\n"
                f"发布：{p.get('published', '')}\n"
                f"置信度：{p.get('confidence', 0.0)}\n"
                f"摘要：{p.get('abstract', '')[:240]}..."
                for p in papers
            ]
        )

        result = await model_client.chat_completion(
            messages=_build_prompt(
                interests=request.interests,
                merged_interests=rec.get("merged_interests", request.interests),
                papers_summary=papers_summary,
                fallback_strategy=strategy,
            ),
            temperature=0.65,
            max_tokens=2200,
        )

        quality_monitor.record_fallback(is_fallback)
        rate = quality_monitor.fallback_rate()
        if rate > 0.2:
            logger.warning(f"推荐降级率过高: {rate:.2%}")

        fallback_note = _build_troubleshooting_message(request.interests) if is_fallback else None
        quality_monitor.record_recommend_latency((perf_counter() - start_ts) * 1000)

        return {
            "success": True,
            "user_id": request.user_id,
            "interests": request.interests,
            "merged_interests": rec.get("merged_interests", request.interests),
            "profile_interests": rec.get("profile_interests", []),
            "recommendations": (result or {}).get("content", _build_troubleshooting_message(request.interests)),
            "papers": papers,
            "model": (result or {}).get("model"),
            "used_provider": (result or {}).get("used_provider"),
            "is_fallback": is_fallback,
            "fallback_strategy": strategy,
            "fallback_rate": rate,
            "fallback_note": fallback_note,
        }

    except Exception as e:
        logger.error(f"推荐研究方向失败：{e}")
        raise HTTPException(status_code=500, detail=f"推荐失败：{str(e)}")


@router.post("/suggest-interests")
async def suggest_interests(request: InterestSuggestRequest):
    """基于输入文本和用户画像提供兴趣关键词建议。"""
    try:
        suggestions = await recommendation_engine.suggest_interests(request.user_id, limit=10)
        return {"success": True, "user_id": request.user_id, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"兴趣建议失败：{e}")
        raise HTTPException(status_code=500, detail=f"兴趣建议失败：{str(e)}")


@router.post("/learning-path")
async def learning_path(request: LearningPathRequest):
    """根据兴趣生成分阶段学习路径。"""
    try:
        safe_limit = max(3, min(15, request.limit))
        rec = await recommendation_engine.generate_recommendations(
            interests=request.interests,
            user_id=request.user_id,
            limit=safe_limit,
        )
        path = recommendation_engine.generate_learning_path(rec.get("papers", []))
        return {
            "success": True,
            "user_id": request.user_id,
            "interests": request.interests,
            "is_fallback": rec.get("is_fallback", False),
            "fallback_strategy": rec.get("fallback_strategy"),
            "learning_path": path,
        }
    except Exception as e:
        logger.error(f"学习路径生成失败：{e}")
        raise HTTPException(status_code=500, detail=f"学习路径生成失败：{str(e)}")


@router.post("/feedback")
async def recommendation_feedback(request: RecommendationFeedbackRequest):
    """记录推荐反馈并更新用户画像。"""
    try:
        if request.feedback not in {"helpful", "not_helpful", "ignore"}:
            raise HTTPException(status_code=400, detail="feedback 必须是 helpful/not_helpful/ignore")

        metrics = await recommendation_engine.record_recommendation_feedback(
            user_id=request.user_id,
            paper=request.paper,
            feedback=request.feedback,
        )
        return {"success": True, "user_id": request.user_id, "feedback": request.feedback, "metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"反馈记录失败：{e}")
        raise HTTPException(status_code=500, detail=f"反馈记录失败：{str(e)}")


@router.post("/cross-domain")
async def cross_domain(request: CrossDomainRequest):
    """发现跨领域研究机会。"""
    try:
        safe_limit = max(3, min(20, request.limit))
        rec = await recommendation_engine.generate_recommendations(
            interests=request.interests,
            user_id=request.user_id,
            limit=safe_limit,
        )
        opportunities = recommendation_engine.find_cross_domain_opportunities(rec.get("papers", []))
        return {
            "success": True,
            "user_id": request.user_id,
            "interests": request.interests,
            "count": len(opportunities),
            "opportunities": opportunities,
        }
    except Exception as e:
        logger.error(f"跨领域机会发现失败：{e}")
        raise HTTPException(status_code=500, detail=f"跨领域机会发现失败：{str(e)}")
