# 테스트 및 품질 게이트

## 품질 게이트 전체 목록

PR 머지 및 배포 전에 아래 명령을 모두 통과해야 합니다.

```bash
# 린트
python -m ruff check app tests scripts

# 타입 검사 (phase-2, blocking)
python scripts/check_mypy.py

# 단위/컨트랙트 테스트 + 커버리지 하한
python -m pytest -q -m "not e2e and not integration" --cov=app --cov-report=term --cov-fail-under=85

# 커밋 메시지 정책
python scripts/check_commit_messages.py --rev-range origin/main..HEAD --mode fail

# 문서-코드 라우트 계약
python scripts/check_docs_routes.py

# 스키마 정책 (런타임 수동 DDL 금지)
python scripts/check_schema_policy.py

# 버전 정합성
python scripts/check_version_consistency.py

# SLO 정책 기준선
python scripts/check_slo_policy.py

# 공급망 보안 (선택)
cyclonedx-py requirements --output-reproducible --of JSON -o sbom-runtime.cdx.json requirements.txt
pip-audit -r requirements.txt -r requirements-dev.txt
```

## 통합 테스트 (PostgreSQL)

```bash
docker compose up -d db
python -m alembic upgrade head
RUN_INTEGRATION=1 python -m pytest -m integration

# 배포 전 런타임 헬스 가드
python scripts/check_runtime_health.py --base-url http://localhost:8000
```

## E2E 테스트 (라이브 서버)

```bash
# 로컬/수동: 대상 서버 미도달 시 skip
python -m pytest -q -m e2e --base-url http://localhost:8000

# CI/강제: 대상 서버 미도달 시 fail
E2E_REQUIRE_TARGET=1 python -m pytest -q -m e2e --base-url http://localhost:8000
```

## 성능 회귀 체크

대표 조회 쿼리 3종(news/minutes/segments) 응답시간 측정. 기본 seed 300행, 25회 반복.

```bash
# staging 프로파일 (CI 기준)
BENCH_PROFILE=staging BENCH_FAIL_THRESHOLD_MS=250 BENCH_FAIL_P95_THRESHOLD_MS=400 python scripts/benchmark_queries.py

# 릴리스 전 점검 (prod 프로파일)
python scripts/benchmark_queries.py --profile prod --runs 40 --seed-rows 500
```

임계값 프로파일 상세: [docs/PERFORMANCE.md](PERFORMANCE.md)

## 로컬 git 훅 설치

커밋 전 자동 메시지 정책 검사를 위해 훅 설치를 권장합니다.

```bash
powershell -ExecutionPolicy Bypass -File scripts/install_git_hooks.ps1
```

## 릴리스 태그

릴리스 태그(`vX.Y.Z`) 푸시 시 `.github/workflows/release-tag.yml`에서 태그 형식과 `docs/CHANGELOG.md` 버전 섹션을 자동 검증합니다.
