"""用户画像管理器。

负责：
- 从用户历史行为中提取研究兴趣关键词
- 为用户输入框提供兴趣关键词建议
- 从搜索和阅读行为更新用户兴趣
- 维护用户兴趣权重（最多20个关键词）

Requirements: 5.1, 5.2, 5.4, 5.5
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from app.storage.local_storage import local_storage


class InterestKeyword:
    """兴趣关键词数据类"""
    
    def __init__(self, keyword: str, weight: float):
        self.keyword = keyword
        self.weight = weight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "weight": round(self.weight, 4)
        }


class InterestSuggestion:
    """兴趣建议数据类"""
    
    def __init__(
        self,
        keyword: str,
        weight: float,
        source: str,
        description: Optional[str] = None
    ):
        self.keyword = keyword
        self.weight = weight
        self.source = source
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "weight": round(self.weight, 4),
            "source": self.source,
            "description": self.description
        }


class UserProfileManager:
    """管理用户兴趣画像，提供兴趣推荐和提取"""
    
    def __init__(self, max_keywords: int = 20):
        """初始化用户画像管理器。
        
        Args:
            max_keywords: 最大兴趣关键词数量（默认20，符合需求5.5）
        """
        self.max_keywords = max_keywords
    
    @staticmethod
    def _normalize_keyword(text: str) -> str:
        """标准化关键词，确保一致的大小写处理。
        
        Args:
            text: 输入文本
            
        Returns:
            标准化的关键词（小写，保留中文字符）
        """
        if not text:
            return ""
        
        # 使用Unicode标准化，保留中文字符
        import unicodedata
        # 先进行Unicode标准化
        normalized = unicodedata.normalize('NFKC', text)
        # 转为小写（支持中文）
        return normalized.lower().strip()
    
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """将文本分词为关键词列表。
        
        支持中英文混合分词：
        - 英文：按空格和标点分词
        - 中文：使用jieba分词
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表（标准化，长度>=2）
        """
        if not text:
            return []
        
        # 尝试导入jieba进行中文分词
        try:
            import jieba
            # 检测是否包含中文
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
            
            if has_chinese:
                # 使用jieba分词处理中文
                tokens = []
                # 先用jieba分词
                words = jieba.cut(text.lower())
                for word in words:
                    word = word.strip()
                    # 过滤掉长度小于2的词和纯标点
                    if len(word) >= 2 and not re.match(r'^[^\w\u4e00-\u9fff]+$', word):
                        tokens.append(UserProfileManager._normalize_keyword(word))
                return [t for t in tokens if t]  # 过滤空字符串
            else:
                # 纯英文，使用正则分词
                tokens = re.split(r"[^\w]+", text)
                normalized_tokens = []
                for token in tokens:
                    if len(token) >= 2:
                        normalized = UserProfileManager._normalize_keyword(token)
                        if normalized:
                            normalized_tokens.append(normalized)
                return normalized_tokens
        
        except ImportError:
            # 如果jieba未安装，使用简单的正则分词
            logger.warning("jieba未安装，使用简单分词。建议安装: pip install jieba")
            tokens = re.split(r"[^\w\u4e00-\u9fff]+", text)
            normalized_tokens = []
            for token in tokens:
                if len(token) >= 2:
                    normalized = UserProfileManager._normalize_keyword(token)
                    if normalized:
                        normalized_tokens.append(normalized)
            return normalized_tokens
    
    @staticmethod
    def _calculate_recency_factor(last_activity: datetime) -> float:
        """计算时间衰减因子。
        
        公式：recency_factor = 0.9 ^ (days_since_last_activity / 30)
        最近30天权重1.0，每30天衰减10%
        
        Args:
            last_activity: 最后活动时间
            
        Returns:
            时间衰减因子 (0.0-1.0)
        """
        days_since = (datetime.utcnow() - last_activity).days
        return 0.9 ** (days_since / 30.0)
    
    async def extract_interests(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[InterestKeyword]:
        """从用户历史行为中提取研究兴趣关键词。
        
        提取策略：
        1. 从搜索历史中提取高频关键词
        2. 从阅读论文中提取主题和分类
        3. 从正向反馈中提取相关主题
        4. 按权重排序，返回top N
        
        权重计算公式：
        interest_weight = (
            search_frequency * 0.4 +      # 搜索频率
            reading_count * 0.3 +          # 阅读次数
            positive_feedback * 0.2 +      # 正向反馈
            recency_factor * 0.1           # 时间衰减因子
        )
        
        Args:
            user_id: 用户ID
            limit: 返回的兴趣关键词数量
            
        Returns:
            兴趣关键词列表，按权重降序排列
            
        Validates: Requirements 5.1
        """
        try:
            # 从本地存储获取用户兴趣
            interests = await local_storage.get_user_interests(user_id, limit=limit)
            
            if not interests:
                # 如果没有存储的兴趣，从搜索历史中提取
                logger.info(f"用户 {user_id} 没有存储的兴趣，从搜索历史提取")
                return await self._extract_from_search_history(user_id, limit)
            
            return [
                InterestKeyword(keyword=row['keyword'], weight=float(row['weight']))
                for row in interests
            ]
        
        except Exception as e:
            logger.error(f"提取用户兴趣失败: {e}")
            return []
    
    async def _extract_from_search_history(
        self,
        user_id: int,
        limit: int
    ) -> List[InterestKeyword]:
        """从搜索历史中提取兴趣关键词。
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            
        Returns:
            兴趣关键词列表
        """
        try:
            # 获取最近90天的搜索历史
            searches = await local_storage.get_search_history(user_id, days=90)
            
            if not searches:
                return []
            
            # 统计关键词频率
            keyword_counts = Counter()
            keyword_last_seen = {}
            
            for search in searches:
                tokens = self._tokenize(search['query'])
                created_at = datetime.fromisoformat(search['created_at'])
                
                for token in tokens:
                    keyword_counts[token] += 1
                    if token not in keyword_last_seen:
                        keyword_last_seen[token] = created_at
            
            # 计算权重（搜索频率 * 时间衰减）
            interests = []
            for keyword, count in keyword_counts.most_common(limit):
                recency_factor = self._calculate_recency_factor(keyword_last_seen[keyword])
                # 简化权重：搜索频率 * 0.4 + 时间衰减 * 0.1
                weight = count * 0.4 + recency_factor * 0.1
                interests.append(InterestKeyword(keyword=keyword, weight=weight))
            
            return interests
        
        except Exception as e:
            logger.error(f"从搜索历史提取兴趣失败: {e}")
            return []
    
    async def suggest_interests_for_input(
        self,
        user_id: int,
        current_input: str = "",
        limit: int = 10
    ) -> List[InterestSuggestion]:
        """为用户输入框提供兴趣关键词建议。
        
        用于前端输入框的自动补全和推荐。
        
        Args:
            user_id: 用户ID
            current_input: 用户当前输入的文本（用于过滤）
            limit: 建议数量
            
        Returns:
            建议列表，包含关键词、权重、来源说明
        """
        try:
            suggestions = []
            
            # 1. 从用户兴趣中获取建议
            interests = await local_storage.get_user_interests(user_id, limit=limit)
            
            for interest in interests:
                keyword = interest['keyword']
                # 如果有当前输入，过滤匹配的关键词
                if current_input and current_input.lower() not in keyword.lower():
                    continue
                
                weight = float(interest['weight'])
                suggestions.append(
                    InterestSuggestion(
                        keyword=keyword,
                        weight=weight,
                        source="user_profile",
                        description=f"您的研究兴趣（权重: {weight:.2f}）"
                    )
                )
            
            # 2. 如果建议不足，从搜索历史补充
            if len(suggestions) < limit:
                remaining = limit - len(suggestions)
                history_suggestions = await self._get_suggestions_from_history(
                    user_id, current_input, remaining
                )
                suggestions.extend(history_suggestions)
            
            return suggestions[:limit]
        
        except Exception as e:
            logger.error(f"获取兴趣建议失败: {e}")
            return []
    
    async def _get_suggestions_from_history(
        self,
        user_id: int,
        current_input: str,
        limit: int
    ) -> List[InterestSuggestion]:
        """从搜索历史中获取建议。"""
        try:
            # 获取搜索历史（按查询分组统计）
            history_items = await local_storage.get_search_history_grouped(user_id, limit=limit * 2)
            
            suggestions = []
            for item in history_items:
                query = item['query']
                count = item['count']
                
                # 如果有当前输入，过滤匹配的查询
                if current_input and current_input.lower() not in query.lower():
                    continue
                
                suggestions.append(
                    InterestSuggestion(
                        keyword=query,
                        weight=float(count),
                        source="search_history",
                        description=f"您搜索过 {count} 次"
                    )
                )
                
                if len(suggestions) >= limit:
                    break
            
            return suggestions
        
        except Exception as e:
            logger.error(f"从搜索历史获取建议失败: {e}")
            return []
    
    async def update_interest_from_search(
        self,
        user_id: int,
        query: str
    ) -> None:
        """从搜索行为更新用户兴趣。
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            
        Validates: Requirements 5.1
        """
        try:
            # 分词提取关键词
            keywords = self._tokenize(query)
            
            for keyword in keywords:
                # 查询是否已存在该兴趣
                existing = await local_storage.get_user_interest_by_keyword(user_id, keyword)
                
                if existing:
                    # 更新权重：搜索频率增加
                    new_weight = float(existing['weight']) + 0.4
                    await local_storage.update_user_interest(
                        user_id,
                        keyword,
                        {
                            'weight': str(new_weight),
                            'last_updated': datetime.utcnow().isoformat()
                        }
                    )
                else:
                    # 创建新兴趣
                    await local_storage.create_user_interest({
                        'user_id': user_id,
                        'keyword': keyword,
                        'weight': 0.4,  # 初始搜索权重
                        'last_updated': datetime.utcnow().isoformat()
                    })
            
            # 维护最多20个关键词
            await self._trim_interests(user_id)
            
            logger.debug(f"更新用户 {user_id} 搜索兴趣: {keywords}")
        
        except Exception as e:
            logger.error(f"更新搜索兴趣失败: {e}")
    
    async def update_interest_from_reading(
        self,
        user_id: int,
        paper_id: str,
        categories: List[str]
    ) -> None:
        """从阅读行为更新用户兴趣。
        
        Args:
            user_id: 用户ID
            paper_id: 论文ID
            categories: 论文分类列表
            
        Validates: Requirements 5.2
        """
        try:
            # 将分类作为兴趣关键词
            for category in categories:
                # 清理分类名称并标准化
                category_normalized = self._normalize_keyword(category)
                if not category_normalized:
                    continue
                
                # 查询是否已存在该兴趣
                existing = await local_storage.get_user_interest_by_keyword(user_id, category_normalized)
                
                if existing:
                    # 更新权重：阅读次数增加
                    new_weight = float(existing['weight']) + 0.3
                    await local_storage.update_user_interest(
                        user_id,
                        category_normalized,
                        {
                            'weight': str(new_weight),
                            'last_updated': datetime.utcnow().isoformat()
                        }
                    )
                else:
                    # 创建新兴趣
                    await local_storage.create_user_interest({
                        'user_id': user_id,
                        'keyword': category_normalized,
                        'weight': 0.3,  # 初始阅读权重
                        'last_updated': datetime.utcnow().isoformat()
                    })
            
            # 维护最多20个关键词
            await self._trim_interests(user_id)
            
            logger.debug(f"更新用户 {user_id} 阅读兴趣: {categories}")
        
        except Exception as e:
            logger.error(f"更新阅读兴趣失败: {e}")
    
    async def update_interest_from_feedback(
        self,
        user_id: int,
        keywords: List[str],
        feedback_type: str
    ) -> None:
        """从用户反馈更新兴趣权重。
        
        Args:
            user_id: 用户ID
            keywords: 相关关键词列表
            feedback_type: 反馈类型（helpful/not_helpful）
            
        Validates: Requirements 5.4
        """
        try:
            # 根据反馈类型确定权重调整
            weight_delta = 0.1 if feedback_type == "helpful" else -0.15
            
            for keyword in keywords:
                # 标准化关键词
                keyword_normalized = self._normalize_keyword(keyword)
                if not keyword_normalized:
                    continue
                
                # 查询是否已存在该兴趣
                existing = await local_storage.get_user_interest_by_keyword(user_id, keyword_normalized)
                
                if existing:
                    # 更新权重
                    new_weight = max(0.0, float(existing['weight']) + weight_delta)
                    await local_storage.update_user_interest(
                        user_id,
                        keyword_normalized,
                        {
                            'weight': str(new_weight),
                            'last_updated': datetime.utcnow().isoformat()
                        }
                    )
                else:
                    # 如果是正向反馈，创建新兴趣
                    if feedback_type == "helpful":
                        await local_storage.create_user_interest({
                            'user_id': user_id,
                            'keyword': keyword_normalized,
                            'weight': 0.1,  # 正向反馈初始权重
                            'last_updated': datetime.utcnow().isoformat()
                        })
            
            # 维护最多20个关键词
            await self._trim_interests(user_id)
            
            logger.debug(f"更新用户 {user_id} 反馈兴趣: {keywords}, 类型: {feedback_type}")
        
        except Exception as e:
            logger.error(f"更新反馈兴趣失败: {e}")
    
    async def _trim_interests(
        self,
        user_id: int
    ) -> None:
        """维护用户兴趣关键词数量上限（最多20个）。
        
        删除权重最低的关键词。
        
        Validates: Requirements 5.5
        """
        try:
            # 查询用户所有兴趣
            interests = await local_storage.get_user_interests(user_id)
            
            # 如果超过最大数量，删除权重最低的
            if len(interests) > self.max_keywords:
                to_delete = interests[self.max_keywords:]
                ids_to_delete = [int(row['id']) for row in to_delete]
                await local_storage.delete_user_interests_by_ids(ids_to_delete)
                
                logger.info(f"用户 {user_id} 兴趣关键词超过 {self.max_keywords}，删除了 {len(to_delete)} 个低权重关键词")
        
        except Exception as e:
            logger.error(f"维护兴趣关键词数量失败: {e}")


# 全局实例
user_profile_manager = UserProfileManager()
