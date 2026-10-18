"""
Beyond the Grade — assessment engine (Python port).

A faithful reimplementation of beyond-the-grade-adaptive.js so the Streamlit app
can share the same behavior: seeded template generation, adaptive routing, and
procedural-vs-conceptual error diagnosis. Scoring stays deterministic — no AI.

The Node version (../beyond-the-grade-adaptive.js) remains the reference; keep
the two in sync when either changes.
"""

import math
import re
import random

# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
SKILL_LABELS = {
    "number_sense": "Number Sense",
    "addition": "Addition",
    "subtraction": "Subtraction",
    "multiplication": "Multiplication & Division",
    "fractions": "Fractions",
    "decimals": "Decimals",
    "word_problems": "Word Problems",
    "ratios": "Ratios",
    "expressions": "Expressions",
    "equations": "Equations",
    "exponents": "Exponents & Powers",
    "proportional_reasoning": "Proportional Reasoning",
    "geometry": "Geometry",
    "statistics": "Statistics",
    "logic": "Logic & Reasoning",
}

SKILL_PREREQS = {
    "addition": ["number_sense"],
    "subtraction": ["number_sense"],
    "multiplication": ["number_sense", "addition"],
    "fractions": ["number_sense"],
    "decimals": ["place_value", "number_sense"],
    "word_problems": ["number_sense", "multiplication"],
    "ratios": ["multiplication"],
    "expressions": ["multiplication"],
    "equations": ["expressions"],
    "exponents": ["multiplication"],
    "proportional_reasoning": ["ratios"],
    "geometry": ["number_sense"],
    "statistics": ["number_sense"],
}

# ---------------------------------------------------------------------------
# Concept bank — each names a template that generates a concrete question.
# ---------------------------------------------------------------------------
QUESTION_BANK = [
    # Grade 2
    {"id": "NS2-01", "grade": 2, "skill": "number_sense", "difficulty": 0.10, "prereq": [], "misconception": None, "template": "number_compare_greatest"},
    {"id": "ADD2-01", "grade": 2, "skill": "addition", "difficulty": 0.15, "prereq": ["number_sense"], "misconception": "regrouping", "template": "addition_basic"},
    {"id": "SUB2-01", "grade": 2, "skill": "subtraction", "difficulty": 0.20, "prereq": ["number_sense"], "misconception": "regrouping", "template": "subtraction_basic"},
    # Grade 3
    {"id": "ADD3-01", "grade": 3, "skill": "addition", "difficulty": 0.30, "prereq": ["addition"], "misconception": "regrouping", "template": "addition_basic"},
    {"id": "SUB3-01", "grade": 3, "skill": "subtraction", "difficulty": 0.32, "prereq": ["subtraction"], "misconception": "regrouping", "template": "subtraction_basic"},
    {"id": "OP3-01", "grade": 3, "skill": "multiplication", "difficulty": 0.28, "prereq": ["addition"], "misconception": "counting_addition_instead_of_multiplication", "template": "multiplication_meaning"},
    {"id": "FR3-01", "grade": 3, "skill": "fractions", "difficulty": 0.34, "prereq": ["number_sense"], "misconception": "fraction_size", "template": "fraction_compare_half"},
    # Grade 4
    {"id": "NS4-01", "grade": 4, "skill": "number_sense", "difficulty": 0.30, "prereq": [], "misconception": None, "template": "number_compare_greatest"},
    {"id": "OP4-01", "grade": 4, "skill": "multiplication", "difficulty": 0.35, "prereq": ["number_sense"], "misconception": "counting_addition_instead_of_multiplication", "template": "multiplication_meaning"},
    {"id": "OP4-02", "grade": 4, "skill": "multiplication", "difficulty": 0.45, "prereq": ["multiplication"], "misconception": "fact_fluency", "template": "multiplication_fact"},
    {"id": "FR4-01", "grade": 4, "skill": "fractions", "difficulty": 0.40, "prereq": ["number_sense"], "misconception": "fraction_size", "template": "fraction_compare_half"},
    {"id": "FR4-02", "grade": 4, "skill": "fractions", "difficulty": 0.52, "prereq": ["fractions"], "misconception": "equivalence", "template": "fraction_equivalent"},
    {"id": "WP4-01", "grade": 4, "skill": "word_problems", "difficulty": 0.50, "prereq": ["multiplication"], "misconception": "operation_selection", "template": "word_problem_multiply"},
    # Grade 5
    {"id": "DEC5-01", "grade": 5, "skill": "decimals", "difficulty": 0.55, "prereq": ["number_sense"], "misconception": "decimal_place_value", "template": "decimal_equiv"},
    {"id": "OP5-01", "grade": 5, "skill": "multiplication", "difficulty": 0.58, "prereq": ["multiplication"], "misconception": "fact_fluency", "template": "multiplication_fact"},
    {"id": "FR5-01", "grade": 5, "skill": "fractions", "difficulty": 0.62, "prereq": ["fractions"], "misconception": "fraction_comparison", "template": "fraction_compare_two"},
    {"id": "FR5-02", "grade": 5, "skill": "fractions", "difficulty": 0.68, "prereq": ["fractions"], "misconception": "common_denominator", "template": "fraction_add"},
    {"id": "RAT5-01", "grade": 5, "skill": "ratios", "difficulty": 0.62, "prereq": ["multiplication"], "misconception": "ratio_order", "template": "ratio_basic"},
    # Grade 6
    {"id": "RAT6-01", "grade": 6, "skill": "ratios", "difficulty": 0.72, "prereq": ["ratios"], "misconception": "unit_rate", "template": "ratio_basic"},
    {"id": "RAT6-02", "grade": 6, "skill": "ratios", "difficulty": 0.76, "prereq": ["ratios"], "misconception": "proportional_scaling", "template": "ratio_scaling"},
    {"id": "ALG6-01", "grade": 6, "skill": "expressions", "difficulty": 0.74, "prereq": ["multiplication"], "misconception": "distributive_property", "template": "expression_distribute"},
    {"id": "FR6-01", "grade": 6, "skill": "fractions", "difficulty": 0.75, "prereq": ["fractions"], "misconception": "equivalence", "template": "fraction_equivalent"},
    {"id": "FR6-02", "grade": 6, "skill": "fractions", "difficulty": 0.82, "prereq": ["fractions"], "misconception": "fraction_operations", "template": "fraction_add"},
    {"id": "GEO6-01", "grade": 6, "skill": "geometry", "difficulty": 0.68, "prereq": ["number_sense"], "misconception": "area_vs_perimeter", "template": "geometry_area"},
    {"id": "STAT6-01", "grade": 6, "skill": "statistics", "difficulty": 0.70, "prereq": ["number_sense"], "misconception": "mean_vs_sum", "template": "stats_mean"},
    # Grade 7
    {"id": "ALG7-01", "grade": 7, "skill": "expressions", "difficulty": 0.84, "prereq": ["expressions"], "misconception": "equation_solving", "template": "equation_solve_mc"},
    {"id": "PROP7-01", "grade": 7, "skill": "proportional_reasoning", "difficulty": 0.86, "prereq": ["ratios"], "misconception": "proportional_scaling", "template": "proportional_speed"},
    {"id": "ALG7-02", "grade": 7, "skill": "equations", "difficulty": 0.90, "prereq": ["expressions"], "misconception": "inverse_operations", "template": "equation_solve_sa"},
    {"id": "FR7-01", "grade": 7, "skill": "fractions", "difficulty": 0.88, "prereq": ["fractions"], "misconception": "fraction_division", "template": "fraction_division"},
    # Grade 8
    {"id": "ALG8-01", "grade": 8, "skill": "equations", "difficulty": 0.92, "prereq": ["equations"], "misconception": "variables_both_sides", "template": "linear_two_sides"},
    {"id": "EXP8-01", "grade": 8, "skill": "exponents", "difficulty": 0.90, "prereq": ["multiplication"], "misconception": "exponent_as_multiplication", "template": "exponent_eval"},
    {"id": "GEO8-01", "grade": 8, "skill": "geometry", "difficulty": 0.94, "prereq": ["number_sense"], "misconception": "pythagorean", "template": "pythagorean"},
    {"id": "PROP8-01", "grade": 8, "skill": "proportional_reasoning", "difficulty": 0.90, "prereq": ["proportional_reasoning"], "misconception": "proportional_scaling", "template": "proportional_speed"},
    # Logic & creative reasoning (spans grades; no arithmetic prerequisite)
    {"id": "LOG2-01", "grade": 2, "skill": "logic", "difficulty": 0.16, "prereq": [], "misconception": None, "template": "logic_block_tower"},
    {"id": "LOG3-01", "grade": 3, "skill": "logic", "difficulty": 0.30, "prereq": [], "misconception": None, "template": "logic_notch"},
    {"id": "LOG3-02", "grade": 3, "skill": "logic", "difficulty": 0.34, "prereq": [], "misconception": None, "template": "logic_block_tower"},
    {"id": "LOG4-01", "grade": 4, "skill": "logic", "difficulty": 0.44, "prereq": [], "misconception": None, "template": "logic_toothpicks"},
    {"id": "LOG4-02", "grade": 4, "skill": "logic", "difficulty": 0.48, "prereq": [], "misconception": None, "template": "logic_connections"},
    {"id": "LOG5-01", "grade": 5, "skill": "logic", "difficulty": 0.58, "prereq": [], "misconception": None, "template": "logic_pattern_next"},
    {"id": "LOG5-02", "grade": 5, "skill": "logic", "difficulty": 0.62, "prereq": [], "misconception": None, "template": "logic_toothpicks"},
    {"id": "LOG6-01", "grade": 6, "skill": "logic", "difficulty": 0.70, "prereq": [], "misconception": None, "template": "logic_connections"},
    {"id": "LOG6-02", "grade": 6, "skill": "logic", "difficulty": 0.74, "prereq": [], "misconception": None, "template": "logic_squares_all_sizes"},
    {"id": "LOG6-03", "grade": 6, "skill": "logic", "difficulty": 0.72, "prereq": [], "misconception": None, "template": "logic_glasses"},
    {"id": "LOG7-01", "grade": 7, "skill": "logic", "difficulty": 0.84, "prereq": [], "misconception": None, "template": "logic_pattern_next"},
    {"id": "LOG7-02", "grade": 7, "skill": "logic", "difficulty": 0.86, "prereq": [], "misconception": None, "template": "logic_squares_all_sizes"},
    {"id": "LOG8-01", "grade": 8, "skill": "logic", "difficulty": 0.92, "prereq": [], "misconception": None, "template": "logic_connections"},
    {"id": "LOG8-02", "grade": 8, "skill": "logic", "difficulty": 0.90, "prereq": [], "misconception": None, "template": "logic_glasses"},
]

QUESTION_BY_ID = {q["id"]: q for q in QUESTION_BANK}

# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------
def normalize_answer(value):
    return re.sub(r"\s+", " ", str("" if value is None else value).strip().lower().replace("$", ""))


def is_correct(question, response):
    return normalize_answer(response) == normalize_answer(question["answer"])


# ---------------------------------------------------------------------------
# Seeded PRNG (mulberry32) — mirrors the JS bit-for-bit.
# ---------------------------------------------------------------------------
def _imul(a, b):
    return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF


def mulberry32(seed):
    state = {"a": seed & 0xFFFFFFFF}

    def rng():
        state["a"] = (state["a"] + 0x6D2B79F5) & 0xFFFFFFFF
        a = state["a"]
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        t &= 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rng


def hash_str(s):
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = _imul(h, 16777619)
    return h & 0xFFFFFFFF


def make_seed():
    return random.getrandbits(32)


def rand_int(rng, lo, hi):
    return lo + int(rng() * (hi - lo + 1))


def pick(rng, arr):
    return arr[int(rng() * len(arr))]


def shuffle(rng, arr):
    a = list(arr)
    for i in range(len(a) - 1, 0, -1):
        j = int(rng() * (i + 1))
        a[i], a[j] = a[j], a[i]
    return a


def frac_str(n, d):
    g = math.gcd(int(n), int(d)) or 1
    n //= g
    d //= g
    if d == 1:
        return str(n)
    if n > d:
        w, r = divmod(n, d)
        return str(w) if r == 0 else f"{w} {r}/{d}"
    return f"{n}/{d}"


MINUS = "−"  # −

# ---------------------------------------------------------------------------
# Error diagnosis dictionary
# ---------------------------------------------------------------------------
ERROR_NOTES = {
    # Procedural — right method, wrong execution.
    "off_by_one": {"type": "procedural", "note": "a small arithmetic slip (off by one)"},
    "off_by_ten": {"type": "procedural", "note": "a place-value / regrouping slip (off by ten)"},
    "computation_slip": {"type": "procedural", "note": "a computation slip while carrying out the steps"},
    "fact_fluency": {"type": "procedural", "note": "a multiplication-fact recall slip"},
    # Conceptual — the underlying idea is off.
    "add_across": {"type": "conceptual", "note": "added the numerators and the denominators"},
    "kept_one_denominator": {"type": "conceptual", "note": "kept one denominator instead of finding a common one"},
    "subtracted_instead": {"type": "conceptual", "note": "subtracted instead of the required operation"},
    "equiv_added_constant": {"type": "conceptual", "note": "added the same amount to top and bottom instead of multiplying"},
    "equiv_scaled_denominator": {"type": "conceptual", "note": "scaled only the denominator, not the numerator"},
    "div_multiplied": {"type": "conceptual", "note": "multiplied instead of dividing (didn't use the reciprocal)"},
    "div_reciprocal_answer": {"type": "conceptual", "note": "gave the reciprocal of the correct answer"},
    "chose_addition": {"type": "conceptual", "note": "read “groups of” as addition, not multiplication"},
    "chose_division": {"type": "conceptual", "note": "chose division instead of multiplication"},
    "used_perimeter": {"type": "conceptual", "note": "found the perimeter instead of the area"},
    "added_dimensions": {"type": "conceptual", "note": "added the two sides instead of multiplying"},
    "gave_sum": {"type": "conceptual", "note": "gave the total instead of the mean"},
    "gave_median": {"type": "conceptual", "note": "gave the middle value instead of the mean"},
    "exponent_times_base": {"type": "conceptual", "note": "multiplied base × exponent instead of repeated multiplication"},
    "added_the_legs": {"type": "conceptual", "note": "added the legs instead of using the Pythagorean theorem"},
    "reversed_ratio": {"type": "conceptual", "note": "reversed the order of the ratio"},
    "part_to_whole": {"type": "conceptual", "note": "compared a part to the whole instead of part to part"},
    "additive_not_multiplicative": {"type": "conceptual", "note": "added a constant instead of scaling proportionally"},
    "added_not_multiplied": {"type": "conceptual", "note": "added the quantities instead of multiplying"},
    "distribute_forgot": {"type": "conceptual", "note": "didn't multiply the number through the parentheses"},
    "distribute_sign": {"type": "conceptual", "note": "made a sign error when distributing"},
    "place_value_decimal": {"type": "conceptual", "note": "confused the decimal place value"},
    "inverse_operations": {"type": "conceptual", "note": "didn't correctly undo the operations"},
    "variables_both_sides": {"type": "conceptual", "note": "didn't gather the variable terms onto one side"},
    "fraction_size": {"type": "conceptual", "note": "misjudged the size of the fraction"},
    "fraction_comparison": {"type": "conceptual", "note": "compared the two fractions incorrectly"},
    # Logic & creative reasoning
    "forgot_halving": {"type": "conceptual", "note": "counted every connection twice (didn't halve)"},
    "counted_per_point": {"type": "conceptual", "note": "counted one line per point instead of per pair"},
    "counted_each_square_separately": {"type": "conceptual", "note": "counted every square on its own, ignoring shared sides"},
    "linear_off_by_one": {"type": "procedural", "note": "an off-by-one in the pattern's position"},
    "ignored_start": {"type": "conceptual", "note": "left out the starting amount in the pattern"},
    "counted_unit_only": {"type": "conceptual", "note": "counted only the smallest squares, not the larger ones"},
    "counted_square_instead": {"type": "conceptual", "note": "used rows × rows instead of adding each row"},
    "doubled_bottom": {"type": "procedural", "note": "doubled the bottom row instead of adding every row"},
    "forgot_two_pieces": {"type": "conceptual", "note": "didn't split the leftover between the two pieces"},
    "used_whole_width": {"type": "conceptual", "note": "used the whole width instead of the leftover"},
    "reasoning_swap": {"type": "conceptual", "note": "swapping two glasses doesn't change which are full"},
    "reasoning_ends": {"type": "conceptual", "note": "moving an end glass can't make the row alternate"},
    "reasoning_impossible": {"type": "conceptual", "note": "it can be done — pour one glass into another"},
}


def diagnose(code):
    if not code:
        return None
    e = ERROR_NOTES.get(code)
    if e:
        return {"code": code, "type": e["type"], "note": e["note"]}
    return {"code": code, "type": "conceptual", "note": str(code).replace("_", " ")}


# ---------------------------------------------------------------------------
# Choice builders
# ---------------------------------------------------------------------------
def mcq(rng, correct, distractors):
    correct = str(correct)
    seen = {correct}
    out = []
    diagnostics = {}
    for d in distractors:
        if isinstance(d, dict):
            s = None if d.get("v") is None else str(d["v"])
            err = d.get("error")
        else:
            s = None if d is None else str(d)
            err = None
        if s and s not in seen:
            seen.add(s)
            out.append(s)
            if err:
                diagnostics[s] = err
        if len(out) >= 3:
            break
    pad = 1
    while len(out) < 3:
        m = re.match(r"^(\D*?)(\d+)(\D*)$", correct)
        cand = f"{m.group(1)}{int(m.group(2)) + pad}{m.group(3)}" if m else f"{correct} ({pad})"
        if cand not in seen:
            seen.add(cand)
            out.append(cand)
            diagnostics[cand] = "computation_slip"
        pad += 1
        if pad > 99:
            break
    return {"choices": shuffle(rng, [correct] + out), "answer": correct, "diagnostics": diagnostics}


def frac_distractors(rng, correct_n, correct_d, pool):
    seen = {frac_str(correct_n, correct_d)}
    out = []
    diag = {}

    def add(n, d, error=None):
        if n <= 0 or d <= 0 or len(out) >= 3:
            return
        s = frac_str(n, d)
        if s not in seen:
            seen.add(s)
            out.append(s)
            if error:
                diag[s] = error

    for entry in pool:
        add(*entry) if len(entry) == 3 else add(entry[0], entry[1])
        if len(out) >= 3:
            break
    k = 1
    while len(out) < 3 and k < 60:
        add(correct_n + k, correct_d, "computation_slip")
        add(correct_n - k, correct_d, "computation_slip")
        k += 1
    lst = shuffle(rng, out)
    diagnostics = {s: diag[s] for s in lst if s in diag}
    return {"list": lst, "diagnostics": diagnostics}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
def _number_compare_greatest(rng, d):
    digits = 2 if d < 0.2 else 3 if d < 0.5 else 4 if d < 0.75 else 5
    lo, hi = 10 ** (digits - 1), 10 ** digits - 1
    nums = set()
    while len(nums) < 4:
        nums.add(rand_int(rng, lo, hi))
    arr = list(nums)
    return {"prompt": "Which number is greatest?", "choices": shuffle(rng, [str(x) for x in arr]), "answer": str(max(arr))}


def _addition_basic(rng, d):
    hi = 12 if d < 0.2 else 99 if d < 0.4 else 999
    a, b = rand_int(rng, 2, hi), rand_int(rng, 2, hi)
    q = mcq(rng, a + b, [{"v": a + b + 10, "error": "off_by_ten"}, {"v": a + b + 1, "error": "off_by_one"}, {"v": a + b - 1, "error": "off_by_one"}])
    return {"prompt": f"What is {a} + {b}?", **q}


def _subtraction_basic(rng, d):
    hi = 18 if d < 0.2 else 99 if d < 0.4 else 999
    a = rand_int(rng, 6, hi)
    b = rand_int(rng, 2, a - 1)
    ans = a - b
    q = mcq(rng, ans, [{"v": ans + 10, "error": "off_by_ten"}, {"v": ans + 1, "error": "off_by_one"}, {"v": ans - 1, "error": "off_by_one"}])
    return {"prompt": f"What is {a} {MINUS} {b}?", **q}


def _exponent_eval(rng, d):
    base, exp = rand_int(rng, 2, 6), rand_int(rng, 2, 3)
    ans = base ** exp
    q = mcq(rng, ans, [{"v": base * exp, "error": "exponent_times_base"}, {"v": ans + base, "error": "computation_slip"}, {"v": ans - base, "error": "computation_slip"}, {"v": ans + 1, "error": "off_by_one"}])
    return {"prompt": f"What is {base}^{exp}?", **q}


def _pythagorean(rng, d):
    a, b, c = pick(rng, [[3, 4, 5], [6, 8, 10], [5, 12, 13], [8, 15, 17], [9, 12, 15], [7, 24, 25]])
    q = mcq(rng, c, [{"v": a + b, "error": "added_the_legs"}, {"v": c + 1, "error": "off_by_one"}, {"v": c - 1, "error": "off_by_one"}, {"v": c + 2, "error": "computation_slip"}])
    return {"prompt": f"A right triangle has legs of {a} and {b}. What is the length of the hypotenuse?", **q}


def _linear_two_sides(rng, d):
    x = rand_int(rng, 2, 9)
    a = rand_int(rng, 3, 6)
    c = rand_int(rng, 1, a - 1)
    b = rand_int(rng, 1, 9)
    rhs = (a - c) * x + b
    q = mcq(rng, x, [{"v": x + 1, "error": "off_by_one"}, {"v": x - 1, "error": "off_by_one"}, {"v": x + 2, "error": "variables_both_sides"}])
    return {"prompt": f"Solve: {a}x + {b} = {c}x + {rhs}.", **q}


def _multiplication_meaning(rng, d):
    a, b = rand_int(rng, 2, 9), rand_int(rng, 2, 9)
    q = mcq(rng, f"{a} × {b}", [{"v": f"{a} + {b}", "error": "chose_addition"}, {"v": f"{b} {MINUS} {a}", "error": "subtracted_instead"}, {"v": f"{b} ÷ {a}", "error": "chose_division"}, {"v": f"{a} ÷ {b}", "error": "chose_division"}])
    return {"prompt": f"Which equation represents {a} groups of {b}?", **q}


def _multiplication_fact(rng, d):
    if d < 0.4:
        a, b = rand_int(rng, 2, 9), rand_int(rng, 2, 9)
    elif d < 0.6:
        a, b = rand_int(rng, 6, 12), rand_int(rng, 3, 9)
    else:
        a, b = rand_int(rng, 8, 15), rand_int(rng, 4, 12)
    return {"prompt": f"What is {a} × {b}?", "type": "short_answer", "answer": str(a * b), "choices": None, "diagnostics": {}}


def _fraction_compare_half(rng, d):
    cd = rand_int(rng, 3, 8)
    cn = rand_int(rng, 1, cd - 1)
    while cn / cd <= 0.5:
        cn = rand_int(rng, 1, cd - 1)
    correct = f"{cn}/{cd}"
    dis = []
    guard = 0
    while len(dis) < 3 and guard < 80:
        guard += 1
        dd = rand_int(rng, 3, 8)
        dn = rand_int(rng, 1, dd - 1)
        if dn / dd < 0.5:
            s = f"{dn}/{dd}"
            if s != correct and s not in dis:
                dis.append(s)
    diagnostics = {s: "fraction_size" for s in dis}
    return {"prompt": "Which fraction is greater than 1/2?", "choices": shuffle(rng, [correct] + dis), "answer": correct, "diagnostics": diagnostics}


def _fraction_equivalent(rng, d):
    b = rand_int(rng, 2, 6)
    a = rand_int(rng, 1, b - 1)
    while math.gcd(a, b) != 1:
        a = rand_int(rng, 1, b - 1)
    k = rand_int(rng, 2, 4)
    q = mcq(rng, f"{a * k}/{b * k}", [{"v": f"{a + k}/{b + k}", "error": "equiv_added_constant"}, {"v": f"{a}/{b * k}", "error": "equiv_scaled_denominator"}, f"{a * k}/{b * (k + 1)}", f"{a * (k + 1)}/{b * k}"])
    return {"prompt": f"Which fraction is equivalent to {a}/{b}?", **q}


def _fraction_compare_two(rng, d):
    while True:
        d1 = rand_int(rng, 3, 8)
        n1 = rand_int(rng, 1, d1 - 1)
        d2 = rand_int(rng, 3, 8)
        n2 = rand_int(rng, 1, d2 - 1)
        if abs(n1 / d1 - n2 / d2) > 1e-9:
            break
    smaller = f"{n2}/{d2}" if n1 / d1 > n2 / d2 else f"{n1}/{d1}"
    bigger = f"{n1}/{d1}" if n1 / d1 > n2 / d2 else f"{n2}/{d2}"
    return {
        "prompt": f"Which is greater, {n1}/{d1} or {n2}/{d2}?",
        "choices": [f"{n1}/{d1}", f"{n2}/{d2}", "They are equal", "Not enough information"],
        "answer": bigger,
        "diagnostics": {smaller: "fraction_comparison", "They are equal": "fraction_comparison", "Not enough information": "fraction_comparison"},
    }


def _fraction_add(rng, d):
    if d < 0.6:
        d1 = rand_int(rng, 2, 6)
        d2 = d1 * rand_int(rng, 1, 2)
    else:
        d1 = rand_int(rng, 2, 6)
        d2 = rand_int(rng, 2, 8)
    n1, n2 = rand_int(rng, 1, d1 - 1), rand_int(rng, 1, d2 - 1)
    sum_n, sum_d = n1 * d2 + n2 * d1, d1 * d2
    fd = frac_distractors(rng, sum_n, sum_d, [
        (n1 + n2, d1 + d2, "add_across"),
        (n1 + n2, max(d1, d2), "kept_one_denominator"),
        (abs(n1 * d2 - n2 * d1), sum_d, "subtracted_instead"),
        (n1 * n2, sum_d, "computation_slip"),
        (sum_n, sum_d * 2, "computation_slip"),
    ])
    correct = frac_str(sum_n, sum_d)
    return {"prompt": f"What is {frac_str(n1, d1)} + {frac_str(n2, d2)}?", "choices": shuffle(rng, [correct] + fd["list"]), "answer": correct, "diagnostics": fd["diagnostics"]}


def _fraction_division(rng, d):
    d1 = rand_int(rng, 2, 5)
    n1 = rand_int(rng, 1, d1 - 1)
    d2 = rand_int(rng, 2, 4)
    n2 = rand_int(rng, 1, d2 - 1)
    rn, rd = n1 * d2, d1 * n2
    fd = frac_distractors(rng, rn, rd, [
        (n1 * n2, d1 * d2, "div_multiplied"),
        (n1, d1, "computation_slip"),
        (rd, rn, "div_reciprocal_answer"),
        (rn, rd * 2, "computation_slip"),
    ])
    correct = frac_str(rn, rd)
    return {"prompt": f"What is {frac_str(n1, d1)} ÷ {frac_str(n2, d2)}?", "choices": shuffle(rng, [correct] + fd["list"]), "answer": correct, "diagnostics": fd["diagnostics"]}


def _decimal_equiv(rng, d):
    n = rand_int(rng, 1, 9)
    q = mcq(rng, f"{n}/10", [{"v": f"{n}/100", "error": "place_value_decimal"}, {"v": f"{n}/1000", "error": "place_value_decimal"}, f"{100 + n}/1000", {"v": f"{n}/2", "error": "place_value_decimal"}])
    return {"prompt": f"Which number is the same as 0.{n}?", **q}


def _word_problem_multiply(rng, d):
    container, item = pick(rng, [["boxes", "pencils"], ["crates", "apples"], ["shelves", "books"], ["bags", "marbles"]])
    b, p = rand_int(rng, 3, 9), rand_int(rng, 10, 30)
    q = mcq(rng, b * p, [{"v": b + p, "error": "added_not_multiplied"}, {"v": b * p - p, "error": "computation_slip"}, {"v": b * (p + 1), "error": "computation_slip"}, {"v": b * p + b, "error": "computation_slip"}])
    return {"prompt": f"There are {b} {container} with {p} {item} in each. How many {item} are there in total?", **q}


def _ratio_basic(rng, d):
    x = rand_int(rng, 2, 6)
    y = rand_int(rng, 2, 6)
    while x == y:
        y = rand_int(rng, 2, 6)
    t1, t2 = pick(rng, [["red apples", "green apples"], ["cats", "dogs"], ["blue pens", "red pens"], ["boys", "girls"]])
    q = mcq(rng, f"{x}:{y}", [{"v": f"{y}:{x}", "error": "reversed_ratio"}, {"v": f"{x}:{x + y}", "error": "part_to_whole"}, {"v": f"{x + y}:{y}", "error": "part_to_whole"}])
    return {"prompt": f"A group has {x} {t1} for every {y} {t2}. What is the ratio of {t1} to {t2}?", **q}


def _ratio_scaling(rng, d):
    u, n, k = rand_int(rng, 2, 5), rand_int(rng, 2, 4), rand_int(rng, 2, 5)
    m, cost, ans = n * k, n * u, n * k * u
    item = pick(rng, ["notebooks", "apples", "markers", "tickets"])
    q = mcq(rng, f"${ans}", [{"v": f"${cost + u}", "error": "additive_not_multiplicative"}, {"v": f"${ans - u}", "error": "off_by_one"}, {"v": f"${ans + u}", "error": "off_by_one"}, {"v": f"${m + cost}", "error": "additive_not_multiplicative"}])
    return {"prompt": f"If {n} {item} cost ${cost}, how much do {m} {item} cost at the same rate?", **q}


def _proportional_speed(rng, d):
    r = rand_int(rng, 4, 7) * 10
    t1 = rand_int(rng, 2, 4)
    t2 = t1 + rand_int(rng, 1, 3)
    d1, ans = r * t1, r * t2
    q = mcq(rng, ans, [{"v": ans - r, "error": "off_by_one"}, {"v": ans + r, "error": "off_by_one"}, {"v": d1 + t2, "error": "additive_not_multiplicative"}])
    return {"prompt": f"A car travels {d1} miles in {t1} hours at a constant speed. How far will it travel in {t2} hours?", **q}


def _expression_distribute(rng, d):
    a, b, c = rand_int(rng, 2, 4), rand_int(rng, 2, 6), rand_int(rng, 1, 3)
    q = mcq(rng, f"{a + c}x {MINUS} {a * b}", [{"v": f"{a + c}x {MINUS} {b}", "error": "distribute_forgot"}, {"v": f"{a * c}x {MINUS} {a * b}", "error": "distribute_forgot"}, {"v": f"{a + c}x + {a * b}", "error": "distribute_sign"}, {"v": f"{a}x {MINUS} {a * b}", "error": "distribute_forgot"}])
    c_term = "x" if c == 1 else f"{c}x"
    return {"prompt": f"Which expression is equivalent to {a}(x {MINUS} {b}) + {c_term}?", **q}


def _equation_solve_mc(rng, d):
    x = rand_int(rng, 2, 9)
    a = rand_int(rng, 2, 5)
    b = rand_int(rng, 1, 12)
    q = mcq(rng, x, [{"v": x + 1, "error": "off_by_one"}, {"v": x - 1, "error": "off_by_one"}, {"v": x + 2, "error": "computation_slip"}])
    return {"prompt": f"Solve: {a}x + {b} = {a * x + b}.", **q}


def _equation_solve_sa(rng, d):
    x = rand_int(rng, 3, 12)
    a = rand_int(rng, 2, 5)
    b = rand_int(rng, 3, 15)
    return {"prompt": f"If {a}x {MINUS} {b} = {a * x - b}, what is x?", "type": "short_answer", "answer": str(x), "choices": None, "diagnostics": {}}


def _geometry_area(rng, d):
    length, width = rand_int(rng, 3, 12), rand_int(rng, 2, 9)
    q = mcq(rng, length * width, [{"v": 2 * (length + width), "error": "used_perimeter"}, {"v": length + width, "error": "added_dimensions"}, {"v": length * width - length, "error": "computation_slip"}])
    return {"prompt": f"A rectangle is {length} units long and {width} units wide. What is its area?", **q}


def _stats_mean(rng, d):
    while True:
        nums = [rand_int(rng, 2, 12), rand_int(rng, 2, 12), rand_int(rng, 2, 12)]
        total = sum(nums)
        if total % 3 == 0:
            break
    srt = sorted(nums)
    q = mcq(rng, total // 3, [{"v": total, "error": "gave_sum"}, {"v": srt[1], "error": "gave_median"}, {"v": total // 3 + 1, "error": "off_by_one"}])
    return {"prompt": f"What is the mean of {', '.join(str(n) for n in nums)}?", **q}


# ---------------------------------------------------------------------------
# Inline SVG figures — deterministic diagrams drawn from the same parameters.
# Themed to the app ink so they read on the periwinkle background.
# ---------------------------------------------------------------------------
_FIG_INK = "#2f3729"
_FIG_TINT = "#cfe0c2"


def _svg(w, h, body):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{int(w)}px" '
            f'xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{_FIG_INK}" '
            f'stroke-width="2" stroke-linejoin="round">{body}</svg>')


def _txt(x, y, s, size=12):
    return (f'<text x="{x}" y="{y}" fill="{_FIG_INK}" stroke="none" font-size="{size}" '
            f'text-anchor="middle" font-family="Inter, system-ui, sans-serif">{s}</text>')


def _fig_block_tower(h):
    c = 26
    cells = [f'<rect x="{i*c+1}" y="{(r-1)*c+1}" width="{c-2}" height="{c-2}" fill="{_FIG_TINT}"/>'
             for r in range(1, h + 1) for i in range(r)]
    return _svg(h * c + 2, h * c + 2, "".join(cells))


def _fig_toothpicks(n):
    c = 30
    w = n * c
    body = [f'<rect x="1" y="1" width="{w-2}" height="{c-2}" fill="{_FIG_TINT}"/>']
    body += [f'<line x1="{i*c}" y1="1" x2="{i*c}" y2="{c-1}"/>' for i in range(1, n)]
    return _svg(w + 2, c + 2, "".join(body))


def _fig_points(n):
    size, r = 150, 58
    cx = cy = size / 2
    dots = []
    for k in range(n):
        ang = -math.pi / 2 + 2 * math.pi * k / n
        dots.append(f'<circle cx="{cx + r*math.cos(ang):.1f}" cy="{cy + r*math.sin(ang):.1f}" '
                    f'r="6" fill="{_FIG_INK}" stroke="none"/>')
    return _svg(size, size, "".join(dots))


def _fig_grid(n):
    c = 34
    w = n * c
    body = [f'<rect x="1" y="1" width="{w-2}" height="{w-2}"/>']
    for i in range(1, n):
        body.append(f'<line x1="{i*c}" y1="0" x2="{i*c}" y2="{w}"/>')
        body.append(f'<line x1="0" y1="{i*c}" x2="{w}" y2="{i*c}"/>')
    return _svg(w + 2, w + 2, "".join(body))


def _fig_pattern(a, b):
    c, per, gap = 16, 5, 24
    body, x0, maxrows = [], 0, 1
    for f in range(3):
        count = a + f * b
        for i in range(count):
            body.append(f'<rect x="{x0+(i%per)*c+1}" y="{(i//per)*c+1}" width="{c-2}" '
                        f'height="{c-2}" fill="{_FIG_TINT}"/>')
        rows = (count + per - 1) // per
        maxrows = max(maxrows, rows)
        gw = min(count, per) * c
        body.append(_txt(x0 + gw / 2, rows * c + 15, f"Fig {f+1}"))
        x0 += gw + gap
    body.append(_txt(x0 + 8, c, "&#8230;", 20))
    return _svg(x0 + 24, maxrows * c + 22, "".join(body))


def _fig_notch(w_units, m_units, piece):
    s, h = 16, 38
    pw, gw, total = piece * s, m_units * s, w_units * s
    body = [
        f'<rect x="1" y="1" width="{pw-1}" height="{h-2}" fill="{_FIG_TINT}"/>',
        f'<rect x="{pw+gw+1}" y="1" width="{pw-1}" height="{h-2}" fill="{_FIG_TINT}"/>',
        _txt(pw + gw / 2, h / 2 + 4, m_units),
        _txt(pw / 2, h + 16, "?", 14),
    ]
    return _svg(total + 2, h + 22, "".join(body))


def _fig_glasses():
    cw, ch, gap = 32, 44, 16
    body = []
    for i in range(6):
        x = i * (cw + gap)
        body.append(f'<polygon points="{x},2 {x+cw},2 {x+cw-6},{ch} {x+6},{ch}" '
                    f'fill="{_FIG_INK if i < 3 else "none"}"/>')
        body.append(_txt(x + cw / 2, ch + 16, i + 1))
    return _svg(6 * cw + 5 * gap, ch + 22, "".join(body))


# ---------------------------------------------------------------------------
# Logic & creative reasoning — parameterized puzzles with deterministic answers.
# ---------------------------------------------------------------------------
def _logic_block_tower(rng, d):
    h = rand_int(rng, 3, 4) if d < 0.35 else rand_int(rng, 4, 5) if d < 0.55 else rand_int(rng, 5, 7)
    ans = h * (h + 1) // 2
    q = mcq(rng, ans, [
        {"v": h * h, "error": "counted_square_instead"},
        {"v": 2 * h, "error": "doubled_bottom"},
        {"v": ans - h, "error": "computation_slip"},
        {"v": ans + 1, "error": "off_by_one"},
    ])
    return {"prompt": f"A tower is built like a staircase: the top row has 1 block, the next row has 2, "
                      f"and so on down to a bottom row of {h} blocks. How many blocks are used in all?", "figure": _fig_block_tower(h), **q}


def _logic_notch(rng, d):
    m = rand_int(rng, 2, 4)
    piece = rand_int(rng, 2, 5) if d < 0.4 else rand_int(rng, 4, 9)
    w = m + 2 * piece
    q = mcq(rng, piece, [
        {"v": w - m, "error": "forgot_two_pieces"},
        {"v": w, "error": "used_whole_width"},
        {"v": piece + 1, "error": "off_by_one"},
        {"v": piece - 1, "error": "off_by_one"},
    ])
    return {"prompt": f"A shelf is {w} units wide. A gap {m} units wide is cut out of the exact middle, "
                      f"leaving two equal pieces — one on the left and one on the right. How wide is each piece?", "figure": _fig_notch(w, m, piece), **q}


def _logic_toothpicks(rng, d):
    n = rand_int(rng, 3, 5) if d < 0.55 else rand_int(rng, 6, 9)
    ans = 3 * n + 1
    q = mcq(rng, ans, [
        {"v": 4 * n, "error": "counted_each_square_separately"},
        {"v": 3 * n, "error": "off_by_one"},
        {"v": 3 * n + 2, "error": "off_by_one"},
    ])
    return {"prompt": f"A row of {n} squares is built from toothpicks, where two side-by-side squares "
                      f"share one toothpick. How many toothpicks are used in all?", "figure": _fig_toothpicks(n), **q}


def _logic_connections(rng, d):
    n = rand_int(rng, 4, 5) if d < 0.6 else rand_int(rng, 5, 6) if d < 0.82 else rand_int(rng, 6, 8)
    ans = n * (n - 1) // 2
    q = mcq(rng, ans, [
        {"v": n * (n - 1), "error": "forgot_halving"},
        {"v": n, "error": "counted_per_point"},
        {"v": n - 1, "error": "counted_per_point"},
        {"v": ans + 1, "error": "off_by_one"},
    ])
    return {"prompt": f"How many straight lines are needed to connect {n} points to each other, "
                      f"if no three of the points lie on one straight line?", "figure": _fig_points(n), **q}


def _logic_pattern_next(rng, d):
    a = rand_int(rng, 2, 5)
    b = rand_int(rng, 2, 4)
    n = rand_int(rng, 6, 9) if d < 0.7 else rand_int(rng, 10, 16)
    ans = a + (n - 1) * b
    q = mcq(rng, ans, [
        {"v": a + n * b, "error": "linear_off_by_one"},
        {"v": a + (n - 2) * b, "error": "linear_off_by_one"},
        {"v": n * b, "error": "ignored_start"},
        {"v": ans + 1, "error": "off_by_one"},
    ])
    return {"prompt": f"In a growing pattern, Figure 1 has {a} squares and each figure has {b} more "
                      f"squares than the one before. How many squares are in Figure {n}?", "figure": _fig_pattern(a, b), **q}


def _logic_squares_all_sizes(rng, d):
    n = 3 if d < 0.72 else 4 if d < 0.9 else rand_int(rng, 4, 5)
    ans = n * (n + 1) * (2 * n + 1) // 6
    q = mcq(rng, ans, [
        {"v": n * n, "error": "counted_unit_only"},
        {"v": n * n + 1, "error": "counted_unit_only"},
        {"v": ans - 1, "error": "off_by_one"},
        {"v": ans + n, "error": "computation_slip"},
    ])
    return {"prompt": f"How many squares of every size (not just the small ones) can be found on a "
                      f"{n}×{n} grid of squares?", "figure": _fig_grid(n), **q}


def _logic_glasses(rng, d):
    correct = "Pour glass 2 into glass 5"
    q = mcq(rng, correct, [
        {"v": "Swap glass 3 and glass 4", "error": "reasoning_swap"},
        {"v": "Pour glass 1 into glass 6", "error": "reasoning_ends"},
        {"v": "It can't be done by moving one glass", "error": "reasoning_impossible"},
    ])
    return {"prompt": "Six glasses sit in a row: glasses 1, 2 and 3 are full; glasses 4, 5 and 6 are empty. "
                      "By pouring just ONE glass into another, make the row alternate full, empty, full, "
                      "empty, full, empty. Which single move works?", "figure": _fig_glasses(), **q}


TEMPLATES = {
    "number_compare_greatest": _number_compare_greatest,
    "addition_basic": _addition_basic,
    "subtraction_basic": _subtraction_basic,
    "exponent_eval": _exponent_eval,
    "pythagorean": _pythagorean,
    "linear_two_sides": _linear_two_sides,
    "multiplication_meaning": _multiplication_meaning,
    "multiplication_fact": _multiplication_fact,
    "fraction_compare_half": _fraction_compare_half,
    "fraction_equivalent": _fraction_equivalent,
    "fraction_compare_two": _fraction_compare_two,
    "fraction_add": _fraction_add,
    "fraction_division": _fraction_division,
    "decimal_equiv": _decimal_equiv,
    "word_problem_multiply": _word_problem_multiply,
    "ratio_basic": _ratio_basic,
    "ratio_scaling": _ratio_scaling,
    "proportional_speed": _proportional_speed,
    "expression_distribute": _expression_distribute,
    "equation_solve_mc": _equation_solve_mc,
    "equation_solve_sa": _equation_solve_sa,
    "geometry_area": _geometry_area,
    "stats_mean": _stats_mean,
    "logic_block_tower": _logic_block_tower,
    "logic_notch": _logic_notch,
    "logic_toothpicks": _logic_toothpicks,
    "logic_connections": _logic_connections,
    "logic_pattern_next": _logic_pattern_next,
    "logic_squares_all_sizes": _logic_squares_all_sizes,
    "logic_glasses": _logic_glasses,
}


# ---------------------------------------------------------------------------
# Assessment state
# ---------------------------------------------------------------------------
def create_skill_state():
    return {
        "evidence": 0,
        "correct": 0,
        "mastery": 0.50,
        "lastResult": None,
        "gradesSeen": set(),
        "misconceptions": [],
        "observedErrors": [],
        "proceduralCount": 0,
        "conceptualCount": 0,
    }


def create_assessment(current_grade, min_questions=12, max_questions=20, seed=None):
    return {
        "currentGrade": current_grade,
        "minQuestions": min_questions,
        "maxQuestions": max_questions,
        "seed": seed if seed is not None else make_seed(),
        "generated": {},
        "questionCount": 0,
        "globalAbility": 0.50,
        "mastery": {},
        "seen": set(),
        "history": [],
    }


def get_skill_state(state, skill):
    if skill not in state["mastery"]:
        state["mastery"][skill] = create_skill_state()
    return state["mastery"][skill]


def materialize(state, blueprint):
    if not blueprint:
        return None
    if blueprint["id"] in state["generated"]:
        return state["generated"][blueprint["id"]]
    tpl = TEMPLATES.get(blueprint.get("template"))
    rng = mulberry32(hash_str(f"{blueprint['id']}:{state['seed']}"))
    gen = tpl(rng, blueprint["difficulty"])
    instance = {
        "id": blueprint["id"],
        "grade": blueprint["grade"],
        "skill": blueprint["skill"],
        "difficulty": blueprint["difficulty"],
        "prereq": blueprint.get("prereq"),
        "misconception": blueprint.get("misconception"),
        "type": gen.get("type", "multiple_choice"),
        "prompt": gen["prompt"],
        "figure": gen.get("figure"),          # inline SVG diagram (optional)
        "image": gen.get("image") or blueprint.get("image"),  # asset path under assets/questions/ (optional)
        "choices": gen.get("choices"),
        "answer": gen["answer"],
        "diagnostics": gen.get("diagnostics", {}),
    }
    state["generated"][blueprint["id"]] = instance
    return instance


def update_skill_mastery(state, question, correct, diagnosis):
    ss = get_skill_state(state, question["skill"])
    prior = ss["mastery"]
    reliability = min(0.30, 0.12 + ss["evidence"] * 0.04)
    obs = 1 if correct else 0
    ss["mastery"] = prior + reliability * (obs - prior)
    ss["evidence"] += 1
    ss["correct"] += 1 if correct else 0
    ss["lastResult"] = correct
    ss["gradesSeen"].add(question["grade"])
    if not correct:
        misc = question.get("misconception")
        if misc and misc not in ss["misconceptions"]:
            ss["misconceptions"].append(misc)
        if diagnosis:
            existing = next((e for e in ss["observedErrors"] if e["code"] == diagnosis["code"]), None)
            if existing:
                existing["count"] += 1
            else:
                ss["observedErrors"].append({**diagnosis, "count": 1})
            if diagnosis["type"] == "procedural":
                ss["proceduralCount"] += 1
            else:
                ss["conceptualCount"] += 1


def update_global_ability(state, correct):
    change = 0.045 if correct else -0.055
    state["globalAbility"] = max(0.05, min(0.95, state["globalAbility"] + change))


def recent_skill_count(state, skill, n=4):
    return sum(1 for h in state["history"][-n:] if h["skill"] == skill)


def has_weak_prerequisite(state, question):
    prereqs = question.get("prereq") or SKILL_PREREQS.get(question["skill"], [])
    for pre in prereqs:
        s = state["mastery"].get(pre)
        if s and s["evidence"] >= 2 and s["mastery"] < 0.38:
            return True
    return False


def choose_next_question(state):
    candidates = [q for q in QUESTION_BANK if q["id"] not in state["seen"]]
    if not candidates:
        return None
    current_grade = state["currentGrade"]

    foundation_targets = [skill for skill, s in state["mastery"].items() if s["evidence"] >= 2 and s["mastery"] < 0.40]
    foundation_pool = [q for q in candidates if q["skill"] in foundation_targets and q["grade"] < current_grade]
    if foundation_pool:
        foundation_pool.sort(key=lambda q: (q["grade"], q["difficulty"]))
        return materialize(state, foundation_pool[0])

    def score(q):
        skill = get_skill_state(state, q["skill"])
        mastery = skill["mastery"]
        uncertainty = 1 - min(1, abs(mastery - 0.50) * 2)
        if q["grade"] == current_grade:
            grade_fit = 1.00
        elif q["grade"] == current_grade - 1:
            grade_fit = 0.82
        elif q["grade"] == current_grade + 1:
            grade_fit = 0.72
        else:
            grade_fit = 0.35
        stretch = 0.70 if (q["grade"] > current_grade and mastery >= 0.68) else 0
        foundation = 0.85 if (q["grade"] < current_grade and mastery < 0.42) else 0
        target_difficulty = 0.30 + state["globalAbility"] * 0.62
        difficulty_fit = 1 - min(1, abs(q["difficulty"] - target_difficulty))
        repetition_penalty = recent_skill_count(state, q["skill"]) * 0.28
        prerequisite_penalty = 0.25 if has_weak_prerequisite(state, q) else 0
        coverage = 0.80 if skill["evidence"] == 0 else 0
        clarification = 0.55 if (skill["lastResult"] is False and skill["evidence"] <= 2) else 0
        return (
            uncertainty * 0.95
            + grade_fit * 0.75
            + stretch
            + foundation
            + difficulty_fit * 0.65
            + coverage
            + clarification
            - repetition_penalty
            - prerequisite_penalty
        )

    best = max(candidates, key=score)
    return materialize(state, best)


def answer_question(state, question, response):
    correct = is_correct(question, response)
    diagnosis = None
    if not correct:
        code = (question.get("diagnostics") or {}).get(str(response)) or question.get("misconception")
        diagnosis = diagnose(code)
    state["seen"].add(question["id"])
    state["history"].append({
        "questionId": question["id"],
        "skill": question["skill"],
        "grade": question["grade"],
        "difficulty": question["difficulty"],
        "correct": correct,
        "response": response,
        "diagnosis": diagnosis,
    })
    update_skill_mastery(state, question, correct, diagnosis)
    update_global_ability(state, correct)
    state["questionCount"] += 1
    return correct


def should_stop(state):
    if state["questionCount"] < state["minQuestions"]:
        return False
    if state["questionCount"] >= state["maxQuestions"]:
        return True
    current_grade_skills = list({q["skill"] for q in QUESTION_BANK if q["grade"] == state["currentGrade"]})
    covered = sum(1 for skill in current_grade_skills if state["mastery"].get(skill) and state["mastery"][skill]["evidence"] >= 1)
    sufficiently_covered = covered >= min(5, len(current_grade_skills))
    has_foundation = any(s["mastery"] < 0.38 and s["evidence"] >= 2 for s in state["mastery"].values())
    has_stretch = any(s["mastery"] > 0.70 and s["evidence"] >= 2 for s in state["mastery"].values())
    return sufficiently_covered and (has_foundation or has_stretch)


def classify(ss):
    if not ss or ss["evidence"] == 0:
        return "Not assessed"
    if ss["mastery"] >= 0.70:
        return "Strong evidence"
    if ss["mastery"] >= 0.50:
        return "Developing / likely on track"
    if ss["mastery"] >= 0.36:
        return "Worth a closer look"
    return "Focus area"


def grade_band_for_skill(state, skill):
    evidence = [h for h in state["history"] if h["skill"] == skill]
    if not evidence:
        return None
    highs = [h["grade"] for h in evidence if h["correct"]]
    lows = [h["grade"] for h in evidence if not h["correct"]]
    return {
        "highestSuccessfulGrade": max(highs) if highs else None,
        "lowestFailedGrade": min(lows) if lows else None,
    }


def build_snapshot(state):
    skills = []
    for skill, s in state["mastery"].items():
        skills.append({
            "skill": skill,
            "label": SKILL_LABELS.get(skill, skill),
            "mastery": round(s["mastery"], 2),
            "evidence": s["evidence"],
            "correct": s["correct"],
            "classification": classify(s),
            "gradesSeen": sorted(s["gradesSeen"]),
            "gradeEvidence": grade_band_for_skill(state, skill),
            "possibleMisconceptions": s["misconceptions"],
            "diagnosedErrors": sorted(s["observedErrors"], key=lambda e: -e["count"]),
            "proceduralCount": s["proceduralCount"],
            "conceptualCount": s["conceptualCount"],
            "errorProfile": (
                None if s["conceptualCount"] == 0 and s["proceduralCount"] == 0
                else "conceptual" if s["conceptualCount"] > s["proceduralCount"]
                else "procedural" if s["proceduralCount"] > s["conceptualCount"]
                else "mixed"
            ),
        })
    wrong = [h for h in state["history"] if not h["correct"] and h["diagnosis"]]
    error_mix = {
        "procedural": sum(1 for h in wrong if h["diagnosis"]["type"] == "procedural"),
        "conceptual": sum(1 for h in wrong if h["diagnosis"]["type"] == "conceptual"),
    }
    return {
        "currentGrade": state["currentGrade"],
        "questionsAnswered": state["questionCount"],
        "globalAbility": round(state["globalAbility"], 2),
        "strongAreas": [s["label"] for s in skills if s["mastery"] >= 0.70],
        "areasToReview": [s["label"] for s in skills if 0.36 <= s["mastery"] < 0.50],
        "focusAreas": [s["label"] for s in skills if s["mastery"] < 0.36],
        "readyForMore": any(any(g > state["currentGrade"] for g in s["gradesSeen"]) and s["mastery"] >= 0.70 for s in skills),
        "errorMix": error_mix,
        "skills": skills,
    }


# ---------------------------------------------------------------------------
# Report framing (ported from server.js enrichment)
# ---------------------------------------------------------------------------
def comparison_for_skill(skill, current_grade):
    mastery = skill["mastery"]
    ge = skill.get("gradeEvidence") or {}
    highest = ge.get("highestSuccessfulGrade")
    if mastery >= 0.7 and highest is not None and current_grade is not None and highest > current_grade:
        return {"label": "Ready for more", "tone": "ahead"}
    if mastery >= 0.5:
        return {"label": "On grade level", "tone": "on"}
    if mastery >= 0.36:
        return {"label": "Slightly below", "tone": "slightly"}
    return {"label": "Below grade level", "tone": "below"}


def overall_band(global_ability):
    if global_ability >= 0.7:
        return "Above grade level"
    if global_ability >= 0.46:
        return "On grade level"
    if global_ability >= 0.32:
        return "Approaching grade level"
    return "Below grade level"
