"""
模型客户端模块
支持多提供商自动回退机制
优先使用 Qwen3.5，失败则回退到 Qwen
"""

import httpx
from typing import Optional, Dict, Any, List
from loguru import logger
from .config import settings


class ModelClient:
    """AI 模型客户端 - 支持自动回退"""
    
    def __init__(self):
        self.base_urls = {
            "qwen3.5": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "openai": "https://api.openai.com/v1",
        }
        self.models = {
            "qwen3.5": "qwen-plus",  # Qwen 3.5 使用 qwen-plus
            "qwen": "qwen-turbo",     # Qwen 使用 qwen-turbo
            "deepseek": "deepseek-chat",
            "openai": "gpt-4",
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_fallback: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        发送聊天请求，支持自动回退
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            use_fallback: 是否启用回退机制
        
        Returns:
            API 响应结果，失败返回 None
        """
        # 获取可用的提供商列表
        providers = settings.available_providers.copy()
        
        if not use_fallback:
            # 不启用回退，只使用首选提供商
            providers = [settings.PRIMARY_PROVIDER]
        
        logger.info(f"🤖 尝试使用提供商：{providers}")
        
        # 依次尝试每个提供商
        for provider in providers:
            api_key = settings.get_api_key(provider)
            
            if not api_key:
                logger.warning(f"⚠️  提供商 {provider} 未配置 API Key，跳过")
                continue
            
            try:
                logger.info(f"📡 正在调用 {provider}...")
                result = await self._call_provider(
                    provider=provider,
                    api_key=api_key,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if result:
                    logger.success(f"✅ {provider} 调用成功！")
                    result["used_provider"] = provider
                    return result
                
            except Exception as e:
                logger.error(f"❌ {provider} 调用失败：{e}")
                if provider == providers[-1]:
                    # 已经是最后一个提供商，抛出异常
                    raise
        
        logger.error("❌ 所有提供商都调用失败")
        return None
    
    async def _call_provider(
        self,
        provider: str,
        api_key: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Optional[Dict[str, Any]]:
        """调用指定提供商的 API"""
        
        base_url = self.base_urls.get(provider)
        model = self.models.get(provider)
        
        if not base_url or not model:
            raise ValueError(f"不支持的提供商：{provider}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"API 返回错误：{response.status_code} - {response.text}")
            
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", model)
            }
    
    async def test_connection(self) -> Dict[str, bool]:
        """测试所有提供商的连接状态"""
        results = {}
        
        for provider in settings.available_providers:
            api_key = settings.get_api_key(provider)
            if not api_key:
                results[provider] = False
                continue
            
            try:
                test_messages = [
                    {"role": "user", "content": "Hello"}
                ]
                result = await self._call_provider(
                    provider=provider,
                    api_key=api_key,
                    messages=test_messages,
                    temperature=0.7,
                    max_tokens=10
                )
                results[provider] = result is not None
            except Exception as e:
                logger.error(f"{provider} 测试失败：{e}")
                results[provider] = False
        
        return results


# 创建全局客户端实例
model_client = ModelClient()
