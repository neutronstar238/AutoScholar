# AutoScholar

自主学术研究 AI Agent 系统

## 简介
AI 驱动的学术研究助手，支持文献检索、笔记生成、方向推荐。

## 快速开始

### Docker 部署 (推荐)
```bash
git clone https://github.com/neutronstar238/AutoScholar.git
cd AutoScholar
docker-compose up -d
# 访问 http://localhost:3000
```

### 本地部署 - 后端
```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs
```

### 本地部署 - 前端
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 常见问题

**Docker 认证错误**: 使用本地部署或 `docker login`

**端口占用**: `netstat -ano | findstr :8000` 然后 `taskkill /F /PID <ID>`

**npm 失败**: `npm config set registry https://registry.npmmirror.com`

**pip 失败**: `pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 版本
V1.0.3

---
AutoScholar Team 2026
