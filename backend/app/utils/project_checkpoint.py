"""项目阶段验收器（P4 Final Checkpoint）。"""

from __future__ import annotations

from typing import Dict

from app.engines.recommendation_engine import recommendation_engine
from app.engines.search_engine import search_engine
from app.utils import autocomplete_service, cache_manager, filter_manager, keyword_expander, query_parser, relevance_scorer, search_history_manager
from app.utils.quality_monitor import quality_monitor


class ProjectCheckpoint:
    @staticmethod
    def _has_attr(obj, name: str) -> bool:
        return hasattr(obj, name) and callable(getattr(obj, name))

    def check_p0(self) -> Dict[str, bool]:
        return {
            "cache_manager": self._has_attr(cache_manager.cache_manager, "get") and self._has_attr(cache_manager.cache_manager, "set"),
            "search_fallback": self._has_attr(search_engine, "search_with_fallback"),
            "keyword_expansion": self._has_attr(keyword_expander, "expand_keywords"),
        }

    def check_p1(self) -> Dict[str, bool]:
        return {
            "recommendations": self._has_attr(recommendation_engine, "generate_recommendations"),
            "learning_path": self._has_attr(recommendation_engine, "generate_learning_path"),
            "feedback_loop": self._has_attr(recommendation_engine, "record_recommendation_feedback"),
        }

    def check_p2(self) -> Dict[str, bool]:
        return {
            "query_parser": self._has_attr(query_parser.query_parser, "parse_query"),
            "filter_manager": self._has_attr(filter_manager.filter_manager, "apply_filters"),
            "relevance_scorer": self._has_attr(relevance_scorer.relevance_scorer, "calculate_relevance"),
            "autocomplete": self._has_attr(autocomplete_service.autocomplete_service, "get_suggestions"),
            "search_history": self._has_attr(search_history_manager.search_history_manager, "get_recent"),
            "hot_searches": self._has_attr(cache_manager.cache_manager, "get_hot_searches"),
        }

    def check_p3(self) -> Dict[str, bool]:
        return {
            "quality_metrics": self._has_attr(quality_monitor, "metrics"),
            "quality_check": self._has_attr(quality_monitor, "quality_check"),
            "cache_stats": self._has_attr(cache_manager.cache_manager, "get_stats"),
        }

    def check_p4(self) -> Dict[str, object]:
        p0 = self.check_p0()
        p1 = self.check_p1()
        p2 = self.check_p2()
        p3 = self.check_p3()

        quality = quality_monitor.quality_check()
        stages_ok = all(all(x.values()) for x in [p0, p1, p2, p3])

        return {
            "p0": p0,
            "p1": p1,
            "p2": p2,
            "p3": p3,
            "quality": quality,
            "all_core_stages_passed": stages_ok,
            "final_checkpoint_passed": stages_ok and bool(quality.get("all_passed", False)),
        }


project_checkpoint = ProjectCheckpoint()
