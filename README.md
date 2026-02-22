# AutoScholar

自主学术研究 AI Agent 系统

## 简介
AI 驱动的学术研究助手，支持文献检索、笔记生成、方向推荐。

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

```bash
# 1. 克隆项目
git clone https://github.com/neutronstar238/AutoScholar.git
cd AutoScholar

# 2. 安装后端依赖
cd backend
pip3 install -r requirements.txt

# 3. 启动后端 (终端 1)
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 安装前端依赖 (新开终端)
cd frontend
npm install

# 5. 启动前端 (终端 2)
npm run dev

# 6. 访问
# 前端：http://localhost:5173
# 后端 API：http://localhost:8000/docs
```

## 常见问题

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
