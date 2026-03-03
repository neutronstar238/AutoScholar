# 数据库迁移到本地文件存储

## 概述

本项目已从PostgreSQL数据库迁移到基于CSV的本地文件存储系统。这使得项目更易于部署和维护，无需配置外部数据库。

## 迁移内容

### 已迁移的组件

1. **UserProfileManager** (`backend/app/engines/user_profile_manager.py`)
   - 从 SQLAlchemy ORM 迁移到本地存储API
   - 所有用户兴趣数据现在存储在 `backend/data/user_interests.csv`
   - 搜索历史存储在 `backend/data/search_history.csv`

2. **TrendingManager** (`backend/app/utils/trending_manager.py`)
   - 从 SQLAlchemy ORM 迁移到本地存储API
   - 热门论文数据存储在 `backend/data/trending_papers.csv`

### 数据存储位置

所有数据文件位于 `backend/data/` 目录：

```
backend/data/
├── papers.csv              # 论文数据
├── trending_papers.csv     # 热门论文缓存
├── user_interests.csv      # 用户兴趣画像
├── search_history.csv      # 搜索历史
├── notes.csv               # 研究笔记
└── users.csv               # 用户信息
```

## 变更说明

### 1. 不再需要的依赖

以下依赖不再需要（可以从 `requirements.txt` 中移除）：

```
sqlalchemy
asyncpg
psycopg2-binary
alembic
```

### 2. 不再需要的配置

不再需要配置 `DATABASE_URL` 环境变量。

### 3. API变更

#### 之前（使用SQLAlchemy）

```python
from app.models.base import UserInterest, get_engine
from sqlalchemy.ext.asyncio import AsyncSession

engine = get_engine()
async with AsyncSession(engine) as session:
    stmt = select(UserInterest).where(UserInterest.user_id == user_id)
    result = await session.execute(stmt)
    interests = result.scalars().all()
```

#### 现在（使用本地存储）

```python
from app.storage.local_storage import local_storage

interests = await local_storage.get_user_interests(user_id, limit=10)
```

## 使用指南

### 初始化

首次运行时，系统会自动创建所有必需的CSV文件：

```python
from app.storage.local_storage import local_storage

# 文件会在首次访问时自动创建
```

### 测试

运行测试脚本验证本地存储是否正常工作：

```bash
cd backend
python test_local_storage.py
```

### 数据备份

定期备份数据目录：

```bash
# 创建备份
tar -czf data_backup_$(date +%Y%m%d).tar.gz backend/data/

# 恢复备份
tar -xzf data_backup_20240115.tar.gz
```

## 性能对比

### 优势

1. **零配置**：无需安装和配置PostgreSQL
2. **易于部署**：只需复制文件即可
3. **易于调试**：可以直接用Excel查看和编辑数据
4. **版本控制友好**：CSV文件可以纳入Git管理
5. **跨平台**：在Windows、Linux、macOS上都能正常工作

### 限制

1. **并发性能**：不适合高并发场景（>100 QPS）
2. **数据规模**：适合小到中等规模数据（<10000条记录）
3. **查询能力**：不支持复杂的SQL查询
4. **事务支持**：没有ACID事务保证

## 何时考虑迁移回数据库

如果遇到以下情况，考虑迁移回PostgreSQL或SQLite：

1. 数据量超过10000条记录
2. 需要高并发访问（>100 QPS）
3. 需要复杂的关联查询
4. 需要ACID事务保证
5. 需要多进程/多服务器部署

## 故障排除

### 问题1：CSV文件损坏

**解决方案**：删除损坏的文件，系统会自动重新创建

```bash
rm backend/data/user_interests.csv
# 重启应用，文件会自动重新创建
```

### 问题2：权限错误

**解决方案**：确保应用有读写权限

```bash
chmod -R 755 backend/data/
```

### 问题3：数据不一致

**解决方案**：手动编辑CSV文件或使用Python脚本修复

```python
import csv

# 读取CSV
with open('backend/data/user_interests.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = list(reader)

# 修复数据
for row in data:
    if float(row['weight']) < 0:
        row['weight'] = '0.0'

# 写回CSV
with open('backend/data/user_interests.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
```

## 回滚到数据库（如果需要）

如果需要回滚到PostgreSQL：

1. 恢复 `app/models/base.py` 中的数据库模型
2. 恢复 `UserProfileManager` 和 `TrendingManager` 中的SQLAlchemy代码
3. 配置 `DATABASE_URL` 环境变量
4. 运行数据库迁移：`alembic upgrade head`

备份的SQL版本代码可以在Git历史中找到。

## 联系支持

如有问题，请查看：

- 本地存储文档：`backend/app/storage/README.md`
- 测试脚本：`backend/test_local_storage.py`
- 源代码：`backend/app/storage/local_storage.py`
