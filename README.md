# Vízfigyelő

## Pages
index.html (rainfall + comparison) · blog.html · forrasok.html (sources, laws) · kapcsolat.html (contact form) · adatvedelem.html (privacy, DRAFT)

## Setup (GitHub Pages)
1. Upload everything to a public repo, Settings > Pages > branch `main`, folder `/ (root)`.
2. Put your contact e-mail in `UA` in `collector/collect.py` and `collector/vizugy.py` (it is visible publicly).
3. `python collector/collect.py --list` once: check each name maps to the right station, pin with `"id"` if needed.
4. Actions > "Update data" > Run workflow. The first run also downloads the long history (a minute or two); it is then cached for 30 days in `climate_cache.json`.

## Contact form without showing your e-mail
1. Create a free account at formspree.io, create a form, and set your e-mail as the destination there (it stays in their dashboard).
2. Copy the form ID and replace `YOUR_FORM_ID` in `kapcsolat.html` (`FORM_ENDPOINT`). Check their current free limits and spam settings.
3. Fill in `adatvedelem.html` (name “Formspree” is already mentioned as the processor).

## Blog
The empty file `.nojekyll` in the repo root must stay: without it GitHub Pages turns `.md` files into pages and the blog can't read them.
Add `blog/my-post.md` (Markdown: #, ##, **bold**, *italic*, [text](https://link), - lists) and one entry in `blog/index.json`:
`{"slug":"my-post","title":"…","date":"2026-12-01","summary":"…"}`  (slug: lowercase letters, digits, hyphens)

### Blog writing rules
Every source the text relies on is a hyperlink, both inline where it is cited and in a closing "Források" list. Attribute claims to who made them, and say what is not known.

## Cookie consent
`assets/site.js` shows the banner and stores the choice in the browser. The site sets no cookies today. If you add analytics later, load it inside `VF.onConsent(c => { if (c.analytics) {...} })`.

## Water levels (data.vizugy.hu, OVF)
Terms shown on data.vizugy.hu: free reuse with attribution (OVF / the regional directorate); recent data is unprocessed, informational only.
1. On data.vizugy.hu select stations (Duna, Tisza, lakes), the data type (water level) and the period, download the CSV.
2. Save it in the repo as `data/vizugy.csv` (or `data/vizugy2.csv`, ... to add more stations: they are merged).
3. The workflow runs `collector/vizugy_csv.py`, which writes `vizugy.json`; the page shows the water section automatically.
To refresh, upload a newer download over the old file (same stations, new dates). Ask OVF (ovf@ovf.hu) whether an API or stable download link exists.

## Resources page
Add links in `forrasok.html` (see the comment in the "Vízmegtartás szabályai" box).


## City pages, forecast, methodology
- `collector/build_pages.py` writes `eso/<city>.html` (one shareable page per city), the city links in `index.html` and `sitemap.xml`.
- `collector/forecast.py` fetches a 7-day forecast from Open-Meteo (CC BY 4.0) into `forecast.json`. The free Open-Meteo tier is **non-commercial only**: no ads, no subscriptions (voluntary donations are fine). It is fetched server-side, visitors' browsers never contact Open-Meteo.
- `modszertan.html` explains measured vs calculated values and lists all sources.
- Water CSVs: `data/vizugy.csv`, `vizugy2.csv`, `vizugy3.csv` are merged. Poroszló "szivattyútelep bel." is skipped (a pump station's internal water, not the Tisza-tó level). To add Tisza-tó or Fertő gauges, download their CSVs and save as `data/vizugy4.csv`, etc.
