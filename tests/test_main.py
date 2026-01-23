# How to do the rest of the tests \/
# https://fastapi.tiangolo.com/tutorial/testing/#extended-fastapi-app-file
# Use "poetry run pytest" to run tests
from fastapi.testclient import TestClient

from src.forecast.main import app

client = TestClient(app)

def test_forecast():
    response = client.get("/forecast")
    assert response.status_code == 200
    assert response.json() == {"Prediction":"Prediction Here"}