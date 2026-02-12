import random
import string
import uuid

import pandas as pd

# Set seed to ensure same results across runs
RANDOM_SEED = 12
random.seed(RANDOM_SEED)

# Load the necessary files
with open("user_creation_data/names.txt", "r") as f:
    NAMES = [line.strip() for line in f]
with open("user_creation_data/email_providers.txt", "r") as f:
    EMAIL_PROVIDERS = [line.strip() for line in f]

def create_user():
    """
    Generates a user. Includes name, email and password.
    :return: A dictionary containing a unique ID, credentials, and contact info. 'date_last_collection' and 'streak' are None as they are determined later by create_user_streaks.py.
    """

    user_id = str(uuid.uuid4())

    # Random combination of letters and numbers
    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    # Random name and email provider forms the users email address
    random_name = random.choice(NAMES).lower()
    random_email_provider = random.choice(EMAIL_PROVIDERS).lower()
    email = f"{random_name}@{random_email_provider}.com"

    return {
        "user_id": user_id,
        "password": password,
        "email": email,
        "date_last_collection": None,
        "streak": None
    }


def create_users(num_users=250):
    """
    Generates N users.
    :param num_users: Number of users to create.
    """
    print("Creating Users...")

    # Iterates num_user times to create users
    users = [create_user() for _ in range(num_users)]
    users_df = pd.DataFrame(users)

    print(f"Created {len(users_df)} users.")
    users_df.to_csv("database_files/users.csv", index=False)

if __name__ == "__main__":
    create_users()
