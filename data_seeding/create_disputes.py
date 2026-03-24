from datetime import timedelta
import random
import uuid

import pandas as pd

# Set seed to ensure same results across runs
RANDOM_SEED = 12
random.seed(RANDOM_SEED)

# Load needed datasets
RESERVATIONS = pd.read_csv("database_files/reservations.csv")
USERS = pd.read_csv("database_files/users.csv")
VENDORS = pd.read_csv("database_files/vendors.csv")
BUNDLES = pd.read_csv("database_files/bundles.csv")
BUNDLES_PRODUCTS = pd.read_csv("database_files/bundles_products.csv")


def simulate_dispute(reservation_id):
    """
    Generate a dispute based on a given reservation id.
    :param reservation_id: ID of the reservation.
    :return: A dictionary containing a dispute scenario, a status, and a response.
    """

    # Gets the reservation row
    reservation = RESERVATIONS[RESERVATIONS['reservation_id'] == reservation_id].iloc[0]
    user_id = reservation['user_id']
    bundle_id = reservation['bundle_id']

    # Ensures the bundle that is being disputed exists
    if BUNDLES[BUNDLES['bundle_id'] == bundle_id].empty:
        print("BUNDLE ID NOT FOUND")

    # Gets the bundle row to get the vendor_id
    bundle = BUNDLES[BUNDLES['bundle_id'] == bundle_id].iloc[0]
    vendor_id = bundle['vendor_id']

    # Each different dispute scenario and a corresponding approval and deny response
    possible_disputes = {
        "DAMAGED": {
            "description": "Bundle was damaged.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "MISSING_ITEMS": {
            "description": "Bundle had missing items.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "QUALITY_ISSUES": {
            "description": "Bundle was poor quality.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "LOCATION_INACCESSIBLE": {
            "description": "I could not find the store.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "VENDOR_NO_SHOW": {
            "description": "You were not there for me to collect my bundle.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "REFUSED_COLLECTION": {
            "description": "You did not let me collect my bundle.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "PAST_WINDOW": {
            "description": "The collection window closed before I got there.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        },
        "OTHER": {
            "description": "I was not happy with the service I received.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle.",
        }
    }

    # Randomly selects a dispute scenario
    random_dispute_key = random.choice(list(possible_disputes.keys()))
    chosen_dispute = possible_disputes[random_dispute_key]

    # 85% the vendor approves the dispute to ensure there is variety in the dispute table
    if random.random() < 0.15:
        status = "APPROVED"
        vendor_response = chosen_dispute['vendor_approve_response']
    else:
        status = "REJECTED"
        vendor_response = chosen_dispute['vendor_deny_response']

    dispute_id = str(uuid.uuid4())

    dispute = {
        'dispute_id': dispute_id,
        'bundle_id': bundle_id,
        'user_id': user_id,
        'vendor_id': vendor_id,
        'description': chosen_dispute['description'],
        'reason': random_dispute_key,
        'vendor_response': vendor_response,
        'status': status,
        'time_created': pd.to_datetime(bundle['collection_end']) + timedelta(hours=1)
    }

    return dispute

def generate_disputes():
    """
    Iterates through each reservation and generates a list of disputes for a subset of them.
    """

    print("Generating disputes...")
    disputes_list = []

    for row in RESERVATIONS.itertuples():

        # 30% chance of the reservation being disputed
        if random.random() < 0.3:
            dispute = simulate_dispute(row.reservation_id)
            disputes_list.append(dispute)

    # Converts list of dictionaries to dataframe
    disputes_df = pd.DataFrame(disputes_list)
    print(f"Generated {len(disputes_df)} disputes.")
    disputes_df.to_csv("database_files/disputes.csv", index=False)

if __name__ == "__main__":
    generate_disputes()



