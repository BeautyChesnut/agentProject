"""对话链管理"""
import logging
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.runnables.history import RunnableWithMessageHistory
from ..llm.base import BaseLLMClient
from ..mcp.tool_manager import ToolManager
from .memory import MemoryManager

logger = logging.getLogger(__name__)


class ChatChain:
    """对话链管理器"""
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        tool_manager: Optional[ToolManager] = None,
        memory_manager: Optional[MemoryManager] = None,
        chat_config: Optional[Dict[str, Any]] = None
    ):
        self.llm_client = llm_client
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager or MemoryManager()
        self.chat_config = chat_config or {}
        
        # 构建对话链
        self.chain = self._build_chain()
        
        logger.info("✅ 对话链构建完成")
    
    def _build_chain(self) -> RunnableWithMessageHistory:
        """构建带记忆的对话链"""
        # 获取系统提示词
        system_prompt = self.chat_config.get("prompt", {}).get(
            "system",
            "你是专业的智能助手，会结合对话历史回答用户问题，语言简洁、准确。"
        )
        
        # 定义 Prompt 模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        
        # 基础链
        base_chain = RunnableSequence(
            prompt,
            RunnableLambda(self._call_llm_with_tools),
            StrOutputParser()
        )
        
        # 添加多轮记忆
        chain_with_history = RunnableWithMessageHistory(
            base_chain,
            self.memory_manager.get_history,
            input_messages_key="question",
            history_messages_key="history"
        )
        
        return chain_with_history
    
    def _call_llm_with_tools(self, raw_prompt) -> str:
        """调用 LLM 并支持工具调用"""
        prompt_text = raw_prompt.to_string()
        
        # 检测是否需要调用工具
        if self.tool_manager:
            prompt_text = self._detect_and_call_tools(prompt_text)
        
        # 调用 LLM
        return self.llm_client.invoke(prompt_text)
    
    def _detect_and_call_tools(self, prompt_text: str) -> str:
        """检测并调用工具"""
        # 天气工具检测
        if self.tool_manager.has_tool("weather"):
            weather_keywords = [
                "天气", "气温", "温度", "下雨", "晴天",
                "多云", "冷不冷", "热不热", "今天天气", "明天天气"
            ]
            
            is_weather_query = any(kw in prompt_text for kw in weather_keywords)
            
            if is_weather_query:
                # 查找城市
                weather_tool = self.tool_manager.get_tool("weather")
                supported_cities = weather_tool.supported_cities if hasattr(weather_tool, 'supported_cities') else {}
                
                mentioned_city = None
                for city in supported_cities.keys():
                    if city in prompt_text:
                        mentioned_city = city
                        break
                
                if mentioned_city:
                    logger.info(f"🌤️ 检测到天气查询: {mentioned_city}")
                    weather_info = self.tool_manager.execute_tool("weather", city=mentioned_city)
                    prompt_text = (
                        f"{prompt_text}\n\n"
                        f"【实时天气信息（MCP）】\n"
                        f"{weather_info}\n\n"
                        f"请基于以上天气信息回答用户问题。"
                    )
        
        return prompt_text
    
    def chat(self, question: str, session_id: str = "default") -> str:
        """
        进行对话
        
        Args:
            question: 用户问题
            session_id: 会话 ID
            
        Returns:
            回答
        """
        try:
            answer = self.chain.invoke(
                {"question": question},
                config={"configurable": {"session_id": session_id}}
            )
            return answer
        except Exception as e:
            logger.error(f"❌ 对话失败: {e}")
            raise
    
    def clear_history(self, session_id: str = "default"):
        """清空对话历史"""
        self.memory_manager.clear_history(session_id)
