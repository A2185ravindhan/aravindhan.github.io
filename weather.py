"""Helpers for fetching weather information from the Open-Meteo service.

The module can be imported for reuse, or executed directly as a small CLI tool.
When run without arguments it demonstrates fetching the weather for Chennai. If
command-line flags are provided, the ``--city`` option can be used to look up a
different location.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

import argparse
import json
import sys
from urllib import error, parse, request

#: Human-readable descriptions for the most common Open-Meteo weather codes.
WEATHER_CODE_DESCRIPTIONS: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_DEFAULT_ERROR = "Error: Could not retrieve weather data."
_CITY_NOT_FOUND_ERROR = "Error: City not found."


def _fetch_json(url: str, params: Mapping[str, Any]) -> Dict[str, Any] | None:
    """Fetch JSON data from *url* using *params* encoded as query arguments."""

    query = parse.urlencode(params)
    full_url = f"{url}?{query}"

    try:
        with request.urlopen(full_url, timeout=10) as response:
            payload = response.read()
    except error.URLError:
        return None

    try:
        decoded_payload = payload.decode("utf-8")
    except UnicodeDecodeError:
        return None

    try:
        data = json.loads(decoded_payload)
    except ValueError:
        return None

    return data if isinstance(data, dict) else None


def get_open_meteo_weather(city: str, day_offset: int = 0) -> str:
    """Fetch weather information for *city* using Open-Meteo APIs.

    By default the function returns the current conditions. Supplying
    ``day_offset=1`` returns tomorrow's forecast, ``day_offset=2`` the day after,
    and so on.
    """

    if day_offset < 0:
        return _DEFAULT_ERROR

    city_query = city.strip()
    if not city_query:
        return _CITY_NOT_FOUND_ERROR

    geocode_data = _fetch_json(
        _GEOCODE_URL,
        {
            "name": city_query,
            "count": 1,
            "language": "en",
        },
    )

    if not geocode_data:
        return _DEFAULT_ERROR

    results = geocode_data.get("results")
    if not results or not isinstance(results, list):
        return _CITY_NOT_FOUND_ERROR

    location = results[0]
    if not isinstance(location, dict):
        return _DEFAULT_ERROR

    try:
        latitude = float(location["latitude"])
        longitude = float(location["longitude"])
    except (KeyError, TypeError, ValueError):
        return _DEFAULT_ERROR

    resolved_name = location.get("name") or city_query

    forecast_params = {
        "latitude": f"{latitude:.4f}",
        "longitude": f"{longitude:.4f}",
        "timezone": "auto",
        "forecast_days": str(day_offset + 1),
    }

    if day_offset == 0:
        forecast_params["current_weather"] = "true"
    else:
        forecast_params["daily"] = (
            "weathercode,temperature_2m_max,temperature_2m_min,windspeed_10m_max"
        )

    forecast_data = _fetch_json(_FORECAST_URL, forecast_params)

    if not forecast_data:
        return _DEFAULT_ERROR

    if day_offset == 0:
        current_weather = forecast_data.get("current_weather")
        if not isinstance(current_weather, dict):
            return _DEFAULT_ERROR

        try:
            temperature = float(current_weather["temperature"])
            wind_speed = float(current_weather["windspeed"])
            weather_code_value = current_weather["weathercode"]
            weather_code = int(weather_code_value)
        except (KeyError, TypeError, ValueError):
            return _DEFAULT_ERROR

        description = WEATHER_CODE_DESCRIPTIONS.get(
            weather_code, f"Unknown weather (code {weather_code})"
        )

        return (
            f"Current weather in {resolved_name}: {description}, {temperature:.1f}°C "
            f"with a wind speed of {wind_speed:.1f} km/h."
        )

    daily = forecast_data.get("daily")
    if not isinstance(daily, dict):
        return _DEFAULT_ERROR

    required_keys = {
        "time",
        "weathercode",
        "temperature_2m_max",
        "temperature_2m_min",
        "windspeed_10m_max",
    }
    if not required_keys.issubset(daily):
        return _DEFAULT_ERROR

    try:
        dates = list(daily["time"])
        codes = list(daily["weathercode"])
        temps_max = list(daily["temperature_2m_max"])
        temps_min = list(daily["temperature_2m_min"])
        winds = list(daily["windspeed_10m_max"])
    except TypeError:
        return _DEFAULT_ERROR

    try:
        date_value = dates[day_offset]
        weather_code = int(codes[day_offset])
        temp_max = float(temps_max[day_offset])
        temp_min = float(temps_min[day_offset])
        wind_speed = float(winds[day_offset])
    except (IndexError, TypeError, ValueError):
        return _DEFAULT_ERROR

    description = WEATHER_CODE_DESCRIPTIONS.get(
        weather_code, f"Unknown weather (code {weather_code})"
    )

    if day_offset == 1:
        day_label = f"tomorrow ({date_value})"
    else:
        day_label = f"on {date_value}"

    return (
        f"Forecast for {resolved_name} {day_label}: {description}, high of "
        f"{temp_max:.1f}°C, low of {temp_min:.1f}°C with winds up to "
        f"{wind_speed:.1f} km/h."
    )


def _build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Fetch the weather for a city using the Open-Meteo API. When no "
            "options are supplied the script prints tomorrow's forecast for "
            "Chennai as a demonstration."
        )
    )
    parser.add_argument(
        "--city",
        default="Chennai",
        help="City name to query (default: %(default)s)",
    )
    parser.add_argument(
        "--day-offset",
        type=int,
        default=0,
        help=(
            "Number of days in the future to forecast. Use 0 for current "
            "conditions (default), 1 for tomorrow, 2 for the day after, etc."
        ),
    )
    return parser


def main(argv: Any = None) -> int:
    """CLI entry point for fetching weather data."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    result = get_open_meteo_weather(args.city, args.day_offset)
    print(result)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Demonstration: fetch and print Chennai's weather when no arguments
        # are provided. Additional flags trigger the CLI parser above.
        print(get_open_meteo_weather("Chennai", day_offset=1))
        sys.exit(0)

    sys.exit(main(sys.argv[1:]))
