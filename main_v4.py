"""
LangGraph 版本的 Agent
- 使用 LangGraph 构建图结构
- 状态管理和节点编排
- 支持复杂的流程控制
"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.checkpoint.sqlite import SqliteSaver
import logging
from config import config
from llm import create_llm_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ===================== 定义状态 =====================
class AgentState(TypedDict):
    """Agent 状态"""
    messages: Annotated[Sequence[BaseMessage], "对话消息列表"]
    should_continue: Annotated[bool, "是否继续执行"]


# ===================== 定义工具 =====================
@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的实时天气信息
    
    Args:
        city: 城市名称，如：北京、上海、广州等
    
    Returns:
        天气信息字符串
    """
    import requests
    
    # 城市经纬度映射
    city_coords = {
        "北京": (39.9042, 116.4074),
        "上海": (31.2304, 121.4737),
        "广州": (23.1291, 113.2644),
        "深圳": (22.5431, 114.0579),
        "东莞": (23.0207, 113.7518),
    }
    
    weather_codes = {
        0: "晴朗", 1: "基本晴朗", 2: "多云", 3: "阴天",
        45: "有雾", 61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
    }
    
    if city not in city_coords:
        return f"❌ 暂不支持查询 {city} 的天气"
    
    try:
        lat, lon = city_coords[city]
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,weather_code&"
            f"timezone=Asia/Shanghai"
        )
        
        response = requests.get(url, timeout=20)
        data = response.json()
        current = data.get("current", {})
        
        temp = current.get("temperature_2m", "未知")
        weather_code = current.get("weather_code", 0)
        weather_desc = weather_codes.get(weather_code, "未知")
        
        return f"🌍 城市：{city}\n🌡️ 温度：{temp}°C\n☁️ 天气：{weather_desc}"
    except Exception as e:
        return f"❌ 查询天气失败：{str(e)}"


# ===================== 定义节点 =====================
def should_continue(state: AgentState) -> str:
    """
    判断是否继续执行
    
    Returns:
        "continue" 或 "end"
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果最后一条消息有工具调用，继续执行
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    
    return "end"


def call_model(state: AgentState, llm_with_tools) -> AgentState:
    """
    调用 LLM 模型
    
    Args:
        state: 当前状态
        llm_with_tools: 绑定工具的 LLM
    
    Returns:
        更新后的状态
    """
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    
    logger.info(f"🤖 LLM 响应: {response.content[:100]}...")
    
    return {"messages": messages + [response]}


def call_tool(state: AgentState, tool_executor: ToolExecutor) -> AgentState:
    """
    调用工具
    
    Args:
        state: 当前状态
        tool_executor: 工具执行器
    
    Returns:
        更新后的状态
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # 获取工具调用
    tool_calls = last_message.tool_calls
    
    # 执行工具
    tool_messages = tool_executor.invoke(tool_calls)
    
    logger.info(f"🔧 执行工具: {len(tool_messages)} 个")
    
    return {"messages": messages + tool_messages}


# ===================== 构建图 =====================
def build_graph(llm_with_tools, tools):
    """
    构建 LangGraph 工作流图
    
    Args:
        llm_with_tools: 绑定工具的 LLM
        tools: 工具列表
    
    Returns:
        编译后的图
    """
    # 创建工具执行器
    tool_executor = ToolExecutor(tools)
    
    # 创建工作流图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node(
        "agent",
        lambda state: call_model(state, llm_with_tools)
    )
    workflow.add_node(
        "action",
        lambda state: call_tool(state, tool_executor)
    )
    
    # 设置入口
    workflow.set_entry_point("agent")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "action",
            "end": END
        }
    )
    
    # 添加普通边
    workflow.add_edge("action", "agent")
    
    # 编译图（带记忆）
    memory = SqliteSaver.from_conn_string(":memory:")
    app = workflow.compile(checkpointer=memory)
    
    logger.info("✅ LangGraph 工作流图构建完成")
    
    return app


# ===================== 主程序 =====================
def initialize_system():
    """初始化系统"""
    logger.info("=" * 60)
    logger.info("🚀 Agent 系统初始化（LangGraph 版本）")
    logger.info("=" * 60)
    
    # 1. 初始化 LLM
    llm_config = config.get_llm_config()
    llm_client = create_llm_client(llm_config)
    logger.info(f"✅ LLM 客户端: {llm_client}")
    
    # 2. 定义工具
    tools = [get_weather]
    logger.info(f"✅ 工具: {[t.name for t in tools]}")
    
    # 3. 绑定工具到 LLM
    llm_with_tools = llm_client.client.bind_tools(tools)
    
    # 4. 构建图
    app = build_graph(llm_with_tools, tools)
    
    logger.info("=" * 60)
    logger.info("✅ 系统初始化完成")
    logger.info("=" * 60)
    
    return app


def start_chat(app):
    """启动交互式对话"""
    session_id = "default_session"
    thread = {"configurable": {"thread_id": session_id}}
    
    print("\n" + "=" * 60)
    print("🎉 智能问答助手（LangGraph 版本）")
    print(f"🏢 环境: {config.environment}")
    print(f"🤖 LLM: {config.get('llm.default')}")
    print("🔧 工具: weather")
    print("💡 支持多轮对话")
    print("💡 基于图结构的智能流程")
    print("💡 输入 'exit/quit/退出' 结束对话")
    print("=" * 60 + "\n")
    
    while True:
        # 获取用户输入
        user_input = input("你: ")
        
        # 退出逻辑
        if user_input.lower() in ["exit", "quit", "退出", "结束"]:
            print("助手: 再见！有任何问题都可以再来问我～")
            break
        
        # 空输入处理
        if not user_input.strip():
            print("助手: 请输入具体的问题，我会尽力解答～\n")
            continue
        
        # 调用图
        try:
            # 创建输入消息
            inputs = {
                "messages": [HumanMessage(content=user_input)]
            }
            
            # 流式执行
            logger.info("🔄 开始执行工作流...")
            for output in app.stream(inputs, config=thread):
                # 输出每个节点的执行结果
                for key, value in output.items():
                    logger.info(f"📍 节点 {key}: {type(value)}")
            
            # 获取最终状态
            final_state = app.get_state(thread)
            final_message = final_state.values["messages"][-1]
            
            print(f"助手: {final_message.content}\n")
            
        except Exception as e:
            logger.error(f"回答生成失败：{str(e)}")
            print(f"助手: 抱歉，处理你的问题时出错了：{str(e)}\n")


def main():
    """主函数"""
    try:
        # 初始化系统
        app = initialize_system()
        
        # 启动对话
        start_chat(app)
        
    except Exception as e:
        logger.error(f"❌ 程序启动失败：{str(e)}")
        print(f"❌ 程序启动失败：{str(e)}")


if __name__ == "__main__":
    """
    使用说明：
    
    1. LangGraph vs V3 Agent:
       - V3: 使用 create_tool_calling_agent（简单）
       - V4: 使用 StateGraph（更灵活） ⭐
    
    2. LangGraph 优势:
       - ✅ 状态管理（内置 checkpointer）
       - ✅ 图结构可视化
       - ✅ 条件路由（更复杂的流程）
       - ✅ 节点可复用
       - ✅ 支持循环和分支
    
    3. 工作流程:
       用户输入 → agent 节点 → 判断 → action 节点 → agent 节点 → 结束
    
    4. 运行:
       pip install langgraph
       python main_v4.py
    
    5. 架构图:
       
       ┌─────────┐
       │  Start  │
       └────┬────┘
            │
       ┌────▼────┐
       │  Agent  │
       └────┬────┘
            │
       ┌────▼────┐
       │Should   │
       │Continue?│
       └────┬────┘
            │
       ┌────┴────┐
       │         │
   Yes │         │ No
       │         │
  ┌────▼──┐  ┌──▼────┐
  │Action │  │  END  │
  └───┬───┘  └───────┘
      │
  ┌───▼───┐
  │ Agent │
  └───────┘
    """
    main()
