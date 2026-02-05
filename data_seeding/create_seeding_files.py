import pandas as pd


def generate_vendors_seeding():
    vendors = pd.read_csv("database_files/vendors.csv")
    vendors_seeding = vendors.copy()
    vendors_seeding = vendors_seeding.rename(
        columns={'vendor_id': 'vendorId', 'street_address': 'streetAddress', 'phone_number': 'phoneNumber'})
    vendors_seeding.to_csv('database_seeding_files/vendors_seeding.csv', index=False)


def generate_users_seeding():
    users = pd.read_csv("database_files/users.csv")
    users_seeding = users.copy()
    users_seeding = users_seeding.rename(columns={
        'user_id': 'userId',
        'date_last_collection': 'lastReservationTime'
    })
    users_seeding = users_seeding.drop(columns=['username'])
    users_seeding.to_csv('database_seeding_files/users_seeding.csv', index=False)


def generate_reservations_seeding():
    reservations = pd.read_csv("database_files/reservations.csv")
    reservations_seeding = reservations.copy()
    reservations_seeding = reservations_seeding.rename(columns={
        'reservation_id': 'reservationId',
        'bundle_id': 'bundleId',
        'user_id': 'userId',
        'collection_status': 'status',
        'reservation_time': 'timeReserved',
        'collection_time': 'timeCollected',
    })
    reservations_seeding = reservations_seeding.drop(columns=['amount_due'])
    reservations_seeding.to_csv('database_seeding_files/reservations_seeding.csv', index=False)


def get_product_allergens(product_id, products_allergens, allergens):
    if product_id not in products_allergens['product_id'].values:
        return []

    df = products_allergens[products_allergens['product_id'] == product_id]
    allergens_list = []
    for _, row in df.iterrows():
        allergen_id = row['allergen_id']
        allergen_name = allergens[allergens['allergen_id'] == allergen_id]['allergen_name'].iloc[0]
        allergens_list.append(allergen_name)

    return allergens_list


def generate_products_seeding():
    products = pd.read_csv("database_files/products.csv")
    products_allergens = pd.read_csv("database_files/products_allergens.csv")
    allergens = pd.read_csv("database_files/allergens.csv")

    products_seeding = products.copy()
    all_products_allergens = []

    for _, row in products_seeding.iterrows():
        product_id = row['product_id']
        product_allergens = get_product_allergens(product_id, products_allergens, allergens)
        all_products_allergens.append(product_allergens)

    products_seeding['allergies'] = all_products_allergens
    products_seeding = products_seeding.rename(columns={
        'product_id': 'productId',
        'vendor_id': 'vendorId',
        'retail_price': 'retailPrice'
    })
    products_seeding = products_seeding.drop(columns=['category'])
    products_seeding.to_csv('database_seeding_files/products_seeding.csv', index=False)


def get_bundle_products(bundle_id, bundles_products):
    df = bundles_products[bundles_products['bundle_id'] == bundle_id]
    product_ids_list = []
    for _, row in df.iterrows():
        product_ids_list.extend([row['product_id']] * row['quantity'])

    return product_ids_list


def generate_bundles_seeding():
    bundles = pd.read_csv("database_files/bundles.csv")
    bundles_products = pd.read_csv("database_files/bundles_products.csv")
    products_allergens = pd.read_csv("database_files/products_allergens.csv")
    allergens = pd.read_csv("database_files/allergens.csv")

    bundles_seeding = bundles.copy()
    all_bundle_allergens = []
    all_bundle_products = []

    for _, row in bundles.iterrows():
        bundle_id = row['bundle_id']
        bundle_products = get_bundle_products(bundle_id, bundles_products)

        bundle_allergens = []
        for product_id in bundle_products:
            product_allergens = get_product_allergens(product_id, products_allergens, allergens)
            bundle_allergens.extend(product_allergens)

        bundle_allergens = list(set(bundle_allergens))

        all_bundle_products.append(bundle_products)
        all_bundle_allergens.append(bundle_allergens)

    bundles_seeding['productIds'] = all_bundle_products
    bundles_seeding['allergyTypes'] = all_bundle_allergens

    bundles_seeding = bundles_seeding.rename(columns={
        'bundle_id': 'bundleId',
        'vendor_id': 'vendorId',
        'posting_time': 'postingTime',
        'collection_start': 'collectionStart',
        'collection_end': 'collectionEnd'
    })
    bundles_seeding.drop(columns=['retail_price'], inplace=True)
    bundles_seeding.to_csv('database_seeding_files/bundles_seeding.csv', index=False)


if __name__ == "__main__":
    # generate_vendors_seeding()
    # generate_users_seeding()
    # generate_reservations_seeding()
    generate_products_seeding()
    # generate_bundles_seeding()
