from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_status_endpoint_reports_provider_shape():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"provider", "model", "key_env", "has_key"}


def test_chat_rejects_empty_message():
    resp = client.post("/api/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_chat_without_key_returns_service_unavailable(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "google")
    resp = client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 503


def test_frontend_is_served_at_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "BD Knowledge Agent" in resp.text
