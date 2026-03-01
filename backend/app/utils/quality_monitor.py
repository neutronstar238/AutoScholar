"""系统质量与性能监控（P3）。"""

from __future__ import annotations

from collections import deque
from statistics import quantiles
from typing import Deque, Dict


class QualityMonitor:
    def __init__(self):
        self._search_latencies_ms: Deque[float] = deque(maxlen=500)
        self._recommend_latencies_ms: Deque[float] = deque(maxlen=500)
        self._fallback_history: Deque[bool] = deque(maxlen=200)

    def record_search_latency(self, latency_ms: float) -> None:
        self._search_latencies_ms.append(max(0.0, float(latency_ms)))

    def record_recommend_latency(self, latency_ms: float) -> None:
        self._recommend_latencies_ms.append(max(0.0, float(latency_ms)))

    def record_fallback(self, is_fallback: bool) -> None:
        self._fallback_history.append(bool(is_fallback))

    @staticmethod
    def _p95(values: Deque[float]) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return round(values[0], 4)
        return round(quantiles(list(values), n=100)[94], 4)

    def fallback_rate(self) -> float:
        if not self._fallback_history:
            return 0.0
        return sum(1 for x in self._fallback_history if x) / len(self._fallback_history)

    def metrics(self) -> Dict[str, float]:
        return {
            "search_p95_ms": self._p95(self._search_latencies_ms),
            "recommend_p95_ms": self._p95(self._recommend_latencies_ms),
            "fallback_rate": round(self.fallback_rate(), 4),
            "search_samples": float(len(self._search_latencies_ms)),
            "recommend_samples": float(len(self._recommend_latencies_ms)),
            "fallback_samples": float(len(self._fallback_history)),
        }

    def quality_check(self) -> Dict[str, object]:
        m = self.metrics()
        checks = {
            "search_p95_lt_2000ms": m["search_p95_ms"] < 2000,
            "recommend_p95_lt_2000ms": m["recommend_p95_ms"] < 2000,
            "fallback_rate_lt_20pct": m["fallback_rate"] < 0.2,
        }
        return {
            "metrics": m,
            "checks": checks,
            "all_passed": all(checks.values()),
        }


quality_monitor = QualityMonitor()
