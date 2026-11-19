"""utils/helpers.py — Premium UI helpers for 2026 SaaS design."""
from __future__ import annotations
import os, streamlit as st
import numpy as np, pandas as pd
from typing import Optional, Tuple

def format_currency(val):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)): return "N/A"
        return f"${int(round(val)):,}"
    except: return "N/A"

def format_number(val):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)): return "N/A"
        val = float(val)
        if abs(val) >= 1_000_000: return f"{val/1_000_000:.1f}M"
        if abs(val) >= 1_000: return f"{val/1_000:.1f}K"
        return f"{val:.0f}"
    except: return "N/A"

def format_percent(val, decimals=1):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)): return "N/A"
        return f"{float(val):.{decimals}f}%"
    except: return "N/A"

def salary_percentile(value, series):
    clean = series.dropna()
    if clean.empty: return 50.0
    return round(float((clean < value).sum() / len(clean) * 100), 1)

def get_percentile_label(pct):
    if pct >= 90: return "top 10%"
    elif pct >= 75: return "top 25%"
    elif pct >= 50: return "top 50%"
    elif pct >= 25: return "bottom 50%"
    return "bottom 25%"

def get_percentile_n(pct):
    p = int(round(pct))
    suffix = {1:"st",2:"nd",3:"rd"}.get(p%10 if p%100 not in (11,12,13) else 0,"th")
    return f"{p}{suffix} percentile"

def get_top_n_values(series, n=10):
    counts = series.value_counts().head(n).reset_index()
    counts.columns = ["value","count"]
    return counts

def inject_css(filepath="assets/style.css"):
    abs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), filepath)
    try:
        with open(abs_path, encoding="utf-8") as f: css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError: pass

def experience_sort_order():
    return ["Internship","Entry level","Associate","Mid-Senior level","Director","Executive"]

def company_size_sort_order():
    return ["1-10","11-50","51-200","201-500","501-1000","1001-5000","5001-10000","10001+"]

def salary_range_label(predicted, pct=0.15):
    low = max(0.0, predicted*(1-pct))
    high = predicted*(1+pct)
    return round(low,0), round(high,0)

def compute_salary_stats(series):
    clean = series.dropna()
    if clean.empty: return {k:0 for k in ["mean","median","min","max","p25","p75","p10","p90","std"]}
    return {"mean":clean.mean(),"median":clean.median(),"min":clean.min(),"max":clean.max(),
            "p10":clean.quantile(.10),"p25":clean.quantile(.25),
            "p75":clean.quantile(.75),"p90":clean.quantile(.90),"std":clean.std()}

def safe_divide(n, d, default=0.0):
    return default if d == 0 else n/d

# ── Premium UI Components ──────────────────────────────────────
def kpi_card(title, value, delta=None, icon="📊", color="blue"):
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon {color}">{icon}</div>
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>"""

# Keep backward compat
def metric_card(title, value, delta=None, icon=""):
    return kpi_card(title, value, delta, icon)

def tip_card(number, text, label="Talking Point"):
    return f"""
    <div class="tip-card">
        <div class="tip-number">{number}</div>
        <div class="tip-content">
            <div class="tip-label">💡 {label} {number}</div>
            <div class="tip-text">{text}</div>
        </div>
    </div>"""

def negotiation_tip_card(number, text):
    return tip_card(number, text)

def step_card_html(step_num, icon, title, description):
    return f"""
    <div class="step-card">
        <div class="step-icon">{icon}</div>
        <div class="step-num">{step_num}</div>
        <div class="step-title">{title}</div>
        <div class="step-desc">{description}</div>
    </div>"""

def section_header(title, subtitle=""):
    sub = f'<p style="font-size:13px;color:var(--text-3);margin:4px 0 0;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div class="section-header">
        <div class="section-dot"></div>
        <div>
            <div class="section-title">{title}</div>
            {sub}
        </div>
    </div>"""

def chip(text, color="blue"):
    return f'<span class="chip chip-{color}">{text}</span>'
