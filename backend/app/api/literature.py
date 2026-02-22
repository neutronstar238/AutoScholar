"""
文献检索 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.tools.literature_search import search_literature
from app.agents.researcher import ResearcherAgent

router = APIRouter()
researcher = ResearcherAgent()


class LiteratureSearchRequest(BaseModel):
    """文献搜索请求"""
    query: str
    limit: int = 10
    source: str = "arxiv"
    sort_by: str = "relevance"  # relevance | submittedDate | lastUpdatedDate


class LiteratureSearchResponse(BaseModel):
    """文献搜索响应"""
    success: bool
    data: dict


@router.post("/search", response_model=LiteratureSearchResponse)
async def search_papers(request: LiteratureSearchRequest):
    """
    搜索学术文献
    
    支持 arXiv 和 Semantic Scholar
    
    排序选项:
    - relevance: 相关性排序（默认）
    - submittedDate: 提交日期排序
    - lastUpdatedDate: 最后更新日期排序
    """
    try:
        results = await search_literature(
            query=request.query,
            limit=request.limit,
            source=request.source,
            sort_by=request.sort_by
        )
        
        return LiteratureSearchResponse(
            success=True,
            data={
                "total": len(results),
                "papers": results
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败：{str(e)}"
        )


@router.get("/search/simple")
async def search_papers_simple(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="结果数量"),
    sort_by: str = Query("relevance", description="排序方式: relevance | submittedDate | lastUpdatedDate")
):
    """简化的文献搜索接口"""
    try:
        results = await search_literature(q, limit, sort_by=sort_by)
        return {
            "success": True,
            "count": len(results),
            "papers": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
