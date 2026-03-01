"""平台集成 API 路由"""

from fastapi import APIRouter

from app.utils.cache_manager import cache_manager
from app.utils.quality_monitor import quality_monitor
from app.utils.project_checkpoint import project_checkpoint
from app.utils.ops_center import ops_center

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


@router.post("/ops/audit")
async def ops_audit():
    return {"success": True, **ops_center.run_audit()}


@router.get("/ops/alerts")
async def ops_alerts(active_only: bool = False):
    return {"success": True, "alerts": ops_center.get_alerts(active_only=active_only)}


@router.post("/ops/alerts/{alert_id}/ack")
async def ops_ack(alert_id: int):
    ok = ops_center.acknowledge(alert_id)
    return {"success": ok, "alert_id": alert_id}


@router.get("/ops/status")
async def ops_status():
    audit = ops_center.run_audit()
    return {"success": True, "status": audit.get("status"), "quality": audit.get("quality"), "checkpoint": audit.get("checkpoint")}
