/* ==========================================================================
   Beyond the Grade — frontend controller
   Talks to the server API; the browser never sees answers or scoring.
   ========================================================================== */

const api = {
  async post(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  }
};

// Shared session state held only for the current visit.
const session = {
  id: null,
  child: null,
  question: null,
  selected: null,
  snapshot: null
};

// ------------------------------- View router -------------------------------
const views = document.querySelectorAll(".view");
const marketingLinks = document.getElementById("marketingLinks");
const appLinks = document.getElementById("appLinks");

function show(name) {
  views.forEach(v => { v.hidden = v.dataset.view !== name; });
  const inApp = name === "results";
  marketingLinks.hidden = inApp;
  appLinks.hidden = !inApp;
  window.scrollTo({ top: 0, behavior: "auto" });
}

document.addEventListener("click", e => {
  const nav = e.target.closest("[data-nav]");
  if (nav) {
    e.preventDefault();
    const dest = nav.dataset.nav;
    if (dest === "results") return goToResults();
    if (dest === "intake") { renderStepper(); show("intake"); return; }
    show(dest);
    return;
  }
  const scroll = e.target.closest("[data-scroll]");
  if (scroll) {
    e.preventDefault();
    show("landing");
    document.getElementById(scroll.dataset.scroll)?.scrollIntoView({ behavior: "smooth" });
  }
});

// -------------------------------- Stepper ----------------------------------
function renderStepper() {
  document.querySelectorAll(".stepper").forEach(el => {
    const step = Number(el.dataset.step);
    el.innerHTML = `
      ${stepEl("1. About You", step >= 1, step === 1)}
      ${lineEl(step > 1)}
      ${stepEl("2. Assessment", step >= 2, step === 2)}
      ${lineEl(step > 2)}
      ${stepEl("3. Results", step >= 3, step === 3)}
    `;
  });
}
function stepEl(label, filled, active) {
  return `<span class="step ${active ? "active" : ""}"><span class="step-dot" style="${filled ? "background:var(--ink)" : ""}"></span>${label}</span>`;
}
function lineEl(done) { return `<span class="step-line ${done ? "done" : ""}"></span>`; }

// -------------------------------- Intake -----------------------------------
const intakeForm = document.getElementById("intakeForm");
const intakeError = document.getElementById("intakeError");

intakeForm.addEventListener("submit", async e => {
  e.preventDefault();
  intakeError.hidden = true;
  const fd = new FormData(intakeForm);
  const name = (fd.get("name") || "").toString().trim();
  const grade = fd.get("grade");
  if (!name || !grade) {
    intakeError.textContent = "Please enter a name and select a grade.";
    intakeError.hidden = false;
    return;
  }
  const submitBtn = intakeForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  submitBtn.textContent = "Starting…";
  try {
    const data = await api.post("/api/start", { name, grade, age: fd.get("age") });
    session.id = data.sessionId;
    session.child = data.child;
    session.question = data.question;
    startAssessment(data);
  } catch (err) {
    intakeError.textContent = err.message;
    intakeError.hidden = false;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Next →";
  }
});

// ------------------------------ Assessment ---------------------------------
const qSkill = document.getElementById("qSkill");
const qCount = document.getElementById("qCount");
const qPrompt = document.getElementById("qPrompt");
const qChoices = document.getElementById("qChoices");
const shortForm = document.getElementById("shortForm");
const shortInput = document.getElementById("shortInput");
const nextBtn = document.getElementById("nextBtn");
const qProgress = document.getElementById("qProgress");

function startAssessment(data) {
  renderStepper();
  show("assessment");
  renderQuestion(data.question, data.progress);
}

function renderQuestion(question, progress) {
  session.question = question;
  session.selected = null;
  qSkill.textContent = question.skillLabel;
  qCount.textContent = `Question ${progress.current}`;
  qPrompt.textContent = question.prompt;
  qProgress.style.setProperty("--pct", `${(progress.answered / progress.total) * 100}%`);
  nextBtn.disabled = true;

  if (question.type === "short_answer" || !question.choices) {
    qChoices.hidden = true;
    shortForm.hidden = false;
    shortInput.value = "";
    shortInput.focus();
  } else {
    shortForm.hidden = true;
    qChoices.hidden = false;
    qChoices.innerHTML = "";
    question.choices.forEach(choice => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "choice";
      btn.innerHTML = `<span class="radio"></span><span>${escapeHTML(choice)}</span>`;
      btn.addEventListener("click", () => {
        session.selected = choice;
        qChoices.querySelectorAll(".choice").forEach(c => c.classList.remove("selected"));
        btn.classList.add("selected");
        nextBtn.disabled = false;
      });
      qChoices.appendChild(btn);
    });
  }
}

shortInput.addEventListener("input", () => {
  session.selected = shortInput.value.trim();
  nextBtn.disabled = session.selected.length === 0;
});
shortForm.addEventListener("submit", e => { e.preventDefault(); if (!nextBtn.disabled) nextBtn.click(); });

nextBtn.addEventListener("click", async () => {
  if (session.selected == null || session.selected === "") return;
  nextBtn.disabled = true;
  const prevLabel = nextBtn.textContent;
  nextBtn.textContent = "…";
  try {
    const data = await api.post("/api/answer", {
      sessionId: session.id,
      questionId: session.question.id,
      response: session.selected
    });
    if (data.done) {
      finishAssessment();
    } else {
      nextBtn.textContent = prevLabel;
      renderQuestion(data.question, data.progress);
    }
  } catch (err) {
    nextBtn.textContent = prevLabel;
    nextBtn.disabled = false;
    alert(err.message);
  }
});

// -------------------------------- Done -------------------------------------
function finishAssessment() {
  document.getElementById("doneName").textContent = session.child?.name || "your child";
  show("done");
}

// ------------------------------- Results -----------------------------------
async function goToResults() {
  if (!session.id) { show("landing"); return; }
  try {
    if (!session.snapshot) {
      session.snapshot = await api.post("/api/snapshot", { sessionId: session.id });
    }
    renderResults(session.snapshot);
    show("results");
  } catch (err) {
    alert(err.message);
  }
}

const SKILL_ICONS = {
  number_sense: "🔢", addition: "➕", subtraction: "➖", multiplication: "✳️",
  fractions: "➗", decimals: "•", word_problems: "📝", ratios: "⚖️",
  expressions: "🔤", equations: "🟰", exponents: "⁝", proportional_reasoning: "📈",
  geometry: "📐", statistics: "📊"
};

function fmtDate(iso) {
  try {
    return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch { return ""; }
}

function renderResults(s) {
  const name = s.child?.name || "Your child";
  const barClass = t => ({ on: "bar-on", slightly: "bar-slightly", below: "bar-below", ahead: "bar-ahead" }[t] || "bar-on");
  const cmpClass = t => ({ slightly: "cmp-slightly", below: "cmp-below", ahead: "cmp-ahead" }[t] || "");

  // Pick a focus skill to feature: weakest with real evidence.
  const assessed = s.skills.filter(k => k.evidence > 0);
  const focusSkill = [...assessed].sort((a, b) => a.mastery - b.mastery)[0];

  const overallDesc = buildOverallDesc(name, s);

  const wrap = document.getElementById("resultsWrap");
  wrap.innerHTML = `
    <!-- Snapshot -->
    <section class="report-card">
      <div class="report-head">
        <div>
          <h2 class="report-title">${escapeHTML(name)}'s Math Snapshot</h2>
          <p class="report-meta">Grade ${s.currentGrade} &nbsp;·&nbsp; Completed ${fmtDate(s.completedAt)}</p>
        </div>
        <button class="btn btn-outline btn-sm" onclick="window.print()">Download PDF</button>
      </div>

      <div class="overall-box">
        <p class="overall-label">Overall understanding</p>
        <p class="overall-band">${s.overall.band}</p>
        <div class="overall-bar"><span style="width:${s.overall.fill}%"></span></div>
        <p class="overall-desc">${overallDesc}</p>
      </div>

      <div class="stat-grid">
        ${statCard("green", s.counts.strong, "Strong areas", "On or above grade level")}
        ${statCard("amber", s.counts.review, "Areas to review", "Slightly below grade level")}
        ${statCard("red", s.counts.focus, "Focus area", "Below grade level")}
        ${statCard("blue", s.counts.readyForMore, "Ready for more", "Above-grade topics")}
      </div>

      <div class="pull-quote">
        <span class="mark">“</span>
        <p>A grade is one number. This is a bigger picture.</p>
      </div>
    </section>

    <!-- Skill breakdown -->
    <section class="report-card">
      <h3 class="section-title">Skill Breakdown</h3>
      <p class="section-sub">See how ${escapeHTML(name)} did across different math areas.</p>
      <div class="thead"><span>Math Area</span><span>Understanding</span><span>Compared to Grade Level</span></div>
      <div class="skill-table">
        ${assessed.map(k => `
          <div class="skill-row">
            <div class="skill-name"><span class="ico">${SKILL_ICONS[k.skill] || "•"}</span>${escapeHTML(k.label)}</div>
            <div class="skill-bar"><span class="${barClass(k.comparison.tone)}" style="width:${k.barFill}%"></span></div>
            <div class="skill-cmp ${cmpClass(k.comparison.tone)}">${k.comparison.label}</div>
          </div>
        `).join("")}
      </div>
    </section>

    <!-- Focus detail -->
    ${focusSkill ? renderFocusDetail(name, focusSkill) : ""}

    <!-- Detailed report with tabs -->
    <section class="report-card">
      <div class="report-head">
        <div>
          <h2 class="report-title">${escapeHTML(name)}'s Detailed Math Report</h2>
          <p class="report-meta">Grade ${s.currentGrade} &nbsp;|&nbsp; ${fmtDate(s.completedAt)}</p>
        </div>
        <button class="btn btn-outline btn-sm" onclick="window.print()">Download PDF</button>
      </div>

      <div class="tabs" id="reportTabs">
        <button class="tab active" data-tab="overview">Overview</button>
        <button class="tab" data-tab="skills">Skill Details</button>
        <button class="tab" data-tab="questions">Questions</button>
        <button class="tab" data-tab="next">Next Steps</button>
      </div>

      <div class="tab-panel" data-panel="overview">
        <div class="two-col">
          <div>
            <p class="overall-label">Overall understanding</p>
            <p class="overall-band">${s.overall.band}</p>
            <div class="overall-bar"><span style="width:${s.overall.fill}%"></span></div>
            <p class="overall-desc">${overallDesc}</p>
          </div>
          <div class="takeaways">
            <h4>Key Takeaways</h4>
            <ul>${buildTakeaways(s).map(t => `<li><span class="tick">✓</span><span>${t}</span></li>`).join("")}</ul>
            ${renderErrorMix(s)}
          </div>
        </div>
      </div>

      <div class="tab-panel" data-panel="skills" hidden>
        ${assessed.map(k => `
          <div class="skill-row">
            <div class="skill-name"><span class="ico">${SKILL_ICONS[k.skill] || "•"}</span>${escapeHTML(k.label)}</div>
            <div class="skill-bar"><span class="${barClass(k.comparison.tone)}" style="width:${k.barFill}%"></span></div>
            <div class="skill-cmp ${cmpClass(k.comparison.tone)}">${k.comparison.label} &nbsp;·&nbsp; ${k.correct}/${k.evidence} correct</div>
          </div>
        `).join("")}
      </div>

      <div class="tab-panel" data-panel="questions" hidden>
        <p class="section-sub">Every question, and — when ${escapeHTML(name)} missed one — whether it looks
          like a <strong>procedural</strong> slip or a <strong>conceptual</strong> gap.</p>
        <div class="qreview">
          ${(s.questionsReview || []).map(renderReviewRow).join("")}
        </div>
      </div>

      <div class="tab-panel" data-panel="next" hidden>
        <div class="next-box">
          <div class="row">
            <div>
              <h4>What's next?</h4>
              <p>Use these results to focus on key areas and build confidence. Small steps make a big difference.</p>
            </div>
            <button class="btn btn-dark" data-nav="landing">Back to home →</button>
          </div>
        </div>
        <ul class="takeaways" style="margin-top:22px">
          ${buildNextSteps(s, focusSkill).map(t => `<li><span class="tick">→</span><span>${t}</span></li>`).join("")}
        </ul>
      </div>
    </section>
  `;

  // Wire tabs
  wrap.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      wrap.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      wrap.querySelectorAll(".tab-panel").forEach(p => { p.hidden = p.dataset.panel !== tab.dataset.tab; });
    });
  });
}

function statCard(color, n, title, sub) {
  return `<div class="stat-card">
    <div class="stat-badge ${color}">${n}</div>
    <p class="stat-title">${title}</p>
    <p class="stat-sub">${sub}</p>
  </div>`;
}

// Badge for a wrong-answer type: procedural (amber) vs conceptual (red).
function errorBadge(type) {
  if (type === "procedural") return `<span class="err-badge err-proc">Procedural error</span>`;
  if (type === "conceptual") return `<span class="err-badge err-cog">Cognitive error</span>`;
  return "";
}

// One row of the question-by-question review.
function renderReviewRow(q) {
  if (q.correct) {
    return `<div class="qreview-row">
      <span class="qreview-mark ok">✓</span>
      <div class="qreview-body">
        <div class="prompt">${escapeHTML(q.prompt)}</div>
        <div class="meta">${escapeHTML(q.skillLabel)} · Grade ${q.grade} · answered ${escapeHTML(String(q.yourAnswer))}</div>
      </div>
    </div>`;
  }
  return `<div class="qreview-row wrong">
    <span class="qreview-mark no">✗</span>
    <div class="qreview-body">
      <div class="prompt">${escapeHTML(q.prompt)}</div>
      <div class="meta">${escapeHTML(q.skillLabel)} · Grade ${q.grade} ·
        chose <strong>${escapeHTML(String(q.yourAnswer))}</strong>,
        correct answer <strong>${escapeHTML(String(q.correctAnswer))}</strong></div>
      ${q.why ? `<div class="qreview-why">Why: ${escapeHTML(q.why)}.</div>` : ""}
    </div>
    ${errorBadge(q.errorType)}
  </div>`;
}

// Overall split of mistakes into procedural slips vs conceptual gaps.
function renderErrorMix(s) {
  const mix = s.errorMix || { procedural: 0, conceptual: 0 };
  const total = mix.procedural + mix.conceptual;
  if (!total) return "";
  const lead = mix.conceptual > mix.procedural
    ? "Most misses were conceptual — worth reteaching the idea, not just more practice."
    : mix.procedural > mix.conceptual
      ? "Most misses were procedural slips — the methods are there; accuracy will come with practice."
      : "Misses were an even mix of procedural slips and conceptual gaps.";
  return `<div class="err-mix">
    <h4>Why answers were missed</h4>
    <div class="err-mix-bars">
      ${mix.procedural ? `<span class="err-badge err-proc">${mix.procedural} procedural</span>` : ""}
      ${mix.conceptual ? `<span class="err-badge err-cog">${mix.conceptual} conceptual</span>` : ""}
    </div>
    <p class="err-mix-note">${lead}</p>
  </div>`;
}

function renderFocusDetail(name, k) {
  const toneBadge = { on: "badge-on", slightly: "badge-slightly", below: "badge-below", ahead: "badge-ahead" }[k.comparison.tone] || "badge-on";
  const notes = buildNoticed(k);
  return `
    <section class="report-card">
      <div class="detail-head">
        <h3 class="section-title">${escapeHTML(k.label)}</h3>
        <span class="badge-level ${toneBadge}">${k.comparison.label}</span>
      </div>
      <p class="detail-lead">${buildSkillLead(name, k)}</p>
      <div class="noticed">
        <h4>What we noticed</h4>
        <ul>${notes.map(n => `<li>${n}</li>`).join("")}</ul>
      </div>
      <div class="why-box">
        <h4>Why this matters</h4>
        <p>${buildWhy(k)}</p>
      </div>
      <div class="home-box">
        <span class="ico">🏠</span>
        <div>
          <h4>Try this at home</h4>
          <p>${buildHome(k)}</p>
        </div>
      </div>
    </section>
  `;
}

// -------- Narrative helpers (templated from real engine data) --------
function buildOverallDesc(name, s) {
  const strong = s.strongAreas.slice(0, 2).join(" and ");
  const focus = s.focusAreas.slice(0, 2).join(" and ");
  let txt = `${escapeHTML(name)} shows ${s.overall.band.toLowerCase()} understanding across ${s.questionsAnswered} questions`;
  if (strong) txt += `, with a solid grasp of ${strong}`;
  if (focus) txt += `, and would benefit from focused support in ${focus}`;
  else if (s.areasToReview.length) txt += `, with a few areas to strengthen`;
  txt += ".";
  if (s.readyForMore) txt += ` There's also readiness for some above-grade topics.`;
  return txt;
}

function buildTakeaways(s) {
  const out = [];
  if (s.strongAreas.length) out.push(`Strong foundation in ${s.strongAreas.slice(0, 2).join(" and ")}`);
  if (s.areasToReview.length) out.push(`${s.areasToReview.slice(0, 2).join(" and ")} need${s.areasToReview.length === 1 ? "s" : ""} additional practice`);
  if (s.focusAreas.length) out.push(`Focus support recommended for ${s.focusAreas.slice(0, 2).join(" and ")}`);
  if (s.readyForMore) out.push("Ready for some above-grade concepts");
  out.push("Personalized practice plan included");
  return out;
}

function buildNextSteps(s, focus) {
  const out = [];
  if (focus) out.push(`Spend short, regular sessions on ${escapeHTML(focus.label)} before moving on.`);
  if (s.areasToReview.length) out.push(`Review ${s.areasToReview.join(", ")} with mixed practice problems.`);
  if (s.readyForMore) out.push(`Introduce a stretch challenge to keep engagement high.`);
  out.push("Re-take the Math Check in 4–6 weeks to measure growth.");
  return out;
}

function buildNoticed(k) {
  const notes = [];
  const pct = k.evidence ? Math.round((k.correct / k.evidence) * 100) : 0;
  notes.push(`Answered ${k.correct} of ${k.evidence} ${escapeHTML(k.label)} questions correctly (${pct}%)`);
  if (k.gradeEvidence?.highestSuccessfulGrade != null)
    notes.push(`Handled ${escapeHTML(k.label)} at up to Grade ${k.gradeEvidence.highestSuccessfulGrade}`);
  if (k.gradeEvidence?.lowestFailedGrade != null)
    notes.push(`Struggled with ${escapeHTML(k.label)} starting around Grade ${k.gradeEvidence.lowestFailedGrade}`);
  // Specific diagnosed errors, tagged by kind (procedural slip vs conceptual gap).
  (k.diagnosedErrors || []).forEach(e => {
    const kind = e.type === "procedural" ? "slip" : "misconception";
    const times = e.count > 1 ? ` (×${e.count})` : "";
    notes.push(`${escapeHTML(e.note)}${times} — ${kind}`);
  });
  return notes;
}

function buildSkillLead(name, k) {
  const tone = k.comparison.tone;
  if (tone === "ahead") return `${escapeHTML(name)} is working confidently in ${escapeHTML(k.label.toLowerCase())} and is ready for more challenging material.`;
  if (tone === "on") return `${escapeHTML(name)} shows a solid, grade-appropriate understanding of ${escapeHTML(k.label.toLowerCase())}.`;
  if (tone === "slightly") return `${escapeHTML(name)} understands the basics of ${escapeHTML(k.label.toLowerCase())} but has a few gaps worth revisiting.`;
  return `${escapeHTML(name)} can work with simple ${escapeHTML(k.label.toLowerCase())} problems, but has difficulty with more advanced ones.`;
}

function buildWhy(k) {
  return `Strengthening ${escapeHTML(k.label.toLowerCase())} supports later work in related topics, so a little targeted practice now pays off across future math.`;
}

function buildHome(k) {
  const tips = {
    fractions: `Use everyday objects — pizza slices, measuring cups — and ask "Can you find another fraction that means the same thing?"`,
    multiplication: `Practice skip-counting and quick facts during car rides or while setting the table.`,
    decimals: `Point out decimals on price tags and ask which is larger and why.`,
    ratios: `Cook together and double or halve a recipe, talking through the ratios.`,
    geometry: `Find rectangles at home and estimate area vs. perimeter together.`,
    word_problems: `Turn small everyday situations into "How many altogether?" story problems.`
  };
  return tips[k.skill] || `Practice a few ${escapeHTML(k.label.toLowerCase())} problems together and talk through the reasoning out loud.`;
}

// -------------------------------- Utils ------------------------------------
function escapeHTML(str) {
  return String(str).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Boot
renderStepper();
show("landing");
