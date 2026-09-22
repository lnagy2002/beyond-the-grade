"""
Beyond the Grade — Streamlit app.

A Python/Streamlit front end over engine.py, deployable on Streamlit Community
Cloud. This is a separate build from the Node version (../server.js + ../public),
which is left intact.

Run locally:   streamlit run streamlit/app.py
"""

import base64
from datetime import date
from pathlib import Path

import streamlit as st
import engine

st.set_page_config(page_title="Beyond the Grade", page_icon="📘", layout="centered")


@st.cache_data
def _img_data_uri(name, mtime):
    """Base64 data URI for an asset image so it embeds without static hosting.

    `mtime` is part of the cache key so swapping the file on disk refreshes it
    (a name starting with '_' would be skipped by st.cache_data's hasher).
    """
    path = Path(__file__).parent / "assets" / name
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/webp;base64,{data}"


def _asset_uri(name):
    path = Path(__file__).parent / "assets" / name
    return _img_data_uri(name, path.stat().st_mtime)


def hero_data_uri():
    """Landing hero photo."""
    return _asset_uri("hero.webp")


def report_data_uri():
    """Report snapshot photo."""
    return _asset_uri("report.webp")

# Light brand styling.
st.markdown(
    """
    <style>
      .stApp { background: #cdd5e8; }
      .badge { display:inline-block; padding:4px 12px; border-radius:999px; font-size:.8rem; font-weight:700; }
      .b-proc { background:#f3e6c4; color:#8a6a1e; }
      .b-cog  { background:#f2d9d2; color:#a5493a; }
      .b-on   { background:#e2efdd; color:#547a45; }
      .b-slightly { background:#f6ecd2; color:#a07d24; }
      .b-below { background:#f6e2dd; color:#b45f4f; }
      .b-ahead { background:#e0e9f2; color:#4f759c; }
      .chip { display:inline-block; background:#cdd5e8; color:#2f3729; padding:4px 12px; border-radius:999px; font-size:.8rem; font-weight:600; }
      .qwhy { color:#2f3729; font-style:italic; }
    </style>
    """,
    unsafe_allow_html=True,
)

ss = st.session_state
ss.setdefault("phase", "landing")
ss.setdefault("state", None)
ss.setdefault("current_q", None)
ss.setdefault("child", None)

# CTA / nav links navigate via a query param.
_go = st.query_params.get("go")
if _go == "intake":
    ss.phase = "intake"
    st.query_params.clear()
elif _go == "home":
    ss.phase = "landing"
    st.query_params.clear()

def build_stepper(active):
    """Progress stepper HTML; `active` is 1 (About You), 2 (Assessment), 3 (Results)."""
    labels = ["1. About You", "2. Assessment", "3. Results"]
    out = ['<div class="stepper">']
    for i, label in enumerate(labels, start=1):
        active_cls = " active" if i == active else ""
        dot_style = ' style="background:#2f3729"' if i <= active else ""
        out.append(f'<span class="step{active_cls}"><span class="dot"{dot_style}></span>{label}</span>')
        if i < 3:
            out.append(f'<span class="{"stepline done" if i < active else "stepline"}"></span>')
    out.append("</div>")
    return "".join(out)


# Shared top nav (used by the landing and intake pages).
NAV_HTML = (
    '<div class="nav">'
    '<a class="brand" href="?go=home" target="_self">Beyond the Grade</a>'
    '<div class="nav-links">'
    '<a href="#how">How It Works</a>'
    '<a href="#signs">Sample Report</a>'
    '<a href="#signs">FAQs</a>'
    '<a href="#signs">Resources</a>'
    '<a href="?go=intake" target="_self">Sign In</a>'
    '<a class="nav-cta" href="?go=intake" target="_self">Get Started</a>'
    "</div></div>"
)


def start(name, grade, age):
    state = engine.create_assessment(grade)
    ss.state = state
    ss.child = {"name": name, "grade": grade, "age": age}
    ss.current_q = engine.choose_next_question(state)
    ss.phase = "assessment"


def submit_answer(response):
    engine.answer_question(ss.state, ss.current_q, response)
    if engine.should_stop(ss.state):
        ss.current_q = None
        ss.phase = "done"
    else:
        nxt = engine.choose_next_question(ss.state)
        ss.current_q = nxt
        if nxt is None:
            ss.phase = "done"


def reset():
    ss.phase = "landing"
    ss.state = None
    ss.current_q = None
    ss.child = None


LANDING_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;600;700&display=swap');
html, body { overflow-x: hidden; }
header[data-testid="stHeader"] { display: none; }
.block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
  max-width: 1280px !important; padding-top: 0 !important; padding-bottom: 0 !important; }
/* Collapse the vertical gap around empty style-injection blocks above the nav */
[data-testid="stVerticalBlock"] { gap: 0 !important; }
/* Top nav */
.nav { background: #cdd5e8; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #2f3729 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #4f574f !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #2f3729 !important; }
.nav-links a.nav-cta { background: #2f3729; color: #fff !important; text-decoration: none !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
.nav-links a.nav-cta:hover { color: #fff !important; }
@media (max-width: 760px) { .nav-links a:not(.nav-cta) { display: none; } }
.bg-hero {
  border-radius: 0; overflow: hidden; background-size: cover; background-position: 62% center;
  min-height: 92vh; display: flex; align-items: center;
  width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%);
}
.hero-inner { width: 100%; padding-left: max(2rem, calc((100vw - 1280px) / 2 + 2rem)); padding-right: 2rem; }
.hero-text { max-width: 620px; padding: 56px 0; }
.hero-inner .eyebrow { text-transform: uppercase; letter-spacing: .16em; font-size: .78rem;
  font-weight: 700; color: #2f3729; margin: 0 0 18px; }
.hero-inner h1 { font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: #141414;
  font-size: clamp(2.6rem, 5.2vw, 4.25rem) !important; line-height: 1.02; margin: 0 0 26px; }
.hero-inner .lede { color: #4f574f; font-size: 1.14rem; max-width: 44ch; margin: 0 0 30px; }
.hero-inner .meta { color: #7c817b; font-size: .95rem; margin: 18px 0 0; }
a.cta { display: inline-block; background: #2f3729; color: #fff !important; padding: 14px 24px;
  border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 1rem; }
a.cta:hover { background: #232a1f; }
.section-eyebrow { text-transform: uppercase; letter-spacing: .16em; font-size: .78rem;
  font-weight: 700; color: #2f3729; text-align: center; margin: 0 0 22px; }
/* Features — white full-width band, icons to the left of the text */
.feat-band { background: #fff; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 46px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; }
.feat { display: flex; align-items: flex-start; gap: 14px; text-align: left; }
.fic { color: #2f3729; flex: 0 0 auto; display: inline-flex; margin-top: 1px; }
.ft-title { font-family: 'Inter', sans-serif; font-size: 1.08rem !important; font-weight: 700;
  color: #2f3729; margin: 0 0 5px !important; line-height: 1.3; }
.ft-sub { color: #4f574f; font-size: .98rem !important; margin: 0 !important; line-height: 1.45; }
/* How it works — full-width cream band */
.hw-band { background: #e3e9f5; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 72px max(2rem, calc((100vw - 1280px) / 2 + 2rem)) 90px; text-align: center; }
.hw-title { font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: #141414;
  font-size: clamp(2.2rem, 5vw, 3.4rem) !important; line-height: 1.08; text-align: center !important; margin: 0 0 16px; }
.hw-sub { display: inline-block !important; color: #4f574f; text-align: center !important;
  max-width: 62ch; font-size: 1.12rem !important; margin: 0 auto; }
/* Signals — white full-width band */
.sig-band { background: #fff; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 72px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.sig-title { font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: #141414;
  font-size: clamp(2.1rem, 4.6vw, 3.3rem) !important; line-height: 1.1; margin: 0 0 8px; }
.sig-title em { color: #2f3729; font-style: italic; }
.sig-sub { color: #4f574f; font-size: 1.1rem !important; margin: 0 0 26px; }
.sig-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.sig-card { background: #fff; border: 1px solid #c7cee1; border-radius: 16px; padding: 26px; }
.sig-num { display: inline-grid; place-items: center; width: 42px; height: 42px; border-radius: 50%;
  background: #2f3729; color: #fff; font-weight: 700; font-size: 1.05rem; margin-bottom: 20px; }
.sig-card h4 { font-family: 'Inter', sans-serif; font-size: 1.18rem; color: #2f3729; margin: 0 0 12px; line-height: 1.25; }
.sig-card p { color: #4f574f; font-size: .98rem; margin: 0; line-height: 1.55; }
.foot { background: #2f3729; border-radius: 0; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 64px max(2rem, calc((100vw - 1280px) / 2 + 2rem)) 72px;
  display: grid; grid-template-columns: 1.1fr 1fr; gap: 60px; }
.foot .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.5rem; color: #eef1e9; margin: 0 0 14px; }
.foot p { color: #dbe0d3; margin: 0; font-size: 1.02rem; }
.foot .note-title { font-weight: 700; margin: 0 0 8px; }
.foot .note { color: #aab0a2; }
@media (max-width: 640px) {
  .feat-grid, .sig-grid, .foot { grid-template-columns: 1fr; }
  .hero-inner h1 { font-size: 2.1rem; }
}
</style>
"""


INTAKE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;600;700&display=swap');
header[data-testid="stHeader"] { display: none; }
.block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
  max-width: 1280px !important; padding-top: 0 !important; padding-bottom: 3rem !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
html, body { overflow-x: hidden; }
.stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp div { font-family: 'Inter', system-ui, sans-serif; }
/* Top nav */
.nav { background: #cdd5e8; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #2f3729 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #4f574f !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #2f3729 !important; }
.nav-links a.nav-cta { background: #2f3729; color: #fff !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
/* Stepper */
.stepper { display: flex; align-items: center; gap: 12px; margin: 40px 0 34px; }
.step { display: flex; align-items: center; gap: 8px; font-size: .92rem; color: #7c817b; white-space: nowrap; }
.step.active { color: #2f3729; font-weight: 600; }
.step .dot { width: 12px; height: 12px; border-radius: 50%; background: #b3bcd6; }
.step.active .dot { background: #2f3729; }
.stepline { flex: 1; height: 3px; background: #bcc4dc; border-radius: 3px; min-width: 24px; }
/* Heading */
h1.intake-h1 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #141414;
  font-size: clamp(2.2rem, 4.4vw, 3.1rem) !important; line-height: 1.05; margin: 0 0 12px; padding: 0; }
.intake-sub { color: #4f574f; font-size: 1.06rem; margin: 0 0 30px; }
/* Form fields */
.stTextInput, .stSelectbox, .stNumberInput { margin-bottom: 22px !important; }
[data-testid="stWidgetLabel"] p { font-weight: 600 !important; color: #2f3729 !important; font-size: .95rem !important; }
/* Uniform 52px control boxes: border/height on the BaseWeb container for all three */
.stTextInput div[data-baseweb="input"],
.stNumberInput div[data-baseweb="input"],
.stSelectbox div[data-baseweb="select"] > div {
  background: #fff !important; border: 1px solid #c7cee1 !important; border-radius: 12px !important;
  height: 52px !important; min-height: 52px !important; box-sizing: border-box !important; align-items: center !important; }
.stTextInput input, .stNumberInput input {
  background: transparent !important; border: none !important; height: 50px !important;
  padding: 0 16px !important; font-size: 1rem !important; color: #2f3729 !important; }
.stNumberInput button { display: none !important; }
.stSelectbox div[data-baseweb="select"] > div > div { padding-left: 6px !important; }
/* Next button */
.stFormSubmitButton button {
  background: #2f3729 !important; color: #fff !important; border: none !important; border-radius: 12px !important;
  width: 100% !important; padding: 14px 0 !important; font-weight: 600 !important; margin-top: 4px; }
.stFormSubmitButton button:hover { background: #232a1f !important; }
.stFormSubmitButton button p { font-size: 1.02rem !important; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; }
</style>
"""


ASSESSMENT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;600;700&display=swap');
header[data-testid="stHeader"] { display: none; }
.block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
  max-width: 1280px !important; padding-top: 0 !important; padding-bottom: 3rem !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
html, body { overflow-x: hidden; }
.stApp, .stApp p, .stApp label, .stApp input, .stApp button, .stApp div { font-family: 'Inter', system-ui, sans-serif; }
/* Top nav */
.nav { background: #cdd5e8; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #2f3729 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #4f574f !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #2f3729 !important; }
.nav-links a.nav-cta { background: #2f3729; color: #fff !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
/* Stepper */
.stepper { display: flex; align-items: center; gap: 12px; margin: 40px 0 34px; }
.step { display: flex; align-items: center; gap: 8px; font-size: .92rem; color: #7c817b; white-space: nowrap; }
.step.active { color: #2f3729; font-weight: 600; }
.step .dot { width: 12px; height: 12px; border-radius: 50%; background: #b3bcd6; }
.stepline { flex: 1; height: 3px; background: #bcc4dc; border-radius: 3px; min-width: 24px; }
.stepline.done { background: #2f3729; }
/* Question head */
.qhead { display: flex; align-items: center; justify-content: space-between; margin: 4px 0 18px; }
.qchip { background: #fff; color: #2f3729; font-weight: 600; font-size: .9rem; padding: 8px 18px; border-radius: 999px; }
.qnum { color: #7c817b; font-size: 1rem; }
.qprompt { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #141414;
  font-size: clamp(1.8rem, 3.2vw, 2.4rem) !important; line-height: 1.15; margin: 0 0 24px; }
/* Choices as cards */
.stRadio [role="radiogroup"] { display: flex; flex-direction: column; gap: 12px; }
.stRadio [role="radiogroup"] > label {
  background: #fff !important; border: 1px solid #c7cee1 !important; border-radius: 14px !important;
  padding: 16px 20px !important; margin: 0 !important; width: 100% !important; min-height: 58px !important;
  display: flex !important; align-items: center !important; cursor: pointer; }
.stRadio [role="radiogroup"] > label:hover { border-color: #9aa6cc !important; }
.stRadio [role="radiogroup"] > label:has(input:checked) { border-color: #9aa6cc !important; background: #e9edf9 !important; }
.stRadio [role="radiogroup"] > label > div:last-child { font-size: 1.08rem !important; color: #2f3729 !important; }
/* Short-answer input — same 52px box as intake inputs */
.stTextInput div[data-baseweb="input"] {
  background: #fff !important; border: 1px solid #c7cee1 !important; border-radius: 12px !important;
  height: 52px !important; min-height: 52px !important; box-sizing: border-box !important; align-items: center !important; }
.stTextInput input { background: transparent !important; border: none !important; height: 50px !important;
  padding: 0 16px !important; font-size: 1rem !important; color: #2f3729 !important; }
/* Progress bar — custom HTML (warm gray track, ink fill) */
.qprog { height: 8px; background: #b3bcd6; border-radius: 6px; width: 100%; overflow: hidden; }
.qprog-fill { height: 100%; background: #2f3729; border-radius: 6px; }
/* Vertically center the progress bar with the Next button */
[data-testid="stHorizontalBlock"] { align-items: center !important; }
.stButton button { background: #2f3729 !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; padding: 12px 26px !important; font-weight: 600 !important; }
.stButton button:disabled { background: #b7bcc2 !important; color: #fff !important; }
</style>
"""


DONE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;600;700&family=Caveat:wght@600&display=swap');
header[data-testid="stHeader"] { display: none; }
.block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
  max-width: 1280px !important; padding-top: 0 !important; padding-bottom: 3rem !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
html, body { overflow-x: hidden; }
.stApp, .stApp p, .stApp label, .stApp div { font-family: 'Inter', system-ui, sans-serif; }
/* Top nav */
.nav { background: #cdd5e8; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #2f3729 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #4f574f !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #2f3729 !important; }
.nav-links a.nav-cta { background: #2f3729; color: #fff !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
/* Done page */
.done-wrap { text-align: center; margin-top: 64px; }
.check-badge { width: 96px; height: 96px; border-radius: 50%; background: #e3e9f5; border: 1px solid #c7cee1;
  display: flex; align-items: center; justify-content: center; font-size: 2.6rem; color: #2f3729; margin: 0 auto 30px; }
h1.done-h1 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #141414;
  font-size: clamp(2.6rem, 5vw, 3.6rem) !important; margin: 0 0 16px; }
.done-sub { color: #4f574f; font-size: 1.15rem; margin: 0 0 32px; text-align: center; }
.done-note { font-family: 'Caveat', cursive; font-size: 1.6rem; color: #2f3729; text-align: center;
  transform: rotate(-3deg); margin-top: 40px; }
.stButton { display: flex; justify-content: center; }
.stButton button { background: #2f3729 !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; padding: 14px 30px !important; font-weight: 600 !important; font-size: 1.05rem !important; }
.stButton button:hover { background: #232a1f !important; }
</style>
"""


RESULTS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,600&family=Inter:wght@400;600;700&display=swap');
header[data-testid="stHeader"] { display: none; }
.block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
  max-width: 1280px !important; padding-top: 0 !important; padding-bottom: 3rem !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
html, body { overflow-x: hidden; }
.stApp, .stApp p, .stApp label, .stApp div { font-family: 'Inter', system-ui, sans-serif; }
/* Top nav */
.nav { background: #cdd5e8; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #2f3729 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #4f574f !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #2f3729 !important; }
.nav-links a.nav-cta { background: #2f3729; color: #fff !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
@media (max-width: 760px) { .nav-links a:not(.nav-cta) { display: none; } }
/* Editorial report — full-bleed hero like the landing page.
   Shares the nav gutter so the menu and content line up. */
.rpt-hero { width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%);
  min-height: 600px; display: flex; align-items: center;
  background-repeat: no-repeat; background-size: cover; background-position: right center; }
.rpt-hero-inner { width: 100%;
  padding: 80px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.rpt-left { max-width: 560px; }
.rpt-eyebrow { text-transform: uppercase; letter-spacing: .2em; font-size: .82rem; font-weight: 700;
  color: #7c817b; margin: 0 0 22px !important; }
.rpt-title { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #141414 !important;
  font-size: clamp(2.6rem, 4.6vw, 4rem) !important; line-height: 1.02; margin: 0 0 22px !important; padding: 0; }
.rpt-meta { color: #7c817b; font-size: 1rem; margin: 0 0 34px !important; }
.rpt-oh { color: #2f3729; font-weight: 600; font-size: 1.02rem; margin: 0 0 8px !important; }
.rpt-band { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #141414;
  font-size: clamp(2.1rem, 3.6vw, 3rem) !important; line-height: 1.05; margin: 0 0 26px !important; }
.rpt-prog { height: 12px; background: #bcc4dc; border-radius: 8px; width: 100%; max-width: 680px; overflow: hidden; }
.rpt-prog-fill { height: 100%; background: #2f3729; border-radius: 8px; }
.rpt-summary { color: #4f574f; font-size: 1.12rem; line-height: 1.5; margin: 22px 0 30px !important; max-width: 46ch; }
.rpt-pdf { display: inline-flex; align-items: center; gap: 10px; border: 1px solid #9aa6cc; border-radius: 12px;
  padding: 12px 22px; color: #2f3729 !important; text-decoration: none !important; font-weight: 600; font-size: .95rem;
  background: transparent; }
.rpt-pdf:hover { background: rgba(255,255,255,.4); }
.rpt-pdf svg { width: 18px; height: 18px; }
/* Lower band — stats + closing line, aligned to the same nav gutter */
.rpt-lower { width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%);
  padding: 4px max(2rem, calc((100vw - 1280px) / 2 + 2rem)) 44px; }
.rpt-stats { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #b6bfda; }
.rpt-stat { padding: 28px 30px; border-left: 1px solid #b6bfda; }
.rpt-stat:first-child { border-left: none; padding-left: 0; }
.rpt-num { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 3rem; line-height: 1; margin-bottom: 14px; }
.n-green { color: #5f7346; } .n-gold { color: #bf9a34; } .n-red { color: #b2543f; } .n-blue { color: #5f7f9e; }
.rpt-stat-t { font-weight: 700; color: #2f3729; font-size: 1.05rem; margin-bottom: 4px; }
.rpt-stat-s { color: #7c817b; font-size: .93rem; }
.rpt-foot { display: flex; align-items: center; justify-content: space-between; gap: 24px;
  border-top: 1px solid #b6bfda; padding: 28px 0 0; }
.rpt-quote { font-family: 'Fraunces', Georgia, serif; font-style: italic; color: #2f3729;
  font-size: 1.5rem; margin: 0 !important; }
.rpt-tag { display: flex; align-items: center; gap: 16px; text-transform: uppercase; letter-spacing: .16em;
  font-size: .74rem; font-weight: 700; color: #7c817b; text-align: right; line-height: 1.55; }
.rpt-tag .tag-line { width: 60px; height: 1px; background: #9aa6cc; flex: 0 0 auto; }
@media (max-width: 820px) {
  .rpt-hero { min-height: 440px; background-position: 72% center; }
  .rpt-hero-inner { padding: 44px max(1.25rem, calc((100vw - 1280px) / 2 + 1.25rem)); }
  .rpt-left { max-width: 100%; }
  .rpt-lower { padding: 4px max(1.25rem, calc((100vw - 1280px) / 2 + 1.25rem)) 32px; }
  .rpt-stats { grid-template-columns: repeat(2, 1fr); }
  .rpt-stat:nth-child(3) { border-left: none; padding-left: 0; }
  .rpt-foot { flex-direction: column; align-items: flex-start; }
}
/* Equal breathing room above and below the nav (keeps the gap symmetric) */
.nav { margin-top: 18px; margin-bottom: 18px; }
</style>
"""


def render_landing():
    st.markdown(LANDING_CSS, unsafe_allow_html=True)
    bg = hero_data_uri()

    nav = NAV_HTML

    hero = (
        f'<div class="bg-hero" style="background-image: '
        f"linear-gradient(100deg, rgba(205,213,232,.95) 0%, rgba(205,213,232,.88) 34%, "
        f"rgba(205,213,232,.55) 62%, rgba(205,213,232,.12) 100%), url('{bg}');\">"
        '<div class="hero-inner"><div class="hero-text">'
        '<p class="eyebrow">A smarter look at math learning</p>'
        "<h1>Because a grade doesn’t tell the whole story.</h1>"
        '<p class="lede">A short, adaptive assessment that shows what your child really '
        "understands — where they may have gaps, and what they’re ready to learn next.</p>"
        '<a class="cta" href="?go=intake" target="_self">Start the Math Check →</a>'
        '<p class="meta">Takes about 15 minutes · Grades 2–8</p>'
        "</div></div></div>"
    )

    svg_bolt = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>')
    svg_lines = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
                 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                 '<line x1="4" y1="7" x2="20" y2="7"></line><line x1="4" y1="12" x2="20" y2="12"></line>'
                 '<line x1="4" y1="17" x2="14" y2="17"></line></svg>')
    svg_circle = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
                  'stroke-width="2"><circle cx="12" cy="12" r="9"></circle></svg>')

    features = (
        '<div class="feat-band"><div class="feat-grid">'
        f'<div class="feat"><span class="fic">{svg_bolt}</span><div class="ftext">'
        '<div class="ft-title">Identify strengths and gaps</div>'
        '<div class="ft-sub">Looks below, at, and above grade level.</div></div></div>'
        f'<div class="feat"><span class="fic">{svg_lines}</span><div class="ftext">'
        '<div class="ft-title">Actionable insights</div>'
        '<div class="ft-sub">Understand what the responses suggest.</div></div></div>'
        f'<div class="feat"><span class="fic">{svg_circle}</span><div class="ftext">'
        '<div class="ft-title">Built for real learners</div>'
        '<div class="ft-sub">Adaptive questions, not a fixed worksheet.</div></div></div>'
        "</div></div>"
    )

    how = (
        '<div class="hw-band" id="how">'
        '<p class="section-eyebrow">How it works</p>'
        '<p class="hw-title">A bigger picture than one score.</p>'
        '<p class="hw-sub">The assessment follows the learner. If something looks uncertain, '
        "it checks the foundation. If something looks strong, it explores what’s next.</p>"
        "</div>"
    )

    signals_cards = [
        ("1", "Says “I understood” — but can’t explain it",
         "Ask them to teach the lesson back to you. If they get stuck, they memorized it instead of learning it."),
        ("2", "Only solves problems “like in class”",
         "Change the wording a little and they no longer know where to start."),
        ("3", "Counts on fingers for simple facts",
         "An uncertain times table means every exercise quietly takes twice as long."),
        ("4", "Avoids math: “No homework today”",
         "Avoidance isn’t laziness — it’s self-protection when the work feels unsafe."),
        ("5", "Grades slip gradually, not suddenly",
         "90% → 80% → 60%. The foundation has gaps, so the collapse is slow and easy to miss."),
    ]
    cards_html = "".join(
        f'<div class="sig-card"><span class="sig-num">{n}</span><h4>{t}</h4><p>{d}</p></div>'
        for n, t, d in signals_cards
    )
    signals = (
        '<div class="sig-band" id="signs">'
        '<p class="section-eyebrow" style="text-align:left">Check for yourself, at home, in 5 minutes</p>'
        '<p class="sig-title">5 signs your child has <em>gaps</em> in math.</p>'
        '<p class="sig-sub">The foundation cracks quietly — here’s what it tends to look like day to day.</p>'
        f'<div class="sig-grid">{cards_html}</div>'
        "</div>"
    )

    footer = (
        '<div class="foot"><div>'
        '<p class="brand">Beyond the Grade</p>'
        "<p>A parent-friendly way to understand math learning beyond the report card.</p></div>"
        '<div><p class="note-title">Prototype note</p>'
        '<p class="note">This version is an engineering prototype. Its results are not '
        "standardized or diagnostic.</p></div></div>"
    )

    st.markdown(nav + hero + features + how + signals + footer, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------
if ss.phase == "landing":
    render_landing()

# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------
elif ss.phase == "intake":
    st.markdown(INTAKE_CSS, unsafe_allow_html=True)
    st.markdown(NAV_HTML, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2.6, 1])
    with col:
        st.markdown(
            build_stepper(1)
            + '<h1 class="intake-h1">Let’s get started.</h1>'
            + '<p class="intake-sub">Tell us a little about your child.</p>',
            unsafe_allow_html=True,
        )
        with st.form("intake", border=False):
            name = st.text_input("Child's first name", placeholder="Alex")
            grade = st.selectbox(
                "Current grade", ["", 2, 3, 4, 5, 6, 7, 8],
                format_func=lambda g: "Select a grade" if g == "" else f"Grade {g}",
            )
            age = st.text_input("Child's age (optional)", placeholder="11")
            submitted = st.form_submit_button("Next →", type="primary")
        if submitted:
            if not name.strip():
                st.error("Please enter a first name to begin.")
            elif grade == "":
                st.error("Please select a grade.")
            else:
                start(name.strip(), int(grade), age.strip() or None)
                st.rerun()

# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------
elif ss.phase == "assessment":
    st.markdown(ASSESSMENT_CSS, unsafe_allow_html=True)
    st.markdown(NAV_HTML, unsafe_allow_html=True)

    q = ss.current_q
    state = ss.state
    current_num = state["questionCount"] + 1

    _, col, _ = st.columns([1, 3.4, 1])
    with col:
        st.markdown(build_stepper(2), unsafe_allow_html=True)
        st.markdown(
            f'<div class="qhead"><span class="qchip">{engine.SKILL_LABELS.get(q["skill"], q["skill"])}</span>'
            f'<span class="qnum">Question {current_num}</span></div>'
            f'<div class="qprompt">{q["prompt"]}</div>',
            unsafe_allow_html=True,
        )

        key = f"resp_{q['id']}"
        if q.get("type") == "short_answer" or not q.get("choices"):
            response = st.text_input("Your answer", key=key, placeholder="Type your answer", label_visibility="collapsed")
        else:
            response = st.radio("Choose one:", q["choices"], index=None, key=key, label_visibility="collapsed")

        disabled = response is None or (isinstance(response, str) and response.strip() == "")
        st.markdown('<div style="height:52px"></div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns([4, 1])
        with pc1:
            pct = round(min(state["questionCount"] / state["maxQuestions"], 1.0) * 100)
            st.markdown(f'<div class="qprog"><div class="qprog-fill" style="width:{pct}%"></div></div>', unsafe_allow_html=True)
        with pc2:
            clicked = st.button("Next →", type="primary", disabled=disabled, use_container_width=True)
        if clicked and not disabled:
            submit_answer(response)
            st.rerun()

# ---------------------------------------------------------------------------
# Done (interstitial before the report)
# ---------------------------------------------------------------------------
elif ss.phase == "done":
    st.markdown(DONE_CSS, unsafe_allow_html=True)
    st.markdown(NAV_HTML, unsafe_allow_html=True)
    name = ss.child["name"] if ss.child else "your child"
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            '<div class="done-wrap">'
            '<div class="check-badge">✓</div>'
            '<h1 class="done-h1">All done!</h1>'
            f'<p class="done-sub">We’ve analyzed {name}’s responses and the Math Snapshot is ready.</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("View Results →", type="primary"):
            ss.phase = "results"
            st.rerun()
        st.markdown('<p class="done-note">Progress starts with understanding.</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
elif ss.phase == "results":
    state = ss.state
    snap = engine.build_snapshot(state)
    name = ss.child["name"]
    grade = ss.child["grade"]
    band = engine.overall_band(snap["globalAbility"])

    assessed = [s for s in snap["skills"] if s["evidence"] > 0]
    for s in assessed:
        s["comparison"] = engine.comparison_for_skill(s, grade)
    ready = sum(1 for s in assessed if s["comparison"]["tone"] == "ahead")

    st.markdown(RESULTS_CSS, unsafe_allow_html=True)

    strong_n = len(snap["strongAreas"])
    review_n = len(snap["areasToReview"])
    focus_n = len(snap["focusAreas"])
    pct = round(min(max(snap["globalAbility"], 0.0), 1.0) * 100)
    completed = date.today().strftime("%B %-d, %Y")

    if focus_n or review_n:
        tail = "with a few areas to strengthen"
    elif strong_n:
        tail = "with consistent strengths across skills"
    else:
        tail = "across a balanced set of skills"
    summary = (
        f"{name} shows {band.lower()} understanding across "
        f"{snap['questionsAnswered']} questions, {tail}."
    )

    photo = report_data_uri()
    dl_icon = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
        '<polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>'
    )

    hero_bg = (
        "linear-gradient(95deg, rgba(205,213,232,1) 0%, rgba(205,213,232,1) 32%, "
        "rgba(205,213,232,.86) 47%, rgba(205,213,232,.34) 66%, rgba(205,213,232,0) 90%), "
        f"url({photo})"
    )

    st.markdown(
        f'{NAV_HTML}'
        f'<div class="rpt-hero" style="background-image:{hero_bg}">'
        f'<div class="rpt-hero-inner"><div class="rpt-left">'
        f'<p class="rpt-eyebrow">Learning Snapshot</p>'
        f'<h1 class="rpt-title">{name}\'s<br>Math Snapshot</h1>'
        f'<p class="rpt-meta">Grade {grade} &nbsp;·&nbsp; Completed {completed}</p>'
        f'<p class="rpt-oh">Overall understanding</p>'
        f'<p class="rpt-band">{band}</p>'
        f'<div class="rpt-prog"><div class="rpt-prog-fill" style="width:{pct}%"></div></div>'
        f'<p class="rpt-summary">{summary}</p>'
        f'<a class="rpt-pdf" href="#" target="_self">{dl_icon} Download PDF</a>'
        f'</div></div></div>'
        f'<div class="rpt-lower">'
        f'<div class="rpt-stats">'
        f'<div class="rpt-stat"><div class="rpt-num n-green">{strong_n}</div>'
        f'<div class="rpt-stat-t">Strong areas</div><div class="rpt-stat-s">On or above grade level</div></div>'
        f'<div class="rpt-stat"><div class="rpt-num n-gold">{review_n}</div>'
        f'<div class="rpt-stat-t">Areas to review</div><div class="rpt-stat-s">Slightly below grade level</div></div>'
        f'<div class="rpt-stat"><div class="rpt-num n-red">{focus_n}</div>'
        f'<div class="rpt-stat-t">Focus area</div><div class="rpt-stat-s">Below grade level</div></div>'
        f'<div class="rpt-stat"><div class="rpt-num n-blue">{ready}</div>'
        f'<div class="rpt-stat-t">Ready for more</div><div class="rpt-stat-s">Above-grade topics</div></div>'
        f'</div>'
        f'<div class="rpt-foot">'
        f'<p class="rpt-quote">A grade is one number. This is a bigger picture.</p>'
        f'<div class="rpt-tag"><span class="tag-line"></span>Different strengths.<br>Brighter possibilities.</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tab_overview, tab_skills, tab_questions, tab_next = st.tabs(
        ["Overview", "Skill details", "Questions", "Next steps"]
    )

    tone_class = {"on": "b-on", "slightly": "b-slightly", "below": "b-below", "ahead": "b-ahead"}

    with tab_overview:
        st.markdown("**Key takeaways**")
        takeaways = []
        if snap["strongAreas"]:
            takeaways.append(f"Strong foundation in {', '.join(snap['strongAreas'][:2])}")
        if snap["areasToReview"]:
            takeaways.append(f"{', '.join(snap['areasToReview'][:2])} could use more practice")
        if snap["focusAreas"]:
            takeaways.append(f"Focus support recommended for {', '.join(snap['focusAreas'][:2])}")
        if snap["readyForMore"]:
            takeaways.append("Ready for some above-grade concepts")
        for t in takeaways:
            st.markdown(f"- {t}")

        mix = snap["errorMix"]
        if mix["procedural"] + mix["conceptual"] > 0:
            st.markdown("**Why answers were missed**")
            st.markdown(
                f"<span class='badge b-proc'>{mix['procedural']} procedural</span> &nbsp; "
                f"<span class='badge b-cog'>{mix['conceptual']} conceptual</span>",
                unsafe_allow_html=True,
            )
            if mix["conceptual"] > mix["procedural"]:
                st.caption("Most misses were conceptual — worth reteaching the idea, not just more practice.")
            elif mix["procedural"] > mix["conceptual"]:
                st.caption("Most misses were procedural slips — the methods are there; accuracy comes with practice.")
            else:
                st.caption("An even mix of procedural slips and conceptual gaps.")

    with tab_skills:
        for s in assessed:
            cmp = s["comparison"]
            left, right = st.columns([3, 2])
            with left:
                st.markdown(f"**{s['label']}**")
                st.progress(min(max(s["mastery"], 0.08), 1.0))
            with right:
                st.markdown(
                    f"<span class='badge {tone_class.get(cmp['tone'], 'b-on')}'>{cmp['label']}</span> "
                    f"&nbsp; {s['correct']}/{s['evidence']} correct",
                    unsafe_allow_html=True,
                )

    with tab_questions:
        st.caption("Every question, and — when missed — whether it was a procedural slip or a conceptual gap.")
        for h in state["history"]:
            gen = state["generated"].get(h["questionId"], {})
            mark = "✅" if h["correct"] else "❌"
            st.markdown(f"{mark} **{gen.get('prompt', h['questionId'])}**")
            meta = f"{engine.SKILL_LABELS.get(h['skill'], h['skill'])} · Grade {h['grade']}"
            if h["correct"]:
                st.caption(f"{meta} · answered {h['response']}")
            else:
                badge = "b-proc" if h["diagnosis"] and h["diagnosis"]["type"] == "procedural" else "b-cog"
                label = "Procedural error" if badge == "b-proc" else "Cognitive error"
                st.caption(f"{meta} · chose **{h['response']}**, correct answer **{gen.get('answer')}**")
                why = h["diagnosis"]["note"] if h["diagnosis"] else None
                st.markdown(
                    (f"<span class='qwhy'>Why: {why}.</span> &nbsp; " if why else "")
                    + f"<span class='badge {badge}'>{label}</span>",
                    unsafe_allow_html=True,
                )
            st.divider()

    with tab_next:
        st.markdown("**What's next?**")
        steps = []
        focus_skill = min(assessed, key=lambda k: k["mastery"]) if assessed else None
        if focus_skill:
            steps.append(f"Spend short, regular sessions on {focus_skill['label']} before moving on.")
        if snap["areasToReview"]:
            steps.append(f"Review {', '.join(snap['areasToReview'])} with mixed practice problems.")
        if snap["readyForMore"]:
            steps.append("Introduce a stretch challenge to keep engagement high.")
        steps.append("Re-take the Math Check in 4–6 weeks to measure growth.")
        for s in steps:
            st.markdown(f"- {s}")

    st.divider()
    st.button("Start over", on_click=reset)
