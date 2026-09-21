"""
Beyond the Grade — Streamlit app.

A Python/Streamlit front end over engine.py, deployable on Streamlit Community
Cloud. This is a separate build from the Node version (../server.js + ../public),
which is left intact.

Run locally:   streamlit run streamlit/app.py
"""

import streamlit as st
import engine

st.set_page_config(page_title="Beyond the Grade", page_icon="📘", layout="centered")

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
ss.setdefault("phase", "intake")
ss.setdefault("state", None)
ss.setdefault("current_q", None)
ss.setdefault("child", None)


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
    ss.phase = "intake"
    ss.state = None
    ss.current_q = None
    ss.child = None


# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------
if ss.phase == "intake":
    st.title("Beyond the Grade")
    st.markdown("#### Because a grade doesn't tell the whole story.")
    st.write(
        "A short, adaptive assessment that shows what your child really understands — "
        "where they may have gaps, and what they're ready to learn next."
    )
    with st.form("intake"):
        name = st.text_input("Child's first name", placeholder="Alex")
        grade = st.selectbox("Current grade", [2, 3, 4, 5, 6, 7, 8], index=4, format_func=lambda g: f"Grade {g}")
        age = st.number_input("Child's age (optional)", min_value=5, max_value=18, value=None, step=1)
        submitted = st.form_submit_button("Start the Math Check →", type="primary")
    st.caption("Takes about 15 minutes · Grades 2–8")
    if submitted:
        if not name.strip():
            st.error("Please enter a first name to begin.")
        else:
            start(name.strip(), int(grade), age)
            st.rerun()

# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------
elif ss.phase == "assessment":
    q = ss.current_q
    state = ss.state
    current_num = state["questionCount"] + 1

    st.progress(min(state["questionCount"] / state["maxQuestions"], 1.0))
    st.markdown(
        f"<span class='chip'>{engine.SKILL_LABELS.get(q['skill'], q['skill'])}</span> "
        f"&nbsp;&nbsp;<span style='color:#8a8578'>Question {current_num}</span>",
        unsafe_allow_html=True,
    )
    st.subheader(q["prompt"])

    key = f"resp_{q['id']}"
    if q.get("type") == "short_answer" or not q.get("choices"):
        response = st.text_input("Your answer", key=key, placeholder="Type your answer")
    else:
        response = st.radio("Choose one:", q["choices"], index=None, key=key)

    if st.button("Next →", type="primary"):
        if response is None or (isinstance(response, str) and response.strip() == ""):
            st.warning("Pick an answer to continue.")
        else:
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
