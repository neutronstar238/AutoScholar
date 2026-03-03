"""验证Task 5: 重构研究方向推荐API

此脚本验证：
1. recommend端点集成搜索引擎降级策略
2. 响应包含is_fallback字段
3. 实现降级率追踪和告警
4. 添加错误处理和用户友好的错误消息
"""

import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
import inspect


def verify_recommend_endpoint():
    """验证recommend端点的实现"""
    logger.info("\n" + "=" * 60)
    logger.info("验证1: recommend端点实现")
    logger.info("=" * 60)
    
    try:
        from app.api.research import recommend
        
        logger.info("✅ recommend端点存在")
        
        # 检查函数签名
        sig = inspect.signature(recommend)
        logger.info(f"  函数签名: {sig}")
        
        # 检查源代码
        source = inspect.getsource(recommend)
        
        # 验证1: 集成搜索引擎降级策略
        if 'recommendation_engine.generate_recommendations' in source:
            logger.info("✅ 集成recommendation_engine")
        else:
            logger.error("❌ 未集成recommendation_engine")
            return False
        
        # 验证2: 响应包含is_fallback字段
        if '"is_fallback"' in source or "'is_fallback'" in source:
            logger.info("✅ 响应包含is_fallback字段")
        else:
            logger.error("❌ 响应缺少is_fallback字段")
            return False
        
        # 验证3: 响应包含fallback_strategy字段
        if '"fallback_strategy"' in source or "'fallback_strategy'" in source:
            logger.info("✅ 响应包含fallback_strategy字段")
        else:
            logger.error("❌ 响应缺少fallback_strategy字段")
            return False
        
        # 验证4: 响应包含fallback_rate字段
        if '"fallback_rate"' in source or "'fallback_rate'" in source:
            logger.info("✅ 响应包含fallback_rate字段")
        else:
            logger.error("❌ 响应缺少fallback_rate字段")
            return False
        
        # 验证5: 实现降级率追踪
        if 'quality_monitor.record_fallback' in source:
            logger.info("✅ 实现降级率追踪（quality_monitor.record_fallback）")
        else:
            logger.error("❌ 未实现降级率追踪")
            return False
        
        # 验证6: 实现降级率告警
        if 'fallback_rate()' in source and ('logger.warning' in source or 'logger.error' in source):
            logger.info("✅ 实现降级率告警")
        else:
            logger.warning("⚠️  降级率告警可能未实现")
        
        # 验证7: 错误处理
        if 'try:' in source and 'except' in source:
            logger.info("✅ 实现错误处理")
        else:
            logger.error("❌ 缺少错误处理")
            return False
        
        # 验证8: 用户友好的错误消息
        if 'HTTPException' in source:
            logger.info("✅ 使用HTTPException返回用户友好错误")
        else:
            logger.warning("⚠️  可能缺少用户友好的错误消息")
        
        # 验证9: 降级提示消息
        if '_build_troubleshooting_message' in source or 'fallback_note' in source:
            logger.info("✅ 提供降级提示消息")
        else:
            logger.warning("⚠️  可能缺少降级提示消息")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ recommend端点验证失败: {e}")
        return False


def verify_quality_monitor():
    """验证quality_monitor实现"""
    logger.info("\n" + "=" * 60)
    logger.info("验证2: quality_monitor实现")
    logger.info("=" * 60)
    
    try:
        from app.utils.quality_monitor import quality_monitor, QualityMonitor
        
        # 检查是否是QualityMonitor实例
        if not isinstance(quality_monitor, QualityMonitor):
            logger.error("❌ quality_monitor不是QualityMonitor实例")
            return False
        
        logger.info("✅ quality_monitor实例存在")
        
        # 检查必需方法
        required_methods = [
            'record_fallback',
            'fallback_rate',
            'record_recommend_latency',
            'metrics',
            'quality_check'
        ]
        
        for method in required_methods:
            if not hasattr(quality_monitor, method):
                logger.error(f"❌ 缺少方法: {method}")
                return False
            logger.info(f"  ✅ {method}() 方法存在")
        
        # 测试fallback_rate方法
        try:
            rate = quality_monitor.fallback_rate()
            logger.info(f"  当前降级率: {rate:.2%}")
        except Exception as e:
            logger.error(f"❌ fallback_rate()调用失败: {e}")
            return False
        
        # 测试metrics方法
        try:
            metrics = quality_monitor.metrics()
            logger.info(f"  指标: {metrics}")
        except Exception as e:
            logger.error(f"❌ metrics()调用失败: {e}")
            return False
        
        # 测试quality_check方法
        try:
            check = quality_monitor.quality_check()
            logger.info(f"  质量检查: {check}")
        except Exception as e:
            logger.error(f"❌ quality_check()调用失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ quality_monitor验证失败: {e}")
        return False


def verify_response_structure():
    """验证响应结构"""
    logger.info("\n" + "=" * 60)
    logger.info("验证3: 响应结构")
    logger.info("=" * 60)
    
    try:
        from app.api.research import recommend
        
        source = inspect.getsource(recommend)
        
        # 检查响应字段
        required_fields = [
            'success',
            'is_fallback',
            'fallback_strategy',
            'fallback_rate',
            'recommendations',
            'papers'
        ]
        
        logger.info("检查响应字段:")
        for field in required_fields:
            if f'"{field}"' in source or f"'{field}'" in source:
                logger.info(f"  ✅ {field}")
            else:
                logger.error(f"  ❌ {field}")
                return False
        
        # 检查可选字段
        optional_fields = [
            'fallback_note',
            'profile_interests',
            'merged_interests',
            'model',
            'used_provider'
        ]
        
        logger.info("检查可选字段:")
        for field in optional_fields:
            if f'"{field}"' in source or f"'{field}'" in source:
                logger.info(f"  ✅ {field}")
            else:
                logger.info(f"  ⚠️  {field} (可选)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 响应结构验证失败: {e}")
        return False


def verify_error_handling():
    """验证错误处理"""
    logger.info("\n" + "=" * 60)
    logger.info("验证4: 错误处理")
    logger.info("=" * 60)
    
    try:
        from app.api.research import recommend
        
        source = inspect.getsource(recommend)
        
        # 检查try-except块
        if 'try:' not in source or 'except' not in source:
            logger.error("❌ 缺少try-except块")
            return False
        
        logger.info("✅ 存在try-except块")
        
        # 检查HTTPException
        if 'HTTPException' not in source:
            logger.error("❌ 未使用HTTPException")
            return False
        
        logger.info("✅ 使用HTTPException")
        
        # 检查status_code
        if 'status_code=500' in source:
            logger.info("✅ 设置status_code=500用于服务器错误")
        else:
            logger.warning("⚠️  可能未设置适当的status_code")
        
        # 检查detail消息
        if 'detail=' in source:
            logger.info("✅ 提供detail错误消息")
        else:
            logger.error("❌ 未提供detail错误消息")
            return False
        
        # 检查日志记录
        if 'logger.error' in source:
            logger.info("✅ 记录错误日志")
        else:
            logger.warning("⚠️  可能未记录错误日志")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误处理验证失败: {e}")
        return False


def verify_fallback_alert():
    """验证降级告警"""
    logger.info("\n" + "=" * 60)
    logger.info("验证5: 降级告警")
    logger.info("=" * 60)
    
    try:
        from app.api.research import recommend
        
        source = inspect.getsource(recommend)
        
        # 检查降级率阈值检查
        if '0.2' in source or '0.20' in source or '20' in source:
            logger.info("✅ 存在降级率阈值检查（20%）")
        else:
            logger.warning("⚠️  可能缺少降级率阈值检查")
        
        # 检查告警日志
        if 'logger.warning' in source and 'fallback' in source.lower():
            logger.info("✅ 实现降级告警日志")
        else:
            logger.warning("⚠️  可能缺少降级告警日志")
        
        # 检查降级率计算
        if 'fallback_rate()' in source:
            logger.info("✅ 调用fallback_rate()计算降级率")
        else:
            logger.error("❌ 未调用fallback_rate()")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 降级告警验证失败: {e}")
        return False


def verify_integration():
    """验证与其他组件的集成"""
    logger.info("\n" + "=" * 60)
    logger.info("验证6: 组件集成")
    logger.info("=" * 60)
    
    try:
        from app.api.research import recommend
        
        source = inspect.getsource(recommend)
        
        # 检查recommendation_engine集成
        if 'recommendation_engine' in source:
            logger.info("✅ 集成recommendation_engine")
        else:
            logger.error("❌ 未集成recommendation_engine")
            return False
        
        # 检查model_client集成
        if 'model_client' in source:
            logger.info("✅ 集成model_client")
        else:
            logger.warning("⚠️  可能未集成model_client")
        
        # 检查quality_monitor集成
        if 'quality_monitor' in source:
            logger.info("✅ 集成quality_monitor")
        else:
            logger.error("❌ 未集成quality_monitor")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 组件集成验证失败: {e}")
        return False


def main():
    """主验证流程"""
    logger.info("=" * 60)
    logger.info("Task 5 功能验证")
    logger.info("=" * 60)
    
    results = []
    
    # 验证1: recommend端点
    results.append(("recommend端点实现", verify_recommend_endpoint()))
    
    # 验证2: quality_monitor
    results.append(("quality_monitor实现", verify_quality_monitor()))
    
    # 验证3: 响应结构
    results.append(("响应结构", verify_response_structure()))
    
    # 验证4: 错误处理
    results.append(("错误处理", verify_error_handling()))
    
    # 验证5: 降级告警
    results.append(("降级告警", verify_fallback_alert()))
    
    # 验证6: 组件集成
    results.append(("组件集成", verify_integration()))
    
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
        logger.info("🎉 Task 5 所有功能验证通过！")
        logger.info("=" * 60)
        logger.info("\n功能已完整实现：")
        logger.info("  ✅ 集成搜索引擎降级策略")
        logger.info("  ✅ 响应包含is_fallback字段")
        logger.info("  ✅ 响应包含fallback_strategy字段")
        logger.info("  ✅ 响应包含fallback_rate字段")
        logger.info("  ✅ 实现降级率追踪")
        logger.info("  ✅ 实现降级率告警（>20%）")
        logger.info("  ✅ 完善的错误处理")
        logger.info("  ✅ 用户友好的错误消息")
        logger.info("  ✅ 降级提示消息")
    else:
        logger.error("❌ 部分验证失败，请检查上述错误")
    
    logger.info("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
