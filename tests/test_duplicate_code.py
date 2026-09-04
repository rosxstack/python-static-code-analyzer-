"""
Tests for duplicate code detection.

What's being tested: whether two or more functions have
structurally identical bodies (same logic, possibly with different
variable names) -- a sign of copy-paste code that should be
refactored into a shared helper.

Why necessary: duplicated logic means bug fixes and improvements
have to be made in multiple places, and is easy to miss when only
one copy gets updated.

Defect prevented: divergent bug fixes (fixing a bug in one copy
but not its duplicate), and unnecessary maintenance burden.
"""
import pytest
from src.analyzer import find_duplicate_code


def test_two_structurally_identical_functions_are_flagged():
    code = (
        "def add_one(x):\n"
        "    result = x + 1\n"
        "    return result\n\n"
        "def add_one_v2(y):\n"
        "    result = y + 1\n"
        "    return result\n"
    )
    result = find_duplicate_code(code)
    assert len(result) == 1
    names = set(result[0]["functions"])
    assert names == {"add_one", "add_one_v2"}


def test_structurally_different_functions_are_not_flagged():
    code = (
        "def add(x, y):\n"
        "    return x + y\n\n"
        "def multiply(x, y):\n"
        "    return x * y\n"
    )
    result = find_duplicate_code(code)
    assert result == []


def test_trivial_one_line_functions_are_not_flagged():
    # avoids noisy false positives on trivial getters/setters
    code = (
        "def get_x(self):\n"
        "    return self.x\n\n"
        "def get_y(self):\n"
        "    return self.y\n"
    )
    result = find_duplicate_code(code)
    assert result == []


def test_three_identical_functions_grouped_together():
    body = "def {name}(n):\n    total = n * 2\n    total = total + 1\n    return total\n\n"
    code = body.format(name="f1") + body.format(name="f2") + body.format(name="f3")
    result = find_duplicate_code(code)
    assert len(result) == 1
    assert set(result[0]["functions"]) == {"f1", "f2", "f3"}


def test_empty_file_returns_no_duplicates():
    assert find_duplicate_code("") == []


def test_regression_literal_value_differences_prevent_false_duplicate_flag():
    """
    Regression test.

    During manual evaluation (see Task 3 of the report) an early
    version of this feature was checked against two functions that
    were structurally identical but used different literal constants
    (42 vs 99). This test locks in the corrected behaviour: functions
    are only flagged as duplicates when BOTH structure and literal
    values match, preventing false positives on genuinely different
    logic that merely looks similar.
    """
    code = (
        "def foo():\n"
        "    x = []\n"
        "    unused_var = 42\n"
        "    return x\n\n"
        "def bar():\n"
        "    y = []\n"
        "    unused = 99\n"
        "    return y\n"
    )
    result = find_duplicate_code(code)
    assert result == []


def test_identifies_duplicate_methods_that_differ_only_by_attribute_name():
    """
    Deep evaluation finding (see report Task 3): the initial normalizer
    only stripped plain variable names, missing a whole class of
    real-world duplicates in OOP code where the difference is a
    self.<attribute> name rather than a local variable name.
    """
    code = (
        "class Calc:\n"
        "    def add(self, a, b):\n"
        "        self.result = a + b\n"
        "        return self.result\n\n"
        "    def add_v2(self, a, b):\n"
        "        self.total = a + b\n"
        "        return self.total\n"
    )
    result = find_duplicate_code(code)
    assert len(result) == 1
    assert set(result[0]["functions"]) == {"add", "add_v2"}


def test_regression_different_method_calls_are_never_falsely_matched():
    """
    Regression test guarding the fix above: normalizing attribute
    NAMES (self.result vs self.total) must never normalize METHOD
    call names (.append vs .extend) -- those represent genuinely
    different behaviour and must not be flagged as duplicates.
    """
    code = (
        "class Foo:\n"
        "    def add_item(self, x):\n"
        "        self.items.append(x)\n"
        "        return self.items\n\n"
        "    def add_all(self, x):\n"
        "        self.items.extend(x)\n"
        "        return self.items\n"
    )
    result = find_duplicate_code(code)
    assert result == []
