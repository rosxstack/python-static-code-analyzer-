# Python Static Code Analyzer

A static code analysis tool built with an AI-assisted Test-Driven
Development (AI-TDD) workflow, for PRT582 Software Unit Testing.

Given Python source code, the analyzer detects:

- **Unused variables** — assigned but never read
- **Naming convention violations** — non-snake_case functions/variables, non-PascalCase classes
- **Cyclomatic complexity** — McCabe complexity per function
- **Duplicate code** — structurally identical functions, regardless of variable naming
- **Code metrics** — lines of code, function/class counts, average complexity

Built using only the Python standard library (`ast`, `re`) — no third-party static analysis packages.

## Project Structure

```
.
├── src/
│   └── analyzer.py          # All 5 analysis features
├── tests/
│   ├── test_unused_variables.py
│   ├── test_naming_violations.py
│   ├── test_complexity.py
│   ├── test_duplicate_code.py
│   └── test_metrics.py
├── cli.py                   # Command-line entry point
├── docs/
│   ├── requirements_and_test_design.md      # Task 1: spec + traceability matrix
│   └── ai_assisted_development_process.md   # Task 2: AI-TDD process per feature
├── coverage_report/         # HTML test coverage report
└── test_run_evidence.txt    # Captured full test run output
```

## Setup

Requires Python 3.8+.

```bash
pip install pytest pytest-cov
```

## Running the tests

```bash
python -m pytest tests/ -v
```

Expected result: **46 tests passing**, ~97% coverage of `src/analyzer.py`.

To generate an HTML coverage report:

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in a browser.

## Running the analyzer

On a single file:

```bash
python cli.py path/to/file.py
```

On a whole directory (recursively analyzes every `.py` file):

```bash
python cli.py path/to/directory/
```

Example output:

```
=== src/analyzer.py ===
  Lines of code:        149
  Functions:            18
  Classes:              4
  Average complexity:   2.10
```

## Development approach

This project was built using strict Test-Driven Development: for every
feature, tests were written and confirmed failing *before* any
implementation code was written. See `docs/ai_assisted_development_process.md`
for the full prompt-by-prompt breakdown, including a documented case
where deeper stress-testing surfaced a real bug (duplicate-code
detection missing object-attribute name differences) and the fix that
was verified not to introduce new false positives.

## Test evidence

- 46 automated tests, all passing
- 97% line coverage of `src/analyzer.py`
- See `test_run_evidence.txt` and `coverage_report/` for full evidence
