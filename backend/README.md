# Backend - Ritadel AI Analysis Engine

这是 Ritadel 项目的后端部分，包含核心的 AI 分析引擎和 API 服务。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 API 密钥

# 3. 启动服务
python src/webui.py
```

服务器将在 http://127.0.0.1:5000 启动

## 环境变量

在 `.env` 文件中添加：

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key    # 可选
GROQ_API_KEY=your_groq_api_key              # 可选
GEMINI_API_KEY=your_gemini_api_key          # 可选
```

## 技术栈

- **语言**: Python 3.9+
- **框架**: Flask
- **依赖管理**: pip
- **AI/ML**: LangChain, OpenAI API
- **数据处理**: Pandas, NumPy

## 项目结构

```
backend/
├── src/                    # 源代码目录
│   ├── agents/             # AI 代理模块
│   ├── data/              # 数据处理模块
│   ├── graph/             # 图形分析模块
│   ├── llm/               # 大语言模型接口
│   ├── round_table/       # 圆桌讨论功能
│   ├── tools/             # 工具模块
│   ├── utils/             # 工具函数
│   ├── main.py            # 主程序入口
│   ├── webui.py           # Web API 服务
│   └── backtester.py      # 回测引擎
├── requirements.txt        # 生产依赖
├── requirements-dev.txt    # 开发依赖
└── README.md              # 项目说明
```

## 核心功能

- **多代理分析**: 基于 LangChain 的多 AI 代理系统
- **投资决策**: LLM 驱动的智能投资策略
- **回测引擎**: 历史数据回测和分析
- **数据分析**: 金融数据处理和可视化

## API 端点

- `GET /api/analysts` - 获取分析师列表
- `POST /api/analysis` - 运行股票分析
- `POST /api/backtest` - 运行历史回测

## 开发环境

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码格式化
black src/

# 类型检查
mypy src/

# 运行测试
pytest
```

## Docker 部署

```bash
# 构建镜像
docker build -t ritadel-backend .

# 运行容器
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your_api_key \
  ritadel-backend
```

## 系统要求

- Python 3.9+
- pip
- 至少一个 LLM API 密钥

## 注意事项

1. 确保已设置所需的API密钥
2. 默认使用 OpenAI GPT-4o 模型
3. 建议在虚拟环境中运行 