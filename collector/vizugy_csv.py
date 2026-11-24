#!/usr/bin/env python3
"""Converts CSV files downloaded from https://data.vizugy.hu (OVF) into vizugy.json.

Put one or more downloads into data/ (file names data/vizugy*.csv). Several files are merged,
so you can add lakes later with a second download. Stations with no readings are skipped.
Source/terms (as published on data.vizugy.hu): free reuse with attribution to OVF or the competent
water directorate; recent data is unprocessed and informational only.
Usage: python collector/vizugy_csv.py        (standard library only)
"""
import csv, glob, io, json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "vizugy.json"
# group + river label by words in the station name (checked in order); everything else -> "Egyéb"
RULES = [
    (("Siófok", "Balaton", "Keszthely", "Balatonfüred", "Velenc", "Agárd", "Fertő", "Fertőrákos", "Tisza-tó", "Kisköre"), "Tavak", "Tó"),
    (("Győr", "Komárom", "Esztergom", "Óbuda", "Budapest", "Paks", "Mohács", "Baja", "Rajka", "Dunaföldvár", "Szob", "Vác", "Duna"), "Duna", "Duna"),
    (("Záhony", "Tokaj", "Szeged", "Szolnok", "Tiszafüred", "Csongrád", "Vásárosnamény", "Tisza"), "Tisza", "Tisza"),
]
ORDER = {"Duna": 0, "Tisza": 1, "Tavak": 2, "Egyéb": 3}
LAKES = {"2891": "Balaton", "818": "Velencei-tó"}   # station id -> lake (add Tisza-tó, Fertő gauges here once downloaded)
MIN_READINGS = 3     # a gauge with fewer readings in all files is skipped (e.g. a single odd value)
TOL24, TOL7 = timedelta(hours=3), timedelta(hours=12)   # how close the reference reading must be to count as "24 h / 7 days ago"

def classify(name):
    for words, group, river in RULES:
        if any(w.lower() in name.lower() for w in words):
            return group, river
    return "Egyéb", ""

def parse_file(path):
    text = open(path, encoding="utf-8-sig").read()
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    cols = []
    for j, h in enumerate(rows[0][1:], start=1):
        parts = [p.strip() for p in h.split("\n")]
        m = re.match(r"(.*?)\s*\[(\d+)\]$", parts[0])
        name, sid = (m.group(1), m.group(2)) if m else (parts[0], str(j))
        kind = parts[1] if len(parts) > 1 else ""
        unit = (re.search(r"\(([^)]+)\)", kind) or [None, ""])[1]
        cols.append((j, name, sid, kind, unit))
    data = {}
    for r in rows[1:]:
        if not r or not r[0].strip(): continue
        try: t = datetime.strptime(r[0].strip(), "%Y-%m-%d %H:%M")
        except ValueError: continue
        for j, name, sid, kind, unit in cols:
            if j < len(r) and r[j].strip() != "":
                try: v = float(r[j].replace(",", "."))
                except ValueError: continue
                data.setdefault((sid, kind), {"name": name, "unit": unit, "r": {}})["r"][t] = v
    return data

def at_or_before(readings, times, target, tol):
    """Reading at/just before `target`, but only if it is within `tol` of it (otherwise None: no data gaps passed off as changes)."""
    best = None
    for t in times:
        if t <= target: best = t
        else: break
    return readings[best] if best and target - best <= tol else None

def main():
    files = sorted(glob.glob(str(ROOT / "data" / "vizugy*.csv")))
    if not files:
        print("no data/vizugy*.csv found: nothing to do"); return
    merged = {}
    for f in files:
        for k, v in parse_file(f).items():
            m = merged.setdefault(k, {"name": v["name"], "unit": v["unit"], "r": {}}); m["r"].update(v["r"])
    gauges, alltimes = [], []
    for (sid, kind), g in merged.items():
        times = sorted(g["r"])
        if len(times) < MIN_READINGS: print(f"skip {g['name']}: only {len(times)} reading(s)", file=sys.stderr); continue
        last = times[-1]; level = g["r"][last]
        c24 = at_or_before(g["r"], times, last - timedelta(hours=24), TOL24); c7 = at_or_before(g["r"], times, last - timedelta(days=7), TOL7)
        lo = min(times, key=lambda t: (g["r"][t], t)); hi = max(times, key=lambda t: (g["r"][t], -t.timestamp()))
        daily = {}
        for t in times: daily.setdefault(t.date(), []).append(g["r"][t])
        group, river = ("Tavak", LAKES[sid]) if sid in LAKES else classify(g["name"])
        gauges.append({"name": g["name"], "id": sid, "kind": kind, "unit": g["unit"], "group": group, "river": river,
                       "time": last.strftime("%Y-%m-%d %H:%M"), "from": times[0].strftime("%Y-%m-%d"), "level": level,
                       "c24": None if c24 is None else round(level - c24, 1), "c7": None if c7 is None else round(level - c7, 1),
                       "min": {"v": g["r"][lo], "t": lo.strftime("%Y-%m-%d")}, "max": {"v": g["r"][hi], "t": hi.strftime("%Y-%m-%d")},
                       "_daily": {d: round(sum(v) / len(v), 1) for d, v in daily.items()}})
        alltimes += [times[0], last]
    if not gauges: sys.exit("No station with readings: keeping the old vizugy.json")
    d0, d1 = min(alltimes).date(), max(alltimes).date()
    dates = [(d0 + timedelta(i)).isoformat() for i in range((d1 - d0).days + 1)]
    for g in gauges:
        dd = g.pop("_daily"); g["v"] = [dd.get(datetime.strptime(d, "%Y-%m-%d").date()) for d in dates]
    gauges.sort(key=lambda g: (ORDER[g["group"]], g["name"]))
    out = {"updated": max(alltimes).strftime("%Y-%m-%d %H:%M"), "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source": "Országos Vízügyi Főigazgatóság (OVF), data.vizugy.hu", "dates": dates, "gauges": gauges}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({len(gauges)} gauges, {len(dates)} days, last reading {out['updated']})")

if __name__ == "__main__":
    main()
