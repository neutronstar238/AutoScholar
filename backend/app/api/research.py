"""研究方向 API 路由"""
from collections import deque
from typing import Deque, List

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel
from loguru import logger

from app.engines.search_engine import search_engine
from app.utils.model_client import model_client

router = APIRouter()


class ResearchRecommendRequest(BaseModel):
    """研究方向推荐请求"""
    interests: List[str]
    limit: int = 5


FALLBACK_HISTORY: Deque[bool] = deque(maxlen=100)


def _fallback_rate() -> float:
    if not FALLBACK_HISTORY:
        return 0.0
    return sum(1 for x in FALLBACK_HISTORY if x) / len(FALLBACK_HISTORY)


def _build_troubleshooting_message(interests: List[str]) -> str:
    joined = "、".join(interests[:3])
    return (
        f"未检索到与“{joined}”高度匹配的论文，已返回通用推荐。"
        "建议尝试更广泛关键词，如 machine learning / NLP / computer vision。"
    )


@router.post("/recommend")
async def recommend(request: ResearchRecommendRequest):
    """基于研究兴趣推荐研究方向。"""
    try:
        logger.info(f"推荐研究方向，兴趣：{request.interests}")

        papers, is_fallback, strategy = await search_engine.search_with_fallback(
            interests=request.interests,
            limit=max(3, request.limit),
        )

        # 如果降级策略仍无结果，构造最小保底推荐
        if not papers:
            fallback_msg = _build_troubleshooting_message(request.interests)
            FALLBACK_HISTORY.append(True)
            return {
                "success": True,
                "is_fallback": True,
                "fallback_strategy": "empty_general_suggestion",
                "fallback_rate": _fallback_rate(),
                "recommendations": fallback_msg,
                "papers": [],
            }

        recent_papers = sorted(
            papers,
            key=lambda x: x.get("published", ""),
            reverse=True,
        )[: max(3, request.limit)]

        papers_summary = "\n\n".join([
            f"标题：{p.get('title', '')}\n"
            f"作者：{', '.join(p.get('authors', [])[:3])}\n"
            f"发布：{p.get('published', '')}\n"
            f"摘要：{p.get('abstract', '')[:200]}..."
            for p in recent_papers
        ])

        result = await model_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "你是一位资深学术研究顾问，请给出热点方向、研究机会、推荐论文和学习路径。",
                },
                {
                    "role": "user",
                    "content": f"用户研究兴趣：{', '.join(request.interests)}\n\n论文：\n{papers_summary}",
                },
            ],
            temperature=0.7,
            max_tokens=1800,
        )

        FALLBACK_HISTORY.append(is_fallback)
        rate = _fallback_rate()
        if rate > 0.2:
            logger.warning(f"推荐降级率过高: {rate:.2%}")

        return {
            "success": True,
            "interests": request.interests,
            "recommendations": (result or {}).get("content", _build_troubleshooting_message(request.interests)),
            "papers": recent_papers,
            "model": (result or {}).get("model"),
            "used_provider": (result or {}).get("used_provider"),
            "is_fallback": is_fallback,
            "fallback_strategy": strategy,
            "fallback_rate": rate,
        }

    except Exception as e:
        logger.error(f"推荐研究方向失败：{e}")
        raise HTTPException(status_code=500, detail=f"推荐失败：{str(e)}")
