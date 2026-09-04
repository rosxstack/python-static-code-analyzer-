"""
Command-line entry point for the Python Static Code Analyzer.

Usage:
    python cli.py path/to/file.py
    python cli.py path/to/directory/
"""
import sys
from pathlib import Path

from src.analyzer import (
    find_unused_variables,
    find_naming_violations,
    compute_complexity,
    find_duplicate_code,
    compute_metrics,
)


def analyze_file(path: Path):
    source = path.read_text()
    print(f"\n=== {path} ===")
    try:
        metrics = compute_metrics(source)
    except SyntaxError as e:
        print(f"  SYNTAX ERROR: {e}")
        return

    print(f"  Lines of code:        {metrics['lines_of_code']}")
    print(f"  Functions:            {metrics['function_count']}")
    print(f"  Classes:              {metrics['class_count']}")
    print(f"  Average complexity:   {metrics['average_complexity']:.2f}")

    unused = find_unused_variables(source)
    if unused:
        print("  Unused variables:")
        for u in unused:
            print(f"    line {u['line']}: '{u['name']}'")

    naming = find_naming_violations(source)
    if naming:
        print("  Naming violations:")
        for n in naming:
            print(f"    line {n['line']}: {n['kind']} '{n['name']}'")

    complexity = compute_complexity(source)
    high_complexity = [c for c in complexity if c["complexity"] > 5]
    if high_complexity:
        print("  High complexity functions (>5):")
        for c in high_complexity:
            print(f"    line {c['line']}: '{c['name']}' = {c['complexity']}")

    duplicates = find_duplicate_code(source)
    if duplicates:
        print("  Duplicate code groups:")
        for d in duplicates:
            print(f"    {', '.join(d['functions'])}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_dir():
        for py_file in sorted(target.rglob("*.py")):
            analyze_file(py_file)
    else:
        analyze_file(target)


if __name__ == "__main__":
    main()
