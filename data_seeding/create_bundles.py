import math
import random
import uuid

import pandas as pd
from datetime import datetime, timedelta, time

# Set seed to ensure same results across runs
RANDOM_SEED = 12
random.seed(RANDOM_SEED)

# Load needed datasets
VENDORS = pd.read_csv("database_files/vendors.csv")
PRODUCTS = pd.read_csv("database_files/products.csv")
VENDOR_CATEGORIES = pd.read_csv("database_files/categories.csv")
OPENING_HOURS = pd.read_csv("database_files/opening_hours.csv")

# Map category name to readable format for users
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
    """
    Select a random date between start_date and end_date.
    :param start_date: Earliest date to pick from.
    :param end_date: Latest date to pick from.
    :return: A random datetime object between start_date and end_date.
    """

    delta = end_date - start_date
    random_number_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_number_days)


def pick_products(vendor_id, category, budget=25.0):
    """
    Simulates a Vendor picking products to go into a bundle.
    :param vendor_id: ID of the Vendor.
    :param category: The category of the bundle.
    :param budget: The budget of the bundle.
    :return: A list of dictionaries containing the picked products and their quantities alongside the total retail price.
    """

    # Filters the PRODUCTS table to find products sold by the vendor with the correct category for the bundle
    available_products = PRODUCTS[
        (PRODUCTS['vendor_id'] == vendor_id) &
        (PRODUCTS['category'] == category)
        ].copy()

    available_products = available_products.to_dict('records')  # Convert available_products to list of dictionaries
    random.shuffle(available_products)
    remaining_budget = budget
    picked_products = []
    retail_price = 0

    # Iterates through each product in available_products
    for product in available_products:
        # Calculate the maximum quantity of the product that would fit in the remaining budget
        max_quantity_of_product = int(remaining_budget // product['retail_price'])
        if max_quantity_of_product <= 0:
            continue

        # Max quantity of each product is 3 to so bundles are more unique
        quantity_of_product = random.randint(1, min(max_quantity_of_product, 3))
        picked_products.append({
            'product_id': product['product_id'],
            'quantity': quantity_of_product
        })

        retail_price += quantity_of_product * product['retail_price']
        remaining_budget -= quantity_of_product * product['retail_price']

        # Function stops if the budget runs out or a random (30% chance) break condition occurs
        if remaining_budget <= 0 or random.random() < 0.3:
            break

    return picked_products, round(retail_price, 2)


def pick_posting_and_pickup_time(vendor_id, day_of_week, date):
    """
    Picks random posting, pickup start, and pickup end times.
    :param vendor_id: ID of the Vendor.
    :param day_of_week: Day of the week of the posting.
    :param date: The date of the posting.
    :return: ISO format strings for posting_time, pickup_start, pickup_end.
    """

    # Filters the OPENING_HOURS table to find the opening hours of the vendor on the specified day of the week
    opening_hours = OPENING_HOURS[
        (OPENING_HOURS['vendor_id'] == vendor_id) &
        (OPENING_HOURS['day'] == day_of_week)
        ]

    opening_time = datetime.strptime(opening_hours.iloc[0]['opening_time'], "%H:%M").time()
    closing_time = datetime.strptime(opening_hours.iloc[0]['closing_time'], "%H:%M").time()

    # Random decimal pickup time chosen between the opening and closing time
    posting_time_float = random.uniform(opening_time.hour, closing_time.hour - 1)

    # Random decimal pickup start and pickup end times between the posting time and closing time
    pickup_start_hour = random.randint(math.ceil(posting_time_float), closing_time.hour - 1)
    pickup_end_hour = random.randint(pickup_start_hour + 1, closing_time.hour)

    # Converts decimal times into HMS times
    posting_time_hour = int(posting_time_float)
    posting_time_minutes = int((posting_time_float - posting_time_hour) * 60)
    posting_time_seconds = int(((posting_time_float - posting_time_hour) * 60 - posting_time_minutes) * 60)

    # Combine the date with HMS times
    posting_datetime = datetime.combine(date, time(hour=posting_time_hour, minute=posting_time_minutes, second=posting_time_seconds))
    pickup_start_datetime = datetime.combine(date, time(hour=pickup_start_hour))
    pickup_end_datetime = datetime.combine(date, time(hour=pickup_end_hour))

    # Converts datetime times into ISO format times
    posting_time = posting_datetime.isoformat()
    pickup_start = pickup_start_datetime.isoformat()
    pickup_end = pickup_end_datetime.isoformat()

    return posting_time, pickup_start, pickup_end


def simulate_bundle():
    """
    Simulates the creation of a single bundle.
    :return: A dictionary of the bundle data needed for the Database Bundle Table and a dictionary of products within the bundle.
    """
    date = pick_date()
    day_of_week = date.strftime("%A")

    # Randomly select a random vendor
    vendors_list = VENDORS.to_dict('records')
    vendor = random.choice(vendors_list)
    vendor_id = vendor['vendor_id']
    vendor_name = vendor['name']

    # Randomly select a category the vendor sells
    categories = VENDOR_CATEGORIES[VENDOR_CATEGORIES['vendor_id'] == vendor_id]['category'].tolist()
    category = random.choice(categories)

    picked_products, retail_price = pick_products(vendor_id, category)

    # Randomly pick a discount between 25% and 75% and apply it to retail_price
    price = round(retail_price * random.uniform(0.25, 0.75), 2)

    posting_time, pickup_start, pickup_end = pick_posting_and_pickup_time(vendor_id, day_of_week, date)

    bundle_id = str(uuid.uuid4())

    # Adds bundle_id to each record in the picked_products list and adds the data to a dictionary
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
    """
    Generates N bundles and saves them to a CSV file.
    :param num_bundles: The number of bundles to generate.
    """

    print("Generating Bundles...")

    bundles_list = []
    bundle_products_list = []

    for _ in range(num_bundles):
        bundle, bundles_products = simulate_bundle()
        bundles_list.append(bundle)
        bundle_products_list.extend(bundles_products)

    # Convert list of dictionaries to dataframe
    bundles_df = pd.DataFrame(bundles_list)
    bundles_products_df = pd.DataFrame(bundle_products_list)

    print(f"Generated {len(bundles_df)} bundles.")
    bundles_df.to_csv("database_files/bundles.csv", index=False)
    bundles_products_df.to_csv("database_files/bundles_products.csv", index=False)


if __name__ == "__main__":
    generate_bundles()
