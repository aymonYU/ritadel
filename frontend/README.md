# Frontend - Ritadel Web UI

这是 Ritadel 项目的前端部分，使用 Next.js 构建的 Web 用户界面。

## 技术栈

- **框架**: Next.js 13+
- **语言**: TypeScript/JavaScript
- **样式**: CSS/Tailwind CSS
- **构建工具**: SWC

## 项目结构

```
frontend/
├── src/                 # 源代码
├── public/             # 静态资源
├── next.config.js      # Next.js 配置
├── package.json        # 依赖管理
└── README.md          # 项目说明
```

## 开发环境设置

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 启动生产服务器

```bash
npm start
```

## 配置说明

- `next.config.js` - Next.js 配置文件
- `env.example` - 环境变量示例文件

## 开发指南

1. 在开发前请先阅读项目的整体 README
2. 前端代码应该与后端 API 进行通信
3. 确保代码遵循项目的编码规范

## 注意事项

- 确保后端服务已启动并运行在正确端口
- 检查环境变量配置是否正确
- 开发时建议开启热重载功能

上传命令： tcb hosting deploy ./frontend/out -e