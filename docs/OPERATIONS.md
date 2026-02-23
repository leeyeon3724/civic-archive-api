# 운영 런북

## 장애 심각도

| 등급 | 기준 |
|------|------|
| SEV-1 | 완전 서비스 불능 또는 데이터 무결성 위험 |
| SEV-2 | 핵심 기능 주요 저하 |
| SEV-3 | 일부 기능 저하 (우회 수단 존재) |

## 장애 대응 절차

1. **트리아지**: 영향 범위 확인(`/api/*`, 특정 엔드포인트, 인증, DB, Redis), 시작 시각/버전 기록
2. **안정화**
   - 배포 진행 중이면 일시 중단 또는 롤백
   - ingest 급증 시: `INGEST_MAX_BATCH_ITEMS`, `MAX_REQUEST_BODY_BYTES` 임시 축소
3. **진단**
   - 헬스 확인: `/health/live`, `/health/ready`
   - 메트릭: 에러 비율, p95 지연, 요청량
   - 로그: `X-Request-Id` 기준 추적
4. **복구**: 수정 적용 또는 롤백 후 readiness/liveness 및 주요 API 경로 재확인
5. **사후 조치**: 타임라인·원인·재발 방지 보고서 작성, SLO 에러 버짓 상태 업데이트

## 롤백 전략

- **애플리케이션**: 이전 정상 이미지/태그 재배포
- **스키마**: `python -m alembic downgrade -1` (롤백 안전성 사전 확인 필수)
- **설정**: 문제 원인이 설정 변경인 경우 환경 변수 우선 롤백

## 운영 점검 명령

품질/정책 검사:

```bash
python -m ruff check app tests scripts
python -m pytest -q -m "not e2e and not integration" --cov=app --cov-report=term --cov-fail-under=85
python scripts/check_docs_routes.py
python scripts/check_schema_policy.py
python scripts/check_version_consistency.py
python scripts/check_slo_policy.py
```

런타임 검사:

```bash
python scripts/check_runtime_health.py --base-url http://localhost:8000
# oversized payload 가드 확인: 413 PAYLOAD_TOO_LARGE 응답 여부
```

운영 Compose 기동:

```bash
docker compose -f docker-compose.prod.yml up -d --build
# 필수 환경 변수: POSTGRES_PASSWORD, API_KEY, JWT_SECRET (최소 32 bytes)
```

성능 회귀 확인:

```bash
BENCH_PROFILE=staging BENCH_FAIL_THRESHOLD_MS=250 BENCH_FAIL_P95_THRESHOLD_MS=400 python scripts/benchmark_queries.py
```
