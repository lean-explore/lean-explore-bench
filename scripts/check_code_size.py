"""Fail if a function or file is too long.

Limits: 40 lines of code per function or method (its docstring does not
count) and 500 lines per file. Run in CI: ``python scripts/check_code_size.py``.
"""

import ast
import sys
from pathlib import Path

MAX_FUNCTION_LINES = 40
MAX_FILE_LINES = 500
ROOTS = ("src", "tests", "scripts")


def _code_start(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    first = node.body[0]
    is_docstring = (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    )
    if is_docstring and len(node.body) > 1:
        return node.body[1].lineno
    return first.lineno


def problems(path: Path) -> list[str]:
    """Describe every limit a file breaks.

    Args:
        path: A Python file.

    Returns:
        One message per violation.
    """
    source = path.read_text(encoding="utf-8")
    found = []
    n_lines = source.count("\n")
    if n_lines > MAX_FILE_LINES:
        found.append(f"{path}: {n_lines} lines (limit {MAX_FILE_LINES})")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            length = (node.end_lineno or node.lineno) - _code_start(node) + 1
            if length > MAX_FUNCTION_LINES:
                found.append(
                    f"{path}:{node.lineno} {node.name}: {length} lines of code "
                    f"(limit {MAX_FUNCTION_LINES})"
                )
    return found


def main() -> int:
    """Run the check.

    Returns:
        Process exit code.
    """
    found = [
        message
        for root in ROOTS
        for path in sorted(Path(root).rglob("*.py"))
        for message in problems(path)
    ]
    for message in found:
        print(message, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
