"""智谱 GLM 客户端"""
import logging
from typing import Dict, Any
from zhipuai import ZhipuAI
from .base import BaseLLMClient

logger = logging.getLogger(__name__)


class ZhipuClient(BaseLLMClient):
    """智谱 GLM 客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        
        try:
            self.client = ZhipuAI(api_key=self.api_key)
            logger.info(f"✅ 智谱 GLM 客户端初始化成功: model={self.model}")
        except Exception as e:
            logger.error(f"❌ 智谱 GLM 客户端初始化失败: {e}")
            raise
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """调用智谱 API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ 智谱 API 调用失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = self.invoke("测试连接")
            return bool(response)
        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}")
            return False
