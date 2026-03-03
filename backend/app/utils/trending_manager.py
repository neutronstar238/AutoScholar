"""热门论文管理器。

负责：
- 更新热门论文缓存（基于推荐次数）
- 查询热门论文
- 维护热门论文评分

Requirements: 1.3, 1.4
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from app.storage.local_storage import local_storage


class TrendingManager:
    """热门论文管理器"""
    
    def __init__(self, max_trending_papers: int = 100):
        """初始化热门论文管理器。
        
        Args:
            max_trending_papers: 最大热门论文数量
        """
        self.max_trending_papers = max_trending_papers
    
    async def update_trending_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str = "",
        url: str = "",
        authors: str = "",
        category: str = "general"
    ) -> None:
        """更新或创建热门论文记录。
        
        当论文被推荐时调用，增加推荐计数并更新评分。
        
        Args:
            paper_id: 论文ID
            title: 论文标题
            abstract: 论文摘要
            url: 论文URL
            authors: 作者列表（逗号分隔）
            category: 论文分类
        """
        try:
            # 查询是否已存在
            existing = await local_storage.get_trending_paper_by_paper_id(paper_id)
            
            if existing:
                # 更新现有记录
                recommended_count = int(existing['recommended_count']) + 1
                last_recommended_at = datetime.utcnow().isoformat()
                
                # 评分 = 推荐次数 * 时间衰减因子
                last_time = datetime.fromisoformat(existing['last_recommended_at'])
                days_since_last = (datetime.utcnow() - last_time).days
                time_decay = 0.95 ** days_since_last
                score = recommended_count * time_decay
                
                await local_storage.update_trending_paper(paper_id, {
                    'recommended_count': str(recommended_count),
                    'last_recommended_at': last_recommended_at,
                    'score': str(score)
                })
                logger.info(f"更新热门论文: {paper_id}, 推荐次数: {recommended_count}")
            else:
                # 创建新记录
                await local_storage.create_trending_paper({
                    'paper_id': paper_id,
                    'title': title,
                    'abstract': abstract,
                    'url': url,
                    'authors': authors,
                    'category': category,
                    'score': 1.0,
                    'recommended_count': 1,
                    'last_recommended_at': datetime.utcnow().isoformat()
                })
                logger.info(f"创建热门论文: {paper_id}")
            
            # 清理旧的热门论文（保持最多max_trending_papers条）
            await self._cleanup_old_papers()
            
        except Exception as e:
            logger.error(f"更新热门论文失败: {e}")
            raise
    
    async def _cleanup_old_papers(self) -> None:
        """清理评分最低的热门论文，保持数量在限制内。"""
        try:
            # 查询总数
            total_count = await local_storage.count_trending_papers()
            
            if total_count > self.max_trending_papers:
                # 删除评分最低的论文
                delete_count = total_count - self.max_trending_papers
                
                # 获取所有论文并按评分排序
                all_papers = await local_storage.get_trending_papers(days=365, limit=total_count)
                
                # 按评分升序排序，取最低的
                all_papers.sort(key=lambda x: float(x.get('score', 0)))
                ids_to_delete = [int(paper['id']) for paper in all_papers[:delete_count]]
                
                # 删除这些论文
                await local_storage.delete_trending_papers_by_ids(ids_to_delete)
                
                logger.info(f"清理了 {delete_count} 条低评分热门论文")
        
        except Exception as e:
            logger.error(f"清理热门论文失败: {e}")
    
    async def get_trending_papers(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取热门论文列表。
        
        Args:
            category: 论文分类过滤（可选）
            limit: 返回数量限制
            days: 时间范围（天数），只返回最近N天推荐的论文
            
        Returns:
            热门论文列表，按评分降序排列
        """
        try:
            # 从本地存储获取热门论文
            papers = await local_storage.get_trending_papers(
                category=category,
                days=days,
                limit=limit
            )
            
            # 转换为字典列表
            return [
                {
                    "id": paper['paper_id'],
                    "title": paper['title'],
                    "abstract": paper['abstract'],
                    "url": paper['url'],
                    "authors": paper['authors'].split(",") if paper['authors'] else [],
                    "category": paper['category'],
                    "score": float(paper['score']),
                    "recommended_count": int(paper['recommended_count']),
                    "last_recommended_at": paper['last_recommended_at']
                }
                for paper in papers
            ]
        
        except Exception as e:
            logger.error(f"获取热门论文失败: {e}")
            return []
    
    async def get_trending_by_category(
        self,
        categories: List[str],
        limit_per_category: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """按分类获取热门论文。
        
        Args:
            categories: 分类列表
            limit_per_category: 每个分类的论文数量限制
            
        Returns:
            分类到论文列表的映射
        """
        result = {}
        for category in categories:
            papers = await self.get_trending_papers(
                category=category,
                limit=limit_per_category
            )
            result[category] = papers
        
        return result


# 全局实例
trending_manager = TrendingManager()
