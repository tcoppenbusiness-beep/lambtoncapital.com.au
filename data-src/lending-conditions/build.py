#!/usr/bin/env python3
"""Build the quarterly 'Australian commercial lending conditions' page and CSV.

Input:  data-src/lending-conditions/editions/<slug>.json  (one file per quarter)
Output: public/commercial-lending-conditions.html          (always the latest edition)
        public/data/commercial-lending-conditions.csv      (every edition, long format)
        public/data/commercial-lending-conditions-<slug>.csv (this edition only)

Header and footer are copied from public/facts.html so the page always matches
the rest of the site. Run from the repo root:  python3 data-src/lending-conditions/build.py
"""
import csv
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
EDITIONS = Path(__file__).resolve().parent / "editions"
PAGE = "commercial-lending-conditions.html"
URL = "https://lambtoncapital.com.au/" + PAGE[:-len(".html")]
CSV_ALL = "data/commercial-lending-conditions.csv"

e = html.escape


def load_editions():
    files = sorted(EDITIONS.glob("*.json"))
    if not files:
        sys.exit("No edition JSON files found")
    return [json.loads(f.read_text()) for f in files]


def chrome():
    src = (PUBLIC / "facts.html").read_text()
    head_start = src.index("<!-- Google Tag Manager -->")
    gtm = src[head_start:src.index("<!-- End Google Tag Manager -->") + len("<!-- End Google Tag Manager -->")]
    body = src[src.index('<body data-depth="0">'):src.index("</header>") + len("</header>")]
    footer = src[src.index('<footer class="site-footer">'):]
    return gtm, body, footer


def fmt(m, key):
    v = m.get(key)
    if not v or v.get("value") in (None, ""):
        return "–"
    val = v["value"]
    if isinstance(val, (int, float)) and m.get("dp") is not None:
        val = f"{val:,.{m['dp']}f}"
    shown = f'{m.get("unit_prefix", "")}{val}{m.get("unit_suffix", "")}'
    return f'{e(shown)}<br><span class="body-sm ink-2">{e(v.get("period", ""))}</span>'


def build_csv(editions):
    fields = ["edition", "published", "group", "metric", "unit", "period", "value",
              "comparison", "series", "source", "source_url"]
    rows = []
    for ed in editions:
        for m in ed["metrics"]:
            for key, label in (("latest", "latest"), ("prev", "previous quarter"), ("year_ago", "year earlier")):
                v = m.get(key)
                if not v or v.get("value") in (None, ""):
                    continue
                rows.append({
                    "edition": ed["edition"], "published": ed["published"], "group": m["group"],
                    "metric": m["metric"], "unit": m["unit"], "period": v["period"],
                    "value": v["value"], "comparison": label, "series": m.get("series", ""),
                    "source": m["source_name"], "source_url": m["source_url"],
                })
    (PUBLIC / "data").mkdir(exist_ok=True)
    with open(PUBLIC / CSV_ALL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    latest = editions[-1]
    with open(PUBLIC / f"data/commercial-lending-conditions-{latest['slug']}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows([r for r in rows if r["edition"] == latest["edition"]])


def build_page(editions):
    ed = editions[-1]
    gtm, body, footer = chrome()
    sources = sorted({(m["source_name"], m["source_url"]) for m in ed["metrics"]})
    dataset = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"Australian commercial lending conditions, {ed['edition']}",
        "description": ed["meta_description"],
        "url": URL,
        "creator": {"@type": "Organization", "@id": "https://lambtoncapital.com.au/#org", "name": "Lambton Capital Pty Ltd", "url": "https://lambtoncapital.com.au/"},
        "publisher": {"@type": "Organization", "@id": "https://lambtoncapital.com.au/#org", "name": "Lambton Capital Pty Ltd", "url": "https://lambtoncapital.com.au/"},
        "datePublished": editions[0]["published"],
        "dateModified": ed.get("updated", ed["published"]),
        "temporalCoverage": ed["temporal_coverage"],
        "spatialCoverage": {"@type": "Place", "name": "Australia"},
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "keywords": ["commercial lending", "business lending rates", "small business lending",
                     "commercial property", "Australia", "RBA", "APRA"],
        "variableMeasured": [m["metric"] for m in ed["metrics"]],
        "isBasedOn": sorted({u for _, u in sources}),
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/csv",
             "contentUrl": f"https://lambtoncapital.com.au/{CSV_ALL}", "name": "All editions"},
            {"@type": "DataDownload", "encodingFormat": "text/csv",
             "contentUrl": f"https://lambtoncapital.com.au/data/commercial-lending-conditions-{ed['slug']}.csv",
             "name": ed["edition"]},
        ],
    }
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://lambtoncapital.com.au/"},
            {"@type": "ListItem", "position": 2, "name": "Commercial lending conditions", "item": URL},
        ],
    }
    webpage = {
        "@context": "https://schema.org", "@type": "WebPage", "url": URL,
        "dateModified": ed.get("updated", ed["published"]),
        "reviewedBy": {"@type": "Person", "@id": "https://lambtoncapital.com.au/#founder",
                       "name": "Thomas Coppen", "jobTitle": "Founder",
                       "url": "https://lambtoncapital.com.au/about"},
    }

    title = f"Australian commercial lending conditions, {ed['edition']} | Lambton Capital"
    stats = "".join(
        f'<div class="stat-band-item"><p class="stat">{e(s["value"])}</p>'
        f'<p class="label">{e(s["label"])}</p></div>' for s in ed["headline_stats"])

    groups = []
    for g in dict.fromkeys(m["group"] for m in ed["metrics"]):
        trs = "".join(
            f'<tr><td>{e(m["metric"])}<br><span class="body-sm ink-2">{e(m["unit"])}</span></td>'
            f'<td>{fmt(m, "latest")}</td><td>{fmt(m, "prev")}</td><td>{fmt(m, "year_ago")}</td>'
            f'<td><a href="{e(m["source_url"])}" rel="noopener">{e(m["source_name"])}</a>'
            f'{"<br><span class=\"body-sm ink-2\">" + e(m["series"]) + "</span>" if m.get("series") else ""}</td></tr>'
            for m in ed["metrics"] if m["group"] == g)
        groups.append(
            f'<h3 class="h3">{e(g)}</h3><div class="card card-flush table-scroll"><table>'
            f'<thead><tr><th>Measure</th><th>Latest</th><th>Previous quarter</th><th>A year earlier</th><th>Source</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div>')

    analysis = "".join(
        f'<section class="{"section-alt" if i % 2 == 0 else ""}"><div class="wrap stack">'
        f'<h2 class="h2">{e(a["question"])}</h2><p class="answer-first max-820">{e(a["answer"])}</p>'
        + (f'<ul class="scan-list max-820">{"".join(f"<li>{e(b)}</li>" for b in a.get("points", []))}</ul>' if a.get("points") else "")
        + (f'<p class="body max-820"><a href="{e(a["link"]["href"])}">{e(a["link"]["text"])}</a></p>' if a.get("link") else "")
        + '</div></section>'
        for i, a in enumerate(ed["analysis"]))

    changelog = "".join(f'<p class="body-sm">{e(c)}</p>' for c in ed["changelog"])
    archive = "".join(
        f'<li><a href="data/commercial-lending-conditions-{x["slug"]}.csv">{e(x["edition"])} (CSV)</a>, published {e(x["published"])}</li>'
        for x in reversed(editions))
    source_list = "".join(f'<li><a href="{e(u)}" rel="noopener">{e(n)}</a></li>' for n, u in sources)
    pub_human = ed["published_human"]

    page = f"""<!doctype html>
<html lang="en">
<head>
{gtm}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.ico?v=2" sizes="48x48">
<link rel="icon" href="/favicon.svg?v=2" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0F2A38">
<title>{e(title)}</title>
<meta name="description" content="{e(ed['meta_description'])}">
<link rel="canonical" href="{URL}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(ed['meta_description'])}">
<meta property="og:image" content="https://lambtoncapital.com.au/img/og-lambton-capital.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-serif-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-sans-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="css/site.css">
<style>.lc-table td,.lc-table th{{vertical-align:top}} .lc-table td:nth-child(2),.lc-table td:nth-child(3),.lc-table td:nth-child(4){{font-variant-numeric:tabular-nums;white-space:nowrap}}</style>
<script type="application/ld+json">
{json.dumps(dataset, indent=1)}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb, indent=1)}
</script>
<script type="application/ld+json">
{json.dumps(webpage, indent=1)}
</script>
</head>
{body}

<main id="main">

  <section class="section-tight">
    <div class="wrap stack">
      <p class="eyebrow">Quarterly data · {e(ed['edition'])} edition · published {e(pub_human)}</p>
      <h1 class="h1">Australian commercial lending conditions, {e(ed['edition'])}.</h1>
      <p class="lead max-820">{e(ed['lead'])}</p>
    </div>
  </section>

  <section class="section-dark">
    <div class="wrap stack-lg">
      <div class="stat-band-grid">{stats}</div>
      <p class="body-sm" style="color:#C9D6DE;margin:0;">{e(ed['stats_caption'])}</p>
    </div>
  </section>

{analysis}

  <section>
    <div class="wrap stack">
      <h2 class="h2" id="data">The full data table</h2>
      <p class="answer-first max-820">Every figure below comes from a public source, linked in the last column, with the period it refers to. Gaps (–) mean the source had not yet published that period.</p>
      <div class="stack lc-table">{''.join(groups)}</div>
      <p class="body max-820"><a class="btn btn-secondary" href="{CSV_ALL}" download>Download the data (CSV)</a></p>
    </div>
  </section>

  <section class="section-alt">
    <div class="wrap stack">
      <h2 class="h2" id="method">How is this put together?</h2>
      <p class="answer-first max-820">{e(ed['method'])}</p>
      <ul class="scan-list max-820">{source_list}</ul>
      <p class="body-sm max-820">This page is general information about market conditions, not advice about any loan or lender. Rates and policies on individual loans vary by lender, borrower and security.</p>
    </div>
  </section>

  <section>
    <div class="wrap stack">
      <h2 class="h2" id="cite">Can I use or quote this data?</h2>
      <p class="answer-first max-820">Yes. The compiled table and Lambton Capital's calculations are free to use under CC BY 4.0. Please cite: Lambton Capital, "Australian commercial lending conditions, {e(ed['edition'])}", {e(pub_human)}, lambtoncapital.com.au/{PAGE[:-5]}. Underlying series remain the property of their publishers.</p>
      <p class="body max-820">Media enquiries: <a href="mailto:thomas@lambtoncapital.com.au">thomas@lambtoncapital.com.au</a>. Next edition: {e(ed['next_update'])}.</p>
      <div class="card stack">
        <p class="label">Editions</p>
        <ul class="scan-list">{archive}</ul>
        <p class="label">Changelog</p>
        {changelog}
      </div>
    </div>
  </section>

  <section>
    <div class="wrap stack">
      <p class="body-sm max-820">Looking at finance for a commercial property or business? See <a href="commercial-property-finance">commercial property finance</a>, <a href="business-finance">business finance</a>, or run the numbers with the <a href="tools/commercial-loan-calculator">commercial loan calculator</a>.</p>
    </div>
  </section>

</main>

  <section class="reviewed-section" aria-label="Page review">
    <div class="wrap">
      <p class="reviewed-by">Compiled and reviewed by <a href="about">Thomas Coppen</a>, Founder · Updated <time datetime="{ed.get('updated', ed['published'])}">{e(ed.get('updated_human', pub_human))}</time></p>
    </div>
  </section>

{footer}"""
    (PUBLIC / PAGE).write_text(page)


if __name__ == "__main__":
    eds = load_editions()
    build_csv(eds)
    build_page(eds)
    print(f"Built {PAGE} from {len(eds)} edition(s); latest {eds[-1]['edition']}")
