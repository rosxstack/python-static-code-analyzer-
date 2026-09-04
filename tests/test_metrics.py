"""
Tests for aggregate code metrics.

What's being tested: whole-file summary statistics -- lines of
code, function count, class count, and average cyclomatic
complexity across all functions.

Why necessary: gives a quick, at-a-glance health signal for a file
or module without having to read every finding individually.

Defect prevented: no single defect, but supports the "code metrics"
requirement in the assignment and helps spot files that have grown
too large/complex to maintain safely.
"""
import pytest
from src.analyzer import compute_metrics


def test_counts_functions_and_classes():
    code = (
        "class Foo:\n    pass\n\n"
        "def bar():\n    pass\n\n"
        "def baz():\n    pass\n"
    )
    result = compute_metrics(code)
    assert result["function_count"] == 2
    assert result["class_count"] == 1


def test_counts_non_blank_non_comment_lines_of_code():
    code = (
        "# a comment\n"
        "\n"
        "def foo():\n"
        "    x = 1  # inline comment doesn't remove the line\n"
        "    return x\n"
    )
    result = compute_metrics(code)
    # lines counted: "def foo():", "    x = 1  ...", "    return x" = 3
    assert result["lines_of_code"] == 3


def test_average_complexity_is_computed_correctly():
    code = (
        "def simple():\n    return 1\n\n"
        "def branchy(x):\n    if x:\n        return 1\n    return 0\n"
    )
    result = compute_metrics(code)
    # complexities: 1 and 2 -> average 1.5
    assert result["average_complexity"] == 1.5


def test_empty_file_has_zeroed_metrics():
    result = compute_metrics("")
    assert result["function_count"] == 0
    assert result["class_count"] == 0
    assert result["lines_of_code"] == 0
    assert result["average_complexity"] == 0


def test_file_with_no_functions_has_zero_average_complexity_not_error():
    code = "x = 1\ny = 2\n"
    result = compute_metrics(code)
    assert result["average_complexity"] == 0
