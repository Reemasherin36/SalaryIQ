"""pages/11_My_Offers.py — Private offer tracker (each user sees only their own records)."""
import os
import sys
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.auth import add_record, delete_record, get_user_records, get_username, require_login
from utils.helpers import get_percentile_n, inject_css, salary_percentile
from utils.market import format_salary, get_market_data, is_india, market_label
from utils.nav import show_sidebar
from utils.theme import render_theme_css

st.set_page_config(layout="wide", page_title="My Offers", page_icon="📁")
inject_css()
render_theme_css()
if not require_login():
    st.stop()
show_sidebar()

unit = "LPA" if is_india() else "USD per year"
flag = "🇮🇳" if is_india() else "🇺🇸"

st.markdown(f"# 📁 My Offers {flag}")
st.markdown(f"Log the offers you receive and see how each one ranks against the {market_label()}. "
            "Only you can see this list.")
st.divider()

with st.spinner("Loading market data..."):
    df = get_market_data()
salary_df = df[df["normalized_salary"].notna()] if not df.empty else pd.DataFrame()

st.subheader("Add an offer")
with st.form("offer_form", clear_on_submit=True):
    a, b = st.columns(2)
    with a:
        role = st.text_input("Job title", placeholder="Data Analyst")
        company = st.text_input("Company", placeholder="Company name")
    with b:
        place = st.text_input("City or state", placeholder="Bengaluru" if is_india() else "California")
        offer = st.number_input(f"Offered salary ({unit})", min_value=0.0,
                                max_value=500.0 if is_india() else 2_000_000.0,
                                value=12.0 if is_india() else 90_000.0,
                                step=0.5 if is_india() else 1_000.0)
    notes = st.text_area("Notes (optional)", placeholder="Joining bonus, notice period, benefits...")
    saved = st.form_submit_button("Save offer", use_container_width=True)

if saved:
    if not role.strip() or not company.strip():
        st.error("Enter the job title and the company so you can find this offer later.")
    elif offer <= 0:
        st.error("Enter the offered salary. It must be more than zero.")
    elif salary_df.empty:
        st.error("Market data is not available, so the offer could not be ranked.")
    else:
        pct = salary_percentile(offer, salary_df["normalized_salary"])
        add_record({
            "market": "india" if is_india() else "us",
            "role": role.strip(), "company": company.strip(), "place": place.strip(),
            "offer": float(offer), "market_median": float(salary_df["normalized_salary"].median()),
            "percentile": float(pct), "notes": notes.strip(),
        })
        st.success(f"Saved. This offer sits at the {get_percentile_n(pct)} of the market.")

st.divider()
st.subheader("Your saved offers")
records = get_user_records()  # always filtered to the signed-in user on the server

if not records:
    st.info("You have not saved any offers yet. Add your first offer above to see how it compares.")
    st.stop()

rows = []
for r in records:
    in_india = r.get("market") == "india"
    fmt = (lambda v: f"₹{v:.1f} LPA") if in_india else (lambda v: f"${int(round(v)):,}")
    rows.append({
        "Saved": datetime.fromtimestamp(r.get("created_at", 0)).strftime("%d %b %Y"),
        "Market": "India" if in_india else "US",
        "Role": r["role"], "Company": r["company"], "Place": r.get("place", ""),
        "Offer": fmt(r["offer"]), "Market median": fmt(r["market_median"]),
        "Percentile": get_percentile_n(r["percentile"]),
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

same_market = [r for r in records if r.get("market") == ("india" if is_india() else "us")]
if same_market:
    labels = [f'{r["company"]} ({r["role"]})' for r in same_market]
    fig = go.Figure()
    fig.add_bar(name="Your offer", x=labels, y=[r["offer"] for r in same_market], marker_color="#2563EB")
    fig.add_bar(name="Market median", x=labels, y=[r["market_median"] for r in same_market], marker_color="#12B5A6")
    fig.update_layout(barmode="group", height=360, margin=dict(l=8, r=8, t=48, b=8),
                      title=dict(text=f"Your offers against the market median ({unit})", x=0.01),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"))
    fig.update_yaxes(gridcolor="#E7ECF3")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Switch the market in the sidebar to chart offers saved in the other market.")

with st.expander("Delete an offer"):
    options = {f'{r["company"]} ({r["role"]}), saved {datetime.fromtimestamp(r.get("created_at", 0)).strftime("%d %b %Y")}': r["id"]
               for r in records}
    choice = st.selectbox("Choose the offer to delete", list(options.keys()))
    if st.button("Delete offer"):
        if delete_record(options[choice]):
            st.success("Offer deleted.")
            st.rerun()
        else:
            st.error("That offer could not be found in your account.")
