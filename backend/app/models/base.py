"""数据库基础模型"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Paper(BaseModel):
    """论文表"""
    __tablename__ = 'papers'
    
    title = Column(String(500), nullable=False)
    abstract = Column(Text)
    url = Column(String(500), unique=True)
    authors = Column(String(1000))
    published_date = Column(String(20))
    
class Note(BaseModel):
    """研究笔记表"""
    __tablename__ = 'notes'
    
    paper_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    model_used = Column(String(100))

class User(BaseModel):
    """用户表"""
    __tablename__ = 'users'
    
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200))
    api_key = Column(String(200))

def get_engine():
    database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://autoscholar:autoscholar@localhost:5432/autoscholar')
    return create_async_engine(database_url, echo=False)

async def init_db():
    """初始化数据库表"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
