"""平台集成 API 路由"""

from fastapi import APIRouter

from app.utils.cache_manager import cache_manager

router = APIRouter()


@router.post("/feishu/send")
async def send_feishu():
    return {"success": True, "message": "待实现"}


@router.get("/cache/stats")
async def cache_stats():
    return {"success": True, "stats": cache_manager.get_stats()}


@router.post("/cache/clear")
async def cache_clear():
    result = await cache_manager.clear()
    return {"success": True, **result}
