from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.platform import router as platform_router


def test_platform_checkpoint_endpoint_structure():
    app = FastAPI()
    app.include_router(platform_router, prefix="/api/v1/platform")
    client = TestClient(app)

    resp = client.get('/api/v1/platform/checkpoint/p4')
    assert resp.status_code == 200
    body = resp.json()
    assert body.get('success') is True
    assert 'p0' in body and 'p1' in body and 'p2' in body and 'p3' in body
    assert 'final_checkpoint_passed' in body
