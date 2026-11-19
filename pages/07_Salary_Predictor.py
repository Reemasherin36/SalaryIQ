"""pages/07_Salary_Predictor.py — ML Salary Predictor with dual market support."""
import streamlit as st
import pandas as pd
import numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css, format_number, salary_range_label, get_percentile_n
from utils.market import (get_market_data, format_salary, market_label,
                           is_india, get_top_titles, get_top_skills,
                           get_top_industries, get_top_locations)
from utils.helpers import salary_percentile
from utils.visualizations import plot_gauge_chart, plot_feature_importance
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="🔮 Salary Predictor", page_icon="🔮")
inject_css(); render_theme_css()
if not require_login(): st.stop()

@st.cache_resource
def load_model():
    import joblib
    root = os.path.dirname(os.path.dirname(__file__))
    mp = os.path.join(root,"models","salary_model.pkl")
    ep = os.path.join(root,"models","encoders.pkl")
    if not os.path.exists(mp):
        return None, None, None
    try:
        pipe = joblib.load(mp)
        enc  = joblib.load(ep)
        return pipe, enc.get("encoders",{}), enc.get("feature_names",[])
    except:
        return None, None, None

show_sidebar()

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD/year"

with st.spinner("Loading…"):
    pipeline, encoders, feature_names = load_model()
    df = get_market_data()
    salary_df = df[df["normalized_salary"].notna()].copy()
    top_titles    = get_top_titles(50)
    top_skills    = get_top_skills(50)
    top_industries= get_top_industries(30)
    locations     = get_top_locations(30)

st.markdown(f"# 🔮 ML Salary Predictor {flag}")
st.markdown(f"*{market_label()} — Enter your profile to get a data-driven salary estimate*")
st.divider()

if pipeline is None:
    st.warning("⚠️ No trained model found. Run `python models/train_model.py` first.")

loc_label = "City" if is_india() else "State"

with st.form("prediction_form"):
    left, right = st.columns(2)
    with left:
        st.markdown("**Role & Work Details**")
        job_title = st.selectbox("Job Title", ["(Other)"]+sorted(top_titles))
        exp_level = st.selectbox("Experience Level",
            ["Internship","Entry level","Associate","Mid-Senior level","Director","Executive"],
            index=2)
        work_type = st.selectbox("Work Type",
            ["Full-time","Part-time","Contract","Temporary","Internship"])
        pay_period = st.selectbox("Pay Period", ["YEARLY","MONTHLY","HOURLY"])
        remote = st.radio("Remote Allowed?", ["Yes","No"], horizontal=True)
    with right:
        st.markdown(f"**{loc_label} & Company**")
        location = st.selectbox(loc_label, locations if locations else ["Bangalore","Mumbai","Delhi"])
        industry = st.selectbox("Industry", ["(Other)"]+sorted(top_industries))
        co_size  = st.selectbox("Company Size",
            ["1-10","11-50","51-200","201-500","501-1000","1001-5000","10001+"], index=2)
        skills   = st.multiselect("Your Skills", sorted(top_skills))
        benefits = st.slider("Number of Benefits", 0, 20, 5)
    submitted = st.form_submit_button("🔮 Predict My Salary", use_container_width=True)

if submitted:
    if is_india():
        # ── Rule-based India estimation ────────────────────────────────────
        from utils.india_loader import estimate_lpa, CITY_TIER
        exp_map = {"Internship":0,"Entry level":1,"Associate":3,
                   "Mid-Senior level":7,"Director":12,"Executive":18}
        mid_exp = exp_map.get(exp_level, 3)
        max_exp = mid_exp + 3
        city = str(location).lower().split("/")[0]
        skill_count = len(skills)
        predicted = estimate_lpa(mid_exp, max_exp, city, skill_count)
    else:
        if pipeline is None:
            st.error("No model found. Run training first."); st.stop()
        from utils.preprocessing import encode_single_input
        inp = {
            "formatted_experience_level": exp_level,
            "formatted_work_type": work_type,
            "remote_allowed": 1 if remote == "Yes" else 0,
            "state": location,
            "company_size": co_size,
            "industry_name": industry,
            "pay_period": pay_period,
            "skill_count": len(skills),
            "benefit_count": benefits,
        }
        try:
            X = encode_single_input(inp, encoders)
            if feature_names:
                for fn in feature_names:
                    if fn not in X.columns: X[fn] = -1
                X = X[feature_names]
            predicted = float(pipeline.predict(X)[0])
            predicted = max(20_000, min(predicted, 2_000_000))
        except Exception as e:
            st.error(f"Prediction failed: {e}"); st.stop()

    sal_low  = round(predicted * 0.85, 1)
    sal_high = round(predicted * 1.20, 1)
    pct = salary_percentile(predicted, salary_df["normalized_salary"])
    pct_n = get_percentile_n(pct)

    st.markdown("---")
    st.markdown("## 🎯 Your Salary Prediction")
    r1, r2, r3 = st.columns([1.5,1,1])

    with r1:
        st.markdown(f"""
        <div class="prediction-card">
            <div class="prediction-label">Predicted Annual Salary {flag}</div>
            <div class="prediction-amount">{format_salary(predicted)}</div>
            <div class="prediction-range">
                Range: {format_salary(sal_low)} – {format_salary(sal_high)}
            </div>
            <div class="prediction-badge">You are in the {pct_n}</div>
        </div>""", unsafe_allow_html=True)

    with r2:
        from utils.helpers import metric_card
        mkt = salary_df["normalized_salary"].median()
        diff = predicted - mkt
        diff_str = f"+{format_salary(diff)}" if diff >= 0 else format_salary(diff)
        st.markdown(metric_card("Market Median", format_salary(mkt), diff_str, "📊"), unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown(metric_card("Your Percentile", pct_n, f"{len(salary_df):,} postings","🏆"), unsafe_allow_html=True)

    with r3:
        fig = plot_gauge_chart(
            predicted,
            min_val=salary_df["normalized_salary"].quantile(0.05),
            max_val=salary_df["normalized_salary"].quantile(0.95),
            title=f"Salary Position {flag}"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔍 Similar Jobs")
    sim = salary_df.copy()
    if "formatted_experience_level" in sim.columns:
        m = sim[sim["formatted_experience_level"]==exp_level]
        if len(m)>=5: sim = m
    sim["diff"]=(sim["normalized_salary"]-predicted).abs()
    sim = sim.nsmallest(5,"diff")
    cols=[c for c in ["title","company_name","location","normalized_salary","formatted_work_type"] if c in sim.columns]
    d=sim[cols].copy()
    d["normalized_salary"]=d["normalized_salary"].apply(format_salary)
    d.columns=[c.replace("_"," ").title() for c in d.columns]
    st.dataframe(d, hide_index=True, use_container_width=True)
