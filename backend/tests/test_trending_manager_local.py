"""热门论文管理器测试（使用本地存储）。

测试TrendingPaper表和trending_manager的功能。

Requirements: 1.3, 1.4
"""

import pytest
from datetime import datetime, timedelta

from app.utils.trending_manager import trending_manager
from app.storage.local_storage import local_storage


@pytest.fixture
async def cleanup_test_data():
    """测试后清理数据"""
    yield
    # 清理测试论文数据（paper_id包含"test_paper"）
    all_papers = await local_storage._read_table("trending_papers")
    cleaned = [row for row in all_papers if "test_paper" not in row.get('paper_id', '')]
    await local_storage._write_table("trending_papers", cleaned)


class TestTrendingManager:
    """热门论文管理器测试"""

    @pytest.mark.asyncio
    async def test_update_trending_paper_creates_new_record(self, cleanup_test_data):
        """测试创建新的热门论文记录"""
        paper_id = f"test_paper_{datetime.utcnow().timestamp()}"
        
        await trending_manager.update_trending_paper(
            paper_id=paper_id,
            title="Test Paper Title",
            abstract="Test abstract content",
            url=f"https://arxiv.org/abs/{paper_id}",
            authors="Author One, Author Two",
            category="cs.AI"
        )
        
        # 验证论文被创建
        papers = await trending_manager.get_trending_papers(limit=100)
        paper_ids = [p["id"] for p in papers]
        assert paper_id in paper_ids

    @pytest.mark.asyncio
    async def test_update_trending_paper_increments_count(self, cleanup_test_data):
        """测试更新现有论文增加推荐计数"""
        paper_id = f"test_paper_increment_{datetime.utcnow().timestamp()}"
        
        # 第一次推荐
        await trending_manager.update_trending_paper(
            paper_id=paper_id,
            title="Test Paper for Increment",
            abstract="Test abstract",
            url=f"https://arxiv.org/abs/{paper_id}",
            authors="Test Author",
            category="cs.LG"
        )
        
        # 获取初始推荐计数
        papers = await trending_manager.get_trending_papers(limit=100)
        paper = next((p for p in papers if p["id"] == paper_id), None)
        assert paper is not None
        initial_count = paper["recommended_count"]
        
        # 第二次推荐
        await trending_manager.update_trending_paper(
            paper_id=paper_id,
            title="Test Paper for Increment",
            abstract="Test abstract",
            url=f"https://arxiv.org/abs/{paper_id}",
            authors="Test Author",
            category="cs.LG"
        )
        
        # 验证推荐计数增加
        papers = await trending_manager.get_trending_papers(limit=100)
        paper = next((p for p in papers if p["id"] == paper_id), None)
        assert paper is not None
        assert paper["recommended_count"] == initial_count + 1

    @pytest.mark.asyncio
    async def test_get_trending_papers_returns_recent(self, cleanup_test_data):
        """测试获取热门论文只返回最近推荐的"""
        # 创建一个最近推荐的论文
        recent_paper_id = f"test_paper_recent_{datetime.utcnow().timestamp()}"
        await trending_manager.update_trending_paper(
            paper_id=recent_paper_id,
            title="Recent Paper",
            abstract="Recent abstract",
            url=f"https://arxiv.org/abs/{recent_paper_id}",
            authors="Recent Author",
            category="cs.CV"
        )
        
        # 获取最近7天的热门论文
        papers = await trending_manager.get_trending_papers(limit=10, days=7)
        
        # 验证返回了论文
        assert len(papers) > 0
        
        # 验证所有论文都在7天内推荐
        cutoff = datetime.utcnow() - timedelta(days=7)
        for paper in papers:
            last_recommended = datetime.fromisoformat(paper["last_recommended_at"])
            assert last_recommended >= cutoff

    @pytest.mark.asyncio
    async def test_get_trending_papers_by_category(self, cleanup_test_data):
        """测试按分类获取热门论文"""
        # 创建不同分类的论文
        paper_id_ai = f"test_paper_ai_{datetime.utcnow().timestamp()}"
        paper_id_cv = f"test_paper_cv_{datetime.utcnow().timestamp()}"
        
        await trending_manager.update_trending_paper(
            paper_id=paper_id_ai,
            title="AI Paper",
            abstract="AI abstract",
            url=f"https://arxiv.org/abs/{paper_id_ai}",
            authors="AI Author",
            category="cs.AI"
        )
        
        await trending_manager.update_trending_paper(
            paper_id=paper_id_cv,
            title="CV Paper",
            abstract="CV abstract",
            url=f"https://arxiv.org/abs/{paper_id_cv}",
            authors="CV Author",
            category="cs.CV"
        )
        
        # 获取AI分类的论文
        ai_papers = await trending_manager.get_trending_papers(category="cs.AI", limit=10)
        ai_paper_ids = [p["id"] for p in ai_papers]
        
        # 验证AI论文在结果中
        assert paper_id_ai in ai_paper_ids
        
        # 验证所有返回的论文都是AI分类
        for paper in ai_papers:
            assert paper["category"] == "cs.AI"

    @pytest.mark.asyncio
    async def test_get_trending_by_category_multiple(self, cleanup_test_data):
        """测试按多个分类获取热门论文"""
        categories = ["cs.AI", "cs.LG"]
        result = await trending_manager.get_trending_by_category(
            categories=categories,
            limit_per_category=5
        )
        
        # 验证返回了所有分类
        assert "cs.AI" in result
        assert "cs.LG" in result
        
        # 验证每个分类的论文数量不超过限制
        for category, papers in result.items():
            assert len(papers) <= 5

    @pytest.mark.asyncio
    async def test_trending_papers_sorted_by_score(self, cleanup_test_data):
        """测试热门论文按评分排序"""
        # 创建多个论文并多次推荐其中一个
        paper_id_high = f"test_paper_high_score_{datetime.utcnow().timestamp()}"
        paper_id_low = f"test_paper_low_score_{datetime.utcnow().timestamp()}"
        
        # 低分论文（推荐1次）
        await trending_manager.update_trending_paper(
            paper_id=paper_id_low,
            title="Low Score Paper",
            abstract="Low score abstract",
            url=f"https://arxiv.org/abs/{paper_id_low}",
            authors="Low Author",
            category="cs.AI"
        )
        
        # 高分论文（推荐3次）
        for _ in range(3):
            await trending_manager.update_trending_paper(
                paper_id=paper_id_high,
                title="High Score Paper",
                abstract="High score abstract",
                url=f"https://arxiv.org/abs/{paper_id_high}",
                authors="High Author",
                category="cs.AI"
            )
        
        # 获取热门论文
        papers = await trending_manager.get_trending_papers(limit=10)
        
        # 找到这两篇论文
        high_paper = next((p for p in papers if p["id"] == paper_id_high), None)
        low_paper = next((p for p in papers if p["id"] == paper_id_low), None)
        
        assert high_paper is not None
        assert low_paper is not None
        
        # 验证高分论文的评分更高
        assert high_paper["score"] > low_paper["score"]
        
        # 验证高分论文在列表中排在前面
        high_index = papers.index(high_paper)
        low_index = papers.index(low_paper)
        assert high_index < low_index


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
