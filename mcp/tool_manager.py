"""MCP 工具管理器"""
import logging
from typing import Dict, Any, List, Optional
from .base import BaseMCPTool
from .weather_tool import WeatherTool

logger = logging.getLogger(__name__)


class ToolManager:
    """MCP 工具管理器"""
    
    def __init__(self):
        self.tools: Dict[str, BaseMCPTool] = {}
        self._tool_classes = {
            "weather": WeatherTool,
        }
        
        logger.info("✅ MCP 工具管理器初始化完成")
    
    def register_tool_class(self, tool_type: str, tool_class: type):
        """注册工具类"""
        self._tool_classes[tool_type] = tool_class
        logger.info(f"✅ 注册工具类: {tool_type}")
    
    def load_tools(self, tools_config: Dict[str, Any]):
        """
        加载工具
        
        Args:
            tools_config: 工具配置字典
        """
        for tool_name, tool_config in tools_config.items():
            if not tool_config.get("enabled", False):
                logger.info(f"⏭️ 跳过未启用的工具: {tool_name}")
                continue
            
            # 根据 tool_name 确定工具类型
            tool_type = tool_name  # 简单映射，可以根据需要扩展
            
            if tool_type not in self._tool_classes:
                logger.warning(f"⚠️ 未知的工具类型: {tool_type}")
                continue
            
            try:
                tool_class = self._tool_classes[tool_type]
                tool = tool_class(tool_name, tool_config)
                self.tools[tool_name] = tool
                logger.info(f"✅ 加载工具: {tool_name}")
            except Exception as e:
                logger.error(f"❌ 加载工具 {tool_name} 失败: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseMCPTool]:
        """获取工具"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return f"❌ 工具不存在: {tool_name}"
        
        if not tool.is_enabled():
            return f"❌ 工具未启用: {tool_name}"
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"❌ 工具执行失败 {tool_name}: {e}")
            return f"❌ 工具执行失败：{str(e)}"
    
    def get_tools_info(self) -> List[Dict[str, str]]:
        """获取所有工具信息"""
        return [tool.get_info() for tool in self.tools.values()]
    
    def get_tools_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 JSON Schema"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self.tools


# 全局工具管理器
tool_manager = ToolManager()
