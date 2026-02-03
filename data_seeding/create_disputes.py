import random
import uuid

import pandas as pd

RANDOM_SEED = 12
random.seed(RANDOM_SEED)

RESERVATIONS = pd.read_csv("database/reservations.csv")
USERS = pd.read_csv("database/users.csv")
VENDORS = pd.read_csv("database/vendors.csv")

BUNDLES = pd.read_csv("database/bundles.csv")
BUNDLES_PRODUCTS = pd.read_csv("database/bundles_products.csv")


def simulate_dispute(reservation_id):
    reservation = RESERVATIONS[RESERVATIONS['reservation_id'] == reservation_id].iloc[0]
    user_id = reservation['user_id']
    bundle_id = reservation['bundle_id']
    if BUNDLES[BUNDLES['bundle_id'] == bundle_id].empty:
        print("BUNDLE ID NOT FOUND")
    bundle = BUNDLES[BUNDLES['bundle_id'] == bundle_id].iloc[0]
    vendor_id = bundle['vendor_id']

    possible_disputes = {
        "missing_items": {
            "complaint": "I collected my bundle but there were missing items.",
            "vendor_approve_response": "We apologise for this. This is not acceptable. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle. We know that all items were placed inside this bundle.",
        },
        "spoiled_item": {
            "complaint": "One of the items was already spoiled when I got home.",
            "vendor_approve_response": "This is unacceptable. We are deeply sorry for this. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle. All produce placed into this bundle was quality and date checked by a member of our team."
        },
        "vendor_closed_early": {
            "complaint": "I arrived during the pickup window but the shop was already closed.",
            "vendor_approve_response": "We apologise for this issue. We had to close early due to an issue. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle. We did not close early on this date.",
        },
        "rude_staff_member": {
            "complaint": "I was spoken to rudely by a member of staff when collecting the bundle.",
            "vendor_approve_response": "We are incredibly sorry for your experience. This is not the standard we expect from our staff. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle. We have spoken to the staff member you interacted with and they claim to not have been rude.",
        },
        "bundle_doesnt_match_desc": {
            "complaint": "The items in my bundle do not match the description.",
            "vendor_approve_response": "We apologise for this issue. We incorrectly labelled this bundle. We will refund you for this bundle.",
            "vendor_deny_response": "Unfortunately, we will not be able to refund this bundle. We are able to confirm that this bundle did match the description."
        }
    }

    random_dispute_key = random.choice(list(possible_disputes.keys()))
    chosen_dispute = possible_disputes[random_dispute_key]

    if random.random() < 0.15:
        status = "APPROVED"
        vendor_response = chosen_dispute['vendor_approve_response']
    else:
        status = "DENIED"
        vendor_response = chosen_dispute['vendor_deny_response']


    dispute = {
        'reservation_id': reservation_id,
        'user_id': user_id,
        'vendor_id': vendor_id,
        'reason': chosen_dispute['complaint'],
        'vendor_response': vendor_response,
        'status': status
    }

    return dispute

def generate_disputes():
    print("Generating disputes...")
    disputes_list = []

    for row in RESERVATIONS.itertuples():
        if random.random() < 0.375:
            dispute = simulate_dispute(row.reservation_id)
            disputes_list.append(dispute)

    disputes_df = pd.DataFrame(disputes_list)
    print(f"Generated {len(disputes_df)} disputes.")
    disputes_df.to_csv("database/disputes.csv", index=False)

if __name__ == "__main__":
    generate_disputes()



