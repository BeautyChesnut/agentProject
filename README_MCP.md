# Agent Project - MCP 版本

基于 LangChain 的智能助手项目，支持 MCP 协议和公司内网模型。

## 📦 项目版本

### 1. 原版 (main.py)
- ✅ 使用智谱 GLM API
- ✅ 内置天气查询功能
- ✅ 多轮对话支持

### 2. MCP 版本 (main_mcp.py) ⭐ 推荐
- ✅ 使用 MCP 协议调用天气服务
- ✅ 支持公司内网模型配置
- ✅ 配置文件化管理
- ✅ 多轮对话支持

## 🚀 快速开始

### 原版使用

```bash
# 1. 配置环境变量
echo "GLM_API_KEY=your_glm_api_key" > .env

# 2. 安装依赖
pip install langchain langchain-core python-dotenv zhipuai>=2.0.0

# 3. 运行
python main.py
```

### MCP 版本使用

```bash
# 1. 编辑配置文件
# 修改 opencode.json，填入公司内网的实际配置
{
  "models": {
    "chat": {
      "base_url": "http://your-company-llm.internal:8000/v1",
      "model": "your-model-name",
      "api_key": "your-api-key"
    }
  }
}

# 2. 安装依赖
pip install -r requirements_mcp.txt

# 3. 运行
python main_mcp.py
```

## 📁 项目结构

```
agentProject/
├── main.py                 # 原版 - 智谱 GLM + 内置天气
├── main_mcp.py            # MCP 版本 - 公司内网模型 + MCP 天气
├── opencode.json          # 公司内网模型配置
├── .env                   # 原版环境变量（GLM API Key）
├── requirements.txt       # 原版依赖
├── requirements_mcp.txt   # MCP 版本依赖
├── README_MCP.md          # 本文档
└── test_*.py              # 测试文件
```

## 🔧 配置说明

### opencode.json 配置

```json
{
  "models": {
    "chat": {
      "provider": "openai",
      "base_url": "http://company-llm.internal:8000/v1",
      "model": "company-gpt-4",
      "api_key": "your-company-api-key",
      "temperature": 0.7,
      "max_tokens": 2048
    }
  },
  "mcp": {
    "weather": {
      "server": "open-meteo",
      "transport": "stdio",
      "enabled": true
    }
  },
  "environment": "company"
}
```

## 🌤️ MCP 天气服务

MCP 版本使用标准的 Open-Meteo MCP 服务器提供天气查询功能。

### 支持的城市

北京、上海、广州、深圳、东莞、杭州、成都、武汉、西安、南京、苏州、重庆、天津、长沙

### MCP 调用流程

```
用户查询天气
    ↓
检测天气关键词
    ↓
通过 MCP 协议调用天气服务
    ↓
获取实时天气数据
    ↓
返回给 LLM 生成回答
```

## ✨ 功能特性

### 共同特性
- 🔄 多轮对话支持
- 🌤️ 实时天气查询
- 📝 对话历史管理

### MCP 版本独有
- 🔌 MCP 协议支持
- 🏢 公司内网模型配置
- ⚙️ 配置文件化管理
- 🔧 易于扩展其他 MCP 服务

## 🔍 使用示例

### 天气查询

```
你: 北京今天天气怎么样？
助手: 🌍 城市：北京
🌡️ 温度：15°C（体感 13°C）
☁️ 天气：晴朗
💧 湿度：45%
🌬️ 风向：北风，风速 12 km/h
📡 来源：MCP Weather Service (open-meteo)
```

### 多轮对话

```
你: 我在上海
助手: 好的，我知道你在上海了。

你: 那边天气怎么样？
助手: 🌍 城市：上海
🌡️ 温度：18°C...
```

## ⚠️ 注意事项

### 原版 (main.py)
- 需要智谱 GLM API Key
- 需要完成智谱实名认证
- 适用于个人开发测试

### MCP 版本 (main_mcp.py)
- 需要公司内网访问权限
- 需要正确配置 opencode.json
- 适用于公司内网环境

## 🔐 安全建议

1. **不要提交敏感信息**
   - `.env` 文件已加入 `.gitignore`
   - `opencode.json` 中的 API Key 应使用占位符

2. **配置文件管理**
   - 生产环境使用环境变量
   - 开发环境使用 `.env` 文件

## 📊 版本对比

| 特性 | 原版 | MCP 版本 |
|------|------|----------|
| LLM 提供商 | 智谱 GLM | 公司内网模型 |
| 天气查询 | 内置 | MCP 协议 |
| 配置方式 | 环境变量 | JSON 配置文件 |
| 适用环境 | 个人/公网 | 公司内网 |
| 扩展性 | 中 | 高 |

## 🛠️ 开发说明

### 添加新的 MCP 服务

1. 在 `opencode.json` 中添加配置
2. 创建对应的 MCP 客户端类
3. 在 `call_llm_with_mcp` 中集成

### 切换 LLM 提供商

只需修改 `opencode.json` 配置，无需修改代码。

## 📝 更新日志

### v2.0.0 (2026-03-04)
- ✨ 新增 MCP 版本 (main_mcp.py)
- 🔌 集成 MCP 天气服务
- 🏢 支持公司内网模型配置
- 📝 添加配置文件管理

### v1.0.0
- 🎉 初始版本
- ✅ 智谱 GLM 集成
- ✅ 天气查询功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
