# Executive Briefing Assistant (portfolio project starter)

Ask business questions in plain English ("Why are we losing SMB customers?") and get an executive-style answer
with numbers and sources, powered by Google's Gemini API (free tier, no card needed). The data is a fictional company, **Lumina Books**, with a few
real-world-style stories hidden in it (a price increase, a paused ad channel, a buggy release) for the AI to find.

## What's in this folder
| File | What it is |
|---|---|
| `app.py` | The web app (Streamlit) |
| `briefing.py` | The prompt and the Gemini call (this is where you'll iterate) |
| `data/` | 4 CSV files of fictional company data; `make_data.py` regenerates them |
| `evals/questions.csv` | 18 test questions with expected answers |
| `evals/run_evals.py` | Runs all test questions and scores them |
| `PRD.md` | Draft product requirements doc, fill in the [brackets] |

## Setup (about 20 minutes)
1. **Install Python 3.11+** (python.org), then in a terminal inside this folder run:
   `pip install -r requirements.txt`
2. **Get a free Gemini API key** at aistudio.google.com → Get API key (Google account, no card).
   Then either run `export GEMINI_API_KEY=...` (Mac) or paste the key into the app's sidebar.
3. **Run the app:** `streamlit run app.py`. It opens in your browser. Click an example question.
4. **Run the tests:** `python evals/run_evals.py`. Note your score.

## Plan: turn it into a portfolio piece (3 weekends)
**Weekend 1: make it work, get a baseline.** Run the app and the evals. Read the failed answers in `evals/results.csv`.
Record the v1 score in `PRD.md`.

**Weekend 2: improve it like a PM.** Change one thing at a time in `SYSTEM_PROMPT` in `briefing.py`
(or add a feature, like a "Board summary" button), re-run evals, and keep a short log:
"v2: told it to compare periods with % change → 14/18 to 16/18". This before/after story is the strongest part of the portfolio.
Optionally swap in your own fictional data set closer to the roles you want.

**Weekend 3: package it.**
- Deploy free on Streamlit Community Cloud (share.streamlit.io): push this folder to a GitHub repo, connect it,
  and add `GEMINI_API_KEY` under the app's *Secrets*.
- Record a 2-minute Loom: the problem (20s), live demo of 2 questions including one it correctly refuses (60s), eval results and what you'd build next (40s).
- Write a one-page portfolio case study from `PRD.md`: problem, users, metrics, what you built, eval results, learnings.
- Link it from the "Portfolio" on your resume and LinkedIn Featured section.

## Interview talking points this sets up
- Why I chose cited answers and "I don't know" behavior (trust is the adoption blocker for exec AI tools)
- How I measured quality (eval set, pass rate before/after) instead of eyeballing demos
- Working within free-tier rate limits, and what changes at real-world data sizes (SQL tools instead of putting all data in the prompt)
