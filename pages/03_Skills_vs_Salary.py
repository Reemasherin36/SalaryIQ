"""pages/03_Skills_vs_Salary.py — Dual market skills analysis."""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css, format_number
from utils.market import (get_market_data, format_salary, market_label,
                           is_india, get_top_skills)
from utils.visualizations import plot_bar_chart
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="🛠️ Skills vs Salary", page_icon="🛠️")
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
overall_median = salary_df["normalized_salary"].median()

st.markdown(f"# 🛠️ Skills vs Salary {flag}")
st.markdown(f"*{market_label()} — {len(salary_df):,} postings with salary data*")
st.divider()

min_jobs = st.slider("Minimum job postings per skill", 2, 50, 5)

# ── Build skill-salary mapping ──────────────────────────────────────────────
skill_col = "skills_desc" if "skills_desc" in salary_df.columns else None

if skill_col is None:
    st.warning("No skills data available for this market.")
    st.stop()

if is_india():
    # Naukri skills are concatenated camelCase/pipe-joined strings
    import re
    def split_skills(text):
        if not isinstance(text, str):
            return []
        parts = re.split(r"[,|;\n]|(?<=[a-z])(?=[A-Z])", text)
        return [p.strip().title() for p in parts if len(p.strip()) > 2]

    exploded = salary_df[["normalized_salary", skill_col]].copy()
    exploded["skill"] = exploded[skill_col].apply(split_skills)
    exploded = exploded.explode("skill").dropna(subset=["skill"])
else:
    # US dataset — skills are comma or pipe separated typically
    exploded = salary_df[["normalized_salary", skill_col]].copy()
    exploded["skill"] = exploded[skill_col].astype(str).str.split(r"[,|]")
    exploded = exploded.explode("skill")
    exploded["skill"] = exploded["skill"].str.strip().str.title()
    exploded = exploded[exploded["skill"].str.len() > 2]

skill_premium = (
    exploded.groupby("skill")["normalized_salary"]
    .agg(avg_salary="mean", job_count="count")
    .query(f"job_count >= {min_jobs}")
    .sort_values("avg_salary", ascending=False)
    .reset_index()
)
skill_premium.columns = ["Skill", "Avg Salary", "job_count"]
skill_premium["Premium vs Median"] = (
    (skill_premium["Avg Salary"] - overall_median) / overall_median * 100
).round(1)

tab1, tab2, tab3 = st.tabs(["🏆 Top Skills", "📋 Skill Table", "🫧 Demand vs Salary"])

with tab1:
    top20 = skill_premium.head(20)
    fig = plot_bar_chart(
        top20[["Skill", "Avg Salary"]], "Avg Salary", "Skill",
        f"Top 20 Highest-Paying Skills ({unit})", orientation="h"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(f"**{len(skill_premium)} skills found with {min_jobs}+ postings**")

    skill_premium["Job Count"] = pd.to_numeric(
        skill_premium["job_count"], errors="coerce"
    ).fillna(0).astype(int)

    display_table = skill_premium[["Skill", "Avg Salary", "Premium vs Median", "Job Count"]].copy()
    display_table = display_table.loc[:, ~display_table.columns.duplicated()]

    for col in ["Avg Salary", "Premium vs Median", "Job Count"]:
        display_table[col] = pd.to_numeric(display_table[col], errors="coerce")
        display_table[col] = display_table[col].replace(
            [float("inf"), float("-inf")], 0
        ).fillna(0)

    display_table["Skill"] = display_table["Skill"].astype(str)
    display_table["Avg Salary"] = display_table["Avg Salary"].apply(format_salary)
    display_table = display_table.reset_index(drop=True)

    st.dataframe(display_table, hide_index=True, use_container_width=True)
    st.success(f"**Market Median:** {format_salary(overall_median)}")

with tab3:
    st.subheader(f"Skill Demand vs Avg Salary {flag}")
    bubble_top = skill_premium.nlargest(60, "job_count")
    fig = px.scatter(
        bubble_top, x="job_count", y="Avg Salary", size="job_count",
        hover_name="Skill", text="Skill", color="Avg Salary",
        color_continuous_scale=["#3B82F6", "#EF4444"],
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(
        xaxis_title="Number of Job Postings",
        yaxis_title=f"Average Salary ({unit})",
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)
