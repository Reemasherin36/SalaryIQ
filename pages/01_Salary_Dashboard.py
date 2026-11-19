"""pages/01_Salary_Dashboard.py — Dual market salary dashboard."""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login
from utils.theme import render_theme_css
from utils.helpers import inject_css, metric_card, format_number, experience_sort_order
from utils.market import get_market_data, format_salary, market_label, is_india
from utils.visualizations import plot_salary_histogram, plot_bar_chart
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="📊 Salary Dashboard", page_icon="📊")
inject_css(); render_theme_css()
if not require_login(): st.stop()
show_sidebar()

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD"

with st.spinner("Loading…"):
    df = get_market_data()
if df.empty:
    st.error("No data. Check data folder."); st.stop()

salary_df = df[df["normalized_salary"].notna()].copy()
st.markdown(f"# 📊 Salary Dashboard {flag}")
st.markdown(f"*{market_label()} · {len(salary_df):,} postings*")
st.divider()

k1,k2,k3,k4 = st.columns(4)
k1.markdown(metric_card("Avg Salary",    format_salary(salary_df["normalized_salary"].mean()),   unit, "💰"), unsafe_allow_html=True)
k2.markdown(metric_card("Median Salary", format_salary(salary_df["normalized_salary"].median()), unit, "📊"), unsafe_allow_html=True)
k3.markdown(metric_card("Salary Range",  format_salary(salary_df["normalized_salary"].max()-salary_df["normalized_salary"].min()), "Spread","📏"), unsafe_allow_html=True)
k4.markdown(metric_card("With Salary",   f"{len(salary_df)/max(len(df),1)*100:.1f}%", f"{len(salary_df):,} postings","📋"), unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)

tab1,tab2,tab3 = st.tabs(["📈 Distribution","🎯 By Category","🏆 Top Titles"])

with tab1:
    c1,c2 = st.columns([2,1])
    with c1:
        fig = plot_salary_histogram(salary_df,"normalized_salary",f"Salary Distribution ({unit})")
        fig.update_layout(xaxis_title=f"Annual Salary ({unit})")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("**Percentile Table**")
        pct = {
            "Percentile":["10th","25th","Median","75th","90th","Mean"],
            "Salary":[format_salary(salary_df["normalized_salary"].quantile(p))
                      for p in [.10,.25,.50,.75,.90]] + [format_salary(salary_df["normalized_salary"].mean())]
        }
        st.dataframe(pd.DataFrame(pct), hide_index=True, use_container_width=True)

with tab2:
    c1,c2 = st.columns(2)
    with c1:
        if "formatted_experience_level" in salary_df.columns:
            order = [e for e in experience_sort_order() if e in salary_df["formatted_experience_level"].unique()]
            exp = salary_df.groupby("formatted_experience_level")["normalized_salary"].median().reindex(order).reset_index()
            exp.columns = ["Experience Level","Median Salary"]
            st.plotly_chart(plot_bar_chart(exp,"Experience Level","Median Salary",f"Salary by Experience ({unit})"), use_container_width=True)
    with c2:
        col = "industry_name" if "industry_name" in salary_df.columns else None
        if col:
            ind = salary_df.groupby(col)["normalized_salary"].median().sort_values(ascending=False).head(10).reset_index()
            ind.columns = ["Industry","Median Salary"]
            st.plotly_chart(plot_bar_chart(ind,"Median Salary","Industry",f"Top 10 Industries ({unit})",orientation="h"), use_container_width=True)

with tab3:
    if "title" in salary_df.columns:
        top = salary_df.groupby("title")["normalized_salary"].agg(median="median",count="count").query("count>=2").nlargest(15,"median").reset_index()
        top.columns=["Job Title","Median Salary","# Postings"]
        st.plotly_chart(plot_bar_chart(top,"Median Salary","Job Title",f"Top 15 Titles ({unit})",orientation="h"),use_container_width=True)
        top["Median Salary"]=top["Median Salary"].apply(format_salary)
        st.dataframe(top,hide_index=True,use_container_width=True)

with st.expander("🗃️ Raw Data"):
    cols=[c for c in ["title","company_name","location","normalized_salary","formatted_experience_level"] if c in salary_df.columns]
    d=salary_df[cols].copy()
    d["normalized_salary"]=d["normalized_salary"].apply(format_salary)
    st.dataframe(d.head(300),hide_index=True,use_container_width=True)
