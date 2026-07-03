#!/usr/bin/env bash
# Weather CLI — Open-Meteo, no API key needed (free, non-commercial).
# Location defaults to Crackington Haven, Bude, Cornwall (EX23 0PE).
# Override with LAT/LON env vars if needed.
# Usage:
#   weather.sh today       # one-line summary for today
#   weather.sh tomorrow    # one-line summary for tomorrow
set -euo pipefail

LAT="${LAT:-50.7331}"
LON="${LON:--4.6188}"
API="https://api.open-meteo.com/v1/forecast"

cmd="${1:-today}"
case "$cmd" in
  today)    day_index=0 ;;
  tomorrow) day_index=1; ;;
  *) echo "usage: weather.sh {today|tomorrow}" >&2; exit 1 ;;
esac

# forecast_days must cover the index we want
days=$(( day_index + 1 ))

WX_JSON="$(curl -s -G "$API" \
  --data-urlencode "latitude=$LAT" \
  --data-urlencode "longitude=$LON" \
  --data-urlencode "daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max" \
  --data-urlencode "timezone=Europe/London" \
  --data-urlencode "wind_speed_unit=mph" \
  --data-urlencode "forecast_days=$days")"

WX_JSON="$WX_JSON" python3 - "$day_index" <<'PY'
import os, sys, json
idx = int(sys.argv[1])
raw = os.environ.get("WX_JSON", "")
try:
    d = json.loads(raw)["daily"]
except Exception:
    print("weather unavailable")
    sys.exit(0)

# WMO weather code -> short description
WMO = {
    0:"clear", 1:"mostly clear", 2:"partly cloudy", 3:"overcast",
    45:"fog", 48:"rime fog",
    51:"light drizzle", 53:"drizzle", 55:"heavy drizzle",
    56:"freezing drizzle", 57:"freezing drizzle",
    61:"light rain", 63:"rain", 65:"heavy rain",
    66:"freezing rain", 67:"freezing rain",
    71:"light snow", 73:"snow", 75:"heavy snow", 77:"snow grains",
    80:"light showers", 81:"showers", 82:"heavy showers",
    85:"snow showers", 86:"heavy snow showers",
    95:"thunderstorm", 96:"thunderstorm w/ hail", 99:"thunderstorm w/ hail",
}
code = d["weather_code"][idx]
desc = WMO.get(code, f"code {code}")
hi   = round(d["temperature_2m_max"][idx])
lo   = round(d["temperature_2m_min"][idx])
rain = d["precipitation_probability_max"][idx]
wind = round(d["wind_speed_10m_max"][idx])

s = f"{desc}, {hi}°/{lo}°C"
if rain is not None and rain >= 20:
    s += f", {rain}% rain"
if wind is not None and wind >= 25:
    s += f", windy ({wind}mph)"
print(s)
PY
