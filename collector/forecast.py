#!/usr/bin/env python3
"""Vízfigyelő: 7-day precipitation forecast per city from Open-Meteo -> forecast.json

Source: Open-Meteo.com, https://open-meteo.com/  (CC BY 4.0, attribution shown on the site).
The free API is for NON-COMMERCIAL use only (no ads / subscriptions on the site); see https://open-meteo.com/en/terms
One request per run for all cities (multiple coordinates). On any error the old forecast.json is kept.
Needs data.json (city coordinates) from collect.py. Standard library only.
"""
import json, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.open-meteo.com/v1/forecast"
DAILY = "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,snowfall_sum"
DAYS = 7
UA = "Vizfigyelo/1.0 (public water site; contact: CHANGE-ME@example.com)"
OUT = ROOT / "forecast.json"

def fetch(stations):
    q = {"latitude": ",".join(f"{s['la']:.4f}" for s in stations), "longitude": ",".join(f"{s['lo']:.4f}" for s in stations),
         "daily": DAILY, "timezone": "Europe/Budapest", "forecast_days": str(DAYS)}
    url = API + "?" + urllib.parse.urlencode(q, safe=",")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def parse(resp, stations):
    items = resp if isinstance(resp, list) else [resp]      # several locations -> list, one location -> object
    if len(items) != len(stations): raise ValueError(f"expected {len(stations)} locations, got {len(items)}")
    out = {}
    for s, it in zip(stations, items):
        d = it["daily"]; n = len(d["time"])
        def col(k): return [None if v is None else round(float(v), 1) for v in d.get(k, [None] * n)]
        out[s["slug"]] = {"dates": d["time"], "precip": col("precipitation_sum"), "prob": col("precipitation_probability_max"),
                          "tmax": col("temperature_2m_max"), "tmin": col("temperature_2m_min"), "snow": col("snowfall_sum")}
    return out

def main():
    try:
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        stations = [s for s in data["stations"] if s.get("slug") and "lo" in s and "la" in s]
        if not stations: raise ValueError("no stations with coordinates in data.json")
        res = parse(fetch(stations), stations)
    except Exception as e:      # never break the whole update because of the forecast
        print(f"forecast skipped, keeping the old file: {type(e).__name__}: {e}", file=sys.stderr); return
    OUT.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Open-Meteo.com (CC BY 4.0)", "stations": res}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({len(res)} cities, {DAYS} days)")

if __name__ == "__main__":
    main()
