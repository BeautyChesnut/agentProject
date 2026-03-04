# Agent Project V3 - Tools 版本

使用 LangChain Tools 机制的智能助手，LLM 自动决定何时调用工具。

## 🎯 V3 版本特点

### 与 V2 的区别

| 特性 | V2 版本 | V3 版本 |
|------|---------|---------|
| 工具调用方式 | 硬编码检测关键词 | LLM 自动决定 ⭐ |
| 扩展性 | 需要修改代码 | 只需注册工具 ⭐ |
| 智能程度 | 中等 | 高 ⭐ |
| 灵活性 | 低 | 高 ⭐ |
| 多工具组合 | 不支持 | 支持 ⭐ |

### 核心优势

1. **更智能** - LLM 根据上下文自动决定何时调用工具
2. **更灵活** - 无需硬编码关键词检测逻辑
3. **易扩展** - 添加新工具只需注册到列表
4. **支持组合** - 可以在一个请求中调用多个工具

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_v3.txt
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
python main_v3.py
```

## 🔧 工具调用机制

### V2 版本（硬编码）

```python
# 在代码中检测关键词
if "天气" in user_input:
    weather_info = get_weather(city)
```

**问题：**
- ❌ 需要硬编码所有关键词
- ❌ 无法理解复杂表达
- ❌ 扩展困难

### V3 版本（Tools 机制）

```python
# LLM 自己决定
tools = [WeatherTool()]
agent = create_tool_calling_agent(llm, tools, prompt)

# 用户输入可以是任何表达方式
user_input = "我想知道北京适不适合出门"
# LLM 自动决定调用 weather 工具
```

**优势：**
- ✅ LLM 理解语义
- ✅ 支持各种表达方式
- ✅ 自动处理上下文

## 📝 使用示例

### 示例 1：直接查询

```
你: 北京今天天气怎么样？
助手: [调用 weather 工具]
🌍 城市：北京
🌡️ 温度：15°C（体感 13°C）
☁️ 天气：晴朗
💧 湿度：45%
🌬️ 风向：北风，风速 12 km/h
```

### 示例 2：间接表达

```
你: 我在上海，今天适合出去跑步吗？
助手: [LLM 理解意图，自动调用 weather 工具]
让我先看看上海今天的天气情况...

[调用 weather 工具]
🌍 城市：上海
🌡️ 温度：18°C...

根据天气情况，今天很适合户外跑步！
```

### 示例 3：多轮对话

```
你: 我想去广州旅游
助手: 好的，广州是个不错的选择！

你: 那边天气怎么样？
助手: [LLM 根据上下文知道是广州]
[调用 weather 工具查询广州天气]
```

## 🛠️ 添加新工具

### 步骤 1：创建工具类

```python
# mcp/search_tool.py
from langchain_core.tools import BaseTool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")

class SearchTool(BaseTool):
    name = "search"
    description = "在互联网上搜索信息"
    args_schema = SearchInput
    
    def _run(self, query: str) -> str:
        # 实现搜索逻辑
        return search_result
```

### 步骤 2：注册工具

```python
# main_v3.py
from mcp.search_tool import SearchTool

tools = [
    WeatherTool(),
    SearchTool()  # 添加新工具
]
```

就这样！LLM 会自动学会何时使用新工具。

## 🎨 工具组合示例

```python
# 用户：帮我查一下北京的天气，并搜索一下北京有什么好玩的景点
# LLM 会自动：
# 1. 调用 weather 工具查询天气
# 2. 调用 search 工具搜索景点
# 3. 综合两个结果返回
```

## 📊 架构对比

### V2 架构（关键词检测）

```
用户输入
    ↓
检测关键词（硬编码）
    ↓
if "天气" in input:
    调用天气函数
    ↓
LLM 生成回答
```

### V3 架构（Agent + Tools）

```
用户输入
    ↓
LLM 分析
    ↓
决定：需要调用工具？
    ↓
    ├─ 是 → 调用工具 → 获取结果
    └─ 否 → 直接回答
    ↓
LLM 综合生成回答
```

## 🔍 工具定义详解

### WeatherTool 结构

```python
class WeatherTool(BaseTool):
    # 工具名称
    name: str = "weather"
    
    # 工具描述（LLM 会根据这个决定何时使用）
    description: str = "查询指定城市的实时天气信息..."
    
    # 输入参数 Schema
    args_schema: Type[BaseModel] = WeatherInput
    
    # 执行逻辑
    def _run(self, city: str) -> str:
        # 实现天气查询
        return weather_info
```

### WeatherInput 验证

```python
class WeatherInput(BaseModel):
    city: str = Field(description="城市名称")
    
    # Pydantic 会自动验证参数
    # 如果缺少 city 或类型错误，会返回错误
```

## ⚙️ 高级配置

### 调整 Agent 行为

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,              # 显示思考过程
    handle_parsing_errors=True, # 处理解析错误
    max_iterations=5,          # 最大迭代次数
    max_execution_time=30,     # 最大执行时间（秒）
    early_stopping_method="generate"  # 早停策略
)
```

### 自定义提示词

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的助手。
    
    你有以下工具可以使用：
    - weather: 查询天气
    
    使用工具时请遵循以下原则：
    1. 仔细理解用户意图
    2. 选择合适的工具
    3. 综合工具结果给出回答
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
```

## 🐛 故障排查

### 问题 1：工具未被调用

**原因：** 工具描述不够清晰

**解决：** 优化 `description`

```python
description = "查询指定城市的实时天气信息。当用户询问天气、气温、下雨等情况时使用此工具。"
```

### 问题 2：参数错误

**原因：** LLM 传递的参数不符合 Schema

**解决：** 添加默认值和验证

```python
class WeatherInput(BaseModel):
    city: str = Field(
        description="城市名称",
        default="北京",  # 默认值
        examples=["北京", "上海", "广州"]
    )
```

### 问题 3：工具调用循环

**原因：** 工具返回格式不当，LLM 重复调用

**解决：** 限制迭代次数

```python
agent_executor = AgentExecutor(
    ...,
    max_iterations=3
)
```

## 📈 性能优化

### 1. 使用异步

```python
async def _arun(self, city: str) -> str:
    # 异步实现
    result = await async_weather_api(city)
    return result
```

### 2. 添加缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def _run(self, city: str) -> str:
    # 相同城市返回缓存结果
    return weather_info
```

### 3. 流式输出

```python
# 使用流式 Agent
async for chunk in agent_executor.astream({"input": user_input}):
    print(chunk, end="", flush=True)
```

## 🔄 迁移指南

### 从 V2 迁移到 V3

1. **更新依赖**
   ```bash
   pip install -r requirements_v3.txt
   ```

2. **替换工具实现**
   - V2: `mcp/weather_tool.py`
   - V3: `mcp/weather_tool_v2.py`

3. **修改入口文件**
   - V2: `main_v2.py`
   - V3: `main_v3.py`

4. **删除硬编码逻辑**
   - 移除关键词检测代码
   - 移除手动工具调用

## 📚 相关文档

- [LangChain Tools 文档](https://python.langchain.com/docs/modules/tools/)
- [Agent 文档](https://python.langchain.com/docs/modules/agents/)
- [Pydantic 文档](https://docs.pydantic.dev/)

## 🎯 总结

**V3 版本优势：**
- 🤖 LLM 驱动的智能工具调用
- 🔧 易于扩展新工具
- 🧠 理解复杂语义
- 🔄 支持工具组合
- 📈 更好的用户体验

**适用场景：**
- 需要灵活工具调用的应用
- 复杂的对话场景
- 多工具协作
- 企业级 Agent 应用

---

**推荐使用 V3 版本获得最佳的智能化体验！** ⭐
