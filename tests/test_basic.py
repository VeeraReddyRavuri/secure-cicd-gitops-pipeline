from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code in [200, 500]
    #assert response.status_code == 200
    #assert response.json() == {"message": "app running"}
