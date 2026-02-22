"""
Agent 基类模块
所有 Agent 的父类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from loguru import logger


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.llm_client = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 Agent 任务
        
        Returns:
            执行结果字典
        """
        pass
    
    def log_info(self, message: str):
        """记录日志"""
        logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str):
        """记录错误"""
        logger.error(f"[{self.name}] {message}")
    
    def log_warning(self, message: str):
        """记录警告"""
        logger.warning(f"[{self.name}] {message}")
