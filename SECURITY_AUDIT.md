# AutoScholar 安全审计报告（初步）

审计时间：2026-03-01  
审计方式：代码静态检查 + 依赖扫描尝试（受环境限制）

## 高风险问题

### 1) 缺少认证与授权（未登录可调用核心 API）
- 现状：核心业务接口（文献检索、笔记生成、研究推荐）未做身份认证或权限校验。
- 影响：任意用户可直接调用高成本能力（LLM/外部 API），导致资源滥用、费用损失与数据泄露风险。
- 证据：
  - 路由直接注册，无全局鉴权依赖。`backend/app/main.py`
  - 认证接口本身是占位实现。`backend/app/api/auth.py`
- 修复建议：
  1. 全局接入 JWT/API Key 鉴权中间件。
  2. 对高成本接口增加角色/配额校验（RBAC + quota）。
  3. 管理端与用户端接口分级授权。

### 2) 前端 Markdown 渲染存在 XSS 风险
- 现状：页面使用 `v-html` 直接注入 `marked()` 输出，未见 HTML 白名单过滤或 sanitize。
- 影响：若模型输出或外部输入包含恶意 HTML/脚本片段，可能触发存储型/反射型 XSS，劫持会话或诱导操作。
- 证据：
  - `frontend/src/pages/Research.vue` 中 `v-html="renderedRecommendations"`。
  - `frontend/src/pages/Notes.vue` 中 `v-html="renderedContent(note.content)"`。
- 修复建议：
  1. 在 `marked` 后追加 DOMPurify 等 sanitizer。
  2. 前后端双重过滤（输出编码 + CSP）。
  3. 尽量改为受控组件渲染，避免直接 `v-html`。

## 中风险问题

### 3) 默认弱密钥与默认数据库口令
- 现状：配置里包含明显弱默认值。
- 影响：误用默认配置上线时，容易被猜解或横向利用。
- 证据：
  - `DATABASE_URL` 默认包含 `autoscholar:password`。
  - `API_KEY_SECRET` 默认值为 `your-secret-key-change-in-production`。
- 修复建议：
  1. 生产环境强制从环境变量读取密钥，未设置则拒绝启动。
  2. 引入密钥复杂度校验与启动时安全自检。
  3. 使用 Secret Manager，不在代码中保留可用默认值。

### 4) 调试模式默认开启 + 错误细节直接回传
- 现状：`APP_DEBUG=True` 为默认值；多个接口在异常时回传 `str(e)`。
- 影响：生产误配置时易暴露内部堆栈/实现细节，辅助攻击者构造利用链。
- 证据：
  - `backend/app/utils/config.py` 中 `APP_DEBUG: bool = True`。
  - 例如 `backend/app/api/research.py`、`backend/app/api/literature.py` 的异常处理回传错误详情。
- 修复建议：
  1. 默认 `APP_DEBUG=False`。
  2. 统一异常处理：对外返回通用错误码，对内记录详细日志。

### 5) 输入约束不足（可能导致滥用与 DoS）
- 现状：多个请求字段缺少长度、格式、上限约束；接口可触发外部请求与大模型调用。
- 影响：可被构造超长输入/高频调用，放大成本并影响可用性。
- 证据：
  - `ResearchRecommendRequest.interests/limit` 未设置 Pydantic 严格边界。
  - 文献检索、笔记生成接口未见请求频率限制。
- 修复建议：
  1. 为关键字段增加 `min_length/max_length/ge/le/regex`。
  2. 接入限流（如 `slowapi` / 网关限流）与并发控制。
  3. 增加用户级配额与调用审计。

## 依赖漏洞扫描说明（环境限制）
- Python：尝试 `pip-audit`，环境中未安装且无法从外网源安装。
- Frontend：尝试 `npm audit`，审计接口返回 403（代理/网络策略限制）。
- 结论：本报告以代码级漏洞为主，依赖 CVE 仍需在可联网 CI 环境补做。

## 优先级建议（7 天内）
1. **P0**：接入统一鉴权 + 限流（先保护高成本 API）。
2. **P0**：修复 `v-html` 渲染链路（引入 sanitize + CSP）。
3. **P1**：移除默认弱密钥与默认口令，改为“未配置拒绝启动”。
4. **P1**：关闭默认 debug，统一错误响应策略。
5. **P2**：补齐依赖扫描（pip-audit / npm audit / SCA）并接入 CI。
