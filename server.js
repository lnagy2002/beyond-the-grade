/**
 * Beyond the Grade — HTTP server
 *
 * A zero-dependency Node server that:
 *   - serves the static frontend from ./public
 *   - exposes a small JSON API that drives the deterministic assessment engine
 *
 * Design principle carried over from the engine:
 *   The client never sees the correct answer or which question comes next until
 *   it has answered. Scoring and routing happen only on the server, in the
 *   engine — never in the browser.
 *
 * Run:
 *   node server.js
 *   open http://localhost:3000
 */

const http = require("http");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const {
  QUESTION_BANK,
  SKILL_LABELS,
  createAssessment,
  chooseNextQuestion,
  answerQuestion,
  shouldStop,
  buildSnapshot
} = require("./beyond-the-grade-adaptive");

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = path.join(__dirname, "public");

// In-memory session store. Fine for a prototype; swap for a real store later.
const sessions = new Map();

const questionById = new Map(QUESTION_BANK.map(q => [q.id, q]));

// -----------------------------------------------------------------------------
// Assessment helpers
// -----------------------------------------------------------------------------

/**
 * Strip everything the client must not know: the answer, the tagged
 * misconception, and prerequisites are all server-only.
 */
function publicQuestion(q) {
  if (!q) return null;
  return {
    id: q.id,
    skill: q.skill,
    skillLabel: SKILL_LABELS[q.skill] || q.skill,
    grade: q.grade,
    type: q.type || "multiple_choice",
    prompt: q.prompt,
    choices: q.choices || null
  };
}

function progressFor(state) {
  return {
    current: Math.min(state.questionCount + 1, state.maxQuestions),
    answered: state.questionCount,
    total: state.maxQuestions
  };
}

function comparisonForSkill(skill) {
  // How this skill sits relative to the child's current grade, in plain words.
  const { mastery, gradeEvidence } = skill;
  const highest = gradeEvidence && gradeEvidence.highestSuccessfulGrade;
  const current = skill._currentGrade;

  if (mastery >= 0.7 && highest != null && current != null && highest > current) {
    return { label: "Ready for more", tone: "ahead" };
  }
  if (mastery >= 0.7) return { label: "On grade level", tone: "on" };
  if (mastery >= 0.5) return { label: "On grade level", tone: "on" };
  if (mastery >= 0.36) return { label: "Slightly below", tone: "slightly" };
  return { label: "Below grade level", tone: "below" };
}

function overallBand(globalAbility) {
  if (globalAbility >= 0.7) return "Above grade level";
  if (globalAbility >= 0.46) return "On grade level";
  if (globalAbility >= 0.32) return "Approaching grade level";
  return "Below grade level";
}

/**
 * Enrich the engine's raw snapshot with the plain-language framing the report
 * UI needs, without duplicating any scoring logic.
 */
function enrichSnapshot(state, meta) {
  const snapshot = buildSnapshot(state);

  const skills = snapshot.skills.map(s => {
    const withGrade = { ...s, _currentGrade: state.currentGrade };
    const comparison = comparisonForSkill(withGrade);
    return {
      ...s,
      comparison,
      // 0..1 bar fill, kept honest to the mastery estimate.
      barFill: Math.round(Math.max(0.08, Math.min(1, s.mastery)) * 100)
    };
  });

  // Per-question review: what was asked, what the child chose, and — when wrong
  // — why (the specific error and whether it was procedural or conceptual).
  const questionsReview = state.history.map(h => {
    const q = state.generated[h.questionId] || {};
    return {
      questionId: h.questionId,
      skillLabel: SKILL_LABELS[h.skill] || h.skill,
      grade: h.grade,
      prompt: q.prompt || h.questionId,
      correct: h.correct,
      yourAnswer: h.response,
      correctAnswer: q.answer,
      errorType: h.diagnosis ? h.diagnosis.type : null,
      why: h.diagnosis ? h.diagnosis.note : null
    };
  });

  return {
    child: meta,
    currentGrade: snapshot.currentGrade,
    completedAt: meta.completedAt,
    questionsAnswered: snapshot.questionsAnswered,
    globalAbility: snapshot.globalAbility,
    overall: {
      band: overallBand(snapshot.globalAbility),
      fill: Math.round(snapshot.globalAbility * 100)
    },
    counts: {
      strong: snapshot.strongAreas.length,
      review: snapshot.areasToReview.length,
      focus: snapshot.focusAreas.length,
      readyForMore: skills.filter(s => s.comparison.tone === "ahead").length
    },
    strongAreas: snapshot.strongAreas,
    areasToReview: snapshot.areasToReview,
    focusAreas: snapshot.focusAreas,
    readyForMore: snapshot.readyForMore,
    errorMix: snapshot.errorMix,
    questionsReview,
    skills
  };
}

// -----------------------------------------------------------------------------
// API handlers
// -----------------------------------------------------------------------------

function handleStart(body, res) {
  const name = String(body.name || "").trim() || "Your child";
  const grade = Number.parseInt(body.grade, 10);
  if (!Number.isFinite(grade)) return sendJSON(res, 400, { error: "A valid grade is required." });

  const state = createAssessment(grade, { minQuestions: 12, maxQuestions: 20 });
  const id = crypto.randomUUID();
  const meta = {
    name,
    grade,
    age: body.age ? String(body.age).trim() : null,
    startedAt: state.startedAt,
    completedAt: null
  };
  sessions.set(id, { state, meta });

  const question = chooseNextQuestion(state);
  return sendJSON(res, 200, {
    sessionId: id,
    child: meta,
    question: publicQuestion(question),
    progress: progressFor(state)
  });
}

function handleAnswer(body, res) {
  const session = sessions.get(body.sessionId);
  if (!session) return sendJSON(res, 404, { error: "Assessment not found." });

  // The concrete (generated) instance the client was shown lives in the
  // session's cache — that's the copy carrying the correct answer. Fall back to
  // the static bank only for concepts without a template.
  const question = session.state.generated[body.questionId] || questionById.get(body.questionId);
  if (!question) return sendJSON(res, 400, { error: "Unknown question." });
  if (session.state.seen.has(question.id)) {
    return sendJSON(res, 409, { error: "Question already answered." });
  }

  answerQuestion(session.state, question, body.response);

  const done = shouldStop(session.state);
  const next = done ? null : chooseNextQuestion(session.state);

  if (done || !next) {
    session.meta.completedAt = new Date().toISOString();
    return sendJSON(res, 200, {
      done: true,
      progress: progressFor(session.state)
    });
  }

  return sendJSON(res, 200, {
    done: false,
    question: publicQuestion(next),
    progress: progressFor(session.state)
  });
}

function handleSnapshot(body, res) {
  const session = sessions.get(body.sessionId);
  if (!session) return sendJSON(res, 404, { error: "Assessment not found." });
  if (!session.meta.completedAt) session.meta.completedAt = new Date().toISOString();
  return sendJSON(res, 200, enrichSnapshot(session.state, session.meta));
}

// -----------------------------------------------------------------------------
// Plumbing
// -----------------------------------------------------------------------------

function sendJSON(res, status, payload) {
  const data = JSON.stringify(payload);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(data)
  });
  res.end(data);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", chunk => {
      raw += chunk;
      if (raw.length > 1e6) reject(new Error("Body too large"));
    });
    req.on("end", () => {
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch (e) {
        reject(new Error("Invalid JSON"));
      }
    });
    req.on("error", reject);
  });
}

const CONTENT_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".webp": "image/webp",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg"
};

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(req.url.split("?")[0]);
  let rel = urlPath === "/" ? "/index.html" : urlPath;
  const filePath = path.normalize(path.join(PUBLIC_DIR, rel));

  // Prevent path traversal outside the public dir.
  if (!filePath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403);
    return res.end("Forbidden");
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      return res.end("Not found");
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { "Content-Type": CONTENT_TYPES[ext] || "application/octet-stream" });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const urlPath = req.url.split("?")[0];

  if (req.method === "POST" && urlPath.startsWith("/api/")) {
    let body;
    try {
      body = await readBody(req);
    } catch (e) {
      return sendJSON(res, 400, { error: e.message });
    }
    try {
      if (urlPath === "/api/start") return handleStart(body, res);
      if (urlPath === "/api/answer") return handleAnswer(body, res);
      if (urlPath === "/api/snapshot") return handleSnapshot(body, res);
      return sendJSON(res, 404, { error: "Unknown endpoint." });
    } catch (e) {
      return sendJSON(res, 500, { error: "Server error: " + e.message });
    }
  }

  if (req.method === "GET") return serveStatic(req, res);

  res.writeHead(405, { "Content-Type": "text/plain" });
  res.end("Method not allowed");
});

server.listen(PORT, () => {
  console.log(`Beyond the Grade running at http://localhost:${PORT}`);
});

module.exports = { server, enrichSnapshot };
