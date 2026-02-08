import requests
import os
import time
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "secret"

ALGORITHM = "HS256"
VENDOR_ID = "e27daa6e-3e67-4d51-8ac0-cc73c621fd40"
BUNDLE_ID = "c283ce75-8fac-4f62-8842-546bb7d3a7b8"
FORECAST_BASE_URL = "http://localhost:8000"


def generate_token():
    payload = {
        "sub": VENDOR_ID,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def output_response(response):
    if response.status_code == 200:
        data = response.json()

        reservation_prediction = data['reservation']['reservation_prediction']
        reservation_probability = data['reservation']['reservation_probability']

        collection_prediction = data['collection']['collection_prediction']
        collection_probability = data['collection']['collection_probability']

        print(f"Reservation Prediction: {reservation_prediction} ({reservation_probability}% Chance of Reservation)")
        print(f"Collection Prediction: {collection_prediction} ({collection_probability}% Chance of Collection)")
        print("SUCCESS")
    else:
        print(f"FAILED: {response.status_code}")
        print(f"Response: {response.text}")


def test_forecast_bundle_id(token):
    print("Test 1: Testing Prediction Based on Existing Bundle")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{FORECAST_BASE_URL}/forecast/predict/{BUNDLE_ID}"

    try:
        response = requests.get(url, headers=headers)
        output_response(response)

    except Exception as e:
        print(f"Connection Error: {e}")


def test_forecast_simulation(token, payload):
    print("Test 2: Testing Prediction Based on Simulation Data")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{FORECAST_BASE_URL}/forecast/simulate"

    try:
        response = requests.post(url, json=payload, headers=headers)
        output_response(response)

    except Exception as e:
        print(f"Connection Error: {e}")


if __name__ == "__main__":
    auth_token = generate_token()
    payload = {
        "price": 11.0,
        "discount": 1.0,
        "lead_time": 5,
        "window_length": 5.0,
        "weather": "Heavy Rain",
        "category": "DRINKS_BEVERAGES",
        "day": "Monday",
        "time_of_day": 15
    }

    test_forecast_bundle_id(auth_token)
    print("\n")
    test_forecast_simulation(auth_token, payload)
