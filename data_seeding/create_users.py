import random
import string

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
    random_adjective = random.choice(ADJECTIVES).replace(" ","").capitalize()
    random_noun = random.choice(NOUNS).replace(" ","").capitalize()
    username = f"{random_adjective}{random_noun}"

    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    random_name = random.choice(NAMES).lower()
    random_email_provider = random.choice(EMAIL_PROVIDERS).lower()
    email = f"{random_name}@{random_email_provider}.com"

    return {
        "username": username,
        "password": password,
        "email": email,
        "money_saved": None,
        "streak": None
    }


def create_users(num_users=250):
    users = [create_user() for _ in range(num_users)]
    users_df = pd.DataFrame(users)
    users_df.to_csv("database_csv_files/users.csv", index=False)

if __name__ == "__main__":
    create_users()
