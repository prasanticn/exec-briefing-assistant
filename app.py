"""Streamlit web app. Run with:  streamlit run app.py"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from google import genai
from google.genai import errors

from briefing import DATA_DIR, ask

st.set_page_config(page_title="Executive Briefing Assistant", page_icon="📊", layout="wide")
st.title("📊 Executive Briefing Assistant")
st.caption("Ask a business question in plain English. Answers come only from the company data, with sources. "
           "Data is fictional (Lumina Books, Jan 2025 to Sep 2026).")

EXAMPLES = [
    "How did Q3 2026 go compared to Q2?",
    "Why are we losing SMB customers?",
    "Which region needs attention right now?",
    "What happened with customer support in August?",
    "Was pausing Social ads a good decision?",
]

with st.sidebar:
    st.header("Try a question")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.question = q
    st.divider()
    st.header("The data")
    for path in sorted(DATA_DIR.glob("*.csv")):
        with st.expander(path.name):
            st.dataframe(pd.read_csv(path), use_container_width=True, hide_index=True)

def get_api_key() -> str:
    """Key comes from the environment, Streamlit secrets (when deployed), or the sidebar box."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:  # no secrets file when running locally
            key = ""
    return key or st.sidebar.text_input("Gemini API key", type="password")


api_key = get_api_key()
question = st.text_input("Your question", key="question", placeholder="e.g. Why did SMB revenue fall after July?")

if st.button("Get briefing", type="primary") and question:
    if not api_key:
        st.warning("Add your Gemini API key in the sidebar first (see README step 2).")
        st.stop()
    with st.spinner("Reading the numbers..."):
        try:
            answer = ask(question, genai.Client(api_key=api_key))
        except errors.ClientError as e:
            if e.code == 429:
                st.error("Free-tier limit reached. Wait a minute and try again.")
            elif e.code in (400, 401, 403):
                st.error("Your Gemini API key looks invalid. See STEP-BY-STEP.md, step 5.")
            else:
                st.error(f"Gemini error: {e.message}")
            st.stop()
        except errors.ServerError:
            st.error("Gemini is having trouble right now. Try again in a minute.")
            st.stop()
        except OSError:
            st.error("Couldn't reach Gemini. Check your internet connection.")
            st.stop()
    st.markdown(answer)

    # Simple chart so the executive can see the trend alongside the answer
    rev = pd.read_csv(Path(DATA_DIR) / "revenue_by_month.csv")
    st.subheader("Monthly revenue by segment")
    st.line_chart(rev.pivot_table(index="month", columns="segment", values="revenue_usd", aggfunc="sum"))
