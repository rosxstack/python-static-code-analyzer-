"""
Tests for cyclomatic complexity calculation.

What's being tested: the McCabe cyclomatic complexity of each
function, computed as 1 + number of independent decision points
(if/elif, for, while, except, boolean and/or, ternary).

Why necessary: high complexity correlates strongly with bug density
and poor testability -- a function with complexity 20 needs far
more test cases to cover than one with complexity 2.

Defect prevented: overly complex, hard-to-test, hard-to-maintain
functions going unnoticed until they cause a production bug.
"""
import pytest
from src.analyzer import compute_complexity


def test_straight_line_function_has_complexity_one():
    code = "def foo():\n    x = 1\n    y = 2\n    return x + y\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 1


def test_single_if_adds_one():
    code = "def foo(x):\n    if x > 0:\n        return 1\n    return 0\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 2


def test_if_elif_else_counts_each_branch_condition():
    code = (
        "def foo(x):\n"
        "    if x > 0:\n"
        "        return 1\n"
        "    elif x < 0:\n"
        "        return -1\n"
        "    else:\n"
        "        return 0\n"
    )
    result = compute_complexity(code)
    # base 1 + if + elif = 3 (else adds no new decision point)
    assert result[0]["complexity"] == 3


def test_for_loop_adds_one():
    code = "def foo(items):\n    for i in items:\n        pass\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 2


def test_while_loop_adds_one():
    code = "def foo():\n    while True:\n        pass\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 2


def test_except_clause_adds_one():
    code = "def foo():\n    try:\n        pass\n    except ValueError:\n        pass\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 2


def test_boolean_and_or_add_complexity():
    code = "def foo(a, b, c):\n    if a and b or c:\n        return 1\n    return 0\n"
    result = compute_complexity(code)
    # base 1 + if(1) + and(1) + or(1) = 4
    assert result[0]["complexity"] == 4


def test_multiple_functions_each_reported_separately():
    code = (
        "def simple():\n    return 1\n\n"
        "def complex_one(x):\n    if x:\n        return 1\n    return 0\n"
    )
    result = compute_complexity(code)
    by_name = {r["name"]: r["complexity"] for r in result}
    assert by_name["simple"] == 1
    assert by_name["complex_one"] == 2

def test_empty_file_returns_empty_list():
    assert compute_complexity("") == []


def test_ternary_expression_adds_one():
    code = "def foo(x):\n    return 1 if x else 0\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 2


def test_async_for_loop_adds_one():
    code = "async def foo(items):\n    async for i in items:\n        pass\n"
    result = compute_complexity(code)
    assert result[0]["complexity"] == 2


def test_nested_function_is_measured_independently_from_outer():
    code = (
        "def outer():\n"
        "    def inner(x):\n"
        "        if x:\n"
        "            return 1\n"
        "        return 0\n"
        "    return inner\n"
    )
    result = compute_complexity(code)
    by_name = {r["name"]: r["complexity"] for r in result}
    assert by_name["outer"] == 1
    assert by_name["inner"] == 2


def test_class_defined_inside_function_does_not_affect_function_complexity():
    code = (
        "def outer():\n"
        "    class Inner:\n"
        "        def method(self, x):\n"
        "            if x:\n"
        "                return 1\n"
        "    return Inner\n"
    )
    result = compute_complexity(code)
    by_name = {r["name"]: r["complexity"] for r in result}
    assert by_name["outer"] == 1
    assert by_name["method"] == 2
