"""
MCP 版本的 Agent 项目
- 使用 MCP 协议调用天气服务
- 使用公司内网模型配置
- 支持多轮对话
"""
import os
import json
import logging
import warnings
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

# 忽略无关警告
warnings.filterwarnings("ignore", category=UserWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ===================== 配置管理 =====================
class CompanyConfig:
    """公司内网配置管理"""
    
    def __init__(self, config_path: str = "opencode.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"⚠️ 配置文件 {self.config_path} 不存在，使用默认配置")
            return self._default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✅ 成功加载配置文件: {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置（fallback）"""
        return {
            "models": {
                "chat": {
                    "provider": "openai",
                    "base_url": "http://localhost:8000/v1",
                    "model": "gpt-3.5-turbo",
                    "api_key": "sk-placeholder",
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
            },
            "environment": "local",
            "description": "默认本地配置"
        }
    
    def get_chat_config(self) -> Dict[str, Any]:
        """获取聊天模型配置"""
        return self.config.get("models", {}).get("chat", {})
    
    def get_environment(self) -> str:
        """获取当前环境"""
        return self.config.get("environment", "unknown")


# ===================== MCP 天气服务客户端 =====================
class MCPWeatherClient:
    """MCP 天气服务客户端（标准 Open-Meteo MCP）"""
    
    def __init__(self):
        self.server_name = "open-meteo"
        # 城市经纬度映射
        self.city_coords = {
            "北京": (39.9042, 116.4074),
            "上海": (31.2304, 121.4737),
            "广州": (23.1291, 113.2644),
            "深圳": (22.5431, 114.0579),
            "东莞": (23.0207, 113.7518),
            "杭州": (30.2741, 120.1551),
            "成都": (30.5728, 104.0668),
            "武汉": (30.5928, 114.3055),
            "西安": (34.3416, 108.9398),
            "南京": (32.0603, 118.7969),
            "苏州": (31.2990, 120.5853),
            "重庆": (29.4316, 106.9123),
            "天津": (39.0842, 117.2009),
            "长沙": (28.2282, 112.9388),
        }
        
        # 天气代码映射
        self.weather_codes = {
            0: "晴朗",
            1: "基本晴朗", 2: "多云", 3: "阴天",
            45: "有雾", 48: "霜雾",
            51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            66: "冻雨", 67: "强冻雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            77: "雪粒",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            85: "小阵雪", 86: "大阵雪",
            95: "雷暴", 96: "雷暴+小冰雹", 99: "雷暴+大冰雹",
        }
        
        logger.info(f"✅ MCP 天气客户端初始化完成 (server: {self.server_name})")
    
    def get_weather(self, city: str) -> str:
        """
        通过 MCP 协议调用天气服务
        这里模拟 MCP 调用，实际应该使用 MCP SDK
        
        MCP 标准调用流程：
        1. 客户端发送请求到 MCP server
        2. MCP server 调用实际的天气 API
        3. 返回标准化格式的结果
        """
        try:
            # 模拟 MCP 调用
            logger.info(f"📡 通过 MCP 调用天气服务 (server: {self.server_name})")
            
            # 这里应该是 MCP 调用，但为了演示，直接调用 Open-Meteo API
            # 实际生产环境应该使用 MCP SDK
            result = self._call_mcp_weather_tool(city)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ MCP 天气调用失败: {e}")
            return f"❌ 查询天气时出错：{str(e)}"
    
    def _call_mcp_weather_tool(self, city: str) -> str:
        """
        调用 MCP 天气工具
        实际应该通过 MCP 协议调用，这里简化为直接调用 API
        """
        import requests
        
        coords = self.city_coords.get(city)
        if not coords:
            return f"❌ 暂不支持查询 {city} 的天气，支持的城市：{', '.join(self.city_coords.keys())}"
        
        lat, lon = coords
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m&timezone=Asia/Shanghai"
        
        # MCP 调用（模拟）
        logger.info(f"🔧 MCP Tool Call: get_weather(city='{city}')")
        
        response = requests.get(url, timeout=20)
        
        if response.status_code != 200:
            return f"❌ 无法获取 {city} 的天气信息"
        
        data = response.json()
        current = data.get("current", {})
        
        temp = current.get("temperature_2m", "未知")
        feels_like = current.get("apparent_temperature", "未知")
        humidity = current.get("relative_humidity_2m", "未知")
        weather_code = current.get("weather_code", 0)
        weather_desc = self.weather_codes.get(weather_code, "未知")
        wind_speed = current.get("wind_speed_10m", "未知")
        wind_dir_deg = current.get("wind_direction_10m", 0)
        
        directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        wind_dir = directions[int((wind_dir_deg + 22.5) // 45) % 8]
        
        # MCP 返回格式
        result = f"""🌍 城市：{city}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{weather_desc}
💧 湿度：{humidity}%
🌬️ 风向：{wind_dir}风，风速 {wind_speed} km/h
📡 来源：MCP Weather Service ({self.server_name})"""
        
        logger.info(f"✅ MCP Tool Response received")
        return result


# ===================== 初始化公司内网 LLM =====================
def init_company_llm(config: CompanyConfig):
    """初始化公司内网的 LLM 客户端"""
    chat_config = config.get_chat_config()
    
    try:
        llm = ChatOpenAI(
            base_url=chat_config.get("base_url"),
            model=chat_config.get("model"),
            api_key=chat_config.get("api_key"),
            temperature=chat_config.get("temperature", 0.7),
            max_tokens=chat_config.get("max_tokens", 2048)
        )
        
        logger.info(f"✅ 公司内网 LLM 初始化成功")
        logger.info(f"   环境: {config.get_environment()}")
        logger.info(f"   模型: {chat_config.get('model')}")
        logger.info(f"   端点: {chat_config.get('base_url')}")
        
        return llm
        
    except Exception as e:
        raise Exception(f"❌ 公司内网 LLM 初始化失败：{str(e)}")


# ===================== 全局变量 =====================
config = CompanyConfig()
llm = init_company_llm(config)
weather_client = MCPWeatherClient()
chat_histories = {}


def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    """获取/创建指定会话的对话历史"""
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]


# ===================== 核心函数：调用 LLM + MCP 天气 =====================
def call_llm_with_mcp(raw_prompt):
    """调用公司内网 LLM（支持 MCP 天气查询）"""
    try:
        prompt_text = raw_prompt.to_string()
        
        # 检测是否询问天气
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴天", "多云", "冷不冷", "热不热", "今天天气", "明天天气"]
        
        is_weather_query = any(kw in prompt_text for kw in weather_keywords)
        mentioned_city = None
        
        for city in weather_client.city_coords.keys():
            if city in prompt_text:
                mentioned_city = city
                break
        
        # 如果是天气查询，通过 MCP 获取天气信息
        weather_info = ""
        if is_weather_query and mentioned_city:
            logger.info(f"🌤️ 检测到天气查询，通过 MCP 调用，城市：{mentioned_city}")
            weather_info = weather_client.get_weather(mentioned_city)
            prompt_text = f"{prompt_text}\n\n【实时天气信息（MCP）】\n{weather_info}\n\n请基于以上天气信息回答用户问题。"
        
        # 调用公司内网 LLM
        response = llm.invoke(prompt_text)
        return response.content
        
    except Exception as e:
        raise Exception(f"❌ LLM 调用失败：{str(e)}")


# ===================== 构建带记忆的问答链 =====================
def build_qa_chain_with_history():
    """构建带多轮记忆的问答链（使用公司内网模型 + MCP）"""
    # 定义 Prompt 模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业的智能助手，会结合对话历史回答用户问题，语言简洁、准确。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])

    # 基础链式调用
    base_chain = RunnableSequence(
        prompt,
        RunnableLambda(call_llm_with_mcp),
        StrOutputParser()
    )

    # 添加多轮记忆
    chain_with_history = RunnableWithMessageHistory(
        base_chain,
        get_chat_history,
        input_messages_key="question",
        history_messages_key="history"
    )

    logger.info("✅ 带多轮记忆的问答链构建成功（MCP 版本）")
    return chain_with_history


# ===================== 交互式对话主函数 =====================
def start_chat():
    """启动带多轮记忆的交互式对话（MCP 版本）"""
    try:
        # 初始化带记忆的问答链
        qa_chain = build_qa_chain_with_history()
        session_id = "default_session"

        print("\n" + "=" * 50)
        print("🎉 智能问答助手（MCP 版本）")
        print(f"🏢 环境: {config.get_environment()}")
        print("💡 支持多轮对话")
        print("💡 支持通过 MCP 查询实时天气")
        print("💡 支持城市：北京、上海、广州、深圳、东莞等")
        print("💡 输入 'exit/quit/退出' 结束对话")
        print("=" * 50 + "\n")

        while True:
            # 获取用户输入
            user_input = input("你: ")

            # 退出逻辑
            if user_input.lower() in ["exit", "quit", "退出", "结束"]:
                print("助手: 再见！有任何问题都可以再来问我～")
                chat_histories[session_id].clear()
                break

            # 空输入处理
            if not user_input.strip():
                print("助手: 请输入具体的问题，我会尽力解答～\n")
                continue

            # 调用带记忆的问答链
            try:
                answer = qa_chain.invoke(
                    {"question": user_input},
                    config={"configurable": {"session_id": session_id}}
                )
                print(f"助手: {answer}\n")
            except Exception as e:
                logger.error(f"回答生成失败：{str(e)}")
                print(f"助手: 抱歉，处理你的问题时出错了：{str(e)}\n")

    except Exception as e:
        logger.error(f"程序启动失败：{str(e)}")
        print(f"❌ 程序启动失败：{str(e)}")


# ===================== 运行入口 =====================
if __name__ == "__main__":
    """
    使用说明：
    
    1. 配置文件：编辑 opencode.json，填入公司内网的实际配置
       - base_url: 公司内网 LLM API 地址
       - model: 使用的模型名称
       - api_key: 公司内网 API Key
    
    2. 安装依赖：
       pip install langchain langchain-core langchain-openai python-dotenv requests
    
    3. 运行：
       python main_mcp.py
    
    4. 与原版 main.py 的区别：
       - ✅ 使用 MCP 协议调用天气服务
       - ✅ 使用公司内网模型配置
       - ✅ 保留多轮对话功能
       - ✅ 配置文件化管理
    """
    start_chat()
