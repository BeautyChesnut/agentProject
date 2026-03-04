"""LLM 客户端工厂"""
import logging
from typing import Dict, Any, Optional
from .base import BaseLLMClient
from .openai_client import OpenAIClient
from .zhipu_client import ZhipuClient

logger = logging.getLogger(__name__)


class LLMFactory:
    """LLM 客户端工厂"""
    
    # 注册的客户端类型
    _clients = {
        "openai": OpenAIClient,
        "zhipuai": ZhipuClient,
    }
    
    @classmethod
    def register_client(cls, provider: str, client_class: type):
        """
        注册新的客户端类型
        
        Args:
            provider: 提供商名称
            client_class: 客户端类
        """
        cls._clients[provider] = client_class
        logger.info(f"✅ 注册 LLM 客户端: {provider}")
    
    @classmethod
    def create_client(cls, config: Dict[str, Any]) -> BaseLLMClient:
        """
        创建 LLM 客户端
        
        Args:
            config: 客户端配置
            
        Returns:
            LLM 客户端实例
        """
        provider = config.get("provider", "openai")
        
        if provider not in cls._clients:
            raise ValueError(f"❌ 不支持的 LLM 提供商: {provider}")
        
        client_class = cls._clients[provider]
        
        try:
            client = client_class(config)
            logger.info(f"✅ 创建 LLM 客户端: {provider}")
            return client
        except Exception as e:
            logger.error(f"❌ 创建 LLM 客户端失败: {e}")
            raise
    
    @classmethod
    def list_providers(cls) -> list:
        """列出所有支持的提供商"""
        return list(cls._clients.keys())


def create_llm_client(config: Dict[str, Any]) -> BaseLLMClient:
    """创建 LLM 客户端的便捷函数"""
    return LLMFactory.create_client(config)
