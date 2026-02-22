"""平台集成 API 路由"""
from fastapi import APIRouter
router = APIRouter()

@router.post("/feishu/send")
async def send_feishu():
    return {"success": True, "message": "待实现"}
