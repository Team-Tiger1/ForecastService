import random
from datetime import datetime

import pandas as pd

RANDOM_SEED = 12
random.seed(RANDOM_SEED)

BUNDLES = pd.read_csv("database_csv_files/bundles.csv")
USERS = pd.read_csv("database_csv_files/users.csv")
WEATHER = pd.read_csv("weather_files/weather_data_exeter.csv")

WEATHER_MODIFIER = pd.read_csv("probability_modifiers/weather.csv")
TEMPERATURE_MODIFIER = pd.read_csv("probability_modifiers/temperature.csv")
DAY_MODIFIER = pd.read_csv("probability_modifiers/day_of_week.csv")
COLLECTION_WINDOW_MODIFIER = pd.read_csv("probability_modifiers/collection_window_length.csv")
COLLECTION_TIME_MODIFIER = pd.read_csv("probability_modifiers/collection_time.csv")
TIME_BETWEEN_POST_AND_COLLECTION_MODIFIER = pd.read_csv("probability_modifiers/time_between_post_and_collection.csv")
CATEGORY_MODIFIER = pd.read_csv("probability_modifiers/category.csv")
PRICE_MODIFIER = pd.read_csv("probability_modifiers/price.csv")
DISCOUNT_MODIFIER = pd.read_csv("probability_modifiers/discount.csv")


# def create_reservation(bundle_id, user_id):
#     is_reserved = reservation_occurs()(bundle_id, user_id)
#     amount_due = BUNDLES[BUNDLES['bundle_id'] == bundle_id]['price'].iloc[0]
#     date = BUNDLES[BUNDLES['bundle_id'] == bundle_id]['date'].iloc[0]
#     current_weather_condition = WEATHER[WEATHER['date'] == user_id]['condition'].iloc[0]
#     current_weather_temp = WEATHER[WEATHER['date'] == user_id]['avgtemp_c'].iloc[0]


def time_str_to_hours(time_str):
    time = datetime.strptime(time_str, "%H:%M:%S")
    return time.hour


def get_probability_modifier(df, value, value_type="exact"):
    if value_type == "exact":
        row = df[df['x'] == value]
        return float(row['probability'].iloc[0])

    elif value_type == "range":
        row = df[(df['min'] <= value) & (df['max'] >= value)]
        return float(row['probability'].iloc[0])


def reservation_probability(time_between_post_and_collection,
                            day_of_week,
                            collection_window_length,
                            collection_time,
                            price,
                            discount,
                            category,
                            weather,
                            temperature):
    p_weather = get_probability_modifier(WEATHER_MODIFIER, weather, "exact")
    p_temperature = get_probability_modifier(TEMPERATURE_MODIFIER, temperature, "range")
    p_discount = get_probability_modifier(DISCOUNT_MODIFIER, discount, "range")
    p_price = get_probability_modifier(PRICE_MODIFIER, price, "range")
    p_time_between_post_and_collection = get_probability_modifier(TIME_BETWEEN_POST_AND_COLLECTION_MODIFIER, time_between_post_and_collection, "range")
    p_day_of_week = get_probability_modifier(DAY_MODIFIER, day_of_week, "exact")
    p_category = get_probability_modifier(CATEGORY_MODIFIER, category, "exact")
    p_collection_time = get_probability_modifier(COLLECTION_TIME_MODIFIER, collection_time, "range")
    p_collection_window_length = get_probability_modifier(COLLECTION_WINDOW_MODIFIER, collection_window_length, "range")

    p_list = [p_weather, p_temperature, p_discount, p_price, p_time_between_post_and_collection, p_day_of_week, p_category, p_collection_time, p_collection_window_length]

    p_no_res = 1
    for p in p_list:
        p = max(0, min(1, p))
        p_no_res *= (1 - p)

    probability = 1 - p_no_res
    return probability


def reservation_occurs(bundle_id):
    bundle = BUNDLES[BUNDLES['bundle_id'] == bundle_id].iloc[0]
    date = pd.to_datetime(bundle['date'])
    day_of_week = date.strftime("%A")

    posting_time = time_str_to_hours(bundle['posting_time'])
    collection_start = time_str_to_hours(bundle['collection_start'])
    collection_end = time_str_to_hours(bundle['collection_end'])

    time_between_post_and_collection = collection_start - posting_time
    collection_window_length = collection_end - collection_start
    collection_midpoint = collection_start + collection_window_length / 2

    price = bundle['price']
    retail_price = bundle['retail_price']
    discount = (1 - price / retail_price) * 100
    category = bundle['category']

    weather_of_day = WEATHER[WEATHER['date'] == bundle['date']].iloc[0]
    weather = weather_of_day['condition']
    temperature = weather_of_day['avgtemp_c']

    probability = reservation_probability(time_between_post_and_collection,
                                          day_of_week,
                                          collection_window_length,
                                          collection_midpoint,
                                          price,
                                          discount,
                                          category,
                                          weather,
                                          temperature)

    return probability


probabilities = []
for row in BUNDLES.itertuples():
    bundle_id = row.bundle_id
    p = reservation_occurs(bundle_id)
    probabilities.append(p)

mean_probability = sum(probabilities) / len(probabilities)
print(f"Mean reservation probability across all bundles: {mean_probability:.3f}")
