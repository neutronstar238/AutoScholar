"""测试本地存储系统"""

import asyncio
from app.storage.local_storage import local_storage


async def test_trending_papers():
    """测试热门论文操作"""
    print("\n=== 测试热门论文操作 ===")
    
    # 创建热门论文
    await local_storage.create_trending_paper({
        'paper_id': 'arxiv:2401.12345',
        'title': '深度学习最新进展',
        'abstract': '本文介绍了深度学习的最新研究成果',
        'url': 'https://arxiv.org/abs/2401.12345',
        'authors': '张三,李四',
        'category': 'cs.AI',
        'score': 1.0,
        'recommended_count': 1
    })
    print("✓ 创建热门论文成功")
    
    # 查询热门论文
    paper = await local_storage.get_trending_paper_by_paper_id('arxiv:2401.12345')
    print(f"✓ 查询热门论文: {paper['title']}")
    
    # 更新热门论文
    await local_storage.update_trending_paper('arxiv:2401.12345', {
        'score': '2.5',
        'recommended_count': '5'
    })
    print("✓ 更新热门论文成功")
    
    # 获取热门论文列表
    papers = await local_storage.get_trending_papers(limit=10)
    print(f"✓ 获取热门论文列表: {len(papers)} 篇")


async def test_user_interests():
    """测试用户兴趣操作"""
    print("\n=== 测试用户兴趣操作 ===")
    
    # 创建用户兴趣
    await local_storage.create_user_interest({
        'user_id': 1,
        'keyword': 'deep learning',
        'weight': 0.8
    })
    print("✓ 创建用户兴趣成功")
    
    # 查询用户兴趣
    interest = await local_storage.get_user_interest_by_keyword(1, 'deep learning')
    print(f"✓ 查询用户兴趣: {interest['keyword']}, 权重: {interest['weight']}")
    
    # 更新用户兴趣
    await local_storage.update_user_interest(1, 'deep learning', {
        'weight': '1.2'
    })
    print("✓ 更新用户兴趣成功")
    
    # 获取用户兴趣列表
    interests = await local_storage.get_user_interests(1, limit=10)
    print(f"✓ 获取用户兴趣列表: {len(interests)} 个")


async def test_search_history():
    """测试搜索历史操作"""
    print("\n=== 测试搜索历史操作 ===")
    
    # 创建搜索历史
    await local_storage.create_search_history({
        'user_id': 1,
        'query': 'machine learning',
        'result_count': 10,
        'source': 'primary'
    })
    print("✓ 创建搜索历史成功")
    
    # 再创建几条
    await local_storage.create_search_history({
        'user_id': 1,
        'query': 'machine learning',
        'result_count': 8,
        'source': 'primary'
    })
    await local_storage.create_search_history({
        'user_id': 1,
        'query': 'neural networks',
        'result_count': 15,
        'source': 'primary'
    })
    
    # 获取搜索历史
    history = await local_storage.get_search_history(1, days=90)
    print(f"✓ 获取搜索历史: {len(history)} 条")
    
    # 获取搜索历史（分组统计）
    grouped = await local_storage.get_search_history_grouped(1)
    print(f"✓ 获取搜索历史（分组）: {len(grouped)} 个查询")
    for item in grouped:
        print(f"  - {item['query']}: {item['count']} 次")


async def main():
    """运行所有测试"""
    print("开始测试本地存储系统...")
    
    try:
        await test_trending_papers()
        await test_user_interests()
        await test_search_history()
        
        print("\n" + "="*50)
        print("✓ 所有测试通过！")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
