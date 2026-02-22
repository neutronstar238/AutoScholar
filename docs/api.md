# AutoScholar API 文档

**版本**: v0.1.0  
**基础 URL**: `http://localhost:8000/api/v1`

---

## 🔐 认证

### 获取 API Key

```http
POST /auth/api-key
Content-Type: application/json

{
  "email": "your@email.com",
  "password": "your_password"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "api_key": "sk-xxxxxxxxxxxxxxxx",
    "expires_at": "2026-12-31T23:59:59Z"
  }
}
```

### 认证方式

在所有 API 请求的 Header 中添加：
```
Authorization: Bearer YOUR_API_KEY
```

---

## 📚 文献检索 API

### 搜索文献

```http
POST /literature/search
```

**请求参数**:
```json
{
  "query": "AI Agent autonomous decision making",
  "limit": 10,
  "year_from": 2024,
  "year_to": 2026,
  "source": "arxiv"  // arxiv | scholar | all
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total": 156,
    "papers": [
      {
        "id": "2401.12345",
        "title": "论文标题",
        "authors": ["作者 1", "作者 2"],
        "abstract": "摘要内容...",
        "url": "https://arxiv.org/abs/2401.12345",
        "year": 2024,
        "citations": 42
      }
    ]
  }
}
```

### 获取论文详情

```http
GET /literature/{paper_id}
```

---

## 📝 研究笔记 API

### 生成研究笔记

```http
POST /notes/generate
```

**请求参数**:
```json
{
  "paper_url": "https://arxiv.org/abs/2401.12345",
  "language": "zh-CN",  // zh-CN | en
  "include_code": true,
  "depth": "detailed"  // brief | standard | detailed
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "note_id": "note_xxx",
    "title": "论文标题",
    "summary": "核心贡献总结...",
    "key_points": [
      "关键点 1",
      "关键点 2"
    ],
    "methodology": "方法论描述...",
    "limitations": "局限性分析...",
    "code_examples": [],
    "generated_at": "2026-02-22T10:00:00Z"
  }
}
```

### 获取笔记列表

```http
GET /notes
Query Parameters:
  - page: 页码
  - limit: 每页数量
  - keyword: 搜索关键词
```

---

## 💡 研究方向 API

### 获取创新方向推荐

```http
POST /research/recommend
```

**请求参数**:
```json
{
  "field": "AI Agent",
  "keywords": ["autonomous", "decision making", "multi-agent"],
  "time_range": "6m",  // 3m | 6m | 1y
  "count": 5
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "direction": "研究方向名称",
        "description": "详细描述...",
        "novelty_score": 0.85,
        "feasibility_score": 0.78,
        "related_papers": [...],
        "potential_applications": [...]
      }
    ]
  }
}
```

### 分析研究趋势

```http
GET /research/trends?field=AI+Agent
```

---

## 🤖 平台集成 API

### 飞书消息推送

```http
POST /platform/feishu/send
```

**请求参数**:
```json
{
  "user_id": "ou_xxxxx",
  "message_type": "text",  // text | markdown | interactive
  "content": {
    "text": "消息内容"
  }
}
```

### 企业微信消息推送

```http
POST /platform/wecom/send
```

### 钉钉消息推送

```http
POST /platform/dingtalk/send
```

---

## 💰 商业化 API

### 查询使用额度

```http
GET /billing/usage
```

**响应**:
```json
{
  "success": true,
  "data": {
    "plan": "free",  // free | pro | enterprise
    "used": 150,
    "limit": 1000,
    "reset_at": "2026-03-01T00:00:00Z"
  }
}
```

### 升级套餐

```http
POST /billing/upgrade
```

---

## ❌ 错误响应

所有 API 错误统一格式：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_API_KEY",
    "message": "API 密钥无效",
    "details": {}
  }
}
```

### 常见错误码

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-----------|
| `INVALID_API_KEY` | API 密钥无效 | 401 |
| `RATE_LIMIT_EXCEEDED` | 请求频率超限 | 429 |
| `INSUFFICIENT_QUOTA` | 额度不足 | 402 |
| `PAPER_NOT_FOUND` | 论文不存在 | 404 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |

---

## 📊 使用限制

| 套餐 | 文献检索 | 笔记生成 | 方向推荐 |
|------|---------|---------|---------|
| **Free** | 100 次/月 | 20 篇/月 | 5 次/月 |
| **Pro** | 1000 次/月 | 200 篇/月 | 50 次/月 |
| **Enterprise** | 无限 | 无限 | 无限 |

---

## 🧪 测试示例

```bash
# 1. 搜索文献
curl -X POST http://localhost:8000/api/v1/literature/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI Agent",
    "limit": 5
  }'

# 2. 生成笔记
curl -X POST http://localhost:8000/api/v1/notes/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "paper_url": "https://arxiv.org/abs/2401.12345",
    "language": "zh-CN"
  }'

# 3. 获取推荐
curl -X POST http://localhost:8000/api/v1/research/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "field": "AI Agent",
    "keywords": ["autonomous"]
  }'
```

---

*最后更新：2026-02-22*
