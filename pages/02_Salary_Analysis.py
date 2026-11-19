"""pages/02_Salary_Analysis.py — Dual market deep salary analysis."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css, experience_sort_order
from utils.market import get_market_data, format_salary, market_label, is_india
from utils.visualizations import plot_bar_chart, plot_salary_boxplot
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="💰 Deep Analysis", page_icon="💰")
inject_css(); render_theme_css()
if not require_login(): st.stop()
show_sidebar()

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD"

with st.spinner("Loading…"):
    df = get_market_data()
if df.empty:
    st.error("No data available."); st.stop()

salary_df = df[df["normalized_salary"].notna()].copy()
st.markdown(f"# 💰 Deep Salary Analysis {flag}")
st.markdown(f"*{market_label()} — {len(salary_df):,} postings*")
st.divider()

c1, c2 = st.columns(2)
with c1:
    if "formatted_experience_level" in salary_df.columns:
        order = [e for e in experience_sort_order()
                if e in salary_df["formatted_experience_level"].unique()]
        try:
            fig = plot_salary_boxplot(
                salary_df,
                category_col="formatted_experience_level",
                value_col="normalized_salary",
                title=f"Salary Spread by Experience ({unit})",
                category_order=order,
            )
        except TypeError:
            # Fallback if the function uses different parameter names
            fig = plot_salary_boxplot(
                salary_df, "formatted_experience_level", "normalized_salary",
                f"Salary Spread by Experience ({unit})"
            )
        st.plotly_chart(fig, use_container_width=True)

with c2:
    if "location" in salary_df.columns or "state" in salary_df.columns:
        col = "location" if "location" in salary_df.columns else "state"
        top_loc = (salary_df.groupby(col)["normalized_salary"]
                  .median().sort_values(ascending=False).head(10).reset_index())
        top_loc.columns = ["Location", "Median Salary"]
        st.plotly_chart(
            plot_bar_chart(top_loc, "Median Salary", "Location",
                           f"Top 10 Locations by Salary ({unit})", orientation="h"),
            use_container_width=True
        )

st.markdown("### 📊 Statistical Summary")
stats = salary_df["normalized_salary"].describe()
stat_table = pd.DataFrame({
    "Metric": ["Count","Mean","Std Dev","Min","25%","Median","75%","Max"],
    "Value": [f"{int(stats['count']):,}"] + [format_salary(v) for v in
              [stats['mean'],stats['std'],stats['min'],
               stats['25%'],stats['50%'],stats['75%'],stats['max']]]
})
st.dataframe(stat_table, hide_index=True, use_container_width=True)

if "formatted_work_type" in salary_df.columns:
    st.markdown("### 💼 Salary by Work Type")
    wt = (salary_df.groupby("formatted_work_type")["normalized_salary"]
         .median().reset_index())
    wt.columns = ["Work Type","Median Salary"]
    st.plotly_chart(plot_bar_chart(wt,"Work Type","Median Salary",
                    f"Median Salary by Work Type ({unit})"), use_container_width=True)
