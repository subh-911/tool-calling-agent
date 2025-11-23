"""
Data retrieval tools for external information.

Best Practice: Rich descriptions with examples for better accuracy.
"""

from typing import Dict
import random
from datetime import datetime
from app.utils.validators import ToolOutputValidator


def get_weather(city: str, units: str = "celsius") -> Dict[str, any]:
    """
    Get current weather information for a specified city.

    This tool retrieves weather data including temperature, conditions,
    humidity, and wind speed. In production, this would connect to a
    real weather API. Currently uses mock data for demonstration.

    Args:
        city: Name of the city (e.g., 'New York', 'London', 'Tokyo')
        units: Temperature units - 'celsius' or 'fahrenheit' (default: celsius)

    Returns:
        Dictionary with temperature, condition, humidity, wind_speed, and feels_like

    Examples:
        1. Input: {"city": "New York"} → Output: {"temperature": 22, "condition": "partly cloudy", "humidity": 65}
        2. Input: {"city": "London", "units": "celsius"} → Output: {"temperature": 15, "condition": "rainy", "humidity": 80}
        3. Input: {"city": "Tokyo", "units": "fahrenheit"} → Output: {"temperature": 75, "condition": "sunny", "humidity": 55}

    Note:
        Weather data is mock values for demonstration. In production,
        integrate with services like OpenWeatherMap, WeatherAPI, or NOAA.
    """
    # Validate inputs
    city = ToolOutputValidator.validate_string(city, min_length=2, max_length=100)
    units = ToolOutputValidator.validate_string(units, pattern=r'^(celsius|fahrenheit)$')

    # Mock weather data
    # In production, fetch from API like openweathermap.org
    conditions = [
        "sunny", "partly cloudy", "cloudy", "rainy", "stormy",
        "snowy", "foggy", "windy", "clear"
    ]

    # Generate mock data based on city hash for consistency
    city_hash = sum(ord(c) for c in city.lower())
    random.seed(city_hash)

    # Base temperature in Celsius (deterministic per city)
    base_temp_c = 10 + (city_hash % 25)
    condition = conditions[city_hash % len(conditions)]
    humidity = 40 + (city_hash % 50)
    wind_speed_kmh = 5 + (city_hash % 30)

    # Convert to requested units
    if units == "fahrenheit":
        temperature = round((base_temp_c * 9/5) + 32, 1)
        feels_like = temperature + random.randint(-3, 3)
        wind_speed = round(wind_speed_kmh * 0.621371, 1)  # Convert to mph
        wind_unit = "mph"
        temp_unit = "°F"
    else:
        temperature = base_temp_c
        feels_like = temperature + random.randint(-2, 2)
        wind_speed = wind_speed_kmh
        wind_unit = "km/h"
        temp_unit = "°C"

    return {
        "city": city,
        "temperature": temperature,
        "temperature_unit": temp_unit,
        "feels_like": feels_like,
        "condition": condition,
        "humidity": humidity,
        "humidity_unit": "%",
        "wind_speed": wind_speed,
        "wind_unit": wind_unit,
        "timestamp": datetime.now().isoformat(),
        "note": "Using mock weather data for demonstration",
    }
