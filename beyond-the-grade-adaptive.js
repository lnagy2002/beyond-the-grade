/**
 * Beyond the Grade — Adaptive Math Assessment Prototype v2
 *
 * Purpose:
 *   Build a useful parent-facing picture of understanding, rather than a single
 *   test score. The assessment can move BELOW, AT, and ABOVE the child's grade.
 *
 * Important architecture decision:
 *   - Question selection/scoring is deterministic.
 *   - AI can later generate question variants and write explanations.
 *   - AI does NOT decide whether a child is correct or which question comes next.
 *
 * Run demo:
 *   node beyond-the-grade-adaptive.js
 *
 * Run a specific demo profile:
 *   node beyond-the-grade-adaptive.js strong
 *   node beyond-the-grade-adaptive.js fractions-gap
 *   node beyond-the-grade-adaptive.js foundation-gap
 */

/**
 * Concept bank. Each entry describes a CONCEPT (skill, grade, difficulty,
 * likely misconception) and names a `template` that generates a concrete
 * question on demand. The inline prompt/choices/answer remain as a static
 * fallback and as a worked example of what the template produces — the engine
 * only uses them when a concept has no template.
 */
const QUESTION_BANK = [
  // ---------------- GRADE 2 / EARLY FOUNDATION ----------------
  {
    id: "NS2-01", grade: 2, skill: "number_sense", difficulty: 0.10,
    prereq: [], misconception: null, template: "number_compare_greatest",
    prompt: "Which number is greatest?", choices: ["23", "32", "19", "28"], answer: "32"
  },
  {
    id: "ADD2-01", grade: 2, skill: "addition", difficulty: 0.15,
    prereq: ["number_sense"], misconception: "regrouping", template: "addition_basic",
    prompt: "What is 8 + 5?", choices: ["12", "13", "14", "15"], answer: "13"
  },
  {
    id: "SUB2-01", grade: 2, skill: "subtraction", difficulty: 0.20,
    prereq: ["number_sense"], misconception: "regrouping", template: "subtraction_basic",
    prompt: "What is 14 − 6?", choices: ["6", "7", "8", "9"], answer: "8"
  },

  // ---------------- GRADE 3 ----------------
  {
    id: "ADD3-01", grade: 3, skill: "addition", difficulty: 0.30,
    prereq: ["addition"], misconception: "regrouping", template: "addition_basic",
    prompt: "What is 47 + 38?", choices: ["75", "84", "85", "95"], answer: "85"
  },
  {
    id: "SUB3-01", grade: 3, skill: "subtraction", difficulty: 0.32,
    prereq: ["subtraction"], misconception: "regrouping", template: "subtraction_basic",
    prompt: "What is 62 − 27?", choices: ["35", "45", "44", "25"], answer: "35"
  },
  {
    id: "OP3-01", grade: 3, skill: "multiplication", difficulty: 0.28,
    prereq: ["addition"], misconception: "counting_addition_instead_of_multiplication", template: "multiplication_meaning",
    prompt: "Which equation represents 3 groups of 5?", choices: ["3 + 5", "3 × 5", "5 − 3", "5 ÷ 3"], answer: "3 × 5"
  },
  {
    id: "FR3-01", grade: 3, skill: "fractions", difficulty: 0.34,
    prereq: ["number_sense"], misconception: "fraction_size", template: "fraction_compare_half",
    prompt: "Which fraction is greater than 1/2?", choices: ["1/4", "2/5", "3/4", "1/3"], answer: "3/4"
  },

  // ---------------- GRADE 4 / FOUNDATION ----------------
  {
    id: "NS4-01", grade: 4, skill: "number_sense", difficulty: 0.30,
    prereq: [], misconception: null, template: "number_compare_greatest",
    prompt: "Which number is greatest?", choices: ["398", "389", "938", "839"], answer: "938"
  },
  {
    id: "OP4-01", grade: 4, skill: "multiplication", difficulty: 0.35,
    prereq: ["number_sense"], misconception: "counting_addition_instead_of_multiplication", template: "multiplication_meaning",
    prompt: "Which equation represents 4 groups of 6?", choices: ["4 + 6", "4 × 6", "6 − 4", "6 ÷ 4"], answer: "4 × 6"
  },
  {
    id: "OP4-02", grade: 4, skill: "multiplication", difficulty: 0.45,
    prereq: ["multiplication"], misconception: "fact_fluency", template: "multiplication_fact",
    prompt: "What is 7 × 8?", type: "short_answer", answer: "56"
  },
  {
    id: "FR4-01", grade: 4, skill: "fractions", difficulty: 0.40,
    prereq: ["number_sense"], misconception: "fraction_size", template: "fraction_compare_half",
    prompt: "Which fraction is greater than 1/2?", choices: ["1/4", "2/5", "3/4", "1/3"], answer: "3/4"
  },
  {
    id: "FR4-02", grade: 4, skill: "fractions", difficulty: 0.52,
    prereq: ["fractions"], misconception: "equivalence", template: "fraction_equivalent",
    prompt: "Which fraction is equivalent to 3/4?", choices: ["6/8", "3/8", "4/6", "5/8"], answer: "6/8"
  },
  {
    id: "WP4-01", grade: 4, skill: "word_problems", difficulty: 0.50,
    prereq: ["multiplication"], misconception: "operation_selection", template: "word_problem_multiply",
    prompt: "There are 6 boxes with 24 pencils in each box. How many pencils are there?",
    choices: ["30", "120", "144", "164"], answer: "144"
  },

  // ---------------- GRADE 5 ----------------
  {
    id: "DEC5-01", grade: 5, skill: "decimals", difficulty: 0.55,
    prereq: ["number_sense"], misconception: "decimal_place_value", template: "decimal_equiv",
    prompt: "Which number is the same as 0.7?", choices: ["7/100", "7/10", "70/1000", "7/1000"], answer: "7/10"
  },
  {
    id: "OP5-01", grade: 5, skill: "multiplication", difficulty: 0.58,
    prereq: ["multiplication"], misconception: "fact_fluency", template: "multiplication_fact",
    prompt: "What is 12 × 6?", type: "short_answer", answer: "72"
  },
  {
    id: "FR5-01", grade: 5, skill: "fractions", difficulty: 0.62,
    prereq: ["fractions"], misconception: "fraction_comparison", template: "fraction_compare_two",
    prompt: "Which is greater, 2/3 or 3/5?", choices: ["2/3", "3/5", "They are equal", "Not enough information"], answer: "2/3"
  },
  {
    id: "FR5-02", grade: 5, skill: "fractions", difficulty: 0.68,
    prereq: ["fractions"], misconception: "common_denominator", template: "fraction_add",
    prompt: "What is 1/2 + 1/4?", choices: ["3/4", "2/6", "1/6", "2/4"], answer: "3/4"
  },
  {
    id: "RAT5-01", grade: 5, skill: "ratios", difficulty: 0.62,
    prereq: ["multiplication"], misconception: "ratio_order", template: "ratio_basic",
    prompt: "A basket has 2 red apples for every 3 green apples. What is the ratio of red apples to green apples?",
    choices: ["2:3", "3:2", "2:5", "5:2"], answer: "2:3"
  },

  // ---------------- GRADE 6 ----------------
  {
    id: "RAT6-01", grade: 6, skill: "ratios", difficulty: 0.72,
    prereq: ["ratios"], misconception: "unit_rate", template: "ratio_basic",
    prompt: "A recipe uses 2 cups of flour for every 3 cups of water. What is the ratio of flour to water?",
    choices: ["2:3", "3:2", "2:5", "5:2"], answer: "2:3"
  },
  {
    id: "RAT6-02", grade: 6, skill: "ratios", difficulty: 0.76,
    prereq: ["ratios"], misconception: "proportional_scaling", template: "ratio_scaling",
    prompt: "If 2 notebooks cost $6, how much do 5 notebooks cost at the same rate?",
    choices: ["$10", "$12", "$15", "$18"], answer: "$15"
  },
  {
    id: "ALG6-01", grade: 6, skill: "expressions", difficulty: 0.74,
    prereq: ["multiplication"], misconception: "distributive_property", template: "expression_distribute",
    prompt: "Which expression is equivalent to 3(x − 4) + 2x?",
    choices: ["5x − 4", "5x − 12", "6x − 12", "3x − 2"], answer: "5x − 12"
  },
  {
    id: "FR6-01", grade: 6, skill: "fractions", difficulty: 0.75,
    prereq: ["fractions"], misconception: "equivalence", template: "fraction_equivalent",
    prompt: "Which fraction is equivalent to 2/3?", choices: ["6/9", "4/9", "3/9", "5/9"], answer: "6/9"
  },
  {
    id: "FR6-02", grade: 6, skill: "fractions", difficulty: 0.82,
    prereq: ["fractions"], misconception: "fraction_operations", template: "fraction_add",
    prompt: "What is 2/3 + 1/6?", choices: ["3/9", "3/6", "5/6", "1 1/6"], answer: "5/6"
  },
  {
    id: "GEO6-01", grade: 6, skill: "geometry", difficulty: 0.68,
    prereq: ["number_sense"], misconception: "area_vs_perimeter", template: "geometry_area",
    prompt: "A rectangle is 5 units long and 3 units wide. What is its area?",
    choices: ["8", "15", "16", "30"], answer: "15"
  },
  {
    id: "STAT6-01", grade: 6, skill: "statistics", difficulty: 0.70,
    prereq: ["number_sense"], misconception: "mean_vs_sum", template: "stats_mean",
    prompt: "What is the mean of 4, 6, and 8?", choices: ["5", "6", "7", "18"], answer: "6"
  },

  // ---------------- GRADE 7 / STRETCH ----------------
  {
    id: "ALG7-01", grade: 7, skill: "expressions", difficulty: 0.84,
    prereq: ["expressions"], misconception: "equation_solving", template: "equation_solve_mc",
    prompt: "Solve: 3x + 5 = 20.", choices: ["3", "5", "7", "15"], answer: "5"
  },
  {
    id: "PROP7-01", grade: 7, skill: "proportional_reasoning", difficulty: 0.86,
    prereq: ["ratios"], misconception: "proportional_scaling", template: "proportional_speed",
    prompt: "A car travels 180 miles in 3 hours at a constant speed. How far will it travel in 5 hours?",
    choices: ["240", "270", "300", "360"], answer: "300"
  },
  {
    id: "ALG7-02", grade: 7, skill: "equations", difficulty: 0.90,
    prereq: ["expressions"], misconception: "inverse_operations", template: "equation_solve_sa",
    prompt: "If 2x − 7 = 15, what is x?", type: "short_answer", answer: "11"
  },
  {
    id: "FR7-01", grade: 7, skill: "fractions", difficulty: 0.88,
    prereq: ["fractions"], misconception: "fraction_division", template: "fraction_division",
    prompt: "What is 3/4 ÷ 1/2?", choices: ["3/8", "1", "1 1/2", "2"], answer: "1 1/2"
  },

  // ---------------- GRADE 8 / ADVANCED STRETCH ----------------
  {
    id: "ALG8-01", grade: 8, skill: "equations", difficulty: 0.92,
    prereq: ["equations"], misconception: "variables_both_sides", template: "linear_two_sides",
    prompt: "Solve: 5x + 3 = 2x + 18.", choices: ["3", "5", "6", "7"], answer: "5"
  },
  {
    id: "EXP8-01", grade: 8, skill: "exponents", difficulty: 0.90,
    prereq: ["multiplication"], misconception: "exponent_as_multiplication", template: "exponent_eval",
    prompt: "What is 4^3?", choices: ["12", "64", "16", "81"], answer: "64"
  },
  {
    id: "GEO8-01", grade: 8, skill: "geometry", difficulty: 0.94,
    prereq: ["number_sense"], misconception: "pythagorean", template: "pythagorean",
    prompt: "A right triangle has legs of 3 and 4. What is the length of the hypotenuse?",
    choices: ["5", "7", "6", "12"], answer: "5"
  },
  {
    id: "PROP8-01", grade: 8, skill: "proportional_reasoning", difficulty: 0.90,
    prereq: ["proportional_reasoning"], misconception: "proportional_scaling", template: "proportional_speed",
    prompt: "A car travels 240 miles in 4 hours at a constant speed. How far will it travel in 6 hours?",
    choices: ["300", "360", "320", "420"], answer: "360"
  }
];

const SKILL_LABELS = {
  number_sense: "Number Sense",
  addition: "Addition",
  subtraction: "Subtraction",
  multiplication: "Multiplication & Division",
  fractions: "Fractions",
  decimals: "Decimals",
  word_problems: "Word Problems",
  ratios: "Ratios",
  expressions: "Expressions",
  equations: "Equations",
  exponents: "Exponents & Powers",
  proportional_reasoning: "Proportional Reasoning",
  geometry: "Geometry",
  statistics: "Statistics"
};

const SKILL_PREREQS = {
  addition: ["number_sense"],
  subtraction: ["number_sense"],
  multiplication: ["number_sense", "addition"],
  fractions: ["number_sense"],
  decimals: ["place_value", "number_sense"],
  word_problems: ["number_sense", "multiplication"],
  ratios: ["multiplication"],
  expressions: ["multiplication"],
  equations: ["expressions"],
  exponents: ["multiplication"],
  proportional_reasoning: ["ratios"],
  geometry: ["number_sense"],
  statistics: ["number_sense"]
};

function normalizeAnswer(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/\$/g, "")
    .replace(/\s+/g, " ");
}

function isCorrect(question, response) {
  return normalizeAnswer(response) === normalizeAnswer(question.answer);
}

// ---------------------------------------------------------------------------
// QUESTION GENERATION (templates)
//
// Each concept in QUESTION_BANK names a `template`. When a concept is chosen,
// we generate a concrete question from that template using a per-assessment
// seed. This means:
//   - retaking the assessment gives different numbers for the SAME concepts
//   - difficulty scales the magnitudes, so the router's harder/easier choices
//     produce genuinely harder/easier items
//   - scoring stays deterministic: the generator computes the answer, never AI
// ---------------------------------------------------------------------------

// Seeded PRNG (mulberry32) — deterministic given a seed.
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashStr(str) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
function makeSeed() { return (Math.random() * 0xffffffff) >>> 0; }

function randInt(rng, lo, hi) { return lo + Math.floor(rng() * (hi - lo + 1)); }
function pick(rng, arr) { return arr[Math.floor(rng() * arr.length)]; }
function shuffle(rng, arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}
function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { [a, b] = [b, a % b]; } return a || 1; }
// Reduced fraction as a display string; whole numbers and mixed numbers handled.
function fracStr(n, d) {
  const g = gcd(n, d); n /= g; d /= g;
  if (d === 1) return String(n);
  if (n > d) { const w = Math.floor(n / d), r = n % d; return r === 0 ? String(w) : `${w} ${r}/${d}`; }
  return `${n}/${d}`;
}

const MINUS = "−"; // U+2212, matching the static bank's glyph

// ---------------------------------------------------------------------------
// ERROR DIAGNOSIS
//
// Every wrong answer is one of two kinds (per the two-student framing):
//   - "procedural": the child knew the method but slipped (miscounted, off by
//     one/ten). Same right idea, wrong execution.
//   - "conceptual": the child's mental model is off (added numerators AND
//     denominators, used perimeter for area, reversed a ratio). A misconception.
//
// Each distractor a template offers is tagged with an error CODE. When the
// child picks that distractor we look the code up here to explain WHY it was
// wrong and which kind of error it was.
// ---------------------------------------------------------------------------
const ERROR_NOTES = {
  // Procedural slips — right method, wrong execution.
  off_by_one:       { type: "procedural", note: "a small arithmetic slip (off by one)" },
  off_by_ten:       { type: "procedural", note: "a place-value / regrouping slip (off by ten)" },
  computation_slip: { type: "procedural", note: "a computation slip while carrying out the steps" },
  fact_fluency:     { type: "procedural", note: "a multiplication-fact recall slip" },

  // Conceptual errors — the underlying idea is off.
  add_across:                  { type: "conceptual", note: "added the numerators and the denominators" },
  kept_one_denominator:        { type: "conceptual", note: "kept one denominator instead of finding a common one" },
  subtracted_instead:          { type: "conceptual", note: "subtracted instead of the required operation" },
  equiv_added_constant:        { type: "conceptual", note: "added the same amount to top and bottom instead of multiplying" },
  equiv_scaled_denominator:    { type: "conceptual", note: "scaled only the denominator, not the numerator" },
  div_multiplied:              { type: "conceptual", note: "multiplied instead of dividing (didn't use the reciprocal)" },
  div_reciprocal_answer:       { type: "conceptual", note: "gave the reciprocal of the correct answer" },
  chose_addition:              { type: "conceptual", note: "read “groups of” as addition, not multiplication" },
  chose_division:              { type: "conceptual", note: "chose division instead of multiplication" },
  used_perimeter:              { type: "conceptual", note: "found the perimeter instead of the area" },
  added_dimensions:            { type: "conceptual", note: "added the two sides instead of multiplying" },
  gave_sum:                    { type: "conceptual", note: "gave the total instead of the mean" },
  gave_median:                 { type: "conceptual", note: "gave the middle value instead of the mean" },
  exponent_times_base:         { type: "conceptual", note: "multiplied base × exponent instead of repeated multiplication" },
  added_the_legs:              { type: "conceptual", note: "added the legs instead of using the Pythagorean theorem" },
  reversed_ratio:              { type: "conceptual", note: "reversed the order of the ratio" },
  part_to_whole:               { type: "conceptual", note: "compared a part to the whole instead of part to part" },
  additive_not_multiplicative: { type: "conceptual", note: "added a constant instead of scaling proportionally" },
  added_not_multiplied:        { type: "conceptual", note: "added the quantities instead of multiplying" },
  distribute_forgot:           { type: "conceptual", note: "didn't multiply the number through the parentheses" },
  distribute_sign:             { type: "conceptual", note: "made a sign error when distributing" },
  place_value_decimal:         { type: "conceptual", note: "confused the decimal place value" },
  inverse_operations:          { type: "conceptual", note: "didn't correctly undo the operations" },
  variables_both_sides:        { type: "conceptual", note: "didn't gather the variable terms onto one side" },
  fraction_size:               { type: "conceptual", note: "misjudged the size of the fraction" },
  fraction_comparison:         { type: "conceptual", note: "compared the two fractions incorrectly" }
};

// Resolve an error code to { code, type, note }; unknown codes read as conceptual.
function diagnose(code) {
  if (!code) return null;
  const e = ERROR_NOTES[code];
  return e ? { code, type: e.type, note: e.note }
           : { code, type: "conceptual", note: String(code).replace(/_/g, " ") };
}

/**
 * Build a shuffled 4-option multiple choice. Distractors are tried in priority
 * order; each may be a plain value or { v, error } to tag the mistake it
 * represents. Duplicates and any value equal to the correct answer are dropped.
 * Returns a `diagnostics` map: choice string -> error code.
 */
function mcq(rng, correct, distractors) {
  correct = String(correct);
  const seen = new Set([correct]);
  const out = [], diagnostics = {};
  for (const d of distractors) {
    const obj = d && typeof d === "object";
    const s = obj ? (d.v == null ? null : String(d.v)) : (d == null ? null : String(d));
    if (s && !seen.has(s)) { seen.add(s); out.push(s); if (obj && d.error) diagnostics[s] = d.error; }
    if (out.length >= 3) break;
  }
  let pad = 1;
  while (out.length < 3) {
    // Nudge the number embedded in the answer (handles "$36", "40", "5x − 6").
    const m = correct.match(/^(\D*?)(\d+)(\D*)$/);
    const cand = m ? `${m[1]}${Number(m[2]) + pad}${m[3]}` : `${correct} (${pad})`;
    if (!seen.has(cand)) { seen.add(cand); out.push(cand); diagnostics[cand] = "computation_slip"; }
    if (++pad > 99) break;
  }
  return { choices: shuffle(rng, [correct, ...out]), answer: correct, diagnostics };
}

/**
 * Build exactly three distinct fraction distractors (as display strings), none
 * equal to the correct value. Pool entries are [n, d, errorCode?]. Guarantees a
 * full set by nudging the numerator (those pads read as computation slips).
 * Returns { list, diagnostics }.
 */
function fracDistractors(rng, correctN, correctD, pool) {
  const seen = new Set([fracStr(correctN, correctD)]);
  const out = [], diag = {};
  const add = (n, d, error) => {
    if (n <= 0 || d <= 0 || out.length >= 3) return; // keep first 3 in priority order
    const s = fracStr(n, d);
    if (!seen.has(s)) { seen.add(s); out.push(s); if (error) diag[s] = error; }
  };
  for (const [n, d, error] of pool) { add(n, d, error); if (out.length >= 3) break; }
  let k = 1;
  while (out.length < 3 && k < 60) { add(correctN + k, correctD, "computation_slip"); add(correctN - k, correctD, "computation_slip"); k++; }
  const list = shuffle(rng, out); // shuffle only for display order
  const diagnostics = {};
  for (const s of list) if (diag[s]) diagnostics[s] = diag[s];
  return { list, diagnostics };
}

const TEMPLATES = {
  number_compare_greatest(rng, d) {
    const digits = d < 0.2 ? 2 : d < 0.5 ? 3 : d < 0.75 ? 4 : 5;
    const lo = Math.pow(10, digits - 1), hi = Math.pow(10, digits) - 1;
    const nums = new Set();
    while (nums.size < 4) nums.add(randInt(rng, lo, hi));
    const arr = [...nums];
    return { prompt: "Which number is greatest?", choices: shuffle(rng, arr.map(String)), answer: String(Math.max(...arr)) };
  },

  addition_basic(rng, d) {
    const hi = d < 0.2 ? 12 : d < 0.4 ? 99 : 999;
    const a = randInt(rng, 2, hi), b = randInt(rng, 2, hi);
    const { choices, answer, diagnostics } = mcq(rng, a + b,
      [{ v: a + b + 10, error: "off_by_ten" }, { v: a + b + 1, error: "off_by_one" }, { v: a + b - 1, error: "off_by_one" }]);
    return { prompt: `What is ${a} + ${b}?`, choices, answer, diagnostics };
  },

  subtraction_basic(rng, d) {
    const hi = d < 0.2 ? 18 : d < 0.4 ? 99 : 999;
    const a = randInt(rng, 6, hi), b = randInt(rng, 2, a - 1);
    const ans = a - b;
    const { choices, answer, diagnostics } = mcq(rng, ans,
      [{ v: ans + 10, error: "off_by_ten" }, { v: ans + 1, error: "off_by_one" }, { v: ans - 1, error: "off_by_one" }]);
    return { prompt: `What is ${a} ${MINUS} ${b}?`, choices, answer, diagnostics };
  },

  exponent_eval(rng, d) {
    const base = randInt(rng, 2, 6), exp = randInt(rng, 2, 3);
    const ans = Math.pow(base, exp);
    const { choices, answer, diagnostics } = mcq(rng, ans,
      [{ v: base * exp, error: "exponent_times_base" }, { v: ans + base, error: "computation_slip" }, { v: ans - base, error: "computation_slip" }, { v: ans + 1, error: "off_by_one" }]);
    return { prompt: `What is ${base}^${exp}?`, choices, answer, diagnostics };
  },

  pythagorean(rng, d) {
    const [a, b, c] = pick(rng, [[3, 4, 5], [6, 8, 10], [5, 12, 13], [8, 15, 17], [9, 12, 15], [7, 24, 25]]);
    const { choices, answer, diagnostics } = mcq(rng, c,
      [{ v: a + b, error: "added_the_legs" }, { v: c + 1, error: "off_by_one" }, { v: c - 1, error: "off_by_one" }, { v: c + 2, error: "computation_slip" }]);
    return { prompt: `A right triangle has legs of ${a} and ${b}. What is the length of the hypotenuse?`, choices, answer, diagnostics };
  },

  linear_two_sides(rng, d) {
    const x = randInt(rng, 2, 9), a = randInt(rng, 3, 6), c = randInt(rng, 1, a - 1), b = randInt(rng, 1, 9);
    const rhs = (a - c) * x + b; // constant on the right so both sides are equal at x
    const { choices, answer, diagnostics } = mcq(rng, x,
      [{ v: x + 1, error: "off_by_one" }, { v: x - 1, error: "off_by_one" }, { v: x + 2, error: "variables_both_sides" }]);
    return { prompt: `Solve: ${a}x + ${b} = ${c}x + ${rhs}.`, choices, answer, diagnostics };
  },

  multiplication_meaning(rng, d) {
    const a = randInt(rng, 2, 9), b = randInt(rng, 2, 9);
    const { choices, answer, diagnostics } = mcq(rng, `${a} × ${b}`,
      [{ v: `${a} + ${b}`, error: "chose_addition" }, { v: `${b} ${MINUS} ${a}`, error: "subtracted_instead" }, { v: `${b} ÷ ${a}`, error: "chose_division" }, { v: `${a} ÷ ${b}`, error: "chose_division" }]);
    return { prompt: `Which equation represents ${a} groups of ${b}?`, choices, answer, diagnostics };
  },

  multiplication_fact(rng, d) {
    let a, b;
    if (d < 0.4) { a = randInt(rng, 2, 9); b = randInt(rng, 2, 9); }
    else if (d < 0.6) { a = randInt(rng, 6, 12); b = randInt(rng, 3, 9); }
    else { a = randInt(rng, 8, 15); b = randInt(rng, 4, 12); }
    return { prompt: `What is ${a} × ${b}?`, type: "short_answer", answer: String(a * b) };
  },

  fraction_compare_half(rng, d) {
    let cd = randInt(rng, 3, 8), cn;
    do { cn = randInt(rng, 1, cd - 1); } while (cn / cd <= 0.5);
    const correct = `${cn}/${cd}`;
    const dis = []; let guard = 0;
    while (dis.length < 3 && guard++ < 80) {
      const dd = randInt(rng, 3, 8), dn = randInt(rng, 1, dd - 1);
      if (dn / dd < 0.5) { const s = `${dn}/${dd}`; if (s !== correct && !dis.includes(s)) dis.push(s); }
    }
    const diagnostics = {}; for (const s of dis) diagnostics[s] = "fraction_size";
    return { prompt: "Which fraction is greater than 1/2?", choices: shuffle(rng, [correct, ...dis]), answer: correct, diagnostics };
  },

  fraction_equivalent(rng, d) {
    const b = randInt(rng, 2, 6);
    let a; do { a = randInt(rng, 1, b - 1); } while (gcd(a, b) !== 1);
    const k = randInt(rng, 2, 4);
    const { choices, answer, diagnostics } = mcq(rng, `${a * k}/${b * k}`,
      [{ v: `${a + k}/${b + k}`, error: "equiv_added_constant" }, { v: `${a}/${b * k}`, error: "equiv_scaled_denominator" }, `${a * k}/${b * (k + 1)}`, `${a * (k + 1)}/${b * k}`]);
    return { prompt: `Which fraction is equivalent to ${a}/${b}?`, choices, answer, diagnostics };
  },

  fraction_compare_two(rng, d) {
    let n1, d1, n2, d2;
    do {
      d1 = randInt(rng, 3, 8); n1 = randInt(rng, 1, d1 - 1);
      d2 = randInt(rng, 3, 8); n2 = randInt(rng, 1, d2 - 1);
    } while (Math.abs(n1 / d1 - n2 / d2) < 1e-9);
    const smaller = n1 / d1 > n2 / d2 ? `${n2}/${d2}` : `${n1}/${d1}`;
    const bigger = n1 / d1 > n2 / d2 ? `${n1}/${d1}` : `${n2}/${d2}`;
    return {
      prompt: `Which is greater, ${n1}/${d1} or ${n2}/${d2}?`,
      choices: [`${n1}/${d1}`, `${n2}/${d2}`, "They are equal", "Not enough information"],
      answer: bigger,
      diagnostics: { [smaller]: "fraction_comparison", "They are equal": "fraction_comparison", "Not enough information": "fraction_comparison" }
    };
  },

  fraction_add(rng, d) {
    let d1, d2;
    if (d < 0.6) { d1 = randInt(rng, 2, 6); d2 = d1 * randInt(rng, 1, 2); }
    else { d1 = randInt(rng, 2, 6); d2 = randInt(rng, 2, 8); }
    const n1 = randInt(rng, 1, d1 - 1), n2 = randInt(rng, 1, d2 - 1);
    const sumN = n1 * d2 + n2 * d1, sumD = d1 * d2;
    const { list, diagnostics } = fracDistractors(rng, sumN, sumD, [
      [n1 + n2, d1 + d2, "add_across"],
      [n1 + n2, Math.max(d1, d2), "kept_one_denominator"],
      [Math.abs(n1 * d2 - n2 * d1), sumD, "subtracted_instead"],
      [n1 * n2, sumD, "computation_slip"],
      [sumN, sumD * 2, "computation_slip"]
    ]);
    return { prompt: `What is ${fracStr(n1, d1)} + ${fracStr(n2, d2)}?`, choices: shuffle(rng, [fracStr(sumN, sumD), ...list]), answer: fracStr(sumN, sumD), diagnostics };
  },

  fraction_division(rng, d) {
    const d1 = randInt(rng, 2, 5), n1 = randInt(rng, 1, d1 - 1);
    const d2 = randInt(rng, 2, 4), n2 = randInt(rng, 1, d2 - 1);
    const rn = n1 * d2, rd = d1 * n2;
    const { list, diagnostics } = fracDistractors(rng, rn, rd, [
      [n1 * n2, d1 * d2, "div_multiplied"],
      [n1, d1, "computation_slip"],
      [rd, rn, "div_reciprocal_answer"],
      [rn, rd * 2, "computation_slip"]
    ]);
    return { prompt: `What is ${fracStr(n1, d1)} ÷ ${fracStr(n2, d2)}?`, choices: shuffle(rng, [fracStr(rn, rd), ...list]), answer: fracStr(rn, rd), diagnostics };
  },

  decimal_equiv(rng, d) {
    const n = randInt(rng, 1, 9);
    const { choices, answer, diagnostics } = mcq(rng, `${n}/10`,
      [{ v: `${n}/100`, error: "place_value_decimal" }, { v: `${n}/1000`, error: "place_value_decimal" }, `${100 + n}/1000`, { v: `${n}/2`, error: "place_value_decimal" }]);
    return { prompt: `Which number is the same as 0.${n}?`, choices, answer, diagnostics };
  },

  word_problem_multiply(rng, d) {
    const [container, item] = pick(rng, [["boxes", "pencils"], ["crates", "apples"], ["shelves", "books"], ["bags", "marbles"]]);
    const b = randInt(rng, 3, 9), p = randInt(rng, 10, 30);
    const { choices, answer, diagnostics } = mcq(rng, b * p,
      [{ v: b + p, error: "added_not_multiplied" }, { v: b * p - p, error: "computation_slip" }, { v: b * (p + 1), error: "computation_slip" }, { v: b * p + b, error: "computation_slip" }]);
    return { prompt: `There are ${b} ${container} with ${p} ${item} in each. How many ${item} are there in total?`, choices, answer, diagnostics };
  },

  ratio_basic(rng, d) {
    let x, y; do { x = randInt(rng, 2, 6); y = randInt(rng, 2, 6); } while (x === y);
    const [t1, t2] = pick(rng, [["red apples", "green apples"], ["cats", "dogs"], ["blue pens", "red pens"], ["boys", "girls"]]);
    const { choices, answer, diagnostics } = mcq(rng, `${x}:${y}`,
      [{ v: `${y}:${x}`, error: "reversed_ratio" }, { v: `${x}:${x + y}`, error: "part_to_whole" }, { v: `${x + y}:${y}`, error: "part_to_whole" }]);
    return { prompt: `A group has ${x} ${t1} for every ${y} ${t2}. What is the ratio of ${t1} to ${t2}?`, choices, answer, diagnostics };
  },

  ratio_scaling(rng, d) {
    const u = randInt(rng, 2, 5), n = randInt(rng, 2, 4), k = randInt(rng, 2, 5);
    const m = n * k, cost = n * u, ans = m * u;
    const item = pick(rng, ["notebooks", "apples", "markers", "tickets"]);
    const { choices, answer, diagnostics } = mcq(rng, `$${ans}`,
      [{ v: `$${cost + u}`, error: "additive_not_multiplicative" }, { v: `$${ans - u}`, error: "off_by_one" }, { v: `$${ans + u}`, error: "off_by_one" }, { v: `$${m + cost}`, error: "additive_not_multiplicative" }]);
    return { prompt: `If ${n} ${item} cost $${cost}, how much do ${m} ${item} cost at the same rate?`, choices, answer, diagnostics };
  },

  proportional_speed(rng, d) {
    const r = randInt(rng, 4, 7) * 10, t1 = randInt(rng, 2, 4), t2 = t1 + randInt(rng, 1, 3);
    const d1 = r * t1, ans = r * t2;
    const { choices, answer, diagnostics } = mcq(rng, ans,
      [{ v: ans - r, error: "off_by_one" }, { v: ans + r, error: "off_by_one" }, { v: d1 + t2, error: "additive_not_multiplicative" }]);
    return { prompt: `A car travels ${d1} miles in ${t1} hours at a constant speed. How far will it travel in ${t2} hours?`, choices, answer, diagnostics };
  },

  expression_distribute(rng, d) {
    const a = randInt(rng, 2, 4), b = randInt(rng, 2, 6), c = randInt(rng, 1, 3);
    const { choices, answer, diagnostics } = mcq(rng, `${a + c}x ${MINUS} ${a * b}`,
      [{ v: `${a + c}x ${MINUS} ${b}`, error: "distribute_forgot" }, { v: `${a * c}x ${MINUS} ${a * b}`, error: "distribute_forgot" }, { v: `${a + c}x + ${a * b}`, error: "distribute_sign" }, { v: `${a}x ${MINUS} ${a * b}`, error: "distribute_forgot" }]);
    const cTerm = c === 1 ? "x" : `${c}x`;
    return { prompt: `Which expression is equivalent to ${a}(x ${MINUS} ${b}) + ${cTerm}?`, choices, answer, diagnostics };
  },

  equation_solve_mc(rng, d) {
    const x = randInt(rng, 2, 9), a = randInt(rng, 2, 5), b = randInt(rng, 1, 12);
    const { choices, answer, diagnostics } = mcq(rng, x,
      [{ v: x + 1, error: "off_by_one" }, { v: x - 1, error: "off_by_one" }, { v: x + 2, error: "computation_slip" }]);
    return { prompt: `Solve: ${a}x + ${b} = ${a * x + b}.`, choices, answer, diagnostics };
  },

  equation_solve_sa(rng, d) {
    const x = randInt(rng, 3, 12), a = randInt(rng, 2, 5), b = randInt(rng, 3, 15);
    return { prompt: `If ${a}x ${MINUS} ${b} = ${a * x - b}, what is x?`, type: "short_answer", answer: String(x) };
  },

  geometry_area(rng, d) {
    const L = randInt(rng, 3, 12), W = randInt(rng, 2, 9);
    const { choices, answer, diagnostics } = mcq(rng, L * W,
      [{ v: 2 * (L + W), error: "used_perimeter" }, { v: L + W, error: "added_dimensions" }, { v: L * W - L, error: "computation_slip" }]);
    return { prompt: `A rectangle is ${L} units long and ${W} units wide. What is its area?`, choices, answer, diagnostics };
  },

  stats_mean(rng, d) {
    let nums, sum;
    do { nums = [randInt(rng, 2, 12), randInt(rng, 2, 12), randInt(rng, 2, 12)]; sum = nums[0] + nums[1] + nums[2]; } while (sum % 3 !== 0);
    const sorted = [...nums].sort((a, b) => a - b);
    const { choices, answer, diagnostics } = mcq(rng, sum / 3,
      [{ v: sum, error: "gave_sum" }, { v: sorted[1], error: "gave_median" }, { v: sum / 3 + 1, error: "off_by_one" }]);
    return { prompt: `What is the mean of ${nums.join(", ")}?`, choices, answer, diagnostics };
  }
};

/**
 * Turn a concept blueprint into a concrete question for this assessment.
 * Cached per concept id, so a concept always renders the same instance within
 * one run (stable if re-shown) but differs across runs via the seed.
 */
function materialize(state, blueprint) {
  if (!blueprint) return null;
  if (state.generated[blueprint.id]) return state.generated[blueprint.id];
  const tpl = blueprint.template && TEMPLATES[blueprint.template];
  let instance;
  if (tpl) {
    const rng = mulberry32(hashStr(`${blueprint.id}:${state.seed}`));
    const gen = tpl(rng, blueprint.difficulty);
    instance = {
      id: blueprint.id, grade: blueprint.grade, skill: blueprint.skill,
      difficulty: blueprint.difficulty, prereq: blueprint.prereq,
      misconception: blueprint.misconception,
      type: gen.type || "multiple_choice",
      prompt: gen.prompt, choices: gen.choices || null, answer: gen.answer,
      diagnostics: gen.diagnostics || {}
    };
  } else {
    instance = blueprint; // static fallback for concepts without a template
  }
  state.generated[blueprint.id] = instance;
  return instance;
}

function createSkillState() {
  return {
    evidence: 0,
    correct: 0,
    mastery: 0.50,
    lastResult: null,
    gradesSeen: new Set(),
    misconceptions: [],
    // Specific diagnosed errors for this skill: [{ code, type, note, count }].
    observedErrors: [],
    proceduralCount: 0,
    conceptualCount: 0
  };
}

function createAssessment(currentGrade, options = {}) {
  return {
    currentGrade,
    minQuestions: options.minQuestions ?? 16,
    maxQuestions: options.maxQuestions ?? 26,
    // Seed drives question generation; random by default so retakes differ,
    // but can be pinned via options.seed for reproducible runs/debugging.
    seed: options.seed ?? makeSeed(),
    generated: {},
    questionCount: 0,
    globalAbility: 0.50,
    mastery: {},
    seen: new Set(),
    history: [],
    startedAt: new Date().toISOString()
  };
}

function getSkillState(state, skill) {
  if (!state.mastery[skill]) state.mastery[skill] = createSkillState();
  return state.mastery[skill];
}

/**
 * Bayesian-inspired lightweight update.
 *
 * This is NOT a validated educational measurement model. It is a prototype
 * routing model. The evidence count is kept separately so the report can say
 * "based on 3 questions" instead of pretending the estimate is exact.
 */
function updateSkillMastery(state, question, correct, diagnosis) {
  const skillState = getSkillState(state, question.skill);
  const prior = skillState.mastery;
  const reliability = Math.min(0.30, 0.12 + skillState.evidence * 0.04);
  const observation = correct ? 1 : 0;

  skillState.mastery = prior + reliability * (observation - prior);
  skillState.evidence += 1;
  skillState.correct += correct ? 1 : 0;
  skillState.lastResult = correct;
  skillState.gradesSeen.add(question.grade);

  if (!correct) {
    if (question.misconception && !skillState.misconceptions.includes(question.misconception)) {
      skillState.misconceptions.push(question.misconception);
    }
    if (diagnosis) {
      const existing = skillState.observedErrors.find(e => e.code === diagnosis.code);
      if (existing) existing.count += 1;
      else skillState.observedErrors.push({ ...diagnosis, count: 1 });
      if (diagnosis.type === "procedural") skillState.proceduralCount += 1;
      else skillState.conceptualCount += 1;
    }
  }
}

function updateGlobalAbility(state, correct) {
  const change = correct ? 0.045 : -0.055;
  state.globalAbility = Math.max(0.05, Math.min(0.95, state.globalAbility + change));
}

function recentSkillCount(state, skill, n = 4) {
  return state.history.slice(-n).filter(h => h.skill === skill).length;
}

function hasWeakPrerequisite(state, question) {
  const prereqs = question.prereq || SKILL_PREREQS[question.skill] || [];
  return prereqs.some(prereq => {
    const s = state.mastery[prereq];
    return s && s.evidence >= 2 && s.mastery < 0.38;
  });
}

/**
 * Select the next question by maximizing diagnostic value.
 *
 * Priority order is encoded as a score, not a hard if/else tree:
 *   - current-grade coverage
 *   - uncertainty in a skill
 *   - foundation checks when something looks weak
 *   - stretch questions when a skill looks strong
 *   - difficulty near current ability
 *   - prerequisite health
 *   - avoid repetitive questions
 */
function chooseNextQuestion(state) {
  const candidates = QUESTION_BANK.filter(q => !state.seen.has(q.id));
  if (!candidates.length) return null;

  const currentGrade = state.currentGrade;

  // First-class diagnostic rule: when a skill has two pieces of negative
  // evidence, immediately look for a simpler item in the same skill. This is
  // what lets the assessment distinguish "Grade 6 concept is hard" from
  // "the Grade 4/5 foundation underneath it is shaky."
  const foundationTargets = Object.entries(state.mastery)
    .filter(([skill, s]) => s.evidence >= 2 && s.mastery < 0.40)
    .map(([skill]) => skill);

  const foundationCandidate = candidates
    .filter(q => foundationTargets.includes(q.skill) && q.grade < currentGrade)
    .sort((a, b) => a.grade - b.grade || a.difficulty - b.difficulty)[0];

  if (foundationCandidate) return materialize(state, foundationCandidate);

  function score(q) {
    const skill = getSkillState(state, q.skill);
    const mastery = skill.mastery;

    // Highest uncertainty is around the middle: we learn more from clarifying
    // an uncertain skill than from asking a fifth easy question about a skill
    // we already know is strong.
    const uncertainty = 1 - Math.min(1, Math.abs(mastery - 0.50) * 2);

    let gradeFit;
    if (q.grade === currentGrade) gradeFit = 1.00;
    else if (q.grade === currentGrade - 1) gradeFit = 0.82;
    else if (q.grade === currentGrade + 1) gradeFit = 0.72;
    else gradeFit = 0.35;

    // Once we have evidence that a skill is strong, a harder item can test
    // readiness beyond the current grade.
    const stretch = q.grade > currentGrade && mastery >= 0.68 ? 0.70 : 0;

    // If a current-grade skill looks weak, deliberately go downward to find
    // whether a prerequisite/foundation issue explains the weakness.
    const foundation = q.grade < currentGrade && mastery < 0.42 ? 0.85 : 0;

    const targetDifficulty = 0.30 + state.globalAbility * 0.62;
    const difficultyFit = 1 - Math.min(1, Math.abs(q.difficulty - targetDifficulty));

    const repetitionPenalty = recentSkillCount(state, q.skill) * 0.28;
    const prerequisitePenalty = hasWeakPrerequisite(state, q) ? 0.25 : 0;

    // Coverage bonus: current-grade skills with no evidence are valuable.
    const coverage = skill.evidence === 0 ? 0.80 : 0;

    // If the child has just missed a skill, one nearby question is valuable,
    // but a third immediate question is usually excessive.
    const clarification = skill.lastResult === false && skill.evidence <= 2 ? 0.55 : 0;

    return (
      uncertainty * 0.95 +
      gradeFit * 0.75 +
      stretch +
      foundation +
      difficultyFit * 0.65 +
      coverage +
      clarification -
      repetitionPenalty -
      prerequisitePenalty
    );
  }

  const best = candidates
    .map(q => ({ q, score: score(q) }))
    .sort((a, b) => b.score - a.score)[0].q;
  return materialize(state, best);
}

function answerQuestion(state, question, response) {
  const correct = isCorrect(question, response);

  // Diagnose WHY it was wrong: prefer the specific error tagged on the chosen
  // distractor; fall back to the concept's own misconception. Correct answers
  // and short-answer items with no match produce no diagnosis.
  let diagnosis = null;
  if (!correct) {
    const code = (question.diagnostics && question.diagnostics[String(response)]) || question.misconception;
    diagnosis = diagnose(code);
  }

  state.seen.add(question.id);
  state.history.push({
    questionId: question.id,
    skill: question.skill,
    grade: question.grade,
    difficulty: question.difficulty,
    correct,
    response,
    diagnosis
  });

  updateSkillMastery(state, question, correct, diagnosis);
  updateGlobalAbility(state, correct);
  state.questionCount += 1;

  return correct;
}

/**
 * Stop only after minimum evidence is collected and the picture is sufficiently
 * stable. Production should use a validated stopping rule after pilot testing.
 */
function shouldStop(state) {
  if (state.questionCount < state.minQuestions) return false;
  if (state.questionCount >= state.maxQuestions) return true;

  const currentGradeSkills = [...new Set(
    QUESTION_BANK.filter(q => q.grade === state.currentGrade).map(q => q.skill)
  )];

  const covered = currentGradeSkills.filter(skill => {
    const s = state.mastery[skill];
    return s && s.evidence >= 1;
  }).length;

  const sufficientlyCovered = covered >= Math.min(5, currentGradeSkills.length);

  // If we have both weak and strong evidence, the assessment has more value in
  // exploring foundations/stretch than continuing to sample the same level.
  const hasFoundationSignal = Object.values(state.mastery).some(s => s.mastery < 0.38 && s.evidence >= 2);
  const hasStretchSignal = Object.values(state.mastery).some(s => s.mastery > 0.70 && s.evidence >= 2);

  return sufficientlyCovered && (hasFoundationSignal || hasStretchSignal);
}

function classify(skillState) {
  if (!skillState || skillState.evidence === 0) return "Not assessed";
  if (skillState.mastery >= 0.70) return "Strong evidence";
  if (skillState.mastery >= 0.50) return "Developing / likely on track";
  if (skillState.mastery >= 0.36) return "Worth a closer look";
  return "Focus area";
}

function gradeBandForSkill(state, skill) {
  const evidence = state.history.filter(h => h.skill === skill);
  if (!evidence.length) return null;

  const highestSuccessfulGrade = Math.max(
    ...evidence.filter(h => h.correct).map(h => h.grade),
    -Infinity
  );
  const lowestFailedGrade = Math.min(
    ...evidence.filter(h => !h.correct).map(h => h.grade),
    Infinity
  );

  return {
    highestSuccessfulGrade: Number.isFinite(highestSuccessfulGrade) ? highestSuccessfulGrade : null,
    lowestFailedGrade: Number.isFinite(lowestFailedGrade) ? lowestFailedGrade : null
  };
}

function buildSnapshot(state) {
  const skills = Object.entries(state.mastery).map(([skill, s]) => ({
    skill,
    label: SKILL_LABELS[skill] || skill,
    mastery: Number(s.mastery.toFixed(2)),
    evidence: s.evidence,
    correct: s.correct,
    classification: classify(s),
    gradesSeen: [...s.gradesSeen].sort((a, b) => a - b),
    gradeEvidence: gradeBandForSkill(state, skill),
    possibleMisconceptions: s.misconceptions,
    // Specific diagnosed errors, most frequent first, each with its type.
    diagnosedErrors: [...s.observedErrors].sort((a, b) => b.count - a.count),
    proceduralCount: s.proceduralCount,
    conceptualCount: s.conceptualCount,
    // A skill's dominant error kind, when it has wrong answers.
    errorProfile: s.conceptualCount === 0 && s.proceduralCount === 0 ? null
      : s.conceptualCount > s.proceduralCount ? "conceptual"
      : s.proceduralCount > s.conceptualCount ? "procedural" : "mixed"
  }));

  // Overall error mix across the whole assessment.
  const wrong = state.history.filter(h => !h.correct && h.diagnosis);
  const errorMix = {
    procedural: wrong.filter(h => h.diagnosis.type === "procedural").length,
    conceptual: wrong.filter(h => h.diagnosis.type === "conceptual").length
  };

  return {
    currentGrade: state.currentGrade,
    questionsAnswered: state.questionCount,
    globalAbility: Number(state.globalAbility.toFixed(2)),
    strongAreas: skills.filter(s => s.mastery >= 0.70).map(s => s.label),
    areasToReview: skills.filter(s => s.mastery >= 0.36 && s.mastery < 0.50).map(s => s.label),
    focusAreas: skills.filter(s => s.mastery < 0.36).map(s => s.label),
    readyForMore: skills.some(s => s.gradesSeen.some(g => g > state.currentGrade) && s.mastery >= 0.70),
    errorMix,
    skills
  };
}

// -----------------------------------------------------------------------------
// DEMO STUDENTS
// -----------------------------------------------------------------------------

/**
 * These profiles are synthetic. They are useful for testing routing behavior,
 * not for validating the assessment scientifically.
 */
const PROFILES = {
  strong: {
    label: "Strong / ready for stretch",
    answer(question) {
      return question.answer;
    }
  },
  "fractions-gap": {
    label: "Mostly solid, fractions need support",
    answer(question) {
      if (question.skill === "fractions" && question.difficulty >= 0.62) return "wrong";
      return question.answer;
    }
  },
  "foundation-gap": {
    label: "Current-grade work masks multiplication foundation gap",
    answer(question) {
      if (["multiplication", "word_problems", "ratios"].includes(question.skill)) return "wrong";
      return question.answer;
    }
  }
};

function runDemo(profileName = "fractions-gap", currentGrade = 6) {
  const profile = PROFILES[profileName] || PROFILES["fractions-gap"];
  const state = createAssessment(currentGrade);
  let question = chooseNextQuestion(state);

  console.log(`\nBEYOND THE GRADE — ${profile.label.toUpperCase()}`);
  console.log(`Starting grade: ${currentGrade}\n`);

  while (question && !shouldStop(state)) {
    const response = profile.answer(question);
    const correct = answerQuestion(state, question, response);
    const next = chooseNextQuestion(state);

    console.log(
      `Q${state.questionCount.toString().padStart(2, "0")}  ` +
      `G${question.grade}  |  ${SKILL_LABELS[question.skill]}  |  ` +
      `${correct ? "✓" : "✗"}  |  next → ${next ? `G${next.grade} ${SKILL_LABELS[next.skill]}` : "stop"}`
    );

    question = next;
  }

  const snapshot = buildSnapshot(state);

  console.log("\nMATH SNAPSHOT\n");
  console.log(`Questions: ${snapshot.questionsAnswered}`);
  console.log(`Strong: ${snapshot.strongAreas.join(", ") || "none yet"}`);
  console.log(`Review: ${snapshot.areasToReview.join(", ") || "none"}`);
  console.log(`Focus: ${snapshot.focusAreas.join(", ") || "none"}`);
  console.log(`Ready for more: ${snapshot.readyForMore ? "yes" : "not enough evidence"}`);

  console.log("\nSkill evidence:");
  for (const skill of snapshot.skills) {
    console.log(
      `  ${skill.label.padEnd(28)} ` +
      `${skill.classification.padEnd(27)} ` +
      `evidence=${skill.evidence} ` +
      `mastery=${skill.mastery}`
    );
  }

  return state;
}

if (require.main === module) {
  runDemo(process.argv[2] || "fractions-gap");
}

module.exports = {
  QUESTION_BANK,
  SKILL_LABELS,
  TEMPLATES,
  createAssessment,
  chooseNextQuestion,
  materialize,
  answerQuestion,
  shouldStop,
  buildSnapshot,
  classify,
  runDemo,
  PROFILES
};
