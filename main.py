import os
import logging
import warnings
import requests
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
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


# ===================== 天气查询配置 =====================
# 城市经纬度映射
CITY_COORDS = {
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
WEATHER_CODES = {
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


def get_weather(city: str) -> str:
    """查询指定城市的实时天气（使用 Open-Meteo API）"""
    try:
        coords = CITY_COORDS.get(city)
        if not coords:
            return f"❌ 暂不支持查询 {city} 的天气，支持的城市：{', '.join(CITY_COORDS.keys())}"
        
        lat, lon = coords
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m&timezone=Asia/Shanghai"
        
        # 增加超时时间
        response = requests.get(url, timeout=20)
        
        if response.status_code != 200:
            return f"❌ 无法获取 {city} 的天气信息"
        
        data = response.json()
        current = data.get("current", {})
        
        temp = current.get("temperature_2m", "未知")
        feels_like = current.get("apparent_temperature", "未知")
        humidity = current.get("relative_humidity_2m", "未知")
        weather_code = current.get("weather_code", 0)
        weather_desc = WEATHER_CODES.get(weather_code, "未知")
        wind_speed = current.get("wind_speed_10m", "未知")
        wind_dir_deg = current.get("wind_direction_10m", 0)
        
        directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        wind_dir = directions[int((wind_dir_deg + 22.5) // 45) % 8]
        
        return f"""🌍 城市：{city}
🌡️ 温度：{temp}°C（体感 {feels_like}°C）
☁️ 天气：{weather_desc}
💧 湿度：{humidity}%
🌬️ 风向：{wind_dir}风，风速 {wind_speed} km/h"""
        
    except requests.exceptions.Timeout:
        return f"❌ 查询 {city} 天气超时，请稍后重试"
    except Exception as e:
        return f"❌ 查询天气时出错：{str(e)}"


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

# ===================== 2. 全局对话记忆（多轮对话核心） =====================
# 存储对话历史（key: 会话ID，value: 对话历史对象）
chat_histories = {}


def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    """获取/创建指定会话的对话历史"""
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]


# ===================== 3. 核心函数：调用 GLM API =====================
def call_glm(raw_prompt):
    """调用 GLM API（支持天气查询）"""
    try:
        prompt_text = raw_prompt.to_string()
        
        # 检测是否询问天气
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴天", "多云", "冷不冷", "热不热", "今天天气", "明天天气"]
        
        is_weather_query = any(kw in prompt_text for kw in weather_keywords)
        mentioned_city = None
        
        for city in CITY_COORDS.keys():
            if city in prompt_text:
                mentioned_city = city
                break
        
        # 如果是天气查询，先获取天气信息
        weather_info = ""
        if is_weather_query and mentioned_city:
            logger.info(f"🌤️ 检测到天气查询，城市：{mentioned_city}")
            weather_info = get_weather(mentioned_city)
            prompt_text = f"{prompt_text}\n\n【实时天气信息】\n{weather_info}\n\n请基于以上天气信息回答用户问题。"
        
        # 调用 GLM API
        response = glm_client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"❌ GLM API 调用失败：{str(e)}")


# ===================== 4. 构建带记忆的问答链 =====================
def build_qa_chain_with_history():
    """构建带多轮记忆的问答链（无字典类型错误）"""
    # 定义 Prompt 模板（包含对话历史占位符）
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是专业的 LangChain 学习助手，会结合对话历史回答用户问题，语言简洁、准确。"),
        MessagesPlaceholder(variable_name="history"),  # 对话历史占位符
        ("human", "{question}")  # 用户当前问题
    ])

    # 基础链式调用（无记忆）- 直接接收字典输入
    base_chain = RunnableSequence(
        prompt,  # 字典→ChatPromptValue
        RunnableLambda(call_glm),  # ChatPromptValue→纯字符串→调用GLM
        StrOutputParser()  # 兜底解析
    )

    # 给基础链添加多轮记忆（关键：不使用 RunnablePassthrough.assign）
    chain_with_history = RunnableWithMessageHistory(
        base_chain,
        get_chat_history,  # 获取对话历史的函数
        input_messages_key="question",  # 输入变量名（匹配字典的key）
        history_messages_key="history"  # 历史变量名（匹配 Prompt 模板的占位符）
    )

    logger.info("✅ 带多轮记忆的问答链构建成功")
    return chain_with_history


# ===================== 5. 交互式对话主函数 =====================
def start_chat():
    """启动带多轮记忆的交互式对话"""
    try:
        # 初始化带记忆的问答链
        qa_chain = build_qa_chain_with_history()
        # 固定会话ID（简单演示，实际可按用户区分）
        session_id = "default_session"

        print("\n" + "=" * 50)
        print("🎉 GLM 智能问答助手（带天气查询功能）")
        print("💡 支持多轮对话，可查询实时天气")
        print("💡 支持城市：北京、上海、广州、深圳、东莞等")
        print("💡 输入 'exit/quit/退出' 结束对话")
        print("=" * 50 + "\n")

        while True:
            # 获取用户输入
            user_input = input("你: ")

            # 退出逻辑
            if user_input.lower() in ["exit", "quit", "退出", "结束"]:
                print("GLM: 再见！学习过程中有任何问题都可以再来问我～")
                # 清空当前会话的历史（可选）
                chat_histories[session_id].clear()
                break

            # 空输入处理
            if not user_input.strip():
                print("GLM: 请输入具体的问题，我会尽力解答～\n")
                continue

            # 调用带记忆的问答链（核心：传入会话ID，避免类型错误）
            try:
                answer = qa_chain.invoke(
                    {"question": user_input},  # ✅ 字典格式输入
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
    # 前置要求：
    # 1. .env 文件：GLM_API_KEY=你的智谱API Key（原样粘贴）
    # 2. 安装依赖：pip install langchain langchain-core python-dotenv zhipuai>=2.0.0 pyjwt sniffio
    # 3. 完成智谱实名认证（否则 API Key 无效）
    start_chat()