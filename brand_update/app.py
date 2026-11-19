"""app.py — SalaryIQ home dashboard with market visualisations."""
import os
import re
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from utils.auth import get_username, require_login
from utils.brand import lockup
from utils.helpers import format_number, inject_css, kpi_card, section_header, step_card_html
from utils.market import format_salary, get_market_data, get_top_skills, is_india, market_label
from utils.nav import show_sidebar
from utils.theme import render_theme_css

st.set_page_config(layout="wide", page_title="SalaryIQ", page_icon="📈", initial_sidebar_state="expanded")
inject_css()
render_theme_css()
if not require_login():
    st.stop()
show_sidebar()

EXP_ORDER = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
BLUES = ["#BFD1FF", "#9DB8FF", "#7A9FFF", "#5585F5", "#3A6DEB", "#2563EB"]


def _flat(html: str) -> str:
    return " ".join(line.strip() for line in html.splitlines() if line.strip())


def _style(fig, title: str, height: int = 350):
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(size=15, color="#0D1B2A", family="Sora, Inter, sans-serif")),
        height=height, margin=dict(l=8, r=8, t=52, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#43536B"),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#E7ECF3", zeroline=False, title=None)
    fig.update_yaxes(gridcolor="#E7ECF3", zeroline=False, title=None)
    return fig


@st.cache_data(show_spinner=False)
def skill_premium(_df: pd.DataFrame, market: str) -> pd.DataFrame:
    """Average salary for the best-paying skills in the selected market."""
    if "skills_desc" not in _df.columns:
        return pd.DataFrame()
    sub = _df[["normalized_salary", "skills_desc"]].dropna()
    if len(sub) > 20000:
        sub = sub.sample(20000, random_state=1)
    if market == "india":
        splitter = re.compile(r"[,|;\n]|(?<=[a-z])(?=[A-Z])")
        sub["skill"] = sub["skills_desc"].astype(str).apply(
            lambda t: [p.strip().title() for p in splitter.split(t) if len(p.strip()) > 2])
    else:
        sub["skill"] = sub["skills_desc"].astype(str).str.split(r"[,|]", regex=True)
    ex = sub.explode("skill")
    ex["skill"] = ex["skill"].astype(str).str.strip().str.title()
    ex = ex[ex["skill"].str.len() > 2]
    out = ex.groupby("skill")["normalized_salary"].agg(avg="mean", n="count")
    out = out[out["n"] >= 10].sort_values("avg", ascending=False).head(12).reset_index()
    return out


# ── Data ──────────────────────────────────────────────────────────────────────
market_key = "india" if is_india() else "us"
unit = "LPA" if is_india() else "USD"
with st.spinner("Loading market data..."):
    df = get_market_data()

if df.empty or "normalized_salary" not in df.columns:
    st.error("No market data found. Check that your data files are in the data folder.")
    st.stop()

salary_df = df[df["normalized_salary"].notna()].copy()
total = len(df)
median_sal = salary_df["normalized_salary"].median()
avg_sal = salary_df["normalized_salary"].mean()
companies = df["company_name"].nunique() if "company_name" in df.columns else 0
try:
    skills_count = len(get_top_skills(500))
except Exception:
    skills_count = 0
remote_pct = df["remote_allowed"].mean() * 100 if "remote_allowed" in df.columns else 0
first_name = get_username().split()[0].title()

# ── Welcome banner ────────────────────────────────────────────────────────────
st.markdown("""
<style>
.sqa { display:grid; grid-template-columns: 1.3fr 1fr; gap:28px; align-items:center; padding:34px 38px; border-radius:24px; color:#fff; margin-bottom:22px;
  background: radial-gradient(700px 320px at 90% 0%, rgba(18,181,166,.30), transparent 60%), linear-gradient(135deg,#0D1B2A 0%,#11294A 62%,#0F3B5F 100%); }
.sqa h1 { font-family: Sora, Inter, sans-serif !important; color:#fff !important; font-size:34px !important; line-height:1.15 !important; margin:16px 0 8px !important; letter-spacing:-0.02em !important; }
.sqa p { color:#B9C7DB !important; font-size:16px !important; margin:0 !important; }
.sqa-stats { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.sqa-stat { background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14); border-radius:14px; padding:14px 16px; }
.sqa-stat b { display:block; font-family: Sora, Inter, sans-serif; font-size:22px; color:#fff; }
.sqa-stat span { font-size:13px; color:#9FB2CC; }
@media (max-width: 900px) { .sqa { grid-template-columns:1fr; padding:26px 22px; } }
</style>
""", unsafe_allow_html=True)

st.markdown(_flat(f"""
<div class="sqa">
  <div>
    {lockup(38, dark_bg=True)}
    <h1>Welcome back, {first_name}</h1>
    <p>Here is the {market_label()} at a glance. Switch markets from the sidebar.</p>
  </div>
  <div class="sqa-stats">
    <div class="sqa-stat"><b>{format_salary(median_sal)}</b><span>Median salary</span></div>
    <div class="sqa-stat"><b>{format_number(total)}</b><span>Job postings</span></div>
    <div class="sqa-stat"><b>{format_number(companies)}</b><span>Companies hiring</span></div>
    <div class="sqa-stat"><b>{skills_count}</b><span>Skills tracked</span></div>
  </div>
</div>"""), unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
k = st.columns(6)
cards = [
    ("Total postings", format_number(total), "In this market", "📋", "blue"),
    ("Average salary", format_salary(avg_sal), unit, "💰", "green"),
    ("Median salary", format_salary(median_sal), "50th percentile", "📊", "blue"),
    ("Companies", format_number(companies), "Unique employers", "🏢", "amber"),
    ("Skills tracked", format_number(skills_count), "Across postings", "🛠️", "purple"),
    ("Remote jobs", f"{remote_pct:.1f}%", "Remote allowed", "🌐", "green"),
]
for col, (title, value, delta, icon, color) in zip(k, cards):
    col.markdown(kpi_card(title, value, delta, icon, color), unsafe_allow_html=True)

# ── Visualisations ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Market snapshot", f"Interactive charts for the {market_label()}"), unsafe_allow_html=True)

clip = salary_df[salary_df["normalized_salary"] <= salary_df["normalized_salary"].quantile(0.99)]

c1, c2 = st.columns(2)
with c1:
    fig = px.histogram(clip, x="normalized_salary", nbins=40, color_discrete_sequence=["#2563EB"])
    fig.add_vline(x=median_sal, line_dash="dash", line_color="#12B5A6",
                  annotation_text=f"Median {format_salary(median_sal)}", annotation_position="top right")
    fig.update_traces(marker_line_width=0, opacity=0.9)
    st.plotly_chart(_style(fig, f"How salaries are spread ({unit})"), use_container_width=True)
with c2:
    if "formatted_experience_level" in salary_df.columns:
        exp = salary_df.groupby("formatted_experience_level")["normalized_salary"].median()
        exp = exp.reindex([e for e in EXP_ORDER if e in exp.index]).reset_index()
        exp.columns = ["Level", "Median"]
        fig = px.bar(exp, x="Level", y="Median", color="Level",
                     color_discrete_sequence=BLUES[-len(exp):] if len(exp) else BLUES)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(_style(fig, f"Median salary by experience ({unit})"), use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    if "industry_name" in salary_df.columns:
        ind = (salary_df.groupby("industry_name")["normalized_salary"].agg(median="median", n="count")
               .query("n >= 5").sort_values("median").tail(10).reset_index())
        if not ind.empty:
            fig = px.bar(ind, x="median", y="industry_name", orientation="h", color_discrete_sequence=["#12B5A6"])
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(_style(fig, f"Top paying industries ({unit})"), use_container_width=True)
with c4:
    loc_col = "location" if "location" in df.columns else ("state" if "state" in df.columns else None)
    if loc_col:
        loc = df[loc_col].value_counts().head(10).sort_values().reset_index()
        loc.columns = ["Place", "Postings"]
        fig = px.bar(loc, x="Postings", y="Place", orientation="h", color_discrete_sequence=["#4F46E5"])
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(_style(fig, "Where the jobs are"), use_container_width=True)

c5, c6 = st.columns([3, 2])
with c5:
    prem = skill_premium(salary_df, market_key)
    if not prem.empty:
        prem = prem.sort_values("avg")
        fig = px.bar(prem, x="avg", y="skill", orientation="h", color="avg",
                     color_continuous_scale=["#BFD1FF", "#2563EB"])
        fig.update_traces(marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(_style(fig, f"Best paying skills ({unit})", 420), use_container_width=True)
    else:
        st.info("Skill data is not available for this market.")
with c6:
    if "formatted_experience_level" in df.columns:
        share = df["formatted_experience_level"].value_counts().reset_index()
        share.columns = ["Level", "Postings"]
        fig = px.pie(share, names="Level", values="Postings", hole=0.6, color_discrete_sequence=BLUES + ["#12B5A6"])
        fig.update_traces(textinfo="percent", sort=False)
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(_style(fig, "Who is being hired", 420).update_layout(showlegend=True),
                        use_container_width=True)

# ── Tools ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Your tools", "Jump straight to what you need"), unsafe_allow_html=True)
t1, t2, t3, t4 = st.columns(4)
tools = [
    (t1, "🔮", "Salary predictor", "Estimate your market salary with a confidence range.", "Open predictor", "pages/07_Salary_Predictor.py", "accent-blue"),
    (t2, "🤖", "AI coach", "Get a negotiation plan written from your numbers.", "Open coach", "pages/10_AI_Advisor.py", "accent-green"),
    (t3, "📁", "My offers", "Log offers privately and compare them with the market.", "Open tracker", "pages/11_My_Offers.py", "accent-purple"),
    (t4, "🧠", "Job analyser", "Pull skills and a salary band from any job post.", "Open analyser", "pages/09_NLP_Analyser.py", "accent-amber"),
]
for col, icon, title, desc, label, page, accent in tools:
    with col:
        st.markdown(f'<div class="quick-card {accent}"><div class="quick-card-icon">{icon}</div>'
                    f'<div class="quick-card-title">{title}</div><div class="quick-card-desc">{desc}</div></div>',
                    unsafe_allow_html=True)
        if st.button(label, key=f"tool_{page}", use_container_width=True):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("How it works", "Three steps to your salary plan"), unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)
for col, num, icon, title, desc in [
    (s1, 1, "📊", "Explore the market", "Browse pay by industry, city, company and skill."),
    (s2, 2, "🔮", "Enter your profile", "Add your role, experience and skills for a prediction."),
    (s3, 3, "🤖", "Get your plan", "Receive talking points and an opening script."),
]:
    col.markdown(step_card_html(num, icon, title, desc), unsafe_allow_html=True)

st.divider()
st.markdown(_flat(f"""
<div style="display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:wrap;padding:6px 0 12px;">
  {lockup(26)}
  <span style="font-size:13px;color:#7A8AA0;">Built with Python, Streamlit, scikit-learn and Google Gemini. &copy; 2026 SalaryIQ</span>
</div>"""), unsafe_allow_html=True)
