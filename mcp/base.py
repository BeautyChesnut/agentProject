"""MCP 工具基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseMCPTool(ABC):
    """MCP 工具抽象基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化 MCP 工具
        
        Args:
            name: 工具名称
            config: 工具配置
        """
        self.name = name
        self.config = config
        self.provider = config.get("provider", "unknown")
        self.enabled = config.get("enabled", False)
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的 JSON Schema
        
        Returns:
            工具的 JSON Schema
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查工具是否启用"""
        return self.enabled
    
    def get_info(self) -> Dict[str, str]:
        """获取工具信息"""
        return {
            "name": self.name,
            "provider": self.provider,
            "description": self.config.get("description", ""),
            "enabled": str(self.enabled)
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} enabled={self.enabled}>"
