"""测试笔记生成功能"""
import asyncio
from app.agents.researcher import ResearcherAgent

async def test():
    researcher = ResearcherAgent()
    
    # 测试一个真实的 arXiv 论文
    print("测试笔记生成功能...")
    print("=" * 60)
    
    # 使用一个真实存在的论文 ID
    paper_url = "https://arxiv.org/abs/2306.04338"
    
    result = await researcher.execute(
        task="generate_note",
        query=paper_url
    )
    
    if result["success"]:
        print(f"\n✅ 笔记生成成功！")
        print(f"\n论文信息：")
        print(f"  标题: {result['paper']['title']}")
        print(f"  作者: {', '.join(result['paper']['authors'][:3])}")
        print(f"  发布: {result['paper']['published']}")
        print(f"  模型: {result['model']}")
        print(f"\n研究笔记：")
        print("=" * 60)
        print(result['note'])
    else:
        print(f"\n❌ 笔记生成失败：{result['error']}")

if __name__ == "__main__":
    asyncio.run(test())
