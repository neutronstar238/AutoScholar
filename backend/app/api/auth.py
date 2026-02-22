"""认证 API 路由"""
from fastapi import APIRouter
router = APIRouter()

@router.post("/api-key")
async def get_api_key():
    return {"success": True, "message": "待实现"}
