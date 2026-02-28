import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.skip(reason="Requires API key and full setup")
def test_research_endpoint():
    """Test research endpoint (requires setup)"""
    payload = {
        "query": "What is Python?",
        "session_id": "test-session"
    }
    response = client.post("/api/v2/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data

def test_history_endpoint_not_found():
    """Test history endpoint with non-existent session"""
    response = client.get("/api/v2/history/nonexistent-session")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0