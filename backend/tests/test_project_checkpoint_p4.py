from app.utils.project_checkpoint import ProjectCheckpoint
from app.utils.quality_monitor import QualityMonitor


def test_project_checkpoint_stages_have_required_capabilities():
    chk = ProjectCheckpoint()
    p0 = chk.check_p0()
    p1 = chk.check_p1()
    p2 = chk.check_p2()
    p3 = chk.check_p3()

    assert all(p0.values())
    assert all(p1.values())
    assert all(p2.values())
    assert all(p3.values())


def test_quality_monitor_threshold_logic_for_p4():
    m = QualityMonitor()
    for x in [80, 100, 120, 150, 180]:
        m.record_search_latency(x)
        m.record_recommend_latency(x + 100)
    m.record_fallback(False)
    m.record_fallback(False)
    m.record_fallback(True)

    result = m.quality_check()
    assert result["checks"]["search_p95_lt_2000ms"] is True
    assert result["checks"]["recommend_p95_lt_2000ms"] is True
    assert result["checks"]["fallback_rate_lt_20pct"] is False
