#!/usr/bin/env python3
"""Validate single-source app version and changelog consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = PROJECT_ROOT / "app" / "version.py"
APP_INIT_FILE = PROJECT_ROOT / "app" / "__init__.py"
CHANGELOG_FILE = PROJECT_ROOT / "docs" / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_ASSIGN_RE = re.compile(r'^\s*APP_VERSION\s*=\s*"([^"]+)"\s*$', re.MULTILINE)
HARDCODED_FASTAPI_VERSION_RE = re.compile(r'version\s*=\s*"[^"]+"')


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def load_app_version() -> str:
    if not VERSION_FILE.exists():
        raise RuntimeError(f"Missing version file: {VERSION_FILE}")
    content = read_text(VERSION_FILE)
    match = VERSION_ASSIGN_RE.search(content)
    if not match:
        raise RuntimeError("app/version.py must define APP_VERSION = \"X.Y.Z\".")
    return match.group(1)


def main() -> int:
    try:
        version = load_app_version()
    except RuntimeError as exc:
        print(f"Version consistency check failed: {exc}")
        return 1

    errors: list[str] = []
    if not SEMVER_RE.match(version):
        errors.append(f"APP_VERSION must be SemVer (X.Y.Z): {version}")

    if not APP_INIT_FILE.exists():
        errors.append(f"Missing app init file: {APP_INIT_FILE}")
    else:
        app_init = read_text(APP_INIT_FILE)
        if "from app.version import APP_VERSION" not in app_init:
            errors.append("app/__init__.py must import APP_VERSION from app/version.py")
        if "version=APP_VERSION" not in app_init:
            errors.append("FastAPI version must use APP_VERSION (version=APP_VERSION)")
        if HARDCODED_FASTAPI_VERSION_RE.search(app_init):
            errors.append("Hardcoded FastAPI version detected in app/__init__.py")

    if not CHANGELOG_FILE.exists():
        errors.append(f"Missing changelog file: {CHANGELOG_FILE}")
    else:
        changelog = read_text(CHANGELOG_FILE)
        if f"## [{version}]" not in changelog:
            errors.append(f"docs/CHANGELOG.md must contain section: ## [{version}]")

    if errors:
        print("Version consistency check failed.")
        for line in errors:
            print(f" - {line}")
        return 1

    print(f"Version consistency check passed: APP_VERSION={version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
