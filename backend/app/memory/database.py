"""数据存储初始化模块 - 使用本地文件存储"""
from loguru import logger
from app.storage.local_storage import local_storage

async def init_database():
    """初始化本地文件存储（CSV文件）"""
    try:
        # 本地存储会在首次访问时自动初始化CSV文件
        # 这里只是确保存储目录存在
        logger.info("✅ 本地文件存储已就绪（使用CSV文件）")
        logger.info(f"📁 数据存储位置: {local_storage.data_dir}")
    except Exception as e:
        logger.error(f"❌ 本地存储初始化失败：{e}")
        raise
