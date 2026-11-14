# Eval log — Executive Briefing Assistant

Model: gemini-3.1-flash-lite (answers and grading). 18 test questions in `questions.csv`.
Each version's full results are saved as `results_vN_*.csv`.

| Version | What I changed | Why | Score |
|---|---|---|---|
| v1 | Original prompt | Baseline | 10/18 (56%) |
| v2 | Prompt: rules for adding up all matching rows, comparing whole quarters, checking totals, and checking marketing for sign-up changes | 7 of 8 failures were wrong sums or single months instead of quarters; 2 missed the Social ads pause | 13/18 (72%) |
| v3 | Code: compute exact quarterly totals (by segment, region, channel) with pandas and give them to the model as a summary table | v2 fixed periods and the marketing total, but the model still added up 24 rows wrong (Q1 had the right % but wrong dollars) | 12/18 by AI grader; 12/18 by hand check |
| v4 (grader) | Stricter grader rules (answer-key facts only, ignore follow-up, name the missing fact); re-graded v1–v3's saved answers | The old grader failed 2 correct v3 answers | v1: 5 · v2: 6 · v3: 7 — worse: Flash-Lite as judge invented "missing" facts (Q3, Q4) and my citation rule wrongly failed correct "can't answer" replies (Q14, Q15). Reverted to hand check as ground truth |
| v5 | Prompt: month-by-month for "right now"/trend and month questions; check every event in the period; churn AND new customers; include CSAT. Grader: stronger model (gemini-3.6-flash), no citation needed for "can't answer", read the whole answer | v3's 6 real misses: too quarter-focused (Q2, Q9, Q10) and missed secondary causes (Q5, Q7, Q18) | 10/18 by grader (3.6 Flash); 10/18 by hand check — no net gain |
| v6 | Prompt: lighter "why" rule (no "mention every event"), explicit suggestions for "what should we do", say "can't isolate" first, headline must match details. Code: monthly totals by segment; temperature 0. Plan: run twice to measure run-to-run noise | v5 fixed Q9 and partly Q5/Q10, but answers got cluttered and new misses appeared (Q13 headline contradicts its own list, Q16 illogical claim, Q17, Q18 no recommendations); Q2 monthly sums still wrong ($3.25M vs actual $3.11M) | |

## v1 failure analysis
- Wrong totals from adding only some rows (Q1, Q3, Q11, Q13: $264K total for parts adding to $444K).
- Compared single months instead of whole quarters (Q4, Q12).
- Missed the Social ads pause as the cause of fewer sign-ups (Q5, Q6).
- Note: grading is done by an AI, so a ±1 change between runs can be noise.

## v2 notes
- Fixed: marketing total ($444K), quarter-vs-quarter comparisons (Q4, Q12), Social ads pause for sign-ups (Q6).
- Still wrong: long sums (Q1 $8.28M vs actual $14.21M; Q3; Q11). Q7 regressed (lead totals added wrong; partly grader noise).
- Lesson: prompt rules fix *what* to compare, but not the model's arithmetic. Move the math into code.

## v3 notes
- Fixed: every number-heavy question now has correct totals (Q1 $14.21M vs $12.76M, Q3, Q11).
- Hand check (corrected): 12/18. Real misses: Q2, Q5, Q7, Q9, Q10, Q18.
- Grader mistakes (hand-checked; answers were correct): Q4 (had West 754 -> 1,625 with citations), Q12 (had West $4.75M; grader treated the suggested follow-up as an unanswered question).
- Real misses: Q2 "right now" answered with quarter totals instead of the month-by-month trend; Q9 quarter totals instead of July and no CSAT; Q10 wrongly said CSAT data was missing; Q5 and Q7 missed the Social ads pause / Social leads (1,877 -> 0); Q18 left out the Sep 15 win-back campaign.
- Lesson: the AI grader itself makes mistakes, so scores move by a few points between runs. Fixing the grader is the next step before trusting small differences.

## v4 notes
- A stricter grader on a small model (Flash-Lite) was *less* accurate, not more: it called facts missing that were in the answer.
- Lesson: an AI judge needs to be checked against human labels. Use a stronger judge model and keep a hand-checked score as ground truth.

## v5 notes
- Grader (3.6 Flash) and hand check agreed on 16 of 18; they disagreed on Q3 (grader over-strict on citation) and Q16 (grader too lenient: answer never said the effect can't be isolated).
- Fixed vs v3: Q9 (July, CSAT), Q10 now has CSAT, Q5 now covers the Social ads pause.
- New misses: Q13, Q16, Q17, Q18. Lesson: piling on rules makes answers longer and introduces new errors; each fix needs to be re-tested on everything.
- With temperature unset, the same prompt gives different answers each run, so +/-2 points can be noise. v6 sets temperature 0 and runs twice.

## v6 on Gemini 3.8 Flash (partial: 14 of 18 questions, daily limit hit)
- This run used gemini-3.8-flash as the assistant (not Flash-Lite), graded by gemini-3.6-flash. Saved as `results_v6_flash38_partial.csv`.
- Grader: 11/14. Hand check: 14/14 (13/14 if strict on Q2). Grader false fails: Q3 (citation strictness), Q7 (answer correctly said new Enterprise customers fell 69 -> 63; key only mentions revenue growth).
- Monthly numbers now correct (Q2: $3.11M Jul -> $3.01M Sep), every number-heavy answer correct, "can't isolate" stated first (Q7).
- Not directly comparable to v1–v5 (different model). Needed: v6 on Flash-Lite to separate the prompt effect from the model effect.
