"""pages/04_Industry_Insights.py — Dual market industry insights."""
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

st.set_page_config(layout="wide", page_title="🏭 Industry Insights", page_icon="🏭")
inject_css(); render_theme_css()
if not require_login(): st.stop()

show_sidebar("🏭 Industry Insights", "Explore salary distributions across industries.")

top_n = 20  # required by original page logic

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD"

with st.spinner("Loading…"):
    df = get_market_data()

ind_col = "industry_name" if "industry_name" in df.columns else None
if df.empty or ind_col is None:
    st.error("No industry data available for this market."); st.stop()

salary_df = df[df["normalized_salary"].notna()].copy()
st.markdown(f"# 🏭 Industry Salary Insights {flag}")
st.markdown(f"*{market_label()} — {salary_df[ind_col].nunique()} industries · "
            f"{len(salary_df):,} postings with salary data*")
st.divider()

ind_stats = (salary_df.groupby(ind_col)["normalized_salary"]
            .agg(median="median", mean="mean", count="count")
            .query("count >= 3")
            .sort_values("median", ascending=False)
            .head(top_n).reset_index())
ind_stats.columns = ["Industry","Median Salary","Avg Salary","Postings"]

st.plotly_chart(
    plot_bar_chart(ind_stats, "Median Salary", "Industry",
                   f"Top {top_n} Industries by Median Salary ({unit})",
                   orientation="h"),
    use_container_width=True
)

display = ind_stats.copy()
display["Median Salary"] = display["Median Salary"].apply(format_salary)
display["Avg Salary"] = display["Avg Salary"].apply(format_salary)
st.dataframe(display, hide_index=True, use_container_width=True)

st.markdown("### 📊 Postings Count by Industry")
count_df = salary_df[ind_col].value_counts().head(top_n).reset_index()
count_df.columns = ["Industry","Postings"]
st.plotly_chart(plot_bar_chart(count_df,"Postings","Industry",
                f"Top {top_n} Industries by Job Count",orientation="h"),
                use_container_width=True)
