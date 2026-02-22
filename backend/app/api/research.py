"""研究方向 API 路由"""
from fastapi import APIRouter
router = APIRouter()

@router.post("/recommend")
async def recommend():
    return {"success": True, "message": "待实现"}
