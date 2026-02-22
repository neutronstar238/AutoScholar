"""pgvector 向量搜索模型"""
from sqlalchemy import Column, Integer, String
from pgvector.sqlalchemy import Vector
from .base import Base, BaseModel

class PaperVector(BaseModel):
    """论文向量表"""
    __tablename__ = 'paper_vectors'
    
    paper_id = Column(Integer, nullable=False)
    title = Column(String(500))
    abstract = Column(String(2000))
    embedding = Column(Vector(768))  # 768 维向量
    
    def __repr__(self):
        return f"<PaperVector {self.title}>"

print("✅ pgvector 模型已创建")
