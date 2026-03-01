"""运维审计中心（P5）。"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from itertools import count
from typing import Dict, List

from app.utils.cache_manager import cache_manager
from app.utils.project_checkpoint import project_checkpoint
from app.utils.quality_monitor import quality_monitor


@dataclass
class OpsAlert:
    id: int
    level: str
    code: str
    message: str
    created_at: str
    acknowledged: bool = False


class OpsCenter:
    def __init__(self):
        self._alerts: List[OpsAlert] = []
        self._id_counter = count(1)

    def _emit(self, level: str, code: str, message: str) -> OpsAlert:
        alert = OpsAlert(
            id=next(self._id_counter),
            level=level,
            code=code,
            message=message,
            created_at=datetime.utcnow().isoformat(),
        )
        self._alerts.append(alert)
        return alert

    def run_audit(self) -> Dict[str, object]:
        quality = quality_monitor.quality_check()
        checkpoint = project_checkpoint.check_p4()
        cache_stats = cache_manager.get_stats()

        created: List[Dict[str, object]] = []

        if not quality["checks"].get("search_p95_lt_2000ms", True):
            created.append(asdict(self._emit("warning", "SEARCH_P95_HIGH", "检索 P95 超过 2000ms")))
        if not quality["checks"].get("recommend_p95_lt_2000ms", True):
            created.append(asdict(self._emit("warning", "RECOMMEND_P95_HIGH", "推荐 P95 超过 2000ms")))
        if not quality["checks"].get("fallback_rate_lt_20pct", True):
            created.append(asdict(self._emit("critical", "FALLBACK_RATE_HIGH", "降级率超过 20%")))

        if not checkpoint.get("all_core_stages_passed", False):
            created.append(asdict(self._emit("critical", "STAGE_CHECK_FAILED", "P0-P3 能力巡检失败")))

        if cache_stats.get("hit_rate", 0.0) < 0.6 and (cache_stats.get("hits", 0) + cache_stats.get("misses", 0)) >= 10:
            created.append(asdict(self._emit("warning", "CACHE_HIT_LOW", "缓存命中率低于 60%")))

        status = "healthy" if not created else "degraded"
        return {
            "status": status,
            "quality": quality,
            "checkpoint": checkpoint,
            "cache": cache_stats,
            "new_alerts": created,
        }

    def get_alerts(self, active_only: bool = False) -> List[Dict[str, object]]:
        alerts = self._alerts
        if active_only:
            alerts = [a for a in alerts if not a.acknowledged]
        return [asdict(a) for a in alerts]

    def acknowledge(self, alert_id: int) -> bool:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False


ops_center = OpsCenter()
