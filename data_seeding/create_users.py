import random
import string
import uuid

import pandas as pd

RANDOM_SEED = 12
random.seed(RANDOM_SEED)

ADJECTIVES = pd.read_csv("user_creation_data/adjectives.csv")["word"].tolist()
NOUNS = pd.read_csv("user_creation_data/nouns.csv")["word"].tolist()

with open("user_creation_data/names.txt", "r") as f:
    NAMES = [line.strip() for line in f]
with open("user_creation_data/email_providers.txt", "r") as f:
    EMAIL_PROVIDERS = [line.strip() for line in f]

def create_user():
    user_id = str(uuid.uuid4())

    random_adjective = random.choice(ADJECTIVES).replace(" ","").capitalize()
    random_noun = random.choice(NOUNS).replace(" ","").capitalize()
    username = f"{random_adjective}{random_noun}"

    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    random_name = random.choice(NAMES).lower()
    random_email_provider = random.choice(EMAIL_PROVIDERS).lower()
    email = f"{random_name}@{random_email_provider}.com"

    return {
        "user_id": user_id,
        "username": username,
        "password": password,
        "email": email,
        "date_last_collection": None,
        "streak": None
    }


def create_users(num_users=250):
    print("Creating Users...")

    users = [create_user() for _ in range(num_users)]
    users_df = pd.DataFrame(users)

    print(f"Created {len(users_df)} users.")
    users_df.to_csv("database/users.csv", index=False)

if __name__ == "__main__":
    create_users()
