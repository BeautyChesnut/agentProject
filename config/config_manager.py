"""配置管理模块"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """统一配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        if self._config is None:
            self.config_path = Path(config_path or "config/opencode.json")
            self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            # 尝试其他路径
            alternative_paths = [
                Path("opencode.json"),
                Path("config/opencode.json.example"),
                Path("../config/opencode.json")
            ]
            
            for alt_path in alternative_paths:
                if alt_path.exists():
                    self.config_path = alt_path
                    break
            else:
                logger.warning(f"⚠️ 配置文件不存在，使用默认配置")
                return self._default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 处理环境变量
                config = self._resolve_env_vars(config)
                logger.info(f"✅ 成功加载配置: {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            return self._default_config()
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """递归解析环境变量"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.getenv(env_var, config)
        else:
            return config
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "version": "2.0",
            "environment": "local",
            "llm": {
                "default": "local_gpt",
                "clients": {
                    "local_gpt": {
                        "provider": "openai",
                        "base_url": "http://localhost:8000/v1",
                        "model": "gpt-3.5-turbo",
                        "api_key": "sk-placeholder",
                        "temperature": 0.7,
                        "max_tokens": 2048
                    }
                }
            },
            "mcp": {
                "enabled": True,
                "tools": {}
            },
            "chat": {
                "session": {"max_history": 50, "timeout": 60},
                "prompt": {"system": "你是专业的智能助手", "temperature": 0.7}
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号分隔的路径）"""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_llm_config(self, client_name: Optional[str] = None) -> Dict[str, Any]:
        """获取 LLM 配置"""
        if client_name is None:
            client_name = self.get("llm.default", "local_gpt")
        
        return self.get(f"llm.clients.{client_name}", {})
    
    def get_mcp_tools(self) -> Dict[str, Any]:
        """获取所有 MCP 工具配置"""
        return self.get("mcp.tools", {})
    
    def get_enabled_mcp_tools(self) -> Dict[str, Any]:
        """获取启用的 MCP 工具"""
        tools = self.get_mcp_tools()
        return {name: config for name, config in tools.items() if config.get("enabled", False)}
    
    def get_chat_config(self) -> Dict[str, Any]:
        """获取对话配置"""
        return self.get("chat", {})
    
    def reload(self):
        """重新加载配置"""
        self._config = self._load_config()
        logger.info("🔄 配置已重新加载")
    
    @property
    def environment(self) -> str:
        """获取当前环境"""
        return self.get("environment", "unknown")
    
    @property
    def version(self) -> str:
        """获取配置版本"""
        return self.get("version", "1.0")


# 全局配置实例
config = ConfigManager()
