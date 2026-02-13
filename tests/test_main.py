from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    """
    Tests the application can start and respond to a basic request.
    """

    response = client.get("/forecast/actuator")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Forecast Service is running"}


