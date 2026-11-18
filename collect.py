#!/usr/bin/env python3
"""Vízfigyelő collector: downloads HungaroMet daily rainfall (official 'rau' values)
and writes data.json. No calculations are done on the values.

Source: HungaroMet Nonprofit Zrt., https://odp.met.hu  (cite the source on the site!)
Usage:   python collector/collect.py            # writes data.json
         python collector/collect.py --list     # shows candidate stations per name
Only the Python standard library is needed.
"""
import io, json, sys, zipfile, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://odp.met.hu/climate/observations_hungary"
META_URL = BASE + "/10_minutes/station_meta_auto.csv"
DAILY_URL = BASE + "/daily/recent/HABP_1D_{id}_akt.zip"
DAYS = 14
UA = "Vizfigyelo/1.0 (public water site; contact: CHANGE-ME@example.com)"
OUT = Path(__file__).resolve().parent.parent / "data.json"

# display name, text to look for in HungaroMet's station name, optional pinned station number.
# Several stations can match one name: run with --list, then pin the one you want with "id".
STATIONS = [
    {"n": "Budapest",    "match": "Budapest"},
    {"n": "Győr",        "match": "Győr"},
    {"n": "Pécs",        "match": "Pécs"},
    {"n": "Szeged",      "match": "Szeged"},
    {"n": "Debrecen",    "match": "Debrecen"},
    {"n": "Miskolc",     "match": "Miskolc"},
    {"n": "Szombathely", "match": "Szombathely"},
    {"n": "Siófok",      "match": "Siófok"},
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def decode(b):
    for enc in ("utf-8-sig", "iso-8859-2"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "replace")

def parse_meta(text):
    rows = []
    for line in text.splitlines():
        p = [x.strip() for x in line.split(";")]
        if len(p) < 8 or not p[0].isdigit():
            continue
        try:
            rows.append({"id": p[0], "end": p[2], "la": float(p[3]), "lo": float(p[4]), "name": p[6], "region": p[7]})
        except ValueError:
            continue
    return rows

def candidates(meta, match):
    c = [m for m in meta if match.lower() in m["name"].lower()]
    return sorted(c, key=lambda m: (m["end"], m["id"]), reverse=True)  # most recently active first

def parse_daily(text):
    """Returns [(YYYY-MM-DD, mm or None), ...] from a HungaroMet daily csv."""
    header, out = None, []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split(";")]
        if header is None:
            header = p
            if "rau" not in header:
                raise ValueError("column 'rau' not found; header was: " + line[:200])
            i_rau = header.index("rau")
            continue
        if len(p) <= i_rau or not p[1].isdigit() or len(p[1]) != 8:
            continue
        try:
            v = float(p[i_rau])
        except ValueError:
            v = None
        if v is not None and v <= -999:
            v = None  # HungaroMet marks missing data as -999
        d = p[1]
        out.append((f"{d[:4]}-{d[4:6]}-{d[6:]}", v))
    return out

def fetch_station(sid):
    z = zipfile.ZipFile(io.BytesIO(get(DAILY_URL.format(id=sid))))
    name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    return parse_daily(decode(z.read(name)))

def main():
    meta = parse_meta(decode(get(META_URL)))
    if not meta:
        sys.exit("Could not read station metadata.")
    if "--list" in sys.argv:
        for s in STATIONS:
            print(f"\n{s['n']}:")
            for m in candidates(meta, s["match"])[:8]:
                print(f"  id={m['id']}  {m['name']}  ({m['region']})  active until {m['end']}")
        return
    result = []
    for s in STATIONS:
        try:
            if s.get("id"):
                m = next(x for x in meta if x["id"] == s["id"])
            else:
                m = candidates(meta, s["match"])[0]
            rows = fetch_station(m["id"])[-DAYS:]
            if not rows:
                raise ValueError("no rows")
            last_date, last_mm = rows[-1]
            result.append({"n": s["n"], "id": m["id"], "hmName": m["name"], "lo": m["lo"], "la": m["la"],
                           "lastDate": last_date, "last": last_mm,
                           "dates": [d for d, _ in rows], "daily": [v for _, v in rows]})
            print(f"ok   {s['n']} -> {m['id']} {m['name']}")
        except (StopIteration, IndexError):
            print(f"SKIP {s['n']}: no station matching '{s['match']}'", file=sys.stderr)
        except Exception as e:
            print(f"SKIP {s['n']}: {type(e).__name__}: {e}", file=sys.stderr)
    if not result:
        sys.exit("No station could be fetched: keeping the old data.json")
    out = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "demo": False,
           "source": "HungaroMet Nonprofit Zrt. (odp.met.hu)", "stations": result}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({len(result)} stations)")

if __name__ == "__main__":
    main()
