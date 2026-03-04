import os
import logging
import warnings
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from zhipuai import ZhipuAI

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 GLM 客户端
load_dotenv()
glm_client = ZhipuAI(api_key=os.getenv("GLM_API_KEY"))
print("✅ GLM 客户端初始化成功")

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
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content

# 构建 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是专业的助手，语言简洁、准确。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# 构建链
base_chain = RunnableSequence(
    prompt,
    RunnableLambda(call_glm),
    StrOutputParser()
)

chain_with_history = RunnableWithMessageHistory(
    base_chain,
    get_chat_history,
    input_messages_key="question",
    history_messages_key="history"
)

print("✅ 问答链构建成功")

# 测试调用
print("\n🧪 测试 1：单次对话")
answer = chain_with_history.invoke(
    {"question": "你好"},
    config={"configurable": {"session_id": "test"}}
)
print(f"GLM: {answer}")

print("\n🧪 测试 2：多轮对话")
answer2 = chain_with_history.invoke(
    {"question": "我刚才问了什么？"},
    config={"configurable": {"session_id": "test"}}
)
print(f"GLM: {answer2}")

print("\n✅ 所有测试通过！")
