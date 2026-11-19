"""pages/10_AI_Advisor.py — Gemini AI Advisor with dual market support."""
import streamlit as st
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.auth import require_login, logout
from utils.theme import render_theme_css, theme_switcher_widget
from utils.helpers import (inject_css, compute_salary_stats,
                            salary_percentile, get_percentile_n)
from utils.market import (get_market_data, format_salary, market_label,
                           is_india, get_top_titles, get_top_skills,
                           get_top_industries, get_top_locations)
from utils.nav import show_sidebar

st.set_page_config(layout="wide", page_title="🤖 AI Advisor", page_icon="🤖")
inject_css(); render_theme_css()
if not require_login(): st.stop()
show_sidebar()

# ══ SET YOUR GEMINI KEY HERE ══════════════════════════════════════════════════
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
# ═════════════════════════════════════════════════════════════════════════════

flag = "🇮🇳" if is_india() else "🇺🇸"
unit = "LPA" if is_india() else "USD/yr"

with st.spinner("Loading market data…"):
    df         = get_market_data()
    salary_df  = df[df["normalized_salary"].notna()].copy()
    top_titles = get_top_titles(50)
    top_skills = get_top_skills(50)
    top_industries = get_top_industries(30)
    locations  = get_top_locations(30)


def call_gemini(prompt: str, api_key: str) -> str:
    """Call Gemini API with automatic model fallback and retry logic.

    Tries multiple current model names in order since Google frequently
    updates which models are available on the free tier. Retries once
    with a short delay if a rate limit (429) is hit.

    Args:
        prompt: The full prompt text to send.
        api_key: Gemini API key.

    Returns:
        Generated text response, or an error string prefixed with
        HTTP_<code> or ERROR.
    """
    import urllib.request, urllib.error

    # Try models in order of preference — free tier availability changes
    # frequently, so fall back automatically instead of hardcoding one.
    models_to_try = [
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash-lite",
    ]

    last_error = ""

    for model in models_to_try:
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={api_key}")
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096},
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload,
                                      headers={"Content-Type": "application/json"},
                                      method="POST")
        for attempt in range(2):  # try once, retry once after short wait
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8")
                try:
                    msg = json.loads(body)["error"]["message"]
                except Exception:
                    msg = body
                last_error = f"HTTP_{e.code}: {msg}"

                if e.code == 429:
                    if attempt == 0:
                        time.sleep(3)  # brief retry wait
                        continue
                    else:
                        break  # move to next model
                elif e.code == 404:
                    break  # model not available, try next model
                else:
                    return last_error
            except Exception as e:
                last_error = f"ERROR: {str(e)}"
                break

    return last_error


def build_prompt(profile: dict, market: dict) -> str:
    pct_label = get_percentile_n(
        salary_percentile(profile["target_salary"], salary_df["normalized_salary"])
    )
    skills_str = ", ".join(profile["skills"][:6]) if profile["skills"] else "Not specified"
    currency_note = "in Indian Rupees (LPA - Lakhs Per Annum)" if is_india() else "in USD"
    return (
        f"You are an expert salary negotiation coach for the {flag} {'Indian' if is_india() else 'US'} job market.\n\n"
        f"CANDIDATE PROFILE:\n"
        f"- Role: {profile['current_title']} → {profile['target_title']}\n"
        f"- Experience: {profile['years_exp']} years\n"
        f"- Location: {profile['location']}\n"
        f"- Industry: {profile['industry']}\n"
        f"- Current Salary: {format_salary(profile['current_salary'])} ({currency_note})\n"
        f"- Target Salary: {format_salary(profile['target_salary'])} ({currency_note})\n"
        f"- Skills: {skills_str}\n"
        f"- Remote Preference: {profile['remote_pref']}\n\n"
        f"REAL MARKET DATA ({flag} {'Indian Naukri' if is_india() else 'US LinkedIn'} dataset):\n"
        f"- Market Median: {format_salary(market['median'])}\n"
        f"- 25th Percentile: {format_salary(market['p25'])}\n"
        f"- 75th Percentile: {format_salary(market['p75'])}\n"
        f"- 90th Percentile: {format_salary(market['p90'])}\n"
        f"- Candidate target is at: {pct_label}\n\n"
        f"Provide a complete negotiation strategy:\n"
        f"## 1. Assessment — Is the ask reasonable?\n"
        f"## 2. Five Talking Points — Reference actual salary figures\n"
        f"## 3. Two Things to AVOID\n"
        f"## 4. Opening Statement — Word-for-word script\n"
        f"## 5. If Budget is Fixed — What to say and what else to negotiate\n\n"
        f"Note: All salary figures are {currency_note}. Be specific to the "
        f"{'Indian' if is_india() else 'US'} job market context. Keep the response concise."
    )


st.markdown(f"# 🤖 AI Negotiation Advisor {flag}")
st.markdown(f"*{market_label()} — Gemini AI strategy grounded in real market data*")
st.divider()

st.markdown("### 📋 Your Negotiation Profile")
with st.form("ai_form"):
    c1, c2 = st.columns(2)
    with c1:
        cur_title  = st.selectbox("Current Title", ["(Other)"]+sorted(top_titles))
        tgt_title  = st.selectbox("Target Role", ["(Same as current)"]+sorted(top_titles))
        years_exp  = st.slider("Years of Experience", 0, 30, 5)
        cur_salary = st.number_input(
            f"Current Salary ({unit})", min_value=0.0,
            max_value=500.0 if is_india() else 2_000_000.0,
            value=8.0 if is_india() else 80_000.0,
            step=0.5 if is_india() else 1_000.0)
        tgt_salary = st.number_input(
            f"Target Salary ({unit})", min_value=0.0,
            max_value=500.0 if is_india() else 2_000_000.0,
            value=15.0 if is_india() else 110_000.0,
            step=0.5 if is_india() else 1_000.0)
    with c2:
        loc_label = "City" if is_india() else "State"
        location  = st.selectbox(loc_label, locations if locations else ["Bangalore","Mumbai"])
        industry  = st.selectbox("Industry", ["(Other)"]+sorted(top_industries))
        skills    = st.multiselect("Your Skills", sorted(top_skills))
        remote    = st.radio("Remote Preference",
                              ["Remote","Hybrid","On-site"], horizontal=True)
        company   = st.text_input("Company (optional)")
    submitted = st.form_submit_button(
        "🤖 Generate AI Negotiation Strategy", use_container_width=True)

if submitted:
    use_title = tgt_title if tgt_title != "(Same as current)" else cur_title
    market    = compute_salary_stats(salary_df["normalized_salary"])
    pct       = salary_percentile(tgt_salary, salary_df["normalized_salary"])

    st.markdown("---")
    st.markdown(f"### 📊 Your Market Position {flag}")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Your Target",     format_salary(tgt_salary))
    m2.metric("Market Median",   format_salary(market["median"]))
    m3.metric("Market 75th Pct", format_salary(market["p75"]))
    m4.metric("Your Percentile", get_percentile_n(pct))
    st.markdown("<br>",unsafe_allow_html=True)

    if pct >= 90:
        st.warning("⚠️ Above 90th percentile — prepare strong justification.")
    elif pct >= 75:
        st.info(f"📈 Top 25% ask — anchor to {format_salary(market['p75'])} 75th percentile.")
    elif pct >= 50:
        st.success("✅ Well within market range — negotiate confidently.")
    else:
        st.info(f"💡 Consider raising target — market median is {format_salary(market['median'])}.")

    st.markdown(f"### 🤖 Gemini AI Strategy {flag}")

    if GEMINI_API_KEY == "PASTE_YOUR_KEY_HERE" or len(GEMINI_API_KEY) < 10:
        st.error("API key not set. Open pages/10_AI_Advisor.py and paste your Gemini key.")
    else:
        profile = {
            "current_title": cur_title, "target_title": use_title,
            "years_exp": years_exp, "location": location, "industry": industry,
            "current_salary": cur_salary, "target_salary": tgt_salary,
            "skills": skills, "remote_pref": remote, "company": company,
        }
        with st.spinner(f"🤖 Gemini generating your {flag} strategy…"):
            response = call_gemini(build_prompt(profile, market), GEMINI_API_KEY)

        if response.startswith("HTTP_") or response.startswith("ERROR"):
            if "429" in response:
                st.warning(
                    "⏳ **Daily or per-minute quota reached on the free Gemini tier.**\n\n"
                    "Google's free tier now allows a limited number of requests per day "
                    "(not just per minute). If this keeps happening immediately on every "
                    "attempt, you have likely hit the **daily quota (RPD)**, which resets "
                    "at midnight Pacific Time (~12:30 PM IST).\n\n"
                    "**Options:**\n"
                    "- Wait until the daily reset\n"
                    "- Generate a **new API key** on a different Google account at "
                    "https://aistudio.google.com/app/apikey\n"
                    "- Enable billing on Google Cloud Console for higher limits (still free "
                    "for low usage)"
                )
            elif "404" in response:
                st.error(
                    "Model not found on your account. Your API key may not have access "
                    "to any Gemini Flash model. Generate a new key at "
                    "https://aistudio.google.com/app/apikey"
                )
            elif "403" in response:
                st.error(
                    "Permission denied. Make sure your key was created in "
                    "**Google AI Studio**, not Google Cloud Console."
                )
            else:
                st.error(f"API Error: {response}")
        else:
            st.markdown(response)
            import pandas as pd
            report = pd.DataFrame({
                "Field": ["Market","Role","Location","Current Salary",
                          "Target Salary","Market Median","Percentile"],
                "Value": [market_label(), use_title, location,
                          format_salary(cur_salary), format_salary(tgt_salary),
                          format_salary(market["median"]), get_percentile_n(pct)],
            })
            st.download_button("⬇️ Download Report",
                               report.to_csv(index=False).encode(),
                               "ai_report.csv","text/csv")
