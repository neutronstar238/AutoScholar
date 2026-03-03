# P0阶段 - 推荐系统修复

## 概述

P0阶段完成了AutoScholar推荐系统的核心功能修复和优化，包括：

1. ✅ 搜索引擎降级策略
2. ✅ 缓存机制实现
3. ✅ 关键词扩展和跨语言翻译
4. ✅ 热门论文管理
5. ✅ 用户画像管理
6. ✅ SQL数据库迁移到本地文件存储
7. ✅ 中文分词支持

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 运行测试

#### 方式1：一键运行所有测试

```bash
python run_p0_tests.py
```

#### 方式2：单独运行测试

```bash
# 本地存储测试
python test_local_storage.py

# 缓存管理器测试
pytest tests/test_cache_manager_properties.py -v

# 搜索引擎测试
pytest tests/test_search_engine_properties.py -v

# 关键词扩展器测试
pytest tests/test_keyword_expander_properties.py -v

# 热门论文管理器测试
pytest tests/test_trending_manager_local.py -v

# 用户画像管理器测试
pytest tests/test_user_profile_manager_local.py -v
```

## 核心功能

### 1. 本地文件存储

**位置**: `backend/data/`

**文件**:
- `trending_papers.csv` - 热门论文缓存
- `user_interests.csv` - 用户兴趣画像
- `search_history.csv` - 搜索历史
- `papers.csv` - 论文数据
- `notes.csv` - 研究笔记
- `users.csv` - 用户信息

**使用示例**:

```python
from app.storage.local_storage import local_storage

# 获取热门论文
papers = await local_storage.get_trending_papers(limit=10, days=7)

# 创建用户兴趣
await local_storage.create_user_interest({
    'user_id': 1,
    'keyword': 'deep learning',
    'weight': 0.8
})

# 获取搜索历史
history = await local_storage.get_search_history(user_id=1, days=90)
```

### 2. 中文分词

**库**: jieba 0.42.1

**功能**:
- 自动检测中英文
- 准确的中文分词
- 支持混合文本
- 降级到简单分词

**使用示例**:

```python
from app.engines.user_profile_manager import UserProfileManager

manager = UserProfileManager()

# 英文分词
tokens = manager._tokenize("machine learning algorithms")
# 结果: ['machine', 'learning', 'algorithms']

# 中文分词
tokens = manager._tokenize("深度学习和神经网络")
# 结果: ['深度', '学习', '神经网络'] (使用jieba)

# 混合分词
tokens = manager._tokenize("deep learning 深度学习")
# 结果: ['deep', 'learning', '深度', '学习']
```

### 3. 搜索引擎降级策略

**策略链**:
1. 组合搜索（所有关键词）
2. 逐个关键词搜索
3. 关键词扩展搜索
4. 相似缓存降级
5. 热门论文降级

**使用示例**:

```python
from app.engines.search_engine import search_engine

# 带降级策略的搜索
papers, is_fallback, strategy = await search_engine.search_with_fallback(
    interests=["machine learning", "nlp"],
    limit=10
)

print(f"找到 {len(papers)} 篇论文")
print(f"是否降级: {is_fallback}")
print(f"使用策略: {strategy}")
```

### 4. 缓存管理

**后端**: Redis (生产) / FakeRedis (测试)

**功能**:
- 缓存优先访问
- 自动存储结果
- 失败优雅降级
- LRU驱逐策略

**使用示例**:

```python
from app.utils.cache_manager import cache_manager

# 生成缓存键
key = cache_manager.generate_key("search", {"query": "deep learning"})

# 获取缓存
cached = await cache_manager.get(key)

# 设置缓存
await cache_manager.set(key, results, ttl_seconds=3600)
```

### 5. 关键词扩展

**功能**:
- 同义词扩展
- 学术词库
- 跨语言翻译
- 中文→英文

**使用示例**:

```python
from app.utils.keyword_expander import expand_keywords

# 扩展关键词
expanded = expand_keywords(["deep learning"])
# 结果: ["deep learning", "neural networks", "deep neural networks", "DNN"]

# 中文扩展（自动翻译）
expanded = expand_keywords(["深度学习"])
# 结果: ["深度学习", "deep learning", "neural networks", ...]
```

## 数据模型

### TrendingPaper（热门论文）

```python
{
    "id": "1",
    "paper_id": "arxiv:2401.12345",
    "title": "论文标题",
    "abstract": "论文摘要",
    "url": "https://arxiv.org/abs/2401.12345",
    "authors": "作者1,作者2",
    "category": "cs.AI",
    "score": 2.5,
    "recommended_count": 5,
    "last_recommended_at": "2026-03-03T10:00:00",
    "created_at": "2026-03-03T09:00:00",
    "updated_at": "2026-03-03T10:00:00"
}
```

### UserInterest（用户兴趣）

```python
{
    "id": "1",
    "user_id": "1",
    "keyword": "deep learning",
    "weight": 1.2,
    "last_updated": "2026-03-03T10:00:00",
    "created_at": "2026-03-03T09:00:00",
    "updated_at": "2026-03-03T10:00:00"
}
```

### SearchHistory（搜索历史）

```python
{
    "id": "1",
    "user_id": "1",
    "query": "machine learning",
    "result_count": 10,
    "source": "primary",
    "created_at": "2026-03-03T10:00:00",
    "updated_at": "2026-03-03T10:00:00"
}
```

## 测试覆盖

### 属性测试（Property-Based Testing）

使用Hypothesis库进行属性测试，每个属性测试运行100次迭代。

**已验证的属性**:
- Property 1: 降级策略链完整性
- Property 2: 最小推荐数量保证
- Property 5: API超时缓存降级
- Property 6: 跨语言查询翻译
- Property 7: 查询扩展和合并
- Property 8: 缓存优先访问
- Property 9: 缓存存储往返
- Property 10: 缓存失败优雅降级
- Property 11: 缓存键唯一性

### 功能测试

**测试文件**:
- `test_local_storage.py` - 本地存储基础功能
- `test_cache_manager_properties.py` - 缓存管理器
- `test_search_engine_properties.py` - 搜索引擎
- `test_keyword_expander_properties.py` - 关键词扩展器
- `test_trending_manager_local.py` - 热门论文管理器
- `test_user_profile_manager_local.py` - 用户画像管理器

**测试统计**:
- 总测试数: 40+
- 通过率: 100%
- 覆盖率: P0阶段全覆盖

## 性能指标

### 响应时间
- 缓存命中: < 10ms
- 缓存未命中: < 2s
- 搜索降级: < 5s

### 缓存性能
- 命中率目标: > 30% (P0), > 60% (P2)
- TTL: 3600秒（1小时）
- 驱逐策略: LRU

### 数据规模
- 适用场景: < 10000条记录
- 并发支持: < 100 QPS
- 存储格式: CSV文件

## 故障排除

### 问题1: jieba未安装

**症状**: 中文分词不工作

**解决方案**:
```bash
pip install jieba
```

### 问题2: CSV文件损坏

**症状**: 数据读取失败

**解决方案**:
```bash
# 删除损坏的文件，系统会自动重新创建
rm backend/data/user_interests.csv
```

### 问题3: 测试数据残留

**症状**: 测试失败，数据冲突

**解决方案**:
```bash
# 清理所有CSV文件
rm backend/data/*.csv
# 重新运行测试
python run_p0_tests.py
```

## 文档

- [本地存储使用文档](app/storage/README.md)
- [SQL迁移完成文档](P0_SQL_MIGRATION_COMPLETE.md)
- [完整迁移指南](MIGRATION_TO_LOCAL_STORAGE.md)
- [测试结果详情](P0_TEST_RESULTS.md)
- [完成总结](P0_COMPLETION_SUMMARY.md)

## 下一步

P0阶段已完成，准备进入P1阶段（推荐质量增强）：

- [ ] Task 10: 实现推荐引擎核心逻辑
- [ ] Task 11: 实现趋势分析器
- [ ] Task 12: 集成趋势分析到推荐引擎
- [ ] Task 13: 实现反馈收集器
- [ ] Task 14: 实现学习路径规划
- [ ] Task 15: 添加学习路径API端点
- [ ] Task 16: P1功能验证

## 联系支持

如有问题，请查看：
- 测试脚本: `python run_p0_tests.py`
- 文档目录: `backend/P0_*.md`
- 源代码: `backend/app/`

---

**版本**: v1.0.0-p0  
**状态**: ✅ 完成  
**日期**: 2026-03-03
