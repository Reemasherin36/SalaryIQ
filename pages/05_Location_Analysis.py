"""pages/05_Location_Analysis.py — Dual market location analysis."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css
from utils.market import get_market_data, format_salary, market_label, is_india
from utils.visualizations import plot_bar_chart
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="📍 Location Analysis", page_icon="📍")
inject_css(); render_theme_css()
if not require_login(): st.stop()

show_sidebar("📍 Location Analysis", "Explore salary by location.")

top_n_states = 15

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD"
loc_col_label = "City" if is_india() else "State"

with st.spinner("Loading…"):
    df = get_market_data()

loc_col = "location" if "location" in df.columns else ("state" if "state" in df.columns else None)
if df.empty or loc_col is None:
    st.error("No location data available."); st.stop()

salary_df = df[df["normalized_salary"].notna()].copy()
st.markdown(f"# 📍 Location Analysis {flag}")
st.markdown(f"*{market_label()} — {salary_df[loc_col].nunique()} {loc_col_label.lower()}s*")
st.divider()

loc_stats = (salary_df.groupby(loc_col)["normalized_salary"]
            .agg(median="median", count="count")
            .query("count >= 2")
            .sort_values("median", ascending=False)
            .head(top_n_states).reset_index())
loc_stats.columns = [loc_col_label, "Median Salary", "Postings"]

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        plot_bar_chart(loc_stats, "Median Salary", loc_col_label,
                       f"Top {top_n_states} {loc_col_label}s by Salary ({unit})",
                       orientation="h"),
        use_container_width=True
    )
with c2:
    count_df = salary_df[loc_col].value_counts().head(top_n_states).reset_index()
    count_df.columns = [loc_col_label,"Postings"]
    st.plotly_chart(
        plot_bar_chart(count_df,"Postings",loc_col_label,
                       f"Top {top_n_states} {loc_col_label}s by Job Count",
                       orientation="h"),
        use_container_width=True
    )

if not is_india() and "remote_allowed" in salary_df.columns:
    st.markdown("### 🌐 Remote vs On-site")
    remote_by_loc = (salary_df.groupby(loc_col)["remote_allowed"]
                     .mean().mul(100).sort_values(ascending=False)
                     .head(top_n_states).reset_index())
    remote_by_loc.columns = [loc_col_label,"Remote %"]
    st.plotly_chart(plot_bar_chart(remote_by_loc,"Remote %",loc_col_label,
                    "Remote Job % by Location",orientation="h"),
                    use_container_width=True)

display = loc_stats.copy()
display["Median Salary"] = display["Median Salary"].apply(format_salary)
st.dataframe(display, hide_index=True, use_container_width=True)
