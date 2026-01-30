import importlib

import create_users
import create_bundles
import create_reservations
import create_disputes
import create_user_streaks
import create_dataset

def generate_entire_database():
    create_users.create_users(250)
    create_bundles.generate_bundles(10000)

    importlib.reload(create_reservations)
    create_reservations.generate_reservations()

    importlib.reload(create_disputes)
    create_disputes.generate_disputes()

    importlib.reload(create_user_streaks)
    create_user_streaks.add_streaks()

    #importlib.reload(create_dataset)
    #create_dataset.generate_dataset()

if __name__ == "__main__":
    generate_entire_database()