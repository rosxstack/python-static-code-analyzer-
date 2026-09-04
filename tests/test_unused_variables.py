"""
Tests for unused-variable detection.

What's being tested: whether a local variable is assigned but never
subsequently read within its enclosing function scope.

Why necessary: unused variables are a common sign of leftover debug
code, incomplete refactors, or logic errors (e.g. computing a value
and forgetting to use it).

Defect prevented: dead code / wasted computation going unnoticed,
and mistaken variable names (e.g. assigning `result` but returning
`result2` by typo).
"""
import pytest
from src.analyzer import find_unused_variables


def test_detects_simple_unused_variable():
    code = "def foo():\n    x = 5\n    return 1\n"
    result = find_unused_variables(code)
    assert len(result) == 1
    assert result[0]["name"] == "x"
    assert result[0]["line"] == 2


def test_does_not_flag_variable_that_is_read():
    code = "def foo():\n    x = 5\n    return x\n"
    result = find_unused_variables(code)
    assert result == []


def test_does_not_flag_function_parameters():
    code = "def foo(x, y):\n    return 1\n"
    result = find_unused_variables(code)
    assert result == []


def test_flags_multiple_unused_variables_in_same_function():
    code = "def foo():\n    x = 1\n    y = 2\n    return 3\n"
    result = find_unused_variables(code)
    names = {r["name"] for r in result}
    assert names == {"x", "y"}


def test_variable_reassigned_and_then_used_is_not_flagged():
    code = "def foo():\n    x = 1\n    x = 2\n    return x\n"
    result = find_unused_variables(code)
    assert result == []


def test_underscore_convention_is_not_flagged():
    # `_` is a common "intentionally discarded" convention
    code = "def foo():\n    _ = compute()\n    return 1\n"
    result = find_unused_variables(code)
    assert result == []


def test_nested_function_scopes_are_independent():
    code = (
        "def outer():\n"
        "    a = 1\n"
        "    def inner():\n"
        "        b = 2\n"
        "        return 3\n"
        "    return a\n"
    )
    result = find_unused_variables(code)
    names = {r["name"] for r in result}
    assert names == {"b"}


def test_empty_file_returns_no_unused_variables():
    result = find_unused_variables("")
    assert result == []


def test_invalid_syntax_raises_syntax_error_not_crash():
    with pytest.raises(SyntaxError):
        find_unused_variables("def foo(:\n    pass")


def test_varargs_and_kwargs_are_not_flagged_as_unused():
    code = "def foo(*args, **kwargs):\n    return 1\n"
    result = find_unused_variables(code)
    assert result == []


def test_keyword_only_argument_is_not_flagged():
    code = "def foo(*, x):\n    return 1\n"
    result = find_unused_variables(code)
    assert result == []


def test_class_defined_inside_function_is_not_treated_as_local_variable():
    code = (
        "def outer():\n"
        "    class Inner:\n"
        "        pass\n"
        "    return Inner\n"
    )
    result = find_unused_variables(code)
    assert result == []
