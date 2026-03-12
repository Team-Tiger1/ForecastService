import datetime
import os

import numpy as np
import pandas as pd
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
                'reservation_probability': round(reservation_probability * 100),
            },
            'collection': {
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

        # For local deployment if no api key is provided
        if not api_key:
            # Return mock data
            return "Sunny", 20.0

        postcode = postcode['postcode']
        url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={postcode}"

        response = requests.get(url).json()

        # Gets just the temperature and weather conditions from the JSON response
        temperature = response['current']['temp_c']
        weather = response['current']['condition']['text']

        return weather, temperature

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather API Error: {e}")


def optimise(input_data, db):
    """
    Determines the best prices, window, etc. for a bundle to sell
    :param input_df: Dataframe containing input data such as category, retail_price, weather, day, and time.
    :param db: Database session.
    :return: The best parameters to make the bundle collection/reservation as high as possible.
    """
    if not model_reservation or not model_collection:
        raise HTTPException(status_code=500, detail="Models not loaded")

    # Extract data from input_data
    product_id_list = input_data['product_id_list']
    category = input_data['category']
    weather = input_data['weather']
    temperature = input_data['temperature']
    vendor_id = input_data['vendor_id']

    try:
        # Get all unique product ids
        unique_product_ids = list(set(product_id_list))

        # Query database to get prices for each unique product
        query = text("SELECT product_id, retail_price FROM products WHERE product_id IN :ids")
        result = db.execute(query, {'ids': tuple(unique_product_ids)}).mappings().all()

        # Create map of product id to price
        product_price_map = {}
        for row in result:
            id = str(row['product_id'])
            price = float(row['retail_price'])
            product_price_map[id] = price

        # Calculate total price using map of product id to price
        retail_price = 0.0
        for product_id in product_id_list:
            retail_price += product_price_map[product_id]

        # If there is no products raise an error
        if retail_price == 0:
            raise HTTPException(status_code=404, detail="No valid products found to calculate price")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error calculating price: {e}")

    # Calculate day and time
    now = datetime.datetime.now().replace(second=0, microsecond=0)

    # Round to the next 30 minute
    if 0 < now.minute < 30:
        now = now.replace(minute=30)
    elif now.minute > 30:
        now = now.replace(minute=0) + datetime.timedelta(hours=1)

    # Current day and time
    day = now.strftime('%A')
    time = now.hour + (now.minute / 60.0)

    # List of days and current day to be used later
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    current_day_idx = days_of_week.index(day)

    # Creates lists to be made into combinations
    discounts = np.arange(0.25, 0.8, 0.05)
    lead_times = np.arange(0.5, 8.5, 0.5)
    window_lengths = np.arange(0.5, 8.5, 0.5)

    combinations = []

    for discount in discounts:
        # Calculates the price
        price = retail_price * (1 - discount)
        for lead_time in lead_times:

            # Checks if the lead_time will make the collection into the next day
            total_hours_ahead = time + lead_time
            days_to_shift = int(total_hours_ahead // 24)
            day = days_of_week[(current_day_idx + days_to_shift) % 7]

            time_of_day = int((time + lead_time) % 24)
            for window_length in window_lengths:
                # Combines options into individual combinations
                combinations.append({
                    'discount': discount,
                    'price': price,
                    'weather': weather,
                    'category': category,
                    'temperature': temperature,
                    'day': day,
                    'lead_time': lead_time,
                    'window_length': window_length,
                    'time_of_day': time_of_day,
                    'vendor_id': vendor_id
                })

    df = pd.DataFrame(combinations)

    try:
        # Tests combinations in model
        reservation_probability = model_reservation.predict_proba(df)[:, 1]
        collection_probability = model_collection.predict_proba(df)[:, 1]

        df['reservation_probability'] = reservation_probability
        df['collection_probability'] = collection_probability

        # Works out the probability of both reservation and collection occurring
        df['joint_probability'] = df['reservation_probability'] * df['collection_probability']

        # Expected price to determine best params
        df['expected_profit'] = df['price'] * df['joint_probability']

        # Gets the best combination
        best_index = df['expected_profit'].idxmax()
        best_params = df.loc[best_index]

        # Calculate the start and end times of the window to be returned
        collection_start = now + datetime.timedelta(hours=best_params['lead_time'])
        collection_end = collection_start + datetime.timedelta(hours=best_params['window_length'])

        discount = int(best_params['discount'] * 100)

        def create_time_phrase(total_hours):
            hours = int(total_hours)
            has_half_hour = (total_hours - hours) > 0

            if hours == 0 and has_half_hour:
                return "half an hour"
            elif hours == 1 and not has_half_hour:
                return "1 hour"
            elif has_half_hour:
                return f"{hours} and a half hours"
            else:
                return f"{hours} hours"

        lead_time = round(best_params['lead_time'] * 2) / 2
        window_length = round(best_params['window_length'] * 2) / 2

        window_length_phrase = create_time_phrase(window_length)
        lead_time_phrase = create_time_phrase(lead_time)
        time_text = f"in {lead_time_phrase} with a window length of {window_length_phrase}"

        optimised_reservation_probability = int(round(best_params['reservation_probability'] * 100))
        optimised_collection_probability = int(round(best_params['collection_probability'] * 100))

        explanation = (
            f"A discount of {discount}% maximises your profit while maintaining a high chance of reservation and collection. "
            f"Posting the bundle {time_text} will also increase the chances of this bundle being reserved and collected. "
            f"This configuration results in a {optimised_reservation_probability}% chance of a reservation and a {optimised_collection_probability}% chance of a successful collection."
        )

        return {
            'price': round(best_params['price'], 2),
            'collection_start': collection_start.strftime("%Y-%m-%d %H:%M:%S"),
            'collection_end': collection_end.strftime("%Y-%m-%d %H:%M:%S"),
            'reservation_probability': int(round(best_params['reservation_probability'] * 100)),
            'collection_probability': int(round(best_params['collection_probability'] * 100)),
            'explanation': explanation
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization Failed: {e}")
