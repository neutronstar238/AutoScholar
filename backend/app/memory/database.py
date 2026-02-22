"""数据库初始化模块"""
from loguru import logger
from app.models.base import init_db

async def init_database():
    """初始化数据库"""
    try:
        await init_db()
        logger.info("✅ 数据库表创建成功")
    except Exception as e:
        logger.warning(f"⚠️  数据库初始化警告：{e}")
        logger.info("如果数据库未运行，某些功能可能不可用")
