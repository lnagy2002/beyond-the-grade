# Beyond the Grade — Streamlit version

A Python/Streamlit build of the adaptive math assessment, deployable on
**Streamlit Community Cloud** (the same flow as a typical Streamlit app).

This is a **separate** build from the Node version at the repo root
(`server.js` + `public/`), which is unchanged. Both share the same assessment
logic; `engine.py` is a Python port of `../beyond-the-grade-adaptive.js`.

## Files
- `engine.py` — assessment engine: seeded template generation, adaptive
  question routing, and procedural-vs-conceptual error diagnosis. No AI;
  scoring is deterministic.
- `app.py` — Streamlit UI: intake → adaptive questions → diagnostic report.
- `requirements.txt` — dependencies (just `streamlit`).

## Run locally
```bash
pip install -r streamlit/requirements.txt
streamlit run streamlit/app.py
```

## Deploy on Streamlit Community Cloud
1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and click **New app**.
3. Pick the repo/branch, set **Main file path** to `streamlit/app.py`.
4. Deploy. Streamlit installs `streamlit/requirements.txt` automatically.

## Note on state
Assessment state lives in `st.session_state` (per browser session), which is
the right model for Streamlit. When a real backend is added later, the engine
in `engine.py` can be reused behind an API unchanged.
