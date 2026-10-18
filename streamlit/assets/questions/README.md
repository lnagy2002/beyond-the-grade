# Question image assets

Drop image files here (PNG, JPG, WEBP, or SVG) to attach a photo/diagram to a
question. Reference them by their path **relative to this folder**.

Two ways to attach an image to a question:

1. On a blueprint in `engine.py` (QUESTION_BANK):
   `{"id": "GEO4-09", "grade": 4, "skill": "geometry", "difficulty": 0.4,
     "prereq": [], "misconception": None, "template": "...",
     "image": "shapes/triangle.png"}`

2. From inside a template function, by returning an `image` key:
   `return {"prompt": "...", "image": "shapes/triangle.png", **q}`

The app (`app.py`) embeds the file as a data URI at render time (mtime-cached,
so swapping the file refreshes it) and shows it in the figure slot — above the
answer choices in the assessment and in the report's Questions tab.

Notes
- If a question sets both `figure` (inline SVG) and `image`, the SVG wins.
- Missing files or paths that escape this folder render nothing (no crash).
- Keep files small; they are base64-embedded into the page.
