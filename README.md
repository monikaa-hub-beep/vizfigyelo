# Vízfigyelő

Public rainfall page using HungaroMet open data (odp.met.hu). Source must be cited; values are shown unchanged.

## Files
- `index.html`: the page (reads `data.json`, falls back to demo data)
- `data.json`: written by the collector (currently demo data)
- `collector/collect.py`: downloads HungaroMet daily rainfall (`rau`) and writes `data.json`
- `.github/workflows/update.yml`: runs the collector every 3 hours and commits changes

## Set up
1. Create a GitHub repo, upload all of these files.
2. In `collector/collect.py` replace `CHANGE-ME@example.com` in `UA` with your contact e-mail.
3. Run `python collector/collect.py --list` once, check that each name maps to the station you want,
   and pin it with `"id": "NNNNN"` in `STATIONS` if needed.
4. Settings > Pages > deploy from branch `main`, folder `/ (root)`.
5. Actions tab > "Update rainfall data" > Run workflow (first run).
