"""utils/auth.py — Landing page, registration, login and private user records.

Security notes
- Passwords are hashed with PBKDF2-HMAC-SHA256 (random salt, 200k rounds).
  Accounts created with the older plain SHA-256 hash still work and are
  upgraded on their next successful login.
- Every page calls require_login(); signed-out visitors only ever see the
  landing page and the sign-in / sign-up forms.
- Private records are stored per account and every read, write and delete
  is keyed to the signed-in user's email on the server, never to a value
  sent from the browser.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import uuid

import streamlit as st

from utils.brand import LOGO_SVG, lockup

# Older modules import this name; it now points at the new SalaryIQ mark.
LI_LOGO_SVG = LOGO_SVG

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_USERS_FILE = os.path.join(_DATA_DIR, "users.json")
_RECORDS_FILE = os.path.join(_DATA_DIR, "user_records.json")

_PBKDF2_ROUNDS = 200_000
_MAX_FAILS = 5
_LOCK_SECONDS = 60


# ── Storage helpers ───────────────────────────────────────────────────────────
def _read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


# ── Password hashing ──────────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2${_PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2$"):
        try:
            _, rounds, salt, digest = stored.split("$")
            calc = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
            return hmac.compare_digest(calc.hex(), digest)
        except Exception:
            return False
    legacy = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(legacy, stored)


# ── Validation ────────────────────────────────────────────────────────────────
def _is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$", email))


def password_problems(password: str) -> list:
    problems = []
    if len(password) < 8:
        problems.append("Use at least 8 characters.")
    if not re.search(r"[A-Za-z]", password):
        problems.append("Add at least one letter.")
    if not re.search(r"\d", password):
        problems.append("Add at least one number.")
    return problems


# ── Accounts ──────────────────────────────────────────────────────────────────
def register_user(name: str, email: str, password: str, confirm: str) -> tuple:
    """Create an account. Returns (ok, list_of_error_messages)."""
    errors = []
    name = name.strip()
    email = email.strip().lower()
    if len(name) < 2:
        errors.append("Enter your full name.")
    if not _is_valid_email(email):
        errors.append("Enter a valid email address, for example name@example.com.")
    errors += password_problems(password)
    if password != confirm:
        errors.append("The two passwords do not match.")
    if errors:
        return False, errors

    users = _read_json(_USERS_FILE)
    if email in users:
        return False, ["An account with this email already exists. Sign in instead."]
    users[email] = {
        "name": name,
        "password_hash": _hash_password(password),
        "created_at": time.time(),
    }
    _write_json(_USERS_FILE, users)
    return True, []


def check_credentials(email: str, password: str) -> tuple:
    """Verify a login. Returns (ok, display_name)."""
    email = email.strip().lower()
    users = _read_json(_USERS_FILE)
    user = users.get(email)
    if not user or not _verify_password(password, user.get("password_hash", "")):
        return False, ""
    if not user["password_hash"].startswith("pbkdf2$"):
        user["password_hash"] = _hash_password(password)
        _write_json(_USERS_FILE, users)
    return True, user.get("name", email.split("@")[0])


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in", False))


def login(email: str, name: str) -> None:
    st.session_state["logged_in"] = True
    st.session_state["username"] = name
    st.session_state["user_email"] = email
    st.session_state["login_time"] = time.time()
    st.session_state.pop("fail_count", None)
    st.session_state.pop("lock_until", None)


def logout() -> None:
    for key in ["logged_in", "username", "user_email", "login_time"]:
        st.session_state.pop(key, None)


def get_username() -> str:
    return st.session_state.get("username", "User")


def get_user_email() -> str:
    return st.session_state.get("user_email", "")


# ── Private records (server-side authorisation) ──────────────────────────────
def _require_owner() -> str:
    if not is_logged_in() or not get_user_email():
        raise PermissionError("Sign in to access your records.")
    return get_user_email()


def add_record(record: dict) -> dict:
    """Save a record to the signed-in user's private list."""
    owner = _require_owner()
    store = _read_json(_RECORDS_FILE)
    entry = dict(record)
    entry["id"] = uuid.uuid4().hex
    entry["created_at"] = time.time()
    store.setdefault(owner, []).append(entry)
    _write_json(_RECORDS_FILE, store)
    return entry


def get_user_records() -> list:
    """Return only the signed-in user's records, newest first."""
    owner = _require_owner()
    records = _read_json(_RECORDS_FILE).get(owner, [])
    return sorted(records, key=lambda r: r.get("created_at", 0), reverse=True)


def delete_record(record_id: str) -> bool:
    """Delete a record, but only if it belongs to the signed-in user."""
    owner = _require_owner()
    store = _read_json(_RECORDS_FILE)
    mine = store.get(owner, [])
    kept = [r for r in mine if r.get("id") != record_id]
    if len(kept) == len(mine):
        return False
    store[owner] = kept
    _write_json(_RECORDS_FILE, store)
    return True


# ── Route guard ───────────────────────────────────────────────────────────────
def require_login() -> bool:
    """Return True for signed-in users; otherwise render the public pages."""
    if is_logged_in():
        return True
    view = st.query_params.get("auth", "")
    if view == "signin":
        _signin_page()
    elif view == "signup":
        _signup_page()
    else:
        _landing_page()
    return False


def _flat(html: str) -> str:
    """Collapse multi-line HTML so Markdown never treats it as a code block."""
    return " ".join(line.strip() for line in html.splitlines() if line.strip())


# ── Shared page chrome ────────────────────────────────────────────────────────
_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
html { scroll-behavior: smooth; }
[data-testid="stAppViewContainer"] { background: #F5F7FA !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"], [data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"], footer { display: none !important; }
a:focus-visible, button:focus-visible { outline: 3px solid #12B5A6 !important; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; scroll-behavior: auto !important; } }
"""

_LANDING_CSS = _BASE_CSS + """
.main .block-container, [data-testid="stMainBlockContainer"] { max-width: 1180px !important; padding: 20px 24px 40px !important; }
.sq, .sq * { font-family: Inter, system-ui, sans-serif; box-sizing: border-box; }
:where(.sq) h1, :where(.sq) h2, :where(.sq) h3 { font-family: Sora, Inter, sans-serif; color: #0D1B2A; margin: 0; letter-spacing: -0.02em; }
:where(.sq) p { margin: 0; }
.sq a { text-decoration: none; }

.sq-nav { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 6px 4px 22px; }
.sq-navlinks { display: flex; gap: 28px; }
.sq-navlinks a { color: #43536B; font-size: 15px; font-weight: 500; }
.sq-navlinks a:hover { color: #0D1B2A; }
.sq-navcta { display: flex; align-items: center; gap: 10px; }

.sq-btn { display: inline-flex; align-items: center; justify-content: center; height: 46px; padding: 0 22px; border-radius: 10px; font-size: 15px; font-weight: 600; transition: transform .15s ease, background .15s ease; white-space: nowrap; }
.sq-btn:hover { transform: translateY(-1px); }
.sq-btn-dark { background: #0D1B2A; color: #fff !important; }
.sq-btn-dark:hover { background: #17304D; }
.sq-btn-line { color: #0D1B2A !important; border: 1.5px solid #C6D0DE; background: #fff; }
.sq-btn-white { background: #fff; color: #0D1B2A !important; }
.sq-btn-white:hover { background: #E7EEF9; }
.sq-btn-ghost { color: #fff !important; border: 1.5px solid rgba(255,255,255,.4); }
.sq-btn-ghost:hover { background: rgba(255,255,255,.1); }
.sq-btn-sm { height: 40px; padding: 0 16px; font-size: 14px; }

.sq-hero { display: grid; grid-template-columns: 1.05fr .95fr; gap: 40px; align-items: center; padding: 56px 52px; border-radius: 28px; color: #fff;
  background: radial-gradient(900px 420px at 85% 0%, rgba(18,181,166,.28), transparent 60%), linear-gradient(135deg, #0D1B2A 0%, #11294A 62%, #0F3B5F 100%); }
.sq-hero h1 { color: #fff; font-size: clamp(34px, 4.6vw, 56px); line-height: 1.06; font-weight: 700; }
.sq-lede { color: #B9C7DB; font-size: 18px; line-height: 1.6; margin-top: 20px; max-width: 520px; }
.sq-cta { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 30px; }
.sq-hero-note { color: #8FA3BF; font-size: 14px; margin-top: 18px; }
.sq-hero-visual { background: #fff; border-radius: 22px; box-shadow: 0 30px 60px rgba(3,10,22,.45); padding: 4px; }
.sq-hero-visual svg { display: block; width: 100%; height: auto; }
@keyframes sqpin { from { transform: translateX(-150px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
.sq-pin { animation: sqpin 1.1s cubic-bezier(.16,1,.3,1) .35s both; }

.sq-stats { display: grid; grid-template-columns: repeat(4, 1fr); margin: 28px 0 8px; background: #fff; border-radius: 18px; border: 1px solid #E3E9F1; }
.sq-stat { padding: 22px 26px; border-right: 1px solid #E3E9F1; }
.sq-stat:last-child { border-right: 0; }
.sq-stat b { display: block; font-family: Sora, Inter, sans-serif; font-size: 28px; color: #0D1B2A; letter-spacing: -0.02em; }
.sq-stat span { color: #5B6B82; font-size: 14px; }

.sq-section { padding: 76px 4px 0; }
.sq-section h2 { font-size: clamp(26px, 3.2vw, 38px); line-height: 1.15; max-width: 640px; }
.sq-sub { color: #5B6B82; font-size: 17px; line-height: 1.6; margin-top: 14px; max-width: 560px; }

.sq-feat { display: grid; grid-template-columns: .8fr 1.2fr; gap: 56px; }
.sq-rows { border-top: 1px solid #DCE4EE; }
.sq-row { display: grid; grid-template-columns: 48px 1fr; gap: 18px; padding: 22px 0; border-bottom: 1px solid #DCE4EE; }
.sq-ico { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: #E3F6F3; }
.sq-row h3 { font-size: 18px; margin-bottom: 6px; }
.sq-row p { color: #5B6B82; font-size: 15px; line-height: 1.6; }

.sq-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; margin-top: 36px; position: relative; }
.sq-steps::before { content: ""; position: absolute; left: 22px; right: 22px; top: 21px; height: 2px; background: linear-gradient(90deg, #2563EB, #12B5A6); opacity: .35; }
.sq-step { position: relative; }
.sq-num { width: 44px; height: 44px; border-radius: 50%; background: #0D1B2A; color: #fff; display: flex; align-items: center; justify-content: center; font-family: Sora, sans-serif; font-weight: 600; position: relative; z-index: 1; }
.sq-step h3 { font-size: 19px; margin: 18px 0 8px; }
.sq-step p { color: #5B6B82; font-size: 15px; line-height: 1.6; max-width: 300px; }

.sq-panel { margin-top: 34px; background: #fff; border: 1px solid #E3E9F1; border-radius: 22px; padding: 30px 30px 18px; }
.sq-insights { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 34px; }
.sq-insights h3 { font-size: 16px; }
.sq-insights p { color: #5B6B82; font-size: 13.5px; margin: 4px 0 10px; }
.sq-insights svg { width: 100%; height: auto; display: block; }
.sq-cap { color: #7A8AA0; font-size: 13px; margin-top: 14px; }

.sq-band { margin-top: 76px; padding: 52px; border-radius: 26px; background: linear-gradient(120deg, #0D1B2A, #123A5C); color: #fff; display: flex; align-items: center; justify-content: space-between; gap: 28px; flex-wrap: wrap; }
.sq-band h2 { color: #fff; font-size: clamp(24px, 3vw, 34px); max-width: 520px; }
.sq-band p { color: #B9C7DB; margin-top: 10px; font-size: 16px; }

.sq-footer { margin-top: 56px; padding: 30px 4px 0; border-top: 1px solid #DCE4EE; display: flex; flex-wrap: wrap; gap: 20px 40px; align-items: center; justify-content: space-between; }
.sq-footer nav { display: flex; gap: 24px; flex-wrap: wrap; }
.sq-footer nav a { color: #43536B; font-size: 14px; }
.sq-footer small { color: #7A8AA0; font-size: 13px; }

@media (max-width: 960px) {
  .sq-hero { grid-template-columns: 1fr; padding: 36px 26px; }
  .sq-feat, .sq-insights { grid-template-columns: 1fr; gap: 28px; }
  .sq-steps { grid-template-columns: 1fr; }
  .sq-steps::before { display: none; }
  .sq-stats { grid-template-columns: 1fr 1fr; }
  .sq-stat:nth-child(2) { border-right: 0; }
  .sq-stat:nth-child(-n+2) { border-bottom: 1px solid #E3E9F1; }
  .sq-navlinks { display: none; }
  .sq-band { padding: 34px 26px; }
}
@media (max-width: 520px) {
  .sq-cta .sq-btn { width: 100%; }
  .sq-nav .sq-btn-line { display: none; }
}
"""

_FORM_CSS = _BASE_CSS + """
.main .block-container, [data-testid="stMainBlockContainer"] { max-width: 480px !important; padding: 36px 20px 40px !important; }
.sqf, .sqf * { font-family: Inter, system-ui, sans-serif; }
.sqf { text-align: center; margin-bottom: 22px; }
.sqf h1 { font-family: Sora, Inter, sans-serif; font-size: 28px; color: #0D1B2A; margin: 22px 0 6px; letter-spacing: -0.02em; }
.sqf p { color: #5B6B82; font-size: 15px; margin: 0; }
div[data-testid="stForm"] { background: #fff !important; border: 1px solid #E3E9F1 !important; border-radius: 18px !important; padding: 26px 24px 20px !important; box-shadow: 0 18px 40px rgba(13,27,42,.07); }
.stTextInput label { font-size: 14px !important; font-weight: 600 !important; color: #0D1B2A !important; }
.stTextInput input { border-radius: 10px !important; border: 1.5px solid #C6D0DE !important; padding: 12px 14px !important; font-size: 16px !important; background: #fff !important; color: #0D1B2A !important; }
.stTextInput input:focus { border-color: #2563EB !important; box-shadow: 0 0 0 3px rgba(37,99,235,.18) !important; }
.stFormSubmitButton button, .stButton button { width: 100% !important; height: 48px !important; border-radius: 10px !important; border: 0 !important; background: #0D1B2A !important; color: #fff !important; font-weight: 600 !important; font-size: 16px !important; }
.stFormSubmitButton button:hover, .stButton button:hover { background: #17304D !important; }
.sqf-alt { text-align: center; color: #5B6B82; font-size: 15px; margin-top: 20px; font-family: Inter, sans-serif; }
.sqf-alt a { color: #2563EB; font-weight: 600; text-decoration: none; }
.sqf-alt a:hover { text-decoration: underline; }
"""


# ── Illustrations (inline SVG) ────────────────────────────────────────────────
def _hero_card() -> str:
    heights = [6, 10, 16, 26, 40, 56, 72, 86, 96, 92, 80, 64, 50, 38, 28, 20, 14, 10, 7, 5]
    bars = "".join(
        f'<rect x="{28 + i * 20.2:.1f}" y="{232 - h}" width="14" height="{h}" rx="3" fill="url(#sqBars)"/>'
        for i, h in enumerate(heights)
    )
    ticks = [(28, "10th", "start"), (110, "25th", "middle"), (230, "Median", "middle"),
             (340, "75th", "middle"), (432, "90th", "end")]
    tick_svg = "".join(
        f'<line x1="{x}" y1="258" x2="{x}" y2="276" stroke="#0D1B2A" stroke-opacity=".3"/>'
        f'<text x="{x}" y="252" text-anchor="{a}" font-size="11.5" fill="#6B7A90" font-family="Inter,sans-serif">{t}</text>'
        for x, t, a in ticks
    )
    return _flat(f"""
    <svg viewBox="0 0 460 360" role="img" aria-label="Salary check showing a predicted salary of 14.2 LPA, the 74th percentile, and the offer placed on a market percentile ruler">
      <defs>
        <linearGradient id="sqTrack" x1="0" x2="1"><stop offset="0" stop-color="#2563EB"/><stop offset=".55" stop-color="#12B5A6"/><stop offset="1" stop-color="#7BE0B8"/></linearGradient>
        <linearGradient id="sqBars" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6E97FF"/><stop offset="1" stop-color="#2563EB" stop-opacity=".3"/></linearGradient>
      </defs>
      <rect x="1" y="1" width="458" height="358" rx="22" fill="#FFFFFF"/>
      <text x="28" y="44" font-size="13.5" fill="#6B7A90" font-family="Inter,sans-serif">Data Analyst in Bengaluru</text>
      <text x="28" y="88" font-size="38" font-weight="700" fill="#0D1B2A" font-family="Sora,Inter,sans-serif">&#8377;14.2 LPA</text>
      <text x="28" y="110" font-size="13" fill="#6B7A90" font-family="Inter,sans-serif">Predicted market salary, range &#8377;12.1 to &#8377;16.4</text>
      <rect x="312" y="26" width="122" height="34" rx="17" fill="#E3F6F3"/>
      <text x="373" y="48" text-anchor="middle" font-size="13" font-weight="600" fill="#0B7F73" font-family="Inter,sans-serif">74th percentile</text>
      <line x1="28" y1="232" x2="432" y2="232" stroke="#E3E9F1"/>
      {bars}
      <line x1="230" y1="130" x2="230" y2="240" stroke="#9FB0C8" stroke-dasharray="4 4"/>
      <rect x="28" y="262" width="404" height="10" rx="5" fill="url(#sqTrack)"/>
      {tick_svg}
      <g class="sq-pin">
        <line x1="335" y1="272" x2="335" y2="318" stroke="#0D1B2A" stroke-width="2"/>
        <circle cx="335" cy="267" r="11" fill="#0D1B2A" stroke="#fff" stroke-width="3"/>
        <rect x="271" y="316" width="128" height="30" rx="15" fill="#0D1B2A"/>
        <text x="335" y="336" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff" font-family="Inter,sans-serif">Your offer &#8377;15.0</text>
      </g>
    </svg>""")


def _icon(path: str) -> str:
    return (f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0B7F73" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>')


_ICONS = {
    "predict": '<path d="M3 17l5-5 4 4 8-9"/><path d="M15 7h5v5"/>',
    "coach": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 17l.7 1.8L21.5 19.5l-1.8.7L19 22l-.7-1.8-1.8-.7 1.8-.7z"/>',
    "market": '<path d="M5 20V10M12 20V4M19 20v-7"/>',
    "skills": '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    "text": '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
}


def _insight_charts() -> tuple:
    labels = ["Intern", "Entry", "Assoc.", "Mid", "Dir.", "Exec."]
    heights = [28, 46, 66, 92, 118, 140]
    colors = ["#BFD1FF", "#9DB8FF", "#7A9FFF", "#5585F5", "#3A6DEB", "#2563EB"]
    a = "".join(
        f'<rect x="{14 + i * 40}" y="{148 - h}" width="28" height="{h}" rx="5" fill="{colors[i]}"/>'
        f'<text x="{28 + i * 40}" y="164" text-anchor="middle" font-size="10" fill="#6B7A90" font-family="Inter,sans-serif">{labels[i]}</text>'
        for i, h in enumerate(heights)
    )
    chart_a = f'<svg viewBox="0 0 260 172" role="img" aria-label="Bar chart of salary rising with experience level">{a}</svg>'

    cities = ["Bengaluru", "Hyderabad", "Pune", "Mumbai", "Chennai"]
    lens = [150, 130, 112, 98, 78]
    b = "".join(
        f'<text x="0" y="{34 + i * 28}" font-size="11.5" fill="#43536B" font-family="Inter,sans-serif">{c}</text>'
        f'<line x1="84" y1="{30 + i * 28}" x2="{84 + lens[i]}" y2="{30 + i * 28}" stroke="#BFEDE7" stroke-width="5" stroke-linecap="round"/>'
        f'<circle cx="{84 + lens[i]}" cy="{30 + i * 28}" r="7" fill="#12B5A6"/>'
        for i, c in enumerate(cities)
    )
    chart_b = f'<svg viewBox="0 0 260 172" role="img" aria-label="Lollipop chart comparing salary by city">{b}</svg>'

    skills = ["Machine learning", "SQL", "Python", "Excel", "Tableau"]
    widths = [108, 92, 80, 60, 48]
    prem = ["+18%", "+12%", "+10%", "+5%", "+3%"]
    c = "".join(
        f'<text x="0" y="{29 + i * 29}" font-size="11.5" fill="#43536B" font-family="Inter,sans-serif">{s}</text>'
        f'<rect x="100" y="{17 + i * 29}" width="{widths[i]}" height="16" rx="8" fill="#2563EB" fill-opacity="{1 - i * 0.14:.2f}"/>'
        f'<text x="{108 + widths[i]}" y="{29 + i * 29}" font-size="11" font-weight="600" fill="#0D1B2A" font-family="Inter,sans-serif">{prem[i]}</text>'
        for i, s in enumerate(skills)
    )
    chart_c = f'<svg viewBox="0 0 260 172" role="img" aria-label="Bar chart of salary premium for top skills">{c}</svg>'
    return chart_a, chart_b, chart_c


# ── Landing page ──────────────────────────────────────────────────────────────
def _landing_page() -> None:
    chart_a, chart_b, chart_c = _insight_charts()
    features = [
        ("predict", "Salary prediction",
         "Three regression models are trained on real job postings. The most accurate one estimates your pay from role, experience, location and skills."),
        ("coach", "AI negotiation coach",
         "Gemini turns your numbers and the market percentiles into talking points and an opening script you can say out loud."),
        ("market", "Market analytics",
         "Explore pay by industry, city, company and experience level with interactive charts."),
        ("skills", "Skills impact",
         "See which skills carry a salary premium and which ones to learn next."),
        ("text", "Job description analyser",
         "Paste any posting to pull out the required skills and a likely salary band."),
        ("globe", "United States and India",
         "Switch markets in one click. Salaries show in USD or LPA, with local cities."),
        ("lock", "Private offer tracker",
         "Log the offers you receive in your own account and see how each one ranks against the market."),
    ]
    rows = "".join(
        f'<div class="sq-row"><div class="sq-ico">{_icon(_ICONS[k])}</div>'
        f'<div><h3>{t}</h3><p>{d}</p></div></div>'
        for k, t, d in features
    )

    html = f"""
    <div class="sq">
      <header class="sq-nav">
        <a href="/" target="_self" aria-label="SalaryIQ home">{lockup(36)}</a>
        <nav class="sq-navlinks" aria-label="Primary">
          <a href="#features">Features</a><a href="#how">How it works</a><a href="#analytics">Analytics</a>
        </nav>
        <div class="sq-navcta">
          <a class="sq-btn sq-btn-line sq-btn-sm" href="?auth=signin" target="_self">Sign in</a>
          <a class="sq-btn sq-btn-dark sq-btn-sm" href="?auth=signup" target="_self">Create account</a>
        </div>
      </header>

      <section class="sq-hero">
        <div>
          <h1>Find out what you should be paid. Then ask for it.</h1>
          <p class="sq-lede">SalaryIQ compares your role, skills and city with real job postings, predicts your market salary, and writes the negotiation plan for you.</p>
          <div class="sq-cta">
            <a class="sq-btn sq-btn-white" href="?auth=signup" target="_self">Create free account</a>
            <a class="sq-btn sq-btn-ghost" href="?auth=signin" target="_self">Sign in</a>
          </div>
          <p class="sq-hero-note">Free to use. No card needed.</p>
        </div>
        <div class="sq-hero-visual">{_hero_card()}</div>
      </section>

      <div class="sq-stats">
        <div class="sq-stat"><b>33,000+</b><span>job postings analysed</span></div>
        <div class="sq-stat"><b>2 markets</b><span>United States and India</span></div>
        <div class="sq-stat"><b>3 models</b><span>compared on every run</span></div>
        <div class="sq-stat"><b>11 tools</b><span>dashboards, predictor and coach</span></div>
      </div>

      <section class="sq-section" id="features">
        <div class="sq-feat">
          <div>
            <h2>Everything you need before the salary conversation</h2>
            <p class="sq-sub">Know the number, know why it is fair, and know what to say. SalaryIQ keeps all three in one place.</p>
          </div>
          <div class="sq-rows">{rows}</div>
        </div>
      </section>

      <section class="sq-section" id="how">
        <h2>From profile to plan in three steps</h2>
        <div class="sq-steps">
          <div class="sq-step"><div class="sq-num">1</div><h3>Create your account</h3><p>Sign up with your email. Your offers and reports stay private to you.</p></div>
          <div class="sq-step"><div class="sq-num">2</div><h3>Describe your role</h3><p>Pick your job title, experience, city and skills, or paste a job description.</p></div>
          <div class="sq-step"><div class="sq-num">3</div><h3>Get your numbers and script</h3><p>See your predicted salary and percentile, then generate a negotiation plan.</p></div>
        </div>
      </section>

      <section class="sq-section" id="analytics">
        <h2>See the market, not just a number</h2>
        <p class="sq-sub">Every page has interactive charts you can filter and explore.</p>
        <div class="sq-panel">
          <div class="sq-insights">
            <div><h3>Pay by experience</h3><p>How salary climbs with seniority</p>{chart_a}</div>
            <div><h3>Pay by city</h3><p>Where the same role pays more</p>{chart_b}</div>
            <div><h3>Skill premium</h3><p>What each skill adds to the median</p>{chart_c}</div>
          </div>
          <p class="sq-cap">Sample visuals. Inside the app, charts use the market you select.</p>
        </div>
      </section>

      <section class="sq-band">
        <div><h2>Check your next offer before you answer it.</h2><p>It takes about a minute to create an account.</p></div>
        <a class="sq-btn sq-btn-white" href="?auth=signup" target="_self">Create free account</a>
      </section>

      <footer class="sq-footer">
        <a href="/" target="_self">{lockup(30)}</a>
        <nav aria-label="Footer"><a href="#features">Features</a><a href="#how">How it works</a><a href="?auth=signin" target="_self">Sign in</a><a href="?auth=signup" target="_self">Create account</a></nav>
        <small>Built with Python, Streamlit, scikit-learn and Google Gemini. &copy; 2026 SalaryIQ</small>
      </footer>
    </div>"""
    st.markdown(f"<style>{_LANDING_CSS}</style>" + _flat(html), unsafe_allow_html=True)


# ── Sign in / sign up ─────────────────────────────────────────────────────────
def _form_header(title: str, subtitle: str) -> None:
    st.markdown(f"<style>{_FORM_CSS}</style>", unsafe_allow_html=True)
    st.markdown(_flat(f"""
    <div class="sqf">
      <a href="/" target="_self" aria-label="Back to SalaryIQ home">{lockup(40)}</a>
      <h1>{title}</h1><p>{subtitle}</p>
    </div>"""), unsafe_allow_html=True)


def _signin_page() -> None:
    _form_header("Welcome back", "Sign in to see your market position.")
    now = time.time()
    locked = st.session_state.get("lock_until", 0) > now

    with st.form("signin_form"):
        email = st.text_input("Email address", placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="Your password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if locked:
            wait = int(st.session_state["lock_until"] - now)
            st.error(f"Too many failed attempts. Try again in {wait} seconds.")
        elif not email.strip() or not password:
            st.error("Enter your email and password.")
        else:
            ok, name = check_credentials(email, password)
            if ok:
                login(email.strip().lower(), name)
                st.query_params.clear()
                st.rerun()
            else:
                fails = st.session_state.get("fail_count", 0) + 1
                st.session_state["fail_count"] = fails
                if fails >= _MAX_FAILS:
                    st.session_state["lock_until"] = now + _LOCK_SECONDS
                    st.session_state["fail_count"] = 0
                    st.error(f"Too many failed attempts. Try again in {_LOCK_SECONDS} seconds.")
                else:
                    st.error("That email and password do not match an account. "
                             "Check your details or create an account.")

    st.markdown('<p class="sqf-alt">New to SalaryIQ? <a href="?auth=signup" target="_self">Create an account</a></p>',
                unsafe_allow_html=True)


def _signup_page() -> None:
    _form_header("Create your account", "Free to use. Your offers stay private to you.")
    with st.form("signup_form"):
        name = st.text_input("Full name", placeholder="Your name")
        email = st.text_input("Email address", placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="8+ characters, with a letter and a number")
        confirm = st.text_input("Confirm password", type="password", placeholder="Type the password again")
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if submitted:
        ok, errors = register_user(name, email, password, confirm)
        if ok:
            login(email.strip().lower(), name.strip())
            st.query_params.clear()
            st.rerun()
        else:
            for message in errors:
                st.error(message)

    st.markdown('<p class="sqf-alt">Already have an account? <a href="?auth=signin" target="_self">Sign in</a></p>',
                unsafe_allow_html=True)
