# weather_service.py
import os
import requests
from datetime import date

# pull coords & timezone from env
LAT = os.getenv("WEATHER_LAT")
LON = os.getenv("WEATHER_LON")
TZ  = "America/New_York"

# map Open-Meteo weathercodes → human text
WEATHER_CODE_DESC = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def get_daily_weather(date_str):
    """
    Fetches the daily min/max temps + a description for `date_str` (YYYY-MM-DD).
    Uses Open-Meteo’s 16-day free endpoint.
    """
    # Compute how many days ahead this is
    target = date.fromisoformat(date_str)
    today  = date.today()
    days_ahead = (target - today).days

    # Call up to 16 days out
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": "temperature_2m_min,temperature_2m_max,weathercode",
        "forecast_days": 16,
        "timezone": TZ
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()["daily"]

    # pick the right index
    if days_ahead < 0:
        return {"error": "Cannot show past dates — please select today or later."}
    if days_ahead >= len(data["time"]):
        return { "error": "Sorry, forecast is only available for dates within the next two weeks." }

    idx = days_ahead
    code = data["weathercode"][idx]
    desc = WEATHER_CODE_DESC.get(code, "Unknown")

    return {
        "date":     data["time"][idx],
        "temp_min": data["temperature_2m_min"][idx],
        "temp_max": data["temperature_2m_max"][idx],
        "weathercode": code,
        "description": desc,
    }
