import math
import random
import uuid

import pandas as pd
from datetime import datetime, timedelta, time

RANDOM_SEED = 12
random.seed(RANDOM_SEED)

VENDORS = pd.read_csv("database/vendors.csv")
PRODUCTS = pd.read_csv("database/products.csv")
VENDOR_CATEGORIES = pd.read_csv("database/categories.csv")
OPENING_HOURS = pd.read_csv("database/opening_hours.csv")

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


def pick_date(start_date=datetime(2025, 1, 17), end_date=datetime(2026, 1, 15)):
    delta = end_date - start_date
    random_number_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_number_days)


def pick_products(vendor_id, category, budget=25.0):
    available_products = PRODUCTS[
        (PRODUCTS['vendor_id'] == vendor_id) &
        (PRODUCTS['category'] == category)
        ].copy()

    available_products = available_products.to_dict('records')  # convert to list of dicts
    random.shuffle(available_products)
    remaining_budget = budget
    picked_products = []
    retail_price = 0

    for product in available_products:
        max_quantity_of_product = int(remaining_budget // product['retail_price'])
        if max_quantity_of_product <= 0:
            continue

        quantity_of_product = random.randint(1, min(max_quantity_of_product, 3))
        picked_products.append({
            'product_id': product['product_id'],
            'quantity': quantity_of_product
        })

        retail_price += quantity_of_product * product['retail_price']
        remaining_budget -= quantity_of_product * product['retail_price']
        if remaining_budget <= 0 or random.random() < 0.3:
            break

    return picked_products, round(retail_price, 2)


def pick_posting_and_pickup_time(vendor_id, day_of_week, date):
    opening_hours = OPENING_HOURS[
        (OPENING_HOURS['vendor_id'] == vendor_id) &
        (OPENING_HOURS['day'] == day_of_week)
        ]

    opening_time = datetime.strptime(opening_hours.iloc[0]['opening_time'], "%H:%M").time()
    closing_time = datetime.strptime(opening_hours.iloc[0]['closing_time'], "%H:%M").time()

    posting_time_float = random.uniform(opening_time.hour, closing_time.hour - 1)
    pickup_start_hour = random.randint(math.ceil(posting_time_float), closing_time.hour - 1)
    pickup_end_hour = random.randint(pickup_start_hour + 1, closing_time.hour)

    posting_time_hour = int(posting_time_float)
    posting_time_minutes = int((posting_time_float - posting_time_hour) * 60)
    posting_time_seconds = int(((posting_time_float - posting_time_hour) * 60 - posting_time_minutes) * 60)

    posting_datetime = datetime.combine(date, time(hour=posting_time_hour, minute=posting_time_minutes,
                                                   second=posting_time_seconds))
    pickup_start_datetime = datetime.combine(date, time(hour=pickup_start_hour))
    pickup_end_datetime = datetime.combine(date, time(hour=pickup_end_hour))

    posting_time = posting_datetime.isoformat()
    pickup_start = pickup_start_datetime.isoformat()
    pickup_end = pickup_end_datetime.isoformat()

    return posting_time, pickup_start, pickup_end


def simulate_bundle():
    date = pick_date()
    day_of_week = date.strftime("%A")

    vendors_list = VENDORS.to_dict('records')
    vendor = random.choice(vendors_list)
    vendor_id = vendor['vendor_id']
    vendor_name = vendor['name']

    categories = VENDOR_CATEGORIES[VENDOR_CATEGORIES['vendor_id'] == vendor_id]['category'].tolist()
    category = random.choice(categories)

    picked_products, retail_price = pick_products(vendor_id, category)
    price = round(retail_price * random.uniform(0.25, 0.75), 2)

    posting_time, pickup_start, pickup_end = pick_posting_and_pickup_time(vendor_id, day_of_week, date)

    bundle_id = str(uuid.uuid4())

    bundles_products = []
    total_products = 0
    for product in picked_products:
        quantity = product['quantity']
        total_products += quantity
        bundles_products.append({
            'bundle_id': bundle_id,
            'product_id': product['product_id'],
            'quantity': quantity
        })

    description = f"{CATEGORY_MAP[category]} bundle from {vendor_name}. Contains {total_products} product(s)."

    bundle = {
        'bundle_id': bundle_id,
        'vendor_id': vendor_id,
        'name': f"{vendor_name} {CATEGORY_MAP[category]} Bundle",
        'description': description,
        'retail_price': retail_price,
        'price': price,
        'category': category,
        'posting_time': posting_time,
        'collection_start': pickup_start,
        'collection_end': pickup_end,
    }

    return bundle, bundles_products


def generate_bundles(num_bundles=25000):
    print("Generating Bundles...")

    bundles_list = []
    bundle_products_list = []

    for _ in range(num_bundles):
        bundle, bundles_products = simulate_bundle()
        bundles_list.append(bundle)
        bundle_products_list.extend(bundles_products)

    bundles_df = pd.DataFrame(bundles_list)
    bundles_products_df = pd.DataFrame(bundle_products_list)

    print(f"Generated {len(bundles_df)} bundles.")
    bundles_df.to_csv("database/bundles.csv", index=False)
    bundles_products_df.to_csv("database/bundles_products.csv", index=False)


if __name__ == "__main__":
    generate_bundles()
