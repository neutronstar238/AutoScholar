# Implementation Plan: Search and Recommendation Optimization

## Overview

本实现计划将AutoScholar系统的研究方向推荐模块从当前的脆弱状态改造为鲁棒、智能的推荐系统。实现按优先级分为三个阶段：P0修复核心问题，P1增强推荐质量，P2优化搜索功能。

**实现语言**: Python 3.11
**核心框架**: FastAPI, SQLAlchemy, Redis, Hypothesis (PBT)

## Tasks

### Phase 1: P0 关键功能 - 推荐系统修复

- [x] 1. 设置Redis缓存基础设施
  - 安装redis-py和fakeredis依赖
  - 创建backend/app/utils/cache_manager.py
  - 实现CacheManager类（get/set/generate_key方法）
  - 配置Redis连接（支持本地开发和生产环境）
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [x] 1.1 编写缓存管理器的属性测试
  - **Property 8: 缓存优先访问**
  - **Property 9: 缓存存储往返**
  - **Property 11: 缓存键唯一性**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [x] 2. 实现关键词扩展器和跨语言翻译
  - 创建backend/app/utils/keyword_expander.py
  - 实现语言检测（中文/英文）
  - 实现LLM翻译功能（中文→英文学术术语）
  - 加载学术词库（同义词、缩写）
  - 实现关键词扩展逻辑
  - _Requirements: 2.1, 2.7_

- [x] 2.1 编写关键词扩展器的属性测试
  - **Property 6: 跨语言查询翻译**
  - **Property 7: 查询扩展和合并**
  - **Validates: Requirements 2.1, 2.7**

- [x] 3. 实现搜索引擎降级策略
  - 创建backend/app/engines/search_engine.py
  - 实现search_with_fallback方法
  - 策略1: 所有关键词组合搜索
  - 策略2: 逐个关键词搜索
  - 策略3: 关键词扩展搜索
  - 策略4: 缓存相似查询降级
  - 策略5: 热门论文降级
  - 实现重试机制（3次，指数退避）
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.2, 2.4_

- [x] 3.1 编写搜索引擎降级策略的属性测试
  - **Property 1: 降级策略链完整性**
  - **Property 2: 最小推荐数量保证**
  - **Property 5: API超时缓存降级**
  - **Property 7: 重试指数退避**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.4**

- [x] 4. 创建热门论文缓存表和管理
  - 在backend/app/models/base.py添加TrendingPaper模型
  - 实现热门论文更新逻辑（基于推荐次数）
  - 实现热门论文查询接口
  - _Requirements: 1.3, 1.4_

- [x] 5. 重构研究方向推荐API
  - 修改backend/app/api/research.py
  - 更新recommend端点，集成搜索引擎降级策略
  - 添加降级标识到响应（is_fallback字段）
  - 实现降级率追踪和告警
  - 添加错误处理和用户友好的错误消息
  - _Requirements: 1.5, 1.6, 1.7, 2.3, 2.5, 2.6_

- [x] 5.1 编写推荐API的属性测试
  - **Property 3: 降级标识正确性**
  - **Property 4: 降级率追踪准确性**
  - **Validates: Requirements 1.6, 1.7**

- [x] 6. 实现缓存集成到文献检索
  - 修改backend/app/tools/literature_search.py
  - 在search_literature中集成CacheManager
  - 实现缓存优先逻辑
  - 实现缓存失败优雅降级
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 6.1 编写缓存集成的属性测试
  - **Property 10: 缓存失败优雅降级**
  - **Validates: Requirements 4.4**

- [x] 7. Checkpoint - P0功能验证
  - 确保所有P0测试通过
  - 验证推荐系统不再返回"未找到相关论文"错误
  - 测试中文输入能正确翻译并搜索英文论文
  - 验证缓存命中率 > 30%
  - 询问用户是否有问题

### Phase 2: P1 重要功能 - 推荐质量增强

- [x] 8. 创建用户画像数据模型
  - 在backend/app/models/base.py添加UserInterest模型
  - 在backend/app/models/base.py添加SearchHistory模型
  - 实现数据库迁移
  - _Requirements: 5.1, 5.2, 10.1_

- [x] 9. 实现用户画像管理器
  - 创建backend/app/engines/user_profile_manager.py
  - 实现extract_interests方法（从历史提取兴趣）
  - 实现suggest_interests_for_input方法（输入建议）
  - 实现update_interest_from_search方法
  - 实现update_interest_from_reading方法
  - 实现兴趣权重计算公式
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 9.1 编写用户画像管理器的属性测试
  - **Property 20: 用户兴趣自动提取**
  - **Property 21: 用户兴趣关键词提取权重**
  - **Property 22: 阅读行为追踪**
  - **Property 24: 反馈权重调整**
  - **Property 25: 兴趣关键词数量上限**
  - **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

- [x] 10. 实现推荐引擎核心逻辑
  - 创建backend/app/engines/recommendation_engine.py
  - 实现generate_recommendations方法（四种模式）
  - 实现suggest_interests方法
  - 集成用户画像管理器
  - 集成搜索引擎
  - _Requirements: 5.1, 5.3_

- [x] 10.1 编写推荐引擎的属性测试
  - **Property 23: 个性化推荐优先级**
  - **Validates: Requirements 5.3**

- [ ] 11. 实现趋势分析器
  - 创建backend/app/engines/trend_analyzer.py
  - 实现analyze_papers方法（综合评分）
  - 实现get_trending_topics方法
  - 实现引用分析逻辑（Top 10%识别）
  - 实现趋势增长率计算
  - 实现热度评分归一化
  - _Requirements: 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 6.5_

- [ ]* 11.1 编写趋势分析器的属性测试
  - **Property 14: 引用分析Top 10%识别**
  - **Property 15: 趋势增长率检测**
  - **Property 16: 推荐评分加权公式**
  - **Property 26: 热度评分归一化**
  - **Validates: Requirements 3.2, 3.3, 3.4, 6.5**

- [ ] 12. 集成趋势分析到推荐引擎
  - 修改backend/app/engines/recommendation_engine.py
  - 在generate_recommendations中调用趋势分析器
  - 实现推荐数量范围约束（3-10）
  - 实现引用数据缺失降级
  - 添加置信度分数计算
  - _Requirements: 3.5, 3.6, 3.7_

- [ ]* 12.1 编写推荐引擎集成的属性测试
  - **Property 17: 推荐数量范围约束**
  - **Property 18: 引用数据缺失降级**
  - **Property 19: 置信度分数存在性**
  - **Validates: Requirements 3.5, 3.6, 3.7**

- [ ] 13. 实现反馈收集器
  - 创建backend/app/utils/feedback_collector.py
  - 实现record_view方法
  - 实现record_feedback方法（helpful/not helpful/ignore）
  - 实现calculate_metrics方法（CTR, helpfulness ratio）
  - 集成到用户画像管理器
  - _Requirements: 8.1, 8.4, 8.6_

- [ ]* 13.1 编写反馈收集器的属性测试
  - **Property 32: 反馈事件记录**
  - **Property 33: 推荐质量指标计算**
  - **Validates: Requirements 8.1, 8.4, 8.6**

- [ ] 14. 实现学习路径规划
  - 在backend/app/engines/recommendation_engine.py添加generate_learning_path方法
  - 实现引用关系排序（foundational → advanced）
  - 实现综述论文识别和优先
  - 实现3-5阶段划分
  - 实现论文数量限制（最多15篇）
  - _Requirements: 7.2, 7.3, 7.4, 7.7_

- [ ]* 14.1 编写学习路径规划的属性测试
  - **Property 28: 学习路径引用排序**
  - **Property 29: 学习路径综述起点**
  - **Property 30: 学习路径阶段数量**
  - **Property 31: 学习路径论文数量限制**
  - **Validates: Requirements 7.2, 7.3, 7.4, 7.7**

- [ ] 15. 添加学习路径API端点
  - 在backend/app/api/research.py添加/learning-path端点
  - 实现请求验证
  - 集成学习路径规划功能
  - _Requirements: 7.1, 7.5, 7.6_

- [ ] 16. Checkpoint - P1功能验证
  - 确保所有P1测试通过
  - 验证个性化推荐对有历史用户生效
  - 验证学习路径包含3-5个阶段
  - 验证反馈机制正确更新用户画像
  - 询问用户是否有问题

### Phase 3: P2 优化功能 - 搜索功能增强

- [ ] 17. 实现布尔运算符查询解析器
  - 创建backend/app/utils/query_parser.py
  - 实现parse_query方法
  - 支持AND, OR, NOT运算符
  - 实现运算符优先级（NOT > AND > OR）
  - 支持括号分组
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ]* 17.1 编写查询解析器的属性测试
  - **Property 34: 布尔运算符优先级**
  - **Validates: Requirements 9.5, 9.6**

- [ ] 18. 实现搜索历史记录
  - 修改backend/app/api/literature.py
  - 在搜索时记录到SearchHistory表
  - 实现/search-history端点（返回最近50条）
  - 实现/search-history DELETE端点
  - 实现90天自动清理
  - _Requirements: 10.1, 10.2, 10.5, 10.6_

- [ ]* 18.1 编写搜索历史的属性测试
  - **Property 35: 搜索历史记录保留**
  - **Validates: Requirements 10.1, 10.5**

- [ ] 19. 实现热门搜索统计
  - 在backend/app/utils/cache_manager.py添加hot_searches方法
  - 使用Redis Sorted Set统计查询频率
  - 实现/hot-searches端点
  - 排除少于3字符的查询
  - _Requirements: 10.3, 10.4, 10.7_

- [ ]* 19.1 编写热门搜索的属性测试
  - **Property 36: 热门搜索统计**
  - **Validates: Requirements 10.4, 10.7**

- [ ] 20. 实现高级过滤管理器
  - 创建backend/app/utils/filter_manager.py
  - 实现apply_filters方法
  - 支持日期范围过滤
  - 支持作者过滤（部分匹配，不区分大小写）
  - 支持分类过滤
  - 实现多过滤条件AND逻辑
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ]* 20.1 编写过滤管理器的属性测试
  - **Property 37: 多过滤条件交集**
  - **Validates: Requirements 11.4**

- [ ] 21. 实现相关性评分器
  - 创建backend/app/utils/relevance_scorer.py
  - 实现calculate_relevance方法
  - 标题关键词频率权重3.0
  - 摘要关键词频率权重1.5
  - 时间衰减因子0.95^years
  - 归一化到[0.0, 1.0]
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

- [ ]* 21.1 编写相关性评分器的属性测试
  - **Property 38: 相关性评分加权**
  - **Validates: Requirements 12.1, 12.2, 12.3**

- [ ] 22. 实现自动补全服务
  - 创建backend/app/utils/autocomplete_service.py
  - 实现get_suggestions方法
  - 优先用户搜索历史
  - 包含全局热门搜索
  - 包含学术词库术语
  - 200ms响应时间要求
  - 实现/autocomplete端点
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

- [ ]* 22.1 编写自动补全服务的属性测试
  - **Property 39: 自动补全响应时间**
  - **Validates: Requirements 13.1, 13.5**

- [ ] 23. 实现跨领域研究机会发现
  - 在backend/app/engines/recommendation_engine.py添加find_cross_domain_opportunities方法
  - 识别多分类论文
  - 分析跨领域引用关系
  - 优先最近24个月的论文
  - 生成跨领域连接说明
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [ ]* 23.1 编写跨领域发现的属性测试
  - **Property 40: 跨领域论文识别**
  - **Validates: Requirements 14.2**

- [ ] 24. 集成所有搜索优化到API
  - 修改backend/app/api/literature.py
  - 集成查询解析器
  - 集成过滤管理器
  - 集成相关性评分器
  - 更新响应格式
  - _Requirements: 9.1-9.7, 11.1-11.7, 12.1-12.7_

- [ ] 25. 添加缓存监控和管理端点
  - 在backend/app/api/platform.py添加/cache/stats端点
  - 实现缓存命中率统计
  - 实现LRU驱逐逻辑
  - 实现缓存清理端点
  - _Requirements: 4.6, 4.7_

- [ ]* 25.1 编写缓存监控的属性测试
  - **Property 12: LRU缓存驱逐**
  - **Property 13: 缓存命中率计算**
  - **Validates: Requirements 4.6, 4.7**

- [ ] 26. Final Checkpoint - 完整系统验证
  - 确保所有测试通过（单元测试 + 属性测试）
  - 验证缓存命中率 > 60%
  - 验证P95响应时间 < 2秒
  - 验证降级率 < 20%
  - 进行端到端测试
  - 询问用户是否有问题

## Notes

- 标记为`*`的任务是可选的属性测试任务，可以跳过以加快MVP开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- Checkpoint任务确保增量验证，及时发现问题
- 属性测试使用Hypothesis库，每个测试最少100次迭代
- 所有代码应与现有的FastAPI + SQLAlchemy架构兼容
- Redis缓存应支持本地开发（fakeredis）和生产环境（真实Redis）
