# 本地文件存储系统

## 概述

本地存储系统使用CSV文件替代SQL数据库，所有数据存储在 `backend/data/` 目录下。

## 数据文件

所有数据文件都是CSV格式，存储在以下位置：

- `backend/data/papers.csv` - 论文数据
- `backend/data/trending_papers.csv` - 热门论文缓存
- `backend/data/user_interests.csv` - 用户兴趣画像
- `backend/data/search_history.csv` - 搜索历史
- `backend/data/notes.csv` - 研究笔记
- `backend/data/users.csv` - 用户信息

## 使用方法

### 导入本地存储

```python
from app.storage.local_storage import local_storage
```

### 基本操作示例

#### 1. 热门论文操作

```python
# 获取热门论文
papers = await local_storage.get_trending_papers(category="cs.AI", limit=10, days=7)

# 创建热门论文
await local_storage.create_trending_paper({
    'paper_id': 'arxiv:2401.12345',
    'title': 'Example Paper',
    'abstract': 'This is an example',
    'category': 'cs.AI',
    'score': 1.0,
    'recommended_count': 1
})

# 更新热门论文
await local_storage.update_trending_paper('arxiv:2401.12345', {
    'score': '2.5',
    'recommended_count': '5'
})
```

#### 2. 用户兴趣操作

```python
# 获取用户兴趣
interests = await local_storage.get_user_interests(user_id=1, limit=10)

# 创建用户兴趣
await local_storage.create_user_interest({
    'user_id': 1,
    'keyword': 'deep learning',
    'weight': 0.8
})

# 更新用户兴趣
await local_storage.update_user_interest(
    user_id=1,
    keyword='deep learning',
    updates={'weight': '1.2'}
)

# 根据关键词查询
interest = await local_storage.get_user_interest_by_keyword(user_id=1, keyword='deep learning')
```

#### 3. 搜索历史操作

```python
# 创建搜索历史
await local_storage.create_search_history({
    'user_id': 1,
    'query': 'machine learning',
    'result_count': 10,
    'source': 'primary'
})

# 获取搜索历史
history = await local_storage.get_search_history(user_id=1, days=90, limit=50)

# 获取搜索历史（按查询分组统计）
grouped = await local_storage.get_search_history_grouped(user_id=1, limit=10)
# 返回: [{'query': 'machine learning', 'count': 5}, ...]
```

## 数据结构

### TrendingPaper (trending_papers.csv)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键ID |
| paper_id | str | 论文ID（如arxiv:2401.12345） |
| title | str | 论文标题 |
| abstract | str | 论文摘要 |
| url | str | 论文URL |
| authors | str | 作者列表（逗号分隔） |
| category | str | 论文分类 |
| score | float | 热度评分 |
| recommended_count | int | 推荐次数 |
| last_recommended_at | datetime | 最后推荐时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### UserInterest (user_interests.csv)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键ID |
| user_id | int | 用户ID |
| keyword | str | 兴趣关键词 |
| weight | float | 兴趣权重 |
| last_updated | datetime | 最后更新时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### SearchHistory (search_history.csv)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键ID |
| user_id | int | 用户ID（可为空） |
| query | str | 搜索查询 |
| result_count | int | 结果数量 |
| source | str | 数据源（primary/fallback/cache等） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 特性

### 1. 异步操作

所有操作都是异步的，使用 `asyncio.to_thread` 在后台线程中执行文件I/O操作。

### 2. 自动初始化

首次使用时会自动创建所有必需的CSV文件和表头。

### 3. 线程安全

使用 `asyncio.to_thread` 确保文件操作的线程安全。

### 4. 数据持久化

所有数据持久化存储在CSV文件中，重启后数据不会丢失。

## 迁移指南

### 从SQL数据库迁移

如果你之前使用SQL数据库，现在已经自动迁移到本地文件存储：

1. **UserProfileManager** - 已更新使用 `local_storage`
2. **TrendingManager** - 已更新使用 `local_storage`
3. 所有数据库操作已替换为本地文件操作

### 数据导出/导入

由于使用CSV格式，你可以轻松地：

- 使用Excel或其他工具查看和编辑数据
- 使用Python的csv模块进行数据处理
- 使用版本控制系统跟踪数据变化

## 性能考虑

- **小数据集**：CSV文件对于小到中等规模的数据集（<10000条记录）性能良好
- **大数据集**：如果数据量增长，考虑迁移到SQLite或PostgreSQL
- **并发访问**：当前实现适合单进程应用，多进程需要额外的锁机制

## 备份建议

定期备份 `backend/data/` 目录：

```bash
# 创建备份
tar -czf data_backup_$(date +%Y%m%d).tar.gz backend/data/

# 恢复备份
tar -xzf data_backup_20240115.tar.gz
```

## 故障排除

### 文件损坏

如果CSV文件损坏，删除对应文件，系统会自动重新创建空文件。

### 权限问题

确保应用有读写 `backend/data/` 目录的权限：

```bash
chmod -R 755 backend/data/
```

### 数据不一致

如果发现数据不一致，可以手动编辑CSV文件或使用Python脚本修复。
