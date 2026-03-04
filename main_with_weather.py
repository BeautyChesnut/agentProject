import os
import logging
import warnings
import requests
import json
from typing import Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from zhipuai import ZhipuAI

# 忽略无关警告
warnings.filterwarnings("ignore", category=UserWarning, module="jwt")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ===================== 1. 初始化 GLM 客户端 =====================
def init_glm_client():
    """初始化智谱 GLM 客户端"""
    load_dotenv()
    glm_api_key = os.getenv("GLM_API_KEY")

    if not glm_api_key:
        raise ValueError("❌ 未找到 GLM_API_KEY，请在 .env 文件中配置")

    try:
        client = ZhipuAI(api_key=glm_api_key)
        logger.info("✅ GLM 客户端初始化成功")
        return client
    except Exception as e:
        raise Exception(f"❌ GLM 客户端初始化失败：{str(e)}")


glm_client = init_glm_client()

# ===================== 2. 全局对话记忆 =====================
chat_histories = {}


def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    """获取/创建指定会话的对话历史"""
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]


# ===================== 3. 天气查询工具 =====================
@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的实时天气信息。
    
    Args:
        city: 城市名称，如"北京"、"上海"、"广州"等
    
    Returns:
        天气信息字符串，包含温度、天气状况、风向等
    """
    try:
        # 使用 wttr.in 免费 API（无需 API Key）
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"❌ 无法获取 {city} 的天气信息"
        
        data = response.json()
        
        # 解析天气数据
        current = data.get("current_condition", [{}])[0]
        location = data.get("nearest_area", [{}])[0]
        
        city_name = location.get("areaName", [{}])[0].get("value", city)
        temp = current.get("temp_C", "未知")
        feels_like = current.get("FeelsLikeC", "未知")
        humidity = current.get("humidity", "未知")
        weather_desc = current.get("lang_zh", [{}])[0].get("value", 
                    current.get("weatherDesc", [{}])[0].get("value", "未知"))
        wind_dir = current.get("winddir16Point", "未知")
        wind_speed = current.get("windspeedKmph", "未知")
        
        result = f"""🌍 城市：{city_name}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{weather_desc}
💧 湿度：{humidity}%
🌬️ 风向：{wind_dir}，风速 {wind_speed} km/h"""
        
        return result
        
    except requests.exceptions.Timeout:
        return f"❌ 查询 {city} 天气超时，请稍后重试"
    except Exception as e:
        return f"❌ 查询天气时出错：{str(e)}"


# ===================== 4. 构建 Agent =====================
def build_agent_with_tools():
    """构建带工具的智能 Agent"""
    
    # 定义工具列表
    tools = [get_weather]
    
    # 定义 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能助手，可以回答用户问题并使用工具获取实时信息。

你有以下工具可用：
- get_weather: 查询指定城市的实时天气

使用工具时，请根据用户的问题选择合适的工具。如果不需要工具，直接回答即可。
回答要简洁、准确、友好。"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 创建 GLM LLM 包装器
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
    from langchain_core.outputs import ChatResult, ChatGeneration
    from pydantic import BaseModel
    from typing import List, Any
    
    class ChatGLM(BaseChatModel, BaseModel):
        """GLM Chat Model 包装器"""
        client: Any = None
        
        def __init__(self, client, **kwargs):
            super().__init__(**kwargs)
            self.client = client
        
        @property
        def _llm_type(self) -> str:
            return "glm"
        
        def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            **kwargs
        ) -> ChatResult:
            # 转换消息格式
            glm_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    glm_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    glm_messages.append({"role": "assistant", "content": msg.content})
                else:
                    glm_messages.append({"role": "user", "content": str(msg.content)})
            
            # 调用 GLM API
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=glm_messages,
                temperature=0.7,
                max_tokens=2048
            )
            
            content = response.choices[0].message.content
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=content))]
            )
    
    # 创建 LLM
    llm = ChatGLM(client=glm_client)
    
    # 创建 Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 创建 Agent Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    logger.info("✅ 带 Agent 的问答链构建成功")
    return agent_executor


# ===================== 5. 简化版：直接调用天气 API =====================
def build_simple_chain_with_weather():
    """构建简化版问答链（带天气检测）"""
    
    # 定义 Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是专业的智能助手，会结合对话历史回答用户问题。

如果用户询问天气相关的问题，请告诉用户你会调用天气查询功能。
回答要简洁、准确。"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    def call_glm_with_weather_check(raw_prompt):
        """调用 GLM，并在需要时调用天气 API"""
        prompt_text = raw_prompt.to_string()
        
        # 检测是否询问天气
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴天", "多云", "冷不冷", "热不热"]
        city_patterns = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安", "南京", "苏州", "东莞"]
        
        is_weather_query = any(kw in prompt_text for kw in weather_keywords)
        mentioned_city = None
        
        for city in city_patterns:
            if city in prompt_text:
                mentioned_city = city
                break
        
        # 如果是天气查询，先获取天气信息
        weather_info = ""
        if is_weather_query and mentioned_city:
            logger.info(f"🌤️ 检测到天气查询，城市：{mentioned_city}")
            weather_info = get_weather.invoke({"city": mentioned_city})
            weather_info = f"\n\n【实时天气信息】\n{weather_info}\n\n请基于以上天气信息回答用户问题。"
            prompt_text = prompt_text + weather_info
        
        # 调用 GLM
        response = glm_client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    
    # 构建链
    base_chain = RunnableSequence(
        prompt,
        RunnableLambda(call_glm_with_weather_check),
        StrOutputParser()
    )
    
    # 添加记忆
    chain_with_history = RunnableWithMessageHistory(
        base_chain,
        get_chat_history,
        input_messages_key="question",
        history_messages_key="history"
    )
    
    logger.info("✅ 简化版问答链构建成功")
    return chain_with_history


# ===================== 6. 交互式对话主函数 =====================
def start_chat():
    """启动带天气查询的交互式对话"""
    try:
        # 使用简化版链（更稳定）
        qa_chain = build_simple_chain_with_weather()
        session_id = "default_session"
        
        print("\n" + "=" * 50)
        print("🎉 GLM 智能问答助手（带天气查询功能）")
        print("💡 支持多轮对话，可查询实时天气")
        print("💡 输入 'exit/quit/退出' 结束对话")
        print("=" * 50 + "\n")
        
        while True:
            user_input = input("你: ")
            
            if user_input.lower() in ["exit", "quit", "退出", "结束"]:
                print("GLM: 再见！有任何问题都可以再来问我～")
                chat_histories[session_id].clear()
                break
            
            if not user_input.strip():
                print("GLM: 请输入具体的问题，我会尽力解答～\n")
                continue
            
            try:
                answer = qa_chain.invoke(
                    {"question": user_input},
                    config={"configurable": {"session_id": session_id}}
                )
                print(f"GLM: {answer}\n")
            except Exception as e:
                logger.error(f"回答生成失败：{str(e)}")
                print(f"GLM: 抱歉，处理你的问题时出错了：{str(e)}\n")
    
    except Exception as e:
        logger.error(f"程序启动失败：{str(e)}")
        print(f"❌ 程序启动失败：{str(e)}")


# ===================== 运行入口 =====================
if __name__ == "__main__":
    # 依赖安装：
    # pip install langchain langchain-core langchain-openai python-dotenv zhipuai requests
    start_chat()
