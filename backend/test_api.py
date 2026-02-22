"""测试 API 连接"""
import asyncio
from app.utils.model_client import model_client

async def test():
    print("测试 API 连接...")
    
    messages = [
        {"role": "user", "content": "你好，请用一句话介绍你自己。"}
    ]
    
    try:
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        if result:
            print(f"\n✅ API 调用成功！")
            print(f"模型：{result.get('model')}")
            print(f"提供商：{result.get('used_provider')}")
            print(f"回复：{result.get('content')}")
        else:
            print("\n❌ API 调用失败")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
