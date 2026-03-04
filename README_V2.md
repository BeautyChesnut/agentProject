# Agent Project V2 - 模块化架构

基于 LangChain 的智能助手项目，采用模块化设计，支持 LLM 客户端和 MCP 工具的灵活扩展。

## 🎯 核心特性

### 1. 模块化架构
- 📦 **配置模块** (`config/`) - 统一配置管理
- 🤖 **LLM 模块** (`llm/`) - 多客户端支持，易于扩展
- 🔧 **MCP 模块** (`mcp/`) - 工具管理，支持多工具
- 💬 **核心模块** (`core/`) - 对话链和记忆管理

### 2. LLM 客户端扩展
- ✅ 支持 OpenAI 兼容接口（公司内网）
- ✅ 支持智谱 GLM
- ✅ 易于添加新的 LLM 提供商
- ✅ 通过配置文件切换模型

### 3. MCP 工具扩展
- ✅ 支持天气查询（Open-Meteo MCP）
- ✅ 工具注册和管理
- ✅ 工具 Schema 定义
- ✅ 易于添加新工具

### 4. 统一配置
- 📄 所有配置集中在 `opencode.json`
- 🔐 支持环境变量替换
- ⚙️ 运行时配置加载
- 🔄 配置热重载

## 📁 项目结构

```
agentProject/
├── config/                     # 配置模块
│   ├── __init__.py
│   ├── config_manager.py      # 配置管理器
│   └── opencode.json          # 统一配置文件
│
├── llm/                        # LLM 模块
│   ├── __init__.py
│   ├── base.py                # LLM 基类
│   ├── openai_client.py       # OpenAI 客户端
│   ├── zhipu_client.py        # 智谱客户端
│   └── factory.py             # LLM 工厂
│
├── mcp/                        # MCP 工具模块
│   ├── __init__.py
│   ├── base.py                # 工具基类
│   ├── weather_tool.py        # 天气工具
│   └── tool_manager.py        # 工具管理器
│
├── core/                       # 核心模块
│   ├── __init__.py
│   ├── memory.py              # 对话记忆
│   └── chat_chain.py          # 对话链
│
├── main.py                     # 原版入口
├── main_mcp.py                # MCP 版本入口
├── main_v2.py                 # 模块化版本入口 ⭐
├── requirements.txt           # 原版依赖
├── requirements_mcp.txt       # MCP 版本依赖
├── requirements_v2.txt        # V2 依赖
├── README_MCP.md              # MCP 文档
└── README_V2.md               # 本文档
```

## 🚀 快速开始

### 1. 配置

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
  },
  "mcp": {
    "tools": {
      "weather": {
        "enabled": true,
        "provider": "open-meteo"
      }
    }
  }
}
```

### 2. 设置环境变量

```bash
export COMPANY_API_KEY=your-api-key
# 或
export GLM_API_KEY=your-glm-key
```

### 3. 安装依赖

```bash
pip install -r requirements_v2.txt
```

### 4. 运行

```bash
python main_v2.py
```

## 🔧 扩展指南

### 添加新的 LLM 客户端

1. **创建客户端类**

```python
# llm/custom_client.py
from llm.base import BaseLLMClient

class CustomClient(BaseLLMClient):
    def __init__(self, config):
        super().__init__(config)
        # 初始化你的客户端
    
    def invoke(self, prompt: str, **kwargs) -> str:
        # 实现调用逻辑
        return response
    
    def test_connection(self) -> bool:
        # 实现连接测试
        return True
```

2. **注册到工厂**

```python
# llm/factory.py
from llm.custom_client import CustomClient

LLMFactory.register_client("custom", CustomClient)
```

3. **添加配置**

```json
{
  "llm": {
    "clients": {
      "my_custom": {
        "provider": "custom",
        "model": "custom-model",
        "api_key": "your-key"
      }
    }
  }
}
```

### 添加新的 MCP 工具

1. **创建工具类**

```python
# mcp/search_tool.py
from mcp.base import BaseMCPTool

class SearchTool(BaseMCPTool):
    def execute(self, query: str, **kwargs) -> str:
        # 实现搜索逻辑
        return result
    
    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": "搜索工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
```

2. **注册工具**

```python
# mcp/tool_manager.py
tool_manager.register_tool_class("search", SearchTool)
```

3. **添加配置**

```json
{
  "mcp": {
    "tools": {
      "search": {
        "enabled": true,
        "provider": "custom",
        "config": {
          "api_key": "your-key"
        }
      }
    }
  }
}
```

## 📊 配置说明

### opencode.json 结构

```json
{
  "version": "2.0",
  "environment": "company",
  
  "llm": {
    "default": "client_name",
    "clients": {
      "client_name": {
        "provider": "openai",
        "base_url": "url",
        "model": "model-name",
        "api_key": "${ENV_VAR}",
        "temperature": 0.7,
        "max_tokens": 2048
      }
    }
  },
  
  "mcp": {
    "enabled": true,
    "tools": {
      "tool_name": {
        "enabled": true,
        "provider": "provider-name",
        "config": {}
      }
    }
  },
  
  "chat": {
    "session": {
      "max_history": 50,
      "timeout": 60
    },
    "prompt": {
      "system": "System prompt",
      "temperature": 0.7
    }
  }
}
```

## 🎨 架构优势

### 1. 松耦合设计
- 模块独立，职责单一
- 通过接口通信
- 易于测试和维护

### 2. 高扩展性
- 新增 LLM：继承 BaseLLMClient
- 新增工具：继承 BaseMCPTool
- 配置驱动，无需修改代码

### 3. 统一管理
- 配置集中管理
- 环境变量支持
- 运行时加载

### 4. 易于维护
- 清晰的模块划分
- 完整的类型注解
- 详细的日志记录

## 🔄 版本对比

| 特性 | V1 (main.py) | V1-MCP (main_mcp.py) | V2 (main_v2.py) |
|------|--------------|----------------------|-----------------|
| 架构 | 单文件 | 单文件 | 模块化 ⭐ |
| LLM 扩展 | ❌ | ❌ | ✅ |
| 工具扩展 | ❌ | ✅ | ✅ |
| 配置管理 | .env | JSON | 统一 JSON ⭐ |
| 代码复用 | ❌ | ❌ | ✅ |
| 易于测试 | ❌ | ❌ | ✅ |
| 生产就绪 | ⚠️ | ⚠️ | ✅ ⭐ |

## 📝 使用示例

### 基本对话

```
你: 你好
助手: 你好！我是智能助手，有什么可以帮你的吗？

你: 北京天气怎么样？
助手: 🌍 城市：北京
🌡️ 温度：15°C（体感 13°C）
☁️ 天气：晴朗
...
```

### 多轮对话

```
你: 我在上海
助手: 好的，我知道你在上海了。

你: 那边天气怎么样？
助手: 🌍 城市：上海
🌡️ 温度：18°C...
```

## ⚙️ 高级配置

### 环境变量

```bash
# LLM API Keys
export COMPANY_API_KEY=your-key
export GLM_API_KEY=your-glm-key

# 配置文件路径（可选）
export AGENT_CONFIG_PATH=/path/to/opencode.json

# 日志级别
export LOG_LEVEL=INFO
```

### 自定义配置

```python
from config import ConfigManager

# 自定义配置路径
config = ConfigManager("/path/to/custom_config.json")

# 运行时修改配置
config.reload()
```

## 🐛 故障排查

### 常见问题

1. **找不到配置文件**
   - 检查 `config/opencode.json` 是否存在
   - 检查环境变量 `AGENT_CONFIG_PATH`

2. **LLM 连接失败**
   - 检查 `base_url` 是否正确
   - 检查 `api_key` 是否有效
   - 查看日志获取详细错误

3. **工具未加载**
   - 检查工具的 `enabled` 是否为 `true`
   - 检查工具类是否正确注册

## 📚 相关文档

- [MCP 版本文档](README_MCP.md)
- [配置示例](config/opencode.json.example)
- [LLM 扩展指南](llm/README.md)
- [MCP 工具指南](mcp/README.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

---

**推荐使用 V2 版本获得最佳的开发体验！** ⭐
