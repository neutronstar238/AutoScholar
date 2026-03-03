"""本地文件存储管理器 - 替代SQL数据库

使用CSV文件存储数据，支持异步操作。
数据存储在 backend/data/ 目录下。
"""

import os
import csv
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import json


class LocalStorage:
    """本地CSV文件存储管理器"""
    
    def __init__(self, data_dir: str = "backend/data"):
        """初始化本地存储。
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义各个表的文件路径
        self.files = {
            "papers": self.data_dir / "papers.csv",
            "trending_papers": self.data_dir / "trending_papers.csv",
            "user_interests": self.data_dir / "user_interests.csv",
            "search_history": self.data_dir / "search_history.csv",
            "notes": self.data_dir / "notes.csv",
            "users": self.data_dir / "users.csv",
        }
        
        # 定义各个表的字段
        self.schemas = {
            "papers": ["id", "title", "abstract", "url", "authors", "published_date", "created_at", "updated_at"],
            "trending_papers": ["id", "paper_id", "title", "abstract", "url", "authors", "category", "score", "recommended_count", "last_recommended_at", "created_at", "updated_at"],
            "user_interests": ["id", "user_id", "keyword", "weight", "last_updated", "created_at", "updated_at"],
            "search_history": ["id", "user_id", "query", "result_count", "source", "created_at", "updated_at"],
            "notes": ["id", "paper_id", "content", "model_used", "created_at", "updated_at"],
            "users": ["id", "username", "email", "api_key", "created_at", "updated_at"],
        }
        
        # 初始化文件
        self._init_files()
    
    def _init_files(self):
        """初始化CSV文件（如果不存在则创建）"""
        for table_name, file_path in self.files.items():
            if not file_path.exists():
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.schemas[table_name])
                    writer.writeheader()
                logger.info(f"创建数据文件: {file_path}")
    
    async def _read_table(self, table_name: str) -> List[Dict[str, Any]]:
        """读取整个表的数据。
        
        Args:
            table_name: 表名
            
        Returns:
            数据行列表
        """
        file_path = self.files[table_name]
        
        def _read():
            if not file_path.exists():
                return []
            
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        
        return await asyncio.to_thread(_read)
    
    async def _write_table(self, table_name: str, data: List[Dict[str, Any]]):
        """写入整个表的数据。
        
        Args:
            table_name: 表名
            data: 数据行列表
        """
        file_path = self.files[table_name]
        
        def _write():
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=self.schemas[table_name])
                    writer.writeheader()
                    writer.writerows(data)
        
        await asyncio.to_thread(_write)
    
    async def _get_next_id(self, table_name: str) -> int:
        """获取下一个ID。
        
        Args:
            table_name: 表名
            
        Returns:
            下一个可用的ID
        """
        data = await self._read_table(table_name)
        if not data:
            return 1
        
        max_id = max(int(row.get('id', 0)) for row in data)
        return max_id + 1
    
    # ==================== TrendingPaper 操作 ====================
    
    async def get_trending_paper_by_paper_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """根据paper_id获取热门论文"""
        data = await self._read_table("trending_papers")
        for row in data:
            if row.get('paper_id') == paper_id:
                return row
        return None
    
    async def create_trending_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建热门论文记录"""
        data = await self._read_table("trending_papers")
        
        new_id = await self._get_next_id("trending_papers")
        now = datetime.utcnow().isoformat()
        
        new_paper = {
            "id": str(new_id),
            "paper_id": paper_data.get("paper_id", ""),
            "title": paper_data.get("title", ""),
            "abstract": paper_data.get("abstract", ""),
            "url": paper_data.get("url", ""),
            "authors": paper_data.get("authors", ""),
            "category": paper_data.get("category", "general"),
            "score": str(paper_data.get("score", 0.0)),
            "recommended_count": str(paper_data.get("recommended_count", 0)),
            "last_recommended_at": paper_data.get("last_recommended_at", now),
            "created_at": now,
            "updated_at": now,
        }
        
        data.append(new_paper)
        await self._write_table("trending_papers", data)
        return new_paper
    
    async def update_trending_paper(self, paper_id: str, updates: Dict[str, Any]):
        """更新热门论文记录"""
        data = await self._read_table("trending_papers")
        
        for row in data:
            if row.get('paper_id') == paper_id:
                row.update(updates)
                row['updated_at'] = datetime.utcnow().isoformat()
                break
        
        await self._write_table("trending_papers", data)
    
    async def get_trending_papers(
        self,
        category: Optional[str] = None,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取热门论文列表"""
        data = await self._read_table("trending_papers")
        
        # 过滤时间范围
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 3600)
        filtered = []
        
        for row in data:
            last_recommended = row.get('last_recommended_at', '')
            if last_recommended:
                try:
                    row_time = datetime.fromisoformat(last_recommended).timestamp()
                    if row_time >= cutoff_date:
                        # 过滤分类
                        if category is None or row.get('category') == category:
                            filtered.append(row)
                except:
                    pass
        
        # 按评分排序
        filtered.sort(key=lambda x: float(x.get('score', 0)), reverse=True)
        return filtered[:limit]
    
    async def delete_trending_papers_by_ids(self, ids: List[int]):
        """删除指定ID的热门论文"""
        data = await self._read_table("trending_papers")
        id_strs = [str(i) for i in ids]
        data = [row for row in data if row.get('id') not in id_strs]
        await self._write_table("trending_papers", data)
    
    async def count_trending_papers(self) -> int:
        """统计热门论文数量"""
        data = await self._read_table("trending_papers")
        return len(data)
    
    # ==================== UserInterest 操作 ====================
    
    async def get_user_interests(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取用户兴趣列表"""
        data = await self._read_table("user_interests")
        
        # 过滤用户ID
        user_data = [row for row in data if int(row.get('user_id', 0)) == user_id]
        
        # 按权重排序
        user_data.sort(key=lambda x: float(x.get('weight', 0)), reverse=True)
        
        if limit:
            return user_data[:limit]
        return user_data
    
    async def get_user_interest_by_keyword(
        self,
        user_id: int,
        keyword: str
    ) -> Optional[Dict[str, Any]]:
        """根据关键词获取用户兴趣"""
        data = await self._read_table("user_interests")
        
        for row in data:
            if int(row.get('user_id', 0)) == user_id and row.get('keyword') == keyword:
                return row
        return None
    
    async def create_user_interest(self, interest_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户兴趣记录"""
        data = await self._read_table("user_interests")
        
        new_id = await self._get_next_id("user_interests")
        now = datetime.utcnow().isoformat()
        
        new_interest = {
            "id": str(new_id),
            "user_id": str(interest_data.get("user_id", 0)),
            "keyword": interest_data.get("keyword", ""),
            "weight": str(interest_data.get("weight", 1.0)),
            "last_updated": interest_data.get("last_updated", now),
            "created_at": now,
            "updated_at": now,
        }
        
        data.append(new_interest)
        await self._write_table("user_interests", data)
        return new_interest
    
    async def update_user_interest(
        self,
        user_id: int,
        keyword: str,
        updates: Dict[str, Any]
    ):
        """更新用户兴趣记录"""
        data = await self._read_table("user_interests")
        
        for row in data:
            if int(row.get('user_id', 0)) == user_id and row.get('keyword') == keyword:
                row.update(updates)
                row['updated_at'] = datetime.utcnow().isoformat()
                break
        
        await self._write_table("user_interests", data)
    
    async def delete_user_interests_by_ids(self, ids: List[int]):
        """删除指定ID的用户兴趣"""
        data = await self._read_table("user_interests")
        id_strs = [str(i) for i in ids]
        data = [row for row in data if row.get('id') not in id_strs]
        await self._write_table("user_interests", data)
    
    # ==================== SearchHistory 操作 ====================
    
    async def create_search_history(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建搜索历史记录"""
        data = await self._read_table("search_history")
        
        new_id = await self._get_next_id("search_history")
        now = datetime.utcnow().isoformat()
        
        new_history = {
            "id": str(new_id),
            "user_id": str(history_data.get("user_id", "")),
            "query": history_data.get("query", ""),
            "result_count": str(history_data.get("result_count", 0)),
            "source": history_data.get("source", ""),
            "created_at": now,
            "updated_at": now,
        }
        
        data.append(new_history)
        await self._write_table("search_history", data)
        return new_history
    
    async def get_search_history(
        self,
        user_id: int,
        days: int = 90,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取搜索历史"""
        data = await self._read_table("search_history")
        
        # 过滤用户ID和时间范围
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 3600)
        filtered = []
        
        for row in data:
            if int(row.get('user_id', 0)) == user_id:
                created_at = row.get('created_at', '')
                if created_at:
                    try:
                        row_time = datetime.fromisoformat(created_at).timestamp()
                        if row_time >= cutoff_date:
                            filtered.append(row)
                    except:
                        pass
        
        # 按时间排序（最新的在前）
        filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        if limit:
            return filtered[:limit]
        return filtered
    
    async def get_search_history_grouped(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取搜索历史（按查询分组统计）"""
        data = await self._read_table("search_history")
        
        # 过滤用户ID
        user_data = [row for row in data if int(row.get('user_id', 0)) == user_id]
        
        # 统计每个查询的次数
        query_counts = {}
        for row in user_data:
            query = row.get('query', '')
            if query:
                query_counts[query] = query_counts.get(query, 0) + 1
        
        # 转换为列表
        result = [{"query": q, "count": c} for q, c in query_counts.items()]
        
        # 按次数排序
        result.sort(key=lambda x: x['count'], reverse=True)
        
        if limit:
            return result[:limit]
        return result


# 全局实例
local_storage = LocalStorage()
