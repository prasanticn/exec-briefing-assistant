# Executive Briefing Assistant
**[▶ Try the live demo](https://prasanticn-exec-briefing.streamlit.app/)** (no sign-up needed)

Executives get a stack of dashboards every week but still can't quickly answer *"why did this number move?"*
This assistant answers business questions in plain English, such as *"Why are we losing SMB customers?"*, with an
executive-style briefing: a headline, the 2-4 drivers with numbers, a source for every number, and a suggested follow-up.
When the data can't answer a question, it says so instead of guessing.

Built with Python, Streamlit and Google's Gemini API, on a fictional company dataset (**Lumina Books**: monthly revenue
by region and segment, marketing spend, support tickets, and a log of business events).

## Results
I built an 18-question evaluation set with expected answers, including 3 questions the data can't answer, and improved
the assistant over six versions. Full history: [`evals/EVAL_LOG.md`](evals/EVAL_LOG.md).

| Version | Change | Correct answers |
|---|---|---|
| v1 | Baseline prompt | 10/18 (56%) |
| v2 | Prompt rules: add up every matching row, compare whole quarters | 13/18 |
| v3 | Totals computed in code and given to the model | 12/18 |
| v5 | More prompt rules | 10/18 |
| **v6** | **Fewer, clearer rules + monthly totals in code + consistent (temperature 0) answers** | **16/18 (89%)** |

All 3 "the data can't answer this" questions are answered correctly: no invented numbers.

## What I learned
- **Move the math out of the model.** Prompt rules fixed *what* to compare, but the model still added up long columns wrong
  (it reported Q3 revenue as $8.3M instead of $14.2M). Computing totals in code made every number-heavy answer correct.
- **More rules can make answers worse.** v5 added rules and dropped back to 10/18: answers got longer and contradicted
  themselves. v6 simplified and reached 16/18.
- **Check the grader.** Answers are graded by a second AI call, but a small grader model marked correct answers wrong, so
  from v3 on every answer was also checked by hand.
- **Model choice is a product trade-off.** Gemini 3.8 Flash answered 14 of 14 correctly but allows 20 free requests a day;
  Flash-Lite reached 89% with about 500 a day. The live demo uses Flash-Lite.

## How it works
1. Four CSV files of company data are loaded (`data/`).
2. Exact quarterly and monthly totals are computed with pandas (`build_summary()` in `briefing.py`).
3. The system prompt (answer rules), the totals and the raw data are sent to Gemini with the executive's question.
4. The answer comes back with a headline, drivers, `[file, period]` sources and a follow-up question.

| File | Purpose |
|---|---|
| `app.py` | Streamlit web app |
| `briefing.py` | System prompt, computed totals and the Gemini call |
| `evals/questions.csv` | 18 test questions with expected answers |
| `evals/run_evals.py` | Runs the test set, grades each answer, saves progress and resumes after rate limits |
| `evals/EVAL_LOG.md` | Every version, what changed, why, and the score |
| `PRD.md` | Product requirements: problem, users, success metrics, risks, launch plan |
| `data/`, `make_data.py` | The fictional dataset and the script that generates it |

## Run it yourself
```
pip install -r requirements.txt
streamlit run app.py
```
Paste a free Gemini API key (from aistudio.google.com) into the sidebar. To run the evaluation:
```
export GEMINI_API_KEY=your-key        # Windows PowerShell: $env:GEMINI_API_KEY="your-key"
python evals/run_evals.py
```

## What I'd build next
- Let the model call a calculation or SQL tool instead of relying on pre-computed tables, so it scales to real data.
- A larger evaluation set (50+ questions) with repeated runs, to separate real improvements from run-to-run noise.
- Charts generated per answer, a one-click board summary, and a Monday-morning briefing in Slack.

*Prasanti Cuttalambakkam Nadadur · [LinkedIn](https://www.linkedin.com/in/prasanticn/) · [Portfolio](https://prasanticn.notion.site/Prasanti-s-Portfolio-5aa8b21d49448253b46b0180aaaa4248)*
