const assert = require('assert');
const {
  createAssessment,
  chooseNextQuestion,
  answerQuestion,
  materialize,
  buildSnapshot,
  QUESTION_BANK
} = require('./beyond-the-grade-adaptive');

function answer(state, id, response) {
  const q = QUESTION_BANK.find(x => x.id === id);
  assert(q, `Missing question ${id}`);
  answerQuestion(state, q, response);
}

// 1. The engine starts at the child's current grade.
{
  const state = createAssessment(6);
  const q = chooseNextQuestion(state);
  assert.strictEqual(q.grade, 6);
}

// 2. A weak skill should cause a lower-grade diagnostic check.
{
  const state = createAssessment(6);
  answer(state, 'OP4-02', 'wrong');
  answer(state, 'OP4-01', 'wrong');
  const q = chooseNextQuestion(state);
  assert(q.grade <= 5 || q.skill === 'multiplication', 'Expected foundation clarification');
}

// 3. Strong evidence should allow the engine to explore above grade.
{
  const state = createAssessment(6);
  answer(state, 'ALG6-01', '5x − 12');
  answer(state, 'RAT6-01', '2:3');
  answer(state, 'FR6-01', 'Both 6/9 and 8/12');
  answer(state, 'FR6-02', '5/6');
  const q = chooseNextQuestion(state);
  assert(q.grade >= 6);
}

// 4. Snapshot keeps evidence separate from the mastery estimate.
{
  const state = createAssessment(6);
  answer(state, 'FR6-01', 'wrong');
  const snapshot = buildSnapshot(state);
  const fractions = snapshot.skills.find(s => s.skill === 'fractions');
  assert(fractions);
  assert.strictEqual(fractions.evidence, 1);
  assert.strictEqual(fractions.correct, 0);
  assert(Array.isArray(fractions.possibleMisconceptions));
}

// 5. A distractor's specific error is diagnosed and classified.
{
  const state = createAssessment(6, { seed: 42 });
  // Materialize the fraction-addition concept and pick the "add across" distractor.
  const q = materialize(state, QUESTION_BANK.find(x => x.id === 'FR6-02'));
  const addAcross = Object.keys(q.diagnostics).find(k => q.diagnostics[k] === 'add_across');
  assert(addAcross, 'Expected an add_across distractor to exist');

  answerQuestion(state, q, addAcross);
  const h = state.history[state.history.length - 1];
  assert.strictEqual(h.correct, false);
  assert.strictEqual(h.diagnosis.code, 'add_across');
  assert.strictEqual(h.diagnosis.type, 'conceptual');
  assert(/numerator/.test(h.diagnosis.note));

  const snap = buildSnapshot(state);
  assert.strictEqual(snap.errorMix.conceptual, 1);
  assert.strictEqual(snap.errorMix.procedural, 0);
  const fr = snap.skills.find(s => s.skill === 'fractions');
  assert.strictEqual(fr.errorProfile, 'conceptual');
  assert(fr.diagnosedErrors.some(e => e.code === 'add_across'));
}

// 6. An off-by-one distractor is diagnosed as a procedural slip.
{
  const state = createAssessment(6, { seed: 7 });
  const q = materialize(state, QUESTION_BANK.find(x => x.id === 'GEO6-01'));
  const slip = Object.keys(q.diagnostics).find(k => q.diagnostics[k] === 'computation_slip');
  assert(slip, 'Expected a computation_slip distractor');
  answerQuestion(state, q, slip);
  const snap = buildSnapshot(state);
  assert.strictEqual(snap.errorMix.procedural, 1);
}

console.log('All adaptive assessment tests passed.');
