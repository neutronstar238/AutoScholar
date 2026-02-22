"""研究笔记 API 路由"""
from fastapi import APIRouter
router = APIRouter()

@router.post("/generate")
async def generate_note():
    return {"success": True, "message": "待实现"}
