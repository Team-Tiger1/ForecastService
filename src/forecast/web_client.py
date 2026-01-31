import csv

import requests

from src.forecast.auth import generate_auth_token


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

    # BUNDLES
    with open('../../data_seeding/database/bundles_with_products.csv', mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        data = list(csv_reader)

        for d in data:
            d["allergyTypes"] = []

    send_data("bundles/internal", data)

    # USERS
    # with open('../../data_seeding/database/users.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    # send_data("users/internal", data)


    # VENDORS
    # with open('../../data_seeding/database/vendors.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    # send_data("vendors/internal", data)

    # PRODUCTS
    # with open('../../data_seeding/database/vendors_products.csv', mode='r', encoding='utf-8') as file:
    #     csv_reader = csv.DictReader(file)
    #     data = list(csv_reader)
    #
    #     for d in data:
    #         d["allergies"] = []
    #
    # send_data("products/internal", data)

