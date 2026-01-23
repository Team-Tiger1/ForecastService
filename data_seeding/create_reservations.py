import random
import uuid
from datetime import datetime
from random import sample

import pandas as pd

RANDOM_SEED = 12
random.seed(RANDOM_SEED)

BUNDLES = pd.read_csv("database_csv_files/bundles.csv")
USERS = pd.read_csv("database_csv_files/users.csv")
WEATHER = pd.read_csv("weather_files/weather_data_exeter.csv")

WEATHER_MODIFIER = pd.read_csv("probability_modifiers/weather.csv")
TEMPERATURE_MODIFIER = pd.read_csv("probability_modifiers/temperature.csv")
DISCOUNT_MODIFIER = pd.read_csv("probability_modifiers/discount.csv")
PRICE_MODIFIER = pd.read_csv("probability_modifiers/price.csv")
TIME_BETWEEN_POST_AND_COLLECTION_MODIFIER = pd.read_csv("probability_modifiers/time_between_post_and_collection.csv")
DAY_MODIFIER = pd.read_csv("probability_modifiers/day_of_week.csv")
CATEGORY_MODIFIER = pd.read_csv("probability_modifiers/category.csv")
COLLECTION_TIME_MODIFIER = pd.read_csv("probability_modifiers/collection_time.csv")
COLLECTION_WINDOW_MODIFIER = pd.read_csv("probability_modifiers/collection_window_length.csv")
TIME_BETWEEN_RESERVATION_AND_COLLECTION_MODIFIER = pd.read_csv(
    "probability_modifiers/time_between_reservation_and_collection.csv")


def time_str_to_hours(time_str):
    time = datetime.strptime(time_str, "%H:%M:%S")
    return time.hour


def get_probability_modifier(df, value, value_type="exact"):
    if value_type == "exact":
        row = df[df['x'] == value]

    elif value_type == "range":
        row = df[(df['min'] <= value) & (df['max'] >= value)]

    if row.empty: raise ValueError(
        f"No probability modifier found for value={value} " f"in range [{df['min'].min()}, {df['max'].max()}]" f"{df}")

    return float(row['probability'].iloc[0])


def reservation_collection_probability(weather,
                                       temperature,
                                       discount,
                                       price,
                                       time_between_post_and_collection,
                                       day_of_week,
                                       category,
                                       collection_time,
                                       collection_window_length,
                                       time_between_reservation_and_collection=None,
                                       multiplier=1.0):
    p_weather = get_probability_modifier(WEATHER_MODIFIER, weather, "exact")
    p_temperature = get_probability_modifier(TEMPERATURE_MODIFIER, temperature, "range")
    p_discount = get_probability_modifier(DISCOUNT_MODIFIER, discount, "range")
    p_price = get_probability_modifier(PRICE_MODIFIER, price, "range")
    p_time_between_post_and_collection = get_probability_modifier(TIME_BETWEEN_POST_AND_COLLECTION_MODIFIER,
                                                                  time_between_post_and_collection, "range")
    p_day_of_week = get_probability_modifier(DAY_MODIFIER, day_of_week, "exact")
    p_category = get_probability_modifier(CATEGORY_MODIFIER, category, "exact")
    p_collection_time = get_probability_modifier(COLLECTION_TIME_MODIFIER, collection_time, "range")
    p_collection_window_length = get_probability_modifier(COLLECTION_WINDOW_MODIFIER, collection_window_length, "range")

    if time_between_reservation_and_collection is None:
        prob_list = [p_weather, p_temperature, p_discount, p_price, p_time_between_post_and_collection, p_day_of_week,
                     p_category, p_collection_time, p_collection_window_length]
    else:
        p_time_between_reservation_and_collection = get_probability_modifier(
            TIME_BETWEEN_RESERVATION_AND_COLLECTION_MODIFIER, time_between_reservation_and_collection, "range")

        prob_list = [p_weather, p_temperature, p_discount, p_price, p_time_between_post_and_collection, p_day_of_week,
                     p_category, p_collection_time, p_collection_window_length,
                     p_time_between_reservation_and_collection]

    probability = 1
    for prob in prob_list:
        probability = max(0, min(probability, 1))
        probability *= (1 - prob)

    probability = 1 - probability
    probability *= multiplier
    return probability


def reservation_collection_occurs(bundle_id, reservation_collection, reservation_time=None):
    bundle = BUNDLES[BUNDLES['bundle_id'] == bundle_id].iloc[0]

    posting_time = bundle['posting_time']
    collection_start = bundle['collection_start']
    collection_end = bundle['collection_end']

    date = datetime.fromtimestamp(posting_time).date()
    day_of_week = date.strftime("%A")

    time_between_post_and_collection = (collection_start - posting_time) / 3600
    collection_window_length = (collection_end - collection_start) / 3600
    midpoint_datetime = datetime.fromtimestamp((collection_start + collection_end) / 2)
    collection_time = midpoint_datetime.hour + midpoint_datetime.minute / 60 + midpoint_datetime.second / 60

    price = bundle['price']
    retail_price = bundle['retail_price']
    discount = (1 - price / retail_price) * 100
    category = bundle['category']

    date_str = datetime.fromtimestamp(posting_time).strftime('%Y-%m-%d')
    weather_of_day = WEATHER[WEATHER['date'] == date_str].iloc[0]
    weather = weather_of_day['condition']
    temperature = weather_of_day['avgtemp_c']

    probability = 1
    if reservation_collection == "reservation":
        probability = reservation_collection_probability(weather,
                                                         temperature,
                                                         discount,
                                                         price,
                                                         time_between_post_and_collection,
                                                         day_of_week,
                                                         category,
                                                         collection_time,
                                                         collection_window_length)

    elif reservation_collection == "collection":
        time_between_reservation_and_collection_datetime = datetime.fromtimestamp(collection_end - reservation_time)
        time_between_reservation_and_collection = time_between_reservation_and_collection_datetime.hour + time_between_reservation_and_collection_datetime.minute / 60 + time_between_reservation_and_collection_datetime.second / 60
        multiplier = 0.8
        probability = reservation_collection_probability(weather,
                                                         temperature,
                                                         discount,
                                                         price,
                                                         time_between_post_and_collection,
                                                         day_of_week,
                                                         category,
                                                         collection_time,
                                                         collection_window_length,
                                                         time_between_reservation_and_collection,
                                                         multiplier)

    probability = probability + random.gauss(0, 0.1)
    probability = max(0, min(probability, 1))
    return random.random() < probability


def simulate_reservation(bundle_id, user_id):
    is_reserved = reservation_collection_occurs(bundle_id, "reservation")
    if not is_reserved:
        return None

    reservation_id = str(uuid.uuid4())
    bundle = BUNDLES[BUNDLES['bundle_id'] == bundle_id].iloc[0]
    amount_due = bundle['price']

    posting_time = bundle['posting_time']
    collection_start = bundle['collection_start']
    collection_end = bundle['collection_end']
    reservation_time = random.uniform(posting_time, collection_end - 3600)

    is_collected = reservation_collection_occurs(bundle_id, "collection", reservation_time)
    if is_collected:
        collection_status = "COLLECTED"
        collection_time = random.uniform(max(reservation_time, collection_start), collection_end)
    else:
        collection_status = "NO_SHOW"
        collection_time = None

    reservation = {
        'reservation_id': reservation_id,
        'bundle_id': bundle_id,
        'user_id': user_id,
        'amount_due': amount_due,
        'reservation_time': reservation_time,
        'collection_status': collection_status,
        'collection_time': collection_time
    }

    return reservation

def generate_reservations():
    reservations_list = []

    for row in BUNDLES.itertuples():
        users_list = USERS.to_dict('records')
        user = random.choice(users_list)
        user_id = user['user_id']

        reservation = simulate_reservation(row.bundle_id, user_id)
        if reservation is not None:
            reservations_list.append(reservation)

    reservations_df = pd.DataFrame(reservations_list)
    reservations_df.to_csv('database_csv_files/reservations.csv', index=False)

if __name__ == "__main__":
    generate_reservations()
