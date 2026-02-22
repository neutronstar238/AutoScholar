"""
AutoScholar Backend - Main Application
自主学术研究与商业化 AI Agent 系统
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from loguru import logger

from app.api import literature, notes, research, auth, platform
from app.agents.coordinator import CoordinatorAgent
from app.memory.database import init_database
from app.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 AutoScholar 启动中...")
    
    # 初始化数据库
    await init_database()
    logger.info("✅ 数据库初始化完成")
    
    # 初始化 Agent 系统
    coordinator = CoordinatorAgent()
    app.state.coordinator = coordinator
    logger.info("✅ Agent 系统初始化完成")
    
    logger.info("✨ AutoScholar 启动完成！")
    
    yield
    
    # 关闭时清理
    logger.info("👋 AutoScholar 关闭中...")


# 创建 FastAPI 应用
app = FastAPI(
    title="AutoScholar API",
    description="自主学术研究与商业化 AI Agent 系统",
    version="0.1.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


# 注册路由
app.include_router(literature.router, prefix="/api/v1/literature", tags=["文献检索"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["研究笔记"])
app.include_router(research.router, prefix="/api/v1/research", tags=["研究方向"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(platform.router, prefix="/api/v1/platform", tags=["平台集成"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to AutoScholar API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG
    )
