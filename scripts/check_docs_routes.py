#!/usr/bin/env python3
"""Check API endpoint docs against route declarations."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def normalize_path(path: str) -> str:
    normalized = path.strip()
    normalized = re.sub(r"<[^>]+>", "{param}", normalized)
    normalized = re.sub(r"\{[^}]+\}", "{param}", normalized)
    normalized = re.sub(r"/{2,}", "/", normalized)
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def _extract_methods(call: ast.Call) -> Set[str]:
    methods: Set[str] = {"GET"}
    for kw in call.keywords:
        if kw.arg != "methods":
            continue
        methods = set()
        if isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    method = elt.value.upper()
                    if method in METHODS:
                        methods.add(method)
        if not methods:
            methods = {"GET"}
    return methods


def _extract_fastapi_method(func: ast.AST) -> Optional[str]:
    if not isinstance(func, ast.Attribute):
        return None
    candidate = func.attr.upper()
    if candidate in METHODS:
        return candidate
    return None


def extract_code_routes(files: Iterable[Path]) -> Set[Tuple[str, str]]:
    routes: Set[Tuple[str, str]] = set()

    for file_path in files:
        tree = ast.parse(read_text(file_path), filename=str(file_path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                method_from_fastapi = _extract_fastapi_method(func)

                if method_from_fastapi is None and (not isinstance(func, ast.Attribute) or func.attr != "route"):
                    continue
                if not dec.args:
                    continue
                first_arg = dec.args[0]
                if not isinstance(first_arg, ast.Constant) or not isinstance(first_arg.value, str):
                    continue

                path = normalize_path(first_arg.value)
                if method_from_fastapi is not None:
                    methods = {method_from_fastapi}
                else:
                    methods = _extract_methods(dec)
                for method in methods:
                    routes.add((method, path))

    return routes


def extract_doc_routes(file_path: Path) -> Set[Tuple[str, str]]:
    routes: Set[Tuple[str, str]] = set()

    for raw_line in read_text(file_path).splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue

        columns = [c.strip() for c in line.strip("|").split("|")]
        if len(columns) < 2:
            continue

        method = columns[0].upper()
        path = columns[1].strip("`")

        if method not in METHODS:
            continue
        if not path.startswith("/"):
            continue

        routes.add((method, normalize_path(path)))

    return routes


def report_diff(name: str, expected: Set[Tuple[str, str]], actual: Set[Tuple[str, str]]) -> List[str]:
    lines: List[str] = []

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    if missing:
        lines.append(f"[{name}] Missing endpoints:")
        lines.extend(f"  - {method} {path}" for method, path in missing)

    if extra:
        lines.append(f"[{name}] Unknown endpoints (not in code):")
        lines.extend(f"  - {method} {path}" for method, path in extra)

    return lines


def check_readme_links(readme_text: str) -> List[str]:
    required_links = ["docs/API.md", "docs/ARCHITECTURE.md"]
    errors: List[str] = []
    for link in required_links:
        if link not in readme_text:
            errors.append(f"[README.md] Missing required link: {link}")
    return errors


def main() -> int:
    route_files = [
        PROJECT_ROOT / "app" / "__init__.py",
        PROJECT_ROOT / "app" / "observability.py",
        PROJECT_ROOT / "app" / "routes" / "news.py",
        PROJECT_ROOT / "app" / "routes" / "minutes.py",
        PROJECT_ROOT / "app" / "routes" / "segments.py",
    ]

    readme_file = PROJECT_ROOT / "README.md"
    api_file = PROJECT_ROOT / "docs" / "API.md"

    for file_path in [*route_files, readme_file, api_file]:
        if not file_path.exists():
            print(f"Required file not found: {file_path}")
            return 2

    code_routes = extract_code_routes(route_files)
    api_routes = extract_doc_routes(api_file)
    readme_text = read_text(readme_file)

    errors: List[str] = []
    errors.extend(report_diff("docs/API.md", code_routes, api_routes))
    errors.extend(check_readme_links(readme_text))

    if errors:
        print("Route-documentation contract check failed.\n")
        print("\n".join(errors))
        return 1

    print(
        "Route-documentation contract check passed: "
        f"{len(code_routes)} endpoints verified in docs/API.md, README links verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
