# Step-by-step: build the Executive Briefing Assistant

This guide assumes no coding background. Each step says what to do and how you know it worked.
Total time: about 3 weekends. Cost: free (Google's Gemini API free tier).

---

## Part A — Get it running (Day 1, about 1 hour)

### Step 1. Download the project
1. Download **ai-exec-briefing.zip** from the project chat.
2. Unzip it into an easy folder, e.g. `Documents/ai-exec-briefing`.

✅ You see `app.py`, `briefing.py`, `README.md`, and the `data` and `evals` folders.

### Step 2. Install Python
1. Go to **python.org/downloads** and install Python 3.12 or newer.
   - **Windows:** on the first installer screen, tick **"Add python.exe to PATH"**.
2. Open a terminal:
   - **Mac:** press Cmd+Space, type *Terminal*, press Enter.
   - **Windows:** press Start, type *PowerShell*, press Enter.
3. Type `python3 --version` (Mac) or `python --version` (Windows) and press Enter.

✅ It prints something like `Python 3.12.x`.

### Step 3. Open the project folder in the terminal
Type `cd ` (with a space), then drag the `ai-exec-briefing` folder into the terminal window, then press Enter.

✅ Typing `ls` (Mac) or `dir` (Windows) lists `app.py` and the other files.

### Step 4. Install the libraries
```
pip3 install -r requirements.txt
```
(On Windows use `pip` instead of `pip3`.)

✅ It ends with "Successfully installed …". Warnings in yellow are fine.

### Step 5. Get a free Gemini API key
1. Go to **aistudio.google.com** and sign in with a Google account.
2. Click **Get API key → Create API key** and copy it. No credit card is needed; just don't turn on billing.
3. Save it somewhere private. Never paste it into GitHub, LinkedIn or a screenshot.

Good to know about the free tier: it allows roughly 10 questions a minute and plenty per day, and Google may use
what you send to improve its models. That's fine here because the company data is made up, but don't paste real company data into it.

### Step 6. Run the app
```
streamlit run app.py
```
(If Mac says "command not found", use `python3 -m streamlit run app.py`.)

1. A browser tab opens at `localhost:8501`.
2. Paste your API key into the **Gemini API key** box at the bottom of the left sidebar and press Enter.
3. Click **"Why are we losing SMB customers?"**, then **Get briefing**.

✅ After 10–30 seconds you get a headline, 2–4 drivers with numbers, sources like `[revenue_by_month.csv, Jul–Sep]`, and a follow-up question.

To stop the app later, click the terminal and press Ctrl+C.

---

## Part B — Understand the data (Day 1, 30 minutes)

### Step 7. Explore it like an exec would
1. Open each CSV in the sidebar's **The data** section.
2. Ask the app 5–10 of your own questions, including one it *shouldn't* be able to answer (e.g. "What is our profit margin?").
3. Keep a note of answers that are wrong, vague or too long. These become what you fix in Part C.

The hidden stories in the data:
- **Jul 1, 2026:** SMB price up 15% → churn more than doubles in the West. Revenue rises at first, then SMB revenue drifts down.
- **Jul 1, 2026:** Social ads paused → SMB sign-ups down about 20%.
- **Aug 12, 2026:** buggy release → bug tickets nearly triple and satisfaction drops (fixed Aug 29).

---

## Part C — Measure and improve it like a PM (Weekend 2)

### Step 8. Get a baseline score
1. Set your key in the terminal so the test script can use it:
   - **Mac:** `export GEMINI_API_KEY=your-key`
   - **Windows:** `$env:GEMINI_API_KEY="your-key"`
2. Run:
   ```
   python3 evals/run_evals.py
   ```
   ✅ It prints PASS or FAIL for 18 questions and a score like `Score: 14/18`. It's free, but it pauses between questions to stay under the free limit, so a run takes about 5 minutes.
3. Open `evals/results.csv` in Excel or Google Sheets and read why each failure failed.
4. Write the score in `PRD.md`, section 8, as **v1**.

### Step 9. Improve one thing at a time
1. Open `briefing.py` in a text editor. VS Code (code.visualstudio.com) is free and easiest.
2. Edit only the text inside `SYSTEM_PROMPT`. Example changes:
   - "Always compare to the previous quarter and give % change."
   - "If the question is about a cause, list evidence for and against."
   - "Use bullet points; no more than 150 words."
3. Save, then rerun `python3 evals/run_evals.py`.
4. Log every attempt in a simple table, kept even when the score goes down:

| Version | What I changed | Why | Score |
|---|---|---|---|
| v1 | Original prompt | Baseline | 14/18 |
| v2 | Required % change vs prior period | Answers lacked comparison | 16/18 |

This log is your strongest interview story: it shows you measure quality instead of eyeballing a demo.

### Step 10 (optional). Add one feature
Ideas: a **"Board summary"** button that runs a preset question, a download button for the answer, or your own fictional dataset for an industry you're targeting (retail, fintech, healthcare). Use Claude, Claude Code or ChatGPT to help write the code: paste in `app.py` and describe the button you want.

---

## Part D — Publish it (Weekend 3)

### Step 11. Put the code on GitHub
1. Create a free account at **github.com**.
2. Click **New repository**, name it `exec-briefing-assistant`, make it **Public**, and create it.
3. Click **uploading an existing file**, drag in everything from the project folder, and click **Commit changes**.
   Don't upload any file containing your API key. The project files don't contain it.

### Step 12. Deploy a live demo (free)
1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **Create app**, pick your repository, and set the main file to `app.py`.
3. Under **Advanced settings → Secrets**, paste:
   ```
   GEMINI_API_KEY = "your-key"
   ```
4. Click **Deploy**.

✅ You get a public link like `exec-briefing-assistant.streamlit.app`. Anyone with the link uses your free quota; if it runs out, the app shows "limit reached" until it resets. It never charges you as long as billing stays off.

### Step 13. Record a 2-minute demo video
Use Loom (free) or Zoom recording:
- **0:00–0:20:** the problem: execs have many dashboards but can't quickly answer "why did this move?"
- **0:20–1:20:** live demo with 2 questions, including one it correctly refuses.
- **1:20–2:00:** your eval scores (v1 → final), and what you'd build next.

### Step 14. Write the case study page
Use **Notion**, Google Sites or a LinkedIn article. Structure it from `PRD.md`:
1. Problem and user
2. Success metrics
3. What I built (with a screenshot and the live link)
4. How I measured quality (the score table from Step 9)
5. What I learned, and what I'd build next

### Step 15. Put it everywhere
- Resume: link it from the "Portfolio" in her header, and add one bullet, e.g.
  *"Built and evaluated an AI executive-briefing assistant (Gemini API, Streamlit); improved answer accuracy from 14/18 to 17/18 through prompt iteration."* Use the real numbers.
- LinkedIn: add it to the **Featured** section, and write a short post with the video.
- Interviews: use it as the answer to "Tell me about an AI product you've worked on" or "How do you measure AI quality?"

---

## If something goes wrong
| Problem | Fix |
|---|---|
| `python3: command not found` | Reinstall Python; on Windows tick "Add to PATH", then use `python` |
| `streamlit: command not found` | Use `python3 -m streamlit run app.py` |
| "API key looks invalid" | Re-copy the key from aistudio.google.com; no spaces before or after it |
| "Free-tier limit reached" | Wait a minute and try again (or until tomorrow if the daily limit is used up) |
| Error mentioning the model name | Google may have renamed it. Check the model list at ai.google.dev, then set it with `export GEMINI_MODEL=new-name` |
| Anything else | Copy the full error into Claude and ask what it means |
