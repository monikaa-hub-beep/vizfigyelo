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

## Cookie consent
`assets/site.js` shows the banner and stores the choice in the browser. The site sets no cookies today. If you add analytics later, load it inside `VF.onConsent(c => { if (c.analytics) {...} })`.

## vizugy.hu water levels (OFF)
`collector/vizugy.py` has `ENABLE_VIZUGY = False`. Turn it on only after OVF confirmed in writing that republishing is allowed. It gives water level (cm), not discharge. When `vizugy.json` exists the page shows the table automatically, with attribution and the disclaimer.

## Resources page
Add links in `forrasok.html` (see the comment in the "Vízmegtartás szabályai" box).
