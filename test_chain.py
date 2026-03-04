import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from zhipuai import ZhipuAI

# 初始化
glm_client = ZhipuAI(api_key=os.getenv("GLM_API_KEY"))

# 对话历史
chat_histories = {}
def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]

# 调用 GLM
def call_glm(raw_prompt):
    prompt_text = raw_prompt.to_string()
    response = glm_client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=100
    )
    return response.choices[0].message.content

# 构建 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是友好的助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# 构建链
def str_to_dict(input_str):
    return {"question": input_str.strip()}

base_chain = RunnableSequence(
    RunnableLambda(str_to_dict),
    prompt,
    RunnableLambda(call_glm)
)

chain_with_history = RunnableWithMessageHistory(
    base_chain,
    get_chat_history,
    input_messages_key="question",
    history_messages_key="history"
)

# 测试调用
print("开始测试...")
try:
    answer = chain_with_history.invoke(
        {"question": "你好"},  # 字典格式
        config={"configurable": {"session_id": "test"}}
    )
    print(f"✅ 成功！响应：{answer}")
except Exception as e:
    print(f"❌ 失败：{e}")
    import traceback
    traceback.print_exc()
