#!/usr/bin/env python3
"""OPTIONAL and OFF by default: river water levels (cm) from vizugy.hu (OVF) -> vizugy.json

Switch ENABLE_VIZUGY on ONLY after you have confirmed in writing with OVF that republishing
is allowed. This reads the public national gauge list page (HTML), once per run.
It provides water LEVELS (cm), not discharge (m3/s). If the page layout changes, the parser may need an update.
"""
import json, re, sys, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ENABLE_VIZUGY = False
URL = "https://vizugy.hu/index.php?mapData=VizmerceLista&mapModule=OpVizallas"
UA = "Vizfigyelo/1.0 (public water site; contact: CHANGE-ME@example.com)"
GAUGES = [("Rajka", "Duna"), ("Esztergom", "Duna"), ("Budapest", "Duna"), ("Mohács", "Duna"), ("Záhony", "Tisza"), ("Szeged", "Tisza")]
OUT = Path(__file__).resolve().parent.parent / "vizugy.json"
TIME = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.\s+\d{2}:\d{2}$")

class Rows(HTMLParser):
    def __init__(self): super().__init__(); self.rows, self.cur, self.cell = [], None, None
    def handle_starttag(self, t, a):
        if t == "tr": self.cur = []
        elif t in ("td", "th"): self.cell = []
    def handle_data(self, d):
        if self.cell is not None: self.cell.append(d)
    def handle_endtag(self, t):
        if t in ("td", "th") and self.cell is not None and self.cur is not None:
            self.cur.append(" ".join("".join(self.cell).split())); self.cell = None
        elif t == "tr" and self.cur is not None: self.rows.append(self.cur); self.cur = None

def parse(html):
    p = Rows(); p.feed(html); out = []
    for r in p.rows:
        i = next((k for k, c in enumerate(r) if TIME.match(c)), None)
        if i is None or i < 2 or i + 1 >= len(r) or not re.fullmatch(r"-?\d+", r[i + 1]): continue
        out.append({"name": r[0], "river": r[1], "fkm": r[2] if i > 2 else "", "time": r[i], "level": int(r[i + 1])})
    return out

def main():
    if not ENABLE_VIZUGY:
        print("vizugy disabled (ENABLE_VIZUGY = False): nothing to do"); return
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    rows = parse(urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace"))
    picked = []
    for name, river in GAUGES:
        hit = next((r for r in rows if r["name"].lower() == name.lower() and r["river"].lower() == river.lower()), None)
        if hit: picked.append(hit)
        else: print(f"SKIP {name} ({river}): not in the list", file=sys.stderr)
    if not picked: sys.exit("No gauge found: keeping the old vizugy.json")
    OUT.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Országos Vízügyi Főigazgatóság (OVF), vizugy.hu", "gauges": picked}, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({len(picked)} gauges)")

if __name__ == "__main__":
    main()
