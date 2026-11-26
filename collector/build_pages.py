#!/usr/bin/env python3
"""Vízfigyelő: builds one static page per city (eso/<slug>.html) from data.json, refreshes the city links on
index.html (between <!--CITIES--> markers) and rewrites sitemap.xml. Standard library only.
Run after collect.py. The pages hold the text as plain HTML (good for search engines); charts are drawn by assets/city.js.
"""
import json, re, sys
from datetime import datetime
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect import STATIONS          # names, slugs, "where?" forms

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://vizesmagyarorszag.hu"
MN = ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember", "október", "november", "december"]
MS = ["jan", "feb", "már", "ápr", "máj", "jún", "júl", "aug", "szep", "okt", "nov", "dec"]
STATIC_PAGES = ["index.html", "modszertan.html", "blog.html", "forrasok.html", "kapcsolat.html", "adatvedelem.html"]

def fmt(x, d=1):
    if x is None: return "–"
    return format(x, f",.{d}f").replace(",", " ").replace(".", ",")

def label(s):
    p = s["hmName"][len(s["n"]):].strip() if s.get("hmName", "").lower().startswith(s["n"].lower()) else s.get("hmName", "")
    return f"{s['n']} – {p}" if p else s["n"]

def mm_phrase(x):
    return "nincs adat" if x is None else ("nem esett eső (0 mm)" if x == 0 else f"{fmt(x)} mm csapadék (eső)")

def rel(cur, avg):
    if not avg: return ""
    p, d = (cur - avg) / avg * 100, cur - avg
    w = "az átlag körül" if abs(p) <= 10 else ("az átlag felett" if p > 0 else "az átlag alatt")
    return f"{w} ({'+' if d > 0 else ''}{fmt(d)} mm, {'+' if p > 0 else ''}{fmt(p, 0)}%)"

def answer_html(s):
    P, out = escape(label(s)), []
    out.append(f"<h3>Mennyi eső esett legutóbb?</h3><p>{P}: a legutóbbi mért napon ({escape(s['lastDate'])}) {mm_phrase(s.get('last'))}.</p>")
    m, M = s.get("mtd"), s.get("mtdStats")
    if m:
        t = f"{P}: {MN[m['month'] - 1]} 1–{m['days']}. között összesen {fmt(m['sum'])} mm csapadék (eső) esett"
        if M: t += f". Ugyanebben az időszakban az átlag {fmt(M['avg'])} mm ({M['from']}–{M['to']}), így ez {rel(m['sum'], M['avg'])}. A legkevesebb {fmt(M['min']['v'])} mm ({M['min']['y']}), a legtöbb {fmt(M['max']['v'])} mm ({M['max']['y']}) volt."
        out.append(f"<h3>Hány mm eső esett ebben a hónapban?</h3><p>{t}.</p>".replace("..", "."))
    y, Y = s.get("ytd"), s.get("ytdStats")
    if y:
        t = f"{P}: január 1. óta összesen {fmt(y['sum'])} mm csapadék (eső) esett"
        if Y: t += f". Az átlag ugyanerre az időszakra {fmt(Y['avg'])} mm ({Y['from']}–{Y['to']}), így ez {rel(y['sum'], Y['avg'])}. A legkevesebb {fmt(Y['min']['v'])} mm ({Y['min']['y']}), a legtöbb {fmt(Y['max']['v'])} mm ({Y['max']['y']}) volt."
        out.append(f"<h3>Hány mm eső esett idén?</h3><p>{t}.</p>".replace("..", "."))
    return "".join(out)

def tiles_html(s):
    T = [("Legutóbbi napi érték", f"{fmt(s.get('last'))} mm", "")]
    if s.get("mtd"): T += [("Eddig a hónapban", f"{fmt(s['mtd']['sum'])} mm", "hl")]
    if s.get("mtdStats"): T += [(f"Átlag eddig a hónapban ({s['mtdStats']['from']}–{s['mtdStats']['to']})", f"{fmt(s['mtdStats']['avg'])} mm", "")]
    if s.get("ytd"): T += [("Eddig az évben", f"{fmt(s['ytd']['sum'])} mm", "")]
    return '<div class="tiles">' + "".join(f'<div class="tile {c}"><b>{v}</b><span>{escape(k)}</span></div>' for k, v, c in T) + "</div>"

def records_html(s):
    rows = []
    for name, cur, st in (("Eddig a hónapban", (s.get("mtd") or {}).get("sum"), s.get("mtdStats")), ("Eddig az évben", (s.get("ytd") or {}).get("sum"), s.get("ytdStats"))):
        if st and cur is not None:
            rows.append(f"<tr><td>{name}</td><td class=n><b>{fmt(cur)}</b></td><td class=n>{fmt(st['min']['v'])}<div class=note>{st['min']['y']}</div></td>"
                        f"<td class=n>{fmt(st['avg'])}<div class=note>{st['from']}–{st['to']}</div></td><td class=n>{fmt(st['max']['v'])}<div class=note>{st['max']['y']}</div></td><td class=n>{st['rank']}. / {st['of']}</td></tr>")
    if not rows: return "<p class='note'>Még nincs elég hosszú adatsor az összehasonlításhoz.</p>"
    return ('<div class="sc"><table><tr><th>Időszak</th><th class=n>Idén (mm)</th><th class=n>Legkevesebb (mm)</th><th class=n>Átlag (mm)</th><th class=n>Legtöbb (mm)</th><th class=n>Sorrend</th></tr>'
            + "".join(rows) + '</table></div><p class="note">Sorrend: hányadik a legszárazabb az állomás vizsgált évei között (1. = a legszárazabb). Számított értékek, részletek: <a href="../modszertan.html">Módszertan</a>.</p>')

def monthly(s):
    Y = s.get("years") or {}
    if not Y: return None
    cur = str((s.get("mtd") or {}).get("year") or max(Y))
    if cur not in Y: cur = max(Y)
    others = [y for y in sorted(Y) if y != cur]
    avg = []
    for m in range(12):
        v = [Y[y][m] for y in others if Y[y][m] is not None]
        avg.append(sum(v) / len(v) if len(v) >= 3 else None)
    return cur, others, avg

def monthly_html(s):
    r = monthly(s)
    if not r: return "<p class='note'>Még nincs elég adat az összehasonlításhoz.</p>"
    cur, others, avg = r
    cm = s["mtd"]["month"] - 1 if s.get("mtd") and str(s["mtd"]["year"]) == cur else -1
    rows = []
    for m in range(12):
        v, a = s["years"][cur][m], avg[m]
        d = None if v is None or a is None else v - a
        rows.append(f"<tr><td>{MN[m]}</td><td class=n>{'<span class=note>folyamatban</span>' if m == cm else fmt(v)}</td><td class=n>{fmt(a)}</td><td class=n>{'–' if d is None else ('+' if d > 0 else '') + fmt(d)}</td></tr>")
    return (f'<div class="legend"><span><i style="background:var(--ac)"></i>Idei év ({cur})</span><span><i style="background:var(--ac3)"></i>Korábbi évek átlaga ({len(others)} év)</span></div><div id="cm"></div>'
            f'<div class="sc" style="margin-top:8px"><table><tr><th>Hónap</th><th class=n>Idei év ({cur}) <span class="tag now">idei év</span></th><th class=n>Korábbi évek átlaga</th><th class=n>Különbség (mm)</th></tr>{"".join(rows)}</table></div>'
            '<p class="note">Havi összegek, számított értékek; olyan hónap nem szerepel, amelyből 2-nél több nap hiányzik.</p>')

def page(s, cfg, stations_cfg, updated):
    slug, loc, n = cfg["slug"], cfg["loc"], cfg["n"]
    url = f"{SITE}/eso/{slug}.html"
    title = f"Mennyi eső esett {loc}? – Vízfigyelő"
    if s:
        P = escape(label(s))
        desc = f"Hány mm eső esett {loc}? Mért csapadék a(z) {label(s)} állomáson: legutóbbi nap, hónap és év, az átlaggal és a rekordokkal összevetve."
        head = f'<p class="sub">{P} mérőállomás · legutóbbi adat: {escape(s["lastDate"])} · forrás: HungaroMet</p>'
        body = (f'<div class="card"><h2>Röviden</h2>{tiles_html(s)}{answer_html(s)}</div>'
                f'<div class="card"><h2>Hány mm eső esett az elmúlt 14 napban?</h2><div id="c14"></div><p class="note">Napi csapadékösszeg (mm); az érték az eső és a hó együtt, a hó olvadt vízmennyisége; egy nap a HungaroMet szerint 06:00-tól másnap 06:00-ig (UTC) tart.</p></div>'
                f'<div class="card"><h2>Rekordok és az átlag: mennyi eső esett a korábbi években?</h2>{records_html(s)}</div>'
                f'<div class="card"><h2>Havi összehasonlítás: idei év és az átlag</h2>{monthly_html(s)}</div>'
                '<div class="card" id="fcc" hidden><h2>Mennyi eső várható a következő napokban?</h2><div id="fc"></div></div>')
        data = '<script type="application/json" id="cd">' + json.dumps(s, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    else:
        desc = f"Mennyi eső esett {loc}? Mért csapadékadatok a HungaroMet adataiból."
        head = '<p class="sub">Az adatok betöltése folyamatban van.</p>'
        body = '<div class="card"><p>Ehhez a városhoz még nem érkezett adat. Nézz vissza később.</p></div>'
        data = ""
    others = " · ".join(f'<a href="{c["slug"]}.html">{escape(c["n"])}</a>' for c in stations_cfg if c["slug"] != slug)
    return f'''<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc, quote=True)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="hu_HU">
<meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="{escape(desc, quote=True)}">
<meta property="og:url" content="{url}">
<link rel="stylesheet" href="../assets/site.css">
</head>
<body data-nav="index.html" data-slug="{slug}" data-url="{url}">
<main class="w">
<p class="note"><a href="../index.html">← Összes város és az országos áttekintés</a></p>
<h1>💧 Mennyi eső esett {escape(loc)}?</h1>
{head}
{body}
<div class="card"><h2>Megosztás és más városok</h2>
<p><button class="btn" id="sh" type="button">Link megosztása</button> <span class="note" id="shs" role="status"></span></p>
<p>Más városok: {others}</p></div>
<p class="note">Csapadékadatok forrása: HungaroMet Nonprofit Zrt. (<a href="https://odp.met.hu" rel="noopener">odp.met.hu</a>), változtatás nélkül; az összegek, átlagok és sorrendek számított értékek (<a href="../modszertan.html">Módszertan</a>). A csapadék az eső és a hó együttes mennyisége. Az oldal frissítve: {escape(updated)}.</p>
</main>
{data}
<script src="../assets/common.js"></script>
<script src="../assets/city.js"></script>
<script src="../assets/site.js"></script>
</body>
</html>
'''

def main():
    try: D = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    except Exception: D = {"stations": [], "updated": ""}
    by = {s["n"]: s for s in D["stations"]}
    upd = D.get("updated", "")[:16].replace("T", " ") or "–"
    (ROOT / "eso").mkdir(exist_ok=True)
    for cfg in STATIONS:
        (ROOT / "eso" / f"{cfg['slug']}.html").write_text(page(by.get(cfg["n"]), cfg, STATIONS, upd), encoding="utf-8")
    # city links on the home page (internal links for visitors and search engines)
    links = " · ".join(f'<a href="eso/{c["slug"]}.html">Mennyi eső esett {escape(c["loc"])}?</a>' for c in STATIONS)
    idx = ROOT / "index.html"; h = idx.read_text(encoding="utf-8")
    if "<!--CITIES-->" in h:
        h = re.sub(r"<!--CITIES-->.*?<!--/CITIES-->", lambda m: f"<!--CITIES-->{links}<!--/CITIES-->", h, flags=re.S)
        idx.write_text(h, encoding="utf-8")
    # sitemap
    lm = (D.get("updated") or datetime.now().isoformat())[:10]
    urls = [f"{SITE}/" if p == "index.html" else f"{SITE}/{p}" for p in STATIC_PAGES] + [f"{SITE}/eso/{c['slug']}.html" for c in STATIONS]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f" <url><loc>{u}</loc><lastmod>{lm}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    print(f"built {len(STATIONS)} city pages, sitemap with {len(urls)} urls")

if __name__ == "__main__":
    main()
