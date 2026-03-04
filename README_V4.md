# Agent Project V4 - LangGraph 版本

基于 LangGraph 的智能助手，提供强大的图编排能力和状态管理。

## 🎯 V4 版本特点

### 与其他版本的对比

| 特性 | V2 | V3 (Agent) | V4 (LangGraph) |
|------|----|-----------|----------------|
| 架构 | 模块化 | Agent | 图结构 ⭐ |
| 状态管理 | 简单 | 简单 | 强大 ⭐ |
| 流程控制 | 硬编码 | Agent 决定 | 图路由 ⭐ |
| 可视化 | ❌ | ❌ | ✅ ⭐ |
| 状态持久化 | ❌ | ❌ | ✅ ⭐ |
| 节点复用 | ❌ | ❌ | ✅ ⭐ |
| 条件分支 | ❌ | ❌ | ✅ ⭐ |
| 循环支持 | ❌ | ❌ | ✅ ⭐ |

### 核心优势

1. **图结构编排** - 清晰的工作流可视化
2. **状态管理** - 内置 checkpointer 持久化
3. **条件路由** - 灵活的流程控制
4. **节点复用** - 构建复杂的处理流程
5. **循环支持** - 支持迭代和反馈循环

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_v4.txt
```

### 2. 配置

编辑 `config/opencode.json`：

```json
{
  "llm": {
    "default": "company_gpt4",
    "clients": {
      "company_gpt4": {
        "provider": "openai",
        "base_url": "http://your-company-llm.internal:8000/v1",
        "model": "gpt-4",
        "api_key": "${COMPANY_API_KEY}"
      }
    }
  }
}
```

### 3. 运行

```bash
python main_v4.py
```

## 📊 架构说明

### 工作流图

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌─────────┐
│  Agent  │ ← 调用 LLM
└────┬────┘
     │
     ▼
┌─────────┐
│Should   │ ← 判断是否需要工具
│Continue?│
└────┬────┘
     │
   ┌─┴─┐
   │   │
 Yes  No
   │   │
   ▼   ▼
┌────┐ ┌─────┐
│Tool│ │ END │
└─┬──┘ └─────┘
  │
  └──────┐
         ▼
    ┌─────────┐
    │  Agent  │ ← 继续处理
    └─────────┘
```

### 核心组件

#### 1. **State（状态）**

```python
class AgentState(TypedDict):
    messages: Sequence[BaseMessage]  # 对话历史
    should_continue: bool            # 是否继续
```

#### 2. **Nodes（节点）**

```python
# Agent 节点
def call_model(state: AgentState) -> AgentState:
    # 调用 LLM
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

# Tool 节点
def call_tool(state: AgentState) -> AgentState:
    # 执行工具
    tool_messages = tool_executor.invoke(tool_calls)
    return {"messages": state["messages"] + tool_messages}
```

#### 3. **Edges（边）**

```python
# 条件边
workflow.add_conditional_edges(
    "agent",
    should_continue,  # 判断函数
    {
        "continue": "action",  # 继续 → 执行工具
        "end": END             # 结束
    }
)

# 普通边
workflow.add_edge("action", "agent")  # 工具执行完 → 回到 Agent
```

## 🔧 高级用法

### 1. 添加更多节点

```python
def analyze_intent(state: AgentState) -> AgentState:
    """分析用户意图"""
    # 你的逻辑
    return state

def generate_response(state: AgentState) -> AgentState:
    """生成响应"""
    # 你的逻辑
    return state

# 添加到图中
workflow.add_node("analyze", analyze_intent)
workflow.add_node("generate", generate_response)

# 设置流程
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "agent")
workflow.add_edge("agent", "generate")
```

### 2. 复杂条件路由

```python
def route_by_intent(state: AgentState) -> str:
    """根据意图路由"""
    last_message = state["messages"][-1]
    
    if "天气" in last_message.content:
        return "weather"
    elif "搜索" in last_message.content:
        return "search"
    else:
        return "general"

workflow.add_conditional_edges(
    "analyze",
    route_by_intent,
    {
        "weather": "weather_tool",
        "search": "search_tool",
        "general": "agent"
    }
)
```

### 3. 状态持久化

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# SQLite 持久化
checkpointer = SqliteSaver.from_conn_string("chat_history.db")
app = workflow.compile(checkpointer=checkpointer)

# 恢复会话
thread = {"configurable": {"thread_id": "user_123"}}
state = app.get_state(thread)
```

### 4. 流式输出

```python
# 流式执行
for output in app.stream(inputs, config=thread):
    for node_name, node_output in output.items():
        print(f"Node {node_name}: {node_output}")
```

## 📝 使用示例

### 示例 1：简单对话

```
你: 你好
助手: 你好！我是智能助手，有什么可以帮你的吗？
```

### 示例 2：工具调用

```
你: 北京天气怎么样？

[执行流程]
1. Agent 节点：LLM 决定调用 weather 工具
2. ShouldContinue：返回 "continue"
3. Action 节点：执行 weather 工具
4. Agent 节点：LLM 基于工具结果生成回答

助手: 🌍 城市：北京
🌡️ 温度：15°C
☁️ 天气：晴朗
```

### 示例 3：多轮对话

```
你: 我在上海
助手: 好的，我知道你在上海了。

你: 那边天气怎么样？
助手: [LLM 从上下文知道是上海]
🌍 城市：上海
🌡️ 温度：18°C...
```

## 🎨 可视化

### 生成图结构

```python
from langgraph.graph import StateGraph

# 编译图
app = workflow.compile()

# 获取图结构
print(app.get_graph().draw_ascii())

# 输出：
#   ┌─────────┐
#   │  Start  │
#   └────┬────┘
#        │
#   ┌────▼────┐
#   │  Agent  │
#   └────┬────┘
#        │
#   ...
```

## 🔄 工作流程详解

### 完整执行流程

```
用户输入
    ↓
[Agent 节点]
    ├─ 调用 LLM
    ├─ LLM 决定是否使用工具
    └─ 返回响应
    ↓
[ShouldContinue 节点]
    ├─ 检查是否有工具调用
    ├─ Yes → [Action 节点]
    └─ No → [END]
    ↓
[Action 节点]
    ├─ 执行工具
    ├─ 获取工具结果
    └─ 返回 [Agent 节点]
    ↓
[Agent 节点]
    ├─ 基于工具结果生成回答
    └─ 返回最终响应
    ↓
[END]
```

## 🆚 版本选择指南

### 何时使用 V2？

- ✅ 简单的模块化需求
- ✅ 不需要复杂流程
- ✅ 快速原型开发

### 何时使用 V3 (Agent)？

- ✅ 需要智能工具调用
- ✅ 不需要复杂流程控制
- ✅ 简单的对话场景

### 何时使用 V4 (LangGraph)？ ⭐

- ✅ 需要复杂的工作流
- ✅ 需要状态持久化
- ✅ 需要条件分支和循环
- ✅ 需要可视化流程
- ✅ 生产级应用

## 📚 扩展指南

### 添加新工具

```python
@tool
def search_web(query: str) -> str:
    """搜索互联网"""
    # 实现搜索逻辑
    return search_result

# 添加到工具列表
tools = [get_weather, search_web]
```

### 添加新节点

```python
def summarize_history(state: AgentState) -> AgentState:
    """总结对话历史"""
    # 实现总结逻辑
    return state

# 添加到图中
workflow.add_node("summarize", summarize_history)
workflow.add_edge("agent", "summarize")
```

### 自定义 Checkpointer

```python
from langgraph.checkpoint.memory import MemorySaver

# 内存持久化（适合测试）
checkpointer = MemorySaver()

# 或自定义持久化
class CustomCheckpointer:
    def save(self, state):
        # 保存到数据库
        pass
    
    def load(self, thread_id):
        # 从数据库加载
        pass
```

## 🐛 故障排查

### 问题 1：图编译失败

**原因：** 节点或边配置错误

**解决：**
```python
# 检查图结构
print(app.get_graph().draw_ascii())

# 确保所有节点都已添加
assert "agent" in workflow.nodes
```

### 问题 2：状态丢失

**原因：** 没有使用 checkpointer

**解决：**
```python
# 使用 SQLite 持久化
checkpointer = SqliteSaver.from_conn_string("chat.db")
app = workflow.compile(checkpointer=checkpointer)
```

### 问题 3：工具未执行

**原因：** LLM 没有正确绑定工具

**解决：**
```python
# 确保工具已绑定
llm_with_tools = llm.bind_tools(tools)
```

## 📖 相关资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph 示例](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [状态管理指南](https://langchain-ai.github.io/langgraph/how-tos/state/)
- [图可视化](https://langchain-ai.github.io/langgraph/how-tos/visualization/)

## 🎯 总结

**V4 优势：**
- 🎨 清晰的图结构可视化
- 💾 强大的状态管理
- 🔀 灵活的条件路由
- 🔄 支持循环和反馈
- 📈 生产级可靠性

**适用场景：**
- 复杂的多步骤工作流
- 需要状态持久化的应用
- 需要可视化流程的系统
- 企业级 Agent 应用

---

**推荐使用 V4 版本构建生产级应用！** ⭐
