#!/usr/bin/env python3
"""Vízfigyelő collector: HungaroMet daily rainfall (official 'rau' values) -> data.json

Adds, on top of the published values:
  - month-to-date and year-to-date sums, their averages, record lows/highs and rank over the station's past years [calculated]
  - monthly totals per year for the year-by-year comparison [calculated]
Source: HungaroMet Nonprofit Zrt., https://odp.met.hu (cite it on the site).
Usage:  python collector/collect.py [--list]      (standard library only)
"""
import calendar, io, json, re, sys, zipfile, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE = "https://odp.met.hu/climate/observations_hungary"
META_URL = BASE + "/10_minutes/station_meta_auto.csv"
DAILY_URL = BASE + "/daily/recent/HABP_1D_{id}_akt.zip"
HIST_INDEX = BASE + "/daily/historical/"
DAYS = 14
CACHE_DAYS = 30        # re-download the long history at most this often
MIN_YEARS_AVG = 5      # no average if fewer past years than this
MAX_MISSING = 2        # a month with more missing days than this is left out
UA = "Vizfigyelo/1.0 (public water site; contact: maksa.monika@gmail.com)"
ROOT = Path(__file__).resolve().parent.parent
OUT, CACHE = ROOT / "data.json", ROOT / "climate_cache.json"

STATIONS = [  # "ids": HungaroMet station numbers (first = preferred, rest = fallbacks); "slug": page address; "loc": "where?" form for titles
    {"n": "Budapest",    "slug": "budapest",    "loc": "Budapesten",    "match": "Budapest",    "ids": ["44527", "44121"]},  # Budapest Pestszentlőrinc
    {"n": "Győr",        "slug": "gyor",        "loc": "Győrben",       "match": "Győr",        "ids": ["23703", "23714"]},  # Győr Likócs
    {"n": "Pécs",        "slug": "pecs",        "loc": "Pécsett",       "match": "Pécs",        "ids": ["38605"]},           # Pécs Árpádtető
    {"n": "Szeged",      "slug": "szeged",      "loc": "Szegeden",      "match": "Szeged",      "ids": ["58102", "58116"]},  # Szeged belterület
    {"n": "Debrecen",    "slug": "debrecen",    "loc": "Debrecenben",   "match": "Debrecen",    "ids": ["64711", "64710"]},  # Debrecen repülőtér
    {"n": "Miskolc",     "slug": "miskolc",     "loc": "Miskolcon",     "match": "Miskolc",     "ids": ["52744"]},           # Miskolc Diósgyőr
    {"n": "Szombathely", "slug": "szombathely", "loc": "Szombathelyen", "match": "Szombathely", "ids": ["15310"]},
    {"n": "Siófok",      "slug": "siofok",      "loc": "Siófokon",      "match": "Siófok",      "ids": ["36100", "36115"]},  # Siófok
]

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r:
        return r.read()

def decode(b):
    for enc in ("utf-8-sig", "iso-8859-2"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("utf-8", "replace")

def parse_meta(text):
    rows = []
    for line in text.splitlines():
        p = [x.strip() for x in line.split(";")]
        if len(p) >= 8 and p[0].isdigit():
            try: rows.append({"id": p[0], "start": p[1], "end": p[2], "la": float(p[3]), "lo": float(p[4]), "name": p[6], "region": p[7]})
            except ValueError: pass
    return rows

def candidates(meta, match):
    """Matching stations, best first: exact name, then name starting with the text, then longest record."""
    k = match.lower()
    rx = re.compile(r"(?:^|[\s\-(/])" + re.escape(k))
    c = [m for m in meta if rx.search(m["name"].lower())]
    return sorted(c, key=lambda m: (m["name"].lower() != k, not m["name"].lower().startswith(k), m["start"], m["id"]))

def parse_daily(text):
    """[(YYYY-MM-DD, mm|None)] from a HungaroMet daily csv (column 'rau', -999 = missing)."""
    header, out, i = None, [], 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        p = [x.strip() for x in line.split(";")]
        if header is None:
            header = p
            if "rau" not in p: raise ValueError("column 'rau' not found; header: " + line[:200])
            i = p.index("rau"); continue
        if len(p) <= i or len(p[1]) != 8 or not p[1].isdigit(): continue
        try: v = float(p[i])
        except ValueError: v = None
        if v is not None and v <= -999: v = None
        out.append((f"{p[1][:4]}-{p[1][4:6]}-{p[1][6:]}", v))
    return out

def read_zip(url):
    z = zipfile.ZipFile(io.BytesIO(get(url)))
    rows = []
    for n in z.namelist():
        if n.lower().endswith(".csv"): rows += parse_daily(decode(z.read(n)))
    return rows

def hist_files(html):
    out = {}
    for m in re.finditer(r"HABP_1D_(\d+)_\d{8}_\d{8}_hist\.zip", html): out.setdefault(m.group(1), set()).add(m.group(0))
    return {k: sorted(v) for k, v in out.items()}

def pack(days):  # compact cache: one comma-separated string per year (empty = missing)
    out = {}
    for y in sorted({int(d[:4]) for d in days}):
        base = date(y, 1, 1)
        out[str(y)] = ",".join("" if days.get((base + timedelta(i)).isoformat()) is None else repr(days[(base + timedelta(i)).isoformat()])
                               for i in range(366 if calendar.isleap(y) else 365))
    return out

def unpack(packed):
    days = {}
    for y, s in packed.items():
        base = date(int(y), 1, 1)
        for i, c in enumerate(s.split(",")):
            if c != "": days[(base + timedelta(i)).isoformat()] = float(c)
    return days

def monthly_sums(days, last):
    """{year: [12 monthly totals or None]}; a month needs <= MAX_MISSING missing days and must be finished."""
    acc, ly, lm, ld = {}, int(last[:4]), int(last[5:7]), int(last[8:])
    for d, v in days.items():
        if v is not None:
            a = acc.setdefault((int(d[:4]), int(d[5:7])), [0.0, 0]); a[0] += v; a[1] += 1
    out = {}
    for y in sorted({int(d[:4]) for d in days}):
        arr = []
        for m in range(1, 13):
            s, n = acc.get((y, m), (0.0, 0)); dim = calendar.monthrange(y, m)[1]
            unfinished = (y, m) > (ly, lm) or ((y, m) == (ly, lm) and ld < dim)
            arr.append(None if unfinished or n < dim - MAX_MISSING else round(s, 1))
        if any(x is not None for x in arr): out[str(y)] = arr
    return out

def current_sum(days, start, end):
    vals = [days.get((start + timedelta(i)).isoformat()) for i in range((end - start).days + 1)]
    return {"sum": round(sum(v for v in vals if v is not None), 1), "days": len(vals), "missing": sum(v is None for v in vals)}

def month_to_date(days, last):
    e = date.fromisoformat(last)
    r = current_sum(days, e.replace(day=1), e); r.update({"month": e.month, "year": e.year}); return r

def year_to_date(days, last):
    e = date.fromisoformat(last)
    r = current_sum(days, date(e.year, 1, 1), e); r.update({"year": e.year}); return r

def stats(cur, per):
    """Average, fewest/most on record and rank (1 = driest) of `cur` among the past years in `per` {year: mm}."""
    if len(per) < MIN_YEARS_AVG: return None
    ys = sorted(per)
    lo = min(ys, key=lambda y: (per[y], y)); hi = max(ys, key=lambda y: (per[y], -y))
    return {"avg": round(sum(per.values()) / len(per), 1), "n": len(per), "from": ys[0], "to": ys[-1],
            "min": {"y": lo, "v": per[lo]}, "max": {"y": hi, "v": per[hi]},
            "rank": 1 + sum(v < cur for v in per.values()), "of": len(per) + 1}

def period_stats(days, last, cur_m, cur_y):
    """Same period in every past year: month-to-date and year-to-date (calculated from published daily values)."""
    e = date.fromisoformat(last); per_m, per_y = {}, {}
    for y in sorted({int(d[:4]) for d in days}):
        if y >= e.year: continue
        end = date(y, e.month, min(e.day, calendar.monthrange(y, e.month)[1]))
        a = current_sum(days, end.replace(day=1), end)
        b = current_sum(days, date(y, 1, 1), end)
        if a["missing"] <= 1: per_m[y] = a["sum"]
        if b["missing"] <= max(3, b["days"] // 100): per_y[y] = b["sum"]
    return stats(cur_m, per_m), stats(cur_y, per_y)

def main():
    meta = parse_meta(decode(get(META_URL)))
    if not meta: sys.exit("Could not read station metadata.")
    if "--list" in sys.argv:
        for s in STATIONS:
            print(f"\n{s['n']}:")
            for m in candidates(meta, s["match"])[:8]: print(f"  id={m['id']}  {m['name']}  ({m['region']})  active until {m['end']}")
        return
    today = date.today().isoformat()
    try: cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception: cache = {}
    hist_idx, result = None, []
    for s in STATIONS:
        byid = {}
        for x in meta:
            if x["id"] not in byid or x["end"] > byid[x["id"]]["end"]: byid[x["id"]] = x
        cands = [byid[i] for i in s["ids"] if i in byid] if s.get("ids") else candidates(meta, s["match"])[:6]
        if not cands:
            print(f"SKIP {s['n']}: no station matching '{s['match']}'", file=sys.stderr); continue
        for m in cands:
            try:
                sid = m["id"]
                recent = dict(read_zip(DAILY_URL.format(id=sid)))
                if not recent: raise ValueError("no recent rows")
                e = cache.get(sid)
                if e and (date.fromisoformat(today) - date.fromisoformat(e["fetched"])).days < CACHE_DAYS:
                    hist = unpack(e["daily"])
                else:
                    if hist_idx is None: hist_idx = hist_files(decode(get(HIST_INDEX)))
                    hist = {}
                    for name in hist_idx.get(sid, []):
                        try: hist.update(dict(read_zip(HIST_INDEX + name)))
                        except Exception as ex: print(f"warn {s['n']} history {name}: {ex}", file=sys.stderr)
                    cache[sid] = {"fetched": today, "daily": pack(hist)}
                days = {**hist, **recent}
                last = max(recent)
                end = date.fromisoformat(last)
                dates = [(end - timedelta(i)).isoformat() for i in range(DAYS - 1, -1, -1)]
                mtd, ytd = month_to_date(days, last), year_to_date(days, last)
                sm, sy = period_stats(days, last, mtd["sum"], ytd["sum"])
                result.append({"n": s["n"], "slug": s["slug"], "loc": s["loc"], "id": sid, "hmName": m["name"], "lo": m["lo"], "la": m["la"],
                               "lastDate": last, "last": recent[last], "dates": dates, "daily": [days.get(d) for d in dates],
                               "mtd": mtd, "mtdAvg": sm and sm["avg"], "mtdAvgN": sm and sm["n"], "mtdAvgFrom": sm and sm["from"], "mtdAvgTo": sm and sm["to"],
                               "mtdStats": sm, "ytd": ytd, "ytdStats": sy,
                               "years": monthly_sums(days, last)})
                print(f"ok   {s['n']} -> {sid} {m['name']} (history years: {len({d[:4] for d in hist})})")
                break
            except Exception as ex:
                print(f"  try {s['n']} / {m['id']} {m['name']}: {type(ex).__name__}: {ex}", file=sys.stderr)
        else:
            print(f"SKIP {s['n']}: none of {len(cands)} candidate stations worked", file=sys.stderr)
    if not result: sys.exit("No station could be fetched: keeping the old data.json")
    CACHE.write_text(json.dumps(cache, separators=(",", ":")), encoding="utf-8")
    OUT.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "demo": False,
                               "source": "HungaroMet Nonprofit Zrt. (odp.met.hu)", "stations": result}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({len(result)} stations)")

if __name__ == "__main__":
    main()
