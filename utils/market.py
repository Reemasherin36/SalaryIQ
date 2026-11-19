"""
utils/market.py
Dual-market switcher — returns correct data, formatters, and labels
for US (LinkedIn) or India (Naukri) based on session state.
"""
import streamlit as st
import numpy as np
import pandas as pd


def get_market() -> str:
    """Return current market key: 'us' or 'india'."""
    return st.session_state.get("market", "us")


def is_india() -> bool:
    """Return True if Indian market is selected."""
    return get_market() == "india"


def format_salary(val) -> str:
    """Format salary in the correct currency for current market.

    Args:
        val: Numeric salary value.

    Returns:
        '₹12.5 LPA' for India or '$120,000' for US.
    """
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "N/A"
        if is_india():
            return f"₹{float(val):.1f} LPA"
        return f"${int(round(float(val))):,}"
    except Exception:
        return "N/A"


def salary_unit() -> str:
    """Return salary unit label for current market."""
    return "LPA" if is_india() else "USD/yr"


def currency_symbol() -> str:
    """Return currency symbol for current market."""
    return "₹" if is_india() else "$"


def market_label() -> str:
    """Return human-readable market label."""
    return "🇮🇳 Indian Market" if is_india() else "🇺🇸 US Market"


def get_market_data() -> pd.DataFrame:
    """Return the correct salary DataFrame for the current market.

    Returns:
        US LinkedIn DataFrame or Indian Naukri DataFrame.
    """
    if is_india():
        from utils.india_loader import load_india_data
        return load_india_data()
    else:
        from utils.data_loader import load_postings
        from utils.preprocessing import clean_postings
        return clean_postings(load_postings())


def get_top_titles(n: int = 50) -> list:
    """Return top job titles for the current market."""
    if is_india():
        from utils.india_loader import get_india_titles
        return get_india_titles(n)
    else:
        from utils.data_loader import get_top_job_titles
        return get_top_job_titles(n)


def get_top_skills(n: int = 50) -> list:
    """Return top skills for the current market."""
    if is_india():
        from utils.india_loader import get_india_skills
        return get_india_skills(n)
    else:
        from utils.data_loader import get_top_skills as us_skills
        return us_skills(n)


def get_top_locations(n: int = 30) -> list:
    """Return top locations/states for the current market."""
    if is_india():
        from utils.india_loader import get_india_cities
        return get_india_cities(n)
    else:
        from utils.data_loader import get_states_list
        return get_states_list()


def get_top_industries(n: int = 30) -> list:
    """Return top industries for the current market."""
    if is_india():
        df = get_market_data()
        if not df.empty and "industry_name" in df.columns:
            return df["industry_name"].value_counts().head(n).index.tolist()
        return []
    else:
        from utils.data_loader import get_top_industries as us_ind
        return us_ind(n)


def market_switcher_widget() -> None:
    """Render the market selector toggle in the sidebar."""
    st.sidebar.markdown("### 🌍 Market")
    current = st.session_state.get("market", "us")
    options = ["🇺🇸 US Market", "🇮🇳 Indian Market"]
    current_label = options[1] if current == "india" else options[0]
    selected = st.sidebar.radio(
        "Select Market",
        options,
        index=options.index(current_label),
        key="market_radio",
        label_visibility="collapsed",
        horizontal=True,
    )
    new_market = "india" if "Indian" in selected else "us"
    if new_market != current:
        st.session_state["market"] = new_market
        st.rerun()
