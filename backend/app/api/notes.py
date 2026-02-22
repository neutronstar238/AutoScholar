"""研究笔记 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.researcher import ResearcherAgent

router = APIRouter()
researcher = ResearcherAgent()

class NoteGenerateRequest(BaseModel):
    """笔记生成请求"""
    paper_url: str

@router.post("/generate")
async def generate_note(request: NoteGenerateRequest):
    """生成研究笔记"""
    try:
        result = await researcher.execute(
            task="generate_note",
            query=request.paper_url
        )
        
        if result.get("success"):
            return {
                "success": True,
                "note": result.get("note"),
                "model": result.get("model"),
                "used_provider": result.get("used_provider")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "生成失败")
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成笔记失败：{str(e)}"
        )
