"""测试用户画像管理器。

测试 Requirements: 5.1, 5.2, 5.4, 5.5
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.user_profile_manager import (
    UserProfileManager,
    InterestKeyword,
    InterestSuggestion
)
from app.models.base import UserInterest, SearchHistory, get_engine


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = get_engine()
    async with AsyncSession(engine) as session:
        yield session
        # 清理测试数据
        await session.rollback()
    await engine.dispose()


@pytest.fixture
def profile_manager():
    """创建用户画像管理器实例"""
    return UserProfileManager(max_keywords=20)


@pytest.mark.asyncio
async def test_extract_interests_from_database(profile_manager, db_session):
    """测试从数据库提取用户兴趣"""
    user_id = 999
    
    # 创建测试数据
    engine = get_engine()
    async with AsyncSession(engine) as session:
        # 添加用户兴趣
        interests = [
            UserInterest(user_id=user_id, keyword="machine learning", weight=5.0),
            UserInterest(user_id=user_id, keyword="deep learning", weight=4.5),
            UserInterest(user_id=user_id, keyword="nlp", weight=3.0),
        ]
        for interest in interests:
            session.add(interest)
        await session.commit()
    
    # 提取兴趣
    result = await profile_manager.extract_interests(user_id, limit=10)
    
    # 验证结果
    assert len(result) == 3
    assert result[0].keyword == "machine learning"
    assert result[0].weight == 5.0
    assert result[1].keyword == "deep learning"
    assert result[1].weight == 4.5
    
    # 清理测试数据
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(UserInterest.user_id == user_id)
        result = await session.execute(stmt)
        interests = result.scalars().all()
        for interest in interests:
            await session.delete(interest)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_extract_interests_from_search_history(profile_manager):
    """测试从搜索历史提取兴趣（当没有存储的兴趣时）"""
    user_id = 998
    
    # 创建测试搜索历史
    engine = get_engine()
    async with AsyncSession(engine) as session:
        searches = [
            SearchHistory(user_id=user_id, query="deep learning tutorial", result_count=10),
            SearchHistory(user_id=user_id, query="deep learning applications", result_count=5),
            SearchHistory(user_id=user_id, query="neural networks", result_count=8),
        ]
        for search in searches:
            session.add(search)
        await session.commit()
    
    # 提取兴趣
    result = await profile_manager.extract_interests(user_id, limit=5)
    
    # 验证结果
    assert len(result) > 0
    # "deep" 和 "learning" 应该出现频率最高
    keywords = [r.keyword for r in result]
    assert "deep" in keywords or "learning" in keywords
    
    # 清理测试数据
    async with AsyncSession(engine) as session:
        stmt = select(SearchHistory).where(SearchHistory.user_id == user_id)
        result = await session.execute(stmt)
        searches = result.scalars().all()
        for search in searches:
            await session.delete(search)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_interest_from_search(profile_manager):
    """测试从搜索行为更新用户兴趣"""
    user_id = 997
    query = "machine learning algorithms"
    
    # 更新兴趣
    await profile_manager.update_interest_from_search(user_id, query)
    
    # 验证兴趣已创建
    engine = get_engine()
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(UserInterest.user_id == user_id)
        result = await session.execute(stmt)
        interests = result.scalars().all()
        
        assert len(interests) > 0
        keywords = [i.keyword for i in interests]
        assert "machine" in keywords
        assert "learning" in keywords
        
        # 清理测试数据
        for interest in interests:
            await session.delete(interest)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_interest_from_reading(profile_manager):
    """测试从阅读行为更新用户兴趣"""
    user_id = 996
    paper_id = "arxiv:2024.12345"
    categories = ["cs.AI", "cs.LG", "cs.CL"]
    
    # 更新兴趣
    await profile_manager.update_interest_from_reading(user_id, paper_id, categories)
    
    # 验证兴趣已创建
    engine = get_engine()
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(UserInterest.user_id == user_id)
        result = await session.execute(stmt)
        interests = result.scalars().all()
        
        assert len(interests) == 3
        keywords = [i.keyword for i in interests]
        assert "cs.ai" in keywords
        assert "cs.lg" in keywords
        assert "cs.cl" in keywords
        
        # 验证权重
        for interest in interests:
            assert interest.weight == 0.3  # 初始阅读权重
        
        # 清理测试数据
        for interest in interests:
            await session.delete(interest)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_interest_from_feedback(profile_manager):
    """测试从反馈更新兴趣权重"""
    user_id = 995
    
    # 先创建一个兴趣
    engine = get_engine()
    async with AsyncSession(engine) as session:
        interest = UserInterest(user_id=user_id, keyword="neural networks", weight=1.0)
        session.add(interest)
        await session.commit()
    
    # 正向反馈
    await profile_manager.update_interest_from_feedback(
        user_id, ["neural networks"], "helpful"
    )
    
    # 验证权重增加
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(
            UserInterest.user_id == user_id,
            UserInterest.keyword == "neural networks"
        )
        result = await session.execute(stmt)
        interest = result.scalar_one()
        
        assert interest.weight == 1.1  # 1.0 + 0.1
        
        # 负向反馈
        await profile_manager.update_interest_from_feedback(
            user_id, ["neural networks"], "not_helpful"
        )
    
    # 验证权重减少
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(
            UserInterest.user_id == user_id,
            UserInterest.keyword == "neural networks"
        )
        result = await session.execute(stmt)
        interest = result.scalar_one()
        
        assert interest.weight == pytest.approx(0.95, 0.01)  # 1.1 - 0.15
        
        # 清理测试数据
        await session.delete(interest)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_max_keywords_limit(profile_manager):
    """测试兴趣关键词数量上限（最多20个）"""
    user_id = 994
    
    # 创建25个兴趣关键词
    engine = get_engine()
    async with AsyncSession(engine) as session:
        for i in range(25):
            interest = UserInterest(
                user_id=user_id,
                keyword=f"keyword_{i}",
                weight=float(i)
            )
            session.add(interest)
        await session.commit()
    
    # 触发trim操作
    await profile_manager.update_interest_from_search(user_id, "new keyword")
    
    # 验证只保留了20个（加上新的1个）
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(UserInterest.user_id == user_id)
        result = await session.execute(stmt)
        interests = result.scalars().all()
        
        assert len(interests) <= 20
        
        # 清理测试数据
        for interest in interests:
            await session.delete(interest)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_suggest_interests_for_input(profile_manager):
    """测试为输入框提供兴趣建议"""
    user_id = 993
    
    # 创建测试数据
    engine = get_engine()
    async with AsyncSession(engine) as session:
        interests = [
            UserInterest(user_id=user_id, keyword="machine learning", weight=5.0),
            UserInterest(user_id=user_id, keyword="deep learning", weight=4.0),
            UserInterest(user_id=user_id, keyword="reinforcement learning", weight=3.0),
        ]
        for interest in interests:
            session.add(interest)
        await session.commit()
    
    # 获取建议（无输入）
    suggestions = await profile_manager.suggest_interests_for_input(user_id, "", limit=5)
    
    assert len(suggestions) > 0
    assert suggestions[0].keyword == "machine learning"
    assert suggestions[0].source == "user_profile"
    
    # 获取建议（有输入过滤）
    suggestions = await profile_manager.suggest_interests_for_input(
        user_id, "deep", limit=5
    )
    
    assert len(suggestions) > 0
    assert "deep" in suggestions[0].keyword.lower()
    
    # 清理测试数据
    async with AsyncSession(engine) as session:
        stmt = select(UserInterest).where(UserInterest.user_id == user_id)
        result = await session.execute(stmt)
        interests = result.scalars().all()
        for interest in interests:
            await session.delete(interest)
        await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_recency_factor_calculation(profile_manager):
    """测试时间衰减因子计算"""
    # 测试最近的活动（应该接近1.0）
    recent_date = datetime.utcnow()
    factor = profile_manager._calculate_recency_factor(recent_date)
    assert factor == pytest.approx(1.0, 0.01)
    
    # 测试30天前的活动（应该是0.9）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    factor = profile_manager._calculate_recency_factor(thirty_days_ago)
    assert factor == pytest.approx(0.9, 0.01)
    
    # 测试60天前的活动（应该是0.81）
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    factor = profile_manager._calculate_recency_factor(sixty_days_ago)
    assert factor == pytest.approx(0.81, 0.01)


def test_tokenize():
    """测试分词功能"""
    manager = UserProfileManager()
    
    # 测试英文
    tokens = manager._tokenize("machine learning algorithms")
    assert "machine" in tokens
    assert "learning" in tokens
    assert "algorithms" in tokens
    
    # 测试中文
    tokens = manager._tokenize("深度学习和神经网络")
    assert "深度学习" in tokens
    assert "神经网络" in tokens
    
    # 测试混合
    tokens = manager._tokenize("deep learning 深度学习")
    assert "deep" in tokens
    assert "learning" in tokens
    assert "深度学习" in tokens
    
    # 测试过滤短词
    tokens = manager._tokenize("a b cd efg")
    assert "a" not in tokens
    assert "b" not in tokens
    assert "cd" in tokens
    assert "efg" in tokens
