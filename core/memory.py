"""对话记忆管理"""
import logging
from typing import Dict
from langchain_core.chat_history import InMemoryChatMessageHistory

logger = logging.getLogger(__name__)


class MemoryManager:
    """对话记忆管理器"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.histories: Dict[str, InMemoryChatMessageHistory] = {}
        
        logger.info(f"✅ 对话记忆管理器初始化完成 (max_history={max_history})")
    
    def get_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """获取或创建对话历史"""
        if session_id not in self.histories:
            self.histories[session_id] = InMemoryChatMessageHistory()
            logger.info(f"📝 创建新会话: {session_id}")
        
        return self.histories[session_id]
    
    def clear_history(self, session_id: str):
        """清空对话历史"""
        if session_id in self.histories:
            self.histories[session_id].clear()
            logger.info(f"🗑️ 清空会话历史: {session_id}")
    
    def list_sessions(self) -> list:
        """列出所有会话"""
        return list(self.histories.keys())
    
    def remove_session(self, session_id: str):
        """删除会话"""
        if session_id in self.histories:
            del self.histories[session_id]
            logger.info(f"❌ 删除会话: {session_id}")
    
    def get_session_count(self) -> int:
        """获取会话数量"""
        return len(self.histories)
