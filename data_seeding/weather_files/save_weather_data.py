import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

def save_weather_data(location):
    """
    Saves a year of weather data for a specified location to csv file.
    :param location: The name of the location
    :return: None: The CSV file is saved as 'weather_data_{location}.csv'
    """

    # start_date is set to yesterday so that all API calls are for past data
    start_date = datetime.today() - timedelta(days=1)
    weather_data = []

    # Iterate backwards for a year
    for x in range(364):
        date = start_date - timedelta(days=x)
        date_string = date.strftime("%Y-%m-%d")

        try:
            url = f"https://api.weatherapi.com/v1/history.json?key={API_KEY}&q={location}&dt={date_string}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Get the day forecast from the JSON response
            day_data = data["forecast"]["forecastday"][0]["day"]

            day_data = {
                "date": date_string,
                **day_data,
                "condition": day_data["condition"]["text"] # Save just the text forecast e.g. "Cloudy"
            }
            weather_data.append(day_data)

        except (requests.RequestException, KeyError) as e:
            print(f"Error fetching data for {date_string}: {e}")
            continue

    # Create df_name using the location name
    df_name = f"weather_data_{location.lower()}.csv"
    df = pd.DataFrame(weather_data)

    # Sort the data based on the date
    df.sort_values("date")

    # Save to a CSV file using the name previously established
    df.to_csv(df_name, index=False)

if __name__ == "__main__":
    save_weather_data("Exeter")