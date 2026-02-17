#!/usr/bin/env python3
"""Check liveness/readiness endpoints for deployment guardrails."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urlparse

import requests


def _http_get_json(url: str, timeout: float) -> tuple[int, dict | str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return 0, f"unsupported URL scheme: {parsed.scheme}"
    try:
        response = requests.get(url, timeout=timeout)
        status = int(response.status_code)
        body_raw = response.text
        try:
            body = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError:
            body = body_raw
        return status, body
    except requests.RequestException as exc:
        return 0, f"connection error: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime health checks for deployment guardrails")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Target base URL")
    parser.add_argument("--timeout-seconds", type=float, default=3.0, help="HTTP timeout seconds")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    timeout = max(0.5, float(args.timeout_seconds))

    checks = [
        ("live", f"{base}/health/live", 200),
        ("ready", f"{base}/health/ready", 200),
    ]

    failed = False
    for name, url, expected in checks:
        status, body = _http_get_json(url, timeout)
        if status != expected:
            failed = True
            print(f"[FAIL] {name}: expected {expected}, got {status} ({url})")
            print(f"       body={body}")
        else:
            print(f"[OK] {name}: {status} ({url})")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
