"""测试文献检索功能"""
import asyncio
from app.tools.literature_search import search_literature

async def test():
    print("测试 arXiv 搜索...")
    results = await search_literature("machine learning", limit=5)
    print(f"找到 {len(results)} 篇论文")
    
    for i, paper in enumerate(results[:3], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   作者: {', '.join(paper['authors'][:3])}")
        print(f"   发布: {paper['published']}")
        print(f"   URL: {paper['url']}")

if __name__ == "__main__":
    asyncio.run(test())
