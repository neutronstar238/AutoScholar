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
        
        messages = [
            {
                "role": "system",
                "content": "你是一位专业的学术研究助手。请根据提供的论文生成详细的研究笔记，包括：核心贡献、方法论、实验结果、局限性、未来方向。"
            },
            {
                "role": "user",
                "content": f"请为这篇论文生成研究笔记：{paper_url}"
            }
        ]
        
        # 调用 LLM
        result = await model_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        
        if result:
            return {
                "success": True,
                "task": "note_generation",
                "url": paper_url,
                "note": result["content"],
                "model": result.get("model"),
                "used_provider": result.get("used_provider")
            }
        else:
            return {
                "success": False,
                "error": "LLM 调用失败"
            }
