"""研究方向 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.tools.literature_search import search_literature
from app.utils.model_client import model_client
from loguru import logger

router = APIRouter()


class ResearchRecommendRequest(BaseModel):
    """研究方向推荐请求"""
    interests: List[str]  # 研究兴趣关键词
    limit: int = 5  # 推荐数量


@router.post("/recommend")
async def recommend(request: ResearchRecommendRequest):
    """
    基于研究兴趣推荐研究方向
    
    分析用户的研究兴趣，推荐相关的研究方向和热点论文
    """
    try:
        logger.info(f"推荐研究方向，兴趣：{request.interests}")
        
        # 1. 搜索相关论文
        all_papers = []
        for interest in request.interests[:3]:  # 限制最多3个关键词
            papers = await search_literature(
                query=interest,
                limit=10,
                sort_by="submittedDate"
            )
            all_papers.extend(papers)
        
        if not all_papers:
            return {
                "success": False,
                "error": "未找到相关论文"
            }
        
        # 2. 去重并选择最新的论文
        unique_papers = {p['id']: p for p in all_papers}.values()
        recent_papers = sorted(
            unique_papers,
            key=lambda x: x.get('published', ''),
            reverse=True
        )[:request.limit]
        
        # 3. 构建论文摘要
        papers_summary = "\n\n".join([
            f"标题：{p['title']}\n作者：{', '.join(p['authors'][:3])}\n发布：{p['published']}\n摘要：{p['abstract'][:200]}..."
            for p in recent_papers
        ])
        
        # 4. 使用 LLM 分析研究方向
        messages = [
            {
                "role": "system",
                "content": """你是一位资深的学术研究顾问。基于用户的研究兴趣和最新论文，分析并推荐研究方向。

请提供：
1. 🔥 热点研究方向（3-5个）
2. 💡 研究机会（未充分探索的领域）
3. 🎯 推荐论文（从提供的论文中选择最相关的）
4. 📚 学习路径建议

使用 Markdown 格式，清晰结构化。"""
            },
            {
                "role": "user",
                "content": f"""用户研究兴趣：{', '.join(request.interests)}

最新相关论文：
{papers_summary}

请分析并推荐研究方向。"""
            }
        ]
        
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.8,
            max_tokens=2048
        )
        
        if result:
            return {
                "success": True,
                "interests": request.interests,
                "recommendations": result["content"],
                "papers": recent_papers,
                "model": result.get("model"),
                "used_provider": result.get("used_provider")
            }
        else:
            return {
                "success": False,
                "error": "LLM 调用失败"
            }
            
    except Exception as e:
        logger.error(f"推荐研究方向失败：{e}")
        raise HTTPException(
            status_code=500,
            detail=f"推荐失败：{str(e)}"
        )
