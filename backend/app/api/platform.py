"""平台集成 API 路由"""

from fastapi import APIRouter

from app.utils.cache_manager import cache_manager
from app.utils.quality_monitor import quality_monitor
from app.utils.project_checkpoint import project_checkpoint

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


@router.get("/quality/metrics")
async def quality_metrics():
    return {"success": True, "metrics": quality_monitor.metrics()}


@router.get("/quality/check")
async def quality_check():
    return {"success": True, **quality_monitor.quality_check()}


@router.get("/checkpoint/p4")
async def checkpoint_p4():
    return {"success": True, **project_checkpoint.check_p4()}
