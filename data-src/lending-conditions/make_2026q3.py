#!/usr/bin/env python3
"""Turn raw/2026q3-extract.json into editions/2026q3.json. All derived figures are computed here,
so the prose and the table can't disagree. Copy this file for the next quarter and update the text."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "raw/2026q3-extract.json").read_text())
f7, d1, d14, ap, cr = r["f7"], r["d1"], r["d14"], r["apra_qpex"], r["cash_rate"]

F7_URL = "https://www.rba.gov.au/statistics/tables/#interest-rates"
D14_URL = "https://www.rba.gov.au/statistics/tables/#money-credit"
D1_URL = d1["source_url"]
APRA_URL = ap["jun26_url"]
CR_URL = cr["source_url"]


def pts(a, b):
    return round(a - b, 2)


def growth(new, old):
    return round((new / old - 1) * 100, 1)


def v(value, period):
    return {"value": value, "period": period}


# Derived figures
prem = {k: pts(f7["FLRBFOSBV"][k], f7["FLRBFOLBV"][k]) for k in ("aug25", "jun26", "aug26")}
prem_new = {k: pts(f7["FLRBFNSBV"][k], f7["FLRBFNLBV"][k]) for k in ("aug25", "jun26", "aug26")}
resi_disc = {k: pts(f7["FLRBFOSBT"][k], f7["FLRBFOSBR"][k]) for k in ("aug25", "jun26", "aug26")}
cost_1m = {k: round(prem[k] * 10000) for k in prem}  # $ per year on $1m: points x $10,000
sb_g = {"aug26": growth(d14["DLBOST"]["aug26"], d14["DLBOST"]["aug25"]), "jun26": growth(d14["DLBOST"]["jun26"], d14["DLBOST"]["jun25"])}
mb_g = {"aug26": growth(d14["DLBOMT"]["aug26"], d14["DLBOMT"]["aug25"]), "jun26": growth(d14["DLBOMT"]["jun26"], d14["DLBOMT"]["jun25"])}
lb_g = {"aug26": growth(d14["DLBOLT"]["aug26"], d14["DLBOLT"]["aug25"]), "jun26": growth(d14["DLBOLT"]["jun26"], d14["DLBOLT"]["jun25"])}
sb_rise = pts(f7["FLRBFOSBV"]["aug26"], f7["FLRBFOSBV"]["aug25"])
lb_rise = pts(f7["FLRBFOLBV"]["aug26"], f7["FLRBFOLBV"]["aug25"])
cash_rise_window = pts(cr["31_aug_2026"], cr["31_aug_2025"])
not_yet = pts(cr["after_3_nov_2026"], cr["31_aug_2026"])
illus = round(f7["FLRBFOSBV"]["aug26"] + not_yet, 2)
cp_qq = growth(ap["exposures_bn"]["jun26"], ap["exposures_bn"]["mar26"])
cp_yy = growth(ap["exposures_bn"]["jun26"], ap["exposures_bn"]["jun25"])
headroom = round(ap["limits_bn"]["jun26"] - ap["exposures_bn"]["jun26"], 1)
sb_share = round(d14["DLBOST"]["aug26"] / (d14["DLBOST"]["aug26"] + d14["DLBOMT"]["aug26"] + d14["DLBOLT"]["aug26"]) * 100, 1)
tot_ago = d14["DLBOST"]["aug25"] + d14["DLBOMT"]["aug25"] + d14["DLBOLT"]["aug25"]
sb_share_ago = round(d14["DLBOST"]["aug25"] / tot_ago * 100, 1)
resi_share = round(r["d14_resi_aug26"] / d14["DLBOST"]["aug26"] * 100)
lb_add = round((d14["DLBOLT"]["aug26"] - d14["DLBOLT"]["aug25"]) / 1000, 1)
sb_add = round((d14["DLBOST"]["aug26"] - d14["DLBOST"]["aug25"]) / 1000, 1)

A26, J26, A25 = "Aug 2026", "Jun 2026", "Aug 2025"
f7m = lambda sid, metric, group="Business lending rates": {
    "group": group, "metric": metric, "unit": "% per year, average", "unit_suffix": "%", "dp": 2,
    "latest": v(f7[sid]["aug26"], A26), "prev": v(f7[sid]["jun26"], J26), "year_ago": v(f7[sid]["aug25"], A25),
    "series": f"RBA F7, {sid}", "source_name": "RBA statistical table F7", "source_url": F7_URL}
calc = lambda metric, unit, d, sfx, series, dp=2, pre="", url=F7_URL, src="Lambton Capital, from RBA F7": {
    "group": "Lambton Capital calculations", "metric": metric, "unit": unit, "unit_suffix": sfx, "dp": dp, "unit_prefix": pre,
    "latest": v(d.get("aug26"), A26), "prev": v(d.get("jun26"), J26),
    "year_ago": v(d.get("aug25"), A25) if d.get("aug25") is not None else None,
    "series": series, "source_name": src, "source_url": url}

metrics = [
    {"group": "Cash rate", "metric": "RBA cash rate target", "unit": "% per year", "unit_suffix": "%", "dp": 2,
     "latest": v(cr["after_3_nov_2026"], "after 3 Nov 2026 decision"), "prev": v(cr["30_jun_2026"], "30 Jun 2026"),
     "year_ago": v(cr["31_aug_2025"], "Nov 2025"), "series": "RBA table A2; Monetary Policy Decision 2026-30",
     "source_name": "RBA media release, 3 Nov 2026", "source_url": CR_URL},
    f7m("FLRBFOSBV", "Small business, variable rate, existing loans"),
    f7m("FLRBFOSBT", "Small business, all existing loans (fixed and variable)"),
    f7m("FLRBFOSBR", "Small business, existing loans secured by a home"),
    f7m("FLRBFOMBV", "Medium business, variable rate, existing loans"),
    f7m("FLRBFOLBV", "Large business, variable rate, existing loans"),
    f7m("FLRBFNSBV", "Small business, variable rate, new loans in the month"),
    f7m("FLRBFNLBV", "Large business, variable rate, new loans in the month"),
    calc("Small-business premium on existing variable loans (small minus large)", "percentage points", prem, " pts", "FLRBFOSBV − FLRBFOLBV"),
    calc("Small-business premium on new variable loans (small minus large)", "percentage points", prem_new, " pts", "FLRBFNSBV − FLRBFNLBV"),
    calc("Gap between all small-business loans and home-secured loans (average rate)", "percentage points", resi_disc, " pts", "FLRBFOSBT − FLRBFOSBR"),
    calc("Extra interest a small business pays per $1m borrowed, vs a large business", "$ per year", cost_1m, "", "Premium on existing variable loans × $1m", 0, "$"),
    calc("Growth in lending to small business, year on year", "% change in $ outstanding", sb_g, "%", "RBA D14, DLBOST", 1, "", D14_URL, "Lambton Capital, from RBA D14"),
    calc("Growth in lending to large business, year on year", "% change in $ outstanding", lb_g, "%", "RBA D14, DLBOLT", 1, "", D14_URL, "Lambton Capital, from RBA D14"),
    {"group": "Credit volumes", "metric": "Business credit growth, year on year (non-financial businesses)", "unit": "% change, seasonally adjusted", "unit_suffix": "%", "dp": 1,
     "latest": v(d1["DGFACBNF12"]["sep26"], "Sep 2026"), "prev": v(d1["DGFACBNF12"]["jun26"], J26), "year_ago": v(d1["DGFACBNF12"]["sep25"], "Sep 2025"),
     "series": "RBA D1, DGFACBNF12", "source_name": "RBA Financial Aggregates", "source_url": D1_URL},
    {"group": "Credit volumes", "metric": "Housing credit growth, year on year", "unit": "% change, seasonally adjusted", "unit_suffix": "%", "dp": 1,
     "latest": v(d1["DGFACH12"]["sep26"], "Sep 2026"), "prev": v(d1["DGFACH12"]["jun26"], J26), "year_ago": v(d1["DGFACH12"]["sep25"], "Sep 2025"),
     "series": "RBA D1, DGFACH12", "source_name": "RBA Financial Aggregates", "source_url": D1_URL},
    {"group": "Credit volumes", "metric": "Lending outstanding to small business", "unit": "$ billion", "unit_prefix": "$", "unit_suffix": "bn", "dp": 1,
     "latest": v(round(d14["DLBOST"]["aug26"]/1000, 1), A26), "prev": v(round(d14["DLBOST"]["jun26"]/1000, 1), J26), "year_ago": v(round(d14["DLBOST"]["aug25"]/1000, 1), A25),
     "series": "RBA D14, DLBOST", "source_name": "RBA statistical table D14", "source_url": D14_URL},
    {"group": "Credit volumes", "metric": "Lending outstanding to large business", "unit": "$ billion", "unit_prefix": "$", "unit_suffix": "bn", "dp": 1,
     "latest": v(round(d14["DLBOLT"]["aug26"]/1000, 1), A26), "prev": v(round(d14["DLBOLT"]["jun26"]/1000, 1), J26), "year_ago": v(round(d14["DLBOLT"]["aug25"]/1000, 1), A25),
     "series": "RBA D14, DLBOLT", "source_name": "RBA statistical table D14", "source_url": D14_URL},
    {"group": "Commercial property", "metric": "Bank (ADI) commercial property exposures", "unit": "$ billion", "unit_prefix": "$", "unit_suffix": "bn", "dp": 1,
     "latest": v(ap["exposures_bn"]["jun26"], J26), "prev": v(ap["exposures_bn"]["mar26"], "Mar 2026"), "year_ago": v(ap["exposures_bn"]["jun25"], "Jun 2025"),
     "series": "Quarterly ADI Property Exposures", "source_name": "APRA quarterly ADI statistics", "source_url": APRA_URL},
    {"group": "Commercial property", "metric": "Bank (ADI) commercial property exposure limits", "unit": "$ billion", "unit_prefix": "$", "unit_suffix": "bn", "dp": 1,
     "latest": v(ap["limits_bn"]["jun26"], J26), "prev": v(ap["limits_bn"]["mar26"], "Mar 2026"), "year_ago": v(ap["limits_bn"]["jun25"], "Jun 2025"),
     "series": "Quarterly ADI Property Exposures", "source_name": "APRA quarterly ADI statistics", "source_url": APRA_URL},
]
# Year-earlier cash rate period label: rate was 3.60% from 13 Aug 2025 until 4 Feb 2026
metrics[0]["year_ago"] = v(3.60, "Nov 2025")


# ABS Lending Indicators, September quarter 2026 (released 11 Nov 2026), read from the primary tables
abs_x = json.loads((HERE.parent / "event-notes/abs-lending-2026q3/extract.json").read_text())
ab = abs_x["business_sa_table29_560129"]; sbx = abs_x["small_business_original_table30_560130"]
ABS_URL = "https://www.abs.gov.au/statistics/economy/finance/lending-indicators/sep-quarter-2026"
def bn(x): return round(x / 1000, 1)
def pc(a, b): return round((b / a - 1) * 100, 1)
def abs_metric(metric, unit_note, d, series):
    return {"group": "Business lending commitments (ABS)", "metric": metric, "unit": f"$ billion, {unit_note}",
            "unit_prefix": "$", "unit_suffix": "bn", "dp": 1,
            "latest": v(bn(d["Sep-26"]), "Sep qtr 2026"),
            "prev": v(bn(d["Jun-26"]), "Jun qtr 2026") if "Jun-26" in d else v("", ""),
            "year_ago": v(bn(d["Sep-25"]), "Sep qtr 2025"),
            "series": series, "source_name": "ABS Lending Indicators", "source_url": ABS_URL}
metrics += [
    abs_metric("New business loans for construction", "seasonally adjusted", ab["construction"], "Table 29"),
    abs_metric("of which non-residential buildings", "seasonally adjusted", ab["construction_non_residential_buildings"], "Table 29"),
    abs_metric("New business loans to purchase property", "seasonally adjusted", ab["purchase_of_property"], "Table 29"),
    abs_metric("Small business new fixed term loans, excluding refinancing", "original (compare with a year earlier)", sbx["total_excl_refinancing"], "Table 30"),
    abs_metric("Small business loans to buy non-residential buildings", "original (compare with a year earlier)", sbx["purchase_non_residential_buildings"], "Table 30"),
]
abs_c = {k: pc(ab[k]["Jun-26"], ab[k]["Sep-26"]) for k in ab if isinstance(ab[k], dict)}
abs_y = {k: pc(ab[k]["Sep-25"], ab[k]["Sep-26"]) for k in ab if isinstance(ab[k], dict)}
sb_tot_y = pc(sbx["total_excl_refinancing"]["Sep-25"], sbx["total_excl_refinancing"]["Sep-26"])
sb_nr_y = pc(sbx["purchase_non_residential_buildings"]["Sep-25"], sbx["purchase_non_residential_buildings"]["Sep-26"])

edition = {
    "edition": "Q3 2026", "slug": "2026q3", "published": "2026-11-03", "published_human": "3 November 2026",
    "updated": "2026-11-11", "updated_human": "11 November 2026",
    "temporal_coverage": "2025-08/2026-11",
    "next_update": "late February 2027 (Q4 2026 edition)",
    "meta_description": (f"Small businesses paid {prem['aug26']} percentage points more than large businesses on variable loans in August 2026, "
                         f"while lending to large business grew {lb_g['aug26']}% vs {sb_g['aug26']}% for small. Quarterly data from RBA, APRA and ABS, with CSV."),
    "lead": (f"Small businesses are paying {prem['aug26']} percentage points more than large businesses to borrow, while their share of business lending has slipped. "
             f"With the cash rate now at {cr['after_3_nov_2026']}% after the fifth rise this year, here is where commercial and business lending stands, from the latest RBA, APRA and ABS data."),
    "headline_stats": [
        {"value": f"{cr['after_3_nov_2026']}%", "label": "RBA cash rate after the 3 Nov 2026 rise"},
        {"value": f"{prem['aug26']} pts", "label": "Extra a small business pays vs a large business, variable loans (Aug 2026)"},
        {"value": f"{sb_g['aug26']}%", "label": f"Growth in small-business lending, year to Aug 2026 (large business: {lb_g['aug26']}%)"},
        {"value": f"${ap['exposures_bn']['jun26']}bn", "label": f"Bank commercial property exposures, Jun 2026 (+{cp_yy}% on a year earlier)"},
    ],
    "stats_caption": "Sources: RBA statistical tables F7, D1, D14 and media release 2026-30; APRA quarterly ADI statistics; ABS Lending Indicators. Calculations by Lambton Capital.",
    "analysis": [
        {"question": "What are small businesses paying to borrow?",
         "answer": (f"The average rate on existing variable-rate small business loans was {f7['FLRBFOSBV']['aug26']}% in August 2026, "
                    f"up {sb_rise} points on a year earlier. Large businesses paid {f7['FLRBFOLBV']['aug26']}%."),
         "points": [
             f"On new variable loans written in August, small businesses paid {f7['FLRBFNSBV']['aug26']}% against {f7['FLRBFNLBV']['aug26']}% for large businesses.",
             f"Small business loans secured by a home averaged {f7['FLRBFOSBR']['aug26']}%, about {resi_disc['aug26']} points below the small business average of {f7['FLRBFOSBT']['aug26']}%. About {resi_share}% of small business lending is secured by a home (RBA D14, August 2026).",
             f"These figures predate the 30 September and 3 November rises ({not_yet:.2f} points in total). If both were passed on in full, the average existing variable small business rate would be about {illus}%. This is arithmetic, not a forecast or an RBA figure; lenders set their own rates.",
         ]},
        {"question": "How big is the small-business premium, and is it changing?",
         "answer": (f"Small businesses paid {prem['aug26']} percentage points more than large businesses on existing variable loans in August 2026, "
                    f"compared with {prem['aug25']} points a year earlier. On a $1 million loan, that gap is about ${cost_1m['aug26']:,} a year in extra interest."),
         "points": [
             f"The premium has barely moved: over the year to August, small business variable rates rose {sb_rise} points and large business rates {lb_rise} points, while the cash rate rose {cash_rise_window} points. Lenders passed rate rises on to both groups at about the same speed.",
             f"On new loans the gap is narrower and moves around month to month: {prem_new['aug26']:.2f} points in August 2026, {prem_new['jun26']:.2f} in June and {prem_new['aug25']:.2f} a year earlier.",
         ]},
        {"question": "Is credit flowing to small business?",
         "answer": (f"Less than the headline suggests. Business credit grew {d1['DGFACBNF12']['sep26']}% in the year to September 2026, well ahead of housing credit at {d1['DGFACH12']['sep26']}%. "
                    f"But lending to large businesses grew {lb_g['aug26']}% in the year to August, against {sb_g['aug26']}% for small businesses."),
         "points": [
             f"In dollar terms, large business lending rose about ${lb_add}bn over the year to August 2026; small business lending rose about ${sb_add}bn.",
             f"Small businesses' share of business lending in RBA table D14 slipped from {sb_share_ago}% to {sb_share}% over the year to August 2026.",
             "The size breakdown covers lenders that report business lending by borrower size; lending by non-bank lenders is only partly captured.",
         ]},
        {"question": "What's happening with bank lending to commercial property?",
         "answer": (f"Banks' commercial property exposures reached ${ap['exposures_bn']['jun26']}bn in June 2026, up {cp_yy}% on a year earlier and {cp_qq}% on the March quarter."),
         "points": [
             f"Approved limits were ${ap['limits_bn']['jun26']}bn, leaving about ${headroom}bn approved but not yet drawn.",
             "APRA publishes the September quarter figures in December 2026; they will be added to the next edition.",
         ]},
        {"question": "What did lenders commit to business borrowers in the September quarter?",
         "answer": (f"New business loans for construction rose {abs_c['construction']}% on the June quarter to ${bn(ab['construction']['Sep-26'])}b, "
                    f"while lending to buy property fell {abs(abs_c['purchase_of_property'])}% to ${bn(ab['purchase_of_property']['Sep-26'])}b (ABS, seasonally adjusted)."),
         "points": [
             f"Compared with a year earlier, construction lending was up {abs_y['construction']}% and property purchase lending up {abs_y['purchase_of_property']}%.",
             f"Small businesses took on ${bn(sbx['total_excl_refinancing']['Sep-26'])}b of new fixed term loans, {sb_tot_y}% more than a year earlier, but lending to buy non-residential buildings fell {abs(sb_nr_y)}%.",
         ],
         "link": {"href": "guides/business-lending-september-quarter-2026.html", "text": "Read the September quarter 2026 note"}},
    ],
    "method": ("Each quarter Lambton Capital collects the latest published figures from the Reserve Bank of Australia (RBA), the Australian Prudential Regulation Authority (APRA) and the Australian Bureau of Statistics (ABS), "
               "compares them with the previous quarter and a year earlier, and calculates the measures marked as Lambton Capital calculations. Rates are averages across all reporting lenders, "
               "not quotes. Growth in lending by business size is calculated from the RBA's D14 dollar figures, which are not adjusted for reporting changes, so treat single-month moves with care. "
               "Each figure shows the month or quarter it refers to; sources publish on different timetables, so not every figure covers the same period."),
    "metrics": metrics,
    "changelog": ["2026-11-03: first edition (Q3 2026).", "2026-11-11: added ABS Lending Indicators business lending commitments for the September quarter 2026 (released 11 November 2026)."],
}
(HERE / "editions").mkdir(exist_ok=True)
(HERE / "editions/2026q3.json").write_text(json.dumps(edition, indent=1, ensure_ascii=False))
print(json.dumps({"prem": prem, "prem_new": prem_new, "resi": resi_disc, "cost": cost_1m, "sb_g": sb_g, "mb_g": mb_g, "lb_g": lb_g,
                  "sb_rise": sb_rise, "lb_rise": lb_rise, "cash_window": cash_rise_window, "not_yet": not_yet, "illus": illus,
                  "cp_qq": cp_qq, "cp_yy": cp_yy, "headroom": headroom, "sb_share": sb_share, "lb_add": lb_add, "sb_add": sb_add}, indent=0))
