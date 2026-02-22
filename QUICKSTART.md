# AutoScholar 快速启动指南

## 🐛 已修复的问题

1. ✅ 前端路由集成问题
2. ✅ 前端 axios 配置
3. ✅ App.vue 缺少路由出口和导航菜单
4. ✅ 数据库初始化函数实现
5. ✅ Notes.vue 缺少 marked 依赖
6. ✅ User.vue 页面缺失
7. ✅ 端口配置统一（前端 5173，后端 8000）
8. ✅ CORS 配置修复
9. ✅ API 路由完善

## 🚀 启动步骤

### 1. 配置环境变量

编辑 `.env` 文件，至少配置一个 AI 模型的 API Key：

```bash
# 推荐：配置 Qwen API Key
QWEN_API_KEY=sk-your-api-key-here

# 或者配置 Qwen3.5
QWEN35_API_KEY=sk-your-api-key-here
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 启动
API 文档：http://localhost:8000/docs

### 3. 启动前端

打开新终端：

```bash
cd frontend
npm install
npm run dev
```

前端将在 http://localhost:5173 启动

## 📝 功能说明

### 文献检索 (/)
- 输入关键词搜索 arXiv 论文
- 显示论文标题、作者、摘要
- 点击链接查看全文

### 研究笔记 (/notes)
- 输入论文 URL 生成研究笔记
- 使用 AI 自动分析论文内容
- 支持复制和删除笔记

### 研究方向 (/research)
- 待实现：研究方向推荐

### 用户中心 (/user)
- 用户信息管理
- API Key 配置
- 使用统计

## ⚠️ 注意事项

### 数据库（可选）
如果没有安装 PostgreSQL，系统会跳过数据库初始化，但核心功能仍可使用。

要使用完整功能，请安装 PostgreSQL：
```bash
# Windows (使用 Chocolatey)
choco install postgresql

# 或下载安装包
# https://www.postgresql.org/download/windows/
```

### Redis（可选）
Redis 用于缓存，不是必需的。

### API Key
必须配置至少一个 AI 模型的 API Key，否则笔记生成功能无法使用。

支持的提供商：
- Qwen (通义千问)
- Qwen3.5 (通义千问 3.5)
- DeepSeek
- OpenAI

## 🔧 常见问题

### 端口被占用
```powershell
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# 结束进程
taskkill /F /PID <进程ID>
```

### npm 安装失败
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### pip 安装失败
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### CORS 错误
确保：
1. 后端 FRONTEND_URL 配置为 `http://localhost:5173`
2. 前端 vite.config.js 配置了正确的 proxy

## 📦 Docker 部署（可选）

```bash
docker-compose up -d
```

访问：
- 前端：http://localhost:3000
- 后端：http://localhost:8000/docs

## 🎯 下一步

1. 配置 API Key
2. 测试文献检索功能
3. 测试笔记生成功能
4. 根据需要配置数据库

祝使用愉快！🎉
