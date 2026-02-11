import os
import requests
import joblib
from fastapi import HTTPException
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.join(BASE_DIR, "ml")

try:
    model_reservation = joblib.load(os.path.join(ML_DIR, "pipeline_reservation.pkl"))
    model_collection = joblib.load(os.path.join(ML_DIR, "pipeline_collection.pkl"))
    print("Models loaded successfully")
except Exception as e:
    print(f"Could not load models: {e}")
    model_reservation = None
    model_collection = None


def predict(input_df):
    if not model_reservation or not model_collection:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        reservation_prediction = bool(model_reservation.predict(input_df)[0])
        reservation_probability = float(model_reservation.predict_proba(input_df)[0][1])

        collection_prediction = bool(model_collection.predict(input_df)[0])
        collection_probability = float(model_collection.predict_proba(input_df)[0][1])

        return {
            'reservation': {
                'reservation_prediction': reservation_prediction,
                'reservation_probability': round(reservation_probability * 100),
            },
            'collection': {
                'collection_prediction': collection_prediction,
                'collection_probability': round(collection_probability * 100),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_current_weather(vendor_id, db):
    try:
        query = text("SELECT postcode FROM vendor WHERE vendor_id = :vid")
        postcode = db.execute(query, {'vid': vendor_id}).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

    if not postcode:
        raise HTTPException(status_code=404, detail="Postcode not found")

    try:
        api_key = os.getenv("WEATHER_API_KEY")
        postcode = postcode['postcode']
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={postcode}"

        response = requests.get(url).json()

        temperature = response['current']['temp_c']
        weather = response['current']['condition']['text']

        return weather, temperature

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather API Error: {e}")