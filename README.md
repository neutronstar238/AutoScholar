# 🚀 AutoScholar

> 自主学术研究与商业化 AI Agent 系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 📖 项目简介

AutoScholar 是一个具备**自主学术研究能力**和**商业化能力**的 AI Agent 系统，能够：

- 🔍 **自主搜索学术文献** - 从 arXiv、Semantic Scholar 获取最新研究
- 📝 **自动生成研究笔记** - 理解论文内容，提取关键信息
- 💡 **提出创新研究方向** - 基于文献分析，发现研究空白
- 💰 **自主商业化** - 提供 API 服务、研究笔记生成等盈利功能
- 🤖 **多 Agent 协作** - 研究员 + 商业化 + 质量控制 Agent 协同工作
- 🌐 **多平台支持** - 原生支持飞书、企业微信、钉钉等平台

---

## ✨ 核心特性

### 1. 双模式部署

| 部署方式 | 适用场景 | 特点 |
|---------|---------|------|
| **API 模式** | 个人/小团队 | 轻量化，快速启动，支持 DeepSeek/Qwen 等 |
| **Ollama 模式** | 企业/隐私敏感 | 本地部署，数据不出域，完全私有化 |

### 2. 前后端分离

- **后端**: Python FastAPI + LangGraph + CrewAI
- **前端**: Vue 3 + TypeScript + Element Plus
- **通信**: RESTful API + WebSocket 实时推送

### 3. 多平台集成

- ✅ 飞书 (Feishu/Lark)
- ✅ 企业微信 (WeCom)
- ✅ 钉钉 (DingTalk)
- ✅ Web 控制台

### 4. 一键部署

- Docker Compose (推荐)
- Kubernetes (生产环境)
- Windows 一键安装包
- Linux 服务端脚本

---

## 🚀 快速开始

### 方式一：Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/AutoScholar.git
cd AutoScholar

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key 或配置 Ollama

# 3. 启动服务
docker-compose up -d

# 4. 访问前端
# http://localhost:3000
```

### 方式二：本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 方式三：Windows 一键安装

```powershell
# 下载并运行安装脚本
.\deploy\windows\install.ps1

# 启动服务
.\deploy\windows\start.ps1
```

---

## 📋 配置说明

### 环境变量 (.env)

```bash
# ===== 基础配置 =====
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000

# ===== 数据库配置 =====
DATABASE_URL=postgresql://autoscholar:password@localhost:5432/autoscholar
REDIS_URL=redis://localhost:6379/0

# ===== AI 模型配置 (二选一) =====

# 方案 1: API 模式 (轻量化)
DEEPSEEK_API_KEY=your_api_key_here
QWEN_API_KEY=your_api_key_here
MODEL_PROVIDER=deepseek  # deepseek | qwen | openai

# 方案 2: Ollama 模式 (本地私有化)
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# ===== 前端配置 =====
FRONTEND_URL=http://localhost:3000

# ===== 平台集成配置 =====
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_VERIFICATION_TOKEN=your_token

WECOM_CORP_ID=your_corp_id
WECOM_AGENT_SECRET=your_agent_secret

DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret

# ===== 商业化配置 =====
API_KEY_SECRET=your_secret_key_for_api_auth
STRIPE_SECRET_KEY=your_stripe_key  # 可选，用于支付
```

---

## 📚 功能文档

### 1. 文献检索

```bash
# API 调用示例
curl -X POST http://localhost:8000/api/v1/literature/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI Agent autonomous decision making",
    "limit": 10,
    "year_from": 2024
  }'
```

### 2. 研究笔记生成

```bash
curl -X POST http://localhost:8000/api/v1/notes/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "paper_url": "https://arxiv.org/abs/2401.12345",
    "language": "zh-CN"
  }'
```

### 3. 创新方向推荐

```bash
curl -X POST http://localhost:8000/api/v1/research/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "field": "AI Agent",
    "keywords": ["autonomous", "decision making", "multi-agent"]
  }'
```

详细 API 文档请查看：[docs/api.md](docs/api.md)

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                      │
│                   http://localhost:3000                  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                      │
│                  http://localhost:8000                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Researcher   │  │ Business     │  │ Critic       │  │
│  │ Agent        │  │ Agent        │  │ Agent        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └──────────────────┼──────────────────┘         │
│                   ┌────────▼────────┐                   │
│                   │ Coordinator     │                   │
│                   │ Agent           │                   │
│                   └────────┬────────┘                   │
└────────────────────────────┼────────────────────────────┘
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐ ┌────────▼────────┐ ┌───────▼───────┐
│   PostgreSQL    │ │     Redis       │ │    Ollama     │
│   (记忆存储)    │ │   (缓存/队列)   │ │  (本地模型)   │
└─────────────────┘ └─────────────────┘ └───────────────┘
```

---

## 📦 项目结构

```
AutoScholar/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── agents/         # Agent 实现
│   │   ├── memory/         # 记忆系统
│   │   ├── tools/          # 工具函数
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具类
│   ├── tests/              # 测试文件
│   ├── requirements.txt    # Python 依赖
│   └── .env.example        # 环境变量示例
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── pages/          # 页面
│   │   ├── stores/         # 状态管理
│   │   ├── utils/          # 工具函数
│   │   └── assets/         # 静态资源
│   ├── public/             # 公共资源
│   ├── package.json        # Node 依赖
│   └── vite.config.js      # Vite 配置
├── docs/                   # 文档
│   └── api.md             # API 文档
├── deploy/                 # 部署配置
│   ├── docker/            # Docker 配置
│   ├── k8s/               # Kubernetes 配置
│   └── windows/           # Windows 部署脚本
├── scripts/                # 辅助脚本
├── docker-compose.yml      # Docker Compose 配置
├── README.md              # 本文件
└── .env.example           # 环境变量模板
```

---

## 🔧 开发指南

### 添加新的 Agent

1. 在 `backend/app/agents/` 创建新的 Agent 类
2. 继承 `BaseAgent` 基类
3. 实现 `execute()` 方法
4. 在 `backend/app/main.py` 中注册

### 添加新的工具

1. 在 `backend/app/tools/` 创建工具函数
2. 使用 `@tool` 装饰器标记
3. 在 Agent 中调用

### 前端开发

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm run test
```

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 📞 联系方式

- 📧 Email: your.email@example.com
- 💬 论坛：[AstrBook](https://astrbook.com)
- 🐛 Issue: [GitHub Issues](https://github.com/YOUR_USERNAME/AutoScholar/issues)

---

## 🙏 致谢

感谢以下开源项目：

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [Ollama](https://ollama.ai/)
- [AstrBot](https://github.com/Soulter/AstrBot) - 飞书插件参考

---

*最后更新：2026-02-22*
*版本：v0.1.0-alpha*
