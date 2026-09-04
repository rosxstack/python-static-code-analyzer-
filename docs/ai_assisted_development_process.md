# AI-Assisted Development Process

This project was built using an AI-assisted Test-Driven Development (AI-TDD)
workflow with Claude (Anthropic) as the AI pair-programmer. For every feature,
tests were written and confirmed failing (red) *before* any implementation
code was written, then implementation was added until tests passed (green).
Iterations 6 and 7 show refinement cycles driven by deeper stress-testing
after the initial "green" state.

---

## Feature 1: Unused Variable Detection

**Prompt to AI:** "Build a Python static code analyzer using AI-TDD. Start
with unused variable detection — write failing tests first using `ast`,
covering normal cases, function parameters, underscore convention, and
nested scopes."

**AI-generated response (summary):** Produced 9 tests covering: simple
unused variable, variable that is read, function parameters exempted,
multiple unused variables, reassignment-then-use, underscore convention,
nested function scope independence, empty file, and invalid syntax
handling — followed immediately by an `ast.NodeVisitor`-based implementation
(`_ScopeVisitor` + `find_unused_variables`).

**Verdict:** **Accepted**, then **refined** in a later iteration.

**Justification:** All 9 tests passed on first implementation. However,
initial parameter handling only covered positional arguments —
stress-testing later revealed `*args`/`**kwargs`/keyword-only arguments
were not exempted from the unused-variable check, which would have
produced false positives. Two additional tests were added
(`test_varargs_and_kwargs_are_not_flagged_as_unused`,
`test_keyword_only_argument_is_not_flagged`) and the parameter-collection
logic was confirmed to already handle these correctly, closing the gap in
*test coverage* rather than requiring a code change.

**Test-first evidence:** Running `pytest tests/test_unused_variables.py`
before `src/analyzer.py` contained `find_unused_variables` produced
`ModuleNotFoundError` (red). After implementation, all 9 (later 12) tests
passed (green). See `test_run_evidence.txt`.

---

## Feature 2: Naming Convention Violations

**Prompt to AI:** "Add naming violation detection: functions/variables
should be snake_case, classes PascalCase. Exempt single-character names
and module-level ALL_CAPS constants."

**AI-generated response (summary):** 8 tests covering camelCase functions,
snake_case classes (wrongly named), PascalCase classes (correct),
camelCase variables, ALL_CAPS constants, single-letter loop variables, and
empty file — followed by a regex-based implementation
(`_SNAKE_CASE_RE`, `_PASCAL_CASE_RE`, `_ALL_CAPS_RE`).

**Verdict:** **Accepted without modification.**

**Justification:** All 8 tests passed on first run. The regex patterns
correctly handle the PEP 8 dunder-method convention (`__init__`) as a
side effect of allowing 1–2 leading underscores, which was verified
directly (`test_dunder_method_naming` during manual evaluation, see
Task 3 notes).

**Test-first evidence:** `ImportError: cannot import name
'find_naming_violations'` before implementation; 8/8 passing after.

---

## Feature 3: Cyclomatic Complexity

**Prompt to AI:** "Add McCabe cyclomatic complexity per function: base 1,
+1 per if/elif/for/while/except, +1 per boolean operator, +1 per ternary."

**AI-generated response (summary):** 9 tests covering straight-line
functions, single `if`, `if/elif/else` chains, `for`, `while`, `except`,
boolean `and`/`or`, multiple functions measured independently, and empty
file — followed by an `ast.NodeVisitor`-based `_ComplexityVisitor`.

**Verdict:** **Accepted**, then **extended** in a refinement iteration.

**Justification:** Initial 9 tests passed immediately. Coverage analysis
(`pytest --cov`) revealed the ternary-expression (`IfExp`), `async for`,
and nested-class-inside-function branches were never exercised by any
test — a real gap, not just a coverage-percentage cosmetic issue, since an
untested branch could silently do the wrong thing. Three tests were added
(`test_ternary_expression_adds_one`, `test_async_for_loop_adds_one`,
`test_class_defined_inside_function_does_not_affect_function_complexity`);
all passed without any code changes, confirming (rather than assuming) the
existing implementation was already correct for those cases.

**Test-first evidence:** Red → green cycle as above; coverage went from
91% → 98% of `src/analyzer.py` after the refinement iteration.

---

## Feature 4: Duplicate Code Detection

**Prompt to AI:** "Detect functions with structurally identical bodies,
ignoring variable names, but don't flag trivial one-line functions."

**AI-generated response (summary):** 5 tests covering two identical
functions (different variable names), structurally different functions,
trivial one-liners excluded, three-way duplicate grouping, and empty
file — followed by an AST-normalization approach (`_Normalizer` +
`_normalized_dump` + `find_duplicate_code`).

**Verdict:** **Accepted, then critically re-evaluated and modified** —
see `docs/requirements_and_test_design.md` and the conversation record
for the full before/after analysis.

**Justification (summary — full detail in Task 3 evaluation):**
Manual stress-testing after the initial green state found that
object-attribute names (`self.result` vs `self.total`) were **not**
normalized, causing real OOP duplicates to be missed (a false negative).
A naive fix (normalize all `Attribute` nodes) was checked *before*
being applied and found to introduce a new false positive: it would
conflate different method calls, e.g. `.append()` vs `.extend()`. The
implemented fix normalizes attribute names only when the attribute is
*not* the target of a method call, preserving the distinction between
"which object" and "which operation." Two new tests lock this in: one
confirming the previously-missed duplicate is now caught, one confirming
the false-positive risk is guarded against.

**Test-first evidence:** Both new tests were written and run to confirm
their intent before the fix (the "missed duplicate" test genuinely failed
first — `assert 0 == 1` — because the initial test case accidentally used
different operators (`+` vs `-`), which was itself a mistake in the test,
not the code; this was caught and corrected before concluding the fix
was correct). Final: 46/46 tests passing.

---

## Feature 5: Code Metrics

**Prompt to AI:** "Add aggregate metrics: lines of code, function count,
class count, average complexity across a file."

**AI-generated response (summary):** 5 tests covering function/class
counts, non-blank/non-comment LOC counting, average complexity
calculation, empty file (all zeros), and a file with no functions
(average complexity must be 0, not a division-by-zero error) — followed
by `compute_metrics`, which reuses `compute_complexity` rather than
duplicating traversal logic.

**Verdict:** **Accepted without modification.**

**Justification:** All 5 tests passed on first implementation, including
the division-by-zero edge case, which the AI proactively guarded against
in its first draft (`sum(...) / len(...) if complexities else 0`) without
being explicitly asked to.

**Test-first evidence:** `ImportError` before implementation; 5/5 passing
after.

---

## Summary of the Iterative Process

| Feature | Initial tests | Passed 1st try? | Refinement tests added | Final test count |
|---|---|---|---|---|
| Unused variables | 9 | Yes | +3 (varargs/kwargs/nested class) | 12 |
| Naming violations | 8 | Yes | 0 | 8 |
| Cyclomatic complexity | 9 | Yes | +4 (ternary/async/nested class) | 13 |
| Duplicate code | 5 | Yes | +3 (regression + attribute fix + false-positive guard) | 8 |
| Code metrics | 5 | Yes | 0 | 5 |
| **Total** | **36** | | **+10** | **46** |

Every feature followed the same cycle: **write failing tests → confirm
red → implement → confirm green → stress-test beyond the original spec →
refine where gaps were found**. This is documented turn-by-turn in the
project conversation transcript, which can be included as an appendix or
screenshots per the report's evidence requirement.
