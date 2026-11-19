"""pages/09_NLP_Analyser.py — Dual market NLP job description analyser."""
import streamlit as st
import pandas as pd
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css
from utils.market import get_market_data, format_salary, market_label, is_india, get_top_skills
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="🧠 NLP Analyser", page_icon="🧠")
inject_css(); render_theme_css()
if not require_login(): st.stop()
show_sidebar()

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD"

with st.spinner("Loading…"):
    df = get_market_data()
    salary_df = df[df["normalized_salary"].notna()].copy()
    known_skills = get_top_skills(300)

st.markdown(f"# 🧠 NLP Job Description Analyser {flag}")
st.markdown(f"*{market_label()} — Paste any job description to extract skills and estimate salary*")
st.divider()

job_text = st.text_area(
    "Paste a job description",
    height=250,
    placeholder="Paste the full job posting text here…"
)
analyse = st.button("🔍 Analyse Job Description", use_container_width=True)

if analyse and job_text.strip():
    text_lower = job_text.lower()

    # ── 1. Skill Extraction ──────────────────────────────────────────────────
    found_skills = []
    for skill in known_skills:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    found_skills = list(dict.fromkeys(found_skills))[:25]  # dedupe, cap at 25

    # ── 2. Experience Detection ──────────────────────────────────────────────
    exp_match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*years?", text_lower)
    exp_single = re.search(r"(\d+)\+?\s*years?", text_lower)
    if exp_match:
        min_exp, max_exp = int(exp_match.group(1)), int(exp_match.group(2))
    elif exp_single:
        min_exp = int(exp_single.group(1))
        max_exp = min_exp + 3
    else:
        min_exp, max_exp = 2, 5

    # ── 3. Education Detection ───────────────────────────────────────────────
    education = "Not specified"
    if re.search(r"\bphd\b|doctorate", text_lower):
        education = "PhD"
    elif re.search(r"\bmaster'?s?\b|\bm\.?tech\b|\bm\.?s\.?\b|\bmba\b", text_lower):
        education = "Master's Degree"
    elif re.search(r"\bbachelor'?s?\b|\bb\.?tech\b|\bb\.?sc\b|\bb\.?e\.?\b", text_lower):
        education = "Bachelor's Degree"

    # ── 4. Remote Detection ──────────────────────────────────────────────────
    if re.search(r"\bremote\b|work from home|\bwfh\b", text_lower):
        remote_status = "Remote"
    elif re.search(r"\bhybrid\b", text_lower):
        remote_status = "Hybrid"
    else:
        remote_status = "On-site"

    # ── 5. Salary Sentiment Scoring ──────────────────────────────────────────
    senior_kw = ["senior","lead","principal","architect","staff","head of","director"]
    junior_kw = ["intern","entry level","junior","fresher","trainee","graduate"]
    score = sum(2 for k in senior_kw if k in text_lower) - \
            sum(2 for k in junior_kw if k in text_lower)
    score += min_exp * 0.5

    explicit_salary = re.findall(r"[₹$]\s?[\d,]+(?:\.\d+)?\s?(?:lpa|k|lakh)?", text_lower)

    if not salary_df.empty:
        if score >= 6:
            est_low, est_high = (salary_df["normalized_salary"].quantile(0.75),
                                 salary_df["normalized_salary"].quantile(0.95))
            level = "Senior / Lead level"
        elif score >= 2:
            est_low, est_high = (salary_df["normalized_salary"].quantile(0.5),
                                 salary_df["normalized_salary"].quantile(0.75))
            level = "Mid level"
        elif score >= -1:
            est_low, est_high = (salary_df["normalized_salary"].quantile(0.25),
                                 salary_df["normalized_salary"].quantile(0.5))
            level = "Associate level"
        else:
            est_low, est_high = (salary_df["normalized_salary"].quantile(0.05),
                                 salary_df["normalized_salary"].quantile(0.25))
            level = "Entry level"
    else:
        est_low, est_high, level = 0, 0, "Unknown"

    # ── Display Results ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"## 📊 Analysis Results {flag}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Experience Required", f"{min_exp}-{max_exp} yrs")
    c2.metric("Education Level", education)
    c3.metric("Work Type", remote_status)
    c4.metric("Seniority", level)

    st.markdown("### 🛠️ Extracted Skills")
    if found_skills:
        skill_html = " ".join(
            f'<span style="background:#EAF0F8;color:#0A66C2;padding:4px 12px;'
            f'border-radius:100px;font-size:13px;font-weight:600;margin:3px;'
            f'display:inline-block;">{s}</span>'
            for s in found_skills
        )
        st.markdown(skill_html, unsafe_allow_html=True)
    else:
        st.info("No known skills detected in this text.")

    st.markdown(f"### 💰 Estimated Salary Range {flag}")
    if explicit_salary:
        st.success(f"**Salary mentioned in text:** {', '.join(explicit_salary[:3])}")
    st.markdown(f"""
    <div class="prediction-card">
        <div class="prediction-label">Estimated Range Based on Text Analysis</div>
        <div class="prediction-amount" style="font-size:2.2rem;">
            {format_salary(est_low)} – {format_salary(est_high)}
        </div>
        <div class="prediction-range">Based on seniority signals and {market_label()} data</div>
        <div class="prediction-badge">{level}</div>
    </div>
    """, unsafe_allow_html=True)

elif analyse:
    st.warning("Please paste a job description first.")
