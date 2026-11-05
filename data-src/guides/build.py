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


HOME_START, HOME_END = "<!-- guides:home -->", "<!-- /guides:home -->"


def patch_nav_and_footer():
    """Idempotent: add a Guides link to the desktop nav, mobile nav and footer Company column on every page."""
    n = 0
    for f in list(PUBLIC.glob("*.html")) + list(PUBLIC.glob("tools/*.html")) + list(PUBLIC.glob("guides/*.html")):
        depth = len(f.relative_to(PUBLIC).parts) - 1
        pre = "../" * depth
        s = f.read_text()
        if f'href="{pre}guides/index.html">Guides</a>' in s:
            continue
        if f'{pre}tools/commercial-loan-calculator.html' not in s:
            continue
        guides = f'<a href="{pre}guides/index.html">Guides</a>'
        def add_after_tools(block):
            pat = r'^([ \t]*)(<a href="' + re.escape(pre) + r'tools/commercial-loan-calculator\.html"[^>]*>Tools</a>)[ \t]*$'
            return re.sub(pat, lambda mm: mm.group(1) + mm.group(2) + "\n" + mm.group(1) + guides, block, count=1, flags=re.M)
        for nav_class in ("site-nav", "mobile-nav"):
            m = re.search(rf'<nav class="{nav_class}".*?</nav>', s, flags=re.S)
            if m:
                s = s[:m.start()] + add_after_tools(m.group(0)) + s[m.end():]
        s = s.replace(f'        <a href="{pre}deal-notes.html">Deal notes</a>\n', f'        {guides}\n        <a href="{pre}deal-notes.html">Deal notes</a>\n', 1)
        f.write_text(s)
        n += 1
    return n


def build_index(guides):
    gtm, body, footer = chrome()
    cards = "".join(guide_card(g, "../", "h2") for g in sorted(guides, key=lambda g: g["updated"], reverse=True))
    data_cards = (
        '<article class="card card-flush"><img loading="lazy" decoding="async" width="1400" height="788" class="card-img" src="../img/home2.webp" srcset="../img/home2-480.webp 480w, ../img/home2-800.webp 800w, ../img/home2.webp 1400w" sizes="(min-width:901px) 400px, 100vw" alt="Industrial unit exterior"><div class="card-img-body"><p class="label">Quarterly data</p>'
        '<h2 class="h3" style="margin:0;"><a href="../commercial-lending-conditions.html">Australian commercial lending conditions</a></h2>'
        '<p class="body-sm">Business lending rates by business size, credit growth and bank commercial property exposures, from RBA and APRA data. CSV included, free to cite.</p></div></article>'
        '<article class="card card-flush"><img loading="lazy" decoding="async" width="800" height="1000" class="card-img" src="../img/cp-brick-commercial-building.webp" srcset="../img/cp-brick-commercial-building-480.webp 480w, ../img/cp-brick-commercial-building.webp 800w" sizes="(min-width:901px) 400px, 100vw" alt="Brick commercial building"><div class="card-img-body"><p class="label">Deal notes</p>'
        '<h2 class="h3" style="margin:0;"><a href="../deal-notes.html">Deals we arrange, with the numbers</a></h2>'
        '<p class="body-sm">Anonymised deal structures: loan size, LVR, lender tier and days to settle.</p></div></article>')
    collection = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Guides and data", "url": f"{SITE}/guides/",
                  "description": "Plain-English guides to commercial property and business finance in Australia, plus Lambton Capital's quarterly lending data.",
                  "publisher": {"@type": "Organization", "@id": f"{SITE}/#org", "name": "Lambton Capital Pty Ltd"},
                  "hasPart": [{"@type": "Article", "headline": g["title"], "url": f"{SITE}/guides/{g['slug']}.html"} for g in guides]}
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
<title>Guides and data | Lambton Capital</title>
<meta name="description" content="Plain-English guides to commercial property and business finance in Australia, with worked examples, plus our quarterly lending data and deal notes.">
<link rel="canonical" href="{SITE}/guides/">
<meta property="og:title" content="Guides and data | Lambton Capital">
<meta property="og:description" content="Plain-English guides to commercial property and business finance in Australia, with worked examples, plus our quarterly lending data and deal notes.">
<meta property="og:image" content="{SITE}/img/og-lambton-capital.jpg">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="/fonts/ibm-plex-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/ibm-plex-serif-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../css/site.css">
<script type="application/ld+json">
{json.dumps(collection, indent=1)}
</script>
</head>
{body}

<main id="main">
  <section class="section-tight">
    <div class="wrap stack">
      <p class="eyebrow">Guides and data</p>
      <h1 class="h1">How commercial finance works, with the numbers.</h1>
      <p class="lead max-820">Plain-English guides to buying, refinancing and borrowing against commercial property and businesses in Australia. Each one has a worked example and says where its figures come from.</p>
    </div>
  </section>
  <section>
    <div class="wrap stack-lg">
      <h2 class="h2">Guides</h2>
      <div class="grid-3">{cards}</div>
    </div>
  </section>
  <section class="section-alt">
    <div class="wrap stack-lg">
      <h2 class="h2">Data and deal notes</h2>
      <div class="grid-3">{data_cards}</div>
    </div>
  </section>
  <section>
    <div class="wrap stack">
      <p class="body-sm max-820">General information only, not credit advice. Got a deal in mind? <a href="../contact.html">Send an early enquiry</a> and we'll reply in writing within two business days.</p>
    </div>
  </section>
</main>

{footer}"""
    (PUBLIC / "guides" / "index.html").write_text(page)


def update_home(guides):
    f = PUBLIC / "index.html"
    s = f.read_text()
    latest = sorted(guides, key=lambda g: g["updated"], reverse=True)[:3]
    cards = "".join(guide_card(g, "", "h3") for g in latest)
    block = (f'{HOME_START}\n  <section id="guides">\n    <div class="wrap stack-lg">\n      <p class="eyebrow">Guides and data</p>\n'
             f'      <h2 class="h2">How it works, with the numbers.</h2>\n      <p class="body ink-2">Plain-English guides with worked examples, and our quarterly lending data. <a href="guides/index.html">All guides and data</a>.</p>\n'
             f'      <div class="grid-3">{cards}</div>\n    </div>\n  </section>\n  {HOME_END}')
    if HOME_START in s:
        s = re.sub(re.escape(HOME_START) + r".*?" + re.escape(HOME_END), block, s, flags=re.S)
    else:
        s = s.replace('  <section id="deal-notes">', block + '\n\n  <section id="deal-notes">', 1)
    f.write_text(s)


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
        "image": f"{SITE}/img/{m['card_image']['base']}.webp" if m.get("card_image") else f"{SITE}/img/og-lambton-capital.jpg",
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
    m["body"] = photo_sections(m["body"], m)
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
<meta property="og:image" content="{SITE}/img/{m['card_image']['base'] + '.webp' if m.get('card_image') else 'og-lambton-capital.jpg'}">
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


def card_img(g, prefix):
    im = g.get("card_image")
    if not im:
        return ""
    base, alt, w, h = im["base"], im["alt"], im.get("width", 1400), im.get("height", 788)
    srcset = ", ".join(f'{prefix}img/{base}-{x}.webp {x}w' for x in im.get("variants", [])) + (", " if im.get("variants") else "") + f"{prefix}img/{base}.webp {w}w"
    return (f'<img loading="lazy" decoding="async" width="{w}" height="{h}" class="card-img" src="{prefix}img/{base}.webp" '
            f'srcset="{srcset}" sizes="(min-width:901px) 400px, 100vw" alt="{esc(alt)}">')


def guide_card(g, prefix, heading_tag="h2"):
    return (f'<article class="card card-flush">{card_img(g, prefix)}<div class="card-img-body">'
            f'<p class="label">Guide · updated {esc(g["updated_human"])}</p>'
            f'<{heading_tag} class="h3" style="margin:0;"><a href="{prefix}guides/{g["slug"]}.html">{esc(g["title"])}</a></{heading_tag}>'
            f'<p class="body-sm">{esc(g["description"])}</p></div></article>')


def photo_sections(body, g):
    """Turn the sections named in meta photo_sections into photo-backed sections (site pattern)."""
    for ps in g.get("photo_sections", []):
        sid, im, alt = ps["id"], ps["image"], ps["alt"]
        w, h = ps.get("width", 1600), ps.get("height", 1066)
        pat = re.compile(rf'<section( class="[^"]*")? id="{sid}"><div class="wrap stack">')
        img = (f'<section class="section-photo" id="{sid}">\n    <img src="../img/bg/{im}-1600.webp" srcset="../img/bg/{im}-800.webp 800w, ../img/bg/{im}-1600.webp 1600w" '
               f'sizes="100vw" alt="{esc(alt)}" loading="lazy" decoding="async" width="{w}" height="{h}">\n    <div class="section-photo-tint" aria-hidden="true"></div>\n    <div class="wrap stack section-photo-inner">')
        body, n = pat.subn(img, body, count=1)
        if not n:
            print("photo section not found:", sid)
    return body


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
    idx = f"{SITE}/guides/"
    newest = max(g["updated"] for g in guides)
    entry = f"  <url><loc>{idx}</loc><lastmod>{newest}</lastmod></url>\n"
    if idx + "</loc>" in s:
        s = re.sub(rf"  <url><loc>{re.escape(idx)}</loc><lastmod>[^<]*</lastmod></url>\n", entry, s)
    else:
        s = s.replace("</urlset>", entry + "</urlset>")
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
    build_index(gs)
    update_home(gs)
    print("nav/footer patched on", patch_nav_and_footer(), "pages")
    update_sitemap(gs)
    update_llms(gs)
