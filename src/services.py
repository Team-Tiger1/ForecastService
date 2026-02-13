import os
import requests
import joblib
from fastapi import HTTPException
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Location of the models
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.join(BASE_DIR, "ml")

# Attempting to load the pre-trained ML pipelines.
try:
    model_reservation = joblib.load(os.path.join(ML_DIR, "pipeline_reservation.pkl"))
    model_collection = joblib.load(os.path.join(ML_DIR, "pipeline_collection.pkl"))
    print("Models loaded successfully")
except Exception as e:
    print(f"Could not load models: {e}")
    model_reservation = None
    model_collection = None


def predict(input_df):
    """
    Runs input_df through both the reservation and collection models and returns a prediction for each.
    :param input_df: Dataframe containing input data such as discount, price, weather etc.
    :return: A nested dictionary containing boolean predictions for both reservation and collection and their corresponding confidence.
    """
    if not model_reservation or not model_collection:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        # Passes the input dataframe to the previously loaded models
        reservation_prediction = bool(model_reservation.predict(input_df)[0])

        # Returns an array [[prob_false, prob_true]] therefore get just prob_true
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
    """
    Gets the weather data for a given vendors location.
    :param vendor_id: ID of the vendor.
    :param db: Database session.
    :return: Condition and temperature data.
    """

    try:
        # Gets the vendors postcode from the vendors table using a parameterised query
        query = text("SELECT postcode FROM vendor WHERE vendor_id = :vid")
        postcode = db.execute(query, {'vid': vendor_id}).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {e}")

    if not postcode:
        raise HTTPException(status_code=404, detail="Postcode not found")

    try:
        # Gets the weather for the vendors location using the weather API
        api_key = os.getenv("WEATHER_API_KEY")
        postcode = postcode['postcode']
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={postcode}"

        response = requests.get(url).json()

        # Gets just the temperature and weather conditions from the JSON response
        temperature = response['current']['temp_c']
        weather = response['current']['condition']['text']

        return weather, temperature

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather API Error: {e}")