# 🔑 AutoScholar 配置指南

## 模型提供商配置

### 推荐配置：Qwen3.5 + Qwen 双提供商自动回退

#### 1. 获取 API Key

**Qwen3.5 API Key**:
1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 登录/注册账号
3. 进入「API-KEY 管理」
4. 创建新的 API Key
5. 复制 Key 到配置文件

**Qwen API Key** (备选):
- 同上，使用同一个阿里云账号即可

#### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# ===== AI 模型配置 =====

# Qwen3.5 (优先使用)
QWEN35_API_KEY=sk-your-qwen35-api-key-here

# Qwen (备选回退)
QWEN_API_KEY=sk-your-qwen-api-key-here

# 模型提供商优先级
MODEL_PROVIDERS=qwen3.5,qwen
PRIMARY_PROVIDER=qwen3.5
FALLBACK_PROVIDER=qwen
```

#### 3. 测试连接

运行测试脚本：

```bash
cd /AstrBot/AutoScholar
python3 scripts/test_model.py
```

**预期输出**:
```
📊 测试结果:
------------------------------------------------------------
  qwen3.5: ✅ 成功
  qwen: ✅ 成功

✅ 调用成功！
  使用的提供商：qwen3.5
  使用的模型：qwen-plus
  回复内容：你好！我是 AutoScholar 的 AI 助手...
```

---

## 回退机制说明

### 工作流程

```
用户请求
    ↓
尝试 Qwen3.5 (PRIMARY_PROVIDER)
    ↓
成功？───是───→ 返回结果
    │
   否
    │
    ↓
尝试 Qwen (FALLBACK_PROVIDER)
    ↓
成功？───是───→ 返回结果
    │
   否
    │
    ↓
返回错误
```

### 日志示例

**成功使用 Qwen3.5**:
```
🤖 尝试使用提供商：['qwen3.5', 'qwen']
📡 正在调用 qwen3.5...
✅ qwen3.5 调用成功！
```

**Qwen3.5 失败，回退到 Qwen**:
```
🤖 尝试使用提供商：['qwen3.5', 'qwen']
📡 正在调用 qwen3.5...
❌ qwen3.5 调用失败：API timeout
📡 正在调用 qwen...
✅ qwen 调用成功！
```

---

## 其他配置选项

### 仅使用 Qwen3.5

```bash
MODEL_PROVIDERS=qwen3.5
PRIMARY_PROVIDER=qwen3.5
FALLBACK_PROVIDER=qwen3.5
QWEN35_API_KEY=sk-your-key
```

### 仅使用 Qwen

```bash
MODEL_PROVIDERS=qwen
PRIMARY_PROVIDER=qwen
FALLBACK_PROVIDER=qwen
QWEN_API_KEY=sk-your-key
```

### 使用 Ollama 本地部署

```bash
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

---

## 故障排查

### 问题 1: API Key 无效

**错误**: `401 Unauthorized`

**解决**:
1. 检查 API Key 是否正确复制
2. 确认 API Key 未过期
3. 检查账号余额是否充足

### 问题 2: 连接超时

**错误**: `Connection timeout`

**解决**:
1. 检查网络连接
2. 增加超时时间配置
3. 尝试使用备用提供商

### 问题 3: 模型不可用

**错误**: `Model not found`

**解决**:
1. 确认模型名称正确
2. 检查模型是否在目标区域可用
3. 联系提供商支持

---

## 最佳实践

1. **始终配置备用提供商** - 避免单点故障
2. **定期检查 API Key 余额** - 避免服务中断
3. **监控调用日志** - 及时发现回退情况
4. **设置告警** - 当频繁回退时通知

---

*最后更新：2026-02-22*
