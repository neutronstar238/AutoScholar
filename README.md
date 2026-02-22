# AutoScholar

自主学术研究 AI Agent 系统

## 项目简介

AutoScholar 是一个 AI 驱动的学术研究助手，能够：
- 检索学术文献 (arXiv)
- 生成研究笔记
- 推荐研究方向
- 多 Agent 协作
- 飞书等平台集成

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
git clone https://github.com/neutronstar238/AutoScholar.git
cd AutoScholar
docker-compose up -d
```

访问：http://localhost:3000

## 技术栈

- 前端：Vue 3
- 后端：FastAPI
- 数据库：PostgreSQL + pgvector
- 缓存：Redis

## 版本

V1.0.0 正式发布

---
AutoScholar Team 2026
