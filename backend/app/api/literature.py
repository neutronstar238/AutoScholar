"""文献检索 API 路由"""

from __future__ import annotations

from time import perf_counter
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.tools.literature_search import search_literature
from app.utils.autocomplete_service import autocomplete_service
from app.utils.cache_manager import cache_manager
from app.utils.filter_manager import filter_manager
from app.utils.query_parser import query_parser
from app.utils.relevance_scorer import relevance_scorer
from app.utils.search_history_manager import search_history_manager
from app.utils.quality_monitor import quality_monitor

router = APIRouter()


class LiteratureSearchRequest(BaseModel):
    """文献搜索请求"""

    user_id: int = 0
    query: str
    limit: int = 10
    source: str = "arxiv"
    sort_by: str = "relevance"  # relevance | submittedDate | lastUpdatedDate
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None


class LiteratureSearchResponse(BaseModel):
    """文献搜索响应"""

    success: bool
    data: dict


@router.post("/search", response_model=LiteratureSearchResponse)
async def search_papers(request: LiteratureSearchRequest):
    """增强文献搜索：布尔解析 + 高级过滤 + 相关性评分 + 历史/热门统计。"""
    try:
        start_ts = perf_counter()
        ast = query_parser.parse_query(request.query)
        parsed_query = query_parser.to_search_query(ast)

        results = await search_literature(
            query=parsed_query,
            limit=max(1, min(50, request.limit)),
            source=request.source,
            sort_by=request.sort_by,
        )

        filtered = filter_manager.apply_filters(
            results,
            start_date=request.start_date,
            end_date=request.end_date,
            author=request.author,
            category=request.category,
        )

        query_terms = [t for t in request.query.replace("(", " ").replace(")", " ").split() if t.upper() not in {"AND", "OR", "NOT"}]
        ranked = relevance_scorer.score_and_sort(filtered, query_terms)

        search_history_manager.record(request.user_id, request.query)
        cache_manager.record_search_query(request.query)

        quality_monitor.record_search_latency((perf_counter() - start_ts) * 1000)
        return LiteratureSearchResponse(
            success=True,
            data={
                "total": len(ranked),
                "papers": ranked,
                "query_ast": ast,
                "parsed_query": parsed_query,
                "applied_filters": {
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "author": request.author,
                    "category": request.category,
                },
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败：{str(e)}")


@router.get("/search/simple")
async def search_papers_simple(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="结果数量"),
    sort_by: str = Query("relevance", description="排序方式: relevance | submittedDate | lastUpdatedDate"),
):
    """简化的文献搜索接口"""
    try:
        results = await search_literature(q, limit, sort_by=sort_by)
        return {"success": True, "count": len(results), "papers": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/search-history")
async def get_search_history(user_id: int = Query(0), limit: int = Query(50, ge=1, le=200)):
    """返回用户最近搜索历史（最多 50 条默认）。"""
    return {
        "success": True,
        "user_id": user_id,
        "history": search_history_manager.get_recent(user_id, limit=limit),
    }


@router.delete("/search-history")
async def clear_search_history(user_id: int = Query(0)):
    """清空用户搜索历史。"""
    removed = search_history_manager.clear(user_id)
    return {"success": True, "user_id": user_id, "removed": removed}


@router.get("/hot-searches")
async def hot_searches(limit: int = Query(10, ge=1, le=100)):
    """热门搜索统计。"""
    return {"success": True, "hot_searches": await cache_manager.get_hot_searches(limit=limit)}


@router.get("/autocomplete")
async def autocomplete(user_id: int = Query(0), q: str = Query(""), limit: int = Query(10, ge=1, le=20)):
    """搜索自动补全。"""
    return {
        "success": True,
        "suggestions": await autocomplete_service.get_suggestions(user_id=user_id, prefix=q, limit=limit),
    }
