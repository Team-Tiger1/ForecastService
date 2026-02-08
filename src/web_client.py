import csv

import requests

from src.auth import generate_auth_token


def send_data(endpoint_url, data):
    url = "https://thelastfork.shop/api/"
    secret = generate_auth_token()
    headers = {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json"
    }

    response = requests.post(url + endpoint_url, json=data, headers=headers)
    if response.status_code == 204:
        print(f"Data successfully sent to {endpoint_url}")
    else:
        print(f"Failed to send data to {endpoint_url} - Status code: {response.status_code}")


if __name__ == "__main__":

    # USERS
    with open('../data_seeding/database_seeding_files/users_seeding.csv', mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        data = list(csv_reader)

    send_data("users/internal", data)

    # RESERVATIONS
    # with open('../../data_seeding/database_seeding_files/reservations_seeding.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    # for i in range(0, len(data), 1000):
    #     batch = data[i:i + 1000]
    #     send_data("reservations/internal", batch)

    # BUNDLES
    # with open('../../data_seeding/database_seeding_files/bundles_seeding.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    #     for d in data:
    #         d["allergyTypes"] = ast.literal_eval(d["allergyTypes"])
    #         d["productIds"] = ast.literal_eval(d["productIds"]) #CSV's cannot store lists
    #
    #     for i in range(0, len(data), 1000):
    #         batch = data[i:i + 1000]
    #         send_data("bundles/internal", batch)


    # VENDORS
    # with open('../../data_seeding/database_seeding_files/vendors_seeding.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    # send_data("vendors/internal", data)

    # PRODUCTS
    # with open('../../data_seeding/database_seeding_files/products_seeding.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    #     for d in data:
    #         d["allergies"] = ast.literal_eval(d["allergies"])
    #
    # send_data("products/internal", data)

