import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

def save_weather_data(location):
    start_date = datetime.today() - timedelta(days=1)
    weather_data = []

    for x in range(364):
        date = start_date - timedelta(days=x)
        date_string = date.strftime("%Y-%m-%d")

        response = requests.get(f"https://api.weatherapi.com/v1/history.json?key={API_KEY}&q={location}&dt={date_string}")
        data = response.json()

        day_data = data["forecast"]["forecastday"][0]["day"]
        day_data = {
            "date": date_string,
            **day_data,
            "condition": day_data["condition"]["text"]
        }
        weather_data.append(day_data)

    df_name = f"weather_data_{location.lower()}.csv"
    df = pd.DataFrame(weather_data)
    df.sort_values("date")
    df.to_csv(df_name, index=False)

save_weather_data("Exeter")