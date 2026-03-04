"""LLM 客户端基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM 客户端
        
        Args:
            config: 客户端配置
        """
        self.config = config
        self.provider = config.get("provider", "unknown")
        self.model = config.get("model", "unknown")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2048)
    
    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        调用 LLM
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            LLM 响应文本
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            连接是否成功
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取客户端信息"""
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider={self.provider} model={self.model}>"
