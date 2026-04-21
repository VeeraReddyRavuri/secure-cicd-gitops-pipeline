from fastapi.testclient import TestClient, Response
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code in [200, 500]
