from collections import defaultdict
import pandas as pd

# Load needed datasets
USERS = pd.read_csv('database_files/users.csv')
RESERVATIONS = pd.read_csv('database_files/reservations.csv')

# Filter RESERVATIONS to contain only successful collections
SUCCESSFUL_COLLECTIONS = RESERVATIONS[RESERVATIONS['collection_status'] == "COLLECTED"]

# LATEST_DATE is set to the latest possible date a bundle could be made
LATEST_DATE = pd.Timestamp("2026-01-15")
LATEST_WEEK = LATEST_DATE.to_period('W')

# Groups all a users collections dates together. Done here to improve efficiency.
user_id_collection_dates = defaultdict(list)
for _, row in SUCCESSFUL_COLLECTIONS.iterrows():
    user_id = row['user_id']
    collection_date = pd.to_datetime(row['collection_time'])
    user_id_collection_dates[user_id].append(collection_date)


def calculate_streak(user_collection_dates):
    """
    Calculate the number of consecutive weeks a user has collected a bundle.
    :param user_collection_dates: List of datetime of every collection.
    :return: The streak of a user.
    """

    # Convert list of datetime to week periods
    collection_weeks = [date.to_period('W') for date in user_collection_dates]

    # Sort in descending order and remove all duplicates
    collection_weeks = sorted(list(set(collection_weeks)), reverse=True)

    if not collection_weeks:
        return 0

    latest_collection_week = collection_weeks[0]

    # If the gap between the LATEST_WEEK and the users last collection is greater than 1 their streak is 0.
    if (LATEST_WEEK - latest_collection_week).n > 1:
        return 0

    # Counts the consecutive weeks a user made a collection
    streak = 1
    for i in range(len(collection_weeks) - 1):
        if (collection_weeks[i] - collection_weeks[i + 1]).n == 1:
            streak += 1
        else:
            break

    return streak


def get_streak(user_id):
    """
    Gets the users streak and the date of their last collection.
    :param user_id: ID of the User.
    :return: Streak of the user and the date of their last collection.
    """

    # Gets the collection dates associated with the specified user
    user_collection_dates = user_id_collection_dates.get(user_id, [])

    # If they have not made a collection return a streak of 0 and no date of last collection
    if not user_collection_dates:
        return 0, None

    # If the user does have previous collections get their streak and the date of their last collection
    else:
        streak = calculate_streak(user_collection_dates)
        date_last_collection = max(user_collection_dates).isoformat()

    return streak, date_last_collection


def add_streaks():
    """
    Adds streaks and date of last collection to the User table.
    """

    print("Creating User Streaks...")

    streaks = []
    dates = []

    # Iterates through each user getting their streak and date of last collection
    for _, row in USERS.iterrows():
        user_id = row['user_id']
        streak, date_last_collection = get_streak(user_id)
        streaks.append(streak)
        dates.append(date_last_collection)

    USERS['streak'] = streaks
    USERS['date_last_collection'] = dates

    print(f"Created user streaks for {len(USERS)} users.")
    USERS.to_csv('database_files/users.csv', index=False)


if __name__ == '__main__':
    add_streaks()