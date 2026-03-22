import pytest
import time
import jwt
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.main import app, get_db
from src.auth import SECRET_KEY, ALGORITHM

# Initialises the test client and if a test fails a traceback will be given rather than just returning a 500 status code
client = TestClient(app, raise_server_exceptions=True)

# IDs fixed to ensure reproducibility
VENDOR_ID = "e27daa6e-3e67-4d51-8ac0-cc73c621fd40"
BUNDLE_ID = "c283ce75-8fac-4f62-8842-546bb7d3a7b8"


@pytest.fixture
def mock_db_session():
    """
    Creates a mock database session for the tests.
    """

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
    }
    session.execute.return_value.mappings.return_value.first.return_value = mock_data
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.clear()


@pytest.fixture
def token():
    """
    Generates a valid JWT token signed with the secret key.
    :return: The JWT token.
    """
    payload = {"sub": VENDOR_ID, "exp": time.time() + 3600}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def payload():
    """
    Predetermined input data for the simulation endpoint.
    :return: Dictionary of input data.
    """
    return {
        "price": 11.0,
        "discount": 0.5,
        "lead_time": 5.0,
        "window_length": 5.0,
        "weather": "Heavy rain at times",
        "category": "DRINKS_BEVERAGES",
        "day": "Monday",
        "time_of_day": 15.0,
        "temperature": 15.0
    }


@pytest.fixture
def optimise_payload():
    """
    Predetermined input data for the optimisation endpoint.
    :return: Dictionary of input data.
    """

    return {
        "product_id_list": [
            "7bf6bc21-0959-455b-9785-69a69bbbe0c9",
            "7bf6bc21-0959-455b-9785-69a69bbbe0c9",
            "b059eae9-f795-492e-9c6e-1161ca953dd2"
        ],
        "category": "READY_MEALS_HOT_FOOD"
    }


def test_forecast_bundle_id(token, mock_db_session):
    """
    Tests the GET /predict/{bundle_id} endpoint.
    :param token: The JWT token.
    :param mock_db_session: The mock database session.
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Patch 'get_current_weather' to set the weather rather use the API.
    with patch("src.main.get_current_weather", return_value=("Sunny", 25.0)):
        response = client.get(f"/forecast/predict/{BUNDLE_ID}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Ensure the ML model output is present
    assert "bundle_id" in data
    assert data["bundle_id"] == BUNDLE_ID

    assert "reservation" in data
    assert "reservation_probability" in data["reservation"]

    assert "collection" in data
    assert "collection_probability" in data["collection"]


def test_forecast_simulation(token, payload, mock_db_session):
    """
    Tests the GET /simulate endpoint.
    :param token: The JWT token.
    :param payload: The predetermined payload.
    :param mock_db_session: The database session.
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = client.post("/forecast/simulate", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Ensure the ML model output is present
    assert "reservation" in data
    assert "reservation_probability" in data["reservation"]

    assert "collection" in data
    assert "collection_probability" in data["collection"]


def test_forecast_optimisation(token, optimise_payload, mock_db_session):
    """
    Tests the POST /forecast/optimise endpoint.
    :param token: The JWT token.
    :param optimise_payload: The predetermined payload.
    :param mock_db_session: The database session.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    mock_products = [
        {"product_id": "7bf6bc21-0959-455b-9785-69a69bbbe0c9", "retail_price": 5.0},
        {"product_id": "b059eae9-f795-492e-9c6e-1161ca953dd2", "retail_price": 10.0}
    ]

    mock_db_session.execute.return_value.mappings.return_value.all.return_value = mock_products

    with patch("src.main.get_current_weather", return_value=("Cloudy", 18.0)):
        response = client.post("/forecast/optimise", json=optimise_payload, headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Ensure the optimisation output is correct
    assert "price" in data
    assert "collection_start" in data
    assert "collection_end" in data
    assert "reservation_probability" in data
    assert "collection_probability" in data
    assert "explanation" in data
