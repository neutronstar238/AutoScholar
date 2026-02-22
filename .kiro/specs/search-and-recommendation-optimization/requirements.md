# Requirements Document

## Introduction

本文档定义了AutoScholar学术研究AI助手系统的搜索与推荐优化功能需求。该功能旨在提升现有文献检索的性能、准确性和用户体验，同时改进研究方向推荐算法，提供更智能、个性化的学术研究支持。

**核心模块：研究方向推荐模块（backend/app/api/research.py）**

当前系统（V1.0.5）已实现基础的arXiv文献检索和简单的研究方向推荐功能。然而，研究方向推荐模块存在严重问题：当搜索无结果时直接返回"未找到相关论文"错误，导致功能完全不可用。本次优化的首要目标是修复研究方向推荐模块的鲁棒性问题，然后逐步引入高级搜索能力、缓存机制、个性化推荐和趋势分析等功能。

**影响范围：**
- 主要修改：backend/app/api/research.py（研究方向推荐API）
- 支持修改：backend/app/tools/literature_search.py（文献检索工具）
- 新增模块：缓存管理、趋势分析、用户画像等

**优先级说明：** 需求按优先级分为三个层级：
- **P0（关键）**: 需求1-4 - 修复研究方向推荐模块的核心问题，确保基本功能可用
- **P1（重要）**: 需求5-8 - 增强研究方向推荐质量和用户体验
- **P2（优化）**: 需求9-14 - 搜索功能优化和高级特性

## Glossary

- **Search_Engine**: 文献搜索引擎，负责处理用户查询并返回相关论文结果
- **Cache_Manager**: 缓存管理器，使用Redis存储和管理搜索结果缓存
- **Query_Parser**: 查询解析器，解析用户输入的搜索查询，支持布尔运算符
- **Recommendation_Engine**: 推荐引擎，基于多种算法生成研究方向推荐
- **User_Profile**: 用户画像，存储用户的搜索历史、阅读偏好和研究兴趣
- **Citation_Analyzer**: 引用分析器，分析论文引用关系和影响力
- **Trend_Analyzer**: 趋势分析器，识别研究领域的热点和发展趋势
- **Relevance_Scorer**: 相关性评分器，计算搜索结果与查询的相关性分数
- **Filter_Manager**: 过滤管理器，处理高级过滤条件（日期、作者、分类等）
- **Autocomplete_Service**: 自动补全服务，提供搜索建议和关键词补全
- **Feedback_Collector**: 反馈收集器，收集和处理用户对推荐结果的反馈
- **Fallback_Strategy**: 降级策略，在主要功能失败时提供替代方案

## Requirements

## P0 关键需求 - 推荐系统修复

### Requirement 1: 推荐系统鲁棒性增强

**User Story:** 作为用户，我希望推荐系统在各种情况下都能提供有价值的建议，而不是简单地返回"未找到相关论文"错误。

#### Acceptance Criteria

1. WHEN initial paper search returns no results, THE Recommendation_Engine SHALL try each interest keyword individually
2. WHEN individual keyword searches fail, THE Recommendation_Engine SHALL use related terms from academic thesaurus
3. WHEN no papers are found for user interests, THE Recommendation_Engine SHALL recommend trending papers from related categories
4. WHEN arXiv API is slow or unresponsive, THE Recommendation_Engine SHALL use cached trending papers from the past 7 days
5. THE Recommendation_Engine SHALL always return at least 3 recommendations unless all fallback strategies fail
6. WHEN providing fallback recommendations, THE Search_Engine SHALL clearly indicate they are general suggestions
7. THE Recommendation_Engine SHALL track fallback usage rate and alert administrators when it exceeds 20%

### Requirement 2: 搜索错误处理和降级策略

**User Story:** 作为用户，我希望即使在搜索失败或无结果的情况下，系统也能提供有用的替代方案，以便我能继续进行研究。

#### Acceptance Criteria

1. WHEN arXiv API returns no results, THE Search_Engine SHALL try alternative query formulations by expanding keywords
2. WHEN external API is unavailable, THE Search_Engine SHALL return cached results from previous similar queries
3. WHEN a search query is too specific and returns zero results, THE Search_Engine SHALL suggest broader search terms
4. WHEN network timeout occurs, THE Search_Engine SHALL retry the request up to 3 times with exponential backoff
5. WHEN all retry attempts fail, THE Search_Engine SHALL return a user-friendly error message with troubleshooting suggestions
6. THE Search_Engine SHALL log all search failures with query details for debugging
7. WHEN search returns fewer than 3 results, THE Search_Engine SHALL automatically broaden the query and merge results

### Requirement 3: 改进推荐算法基础实现

**User Story:** 作为研究人员，我希望获得基于引用关系和研究趋势的智能推荐，以便发现高质量和前沿的研究方向。

#### Acceptance Criteria

1. WHEN generating recommendations, THE Recommendation_Engine SHALL analyze citation networks of papers in user's interest areas
2. WHEN analyzing citations, THE Citation_Analyzer SHALL identify highly cited papers (top 10% by citation count)
3. WHEN analyzing trends, THE Trend_Analyzer SHALL identify topics with increasing publication frequency in the past 12 months
4. WHEN calculating recommendation score, THE Recommendation_Engine SHALL combine citation impact (weight 0.4), trend score (weight 0.3), and relevance (weight 0.3)
5. THE Recommendation_Engine SHALL recommend at least 3 and at most 10 research directions per request
6. WHEN insufficient data exists for citation analysis, THE Recommendation_Engine SHALL fall back to keyword-based recommendations
7. THE Recommendation_Engine SHALL provide confidence scores for each recommendation

### Requirement 4: 搜索结果缓存机制

**User Story:** 作为系统管理员，我希望实现搜索结果缓存，以便减少外部API调用次数，提升响应速度并降低系统负载。

#### Acceptance Criteria

1. WHEN a search query is executed, THE Cache_Manager SHALL check Redis for cached results before calling external APIs
2. WHEN cached results exist and are not expired, THE Search_Engine SHALL return cached results immediately
3. WHEN cached results do not exist, THE Cache_Manager SHALL store new results in Redis with a TTL of 3600 seconds
4. WHEN cache storage fails, THE Search_Engine SHALL continue operation and return results without caching
5. THE Cache_Manager SHALL use query string and filter parameters as cache key components
6. WHEN cache memory reaches 80% capacity, THE Cache_Manager SHALL evict least recently used entries
7. THE Cache_Manager SHALL provide cache hit rate metrics for monitoring

## P1 重要需求 - 推荐质量增强

### Requirement 5: 个性化推荐

**User Story:** 作为用户，我希望系统根据我的历史行为提供个性化推荐，以便发现与我研究兴趣最相关的内容。

#### Acceptance Criteria

1. WHEN a user has search history, THE User_Profile SHALL extract research interest keywords from past queries
2. WHEN a user has read papers, THE User_Profile SHALL track paper categories and topics as interest indicators
3. WHEN generating personalized recommendations, THE Recommendation_Engine SHALL prioritize topics matching user's interest profile
4. WHEN a user provides explicit feedback, THE User_Profile SHALL update interest weights accordingly
5. THE User_Profile SHALL maintain a maximum of 20 interest keywords with associated weights
6. WHEN a user is new (no history), THE Recommendation_Engine SHALL provide general trending recommendations
7. THE Recommendation_Engine SHALL refresh personalized recommendations daily based on updated user profile

### Requirement 6: 研究热度和趋势分析

**User Story:** 作为研究人员，我希望了解研究领域的热度和趋势，以便把握学术前沿和选择有潜力的研究方向。

#### Acceptance Criteria

1. WHEN analyzing trends, THE Trend_Analyzer SHALL calculate publication growth rate for each topic over the past 12 months
2. WHEN a topic has growth rate exceeding 20%, THE Trend_Analyzer SHALL classify it as "hot topic"
3. WHEN analyzing research heat, THE Trend_Analyzer SHALL consider both publication count and citation velocity
4. THE Trend_Analyzer SHALL provide trend visualization data including monthly publication counts
5. WHEN comparing topics, THE Trend_Analyzer SHALL normalize heat scores to a 0-100 scale
6. THE Trend_Analyzer SHALL update trend data weekly from arXiv API
7. WHEN trend data is unavailable, THE Search_Engine SHALL return cached trend analysis from previous week

### Requirement 7: 详细学习路径规划

**User Story:** 作为学生或新研究人员，我希望获得详细的学习路径建议，以便系统地掌握某个研究领域的知识。

#### Acceptance Criteria

1. WHEN generating learning path, THE Recommendation_Engine SHALL identify foundational papers in the target field
2. WHEN ordering learning materials, THE Recommendation_Engine SHALL sequence papers from basic to advanced based on citation relationships
3. WHEN creating learning path, THE Recommendation_Engine SHALL include survey papers as starting points
4. THE Recommendation_Engine SHALL organize learning path into 3-5 stages with clear progression
5. WHEN presenting learning path, THE Search_Engine SHALL provide estimated reading time for each stage
6. THE Recommendation_Engine SHALL include prerequisite knowledge requirements for each stage
7. WHEN a learning path has more than 20 papers, THE Recommendation_Engine SHALL prioritize the most essential 15 papers

### Requirement 8: 推荐结果反馈和调整

**User Story:** 作为用户，我希望能够对推荐结果提供反馈，以便系统不断改进推荐质量。

#### Acceptance Criteria

1. WHEN a user views a recommended paper, THE Feedback_Collector SHALL record the view event with timestamp
2. WHEN a user marks a recommendation as helpful, THE User_Profile SHALL increase the weight of related topics by 0.1
3. WHEN a user marks a recommendation as not helpful, THE User_Profile SHALL decrease the weight of related topics by 0.15
4. WHEN a user ignores a recommendation (no interaction), THE Feedback_Collector SHALL record it as neutral feedback
5. THE Recommendation_Engine SHALL use feedback data to adjust future recommendations within 24 hours
6. WHEN calculating recommendation quality, THE Feedback_Collector SHALL compute click-through rate and helpfulness ratio
7. THE Feedback_Collector SHALL provide feedback analytics to system administrators for algorithm tuning

## P2 优化需求 - 搜索功能增强

### Requirement 9: 多关键词搜索和布尔运算符支持

**User Story:** 作为研究人员，我希望能够使用多个关键词和布尔运算符进行精确搜索，以便快速找到符合特定条件的文献。

#### Acceptance Criteria

1. WHEN a user enters multiple keywords separated by spaces, THE Search_Engine SHALL treat them as AND operation by default
2. WHEN a user uses "AND" operator between keywords, THE Query_Parser SHALL return papers containing all specified keywords
3. WHEN a user uses "OR" operator between keywords, THE Query_Parser SHALL return papers containing any of the specified keywords
4. WHEN a user uses "NOT" operator before a keyword, THE Query_Parser SHALL exclude papers containing that keyword
5. WHEN a user combines multiple operators, THE Query_Parser SHALL evaluate them with correct precedence (NOT > AND > OR)
6. WHEN a user uses parentheses in query, THE Query_Parser SHALL respect grouping for operator precedence
7. WHEN a user enters an invalid query syntax, THE Search_Engine SHALL return a descriptive error message

### Requirement 10: 搜索历史记录和热门搜索

**User Story:** 作为用户，我希望查看我的搜索历史和系统热门搜索，以便快速重复之前的搜索或发现其他研究人员关注的话题。

#### Acceptance Criteria

1. WHEN a user performs a search, THE User_Profile SHALL record the query with timestamp in PostgreSQL
2. WHEN a user requests search history, THE Search_Engine SHALL return the most recent 50 queries for that user
3. WHEN calculating hot searches, THE Trend_Analyzer SHALL count query frequency across all users in the past 7 days
4. WHEN a user requests hot searches, THE Search_Engine SHALL return the top 10 most frequent queries
5. THE User_Profile SHALL store search history for a maximum of 90 days
6. WHEN a user deletes their search history, THE Search_Engine SHALL remove all history records for that user
7. THE Search_Engine SHALL exclude queries with fewer than 3 characters from hot search calculation

### Requirement 11: 高级过滤选项

**User Story:** 作为研究人员，我希望能够按日期范围、作者和分类过滤搜索结果，以便精确定位我需要的文献。

#### Acceptance Criteria

1. WHEN a user specifies a date range filter, THE Filter_Manager SHALL return only papers published within that range
2. WHEN a user specifies an author filter, THE Filter_Manager SHALL return only papers where the author name matches
3. WHEN a user specifies a category filter, THE Filter_Manager SHALL return only papers in the specified arXiv categories
4. WHEN multiple filters are applied, THE Filter_Manager SHALL return papers matching all filter conditions
5. WHEN a date range is invalid (start date after end date), THE Search_Engine SHALL return a validation error
6. THE Filter_Manager SHALL support partial author name matching (case-insensitive)
7. WHEN no papers match the filter criteria, THE Search_Engine SHALL return an empty result set with appropriate message

### Requirement 12: 搜索结果排序算法优化

**User Story:** 作为用户，我希望搜索结果按相关性智能排序，以便最相关的论文排在前面。

#### Acceptance Criteria

1. WHEN calculating relevance score, THE Relevance_Scorer SHALL consider keyword frequency in title with weight 3.0
2. WHEN calculating relevance score, THE Relevance_Scorer SHALL consider keyword frequency in abstract with weight 1.5
3. WHEN calculating relevance score, THE Relevance_Scorer SHALL consider paper recency with exponential decay factor 0.95 per year
4. WHEN calculating relevance score, THE Relevance_Scorer SHALL consider author reputation based on citation count
5. WHEN sorting results, THE Search_Engine SHALL order papers by relevance score in descending order
6. THE Relevance_Scorer SHALL normalize all scores to a range of 0.0 to 1.0
7. WHEN multiple papers have identical scores, THE Search_Engine SHALL use publication date as secondary sort criterion

### Requirement 13: 搜索建议和自动补全

**User Story:** 作为用户，我希望在输入搜索关键词时获得实时建议，以便更快地构建准确的搜索查询。

#### Acceptance Criteria

1. WHEN a user types at least 3 characters, THE Autocomplete_Service SHALL provide up to 10 keyword suggestions
2. WHEN generating suggestions, THE Autocomplete_Service SHALL prioritize user's own search history
3. WHEN generating suggestions, THE Autocomplete_Service SHALL include popular search terms from all users
4. WHEN generating suggestions, THE Autocomplete_Service SHALL include common academic terms from a predefined dictionary
5. THE Autocomplete_Service SHALL return suggestions within 200 milliseconds
6. WHEN a user selects a suggestion, THE Search_Engine SHALL execute the search with the selected term
7. THE Autocomplete_Service SHALL rank suggestions by relevance score combining frequency and recency

### Requirement 14: 跨领域研究机会发现

**User Story:** 作为研究人员，我希望发现跨学科的研究机会，以便探索创新的研究方向和合作可能性。

#### Acceptance Criteria

1. WHEN analyzing user interests, THE Recommendation_Engine SHALL identify papers that bridge multiple research categories
2. WHEN a paper belongs to multiple arXiv categories, THE Citation_Analyzer SHALL flag it as interdisciplinary
3. WHEN generating cross-domain recommendations, THE Recommendation_Engine SHALL find papers citing works from different fields
4. THE Recommendation_Engine SHALL recommend at least 2 cross-domain opportunities per request when available
5. WHEN presenting cross-domain opportunities, THE Search_Engine SHALL explain the connection between different fields
6. THE Recommendation_Engine SHALL prioritize recent cross-domain papers (published within 24 months)
7. WHEN no cross-domain opportunities exist, THE Recommendation_Engine SHALL return an empty list without error
