"""OpenAI 兼容客户端"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from .base import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI 兼容客户端（支持公司内网）"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        
        # 初始化 LangChain ChatOpenAI
        try:
            self.client = ChatOpenAI(
                base_url=self.base_url,
                model=self.model,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            logger.info(f"✅ OpenAI 客户端初始化成功: {self.base_url}")
        except Exception as e:
            logger.error(f"❌ OpenAI 客户端初始化失败: {e}")
            raise
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """调用 OpenAI API"""
        try:
            response = self.client.invoke(prompt, **kwargs)
            return response.content
        except Exception as e:
            logger.error(f"❌ OpenAI API 调用失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            # 简单的测试调用
            response = self.invoke("测试连接")
            return bool(response)
        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}")
            return False
