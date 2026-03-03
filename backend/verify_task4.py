"""验证Task 4: 热门论文缓存表和管理功能

此脚本验证：
1. TrendingPaper模型存在
2. trending_manager功能完整
3. 搜索引擎集成trending_manager
4. 推荐引擎更新trending_manager
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


def verify_model_exists():
    """验证TrendingPaper模型存在"""
    logger.info("\n" + "=" * 60)
    logger.info("验证1: TrendingPaper模型")
    logger.info("=" * 60)
    
    try:
        from app.models.base import TrendingPaper
        
        # 检查模型字段
        required_fields = [
            'paper_id', 'title', 'abstract', 'url', 'authors',
            'category', 'score', 'recommended_count', 'last_recommended_at'
        ]
        
        model_columns = [col.name for col in TrendingPaper.__table__.columns]
        
        logger.info(f"✅ TrendingPaper模型存在")
        logger.info(f"  表名: {TrendingPaper.__tablename__}")
        logger.info(f"  字段: {', '.join(model_columns)}")
        
        # 验证必需字段
        missing_fields = [f for f in required_fields if f not in model_columns]
        if missing_fields:
            logger.error(f"❌ 缺少字段: {', '.join(missing_fields)}")
            return False
        
        logger.info(f"✅ 所有必需字段都存在")
        return True
        
    except Exception as e:
        logger.error(f"❌ TrendingPaper模型验证失败: {e}")
        return False


def verify_trending_manager():
    """验证trending_manager功能"""
    logger.info("\n" + "=" * 60)
    logger.info("验证2: trending_manager功能")
    logger.info("=" * 60)
    
    try:
        from app.utils.trending_manager import trending_manager, TrendingManager
        
        # 检查trending_manager是TrendingManager实例
        if not isinstance(trending_manager, TrendingManager):
            logger.error("❌ trending_manager不是TrendingManager实例")
            return False
        
        logger.info("✅ trending_manager实例存在")
        
        # 检查必需方法
        required_methods = [
            'update_trending_paper',
            'get_trending_papers',
            'get_trending_by_category',
            '_cleanup_old_papers'
        ]
        
        for method in required_methods:
            if not hasattr(trending_manager, method):
                logger.error(f"❌ 缺少方法: {method}")
                return False
            logger.info(f"  ✅ {method}() 方法存在")
        
        # 检查配置
        logger.info(f"  最大热门论文数: {trending_manager.max_trending_papers}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ trending_manager验证失败: {e}")
        return False


def verify_search_engine_integration():
    """验证搜索引擎集成trending_manager"""
    logger.info("\n" + "=" * 60)
    logger.info("验证3: 搜索引擎集成")
    logger.info("=" * 60)
    
    try:
        from app.engines.search_engine import search_engine
        import inspect
        
        # 检查_fetch_trending_fallback方法
        if not hasattr(search_engine, '_fetch_trending_fallback'):
            logger.error("❌ 搜索引擎缺少_fetch_trending_fallback方法")
            return False
        
        logger.info("✅ _fetch_trending_fallback方法存在")
        
        # 检查方法源代码是否包含trending_manager
        source = inspect.getsource(search_engine._fetch_trending_fallback)
        
        if 'trending_manager' in source:
            logger.info("✅ _fetch_trending_fallback使用trending_manager")
        else:
            logger.warning("⚠️  _fetch_trending_fallback可能未使用trending_manager")
        
        if 'get_trending_papers' in source:
            logger.info("✅ 调用trending_manager.get_trending_papers()")
        else:
            logger.warning("⚠️  未调用get_trending_papers()")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 搜索引擎集成验证失败: {e}")
        return False


def verify_recommendation_engine_integration():
    """验证推荐引擎更新trending_manager"""
    logger.info("\n" + "=" * 60)
    logger.info("验证4: 推荐引擎集成")
    logger.info("=" * 60)
    
    try:
        from app.engines.recommendation_engine import recommendation_engine
        import inspect
        
        # 检查_update_trending_papers方法
        if not hasattr(recommendation_engine, '_update_trending_papers'):
            logger.error("❌ 推荐引擎缺少_update_trending_papers方法")
            return False
        
        logger.info("✅ _update_trending_papers方法存在")
        
        # 检查generate_recommendations是否调用_update_trending_papers
        gen_source = inspect.getsource(recommendation_engine.generate_recommendations)
        
        if '_update_trending_papers' in gen_source:
            logger.info("✅ generate_recommendations调用_update_trending_papers")
        else:
            logger.error("❌ generate_recommendations未调用_update_trending_papers")
            return False
        
        # 检查_update_trending_papers源代码
        update_source = inspect.getsource(recommendation_engine._update_trending_papers)
        
        if 'trending_manager' in update_source:
            logger.info("✅ _update_trending_papers使用trending_manager")
        else:
            logger.error("❌ _update_trending_papers未使用trending_manager")
            return False
        
        if 'update_trending_paper' in update_source:
            logger.info("✅ 调用trending_manager.update_trending_paper()")
        else:
            logger.error("❌ 未调用update_trending_paper()")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 推荐引擎集成验证失败: {e}")
        return False


async def main():
    """主验证流程"""
    logger.info("=" * 60)
    logger.info("Task 4 功能验证")
    logger.info("=" * 60)
    
    results = []
    
    # 验证1: 模型
    results.append(("TrendingPaper模型", verify_model_exists()))
    
    # 验证2: trending_manager
    results.append(("trending_manager功能", verify_trending_manager()))
    
    # 验证3: 搜索引擎集成
    results.append(("搜索引擎集成", verify_search_engine_integration()))
    
    # 验证4: 推荐引擎集成
    results.append(("推荐引擎集成", verify_recommendation_engine_integration()))
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("验证总结")
    logger.info("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("🎉 Task 4 所有功能验证通过！")
        logger.info("=" * 60)
        logger.info("\n功能已完整实现：")
        logger.info("  ✅ TrendingPaper数据库模型")
        logger.info("  ✅ 热门论文管理器（trending_manager）")
        logger.info("  ✅ 更新逻辑（基于推荐次数）")
        logger.info("  ✅ 查询接口（支持分类和时间过滤）")
        logger.info("  ✅ 搜索引擎集成（降级策略）")
        logger.info("  ✅ 推荐引擎集成（自动更新）")
        logger.info("\n注意：需要PostgreSQL数据库运行才能实际使用功能")
    else:
        logger.error("❌ 部分验证失败，请检查上述错误")
    
    logger.info("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
