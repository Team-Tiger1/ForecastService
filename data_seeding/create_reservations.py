import uuid

import pandas as pd
import math
import random
from datetime import datetime
from pathlib import Path

RANDOM_SEED = 12
random.seed(RANDOM_SEED)

WEATHER = pd.read_csv('weather_files/weather_data_exeter.csv')
BUNDLES = pd.read_csv('database_files/bundles.csv')
USERS = pd.read_csv('database_files/users.csv')

NORMALISED_CATEGORIES = pd.read_csv('normalisation_files/categories.csv')
NORMALISED_WEATHER = pd.read_csv('normalisation_files/weather.csv')


def normalise_price(price):
    return math.exp(-0.1 * price)


def normalise_weather(condition):
    return NORMALISED_WEATHER.loc[NORMALISED_WEATHER['condition'] == condition, 'value'].values[0]


def normalise_category(category):
    return NORMALISED_CATEGORIES.loc[NORMALISED_CATEGORIES['category'] == category, 'value'].values[0]


def normalise_temperature(temp_c):
    optimal_temp = 20
    standard_deviation = 10
    return math.exp(-((temp_c - optimal_temp) ** 2) / (2 * (standard_deviation ** 2)))


def normalise_lead_time(hours):
    if hours < 1: return 0.3
    if 1 <= hours <= 4: return 1.0
    if hours > 6: return 0.4
    return 0.6


def normalise_window_length(hours):
    return min(1.0, hours / 4.0)


def normalise_time_of_day(hour):
    if 11 <= hour <= 14: return 1.0
    if 17 <= hour <= 20: return 0.9
    if 8 <= hour <= 10: return 0.6
    if hour > 21: return 0.2
    return 0.5


def calculate_decision(bundle, weights, threshold, create_dataset_entry=False):
    fmt = "%Y-%m-%dT%H:%M:%S"
    post_datetime = datetime.strptime(bundle['posting_time'], fmt)
    start_datetime = datetime.strptime(bundle['collection_start'], fmt)
    end_datetime = datetime.strptime(bundle['collection_end'], fmt)

    price = bundle['price']
    retail_price = bundle['retail_price']
    category = bundle['category']
    date = start_datetime.strftime('%Y-%m-%d')

    discount = max(0, (retail_price - price) / retail_price)
    lead_time_hrs = (start_datetime - post_datetime).total_seconds() / 3600
    window_length_hrs = (end_datetime - start_datetime).total_seconds() / 3600
    pickup_hour = start_datetime.hour
    is_weekend = start_datetime.weekday() >= 5

    weather = WEATHER[WEATHER['date'] == date].iloc[0]
    condition = weather['condition'].strip()
    temperature = weather['avgtemp_c']

    normalised_discount = discount
    normalised_price = normalise_price(price)
    normalised_weather = normalise_weather(condition)
    normalised_category = normalise_category(category)
    normalised_temperature = normalise_temperature(temperature)
    normalised_day = 1.0 if is_weekend else 0.7
    normalised_lead_time = normalise_lead_time(lead_time_hrs)
    normalised_window_length = normalise_window_length(window_length_hrs)
    normalised_time_of_day = normalise_time_of_day(pickup_hour)

    score = (
            (normalised_discount * weights['discount']) +
            (normalised_price * weights['price']) +
            (normalised_weather * weights['weather']) +
            (normalised_category * weights['category']) +
            (normalised_temperature * weights['temperature']) +
            (normalised_day * weights['day_of_week']) +
            (normalised_lead_time * weights['lead_time']) +
            (normalised_window_length * weights['window_length']) +
            (normalised_time_of_day * weights['time_of_day'])
    )

    if create_dataset_entry:
        dataset_entry = {
            'discount': discount,
            'price': price,
            'weather': condition,
            'category': category,
            'temperature': temperature,
            'day': start_datetime.strftime('%A'),
            'lead_time': lead_time_hrs,
            'window_length': window_length_hrs,
            'time_of_day': pickup_hour
        }

        return score > threshold, dataset_entry

    return score > threshold


def simulate_reservation(bundle, user_id):
    reservation_weights = {
        'discount': 0.3,
        'price': 0.15,
        'weather': 0.15,
        'lead_time': 0.1,
        'temperature': 0.1,
        'day_of_week': 0.05,
        'window_length': 0.05,
        'time_of_day': 0.05,
        'category': 0.05
    }

    threshold = 0.5 + random.uniform(-0.05, 0.05)
    is_reserved, dataset_entry = calculate_decision(bundle, reservation_weights, threshold, True)
    dataset_entry['is_reserved'] = is_reserved

    collection_weights = {
        'weather': 0.3,
        'temperature': 0.15,
        'window_length': 0.15,
        'day_of_week': 0.1,
        'time_of_day': 0.1,
        'lead_time': 0.05,
        'discount': 0.05,
        'price': 0.05,
        'category': 0.05
    }

    if is_reserved:
        threshold = 0.5 + random.uniform(-0.05, 0.05)
        is_collected = calculate_decision(bundle, collection_weights, threshold, False)
        dataset_entry['is_collected'] = is_collected
    else:
        dataset_entry['is_collected'] = False
        return None, dataset_entry

    if is_collected:
        status = 'COLLECTED'
    else:
        status = 'NO_SHOW'

    reservation_id = uuid.uuid4()
    bundle_id = bundle['bundle_id']

    posting_timestamp = datetime.fromisoformat(bundle['posting_time']).timestamp()
    collection_start_timestamp = datetime.fromisoformat(bundle['collection_start']).timestamp()
    collection_end_timestamp = datetime.fromisoformat(bundle['collection_end']).timestamp()

    reservation_time_unix = random.uniform(posting_timestamp, collection_end_timestamp - 3600)
    reservation_time = datetime.fromtimestamp(reservation_time_unix).isoformat()

    collection_time_unix = random.uniform(max(reservation_time_unix, collection_start_timestamp),
                                          collection_end_timestamp)
    collection_time = datetime.fromtimestamp(collection_time_unix).isoformat()

    reservation = {
        'reservation_id': reservation_id,
        'bundle_id': bundle_id,
        'user_id': user_id,
        'amount_due': bundle['price'],
        'reservation_time': reservation_time,
        'collection_time': collection_time,
        'collection_status': status,
    }

    return reservation, dataset_entry


def generate_reservations():
    print("Generating Reservations...")

    users_list = USERS.to_dict('records')

    reservations = []
    dataset = []
    for _, bundle in BUNDLES.iterrows():
        user_id = random.choice(users_list)['user_id']
        reservation, dataset_entry = simulate_reservation(bundle, user_id)

        dataset.append(dataset_entry)

        if reservation:
            reservations.append(reservation)

    dataset_df = pd.DataFrame(dataset)
    current_dir = Path(__file__).resolve().parent
    target_dir = current_dir.parent / 'src' / 'ml'
    file_path = target_dir / 'ml.csv'
    dataset_df.to_csv(file_path, index=False)

    reservations_df = pd.DataFrame(reservations)
    reservations_df.to_csv('database_files/reservations.csv', index=False)
    print(f"Generated {len(reservations_df)} reservations")


if __name__ == "__main__":
    generate_reservations()