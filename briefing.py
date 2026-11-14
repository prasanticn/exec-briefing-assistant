"""Core logic: load the company data and ask Gemini to answer an executive's question."""
import os
from pathlib import Path

import pandas as pd

from google import genai
from google.genai import types

DATA_DIR = Path(__file__).parent / "data"
# Free-tier Gemini model. Flash-Lite allows ~500 requests/day free (Flash: 20/day), so it is the default.
# To try another, set GEMINI_MODEL (e.g. gemini-3.8-flash).
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

SYSTEM_PROMPT = """You are an analyst who briefs busy executives at Lumina Books, a SaaS accounting tool for small businesses.
You answer questions using ONLY the company data provided below.

How to answer:
- Start with a one-sentence headline answer.
- Then give the 2-4 biggest drivers, each with the specific numbers behind it (compare periods, show % change).
- Cite where each number came from as [file name, month(s)].
- Connect numbers to the business events log when the timing lines up, but say "likely" when you are inferring cause.
- If the data cannot answer the question, say so plainly and say what data would be needed. Never invent numbers.
- End with one suggested follow-up question the executive should ask next.
- Keep it under 200 words unless asked for more. Quarters: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec.

How to get the numbers right:
- The data runs from Jan 2025 to Sep 2026. revenue_by_month.csv has one row per month, region and segment.
- For any total, add up EVERY matching row: all 4 regions and both segments unless the question names one,
  and all 3 months when the question is about a quarter. A quarter total for the whole company is 24 rows.
- When the question names a quarter (e.g. Q3), compare the whole quarter with the previous whole quarter
  (Q3 vs Q2), not single months.
- When the question names a month, or asks about "right now", "currently", "lately" or a trend, use the
  "by month and segment" summary for the most recent months (e.g. Jul, Aug, Sep 2026) and say which direction they are moving.
  Quarter totals can hide a recent decline.
- Otherwise, if no period is named, use the latest quarter (Q3 2026) vs Q2 2026.
- Check your arithmetic before answering: any total you state must equal the sum of the parts you list.
- A PRE-COMPUTED SUMMARY with exact quarterly totals comes before the raw data. Use its numbers for any
  quarter, segment, region or channel total instead of adding raw rows yourself. Use the raw rows only for
  single-month detail. Cite summary numbers with the underlying file, e.g. [revenue_by_month.csv, Q3 2026].
- When new customers or sign-ups change, check marketing_spend.csv and the events log for channel changes
  (e.g. ads paused or budget moved), not only pricing.
- For "why" questions, check the events log for that period and name the events whose timing matches.
  Customer counts fall from two sides: more churn AND fewer new customers; cover both, and say which region is worst.
- For "what should we do" questions, give 2-3 concrete suggestions, clearly labeled as suggestions (not facts),
  and mention any action already taken (e.g. a campaign in the events log) and what the data shows since.
- If the data cannot isolate the effect of something (e.g. a launch), say that first, before any other numbers.
- Your headline must agree with the details below it (e.g. don't say "only Search and Events" and then list Partners).
- support_tickets.csv has tickets, avg_resolution_hours and csat_pct for each month and category.
  Include CSAT when talking about support quality or recovery.
"""


def load_data_text() -> str:
    """Returns every CSV in data/ as one text block for the prompt."""
    parts = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        parts.append(f"=== {path.name} ===\n{path.read_text().strip()}")
    return "\n\n".join(parts)


def _quarter(month_col: pd.Series) -> pd.Series:
    return pd.PeriodIndex(month_col, freq="M").asfreq("Q").astype(str).str.replace("Q", " Q")


def _table(df: pd.DataFrame) -> str:
    return df.to_csv(index=False).strip()


def build_summary() -> str:
    """Exact quarterly totals computed in code, so the model reads numbers instead of adding long columns."""
    rev = pd.read_csv(DATA_DIR / "revenue_by_month.csv")
    rev["quarter"] = _quarter(rev["month"])
    last_month = rev.groupby("quarter")["month"].transform("max")

    def by(keys):
        flows = rev.groupby(keys, as_index=False)[["revenue_usd", "new_customers", "churned_customers"]].sum()
        active = (rev[rev["month"] == last_month].groupby(keys, as_index=False)["active_customers"].sum()
                  .rename(columns={"active_customers": "active_customers_end_of_quarter"}))
        return flows.merge(active, on=keys)

    mkt = pd.read_csv(DATA_DIR / "marketing_spend.csv")
    mkt["quarter"] = _quarter(mkt["month"])
    mkt_month = mkt.groupby("month", as_index=False)[["spend_usd", "leads"]].sum()
    mkt_q = mkt.groupby(["quarter", "channel"], as_index=False)[["spend_usd", "leads"]].sum()

    tix = pd.read_csv(DATA_DIR / "support_tickets.csv")
    tix["quarter"] = _quarter(tix["month"])
    tix_q = tix.groupby(["quarter", "category"], as_index=False).agg(
        tickets=("tickets", "sum"), avg_resolution_hours=("avg_resolution_hours", "mean"), avg_csat_pct=("csat_pct", "mean"))
    tix_q[["avg_resolution_hours", "avg_csat_pct"]] = tix_q[["avg_resolution_hours", "avg_csat_pct"]].round(1)

    recent = rev[rev["month"] >= "2026-01"]
    by_month = (recent.groupby(["month", "segment"], as_index=False)
                [["revenue_usd", "new_customers", "churned_customers", "active_customers"]].sum())

    sections = {
        "Company totals by quarter (all regions, both segments)": by(["quarter"]),
        "Totals by month and segment, 2026 (all regions)": by_month,
        "Totals by quarter and segment (all regions)": by(["quarter", "segment"]),
        "Totals by quarter, region and segment": by(["quarter", "region", "segment"]),
        "Marketing by month (all channels)": mkt_month,
        "Marketing by quarter and channel": mkt_q,
        "Support tickets by quarter and category": tix_q,
    }
    return "\n\n".join(f"--- {title} ---\n{_table(df)}" for title, df in sections.items())


def ask(question: str, client: genai.Client | None = None) -> str:
    client = client or genai.Client()  # reads the GEMINI_API_KEY environment variable
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            temperature=0,  # same question -> (nearly) the same answer, so eval runs are comparable
            system_instruction=(SYSTEM_PROMPT + "\n\nPRE-COMPUTED SUMMARY (exact):\n\n" + build_summary()
                                + "\n\nCOMPANY DATA (raw rows):\n\n" + load_data_text()),
        ),
    )
    return response.text or "Sorry, I couldn't produce an answer to that one."
