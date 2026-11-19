"""pages/06_Company_Analysis.py — Dual market company analysis."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css, format_number
from utils.market import get_market_data, format_salary, market_label, is_india
from utils.visualizations import plot_bar_chart
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="🏢 Company Analysis", page_icon="🏢")
inject_css(); render_theme_css()
if not require_login(): st.stop()
show_sidebar()

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD"

with st.spinner("Loading…"):
    df = get_market_data()
if df.empty or "company_name" not in df.columns:
    st.error("No company data available for this market.")
    st.stop()

salary_df = df[df["normalized_salary"].notna()].copy()

st.markdown(f"# 🏢 Company & Hiring Analysis {flag}")
st.markdown(f"*{market_label()} — {df['company_name'].nunique():,} companies · "
            f"{len(df):,} total postings*")
st.divider()

has_company_size = "company_size" in df.columns

if is_india():
    tab1, tab2, tab3 = st.tabs(["🏆 Top Hirers", "💰 Salary by Company", "🔍 Company Profile"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🏆 Top Hirers", "📏 Company Size", "💰 Salary by Company", "🔍 Company Profile"]
    )

with tab1:
    top_hirers = (df["company_name"].value_counts().head(20)
                  .reset_index())
    top_hirers.columns = ["Company", "Job Postings"]
    st.plotly_chart(
        plot_bar_chart(top_hirers, "Job Postings", "Company",
                       f"Top 20 Hirers {flag}", orientation="h"),
        use_container_width=True
    )
    st.dataframe(top_hirers, hide_index=True, use_container_width=True)

if not is_india():
    with tab2:
        if has_company_size:
            size_dist = df["company_size"].value_counts().reset_index()
            size_dist.columns = ["Company Size", "Postings"]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Company Size Distribution**")
                st.plotly_chart(
                    plot_bar_chart(size_dist, "Postings", "Company Size",
                                   "Company Size Distribution"),
                    use_container_width=True
                )
            with c2:
                st.markdown("**Avg Salary by Company Size**")
                size_sal = (salary_df.groupby("company_size")["normalized_salary"]
                           .mean().reset_index())
                size_sal.columns = ["Company Size", "Avg Salary"]
                st.plotly_chart(
                    plot_bar_chart(size_sal, "Company Size", "Avg Salary",
                                   f"Avg Salary by Size ({unit})"),
                    use_container_width=True
                )
        else:
            st.info("Company size data not available for this dataset.")

sal_tab = tab2 if is_india() else tab3
with sal_tab:
    if "company_name" in salary_df.columns:
        top_paying = (salary_df.groupby("company_name")["normalized_salary"]
                      .agg(median="median", count="count")
                      .query("count >= 2")
                      .nlargest(15, "median").reset_index())
        top_paying.columns = ["Company", "Median Salary", "# Postings"]
        st.plotly_chart(
            plot_bar_chart(top_paying, "Median Salary", "Company",
                           f"Top 15 Paying Companies ({unit})", orientation="h"),
            use_container_width=True
        )
        top_paying["Median Salary"] = top_paying["Median Salary"].apply(format_salary)
        st.dataframe(top_paying, hide_index=True, use_container_width=True)

profile_tab = tab3 if is_india() else tab4
with profile_tab:
    st.markdown("**Search a Company**")
    company_list = sorted(df["company_name"].dropna().unique().tolist())
    selected = st.selectbox("Select a company", ["(Select)"] + company_list)
    if selected != "(Select)":
        comp_df = df[df["company_name"] == selected]
        comp_sal = comp_df[comp_df["normalized_salary"].notna()]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Postings", format_number(len(comp_df)))
        c2.metric("Avg Salary", format_salary(comp_sal["normalized_salary"].mean())
                  if not comp_sal.empty else "N/A")
        if "location" in comp_df.columns:
            c3.metric("Top Location", comp_df["location"].mode()[0]
                      if not comp_df["location"].mode().empty else "N/A")
        show_cols = [c for c in ["title","location","normalized_salary","formatted_experience_level"]
                    if c in comp_df.columns]
        d = comp_df[show_cols].copy()
        if "normalized_salary" in d.columns:
            d["normalized_salary"] = d["normalized_salary"].apply(format_salary)
        st.dataframe(d.head(50), hide_index=True, use_container_width=True)
