from collections import defaultdict

import pandas as pd

USERS = pd.read_csv('database/users.csv')
RESERVATIONS = pd.read_csv('database/reservations.csv')
SUCCESSFUL_COLLECTIONS = df = RESERVATIONS[RESERVATIONS['collection_status'] == "COLLECTED"]

LATEST_DATE = pd.Timestamp("2026-01-15")
LATEST_WEEK = LATEST_DATE.to_period('W')

user_id_collection_dates = defaultdict(list)
for _, row in SUCCESSFUL_COLLECTIONS.iterrows():
    user_id = row['user_id']
    collection_date = pd.to_datetime(row['collection_time'])
    user_id_collection_dates[user_id].append(collection_date)


def calculate_streak(user_collection_dates):
    collection_weeks = []
    for date in user_collection_dates:
        collection_weeks.append(date.to_period('W'))
        collection_weeks = list(set(collection_weeks))
        collection_weeks = sorted(collection_weeks, reverse=True)

    latest_collection_week = collection_weeks[0]
    if (LATEST_WEEK - latest_collection_week).n > 1:
        return 0

    streak = 1
    for i in range(len(collection_weeks) - 1):
        if (collection_weeks[i] - collection_weeks[i + 1]).n == 1:
            streak += 1
        else:
            break

    return streak


def get_streak(user_id):
    user_collection_dates = user_id_collection_dates.get(user_id, [])
    if not user_collection_dates:
        return 0, None
    else:
        streak = calculate_streak(user_collection_dates)
        date_last_collection = max(user_collection_dates).isoformat()

    return streak, date_last_collection

def add_streaks():
    print("Creating User Streaks...")

    streaks = []
    dates = []

    for _, row in USERS.iterrows():
        user_id = row['user_id']
        streak, date_last_collection = get_streak(user_id)
        streaks.append(streak)
        dates.append(date_last_collection)

    USERS['streak'] = streaks
    USERS['date_last_collection'] = dates

    print(f"Created user streaks for {len(USERS)} users.")
    USERS.to_csv('database/users.csv', index=False)

if __name__ == '__main__':
    add_streaks()
