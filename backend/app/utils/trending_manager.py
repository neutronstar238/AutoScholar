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
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import TrendingPaper, get_engine


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
        engine = get_engine()
        async with AsyncSession(engine) as session:
            try:
                # 查询是否已存在
                stmt = select(TrendingPaper).where(TrendingPaper.paper_id == paper_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    existing.recommended_count += 1
                    existing.last_recommended_at = datetime.utcnow()
                    # 评分 = 推荐次数 * 时间衰减因子
                    days_since_last = (datetime.utcnow() - existing.last_recommended_at).days
                    time_decay = 0.95 ** days_since_last
                    existing.score = existing.recommended_count * time_decay
                    logger.info(f"更新热门论文: {paper_id}, 推荐次数: {existing.recommended_count}")
                else:
                    # 创建新记录
                    new_paper = TrendingPaper(
                        paper_id=paper_id,
                        title=title,
                        abstract=abstract,
                        url=url,
                        authors=authors,
                        category=category,
                        score=1.0,
                        recommended_count=1,
                        last_recommended_at=datetime.utcnow()
                    )
                    session.add(new_paper)
                    logger.info(f"创建热门论文: {paper_id}")
                
                await session.commit()
                
                # 清理旧的热门论文（保持最多max_trending_papers条）
                await self._cleanup_old_papers(session)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"更新热门论文失败: {e}")
                raise
            finally:
                await engine.dispose()
    
    async def _cleanup_old_papers(self, session: AsyncSession) -> None:
        """清理评分最低的热门论文，保持数量在限制内。"""
        try:
            # 查询总数
            count_stmt = select(TrendingPaper)
            result = await session.execute(count_stmt)
            total_count = len(result.scalars().all())
            
            if total_count > self.max_trending_papers:
                # 删除评分最低的论文
                delete_count = total_count - self.max_trending_papers
                # 获取评分最低的论文ID
                stmt = (
                    select(TrendingPaper.id)
                    .order_by(TrendingPaper.score.asc())
                    .limit(delete_count)
                )
                result = await session.execute(stmt)
                ids_to_delete = [row[0] for row in result.fetchall()]
                
                # 删除这些论文
                for paper_id in ids_to_delete:
                    stmt = select(TrendingPaper).where(TrendingPaper.id == paper_id)
                    result = await session.execute(stmt)
                    paper = result.scalar_one_or_none()
                    if paper:
                        await session.delete(paper)
                
                await session.commit()
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
        engine = get_engine()
        async with AsyncSession(engine) as session:
            try:
                # 构建查询
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                stmt = (
                    select(TrendingPaper)
                    .where(TrendingPaper.last_recommended_at >= cutoff_date)
                    .order_by(TrendingPaper.score.desc())
                    .limit(limit)
                )
                
                if category:
                    stmt = stmt.where(TrendingPaper.category == category)
                
                result = await session.execute(stmt)
                papers = result.scalars().all()
                
                # 转换为字典列表
                return [
                    {
                        "id": paper.paper_id,
                        "title": paper.title,
                        "abstract": paper.abstract,
                        "url": paper.url,
                        "authors": paper.authors.split(",") if paper.authors else [],
                        "category": paper.category,
                        "score": paper.score,
                        "recommended_count": paper.recommended_count,
                        "last_recommended_at": paper.last_recommended_at.isoformat()
                    }
                    for paper in papers
                ]
            
            except Exception as e:
                logger.error(f"获取热门论文失败: {e}")
                return []
            finally:
                await engine.dispose()
    
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
