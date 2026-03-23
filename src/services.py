import datetime
import os

import numpy as np
import pandas as pd
import requests
import joblib
from fastapi import HTTPException
from sqlalchemy import text
from dotenv import load_dotenv

import datetime
from sqlalchemy import text
from fastapi import HTTPException

CATEGORY_MAP = {
    'BREAD_BAKED_GOODS': 'Bread & Baked Goods',
    'SWEET_TREATS_DESSERTS': 'Sweet Treats & Desserts',
    'MEAT_PROTEIN': 'Meat & Protein',
    'FRUIT_VEGETABLES': 'Fruit & Vegetables',
    'DAIRY_EGGS': 'Dairy & Eggs',
    'READY_MEALS_HOT_FOOD': 'Ready Meals & Hot Food',
    'SNACKS_SAVOURY_ITEMS': 'Snacks & Savoury Items',
    'BREAKFAST_ITEMS': 'Breakfast Items',
    'VEGAN_VEGETARIAN': 'Vegan & Vegetarian',
    'DRINKS_BEVERAGES': 'Drinks & Beverages'
}

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
        raise HTTPException(status_code=500)

    try:
        # Returns an array [[prob_false, prob_true]] therefore get just prob_true
        reservation_probability = float(model_reservation.predict_proba(input_df)[0][1])

        collection_probability = float(model_collection.predict_proba(input_df)[0][1])

        return {
            'reservation': {
                'reservation_probability': round(reservation_probability * 100),
            },
            'collection': {
                'collection_probability': round(collection_probability * 100),
            }
        }

    except Exception:
        raise HTTPException(status_code=500)


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
        raise HTTPException(status_code=500)

    if not postcode:
        raise HTTPException(status_code=404)

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

        # Ensures API failure handled
        if response.status_code != 200:
            return "Sunny", 20.0

        # Gets just the temperature and weather conditions from the JSON response
        temperature = response['current']['temp_c']
        weather = response['current']['condition']['text']

        return weather, temperature

    except Exception:
        return "Sunny", 20.0


def optimise(input_data, db):
    """
    Determines the best prices, window, etc. for a bundle to sell
    :param input_data: Dataframe containing input data such as category, retail_price, weather, day, and time.
    :param db: Database session.
    :return: The best parameters to make the bundle collection/reservation as high as possible.
    """
    if not model_reservation or not model_collection:
        raise HTTPException(status_code=500)

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
            raise HTTPException(status_code=404)

    except Exception:
        raise HTTPException(status_code=500)

    # Calculate day and time
    now = datetime.datetime.now().replace(second=0, microsecond=0)

    # Round to the next 30 minute
    if 0 < now.minute < 30:
        now = now.replace(minute=30)
    elif now.minute > 30:
        now = now.replace(minute=0) + datetime.timedelta(hours=1)

    # Current time
    time = now.hour + (now.minute / 60.0)

    # Check the current time is not after 10 or before 6 and get the day
    if time > 22 or time < 6:
        if time > 22:
            now = (now + datetime.timedelta(days=1)).replace(hour=6, minute=0)
        else:
            now = now.replace(hour=6, minute=0)

        time = 6
        day = now.strftime('%A')
    else:
        day = now.strftime('%A')

    # Creates lists to be made into combinations
    discounts = np.arange(0.25, 0.8, 0.05)
    lead_times = np.arange(0.5, 8.5, 0.5)
    window_lengths = np.arange(0.5, 8.5, 0.5)

    combinations = []

    for discount in discounts:
        # Calculates the price
        price = retail_price * (1 - discount)

        for lead_time in lead_times:
            time_of_day = time + lead_time
            lead_time_output = lead_time

            # Check the lead_time doesn't push the posting to the next day
            if time_of_day > 22:
                overflow = time_of_day - 22.5
                time_of_day = 6 + overflow
                day = (now + datetime.timedelta(days=1)).strftime('%A')
                lead_time_output += 8

            for window_length in window_lengths:
                end_time = time_of_day + window_length
                if end_time > 22:
                    break

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
                    'vendor_id': vendor_id,
                    'lead_time_output': lead_time_output
                })

    df = pd.DataFrame(combinations)

    try:
        model_input_df = df.drop(columns=['lead_time_output'])

        # Tests combinations in model
        reservation_probability = model_reservation.predict_proba(model_input_df)[:, 1]
        collection_probability = model_collection.predict_proba(model_input_df)[:, 1]

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
        collection_start = now + datetime.timedelta(hours=best_params['lead_time_output'])
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

        lead_time = round(best_params['lead_time_output'] * 2) / 2
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

    except Exception:
        raise HTTPException(status_code=500)


def generate_production_recommendations(vendor_id, db):
    """
    Determines the most common products wasted by vendors and recommends them to reduce production on specific days.
    :param vendor_id: ID of the vendor.
    :param db: Database session.
    :return: A dictionary containing a list of production recommendations.
    """

    # Number of weeks to lookback
    num_weeks = 12

    try:
        # Find the vendors latest post
        latest_post_date_query = text("SELECT MAX(posting_time) FROM bundles WHERE vendor_id = :vid")
        latest_post_date = db.execute(latest_post_date_query, {'vid': vendor_id}).scalar()

        if not latest_post_date:
            return {'recommendations': []}

        # Get the date num_weeks ago
        start_date = latest_post_date - datetime.timedelta(weeks=num_weeks)

        # Joins the bundles, bundle_products, and products tables to get the quantities and names of the products inside the bundles posted between start_date and latest_post_date
        query = text("""
                     SELECT b.category,
                            -- Gets the day and removes all whitespace from the returned value
                            TRIM(TO_CHAR(b.posting_time, 'day')) AS day_of_week, DATE (b.posting_time) as post_date, b.bundle_id, p.name AS product_name, bp.quantity
                     FROM bundles b
                         JOIN bundle_products bp
                     ON b.bundle_id = bp.bundle_id
                         JOIN products p ON bp.product_id = p.product_id
                     WHERE b.vendor_id = :vid
                       AND b.posting_time >= :start_date
                       AND b.posting_time <= :latest_post_date
                     """)

        result = db.execute(query, {
            'vid': vendor_id,
            'start_date': start_date,
            'latest_post_date': latest_post_date
        }).mappings().all()

        # Combines the result into a dict containing relevant info
        post_data = {}
        for row in result:
            key = (row['category'], row['day_of_week'])
            if key not in post_data:
                post_data[key] = {
                    'bundles': set(),
                    'dates': set(),
                    'products': {},
                }

            post_data[key]['bundles'].add(row['bundle_id'])
            post_data[key]['dates'].add(row['post_date'])

            product_name = row['product_name']
            post_data[key]['products'][product_name] = post_data[key]['products'].get(product_name, 0) + row['quantity']

        recommendations = []

        # Iterates through post_data to calculate averages and generate outputs
        for (category, day_of_week), data in post_data.items():
            total_bundles = len(data['bundles'])
            weeks_posted = len(data['dates'])

            # Calculate the average bundles posted per week for each day
            avg_bundles_per_day = total_bundles / num_weeks

            # Determines the confidence based on the posting frequency per day per week over the time period
            if avg_bundles_per_day > 0.1:
                confidence_ratio = weeks_posted / num_weeks
                if confidence_ratio >= 0.8:
                    confidence = "High"
                elif confidence_ratio >= 0.5:
                    confidence = "Medium"
                else:
                    confidence = "Low"

                # Sorts the list of products by their quantity
                product_items = data['products'].items()
                sorted_products = sorted(product_items, key=lambda x: x[1], reverse=True)

                top_products = ""
                recommendation_text = ""

                # Formats the top 2 products wasted into strings
                for name, total_qty in sorted_products[:2]:
                    average_qty = round(total_qty / num_weeks)

                    if average_qty > 0:

                        # If the string is not empty add connecting words
                        if top_products != "":
                            top_products += " and "
                            recommendation_text += " and "

                        top_products += name
                        recommendation_text += f"{name} by {average_qty} unit(s)"

                if top_products == "":
                    continue

                # Makes the day_of_week and category a clean format for the frontend
                display_category = CATEGORY_MAP.get(category)
                display_day_of_week = day_of_week.capitalize()

                # The advice dictionary for each day
                advice = {
                    'category': display_category,
                    'day_of_week': display_day_of_week,
                    'avg_bundles': round(avg_bundles_per_day, 1),
                    'recommendation': f"We recommend that on {display_day_of_week} you should reduce your production of {recommendation_text}.",
                    'rationale': f"Over the 3 months leading up to your most recent post, your most consistently overproduced {display_category} items on {display_day_of_week}s were {top_products}. Cutting back on these items will reduce your waste!",
                    'confidence': confidence
                }
                recommendations.append(advice)

        return {"recommendations": recommendations}


    except Exception:
        raise HTTPException(status_code=500)
