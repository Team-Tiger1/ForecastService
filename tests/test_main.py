from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
<<<<<<< HEAD
    """
    Tests the application can start and respond to a basic request.
    """

    response = client.get("/forecast/actuator")
=======
    response = client.get("/forecast")
>>>>>>> 2199e9c1f5f61fc99eb47626b9746022efb58fda

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Forecast Service is running"}


