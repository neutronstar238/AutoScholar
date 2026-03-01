from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.platform import router as platform_router
from app.utils.ops_center import OpsCenter
from app.utils.quality_monitor import quality_monitor


def test_ops_center_generates_and_acks_alerts():
    center = OpsCenter()

    for _ in range(5):
        quality_monitor.record_search_latency(3000)
        quality_monitor.record_recommend_latency(3100)
        quality_monitor.record_fallback(True)

    result = center.run_audit()
    assert result["status"] == "degraded"
    assert len(result["new_alerts"]) >= 1

    alerts = center.get_alerts(active_only=True)
    assert len(alerts) >= 1

    aid = alerts[0]["id"]
    assert center.acknowledge(aid) is True


def test_platform_ops_endpoints():
    app = FastAPI()
    app.include_router(platform_router, prefix="/api/v1/platform")
    client = TestClient(app)

    audit = client.post('/api/v1/platform/ops/audit')
    assert audit.status_code == 200
    body = audit.json()
    assert body.get('success') is True
    assert 'status' in body

    alerts = client.get('/api/v1/platform/ops/alerts')
    assert alerts.status_code == 200
    assert alerts.json().get('success') is True

    status = client.get('/api/v1/platform/ops/status')
    assert status.status_code == 200
    assert status.json().get('success') is True
