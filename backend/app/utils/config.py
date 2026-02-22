"""
配置管理模块
支持 API 模式和 Ollama 本地部署模式
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # ===== 基础配置 =====
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8000
    
    # ===== 数据库配置 =====
    DATABASE_URL: str = "postgresql://autoscholar:password@localhost:5432/autoscholar"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ===== AI 模型配置 =====
    # API 模式 - 支持多个提供商，按优先级排序
    QWEN35_API_KEY: Optional[str] = None  # Qwen 3.5 (优先)
    QWEN_API_KEY: Optional[str] = None    # Qwen (备选)
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # 模型提供商优先级列表 (默认使用 Qwen3.5，失败则回退到 Qwen)
    MODEL_PROVIDERS: List[str] = ["qwen3.5", "qwen"]
    PRIMARY_PROVIDER: str = "qwen3.5"
    FALLBACK_PROVIDER: str = "qwen"
    
    # Ollama 模式 (本地私有化部署)
    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    
    # ===== 前端配置 =====
    FRONTEND_URL: str = "http://localhost:3000"
    
    # ===== 平台集成配置 =====
    # 飞书
    FEISHU_APP_ID: Optional[str] = None
    FEISHU_APP_SECRET: Optional[str] = None
    FEISHU_VERIFICATION_TOKEN: Optional[str] = None
    
    # 企业微信
    WECOM_CORP_ID: Optional[str] = None
    WECOM_AGENT_SECRET: Optional[str] = None
    
    # 钉钉
    DINGTALK_APP_KEY: Optional[str] = None
    DINGTALK_APP_SECRET: Optional[str] = None
    
    # ===== 商业化配置 =====
    API_KEY_SECRET: str = "your-secret-key-change-in-production"
    STRIPE_SECRET_KEY: Optional[str] = None
    
    # ===== 属性 =====
    @property
    def is_ollama_mode(self) -> bool:
        """判断是否使用 Ollama 模式"""
        return self.OLLAMA_ENABLED or self.PRIMARY_PROVIDER == "ollama"
    
    @property
    def is_api_mode(self) -> bool:
        """判断是否使用 API 模式"""
        return not self.is_ollama_mode
    
    @property
    def current_provider(self) -> str:
        """获取当前使用的提供商"""
        if self.is_ollama_mode:
            return "ollama"
        return self.PRIMARY_PROVIDER
    
    @property
    def available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        if self.is_ollama_mode:
            return ["ollama"]
        return self.MODEL_PROVIDERS
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """获取指定提供商的 API Key"""
        key_map = {
            "qwen3.5": self.QWEN35_API_KEY,
            "qwen": self.QWEN_API_KEY,
            "deepseek": self.DEEPSEEK_API_KEY,
            "openai": self.OPENAI_API_KEY,
            "ollama": None  # Ollama 不需要 API Key
        }
        return key_map.get(provider)
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        if self.is_api_mode:
            # 检查至少有一个提供商配置了 API Key
            has_key = False
            for provider in self.MODEL_PROVIDERS:
                if self.get_api_key(provider):
                    has_key = True
                    break
            
            if not has_key:
                print("⚠️  警告：未配置任何 API Key")
                print("   请在 .env 文件中配置 QWEN35_API_KEY 或 QWEN_API_KEY")
        
        return True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 验证配置
try:
    settings.validate()
except ValueError as e:
    print(f"⚠️  配置警告：{e}")
    print("   请检查 .env 文件配置")
