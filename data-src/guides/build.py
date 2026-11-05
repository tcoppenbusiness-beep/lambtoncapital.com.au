#!/usr/bin/env python3
"""Build guide pages under public/guides/ from data-src/guides/<slug>/body.html + meta.json.

meta.json: {"title", "description", "published", "updated", "faq": [{"q","a"}], "related_from": [service pages that
should link to this guide], "keywords": [...]}
Header/footer are copied from public/facts.html (nav links rewritten with ../ for the /guides/ folder).
Also maintains the "Latest guides" block on each page listed in related_from, sitemap.xml and llms.txt.
Run from repo root: python3 data-src/guides/build.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
SRC = Path(__file__).resolve().parent
SITE = "https://lambtoncapital.com.au"
BLOCK_START, BLOCK_END = "<!-- guides:related -->", "<!-- /guides:related -->"
PREF_SOURCE = """<section class="pref-source" aria-label="Follow Lambton Capital on Google">
  <div class="wrap pref-source-inner">
    <div class="pref-source-copy">
      <p class="pref-source-title">See Lambton Capital first in Google</p>
      <p class="pref-source-text">Add us as a preferred source and our deal notes and guides are highlighted for you in Top Stories, AI Overviews and AI Mode.</p>
    </div>
    <div class="pref-source-btn" google-add-preferred-source-btn data-lang="en">
      <a class="btn btn-secondary" href="https://www.google.com/preferences/source?q=lambtoncapital.com.au" target="_blank" rel="noopener">Add as a preferred source on Google</a>
    </div>
  </div>
</section>
"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def chrome():
    src = (PUBLIC / "facts.html").read_text()
    gtm = src[src.index("<!-- Google Tag Manager -->"):src.index("<!-- End Google Tag Manager -->") + len("<!-- End Google Tag Manager -->")]
    body = src[src.index('<body data-depth="0">'):src.index("</header>") + len("</header>")]
    footer = src[src.index('<footer class="site-footer">'):]
    # relative links one level deeper
    body = body.replace('data-depth="0"', 'data-depth="1"')
    for part in ("body", "footer"):
        pass
    fix = lambda h: re.sub(r'(href|src)="(?!https?:|/|#|mailto:|tel:|\.\./)([^"]+)"', r'\1="../\2"', h)
    # no enquiry form on guide pages: send the header CTA to the contact page
    body = fix(body).replace('href="#enquiry"', 'href="../contact.html"')
    return gtm, body, fix(footer)


def guide_pages():
    out = []
    for d in sorted(SRC.iterdir()):
        if d.is_dir() and (d / "meta.json").exists():
            m = json.loads((d / "meta.json").read_text())
            m["slug"] = d.name
            m["body"] = (d / "body.html").read_text()
            out.append(m)
    return out


def build_page(m):
    gtm, body, footer = chrome()
    url = f"{SITE}/guides/{m['slug']}.html"
    article = {
        "@context": "https://schema.org", "@type": "Article", "headline": m["title"], "description": m["description"],
        "url": url, "datePublished": m["published"], "dateModified": m["updated"], "inLanguage": "en-AU",
        "author": {"@type": "Person", "@id": f"{SITE}/#founder", "name": "Thomas Coppen", "url": f"{SITE}/about.html"},
        "publisher": {"@type": "Organization", "@id": f"{SITE}/#org", "name": "Lambton Capital Pty Ltd", "url": f"{SITE}/"},
        "isPartOf": {"@type": "WebSite", "url": f"{SITE}/"}, "keywords": m.get("keywords", []),
        "about": "Commercial property finance in Australia",
    }
    breadcrumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{SITE}/guides/"},
        {"@type": "ListItem", "position": 3, "name": m["title"], "item": url}]}
    faq_html = ""
    if m.get("faq"):
        items = "".join(
            f'<details class="faq-item"><summary>{esc(f["q"])}<span class="faq-icon-plus">+</span><span class="faq-icon-minus">−</span></summary><p>{esc(f["a"])}</p></details>'
            for f in m["faq"])
        faq_html = f'<section><div class="wrap stack"><h2 class="h2">Frequently asked</h2><div class="stack" style="gap:0;">{items}</div></div></section>'
    updated_human = m["updated_human"]
    rel = re.search(r'<section[^>]*><div class="wrap stack">\s*<h2 class="h2">Related</h2>', m["body"])
    body_with_pref = (m["body"][:rel.start()] + PREF_SOURCE + "\n" + m["body"][rel.start():]) if rel else m["body"] + PREF_SOURCE
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
<title>{esc(m.get('seo_title', m['title']))}</title>
<meta name="description" content="{esc(m['description'])}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(m['title'])}">
<meta property="og:description" content="{esc(m['description'])}">
<meta property="og:image" content="{SITE}/img/og-lambton-capital.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-serif-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-sans-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../css/site.css">
<script type="application/ld+json">
{json.dumps(article, indent=1)}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb, indent=1)}
</script>
</head>
{body}

<main id="main">
{body_with_pref}
{faq_html}

  <section class="section-border-top" id="enquiry">
    <div class="wrap form-panel">
      <p class="prelaunch-note"><strong>Now taking early enquiries.</strong> Deal assessments open once our lender panel is confirmed. Early enquiries are contacted first. Written reply within two business days, no obligation, and we don't pass your details to anyone without asking you.</p>
      <form id="enquiryForm" novalidate>
        <div id="formSteps"></div>
        <label class="honeypot" aria-hidden="true">Leave this field empty <input type="text" name="botcheck" id="botcheck" tabindex="-1" autocomplete="off"></label>
      </form>
      <div id="thankyou" class="thankyou" style="display:none;"></div>
    </div>
  </section>
</main>

  <section class="reviewed-section" aria-label="Page review">
    <div class="wrap">
      <p class="reviewed-by">Written by <a href="../about.html">Thomas Coppen</a>, Founder · Updated <time datetime="{m['updated']}">{esc(updated_human)}</time></p>
    </div>
  </section>

{footer.replace('<script src="../js/form.js"></script>', '<div class="sticky-bar" id="stickyBar">\n  <a href="#enquiry" class="btn btn-primary btn-block" id="stickyCta">Get assessed</a>\n</div>\n\n<script src="../js/form.js"></script>')}"""
    (PUBLIC / "guides").mkdir(exist_ok=True)
    (PUBLIC / "guides" / f"{m['slug']}.html").write_text(page)
    return url


def related_block(guides, for_page):
    links = [g for g in guides if for_page in g.get("related_from", [])]
    if not links:
        return None
    prefix = "../" * for_page.count("/")
    items = "".join(f'<li><a href="{prefix}guides/{g["slug"]}.html">{esc(g["title"])}</a></li>' for g in links)
    return (f'{BLOCK_START}\n  <section class="section-alt">\n    <div class="wrap stack">\n      <h2 class="h2">Guides</h2>\n'
            f'      <ul class="scan-list max-820">{items}</ul>\n    </div>\n  </section>\n  {BLOCK_END}')


def update_service_pages(guides):
    pages = sorted({p for g in guides for p in g.get("related_from", [])})
    n = 0
    for p in pages:
        f = PUBLIC / p
        s = f.read_text()
        block = related_block(guides, p)
        if BLOCK_START in s:
            s = re.sub(re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END), block, s, flags=re.S)
        else:
            # insert just before the closing </main>
            s = s.replace("</main>", block + "\n\n</main>", 1)
        f.write_text(s)
        n += 1
    return n


def update_sitemap(guides):
    s = (PUBLIC / "sitemap.xml").read_text()
    for g in guides:
        loc = f"{SITE}/guides/{g['slug']}.html"
        entry = f"  <url><loc>{loc}</loc><lastmod>{g['updated']}</lastmod></url>\n"
        if loc in s:
            s = re.sub(rf"  <url><loc>{re.escape(loc)}</loc><lastmod>[^<]*</lastmod></url>\n", entry, s)
        else:
            s = s.replace("</urlset>", entry + "</urlset>")
    (PUBLIC / "sitemap.xml").write_text(s)


def update_llms(guides):
    s = (PUBLIC / "llms.txt").read_text()
    lines = "".join(f"- [{g['title']}]({SITE}/guides/{g['slug']}.html): {g['description']}\n" for g in guides)
    section = f"## Guides\n{lines}\n"
    if "## Guides\n" in s:
        s = re.sub(r"## Guides\n.*?\n\n", section, s, flags=re.S)
    else:
        s = s.replace("## Tools\n", section + "## Tools\n", 1)
    (PUBLIC / "llms.txt").write_text(s)


if __name__ == "__main__":
    gs = guide_pages()
    if not gs:
        sys.exit("no guides")
    for g in gs:
        print("built", build_page(g))
    print("service pages updated:", update_service_pages(gs))
    update_sitemap(gs)
    update_llms(gs)
