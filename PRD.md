# PRD: Executive Briefing Assistant

*Draft by Prasanti C. N. · v0.1 · Fill in the [brackets] with your own words and results.*

## 1. Problem
Executives get 6+ dashboards a week but still can't quickly answer "why did this number move?" Getting an answer means pinging an analyst, which takes [1-3 days]. At Intuit I saw this firsthand while consolidating dashboards for VP/SVP planning reviews.

## 2. Target user
**Primary:** VP / SVP of a business unit preparing for a weekly business review or board meeting.
**Secondary:** Chief of staff / BizOps analyst who prepares those briefings today.

## 3. Goals and success metrics
| Goal | Metric | Target for v1 |
|---|---|---|
| Fast answers | Time from question to answer | < 30 seconds (vs. 1-3 days via analyst) |
| Trustworthy answers | % of test questions answered correctly with sources | ≥ 85% on the 18-question eval set |
| No made-up numbers | % of "unanswerable" questions where the assistant says it can't answer | 100% |
| Adoption (if piloted) | Weekly active execs / invited execs | [40%] in first quarter |

## 4. Key user stories
1. As a VP, I ask "how did Q3 go?" and get a headline, the 2-4 drivers with numbers, and sources.
2. As a VP, I ask "why" and get causes linked to real business events, clearly labeled as likely, not proven.
3. As a VP, when I ask something the data can't answer, I'm told so instead of getting a guess.
4. As a chief of staff, I can generate a 3-bullet board summary in one click.

## 5. Scope
**v1 (this prototype):** natural-language Q&A over 4 business datasets, cited answers, example questions, trend chart.
**Not in v1:** live database connections, user logins, permissions by role, editing data, forecasting.

## 6. How it works
Company data (CSV) → exact quarterly and monthly totals computed in code (pandas) → system prompt with answer rules + the totals + the raw data → Gemini Flash-Lite (temperature 0) → answer with headline, drivers, sources, follow-up question. The model reads totals instead of adding hundreds of rows itself.

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Hallucinated numbers | Prompt forbids invented numbers; eval set includes 3 "unanswerable" questions; sources required |
| Correlation presented as cause | Prompt requires "likely" wording; eval checks this |
| Exec over-trust | Every number cites its file and month so it can be checked |
| Data too large for prompt at scale | v2: query data with SQL tools instead of putting all data in the prompt |

## 8. Evaluation
18 test questions with expected answers (`evals/questions.csv`), graded automatically by a second model call and checked by hand. Full history in `evals/EVAL_LOG.md`.

**Results:** v1 prompt: 10/18 (56%) · final v6: **16/18 (89%)**, beating the 85% target. All 3 "unanswerable" questions answered correctly (100% target met).

**Biggest fix:** moving the math out of the model. Prompt rules (v2) fixed *what* to compare, but the model still added up 24 rows wrong (e.g. Q3 revenue $8.3M instead of $14.2M). Computing totals in code and handing the model a summary table made every number-heavy answer correct.

**Other lessons:**
- More rules isn't better: v5 added rules and dropped back to 10/18 because answers got cluttered and contradicted themselves. v6 simplified.
- The AI grader can't be trusted on its own: a small grader model marked correct answers wrong (agreed with my hand check on 14 of 18). From v3 on I hand-checked every answer.
- Model choice is a product trade-off: Gemini 3.8 Flash answered 14/14 correctly but allows 20 free requests a day; Flash-Lite reached 16/18 with ~500 a day. I shipped Flash-Lite.

## 9. Launch plan (if this were real)
Phase 1: pilot with [5] execs for weekly reviews → Phase 2: add live data sources → Phase 3: scheduled Monday-morning briefing emails. Adoption driven with the ADKAR change approach: awareness via a demo in staff meeting, ability via a 10-minute walkthrough.

## 10. What I'd build next
- **Tool use for the math:** let the model call a calculation/SQL tool for any total, instead of pre-computing a fixed set of tables. This scales to real data that won't fit in a prompt.
- **Bigger, auto-generated eval set:** 50+ questions with run-to-run averaging, so a 1-2 point change can be told apart from noise.
- **Charts per answer** and a one-click "board summary" export.
- **Slack integration** for a Monday-morning briefing, with role-based data access.
