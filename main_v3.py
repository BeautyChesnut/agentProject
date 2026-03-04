"""
使用 LangChain Tools 的 Agent 版本
- 使用 LangChain Agent 机制
- 天气工具作为 Tool 注册
- LLM 自动决定何时调用工具
"""
import logging
from typing import List
from config import config
from llm import create_llm_client
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from mcp.weather_tool_v2 import WeatherTool

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def initialize_system():
    """初始化系统"""
    logger.info("=" * 60)
    logger.info("🚀 Agent 系统初始化（Tools 版本）")
    logger.info("=" * 60)
    
    # 1. 显示配置信息
    logger.info(f"📋 环境: {config.environment}")
    logger.info(f"📋 配置版本: {config.version}")
    
    # 2. 初始化 LLM 客户端
    llm_config = config.get_llm_config()
    llm_client = create_llm_client(llm_config)
    logger.info(f"✅ LLM 客户端: {llm_client}")
    
    # 3. 初始化工具
    tools = [WeatherTool()]
    logger.info(f"✅ 加载工具: {[tool.name for tool in tools]}")
    
    # 4. 创建 Agent
    chat_config = config.get_chat_config()
    system_prompt = chat_config.get("prompt", {}).get(
        "system",
        "你是专业的智能助手，会使用工具来帮助用户解决问题。"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm_client.client, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    logger.info("✅ Agent 创建成功")
    
    logger.info("=" * 60)
    logger.info("✅ 系统初始化完成")
    logger.info("=" * 60)
    
    return agent_executor


def start_chat(agent_executor: AgentExecutor):
    """启动交互式对话"""
    chat_history = []
    session_id = "default_session"
    
    print("\n" + "=" * 60)
    print("🎉 智能问答助手（Tools 版本）")
    print(f"🏢 环境: {config.environment}")
    print(f"🤖 LLM: {config.get('llm.default')}")
    print(f"🔧 工具: weather")
    print("💡 支持多轮对话")
    print("💡 LLM 会自动决定何时调用工具")
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
        
        # 调用 Agent
        try:
            result = agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            response = result.get("output", "抱歉，我没有理解你的问题。")
            print(f"助手: {response}\n")
            
            # 更新对话历史
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": response})
            
        except Exception as e:
            logger.error(f"回答生成失败：{str(e)}")
            print(f"助手: 抱歉，处理你的问题时出错了：{str(e)}\n")


def main():
    """主函数"""
    try:
        # 初始化系统
        agent_executor = initialize_system()
        
        # 启动对话
        start_chat(agent_executor)
        
    except Exception as e:
        logger.error(f"❌ 程序启动失败：{str(e)}")
        print(f"❌ 程序启动失败：{str(e)}")


if __name__ == "__main__":
    """
    使用说明：
    
    1. 与 V2 版本的区别：
       - V2: 代码中硬编码检测天气关键词
       - V3: LLM 自己决定何时调用工具（更智能）
    
    2. 工具调用流程：
       用户输入 → LLM 分析 → 决定是否调用工具 → 执行工具 → 返回结果
    
    3. 优势：
       - 更灵活：LLM 可以根据上下文决定
       - 可扩展：添加新工具只需注册到 tools 列表
       - 更智能：支持复杂的多工具组合
    
    4. 运行：
       python main_v3.py
    """
    main()
