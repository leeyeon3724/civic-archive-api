#!/usr/bin/env python3
"""Simple query benchmark for regression checks."""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
from datetime import date
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.database as database
from app.config import Config
from app.repositories.minutes_repository import list_minutes, upsert_minutes
from app.repositories.news_repository import list_articles, upsert_articles
from app.repositories.segments_repository import insert_segments, list_segments


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * p))))
    return float(ordered[k])


def _seed_data(rows: int = 300) -> None:
    with database.engine.begin() as conn:
        conn.execute(
            text(
                """
                TRUNCATE TABLE
                  news_articles,
                  council_minutes,
                  council_speech_segments
                RESTART IDENTITY
                """
            )
        )

    news_items = []
    minutes_items = []
    segment_items = []
    for i in range(rows):
        day = (i % 28) + 1
        news_items.append(
            {
                "source": "bench-source",
                "title": f"budget news {i}",
                "url": f"https://example.com/bench/news/{i}",
                "published_at": f"2026-02-{day:02d}T10:00:00Z",
                "summary": "budget update",
                "content": "budget agenda report",
                "keywords": ["budget", "agenda"],
            }
        )
        minutes_items.append(
            {
                "council": "seoul",
                "committee": "budget",
                "session": "301",
                "meeting_no": i % 10 + 1,
                "meeting_no_combined": f"301 {i % 10 + 1}th",
                "url": f"https://example.com/bench/minutes/{i}",
                "meeting_date": date(2026, 2, day),
                "content": "agenda and budget minutes",
                "tag": ["budget"],
                "attendee": {"count": 10},
                "agenda": ["agenda-item"],
            }
        )
        segment_items.append(
            {
                "council": "seoul",
                "committee": "budget",
                "session": "301",
                "meeting_no": i % 10 + 1,
                "meeting_no_combined": f"301 {i % 10 + 1}th",
                "meeting_date": date(2026, 2, day),
                "content": "segment budget text",
                "summary": "segment summary",
                "subject": "budget subject",
                "tag": ["budget"],
                "importance": (i % 3) + 1,
                "questioner": {"name": "member"},
                "answerer": [{"name": "official"}],
                "party": "party-a",
                "constituency": "district-1",
                "department": "finance",
            }
        )

    upsert_articles(news_items)
    upsert_minutes(minutes_items)
    insert_segments(segment_items)


def _measure(name: str, fn, runs: int = 25) -> dict[str, float]:
    durations = []
    for _ in range(runs):
        started = time.perf_counter()
        fn()
        durations.append((time.perf_counter() - started) * 1000.0)

    return {
        "avg_ms": round(statistics.fmean(durations), 2),
        "p95_ms": round(percentile(durations, 0.95), 2),
        "min_ms": round(min(durations), 2),
        "max_ms": round(max(durations), 2),
    }


def main() -> int:
    config = Config()
    database.init_db(config.DATABASE_URL)
    _seed_data()

    results = {
        "news_list": _measure(
            "news_list",
            lambda: list_articles(
                q="budget",
                source="bench-source",
                date_from="2026-02-01",
                date_to="2026-02-28",
                page=1,
                size=20,
            ),
        ),
        "minutes_list": _measure(
            "minutes_list",
            lambda: list_minutes(
                q="agenda",
                council="seoul",
                committee="budget",
                session="301",
                meeting_no=None,
                date_from="2026-02-01",
                date_to="2026-02-28",
                page=1,
                size=20,
            ),
        ),
        "segments_list": _measure(
            "segments_list",
            lambda: list_segments(
                q="segment",
                council="seoul",
                committee="budget",
                session="301",
                meeting_no=None,
                importance=2,
                party="party-a",
                constituency="district-1",
                department="finance",
                date_from="2026-02-01",
                date_to="2026-02-28",
                page=1,
                size=20,
            ),
        ),
    }

    print(json.dumps(results, ensure_ascii=False, indent=2))

    avg_threshold_raw = os.getenv("BENCH_FAIL_THRESHOLD_MS")
    if avg_threshold_raw:
        avg_threshold = float(avg_threshold_raw)
        avg_offenders = [name for name, stats in results.items() if stats["avg_ms"] > avg_threshold]
        if avg_offenders:
            print(
                f"Benchmark regression check failed: avg_ms exceeded {avg_threshold} for {', '.join(avg_offenders)}",
                file=sys.stderr,
            )
            return 1

    p95_threshold_raw = os.getenv("BENCH_FAIL_P95_THRESHOLD_MS")
    if p95_threshold_raw:
        p95_threshold = float(p95_threshold_raw)
        p95_offenders = [name for name, stats in results.items() if stats["p95_ms"] > p95_threshold]
        if p95_offenders:
            print(
                f"Benchmark regression check failed: p95_ms exceeded {p95_threshold} for {', '.join(p95_offenders)}",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
