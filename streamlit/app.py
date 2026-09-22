"""
Beyond the Grade — Streamlit app.

A Python/Streamlit front end over engine.py, deployable on Streamlit Community
Cloud. This is a separate build from the Node version (../server.js + ../public),
which is left intact.

Run locally:   streamlit run streamlit/app.py
"""

import base64
from pathlib import Path

import streamlit as st
import engine

st.set_page_config(page_title="Beyond the Grade", page_icon="📘", layout="centered")


@st.cache_data
def hero_data_uri():
    """Base64 data URI for the hero photo so it embeds without static hosting."""
    path = Path(__file__).parent / "assets" / "hero.webp"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/webp;base64,{data}"

# Light brand styling.
st.markdown(
    """
    <style>
      .stApp { background: #f4f0e7; }
      .badge { display:inline-block; padding:4px 12px; border-radius:999px; font-size:.8rem; font-weight:700; }
      .b-proc { background:#f3e6c4; color:#8a6a1e; }
      .b-cog  { background:#f2d9d2; color:#a5493a; }
      .b-on   { background:#e2efdd; color:#547a45; }
      .b-slightly { background:#f6ecd2; color:#a07d24; }
      .b-below { background:#f6e2dd; color:#b45f4f; }
      .b-ahead { background:#e0e9f2; color:#4f759c; }
      .chip { display:inline-block; background:#f0dcd5; color:#8f5a4c; padding:4px 12px; border-radius:999px; font-size:.8rem; font-weight:600; }
      .qwhy { color:#8f5a4c; font-style:italic; }
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
        dot_style = ' style="background:#1c2530"' if i <= active else ""
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
        ss.phase = "results"
    else:
        nxt = engine.choose_next_question(ss.state)
        ss.current_q = nxt
        if nxt is None:
            ss.phase = "results"


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
.nav { background: #f4f0e7; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #1c2530 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #43505d !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #1c2530 !important; }
.nav-links a.nav-cta { background: #1c2530; color: #fff !important; text-decoration: none !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
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
  font-weight: 700; color: #6f7016; margin: 0 0 18px; }
.hero-inner h1 { font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: #1c2530;
  font-size: clamp(2.6rem, 5.2vw, 4.25rem) !important; line-height: 1.02; margin: 0 0 26px; }
.hero-inner .lede { color: #43505d; font-size: 1.14rem; max-width: 44ch; margin: 0 0 30px; }
.hero-inner .meta { color: #8a8578; font-size: .95rem; margin: 18px 0 0; }
a.cta { display: inline-block; background: #1c2530; color: #fff !important; padding: 14px 24px;
  border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 1rem; }
a.cta:hover { background: #10161d; }
.section-eyebrow { text-transform: uppercase; letter-spacing: .16em; font-size: .78rem;
  font-weight: 700; color: #6f7016; text-align: center; margin: 0 0 22px; }
/* Features — white full-width band, icons to the left of the text */
.feat-band { background: #fff; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 46px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; }
.feat { display: flex; align-items: flex-start; gap: 14px; text-align: left; }
.fic { color: #1c2530; flex: 0 0 auto; display: inline-flex; margin-top: 1px; }
.ft-title { font-family: 'Inter', sans-serif; font-size: 1.08rem !important; font-weight: 700;
  color: #1c2530; margin: 0 0 5px !important; line-height: 1.3; }
.ft-sub { color: #43505d; font-size: .98rem !important; margin: 0 !important; line-height: 1.45; }
/* How it works — full-width cream band */
.hw-band { background: #efe9dc; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 72px max(2rem, calc((100vw - 1280px) / 2 + 2rem)) 90px; text-align: center; }
.hw-title { font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: #1c2530;
  font-size: clamp(2.2rem, 5vw, 3.4rem) !important; line-height: 1.08; text-align: center !important; margin: 0 0 16px; }
.hw-sub { display: inline-block !important; color: #43505d; text-align: center !important;
  max-width: 62ch; font-size: 1.12rem !important; margin: 0 auto; }
/* Signals — white full-width band */
.sig-band { background: #fff; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 72px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.sig-title { font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: #1c2530;
  font-size: clamp(2.1rem, 4.6vw, 3.3rem) !important; line-height: 1.1; margin: 0 0 8px; }
.sig-title em { color: #6f7016; font-style: italic; }
.sig-sub { color: #43505d; font-size: 1.1rem !important; margin: 0 0 26px; }
.sig-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.sig-card { background: #fff; border: 1px solid #e4ddcf; border-radius: 16px; padding: 26px; }
.sig-num { display: inline-grid; place-items: center; width: 42px; height: 42px; border-radius: 50%;
  background: #1c2530; color: #fff; font-weight: 700; font-size: 1.05rem; margin-bottom: 20px; }
.sig-card h4 { font-family: 'Inter', sans-serif; font-size: 1.18rem; color: #1c2530; margin: 0 0 12px; line-height: 1.25; }
.sig-card p { color: #43505d; font-size: .98rem; margin: 0; line-height: 1.55; }
.foot { background: #e7c7bd; border-radius: 0; width: 100vw; margin: 0 calc(-50vw + 50%);
  padding: 64px max(2rem, calc((100vw - 1280px) / 2 + 2rem)) 72px;
  display: grid; grid-template-columns: 1.1fr 1fr; gap: 60px; }
.foot .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.5rem; color: #1c2530; margin: 0 0 14px; }
.foot p { color: #1c2530; margin: 0; font-size: 1.02rem; }
.foot .note-title { font-weight: 700; margin: 0 0 8px; }
.foot .note { color: #9a6b60; }
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
.nav { background: #f4f0e7; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #1c2530 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #43505d !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #1c2530 !important; }
.nav-links a.nav-cta { background: #1c2530; color: #fff !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
/* Stepper */
.stepper { display: flex; align-items: center; gap: 12px; margin: 40px 0 34px; }
.step { display: flex; align-items: center; gap: 8px; font-size: .92rem; color: #8a8578; white-space: nowrap; }
.step.active { color: #1c2530; font-weight: 600; }
.step .dot { width: 12px; height: 12px; border-radius: 50%; background: #cdc7b8; }
.step.active .dot { background: #1c2530; }
.stepline { flex: 1; height: 3px; background: #ded8c9; border-radius: 3px; min-width: 24px; }
/* Heading */
h1.intake-h1 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #1c2530;
  font-size: clamp(2.2rem, 4.4vw, 3.1rem) !important; line-height: 1.05; margin: 0 0 12px; padding: 0; }
.intake-sub { color: #43505d; font-size: 1.06rem; margin: 0 0 30px; }
/* Form fields */
.stTextInput, .stSelectbox, .stNumberInput { margin-bottom: 22px !important; }
[data-testid="stWidgetLabel"] p { font-weight: 600 !important; color: #1c2530 !important; font-size: .95rem !important; }
/* Uniform 52px control boxes: border/height on the BaseWeb container for all three */
.stTextInput div[data-baseweb="input"],
.stNumberInput div[data-baseweb="input"],
.stSelectbox div[data-baseweb="select"] > div {
  background: #fff !important; border: 1px solid #e4ddcf !important; border-radius: 12px !important;
  height: 52px !important; min-height: 52px !important; box-sizing: border-box !important; align-items: center !important; }
.stTextInput input, .stNumberInput input {
  background: transparent !important; border: none !important; height: 50px !important;
  padding: 0 16px !important; font-size: 1rem !important; color: #1c2530 !important; }
.stNumberInput button { display: none !important; }
.stSelectbox div[data-baseweb="select"] > div > div { padding-left: 6px !important; }
/* Next button */
.stFormSubmitButton button {
  background: #1c2530 !important; color: #fff !important; border: none !important; border-radius: 12px !important;
  width: 100% !important; padding: 14px 0 !important; font-weight: 600 !important; margin-top: 4px; }
.stFormSubmitButton button:hover { background: #10161d !important; }
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
.nav { background: #f4f0e7; width: 100vw; margin: 0 calc(-50vw + 50%);
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px max(2rem, calc((100vw - 1280px) / 2 + 2rem)); }
.nav .brand { font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: 1.35rem; color: #1c2530 !important; text-decoration: none !important; }
.nav-links { display: flex; align-items: center; gap: 26px; }
.nav-links a { color: #43505d !important; text-decoration: none !important; font-size: .95rem; }
.nav-links a:hover { color: #1c2530 !important; }
.nav-links a.nav-cta { background: #1c2530; color: #fff !important; padding: 9px 18px; border-radius: 10px; font-weight: 600; }
/* Stepper */
.stepper { display: flex; align-items: center; gap: 12px; margin: 40px 0 34px; }
.step { display: flex; align-items: center; gap: 8px; font-size: .92rem; color: #8a8578; white-space: nowrap; }
.step.active { color: #1c2530; font-weight: 600; }
.step .dot { width: 12px; height: 12px; border-radius: 50%; background: #cdc7b8; }
.stepline { flex: 1; height: 3px; background: #ded8c9; border-radius: 3px; min-width: 24px; }
.stepline.done { background: #1c2530; }
/* Question head */
.qhead { display: flex; align-items: center; justify-content: space-between; margin: 4px 0 18px; }
.qchip { background: #f0dcd5; color: #8f5a4c; font-weight: 600; font-size: .9rem; padding: 8px 18px; border-radius: 999px; }
.qnum { color: #8a8578; font-size: 1rem; }
.qprompt { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; color: #1c2530;
  font-size: clamp(1.8rem, 3.2vw, 2.4rem) !important; line-height: 1.15; margin: 0 0 24px; }
/* Choices as cards */
.stRadio [role="radiogroup"] { display: flex; flex-direction: column; gap: 12px; }
.stRadio [role="radiogroup"] > label {
  background: #fff !important; border: 1px solid #e4ddcf !important; border-radius: 14px !important;
  padding: 16px 20px !important; margin: 0 !important; width: 100% !important; min-height: 58px !important;
  display: flex !important; align-items: center !important; cursor: pointer; }
.stRadio [role="radiogroup"] > label:hover { border-color: #b6b73f !important; }
.stRadio [role="radiogroup"] > label:has(input:checked) { border-color: #b6b73f !important; background: #fbfae9 !important; }
.stRadio [role="radiogroup"] > label > div:last-child { font-size: 1.08rem !important; color: #1c2530 !important; }
/* Short-answer input — same 52px box as intake inputs */
.stTextInput div[data-baseweb="input"] {
  background: #fff !important; border: 1px solid #e4ddcf !important; border-radius: 12px !important;
  height: 52px !important; min-height: 52px !important; box-sizing: border-box !important; align-items: center !important; }
.stTextInput input { background: transparent !important; border: none !important; height: 50px !important;
  padding: 0 16px !important; font-size: 1rem !important; color: #1c2530 !important; }
/* Progress bar — custom HTML (warm gray track, ink fill) */
.qprog { height: 8px; background: #cdc7b8; border-radius: 6px; width: 100%; overflow: hidden; }
.qprog-fill { height: 100%; background: #1c2530; border-radius: 6px; }
/* Vertically center the progress bar with the Next button */
[data-testid="stHorizontalBlock"] { align-items: center !important; }
.stButton button { background: #1c2530 !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; padding: 12px 26px !important; font-weight: 600 !important; }
.stButton button:disabled { background: #b7bcc2 !important; color: #fff !important; }
</style>
"""


def render_landing():
    st.markdown(LANDING_CSS, unsafe_allow_html=True)
    bg = hero_data_uri()

    nav = NAV_HTML

    hero = (
        f'<div class="bg-hero" style="background-image: '
        f"linear-gradient(100deg, rgba(245,241,233,.95) 0%, rgba(245,241,233,.88) 34%, "
        f"rgba(245,241,233,.55) 62%, rgba(245,241,233,.12) 100%), url('{bg}');\">"
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

    st.title(f"{name}'s Math Snapshot")
    st.caption(f"Grade {grade} · {snap['questionsAnswered']} questions answered")

    st.markdown(f"### Overall understanding: {band}")
    st.progress(snap["globalAbility"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strong areas", len(snap["strongAreas"]))
    c2.metric("To review", len(snap["areasToReview"]))
    c3.metric("Focus areas", len(snap["focusAreas"]))
    c4.metric("Ready for more", ready)

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
