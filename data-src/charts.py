"""Static, accessible SVG charts for the site (no JavaScript, no external libraries).

grouped_bars() returns a <figure> with an inline SVG: values printed on every bar (readable on phones and in
screenshots), a legend, role="img" plus an aria-label that states every value, and a figcaption with the source.
The data table on the page stays the source of truth; the chart is a picture of it.
"""
from html import escape

COLOURS = ["#8FA0AA", "#1E4B63", "#E0A21B", "#0F2A38"]  # oldest period first; latest in amber


def _fmt(v, dp, prefix, suffix):
    return f"{prefix}{v:,.{dp}f}{suffix}"


def grouped_bars(fig_id, title, categories, series, caption, dp=2, prefix="", suffix="", axis_from_zero=False):
    """categories: list of group labels. series: list of {"name": str, "values": [float|None per category]}."""
    w, h = 720, 360
    ml, mr, mt, mb = 16, 16, 56, 64
    vals = [v for s in series for v in s["values"] if v is not None]
    vmax = max(vals)
    vmin = 0 if axis_from_zero else min(vals)
    lo = 0 if axis_from_zero else max(0, vmin - (vmax - vmin) * 0.6 - 0.5)
    hi = vmax + (vmax - lo) * 0.12
    plot_w, plot_h = w - ml - mr, h - mt - mb
    gw = plot_w / len(categories)
    bw = min(56, gw * 0.8 / len(series))
    y = lambda v: mt + plot_h - (v - lo) / (hi - lo) * plot_h
    parts = []
    # legend
    lx = ml
    for i, s in enumerate(series):
        parts.append(f'<rect x="{lx}" y="14" width="14" height="14" rx="2" fill="{COLOURS[i % len(COLOURS)]}"/>'
                     f'<text x="{lx + 20}" y="26" class="ch-leg">{escape(s["name"])}</text>')
        lx += 20 + 8 * len(s["name"]) + 28
    # baseline
    parts.append(f'<line x1="{ml}" x2="{w - mr}" y1="{mt + plot_h}" y2="{mt + plot_h}" stroke="#D6DBD9"/>')
    for ci, cat in enumerate(categories):
        gx = ml + ci * gw + (gw - bw * len(series)) / 2
        for si, s in enumerate(series):
            v = s["values"][ci]
            if v is None:
                continue
            x, top = gx + si * bw, y(v)
            parts.append(f'<rect x="{x + 3:.1f}" y="{top:.1f}" width="{bw - 6:.1f}" height="{mt + plot_h - top:.1f}" rx="2" fill="{COLOURS[si % len(COLOURS)]}"/>'
                         f'<text x="{x + bw / 2:.1f}" y="{top - 6:.1f}" text-anchor="middle" class="ch-val">{escape(_fmt(v, dp, prefix, suffix))}</text>')
        parts.append(f'<text x="{ml + ci * gw + gw / 2:.1f}" y="{mt + plot_h + 24}" text-anchor="middle" class="ch-cat">{escape(cat)}</text>')
    if lo > 0:
        parts.append(f'<text x="{ml}" y="{mt + plot_h + 50}" class="ch-note">Bars start at {escape(_fmt(lo, dp, prefix, suffix))}, not zero, so the gaps are easier to see.</text>')
    label = f"{title}. " + "; ".join(
        f"{cat}: " + ", ".join(f"{s['name']} {_fmt(s['values'][ci], dp, prefix, suffix)}" for s in series if s["values"][ci] is not None)
        for ci, cat in enumerate(categories))
    svg = (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{escape(label)}" '
           f'style="display:block;max-width:{w}px;height:auto;font-family:var(--sans)">'
           '<style>.ch-val{font-size:13px;fill:#131C26;font-variant-numeric:tabular-nums}.ch-cat{font-size:14px;fill:#131C26}'
           '.ch-leg{font-size:13px;fill:#5B6770}.ch-note{font-size:12px;fill:#5B6770}</style>'
           + "".join(parts) + '</svg>')
    return (f'<figure class="card stack chart-figure" id="{escape(fig_id)}" style="margin:0;">'
            f'<p class="label" style="margin:0;">{escape(title)}</p>{svg}'
            f'<figcaption class="body-sm ink-2">{caption}</figcaption></figure>')
