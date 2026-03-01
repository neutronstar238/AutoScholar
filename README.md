# AutoScholar

自主学术研究 AI Agent 系统

## ✨ 最新更新 (V1.0.5)

🎉 **代码框架已完成 Debug！**

已修复 11 个核心问题，包括：
- ✅ 前端路由集成
- ✅ API 配置
- ✅ 用户界面完善
- ✅ 数据库初始化
- ✅ 笔记生成功能

详见 [FIXES_SUMMARY.md](./FIXES_SUMMARY.md) 和 [QUICKSTART.md](./QUICKSTART.md)

## 简介
AI 驱动的学术研究助手，支持文献检索、笔记生成、方向推荐。

## 系统要求

- Python 3.10-3.13 (推荐 3.11)
  - ⚠️ Python 3.14+ 暂不支持部分依赖库（crewai, langgraph）
- Node.js 18+ (前端)
- PostgreSQL 15+ (可选，用于数据持久化)
- Redis 7+ (可选，用于缓存)

## 快速开始

### 方式一：Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/neutronstar238/AutoScholar.git
cd AutoScholar

# 2. 启动服务
docker-compose up -d

# 3. 访问
# 前端：http://localhost:3000
# 后端 API：http://localhost:8000/docs
```

### 方式二：本地完整部署 (无需 Docker)

**前置要求：Python 3.10-3.13 (推荐 3.11)**

```bash
# 1. 克隆项目
git clone https://github.com/neutronstar238/AutoScholar.git
cd AutoScholar

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少配置一个 AI 模型的 API Key

# 3. 创建虚拟环境并安装后端依赖
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt

# 4. 启动后端 (终端 1)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. 安装前端依赖 (新开终端)
cd frontend
npm install

# 6. 启动前端 (终端 2)
npm run dev

# 7. 访问
# 前端：http://localhost:5173
# 后端 API：http://localhost:8000/docs
```


## 🗺️ Kiro 规划执行进度

> 按 P 阶段逐步交付，并在每个阶段完成后更新本节。

- **P0（推荐系统修复）**：✅ 已完成（缓存基础设施、关键词扩展、搜索降级链、推荐API降级标识、缓存集成与基础测试）。
- **P1（推荐质量增强）**：⏳ 未开始。
- **P2（搜索功能增强）**：⏳ 未开始。

### P0 已交付要点
- 推荐接口在无精确结果时不再直接返回“未找到相关论文”，而是触发降级策略并返回可用建议。
- 搜索链路支持：组合查询 → 逐词查询 → 关键词扩展 → 相似缓存 → 热门主题兜底。
- 文献检索支持缓存优先读取，降低外部 API 波动带来的影响。
- 推荐响应新增 `is_fallback`、`fallback_strategy`、`fallback_rate`、`fallback_note`，便于前端展示与监控。

## 常见问题

**Python 版本不兼容**
```bash
# 检查 Python 版本
python --version

# 需要 Python 3.10-3.13 (推荐 3.11)
# Python 3.14+ 暂不支持，请安装 Python 3.11
# 下载地址：https://www.python.org/downloads/
```

**Docker 认证错误**: 使用本地部署方式或 `docker login`

**端口占用**: 
```powershell
netstat -ano | findstr :8000
taskkill /F /PID <ID>
```

**npm 失败**: 
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

**pip 失败**: 
```bash
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 版本
V1.0.4 (最新)

---
AutoScholar Team 2026
