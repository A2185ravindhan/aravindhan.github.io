# aravindhan.github.io

This repository includes a small helper script, `weather.py`, that fetches the
weather for a city from the free and open [Open-Meteo](https://open-meteo.com)
service. The script can be used both as a library function and as a
command-line utility without any API keys or registration.

## Finding the weather for Chennai (and other cities)

The script now demonstrates how to fetch **tomorrow's** forecast for Chennai.
Simply run:

```bash
python weather.py
```

To query a different city, supply the `--city` flag:

```bash
python weather.py --city "Berlin" --day-offset 1
```

Use `--day-offset 0` to view the current conditions, `1` for tomorrow, `2` for
the day after, and so on. Output looks like:

```
Forecast for Berlin tomorrow (2024-05-19): Partly cloudy, high of 9.2°C, low of
3.4°C with winds up to 10.5 km/h.
```

You can also reuse the function directly in your own Python code:

```python
from weather import get_open_meteo_weather

report = get_open_meteo_weather("Chennai", day_offset=1)
print(report)
```

## Development notes

Run a quick syntax check before committing changes:

```bash
python -m compileall weather.py
```

This repository otherwise follows the standard HTML5 UP "Editorial" template
for the website content.
