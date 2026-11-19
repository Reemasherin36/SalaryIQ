"""utils/theme.py — LinkedIn theme system. CSS injected via st.markdown only."""
import streamlit as st

THEMES = {"☀️ Light": "light", "🌙 Dark": "dark"}

def get_theme_key():
    return st.session_state.get("theme", "light")

def render_theme_css():
    """Inject all LinkedIn CSS into the page. Called on every page."""

    light_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{
        font-family:'Inter',-apple-system,sans-serif!important;
        background:#F3F2EE!important;}
    .main .block-container{padding:24px 28px!important;max-width:1280px;}
    [data-testid="stSidebar"]{background:#1C1C1C!important;border-right:1px solid #333!important;}
    [data-testid="stSidebar"] *{color:#B0B7BF!important;}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3{color:#FFFFFF!important;}
    [data-testid="stSidebar"] hr{border-color:#333!important;}
    [data-testid="stSidebar"] p{color:#B0B7BF!important;}
    [data-testid="stSidebar"] .stPageLink a,
    [data-testid="stSidebar"] .stPageLink a p,
    [data-testid="stSidebar"] .stPageLink span{
        color:#B0B7BF!important;font-weight:500!important;font-size:14px!important;
        border-radius:6px!important;padding:8px 10px!important;
        transition:all .2s!important;text-decoration:none!important;}
    [data-testid="stSidebar"] .stPageLink a:hover,
    [data-testid="stSidebar"] .stPageLink a:hover p{
        background:rgba(10,102,194,.2)!important;color:#70B5F9!important;}
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSlider label{color:#86939E!important;font-size:13px!important;}
    [data-testid="stSidebar"] .stButton>button{
        background:transparent!important;color:#B0B7BF!important;
        border:1px solid #444!important;border-radius:6px!important;
        font-size:13px!important;padding:8px 16px!important;box-shadow:none!important;}
    [data-testid="stSidebar"] .stButton>button:hover{
        background:rgba(255,255,255,.08)!important;color:#FFFFFF!important;transform:none!important;}
    h1{font-size:20px!important;font-weight:800!important;color:#1C1C1C!important;}
    h2{font-size:18px!important;font-weight:700!important;color:#1C1C1C!important;}
    h3{font-size:16px!important;font-weight:600!important;color:#38434F!important;}
    .kpi-card{background:#FFFFFF!important;border:1px solid #E0DFDC!important;
        border-radius:10px!important;padding:20px 18px!important;transition:all .2s!important;
        box-shadow:0 2px 6px rgba(0,0,0,.05)!important;}
    .kpi-card:hover{box-shadow:0 4px 12px rgba(0,0,0,.08)!important;transform:translateY(-1px)!important;}
    .kpi-label{font-size:11px!important;font-weight:700!important;text-transform:uppercase!important;
        letter-spacing:.07em!important;color:#86939E!important;margin-bottom:5px!important;}
    .kpi-value{font-size:24px!important;font-weight:800!important;color:#1C1C1C!important;
        letter-spacing:-.02em!important;line-height:1!important;margin-bottom:5px!important;}
    .kpi-delta{font-size:12px!important;font-weight:500!important;color:#057642!important;}
    .kpi-icon{font-size:22px!important;margin-bottom:10px!important;width:40px!important;
        height:40px!important;border-radius:8px!important;display:flex!important;
        align-items:center!important;justify-content:center!important;}
    .kpi-icon.blue{background:#EAF0F8!important;}
    .kpi-icon.green{background:#E8F5EE!important;}
    .kpi-icon.amber{background:#FEF3C7!important;}
    .kpi-icon.purple{background:#EDE9FE!important;}
    .kpi-icon.cyan{background:#E0F7FF!important;}
    .quick-card{background:#FFFFFF!important;border:1px solid #E0DFDC!important;
        border-radius:10px!important;padding:20px!important;transition:all .2s!important;
        box-shadow:0 1px 4px rgba(0,0,0,.04)!important;}
    .quick-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)!important;
        border-color:#0A66C2!important;transform:translateY(-2px)!important;}
    .quick-card.accent-blue{border-top:3px solid #0A66C2!important;}
    .quick-card.accent-green{border-top:3px solid #057642!important;}
    .quick-card.accent-purple{border-top:3px solid #7C3AED!important;}
    .quick-card.accent-amber{border-top:3px solid #F59E0B!important;}
    .quick-card-icon{font-size:28px!important;margin-bottom:10px!important;}
    .quick-card-title{font-size:15px!important;font-weight:700!important;color:#1C1C1C!important;margin-bottom:5px!important;}
    .quick-card-desc{font-size:13px!important;color:#56687A!important;line-height:1.5!important;}
    .step-card{background:#FFFFFF!important;border:1px solid #E0DFDC!important;
        border-radius:10px!important;padding:24px 20px!important;text-align:center!important;transition:all .2s!important;}
    .step-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)!important;transform:translateY(-2px)!important;}
    .step-num{width:42px!important;height:42px!important;border-radius:50%!important;
        background:#0A66C2!important;color:white!important;display:flex!important;
        align-items:center!important;justify-content:center!important;
        font-size:16px!important;font-weight:800!important;margin:0 auto 12px!important;}
    .step-icon{font-size:30px!important;margin-bottom:10px!important;}
    .step-title{font-size:14px!important;font-weight:700!important;color:#1C1C1C!important;margin-bottom:6px!important;}
    .step-desc{font-size:12px!important;color:#56687A!important;line-height:1.6!important;}
    .section-header{display:flex!important;align-items:center!important;gap:8px!important;
        margin-bottom:16px!important;padding-bottom:12px!important;border-bottom:1px solid #E0DFDC!important;}
    .section-dot{width:6px!important;height:6px!important;border-radius:50%!important;
        background:#0A66C2!important;flex-shrink:0!important;}
    .section-title{font-size:16px!important;font-weight:700!important;color:#1C1C1C!important;margin:0!important;}
    .li-hero{background:#FFFFFF!important;border:1px solid #E0DFDC!important;
        border-radius:12px!important;overflow:hidden!important;margin-bottom:20px!important;}
    .li-hero-cover{height:120px!important;
        background:linear-gradient(135deg,#0A66C2 0%,#004182 60%,#000000 100%)!important;}
    .li-hero-body{padding:0 24px 24px!important;}
    .li-hero-avatar{width:80px!important;height:80px!important;border-radius:50%!important;
        background:linear-gradient(135deg,#0A66C2,#004182)!important;
        border:4px solid white!important;display:flex!important;
        align-items:center!important;justify-content:center!important;
        font-size:32px!important;margin-top:-40px!important;}
    .li-hero-name{font-size:22px!important;font-weight:800!important;color:#1C1C1C!important;
        letter-spacing:-.02em!important;margin:10px 0 4px!important;}
    .li-hero-subtitle{font-size:14px!important;color:#38434F!important;margin-bottom:4px!important;}
    .li-hero-meta{font-size:13px!important;color:#0A66C2!important;font-weight:600!important;}
    .li-hero-stats{display:flex!important;gap:24px!important;margin-top:16px!important;
        padding-top:16px!important;border-top:1px solid #E0DFDC!important;flex-wrap:wrap!important;}
    .li-hero-stat-val{font-size:18px!important;font-weight:800!important;color:#1C1C1C!important;}
    .li-hero-stat-lbl{font-size:11px!important;color:#86939E!important;margin-top:2px!important;}
    .prediction-card{background:#FFFFFF!important;border:1px solid #E0DFDC!important;
        border-radius:12px!important;padding:36px 32px!important;text-align:center!important;
        position:relative!important;overflow:hidden!important;}
    .prediction-card::before{content:''!important;position:absolute!important;top:0!important;
        left:0!important;right:0!important;height:4px!important;
        background:linear-gradient(90deg,#0A66C2,#004182)!important;}
    .prediction-label{font-size:11px!important;font-weight:700!important;
        text-transform:uppercase!important;letter-spacing:.08em!important;
        color:#0A66C2!important;margin-bottom:8px!important;}
    .prediction-amount{font-size:3.5rem!important;font-weight:900!important;
        color:#1C1C1C!important;letter-spacing:-.04em!important;
        line-height:1!important;margin-bottom:6px!important;}
    .prediction-range{font-size:13px!important;color:#86939E!important;margin-bottom:16px!important;}
    .prediction-badge{display:inline-block!important;background:#E8F5EE!important;
        color:#057642!important;padding:5px 16px!important;border-radius:100px!important;
        font-size:12px!important;font-weight:700!important;border:1px solid #C6E8D4!important;}
    .tip-card{background:#FFFFFF!important;border:1px solid #E0DFDC!important;
        border-radius:10px!important;padding:16px!important;margin-bottom:10px!important;
        display:flex!important;gap:14px!important;align-items:flex-start!important;}
    .tip-card:hover{border-color:#0A66C2!important;}
    .tip-number{width:30px!important;height:30px!important;border-radius:6px!important;
        background:#0A66C2!important;color:white!important;display:flex!important;
        align-items:center!important;justify-content:center!important;
        font-size:13px!important;font-weight:800!important;flex-shrink:0!important;}
    .tip-label{font-size:10px!important;font-weight:700!important;
        text-transform:uppercase!important;letter-spacing:.06em!important;
        color:#0A66C2!important;margin-bottom:3px!important;}
    .tip-text{font-size:13px!important;color:#38434F!important;line-height:1.6!important;}
    .stButton>button{background:#0A66C2!important;color:white!important;
        border:none!important;border-radius:24px!important;font-weight:700!important;
        font-size:14px!important;padding:10px 24px!important;transition:all .2s!important;box-shadow:none!important;}
    .stButton>button:hover{background:#004182!important;transform:translateY(-1px)!important;}
    .stTextInput input,.stNumberInput input,.stTextArea textarea{
        border-radius:6px!important;border:1.5px solid #B0B7BF!important;
        font-size:14px!important;color:#1C1C1C!important;background:white!important;}
    .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{
        border-color:#0A66C2!important;box-shadow:0 0 0 2px rgba(10,102,194,.2)!important;}
    .stSelectbox>div>div,.stMultiselect>div>div{
        border-radius:6px!important;border:1.5px solid #B0B7BF!important;background:white!important;}
    label{font-size:13px!important;font-weight:600!important;color:#38434F!important;}
    .stTabs [data-baseweb="tab-list"]{gap:0!important;background:white!important;
        border-bottom:2px solid #E0DFDC!important;padding:0 4px!important;}
    .stTabs [data-baseweb="tab"]{border-radius:0!important;padding:10px 18px!important;
        font-weight:600!important;font-size:14px!important;color:#56687A!important;
        background:transparent!important;border:none!important;
        border-bottom:3px solid transparent!important;}
    .stTabs [aria-selected="true"]{color:#0A66C2!important;border-bottom-color:#0A66C2!important;}
    [data-testid="stMetric"]{background:white!important;border:1px solid #E0DFDC!important;
        border-radius:10px!important;padding:16px 18px!important;}
    [data-testid="stMetricLabel"]{font-size:11px!important;font-weight:700!important;
        color:#86939E!important;text-transform:uppercase!important;letter-spacing:.06em!important;}
    [data-testid="stMetricValue"]{font-size:22px!important;font-weight:800!important;color:#1C1C1C!important;}
    .stDataFrame{border:1px solid #E0DFDC!important;border-radius:10px!important;overflow:hidden!important;}
    .stDataFrame th{background:#F8F8F8!important;font-size:11px!important;font-weight:700!important;
        text-transform:uppercase!important;letter-spacing:.05em!important;
        color:#86939E!important;padding:12px 14px!important;}
    .stDataFrame td{font-size:13px!important;padding:10px 14px!important;color:#38434F!important;}
    .stDataFrame tr:hover td{background:#EAF0F8!important;}
    .stSuccess{border-radius:10px!important;border-left:4px solid #057642!important;background:#E8F5EE!important;}
    .stInfo{border-radius:10px!important;border-left:4px solid #0A66C2!important;background:#EAF0F8!important;}
    .stWarning{border-radius:10px!important;border-left:4px solid #F59E0B!important;}
    .stError{border-radius:10px!important;border-left:4px solid #CC1016!important;}
    .streamlit-expanderHeader{background:white!important;border:1px solid #E0DFDC!important;
        border-radius:10px!important;font-weight:600!important;font-size:14px!important;color:#1C1C1C!important;}
    hr{border:none!important;border-top:1px solid #E0DFDC!important;margin:16px 0!important;}
    ::-webkit-scrollbar{width:5px;height:5px;}
    ::-webkit-scrollbar-thumb{background:#C8D6E0;border-radius:10px;}
    </style>"""

    dark_css = """
    <style>
    html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{
        background:#1B1F23!important;}
    [data-testid="stSidebar"]{background:#111418!important;border-color:#2D3139!important;}
    .kpi-card,.quick-card,.step-card,.tip-card,.li-hero,.prediction-card{
        background:#1E2328!important;border-color:#2D3139!important;}
    .kpi-value,.quick-card-title,.step-title,.li-hero-name,.prediction-amount{color:#F8F8F8!important;}
    .kpi-label,.quick-card-desc,.step-desc,.li-hero-stat-lbl{color:#64748B!important;}
    .li-hero-subtitle,.li-hero-stat-val{color:#B0B7BF!important;}
    .li-hero-stats,.section-header{border-color:#2D3139!important;}
    .section-title{color:#F8F8F8!important;}
    h1,h2,h3{color:#F8F8F8!important;}
    p,span,div,label{color:#B0B7BF!important;}
    [data-testid="stMetric"]{background:#1E2328!important;border-color:#2D3139!important;}
    [data-testid="stMetricValue"]{color:#F8F8F8!important;}
    [data-testid="stMetricLabel"]{color:#64748B!important;}
    .stTextInput input,.stNumberInput input,.stTextArea textarea{
        background:#1E2328!important;color:#F8F8F8!important;border-color:#2D3139!important;}
    .stSelectbox>div>div,.stMultiselect>div>div{
        background:#1E2328!important;color:#F8F8F8!important;border-color:#2D3139!important;}
    label{color:#B0B7BF!important;}
    .stTabs [data-baseweb="tab-list"]{background:#1E2328!important;border-color:#2D3139!important;}
    .stTabs [data-baseweb="tab"]{color:#64748B!important;}
    .stTabs [aria-selected="true"]{color:#70B5F9!important;border-bottom-color:#70B5F9!important;}
    .stDataFrame th{background:#111418!important;color:#64748B!important;}
    .stDataFrame td{color:#B0B7BF!important;}
    .stDataFrame tr:hover td{background:#1E2328!important;}
    hr{border-color:#2D3139!important;}
    .streamlit-expanderHeader{background:#1E2328!important;border-color:#2D3139!important;color:#F8F8F8!important;}
    </style>"""

    # Always inject light CSS
    st.markdown(light_css, unsafe_allow_html=True)

    # Only inject dark CSS on top if dark mode selected
    if get_theme_key() == "dark":
        st.markdown(dark_css, unsafe_allow_html=True)


def theme_switcher_widget():
    st.sidebar.markdown("### 🎨 Appearance")
    current = st.session_state.get("theme", "light")
    lmap = {v: k for k, v in THEMES.items()}
    sel = st.sidebar.radio(
        "Theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(lmap.get(current, "☀️ Light")),
        key="theme_radio",
        label_visibility="collapsed"
    )
    new = THEMES[sel]
    if new != current:
        st.session_state["theme"] = new
        st.rerun()