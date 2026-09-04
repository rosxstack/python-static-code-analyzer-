"""
Tests for naming convention violations (PEP 8).

What's being tested: functions/variables should be snake_case,
classes should be PascalCase, module-level constants (ALL_CAPS)
are exempt from the snake_case rule.

Why necessary: inconsistent naming hurts readability and signals
either careless AI-generated code or mixed coding conventions
across a team.

Defect prevented: unreadable, inconsistent codebases; misleading
naming (e.g. a class that looks like a function).
"""
import pytest
from src.analyzer import find_naming_violations


def test_flags_camel_case_function_name():
    code = "def myFunction():\n    pass\n"
    result = find_naming_violations(code)
    assert len(result) == 1
    assert result[0]["name"] == "myFunction"
    assert result[0]["kind"] == "function"


def test_does_not_flag_snake_case_function_name():
    code = "def my_function():\n    pass\n"
    result = find_naming_violations(code)
    assert result == []


def test_flags_snake_case_class_name():
    code = "class my_class:\n    pass\n"
    result = find_naming_violations(code)
    assert len(result) == 1
    assert result[0]["name"] == "my_class"
    assert result[0]["kind"] == "class"


def test_does_not_flag_pascal_case_class_name():
    code = "class MyClass:\n    pass\n"
    result = find_naming_violations(code)
    assert result == []


def test_flags_camel_case_variable_name():
    code = "def foo():\n    myVar = 1\n    return myVar\n"
    result = find_naming_violations(code)
    assert len(result) == 1
    assert result[0]["name"] == "myVar"
    assert result[0]["kind"] == "variable"


def test_module_level_all_caps_constant_is_not_flagged():
    code = "MAX_SIZE = 100\n"
    result = find_naming_violations(code)
    assert result == []


def test_single_letter_loop_variable_is_not_flagged():
    # common, accepted convention (i, j, k, x, y, _...)
    code = "def foo():\n    for i in range(10):\n        pass\n"
    result = find_naming_violations(code)
    assert result == []


def test_empty_file_returns_no_violations():
    assert find_naming_violations("") == []
