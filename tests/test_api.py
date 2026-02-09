import pytest
import os
import time
from jose import jwt
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.main import app, get_db

client = TestClient(app, raise_server_exceptions=True)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret")
ALGORITHM = "HS256"
VENDOR_ID = "e27daa6e-3e67-4d51-8ac0-cc73c621fd40"
BUNDLE_ID = "c283ce75-8fac-4f62-8842-546bb7d3a7b8"


@pytest.fixture
def mock_db_session():
    session = MagicMock()

    mock_data = {
        "bundle_id": BUNDLE_ID,
        "vendor_id": VENDOR_ID,
        "collection_start": "2023-10-30 10:00:00",
        "posting_time": "2023-10-30 08:00:00",
        "collection_end": "2023-10-30 11:00:00",
        "retail_price": 20.0,
        "price": 10.0,
        "category": "DRINKS_BEVERAGES",
        "postcode": "SW1A 1AA",
        "name": "Test Vendor",
        "weather": "Rain",
        "temperature": 15.0
    }
    session.execute.return_value.mappings.return_value.first.return_value = mock_data

    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


@pytest.fixture
def token():
    payload = {
        "sub": VENDOR_ID,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def payload():
    return {
        "price": 11.0,
        "discount": 1.0,
        "lead_time": 5,
        "window_length": 5.0,
        "weather": "Heavy Rain",
        "category": "DRINKS_BEVERAGES",
        "day": "Monday",
        "time_of_day": 15
    }


def test_forecast_bundle_id(token, mock_db_session):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = client.get(f"/forecast/predict/{BUNDLE_ID}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "reservation" in data
    assert "collection" in data


def test_forecast_simulation(token, payload, mock_db_session):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = client.post("/forecast/simulate", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "reservation" in data
    assert "collection" in data