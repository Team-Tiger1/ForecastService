import pandas as pd


def generate_vendors_seeding():
    """
    Prepares Vendors table for seeding the Database. Renames columns to match required formats.
    """
    vendors = pd.read_csv("database_files/vendors.csv")
    vendors_seeding = vendors.copy()
    vendors_seeding = vendors_seeding.rename(columns={'vendor_id': 'vendorId', 'street_address': 'streetAddress', 'phone_number': 'phoneNumber'})
    vendors_seeding.to_csv('database_seeding_files/vendors_seeding.csv', index=False)


def generate_users_seeding():
    """
    Prepares Users table for seeding the Database. Renames columns to match required formats.
    """
    users = pd.read_csv("database_files/users.csv")
    users_seeding = users.copy()
    users_seeding = users_seeding.rename(columns={
        'user_id': 'userId',
        'date_last_collection': 'lastReservationTime'
    })
    users_seeding.to_csv('database_seeding_files/users_seeding.csv', index=False)


def generate_reservations_seeding():
    """
    Prepares Reservations table for seeding the Database. Renames columns to match required formats.
    """
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
    reservations_seeding = reservations_seeding.drop(columns=['amount_due']) # This is calculated using the product retail_price so is not needed in reservation table
    reservations_seeding.to_csv('database_seeding_files/reservations_seeding.csv', index=False)


def get_product_allergens(product_id, products_allergens, allergens):
    """
    Helper function for getting allergens for a product.
    :param product_id: ID of product.
    :param products_allergens: Dataframe linking product IDs to allergen IDs.
    :param allergens: Dataframe of allergen IDs and their names.
    :return: List of allergen names in given product.
    """

    # Return an empty list if the product has no allergens
    if product_id not in products_allergens['product_id'].values:
        return []

    # Filter products_allergens for the given product
    df = products_allergens[products_allergens['product_id'] == product_id]
    allergens_list = []

    # Iterates each row of allergens adding the names to a list
    for _, row in df.iterrows():
        allergen_id = row['allergen_id']
        allergen_name = allergens[allergens['allergen_id'] == allergen_id]['allergen_name'].iloc[0]
        allergens_list.append(allergen_name)

    return allergens_list


def generate_products_seeding():
    """
    Prepares Products table for seeding the Database. Renames columns to match required formats. Adds allergen column to products table.
    """

    products = pd.read_csv("database_files/products.csv")
    products_allergens = pd.read_csv("database_files/products_allergens.csv")
    allergens = pd.read_csv("database_files/allergens.csv")

    products_seeding = products.copy()
    all_products_allergens = []

    # Iterates through each product adding each products allergen data to a list all_products_allergens
    for _, row in products_seeding.iterrows():
        product_id = row['product_id']
        product_allergens = get_product_allergens(product_id, products_allergens, allergens)
        all_products_allergens.append(product_allergens)

    # Adds the products allergens to each product row
    products_seeding['allergies'] = all_products_allergens

    products_seeding = products_seeding.rename(columns={
        'product_id': 'productId',
        'vendor_id': 'vendorId',
        'retail_price': 'retailPrice'
    })
    products_seeding = products_seeding.drop(columns=['category'])
    products_seeding.to_csv('database_seeding_files/products_seeding.csv', index=False)


def get_bundle_products(bundle_id, bundles_products):
    """
    Helper function for getting products within a bundle.
    :param bundle_id: ID of bundle.
    :param bundles_products: Dataframe linking bundle IDs to products IDs.
    :return: List of products within given bundle.
    """

    df = bundles_products[bundles_products['bundle_id'] == bundle_id]
    product_ids_list = []

    # Iterates through each product and multiplies it by the quantity so product ID is in the list {quantity} times
    for _, row in df.iterrows():
        product_ids_list.extend([row['product_id']] * row['quantity'])

    return product_ids_list


def generate_bundles_seeding():
    """
    Prepares Bundles table for seeding the Database. Renames columns to match required formats. Adds allergen and products column.
    """

    bundles = pd.read_csv("database_files/bundles.csv")
    bundles_products = pd.read_csv("database_files/bundles_products.csv")
    products_allergens = pd.read_csv("database_files/products_allergens.csv")
    allergens = pd.read_csv("database_files/allergens.csv")

    bundles_seeding = bundles.copy()
    all_bundle_allergens = []
    all_bundle_products = []

    # Iterates through each bundle in the bundle dataset
    for _, row in bundles.iterrows():
        bundle_id = row['bundle_id']
        bundle_products = get_bundle_products(bundle_id, bundles_products)

        # Get all the allergens for each product in the bundle
        bundle_allergens = []
        for product_id in bundle_products:
            product_allergens = get_product_allergens(product_id, products_allergens, allergens)
            bundle_allergens.extend(product_allergens)

        # Removes duplicate allergens by converting the list of all allergens to a set and then back to a list
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
