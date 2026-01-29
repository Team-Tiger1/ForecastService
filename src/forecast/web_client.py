import requests

from src.forecast.auth import generate_auth_token

url = "https://thelastfork.shop/api/"
secret = generate_auth_token()
headers = {
    "Authorization": f"Bearer {secret}",
    "Content-Type": "application/json"
}

def send_data(endpoint_url, data):
    response = requests.post(url + endpoint_url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Data successfully sent to {endpoint_url}")
    else:
        print(f"Failed to send data to {endpoint_url} - Status code: {response.status_code}")


if __name__ == "__main__":
    send_data("users/internal", {})