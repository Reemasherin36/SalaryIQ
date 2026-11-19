"""pages/08_Negotiation_Advisor.py — Dual market negotiation advisor."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import (inject_css, get_percentile_n, salary_percentile,
                            compute_salary_stats, negotiation_tip_card, safe_divide)
from utils.market import (get_market_data, format_salary, market_label,
                           is_india, get_top_titles, get_top_skills,
                           get_top_industries, get_top_locations)
from utils.nav import show_sidebar
from utils.visualizations import plot_salary_distribution_with_markers

st.set_page_config(layout="wide", page_title="🤝 Negotiation Advisor", page_icon="🤝")
inject_css(); render_theme_css()
if not require_login(): st.stop()
show_sidebar()

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD/yr"
curr = "₹" if is_india() else "$"

with st.spinner("Loading market data…"):
    df          = get_market_data()
    salary_df   = df[df["normalized_salary"].notna()].copy()
    top_titles  = get_top_titles(50)
    top_skills  = get_top_skills(50)
    top_industries = get_top_industries(30)
    locations   = get_top_locations(30)

st.markdown(f"# 🤝 Negotiation Advisor {flag}")
st.markdown(f"*{market_label()} — Data-driven negotiation strategy*")
st.divider()

with st.form("neg_form"):
    c1, c2 = st.columns(2)
    with c1:
        cur_title  = st.selectbox("Current Job Title", ["(Other)"]+sorted(top_titles))
        tgt_title  = st.selectbox("Target Role", ["(Same as current)"]+sorted(top_titles))
        years_exp  = st.slider("Years of Experience", 0, 30, 5)
        cur_salary = st.number_input(
            f"Current Salary ({unit})", min_value=0.0,
            max_value=500.0 if is_india() else 2_000_000.0,
            value=8.0 if is_india() else 80_000.0,
            step=0.5 if is_india() else 1_000.0)
        tgt_salary = st.number_input(
            f"Target Salary ({unit})", min_value=0.0,
            max_value=500.0 if is_india() else 2_000_000.0,
            value=15.0 if is_india() else 110_000.0,
            step=0.5 if is_india() else 1_000.0)
    with c2:
        loc_label = "City" if is_india() else "State"
        location   = st.selectbox(loc_label, locations if locations else ["Bangalore","Mumbai"])
        industry   = st.selectbox("Industry", ["(Other)"]+sorted(top_industries))
        skills     = st.multiselect("Your Skills", sorted(top_skills))
        remote_pref= st.radio("Remote Preference",
                               ["Remote","Hybrid","On-site"], horizontal=True)
        company    = st.text_input("Company (optional)")
    submitted = st.form_submit_button("🤝 Get My Negotiation Strategy", use_container_width=True)

if submitted:
    use_title = tgt_title if tgt_title != "(Same as current)" else cur_title
    market    = compute_salary_stats(salary_df["normalized_salary"])
    pct       = salary_percentile(tgt_salary, salary_df["normalized_salary"])

    st.markdown("---")
    st.markdown(f"### 📊 Your Market Position {flag}")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Your Target",     format_salary(tgt_salary))
    m2.metric("Market Median",   format_salary(market["median"]))
    m3.metric("Market 75th Pct", format_salary(market["p75"]))
    m4.metric("Your Percentile", get_percentile_n(pct))
    st.markdown("<br>",unsafe_allow_html=True)

    if pct >= 90:
        st.warning("⚠️ Your target is above the 90th percentile. Prepare strong justification.")
    elif pct >= 75:
        st.info(f"📈 Top 25% ask. Anchor to the {format_salary(market['p75'])} 75th percentile.")
    elif pct >= 50:
        st.success("✅ Well within market range. Negotiate confidently.")
    else:
        st.info(f"💡 Consider raising your target. Market median is {format_salary(market['median'])}.")

    fig = plot_salary_distribution_with_markers(
        salary_df["normalized_salary"],
        current=cur_salary, target=tgt_salary,
        median=market["median"], p75=market["p75"],
        title=f"Your Salary vs {flag} Market",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── 5 Talking Points ──────────────────────────────────────────────────────
    st.markdown(f"### 🗣️ Your 5 Negotiation Talking Points {flag}")
    ask_pct = safe_divide(tgt_salary - cur_salary, cur_salary, 0) * 100
    top3    = ", ".join(skills[:3]) if skills else "your core technical skills"

    tips = [
        f"Professionals with skills in {top3} in {location} earn a median of "
        f"{format_salary(market['median'])} — cite this benchmark directly.",

        f"The {flag} market data shows {format_salary(market['p75'])} at the 75th percentile "
        f"for this role. Your target of {format_salary(tgt_salary)} is at the "
        f"{get_percentile_n(pct)} — a well-justified ask.",

        f"You are asking for a {ask_pct:.1f}% increase. Given your {years_exp} years of "
        f"experience and expertise in {top3}, this reflects fair market value.",

        f"The {industry if industry!='(Other)' else 'industry'} sector offers a median of "
        f"{format_salary(market['median'])} and 75th percentile of {format_salary(market['p75'])}. "
        f"If base salary is firm, negotiate equity, bonuses, or additional benefits instead.",

        f"Companies hiring for {use_title} in {location} typically post roles in the "
        f"{format_salary(market['p25'])} – {format_salary(market['p75'])} range. "
        f"Your target is {'within' if market['p25'] <= tgt_salary <= market['p75'] else 'near'} this range.",
    ]
    for i, tip in enumerate(tips, 1):
        st.markdown(negotiation_tip_card(i, tip), unsafe_allow_html=True)

    # ── Negotiation Script ─────────────────────────────────────────────────────
    st.markdown("### 📝 Your Negotiation Script")
    script = (
        f"Based on my {years_exp} year{'s' if years_exp != 1 else ''} of experience "
        f"in the {industry if industry != '(Other)' else '[Industry]'} sector, "
        f"my expertise in {', '.join(skills[:3]) if skills else '[Your Key Skills]'}, "
        f"and market data showing that {use_title} roles in {location} command a median salary of "
        f"{format_salary(market['median'])} with top performers earning {format_salary(market['p75'])}, "
        f"I am seeking a total compensation of {format_salary(tgt_salary)}.\n\n"
        f"This reflects both my direct contribution and fair {flag} market value. "
        f"I'm excited about this opportunity and confident I can deliver significant value."
    )
    st.code(script, language="text")

    report = pd.DataFrame({
        "Field": ["Target Role","Location","Target Salary","Market Median","Market 75th","Percentile"],
        "Value": [use_title, location, format_salary(tgt_salary),
                  format_salary(market["median"]), format_salary(market["p75"]),
                  get_percentile_n(pct)],
    })
    st.download_button("⬇️ Download Report",
                       report.to_csv(index=False).encode(),
                       "negotiation_report.csv","text/csv")
