import os
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from zhipuai import ZhipuAI

print("✅ 导入成功")

# 初始化
glm_client = ZhipuAI(api_key=os.getenv("GLM_API_KEY"))
print("✅ GLM 客户端初始化成功")

# 对话历史
chat_histories = {}
def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]

print("✅ 历史记录函数定义成功")

# 调用 GLM
def call_glm(raw_prompt):
    print(f"📝 调用 GLM，prompt 类型: {type(raw_prompt)}")
    prompt_text = raw_prompt.to_string()
    print(f"📝 Prompt 内容: {prompt_text[:100]}...")
    
    print("🌐 正在调用 GLM API...")
    response = glm_client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=100,
        timeout=10  # 添加超时
    )
    print(f"✅ GLM API 响应成功")
    return response.choices[0].message.content

print("✅ call_glm 定义成功")

# 构建 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是友好的助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])
print("✅ Prompt 模板构建成功")

# 构建链
base_chain = RunnableSequence(
    prompt,
    RunnableLambda(call_glm)
)
print("✅ base_chain 构建成功")

chain_with_history = RunnableWithMessageHistory(
    base_chain,
    get_chat_history,
    input_messages_key="question",
    history_messages_key="history"
)
print("✅ chain_with_history 构建成功")

# 测试调用
print("\n🚀 开始测试调用...")
try:
    answer = chain_with_history.invoke(
        {"question": "你好"},
        config={"configurable": {"session_id": "test"}}
    )
    print(f"✅ 成功！响应：{answer}")
except Exception as e:
    print(f"❌ 失败：{e}")
    import traceback
    traceback.print_exc()
