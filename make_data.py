"""Generates the fictional company data used by the app (run once; output is already in data/).

The company is "Lumina Books", a made-up SaaS accounting tool for small businesses.
A few real-world-style stories are planted in the numbers so the assistant has
something to find:
  * Jul 2026: 15% price increase on the SMB plan -> SMB churn jumps, worst in the West.
  * Jul 2026: Social ads paused to fund Events -> fewer SMB new customers in Q3.
  * Aug 2026: checkout bug in release v4.2 (fixed Aug 29) -> bug tickets spike, CSAT drops.
  * Enterprise and International keep growing and partly offset the SMB dip.
"""
import csv, random
from pathlib import Path

random.seed(7)
OUT = Path(__file__).parent / "data"
months = [f"{y}-{m:02d}" for y in (2025, 2026) for m in range(1, 13)][:21]  # Jan 2025 .. Sep 2026

regions = {"West": 1.30, "East": 1.10, "Central": 0.80, "International": 0.60}
price = {"SMB": 120, "Enterprise": 2400}  # monthly revenue per customer

def after(month, start):
    return month >= start

rows = []
for region, size in regions.items():
    for seg in ("SMB", "Enterprise"):
        active = int((4000 if seg == "SMB" else 90) * size)
        for i, m in enumerate(months):
            growth = 1 + 0.012 * i
            if seg == "SMB":
                new = int(260 * size * growth * random.uniform(0.93, 1.07))
                if after(m, "2026-07"):  # social ads paused
                    new = int(new * 0.80)
                churn_rate = 0.035
                if after(m, "2026-07"):  # price increase
                    churn_rate = 0.072 if region == "West" else 0.052
                unit_price = price[seg] * (1.15 if after(m, "2026-07") else 1.0)
            else:
                new = int(5 * size * growth * random.uniform(0.8, 1.2)) + (2 if region == "International" and after(m, "2026-01") else 0)
                churn_rate = 0.010
                unit_price = price[seg] * (1.04 if after(m, "2026-01") else 1.0)
            churned = int(active * churn_rate * random.uniform(0.92, 1.08))
            active = active + new - churned
            revenue = round(active * unit_price, -2)
            rows.append([m, region, seg, new, churned, active, int(revenue)])

with open(OUT / "revenue_by_month.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "region", "segment", "new_customers", "churned_customers", "active_customers", "revenue_usd"])
    w.writerows(rows)

with open(OUT / "marketing_spend.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "channel", "spend_usd", "leads"])
    for i, m in enumerate(months):
        for ch, base, cpl in (("Search", 180000, 95), ("Social", 120000, 70), ("Events", 60000, 240), ("Partners", 40000, 130)):
            spend = base * (1 + 0.01 * i)
            if ch == "Social" and after(m, "2026-07"):
                spend = 0
            if ch == "Events" and after(m, "2026-07"):
                spend = base * 3.0
            leads = int(spend / (cpl * random.uniform(0.9, 1.1))) if spend else 0
            w.writerow([m, ch, int(round(spend, -3)), leads])

with open(OUT / "support_tickets.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["month", "category", "tickets", "avg_resolution_hours", "csat_pct"])
    for i, m in enumerate(months):
        for cat, base in (("Billing", 900), ("Bugs", 1100), ("Onboarding", 700), ("Feature requests", 500)):
            t, hrs, csat = base * random.uniform(0.92, 1.08), random.uniform(9, 13), random.uniform(86, 91)
            if cat == "Billing" and m in ("2026-07", "2026-08"):
                t, csat = t * 2.1, csat - 9
            if cat == "Bugs" and m == "2026-08":
                t, hrs, csat = t * 2.6, hrs * 2.2, csat - 17
            w.writerow([m, cat, int(t), round(hrs, 1), round(csat, 1)])

with open(OUT / "business_events.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "team", "event"])
    w.writerows([
        ["2025-03-10", "Product", "Launched mobile receipt scanning"],
        ["2025-09-02", "Sales", "Opened London office to sell Enterprise plan internationally"],
        ["2026-01-01", "Finance", "Enterprise plan list price raised 4%"],
        ["2026-04-20", "Product", "Released AI bookkeeping assistant (beta)"],
        ["2026-07-01", "Finance", "SMB plan price raised 15% ($120 to $138 per month)"],
        ["2026-07-01", "Marketing", "Paused all Social ads; budget moved to Events for Enterprise pipeline"],
        ["2026-08-12", "Engineering", "Release v4.2 shipped with a checkout bug affecting card payments"],
        ["2026-08-29", "Engineering", "Checkout bug fixed in v4.2.1"],
        ["2026-09-15", "Customer Success", "Started win-back email campaign for churned SMB customers"],
    ])
print("wrote", *sorted(p.name for p in OUT.iterdir()))
