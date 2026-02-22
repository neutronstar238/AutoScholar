"""
研究员 Agent
负责文献检索、分析和研究笔记生成
"""

from typing import Dict, Any, List
from loguru import logger
from .base import BaseAgent
from ..tools.literature_search import search_literature
from ..utils.model_client import model_client


class ResearcherAgent(BaseAgent):
    """研究员 Agent - 负责学术研究相关任务"""
    
    def __init__(self):
        super().__init__(
            name="Researcher",
            description="负责文献检索、分析和研究笔记生成"
        )
    
    async def execute(
        self,
        task: str,
        query: str = "",
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行研究任务
        
        Args:
            task: 任务类型 (search | analyze | generate_note)
            query: 搜索关键词或论文 URL
            limit: 返回结果数量
        
        Returns:
            研究结果
        """
        self.log_info(f"开始执行任务：{task}, 查询：{query}")
        
        try:
            if task == "search":
                return await self._search_literature(query, limit)
            elif task == "analyze":
                return await self._analyze_paper(query)
            elif task == "generate_note":
                return await self._generate_note(query)
            else:
                raise ValueError(f"未知任务类型：{task}")
                
        except Exception as e:
            self.log_error(f"任务执行失败：{e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _search_literature(self, query: str, limit: int) -> Dict[str, Any]:
        """搜索文献"""
        self.log_info(f"搜索文献：{query}")
        
        # 调用文献检索工具
        results = await search_literature(query, limit)
        
        return {
            "success": True,
            "task": "literature_search",
            "query": query,
            "count": len(results),
            "papers": results
        }
    
    async def _analyze_paper(self, paper_url: str) -> Dict[str, Any]:
        """分析论文"""
        self.log_info(f"分析论文：{paper_url}")
        
        # TODO: 实现论文分析逻辑
        # 1. 获取论文内容
        # 2. 使用 LLM 分析
        # 3. 提取关键信息
        
        return {
            "success": True,
            "task": "paper_analysis",
            "url": paper_url,
            "analysis": "待实现"
        }
    
    async def _generate_note(self, paper_url: str) -> Dict[str, Any]:
        """生成研究笔记"""
        self.log_info(f"生成笔记：{paper_url}")
        
        try:
            # 1. 从 URL 提取 arXiv ID
            import re
            arxiv_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', paper_url)
            if not arxiv_match:
                return {
                    "success": False,
                    "error": "无效的 arXiv URL 格式。请提供格式如：https://arxiv.org/abs/2401.12345"
                }
            
            arxiv_id = arxiv_match.group(1)
            self.log_info(f"提取到 arXiv ID: {arxiv_id}")
            
            # 2. 搜索论文获取详细信息
            papers = await search_literature(arxiv_id, limit=1)
            
            if not papers:
                return {
                    "success": False,
                    "error": f"未找到论文 {arxiv_id}。请检查 arXiv ID 是否正确。"
                }
            
            paper = papers[0]
            self.log_info(f"找到论文：{paper['title']}")
            
            # 3. 构建详细的提示词（限制摘要长度）
            abstract_preview = paper['abstract'][:500] + "..." if len(paper['abstract']) > 500 else paper['abstract']
            
            paper_info = f"""
论文标题：{paper['title']}

作者：{', '.join(paper['authors'][:5])}

发布日期：{paper['published']}

摘要：
{abstract_preview}

arXiv ID：{paper['id']}
"""
            
            messages = [
                {
                    "role": "system",
                    "content": """你是一位专业的学术研究助手。请根据提供的论文信息生成详细的研究笔记。

研究笔记应包含以下部分：

1. 📌 核心贡献
   - 论文的主要创新点
   - 解决了什么问题

2. 🔬 方法论
   - 使用的技术和方法
   - 关键算法或架构

3. 📊 实验结果
   - 主要实验设置
   - 关键性能指标

4. ⚠️ 局限性
   - 方法的限制
   - 未解决的问题

5. 🚀 未来方向
   - 可能的改进方向
   - 潜在应用场景

请用清晰、结构化的方式组织内容，使用 Markdown 格式。"""
                },
                {
                    "role": "user",
                    "content": f"请为以下论文生成研究笔记：\n\n{paper_info}"
                }
            ]
            
            # 4. 调用 LLM 生成笔记
            self.log_info("正在调用 LLM 生成笔记...")
            result = await model_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1500  # 减少 token 数量
            )
            
            if result:
                return {
                    "success": True,
                    "task": "note_generation",
                    "paper": {
                        "id": paper['id'],
                        "title": paper['title'],
                        "authors": paper['authors'],
                        "published": paper['published'],
                        "url": paper['url']
                    },
                    "note": result["content"],
                    "model": result.get("model"),
                    "used_provider": result.get("used_provider")
                }
            else:
                return {
                    "success": False,
                    "error": "LLM 调用失败"
                }
                
        except Exception as e:
            self.log_error(f"生成笔记失败：{e}")
            return {
                "success": False,
                "error": str(e)
            }
