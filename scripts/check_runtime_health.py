#!/usr/bin/env python3
"""Check liveness/readiness endpoints for deployment guardrails."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _http_get_json(url: str, timeout: float) -> tuple[int, dict | str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            body_raw = resp.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(body_raw) if body_raw else {}
            except Exception:
                body = body_raw
            return status, body
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        body_raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(body_raw) if body_raw else {}
        except Exception:
            body = body_raw
        return status, body
    except urllib.error.URLError as exc:
        return 0, f"connection error: {exc.reason}"


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
