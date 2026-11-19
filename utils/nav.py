"""utils/nav.py — Shared sidebar shown on every signed-in page."""
import streamlit as st

from utils.auth import get_user_email, get_username, logout
from utils.brand import lockup
from utils.market import market_label, market_switcher_widget
from utils.theme import theme_switcher_widget


def show_sidebar(page_title: str = "", page_desc: str = "") -> None:
    """Render the sidebar: brand, account, market switch, navigation, sign out."""
    with st.sidebar:
        st.markdown(f'<div style="padding:8px 0 14px;">{lockup(34, dark_bg=True)}</div>',
                    unsafe_allow_html=True)

        name = get_username().title()
        email = get_user_email()
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:10px;background:#1F2A3A;
            border-radius:10px;padding:10px 12px;margin-bottom:4px;">
            <div style="width:34px;height:34px;border-radius:50%;background:#12B5A6;display:flex;
            align-items:center;justify-content:center;color:#0D1B2A;font-size:14px;font-weight:800;
            flex-shrink:0;">{name[:1].upper()}</div>
            <div style="min-width:0;"><div style="font-size:13px;font-weight:700;color:#FFFFFF;">{name}</div>
            <div style="font-size:11px;color:#8FA3BF;overflow:hidden;text-overflow:ellipsis;
            white-space:nowrap;">{email}</div></div></div>""",
            unsafe_allow_html=True,
        )
        st.divider()

        market_switcher_widget()
        st.divider()

        st.markdown('<p style="font-size:11px;font-weight:700;color:#8FA3BF;letter-spacing:.08em;'
                    'margin:0 0 6px 4px;">MAIN</p>', unsafe_allow_html=True)
        st.page_link("app.py", label="🏠  Home")
        st.page_link("pages/07_Salary_Predictor.py", label="🔮  Salary Predictor")
        st.page_link("pages/08_Negotiation_Advisor.py", label="🤝  Negotiation Advisor")
        st.page_link("pages/10_AI_Advisor.py", label="🤖  AI Coach")
        st.page_link("pages/09_NLP_Analyser.py", label="🧠  Job Analyser")
        st.page_link("pages/11_My_Offers.py", label="📁  My Offers")
        st.divider()

        st.markdown('<p style="font-size:11px;font-weight:700;color:#8FA3BF;letter-spacing:.08em;'
                    'margin:0 0 6px 4px;">ANALYTICS</p>', unsafe_allow_html=True)
        st.page_link("pages/01_Salary_Dashboard.py", label="📊  Salary Dashboard")
        st.page_link("pages/02_Salary_Analysis.py", label="💰  Deep Analysis")
        st.page_link("pages/03_Skills_vs_Salary.py", label="🛠️  Skills Impact")
        st.page_link("pages/04_Industry_Insights.py", label="🏭  Industries")
        st.page_link("pages/05_Location_Analysis.py", label="📍  Locations")
        st.page_link("pages/06_Company_Analysis.py", label="🏢  Companies")
        st.divider()

        theme_switcher_widget()
        st.divider()

        if st.button("🚪  Sign out", use_container_width=True, key="nav_logout"):
            logout()
            st.rerun()

        st.markdown(f'<p style="font-size:11px;color:#8FA3BF;text-align:center;margin-top:8px;">'
                    f'{market_label()}</p>', unsafe_allow_html=True)
