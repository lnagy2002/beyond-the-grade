# Beyond the Grade

An adaptive math assessment that builds a parent-facing picture of a child's
understanding — below, at, and above grade level — instead of a single score.
It shows *where* the gaps are and *why* an answer was wrong (a procedural slip
vs. a conceptual misconception).

Question selection and scoring are **deterministic**. Questions are generated
from parameterized templates with a seeded RNG, so a retake asks the same
concepts with different numbers. No AI is involved in scoring or routing.

## Two builds, one engine

| Build | Stack | Entry point | Deploy |
|-------|-------|-------------|--------|
| Web app | Node (zero deps) + static HTML/CSS/JS | `server.js` → `public/` | Any Node host (Render, Railway, Fly) |
| Streamlit app | Python + Streamlit | `streamlit/app.py` | Streamlit Community Cloud |

Both share the same logic. `streamlit/engine.py` is a Python port of
`beyond-the-grade-adaptive.js`; keep the two in sync when either changes.

## Run the Node web app
```bash
node server.js
# open http://localhost:3000
```
- `beyond-the-grade-adaptive.js` — assessment engine (templates, routing, diagnosis)
- `server.js` — zero-dependency HTTP server + JSON API (`/api/start`, `/api/answer`, `/api/snapshot`)
- `public/` — the front end (landing page, assessment flow, diagnostic report)
- `test-beyond-the-grade-adaptive.js` — engine tests (`npm test` or `node test-beyond-the-grade-adaptive.js`)

## Run the Streamlit app
```bash
pip install -r streamlit/requirements.txt
streamlit run streamlit/app.py
# open http://localhost:8501
```
See `streamlit/README.md` for Streamlit Community Cloud deployment.

## Status
Engineering prototype. The routing/mastery model is a lightweight heuristic, not
a validated psychometric instrument — results are illustrative, not diagnostic.
