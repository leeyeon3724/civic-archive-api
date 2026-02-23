# SLO 정책

서비스: `civic-archive-api` / 환경: `APP_ENV=production` / 대상: `/api/*`
관측 소스: Prometheus 메트릭 (`civic_archive_http_requests_total`, `civic_archive_http_request_duration_seconds`)

## SLI 정의

| 지표 | 정의 | 수식 |
|------|------|------|
| 가용성 | `/api/*` 성공 요청 비율 (HTTP < 500) | `1 - (5xx / total)` |
| 지연 | `/api/*` 전체 p95 응답 시간 (집계) | `histogram_quantile(0.95, ...)` |

## SLO 목표

| 항목 | 목표 |
|------|------|
| 가용성 (30일 롤링) | ≥ 99.9% |
| 지연 (5분 윈도우 p95, 전체 집계) | ≤ 250ms (검색 포함 목록 엔드포인트 개별 목표: `docs/PERFORMANCE.md`) |
| Readiness | `/health/live` = 200, `/health/ready` = 200 |

## 에러 버짓 정책

가용성 99.9% 기준 월 에러 버짓: **약 43분 12초 / 30일**

| 조건 | 조치 |
|------|------|
| 2시간 소진 > 10% | 즉시 온콜 호출, 비필수 배포 중단 |
| 24시간 소진 > 25% | 기능 배포 전 인시던트 리뷰 필수 |
| 30일 소진 > 50% | 비필수 변경 릴리즈 중단 |
| 30일 소진 > 80% | 인시던트·보안·안정성 변경만 허용 |

## 알림 정책

| 우선순위 | 조건 |
|----------|------|
| Page (긴급) | 5xx 비율 > 5% (5분) / p95 > 500ms (10분) / `/health/ready` ≠ 200 (3회 연속) |
| Warning | 5xx 비율 > 1% (15분) / p95 > 300ms (15분) / 24시간 에러 버짓 소진 > 25% |

## 배포 전 체크리스트

1. 품질 게이트 전체 통과 → [docs/TESTING.md](TESTING.md)
2. DB 마이그레이션: `python -m alembic upgrade head`
3. 런타임 헬스 확인: `python scripts/check_runtime_health.py --base-url <target>`
4. 성능 회귀 확인: `BENCH_PROFILE=staging ... python scripts/benchmark_queries.py`

인시던트 대응 및 롤백: [docs/OPERATIONS.md](OPERATIONS.md)
