# Python Static Code Analyzer — Requirements Analysis & Test Design

## 1. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | The system shall detect local variables that are assigned but never read within their enclosing function scope. |
| FR2 | The system shall detect naming convention violations: non-snake_case functions/variables, non-PascalCase classes. |
| FR3 | The system shall compute the McCabe cyclomatic complexity of every function in the source file. |
| FR4 | The system shall detect groups of functions with structurally identical bodies (duplicate code), regardless of variable naming. |
| FR5 | The system shall compute aggregate code metrics: lines of code, function count, class count, average complexity. |
| FR6 | The system shall accept a single `.py` file or a directory (recursively) as input via CLI. |
| FR7 | The system shall report a clear error message (not a crash) when given syntactically invalid Python. |

## 2. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | The system shall use only the Python standard library (`ast`, `re`) — no third-party static analysis packages. |
| NFR2 | The system shall analyze a ~500-line file in under 1 second on commodity hardware. |
| NFR3 | The system shall run fully offline with no network dependency. |
| NFR4 | Test suite shall achieve ≥90% line coverage of the analysis module. |

## 3. Assumptions

- Input is valid Python 3 syntax unless explicitly testing the invalid-input path (FR7).
- "Unused" means never referenced by name anywhere within that variable's own scope (not across scopes).
- Single-character identifiers (`i`, `j`, `x`, `_`) are exempt from naming checks — an accepted convention for short-lived loop variables.
- Two functions are "duplicates" only if their control-flow structure AND literal values match — matching structure alone (with different constants) is not flagged, to avoid false positives on genuinely different logic.

## 4. Constraints

- No third-party static analysis libraries (defeats the purpose of the assignment).
- Analysis is purely static (AST-based) — the target code is never executed.

## 5. Expected System Behaviours (≥10 required)

| # | Behaviour |
|---|-----------|
| 1 | Detects a simple unused local variable |
| 2 | Does not flag a variable that is later read |
| 3 | Does not flag function parameters (positional, *args, **kwargs, keyword-only) as unused |
| 4 | Detects camelCase function names as naming violations |
| 5 | Detects snake_case class names as naming violations |
| 6 | Computes cyclomatic complexity = 1 for a straight-line function |
| 7 | Increments complexity per decision point (if/elif, for, while, except, and/or, ternary) |
| 8 | Flags two or more functions with identical structure AND literal values as duplicates |
| 9 | Does not flag functions that share structure but differ in literal values |
| 10 | Reports correct LOC/function/class counts, including for an empty file |
| 11 | Raises a clear `SyntaxError` (not an unhandled crash) on invalid Python input |
| 12 | Function/variable scopes are independent — a nested function's locals don't leak into the outer function's analysis |

## 6. Boundary Conditions Covered

- Empty file (all five analyses return zero/empty results, not errors)
- Single-character variable/loop names (exempt from naming + unused-variable rules)
- Nested function and class scopes (each analyzed independently)
- Trivial one-line functions (excluded from duplicate detection to avoid noisy false positives on getters/setters)
- `*args` / `**kwargs` / keyword-only parameters (must not be misidentified as unused locals)
- Async functions and `async for` loops (must be handled by the same complexity/scope logic as sync code)

## 7. Invalid Input Scenarios Covered

- Syntactically invalid Python source (unclosed parenthesis, etc.) → `SyntaxError` raised, caught and reported cleanly by the CLI rather than crashing.

## 8. Test Design — Traceability Matrix

Every requirement and behaviour above is covered by at least one automated test. Each test file's module docstring documents *what* is tested, *why* it matters, and *what defect it prevents* — satisfying the "test design must include rationale" requirement.

| Requirement / Behaviour | Test file | Representative test(s) |
|---|---|---|
| FR1, Behaviours 1–3, 12 | `tests/test_unused_variables.py` | `test_detects_simple_unused_variable`, `test_does_not_flag_function_parameters`, `test_varargs_and_kwargs_are_not_flagged_as_unused`, `test_nested_function_scopes_are_independent` |
| FR2, Behaviours 4–5 | `tests/test_naming_violations.py` | `test_flags_camel_case_function_name`, `test_flags_snake_case_class_name`, `test_single_letter_loop_variable_is_not_flagged` |
| FR3, Behaviours 6–7 | `tests/test_complexity.py` | `test_straight_line_function_has_complexity_one`, `test_if_elif_else_counts_each_branch_condition`, `test_boolean_and_or_add_complexity`, `test_ternary_expression_adds_one` |
| FR4, Behaviours 8–9 | `tests/test_duplicate_code.py` | `test_two_structurally_identical_functions_are_flagged`, `test_structurally_different_functions_are_not_flagged` |
| FR5, Behaviour 10 | `tests/test_metrics.py` | `test_counts_functions_and_classes`, `test_empty_file_has_zeroed_metrics` |
| FR7, Invalid input | `tests/test_unused_variables.py` | `test_invalid_syntax_raises_syntax_error_not_crash` |
| NFR4 (coverage) | full suite | 43 tests, 98% line coverage of `src/analyzer.py` (see `coverage_report/index.html`) |

## 9. Test Suite Summary

- **43 automated tests** across 5 test modules, one module per analysis feature.
- Each test group includes: normal-behaviour cases, boundary cases, and invalid-input cases where applicable — as required by Task 1.
- Every test was written *before* the corresponding implementation (TDD red→green), with the red-phase failure captured as evidence for Task 2.
