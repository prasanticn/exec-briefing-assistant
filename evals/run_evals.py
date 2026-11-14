"""Runs every test question through the assistant and has Gemini grade each answer.

Usage:  python evals/run_evals.py
Writes evals/results.csv and prints the pass rate. Re-run after every prompt change
and record the score in evals/EVAL_LOG.md.
It pauses between calls to stay under the free tier's per-minute limit, so a full run takes about 5 minutes.

If Google's servers are busy (503) or the per-minute limit is hit, it waits and retries automatically.
Each graded question is saved to evals/progress.csv as it goes, so if the run stops (for example the
daily limit runs out), just run the same command again and it picks up where it left off.
Progress is only reused while SYSTEM_PROMPT, the grader and the model are unchanged; edit any and it starts fresh.

Re-grade saved answers without asking the assistant again (18 calls instead of 36), e.g. to score
every earlier version with the same grader:
    python evals/run_evals.py --regrade evals/results_v1_baseline.csv
This writes evals/regraded_<file name>.csv and prints the new score.
"""
import csv
import hashlib
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import errors

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from briefing import MODEL, SYSTEM_PROMPT, ask  # noqa: E402

HERE = Path(__file__).parent
PROGRESS = HERE / "progress.csv"
# The grader can be a different (stronger) model than the assistant, e.g.  $env:GRADER_MODEL="gemini-3.6-flash"
GRADER_MODEL = os.environ.get("GRADER_MODEL", MODEL)
PAUSE_SECONDS = 8  # free tier allows roughly 10 requests per minute
RETRY_WAITS = [20, 45, 90, 180]  # seconds to wait before each retry when the API is busy

GRADER_PROMPT = """You are grading an AI analyst's answer to an executive's question against an answer key.

Question: {question}
Answer key (the facts that must be present; numbers may be rounded differently): {expected}
Actual answer: {actual}

Grade ONLY against the answer key:
- PASS if every key fact in the answer key is present and correct (small rounding differences of a few percent are fine)
  and the numbers it states come with a source in square brackets, e.g. [revenue_by_month.csv, Q3 2026].
- Read the whole answer carefully before deciding a fact is missing; facts may be phrased differently than in the key.
- Extra details that are not in the answer key are fine. Do not treat them as invented unless they contradict the key.
- If the key numbers are present, comparing them with a different but sensible earlier period is fine.
- The "suggested follow-up question" at the end is a suggestion for the executive. Do not require it to be answered.
- FAIL if a key fact is missing or wrong, if a number contradicts the answer key, or if the answer states as certain
  a cause that the answer key says is only likely or can't be proven.
- If the answer key says the data can't answer the question, PASS if the answer clearly says that and does not
  make up a number. No citation is needed in that case.

Reply with PASS or FAIL on the first line. On the second line, name the specific key fact that was missing or wrong
(or "All key facts present" for PASS)."""


class DailyLimitReached(Exception):
    pass


def with_retries(fn, *args):
    """Calls fn(*args), waiting and retrying when Google is busy or the per-minute limit is hit."""
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            return fn(*args)
        except (errors.ServerError, errors.ClientError) as e:
            code = getattr(e, "code", None)
            text = str(e).lower()
            if code == 429 and "per day" in text:
                raise DailyLimitReached() from e
            if code not in (429, 500, 502, 503, 504) or attempt == len(RETRY_WAITS):
                raise
            wait = RETRY_WAITS[attempt]
            reason = "Google's servers are busy" if code != 429 else "per-minute limit reached"
            print(f"   ...{reason} ({code}). Waiting {wait}s and retrying...")
            time.sleep(wait)


def grade(client, question, expected, actual):
    response = client.models.generate_content(
        model=GRADER_MODEL,
        contents=GRADER_PROMPT.format(question=question, expected=expected, actual=actual),
    )
    text = (response.text or "").strip()
    verdict = "PASS" if text.upper().startswith("PASS") else "FAIL"
    reason = text.split("\n", 1)[1].strip() if "\n" in text else text
    return verdict, reason


def run_fingerprint():
    return hashlib.sha1((MODEL + GRADER_MODEL + SYSTEM_PROMPT + GRADER_PROMPT).encode("utf-8")).hexdigest()[:10]


def load_progress(fingerprint):
    if not PROGRESS.exists():
        return {}
    with open(PROGRESS, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or rows[0].get("run_id") != fingerprint:
        return {}  # prompt or model changed since last time: start fresh
    return {r["id"]: r for r in rows}


def save_progress(rows):
    with open(PROGRESS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def regrade(path_text):
    """Grades answers saved in an earlier results file again, without asking the assistant again."""
    client = genai.Client()
    src = Path(path_text)
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"Re-grading {len(rows)} saved answers from {src.name} with {GRADER_MODEL}\n")
    out = []
    try:
        for r in rows:
            verdict, reason = with_retries(grade, client, r["question"], r["expected_answer"], r["actual_answer"])
            time.sleep(PAUSE_SECONDS)
            print(f"[{verdict}] {r['id']}. {r['question']}   (was {r['verdict']})")
            out.append({**r, "verdict": verdict, "grader_reason": reason, "previous_verdict": r["verdict"]})
    except DailyLimitReached:
        print(f"\nDaily free limit reached for {GRADER_MODEL}. Run it again after midnight Pacific time.")
        return
    dest = src.with_name(f"regraded_{src.name}")
    with open(dest, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    passed = sum(r["verdict"] == "PASS" for r in out)
    print(f"\nRe-graded score: {passed}/{len(out)} passed. Details in evals/{dest.name}")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--regrade":
        return regrade(sys.argv[2])
    client = genai.Client()  # reads the GEMINI_API_KEY environment variable
    with open(HERE / "questions.csv", encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    fingerprint = run_fingerprint()
    done = load_progress(fingerprint)
    if done:
        print(f"Resuming: {len(done)} of {len(questions)} questions already graded with this prompt and model.\n")
    print(f"Assistant model: {MODEL}   Grader model: {GRADER_MODEL}\n")

    results = []
    try:
        for q in questions:
            if q["id"] in done:
                r = done[q["id"]]
                print(f"[{r['verdict']}] {q['id']}. {q['question']}  (saved)")
                results.append(r)
                continue
            actual = with_retries(ask, q["question"], client) or ""
            time.sleep(PAUSE_SECONDS)
            verdict, reason = with_retries(grade, client, q["question"], q["expected_answer"], actual)
            time.sleep(PAUSE_SECONDS)
            print(f"[{verdict}] {q['id']}. {q['question']}")
            results.append({"run_id": fingerprint, **q, "actual_answer": actual,
                            "verdict": verdict, "grader_reason": reason})
            save_progress(results)
    except DailyLimitReached:
        print(f"\nDaily free limit reached (assistant {MODEL} / grader {GRADER_MODEL}) after {len(results)} of {len(questions)} questions.")
        print("Your progress is saved. Run the same command again after midnight Pacific time,")
        print("or switch to another model, e.g.  $env:GEMINI_MODEL=\"gemini-3.5-flash-lite\"  (this starts fresh).")
        return

    with open(HERE / "results.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)
    PROGRESS.unlink(missing_ok=True)
    passed = sum(r["verdict"] == "PASS" for r in results)
    print(f"\nScore: {passed}/{len(results)} passed (assistant {MODEL}, grader {GRADER_MODEL}). Details in evals/results.csv")


if __name__ == "__main__":
    main()
