# Backend - Ritadel AI Analysis Engine

这是 Ritadel 项目的后端部分，包含核心的 AI 分析引擎和 API 服务。

## 技术栈

- **语言**: Python 3.11+
- **框架**: FastAPI/Flask
- **依赖管理**: Poetry
- **AI/ML**: LangChain, OpenAI API
- **数据处理**: Pandas, NumPy

## 项目结构

```
backend/
├── src/                # 源代码目录
│   ├── agents/         # AI 代理模块
│   ├── data/          # 数据处理模块
│   ├── graph/         # 图形分析模块
│   ├── llm/           # 大语言模型接口
│   ├── round_table/   # 圆桌讨论功能
│   ├── tools/         # 工具模块
│   ├── utils/         # 工具函数
│   ├── main.py        # 主程序入口
│   ├── webui.py       # Web API 服务
│   └── backtester.py  # 回测引擎
├── pyproject.toml     # Python 项目配置
├── poetry.lock        # 依赖锁定文件
└── README.md          # 项目说明
```

## 核心功能

- **多代理分析**: 基于 LangChain 的多 AI 代理系统
- **投资决策**: LLM 驱动的智能投资策略
- **回测引擎**: 历史数据回测和分析
- **圆桌讨论**: AI 角色间的互动讨论
- **数据分析**: 金融数据处理和可视化

## 开发环境设置

### 使用 Poetry 安装依赖

```bash
# 确保在 backend 目录中
cd backend
poetry install
```

### 激活虚拟环境

```bash
poetry shell
```

### 运行后端服务

```bash
python src/webui.py
```

### 运行主程序

```bash
python src/main.py
```

### 运行回测

```bash
python src/backtester.py
```

## 环境变量配置

在项目根目录创建 `.env` 文件并配置以下变量：

```bash
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key

# 其他 API 配置
# 添加其他必要的环境变量
```

## API 接口

后端提供以下主要 API 接口：

- `/api/analysis` - 执行投资分析
- `/api/backtest` - 运行回测
- `/api/roundtable` - 圆桌讨论功能
- `/api/portfolio` - 投资组合管理

## 开发指南

1. 遵循 Python PEP 8 编码规范
2. 使用 type hints 进行类型注解
3. 编写单元测试覆盖核心功能
4. 使用 logging 模块记录日志
5. 所有 Python 代码都位于 `src/` 目录中

## 从根目录运行

如果需要从项目根目录运行命令：

```bash
# 分析命令
cd backend && poetry run python src/main.py --ticker AAPL

# 启动服务
cd backend && poetry run python src/webui.py --api
```

## 注意事项

- 确保所有 API 密钥已正确配置
- 开发时建议使用测试数据
- 生产环境需要配置适当的安全措施
- Python 源代码现在位于 `backend/src/` 目录中 