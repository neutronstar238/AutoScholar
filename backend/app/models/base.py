"""数据模型定义（仅用于类型提示和文档）

注意：本项目已迁移到本地文件存储（CSV），不再使用SQL数据库。
这些模型定义保留用于：
1. 代码文档和类型提示
2. 数据结构参考
3. 未来可能的数据库迁移

实际数据操作请使用：
from app.storage.local_storage import local_storage
"""

from datetime import datetime
from typing import Optional


class BaseModel:
    """基础模型（仅用于文档）"""
    id: int
    created_at: datetime
    updated_at: datetime


class Paper(BaseModel):
    """论文表（仅用于文档）"""
    title: str
    abstract: Optional[str]
    url: str
    authors: Optional[str]
    published_date: Optional[str]


class TrendingPaper(BaseModel):
    """热门论文缓存表（仅用于文档）
    
    实际使用：
    await local_storage.get_trending_papers(limit=10)
    await local_storage.create_trending_paper({...})
    """
    paper_id: str
    title: str
    abstract: Optional[str]
    url: Optional[str]
    authors: Optional[str]
    category: str
    score: float
    recommended_count: int
    last_recommended_at: datetime


class UserInterest(BaseModel):
    """用户兴趣画像（仅用于文档）
    
    实际使用：
    await local_storage.get_user_interests(user_id, limit=10)
    await local_storage.create_user_interest({...})
    """
    user_id: int
    keyword: str
    weight: float
    last_updated: datetime


class SearchHistory(BaseModel):
    """搜索历史（仅用于文档）
    
    实际使用：
    await local_storage.get_search_history(user_id, days=90)
    await local_storage.create_search_history({...})
    """
    user_id: Optional[int]
    query: str
    result_count: int
    source: str


class Note(BaseModel):
    """研究笔记表（仅用于文档）"""
    paper_id: int
    content: str
    model_used: Optional[str]


class User(BaseModel):
    """用户表（仅用于文档）"""
    username: str
    email: Optional[str]
    api_key: Optional[str]
