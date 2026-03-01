"""反馈采集器（P1）。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict


@dataclass
class FeedbackStats:
    views: int = 0
    helpful: int = 0
    not_helpful: int = 0
    ignore: int = 0


class FeedbackCollector:
    def __init__(self):
        self._stats: Dict[int, FeedbackStats] = defaultdict(FeedbackStats)

    def record_view(self, user_id: int) -> None:
        self._stats[user_id].views += 1

    def record_feedback(self, user_id: int, feedback: str) -> None:
        stat = self._stats[user_id]
        if feedback == "helpful":
            stat.helpful += 1
        elif feedback == "not_helpful":
            stat.not_helpful += 1
        else:
            stat.ignore += 1

    def calculate_metrics(self, user_id: int) -> Dict[str, float]:
        stat = self._stats[user_id]
        views = stat.views
        total_feedback = stat.helpful + stat.not_helpful + stat.ignore

        ctr = 0.0 if views <= 0 else min(1.0, total_feedback / views)
        helpful_ratio = 0.0 if total_feedback <= 0 else stat.helpful / total_feedback

        return {
            "views": float(views),
            "feedback_events": float(total_feedback),
            "ctr": round(ctr, 4),
            "helpfulness_ratio": round(helpful_ratio, 4),
        }


feedback_collector = FeedbackCollector()
