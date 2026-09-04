"""
Python Static Code Analyzer.

Analyzes Python source code for:
  - unused variables
  - naming convention violations
  - cyclomatic complexity
  - duplicate code
  - general code metrics

Uses only the Python standard library (ast, re) -- no third-party
static analysis packages, per assignment constraints.
"""
import ast
import re

_SNAKE_CASE_RE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*$|^_+$")
_PASCAL_CASE_RE = re.compile(r"^_{0,2}[A-Z][a-zA-Z0-9]*$")
_ALL_CAPS_RE = re.compile(r"^_{0,2}[A-Z][A-Z0-9_]*$")


class _ScopeVisitor(ast.NodeVisitor):
    """
    Walks a single function/module scope, tracking every name that is
    assigned (a "binding") and every name that is read (a "load").
    Nested functions/classes get their own independent visitor so
    that scopes don't leak into each other.
    """

    def __init__(self):
        self.assigned = {}  # name -> lineno of first assignment
        self.used = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            if node.id not in self.assigned:
                self.assigned[node.id] = node.lineno
        elif isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Don't descend into nested functions here; they're handled
        # as their own separate scope by the caller.
        pass

    def visit_AsyncFunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass


def _collect_function_scopes(tree):
    """Yield every FunctionDef/AsyncFunctionDef node in the tree, at any depth."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def find_unused_variables(source: str):
    """
    Return a list of {"name": str, "line": int} for local variables
    that are assigned but never read, within each function's own scope.

    Function parameters are never flagged. Names starting with an
    underscore (the "intentionally discarded" convention) are never
    flagged.
    """
    tree = ast.parse(source)  # raises SyntaxError on invalid input
    findings = []

    for func in _collect_function_scopes(tree):
        visitor = _ScopeVisitor()
        for stmt in func.body:
            visitor.visit(stmt)

        param_names = {a.arg for a in func.args.args}
        param_names |= {a.arg for a in func.args.kwonlyargs}
        if func.args.vararg:
            param_names.add(func.args.vararg.arg)
        if func.args.kwarg:
            param_names.add(func.args.kwarg.arg)

        for name, line in visitor.assigned.items():
            if name in param_names:
                continue
            if name.startswith("_"):
                continue
            if name not in visitor.used:
                findings.append({"name": name, "line": line})

    return findings


def find_naming_violations(source: str):
    """
    Return a list of {"name": str, "line": int, "kind": str} for
    identifiers that violate PEP 8 naming conventions:
      - functions: snake_case
      - classes: PascalCase
      - variables: snake_case (module-level ALL_CAPS constants exempt)

    Single-character names (i, j, x, _, ...) are exempt -- common,
    accepted convention for short-lived loop/throwaway variables.
    """
    tree = ast.parse(source)
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _SNAKE_CASE_RE.match(node.name):
                violations.append(
                    {"name": node.name, "line": node.lineno, "kind": "function"}
                )
        elif isinstance(node, ast.ClassDef):
            if not _PASCAL_CASE_RE.match(node.name):
                violations.append(
                    {"name": node.name, "line": node.lineno, "kind": "class"}
                )

    # Variables: walk module body and every function body looking for
    # Name nodes in Store context, skipping single-char and ALL_CAPS names.
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
            if len(name) <= 1:
                continue
            if _ALL_CAPS_RE.match(name):
                continue
            if not _SNAKE_CASE_RE.match(name):
                violations.append(
                    {"name": name, "line": node.lineno, "kind": "variable"}
                )

    return violations


class _ComplexityVisitor(ast.NodeVisitor):
    """
    Counts McCabe decision points within a single function's body
    (not descending into nested function/class definitions -- those
    are measured independently).
    """

    def __init__(self):
        self.decisions = 0

    def visit_If(self, node):
        self.decisions += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.decisions += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.decisions += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.decisions += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.decisions += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # `a and b and c` has 2 operators joining 3 values -> +2
        self.decisions += len(node.values) - 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        # ternary expression: `x if cond else y`
        self.decisions += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        pass  # don't descend into nested functions

    def visit_AsyncFunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass


def compute_complexity(source: str):
    """
    Return a list of {"name": str, "line": int, "complexity": int}
    giving the McCabe cyclomatic complexity of each function.
    Complexity starts at 1 (a single straight-line path) and gains
    1 for every independent decision point (if/elif, for, while,
    except, ternary, and/or).
    """
    tree = ast.parse(source)
    results = []

    for func in _collect_function_scopes(tree):
        visitor = _ComplexityVisitor()
        for stmt in func.body:
            visitor.visit(stmt)
        results.append(
            {
                "name": func.name,
                "line": func.lineno,
                "complexity": 1 + visitor.decisions,
            }
        )

    return results


class _Normalizer(ast.NodeTransformer):
    """
    Replaces every identifier name (variables, arguments) with a
    placeholder so that two functions with the same *structure* but
    different variable names compare equal. Function/argument names
    themselves are not part of the body being compared.
    """

    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id="_VAR_", ctx=node.ctx), node)

    def visit_arg(self, node):
        new_arg = ast.arg(arg="_ARG_", annotation=None)
        return ast.copy_location(new_arg, node)

    def visit_Call(self, node):
        # Preserve method-call names (e.g. .append vs .extend) so two
        # genuinely different operations are never conflated as
        # "duplicates" just because their receivers normalize the same.
        # Only the receiver (e.g. `self`, or an earlier attribute chain)
        # is normalized -- the called method's name is left untouched.
        if isinstance(node.func, ast.Attribute):
            new_receiver = self.visit(node.func.value)
            new_func = ast.copy_location(
                ast.Attribute(value=new_receiver, attr=node.func.attr, ctx=node.func.ctx),
                node.func,
            )
        else:
            new_func = self.visit(node.func)
        new_args = [self.visit(a) for a in node.args]
        new_keywords = [self.visit(k) for k in node.keywords]
        return ast.copy_location(
            ast.Call(func=new_func, args=new_args, keywords=new_keywords), node
        )

    def visit_Attribute(self, node):
        # Normalize instance-attribute access (e.g. self.result vs
        # self.total) so structurally identical methods are recognized
        # as duplicates even if they touch differently-named attributes.
        # Method-call attribute names are protected from this by
        # visit_Call above, which runs first for `obj.method(...)`.
        new_value = self.visit(node.value)
        return ast.copy_location(
            ast.Attribute(value=new_value, attr="_ATTR_", ctx=node.ctx), node
        )


def _normalized_dump(func_node):
    clone = ast.parse(ast.unparse(func_node)).body[0]
    normalized = _Normalizer().visit(clone)
    # Strip the function's own name so only the body structure counts
    normalized.name = "_FUNC_"
    return ast.dump(normalized, annotate_fields=False)


def find_duplicate_code(source: str, min_statements: int = 2):
    """
    Return a list of {"functions": [names...]} groups where each
    group of functions has structurally identical bodies (same
    control flow and operations, regardless of variable names).

    Functions with fewer than `min_statements` statements are
    skipped to avoid flagging trivial one-line getters as
    "duplicates" of each other.
    """
    tree = ast.parse(source)
    groups = {}

    for func in _collect_function_scopes(tree):
        if len(func.body) < min_statements:
            continue
        key = _normalized_dump(func)
        groups.setdefault(key, []).append(func.name)

    return [{"functions": names} for names in groups.values() if len(names) > 1]


def compute_metrics(source: str):
    """
    Return aggregate metrics for the whole file:
      - lines_of_code: non-blank, non-comment-only lines
      - function_count / class_count
      - average_complexity: mean cyclomatic complexity across functions
        (0 if there are no functions)
    """
    tree = ast.parse(source)

    function_count = sum(
        1 for _ in _collect_function_scopes(tree)
    )
    class_count = sum(
        1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    )

    lines_of_code = 0
    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if stripped and not stripped.startswith("#"):
            lines_of_code += 1

    complexities = [c["complexity"] for c in compute_complexity(source)]
    average_complexity = (
        sum(complexities) / len(complexities) if complexities else 0
    )

    return {
        "lines_of_code": lines_of_code,
        "function_count": function_count,
        "class_count": class_count,
        "average_complexity": average_complexity,
    }
