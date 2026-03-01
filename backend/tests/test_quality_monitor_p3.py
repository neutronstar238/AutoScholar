from app.utils.quality_monitor import QualityMonitor


def test_quality_monitor_metrics_and_check():
    m = QualityMonitor()
    for v in [100, 120, 150, 90, 110]:
        m.record_search_latency(v)
        m.record_recommend_latency(v + 30)

    m.record_fallback(True)
    m.record_fallback(False)
    m.record_fallback(False)

    metrics = m.metrics()
    assert metrics["search_p95_ms"] > 0
    assert metrics["recommend_p95_ms"] > 0
    assert 0.0 <= metrics["fallback_rate"] <= 1.0

    check = m.quality_check()
    assert "all_passed" in check
    assert "checks" in check
