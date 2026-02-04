from fastapi.testclient import TestClient
from src.forecast.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/forecast")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Forecast Service is running"}