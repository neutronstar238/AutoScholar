# AutoScholar

自主学术研究 AI Agent 系统

## 项目简介

AutoScholar 是一个 AI 驱动的学术研究助手，能够：
- 检索学术文献 (arXiv)
- 生成研究笔记
- 推荐研究方向
- 多 Agent 协作
- 飞书等平台集成

**目标用户**: 研究人员、研究生、科研工作者

## 输入输出

### 文献检索
**输入**: 关键词字符串
**输出**: 论文列表 JSON

### 研究笔记
**输入**: 论文 URL
**输出**: Markdown 格式笔记

### 方向推荐
**输入**: 研究领域 + 关键词
**输出**: 推荐方向列表 (含新颖度、可行性评分)

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/neutronstar238/AutoScholar.git
cd AutoScholar

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
# 前端：http://localhost:3000
# 后端：http://localhost:8000/docs
```

## 技术栈

- 前端：Vue 3
- 后端：FastAPI
- 数据库：PostgreSQL + pgvector
- 缓存：Redis

## 常见问题

### 1. Docker 认证错误

**错误**:
```
authentication required - email must be verified before using account
```

**解决方案**:
```bash
# 方案 A: 登录 Docker Hub
docker login

# 方案 B: 使用 WSL2 (Windows)
# 在 WSL2 中运行 docker-compose

# 方案 C: 仅运行后端
pip3 install -r backend/requirements.txt
python3 -m uvicorn app.main:app --reload
```

### 2. 端口被占用

**错误**:
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解决方案**:

Windows:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 终止进程
taskkill /PID <进程 ID> /F
```

Linux/Mac:
```bash
lsof -i :8000
kill -9 <进程 ID>
```

### 3. 数据库连接失败

**错误**:
```
could not connect to server: Connection refused
```

**解决方案**:
```bash
# 检查数据库是否启动
docker-compose ps

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db

# 等待 30 秒后重试
```

### 4. 前端无法访问后端

**现象**: 浏览器控制台显示 API 请求失败

**解决方案**:
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查前端配置
# 确保 frontend/src/main.js 中的 API 地址正确

# 重启服务
docker-compose restart backend frontend
```

### 5. 依赖安装失败

**错误**:
```
ERROR: Could not find a version that satisfies the requirement xxx
```

**解决方案**:
```bash
# 升级 pip
python3 -m pip install --upgrade pip

# 使用国内镜像
pip3 install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6. Docker Compose 警告

**警告**:
```
the attribute `version` is obsolete, it will be ignored
```

**解决方案**:
- 已修复，请拉取最新代码
```bash
git pull origin main
```

## 版本

**当前版本**: V1.0.1 (最新稳定版)

---

AutoScholar Team 2026
