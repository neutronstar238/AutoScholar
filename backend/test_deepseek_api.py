"""测试 DeepSeek API 配置"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.model_client import model_client
from app.utils.config import settings
from loguru import logger


async def test_deepseek():
    """测试 DeepSeek API"""
    print("=" * 60)
    print("DeepSeek API 配置测试")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n1. 检查配置")
    print(f"   DeepSeek API Key: {'已配置 ✓' if settings.DEEPSEEK_API_KEY else '未配置 ✗'}")
    print(f"   DeepSeek Base URL: {settings.DEEPSEEK_BASE_URL}")
    print(f"   DeepSeek Model: {settings.DEEPSEEK_MODEL}")
    
    if not settings.DEEPSEEK_API_KEY:
        print("\n❌ 错误：未配置 DEEPSEEK_API_KEY")
        print("   请在 .env 文件中添加：")
        print("   DEEPSEEK_API_KEY=sk-your-key-here")
        return False
    
    # 2. 测试简单对话
    print("\n2. 测试简单对话")
    print("   发送消息: '你好，请用一句话介绍你自己'")
    
    try:
        messages = [
            {"role": "user", "content": "你好，请用一句话介绍你自己"}
        ]
        
        # 强制使用 DeepSeek（通过临时修改配置）
        original_providers = settings.MODEL_PROVIDERS
        settings.MODEL_PROVIDERS = "deepseek"
        
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=100,
            use_fallback=False  # 不使用回退，只测试 DeepSeek
        )
        
        # 恢复原配置
        settings.MODEL_PROVIDERS = original_providers
        
        if result:
            print(f"\n   ✅ DeepSeek 响应成功！")
            print(f"   使用的提供商: {result.get('used_provider', 'unknown')}")
            print(f"   使用的模型: {result.get('model', 'unknown')}")
            print(f"\n   回复内容:")
            print(f"   {result['content']}")
            
            if result.get('usage'):
                print(f"\n   Token 使用情况:")
                print(f"   - 输入: {result['usage'].get('prompt_tokens', 0)}")
                print(f"   - 输出: {result['usage'].get('completion_tokens', 0)}")
                print(f"   - 总计: {result['usage'].get('total_tokens', 0)}")
        else:
            print("\n   ❌ DeepSeek 调用失败")
            return False
            
    except Exception as e:
        print(f"\n   ❌ 调用出错: {str(e)}")
        import traceback
        print(f"\n   详细错误信息:")
        print(traceback.format_exc())
        return False
    
    # 3. 测试学术翻译场景
    print("\n" + "=" * 60)
    print("3. 测试学术翻译场景")
    print("   任务: 将'深度学习'翻译为英文学术术语")
    
    try:
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的学术翻译专家。请将中文学术术语翻译为准确的英文学术术语。"
            },
            {
                "role": "user",
                "content": "请将以下中文学术术语翻译为英文：深度学习\n\n只返回英文翻译，不要解释。"
            }
        ]
        
        # 强制使用 DeepSeek
        settings.MODEL_PROVIDERS = "deepseek"
        
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.3,  # 较低温度以获得更确定的翻译
            max_tokens=50,
            use_fallback=False
        )
        
        # 恢复原配置
        settings.MODEL_PROVIDERS = original_providers
        
        if result:
            print(f"\n   ✅ 翻译成功！")
            print(f"   翻译结果: {result['content']}")
        else:
            print("\n   ❌ 翻译失败")
            return False
            
    except Exception as e:
        print(f"\n   ❌ 翻译出错: {str(e)}")
        return False
    
    # 4. 测试推荐生成场景
    print("\n" + "=" * 60)
    print("4. 测试研究方向推荐生成场景")
    print("   任务: 基于'机器学习'生成研究方向推荐")
    
    try:
        messages = [
            {
                "role": "system",
                "content": "你是一位资深的学术研究顾问，擅长为研究人员提供研究方向建议。"
            },
            {
                "role": "user",
                "content": """基于以下信息，生成研究方向推荐：

用户兴趣: 机器学习
相关论文数量: 5篇

请用简洁的语言（不超过100字）推荐2-3个研究方向。"""
            }
        ]
        
        # 强制使用 DeepSeek
        settings.MODEL_PROVIDERS = "deepseek"
        
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=200,
            use_fallback=False
        )
        
        # 恢复原配置
        settings.MODEL_PROVIDERS = original_providers
        
        if result:
            print(f"\n   ✅ 推荐生成成功！")
            print(f"\n   推荐内容:")
            print(f"   {result['content']}")
        else:
            print("\n   ❌ 推荐生成失败")
            return False
            
    except Exception as e:
        print(f"\n   ❌ 推荐生成出错: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！DeepSeek API 配置正确")
    print("=" * 60)
    return True


async def test_all_providers():
    """测试所有配置的提供商"""
    print("\n" + "=" * 60)
    print("测试所有配置的提供商")
    print("=" * 60)
    
    results = await model_client.test_connection()
    
    print("\n提供商连接状态:")
    for provider, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {provider}: {'可用' if status else '不可用'}")
    
    return results


if __name__ == "__main__":
    print("\n🚀 开始测试 DeepSeek API...\n")
    
    # 运行 DeepSeek 测试
    success = asyncio.run(test_deepseek())
    
    # 测试所有提供商
    asyncio.run(test_all_providers())
    
    if success:
        print("\n✅ DeepSeek API 测试完成！")
        sys.exit(0)
    else:
        print("\n❌ DeepSeek API 测试失败")
        sys.exit(1)
