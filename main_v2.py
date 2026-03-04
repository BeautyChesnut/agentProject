"""
模块化版本的 Agent 主程序
- 支持 LLM 客户端扩展
- 支持 MCP 工具扩展
- 统一配置管理
"""
import logging
from config import config
from llm import create_llm_client
from mcp import tool_manager
from core import ChatChain

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
    logger.info("🚀 Agent 系统初始化")
    logger.info("=" * 60)
    
    # 1. 显示配置信息
    logger.info(f"📋 环境: {config.environment}")
    logger.info(f"📋 配置版本: {config.version}")
    
    # 2. 初始化 LLM 客户端
    llm_config = config.get_llm_config()
    llm_client = create_llm_client(llm_config)
    logger.info(f"✅ LLM 客户端: {llm_client}")
    
    # 3. 加载 MCP 工具
    mcp_tools = config.get_enabled_mcp_tools()
    if mcp_tools:
        tool_manager.load_tools(mcp_tools)
        logger.info(f"✅ 加载 MCP 工具: {tool_manager.list_tools()}")
    else:
        logger.warning("⚠️ 没有启用的 MCP 工具")
    
    # 4. 创建对话链
    chat_config = config.get_chat_config()
    chat_chain = ChatChain(
        llm_client=llm_client,
        tool_manager=tool_manager,
        chat_config=chat_config
    )
    logger.info("✅ 对话链创建成功")
    
    logger.info("=" * 60)
    logger.info("✅ 系统初始化完成")
    logger.info("=" * 60)
    
    return chat_chain


def start_chat(chat_chain: ChatChain):
    """启动交互式对话"""
    session_id = "default_session"
    
    print("\n" + "=" * 60)
    print("🎉 智能问答助手（模块化版本）")
    print(f"🏢 环境: {config.environment}")
    print(f"🤖 LLM: {config.get('llm.default')}")
    print(f"🔧 MCP 工具: {', '.join(tool_manager.list_tools())}")
    print("💡 支持多轮对话")
    print("💡 输入 'exit/quit/退出' 结束对话")
    print("=" * 60 + "\n")
    
    while True:
        # 获取用户输入
        user_input = input("你: ")
        
        # 退出逻辑
        if user_input.lower() in ["exit", "quit", "退出", "结束"]:
            print("助手: 再见！有任何问题都可以再来问我～")
            chat_chain.clear_history(session_id)
            break
        
        # 空输入处理
        if not user_input.strip():
            print("助手: 请输入具体的问题，我会尽力解答～\n")
            continue
        
        # 调用对话链
        try:
            answer = chat_chain.chat(user_input, session_id)
            print(f"助手: {answer}\n")
        except Exception as e:
            logger.error(f"回答生成失败：{str(e)}")
            print(f"助手: 抱歉，处理你的问题时出错了：{str(e)}\n")


def main():
    """主函数"""
    try:
        # 初始化系统
        chat_chain = initialize_system()
        
        # 启动对话
        start_chat(chat_chain)
        
    except Exception as e:
        logger.error(f"❌ 程序启动失败：{str(e)}")
        print(f"❌ 程序启动失败：{str(e)}")


if __name__ == "__main__":
    """
    使用说明：
    
    1. 配置文件：编辑 config/opencode.json
       - 配置 LLM 客户端
       - 配置 MCP 工具
    
    2. 环境变量（可选）：
       export COMPANY_API_KEY=your-company-key
       export GLM_API_KEY=your-glm-key
    
    3. 安装依赖：
       pip install -r requirements_v2.txt
    
    4. 运行：
       python main_v2.py
    
    5. 扩展性：
       - 添加新 LLM: 继承 BaseLLMClient，注册到 LLMFactory
       - 添加新工具: 继承 BaseMCPTool，注册到 ToolManager
    """
    main()
