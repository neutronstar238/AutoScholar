"""
文献检索工具
支持 arXiv 和 Semantic Scholar
"""

import httpx
from typing import List, Dict, Any
from loguru import logger


async def search_literature(
    query: str,
    limit: int = 10,
    source: str = "arxiv"
) -> List[Dict[str, Any]]:
    """
    搜索学术文献
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量
        source: 数据源 (arxiv | scholar)
    
    Returns:
        论文列表
    """
    logger.info(f"搜索文献：{query}, 来源：{source}")
    
    if source == "arxiv":
        return await _search_arxiv(query, limit)
    elif source == "scholar":
        return await _search_scholar(query, limit)
    else:
        raise ValueError(f"不支持的数据源：{source}")


async def _search_arxiv(query: str, limit: int) -> List[Dict[str, Any]]:
    """搜索 arXiv"""
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            
            # 解析 XML 响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            papers = []
            entries = root.findall("atom:entry", ns)[:limit]
            
            for entry in entries:
                paper = {
                    "id": entry.find("atom:id", ns).text.split("/")[-1] if entry.find("atom:id", ns) is not None else "",
                    "title": entry.find("atom:title", ns).text.strip() if entry.find("atom:title", ns) is not None else "",
                    "abstract": entry.find("atom:summary", ns).text.strip() if entry.find("atom:summary", ns) is not None else "",
                    "url": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else "",
                    "authors": [],
                    "published": entry.find("atom:published", ns).text[:10] if entry.find("atom:published", ns) is not None else ""
                }
                
                # 获取作者列表
                authors = entry.findall("atom:author", ns)
                for author in authors:
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        paper["authors"].append(name_elem.text)
                
                papers.append(paper)
            
            logger.info(f"arXiv 搜索成功，找到 {len(papers)} 篇论文")
            return papers
            
    except Exception as e:
        logger.error(f"arXiv 搜索失败：{e}")
        return []


async def _search_scholar(query: str, limit: int) -> List[Dict[str, Any]]:
    """搜索 Semantic Scholar"""
    # TODO: 实现 Semantic Scholar API 调用
    logger.warning("Semantic Scholar 搜索暂未实现")
    return []
