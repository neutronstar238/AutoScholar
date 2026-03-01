"""
文献检索工具
支持 arXiv 和 Semantic Scholar
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any

import httpx
from loguru import logger

from app.utils.cache_manager import cache_manager


async def search_literature(
    query: str,
    limit: int = 10,
    source: str = "arxiv",
    sort_by: str = "relevance"
) -> List[Dict[str, Any]]:
    """搜索学术文献，优先读取缓存。"""
    logger.info(f"搜索文献：{query}, 来源：{source}, 排序：{sort_by}")

    cache_key = cache_manager.generate_key("literature", {
        "query": query,
        "limit": limit,
        "source": source,
        "sort_by": sort_by,
    })

    cached = await cache_manager.get(cache_key)
    if cached:
        return cached

    if source == "arxiv":
        papers = await _search_arxiv(query, limit, sort_by)
    elif source == "scholar":
        papers = await _search_scholar(query, limit)
    else:
        raise ValueError(f"不支持的数据源：{source}")

    if papers:
        await cache_manager.set(cache_key, papers, ttl_seconds=3600)
    return papers


async def _search_arxiv(query: str, limit: int, sort_by: str = "relevance") -> List[Dict[str, Any]]:
    """搜索 arXiv"""
    base_url = "https://export.arxiv.org/api/query"
    sort_map = {
        "relevance": "relevance",
        "submittedDate": "submittedDate",
        "lastUpdatedDate": "lastUpdatedDate",
        "date": "submittedDate"
    }

    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 100),
        "sortBy": sort_map.get(sort_by, "relevance"),
        "sortOrder": "descending"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            papers = []
            entries = root.findall("atom:entry", ns)
            if not entries:
                logger.warning(f"arXiv 未找到匹配的论文：{query}")
                return []

            for entry in entries[:limit]:
                paper = {
                    "id": entry.find("atom:id", ns).text.split("/")[-1] if entry.find("atom:id", ns) is not None else "",
                    "title": entry.find("atom:title", ns).text.strip().replace("\n", " ") if entry.find("atom:title", ns) is not None else "",
                    "abstract": entry.find("atom:summary", ns).text.strip().replace("\n", " ") if entry.find("atom:summary", ns) is not None else "",
                    "url": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else "",
                    "authors": [],
                    "published": entry.find("atom:published", ns).text[:10] if entry.find("atom:published", ns) is not None else "",
                    "updated": entry.find("atom:updated", ns).text[:10] if entry.find("atom:updated", ns) is not None else "",
                }
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        paper["authors"].append(name_elem.text)

                categories = entry.findall("atom:category", ns)
                paper["categories"] = [cat.get("term") for cat in categories if cat.get("term")]
                papers.append(paper)

            logger.info(f"arXiv 搜索成功，找到 {len(papers)} 篇论文")
            return papers

    except httpx.TimeoutException:
        logger.error(f"arXiv 搜索超时：{query}")
        return []
    except httpx.HTTPError as e:
        logger.error(f"arXiv HTTP 错误：{e}")
        return []
    except Exception as e:
        logger.error(f"arXiv 搜索失败：{e}")
        return []


async def _search_scholar(query: str, limit: int) -> List[Dict[str, Any]]:
    """搜索 Semantic Scholar"""
    logger.warning("Semantic Scholar 搜索暂未实现")
    return []
