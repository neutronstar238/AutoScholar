# Python 版本兼容性指南

## 支持的 Python 版本

AutoScholar 项目推荐使用 **Python 3.10-3.13**，最佳版本是 **Python 3.11**。

## 为什么不支持 Python 3.14+？

部分核心依赖库尚未支持 Python 3.14：
- `crewai` - 最高支持到 Python 3.13
- `langgraph` - 最高支持到 Python 3.13

这些库已在 `requirements.txt` 中被注释掉，核心功能（文献检索、笔记生成）不受影响。

## 如何检查 Python 版本

```bash
python --version
```

## 如何安装 Python 3.11

### Windows

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.11.x 安装包
3. 运行安装程序，勾选 "Add Python to PATH"
4. 完成安装后验证：`python --version`

### 使用多个 Python 版本

如果系统已安装 Python 3.14，可以同时安装 Python 3.11：

```bash
# 使用 Python Launcher 选择版本
py -3.11 --version

# 创建虚拟环境时指定版本
py -3.11 -m venv .venv
```

## 创建虚拟环境

### 推荐方式（Python 3.11）

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 验证版本
python --version

# 安装依赖
pip install -r backend/requirements.txt
```

### 使用 Python 3.14（部分功能受限）

如果必须使用 Python 3.14，项目仍可运行，但以下功能不可用：
- CrewAI 多 Agent 协作
- LangGraph 工作流

核心功能正常：
- ✅ 文献检索（arXiv）
- ✅ 研究笔记生成
- ✅ API 服务
- ✅ 前端界面

## 测试安装

```bash
# 激活虚拟环境后
cd backend
python -m uvicorn app.main:app --reload

# 应该看到：
# ✨ AutoScholar 启动完成！
# INFO: Uvicorn running on http://0.0.0.0:8000
```

## 常见问题

### Q: 我的系统只有 Python 3.14，怎么办？

A: 有两个选择：
1. 安装 Python 3.11（推荐）- 可以与 3.14 共存
2. 继续使用 3.14 - 核心功能可用，但缺少部分 Agent 框架

### Q: 虚拟环境创建失败？

A: 尝试以下方法：
```bash
# 方法 1: 清理后重建
Remove-Item -Recurse -Force .venv
python -m venv .venv

# 方法 2: 使用不同名称
python -m venv venv311

# 方法 3: 指定 Python 版本
py -3.11 -m venv .venv
```

### Q: 依赖安装失败？

A: 检查以下几点：
1. Python 版本是否正确：`python --version`
2. 虚拟环境是否激活：提示符应显示 `(.venv)`
3. 使用国内镜像：已在 pip 配置中设置清华源

### Q: 数据库连接失败？

A: 这是正常的，如果没有安装 PostgreSQL：
- 系统会显示警告但继续运行
- 核心功能（文献检索、笔记生成）不受影响
- 数据不会持久化，但可以正常使用

## 版本兼容性矩阵

| Python 版本 | 状态 | 说明 |
|------------|------|------|
| 3.9 及以下 | ❌ 不支持 | 依赖库要求 3.10+ |
| 3.10 | ✅ 支持 | 完整功能 |
| 3.11 | ✅ 推荐 | 最佳性能和兼容性 |
| 3.12 | ✅ 支持 | 完整功能 |
| 3.13 | ✅ 支持 | 完整功能 |
| 3.14+ | ⚠️ 部分支持 | 核心功能可用，Agent 框架不可用 |

## 更新日志

- 2026-02-22: 添加 Python 3.14 兼容性说明
- 2026-02-22: 注释掉不兼容的依赖（crewai, langgraph）
- 2026-02-22: 验证 Python 3.14 下核心功能正常运行
