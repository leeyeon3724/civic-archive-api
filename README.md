# Civic Archive API

한국 지방의회 시민 아카이브 데이터 수집/조회 API.
FastAPI + PostgreSQL 기반으로 뉴스, 회의록, 발언 단락 저장/검색을 제공합니다.

## 퀵스타트

```bash
# 1) 의존성 설치
pip install -r requirements-dev.txt

# 2) DB 마이그레이션 반영 (필수)
python scripts/bootstrap_db.py

# 3) 테스트 (기본: unit/contract만, integration/e2e 제외)
python -m pytest

# 4) 로컬 서버 실행 (권장)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5) Docker Compose (PostgreSQL + API)
docker compose up --build
```

## 환경 변수

`.env.example`을 복사해 환경에 맞게 값을 설정하세요.

```bash
# PowerShell 예시
Copy-Item .env.example .env
```

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `POSTGRES_HOST` | `127.0.0.1` | DB 호스트 |
| `POSTGRES_PORT` | `5432` | DB 포트 |
| `POSTGRES_USER` | `app_user` | DB 사용자 |
| `POSTGRES_PASSWORD` | `change_me` | DB 비밀번호 |
| `POSTGRES_DB` | `civic_archive` | DB 이름 |
| `DB_POOL_SIZE` | `10` | SQLAlchemy 커넥션 풀 기본 크기 |
| `DB_MAX_OVERFLOW` | `20` | 풀 초과 허용 커넥션 수 |
| `DB_POOL_TIMEOUT_SECONDS` | `30` | 풀 커넥션 획득 대기 시간(초) |
| `DB_POOL_RECYCLE_SECONDS` | `3600` | 유휴 커넥션 재생성 주기(초) |
| `DB_CONNECT_TIMEOUT_SECONDS` | `3` | DB TCP 연결 타임아웃(초) |
| `DB_STATEMENT_TIMEOUT_MS` | `5000` | PostgreSQL statement timeout(ms) |
| `INGEST_MAX_BATCH_ITEMS` | `200` | 단건 수집 API(`POST /api/*`) 최대 batch item 수 |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | `/api/*` write 요청 최대 payload 크기(bytes) |
| `DEBUG` | `0` | 서버 debug/reload 모드 |
| `APP_ENV` | `development` | 실행 환경 (`development`/`staging`/`production`) |
| `SECURITY_STRICT_MODE` | `0` | `1`이면 운영 보안 가드 강제(아래 설명 참고) |
| `PORT` | `8000` | 서버 포트 |
| `BOOTSTRAP_TABLES_ON_STARTUP` | `0` | 정책상 항상 `0` (수동 DDL 금지) |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `LOG_JSON` | `1` | JSON 구조화 로그 사용 여부 |
| `REQUIRE_API_KEY` | `0` | `1`이면 `/api/*` 엔드포인트에 `X-API-Key` 필수 |
| `API_KEY` | `` | API 키 값 (`REQUIRE_API_KEY=1`일 때 필수) |
| `REQUIRE_JWT` | `0` | `1`이면 `/api/*` 엔드포인트에 `Authorization: Bearer <JWT>` 필수 |
| `JWT_SECRET` | `` | JWT HMAC secret (`REQUIRE_JWT=1`일 때 필수) |
| `JWT_ALGORITHM` | `HS256` | 현재 `HS256`만 지원 |
| `JWT_AUDIENCE` | `` | 지정 시 `aud` 클레임 검증 |
| `JWT_ISSUER` | `` | 지정 시 `iss` 클레임 검증 |
| `JWT_SCOPE_READ` | `archive:read` | 읽기( GET/HEAD ) 권한 scope |
| `JWT_SCOPE_WRITE` | `archive:write` | 쓰기( POST/PUT/PATCH ) 권한 scope |
| `JWT_SCOPE_DELETE` | `archive:delete` | 삭제( DELETE ) 권한 scope |
| `JWT_ADMIN_ROLE` | `admin` | 이 role 보유 시 scope 검사 우회 |
| `RATE_LIMIT_PER_MINUTE` | `0` | IP 기준 분당 요청 제한 (`0`이면 비활성) |
| `RATE_LIMIT_BACKEND` | `memory` | rate limit 저장소 (`memory` 또는 `redis`) |
| `REDIS_URL` | `` | Redis 연결 URL (`RATE_LIMIT_BACKEND=redis`일 때 필수) |
| `RATE_LIMIT_REDIS_PREFIX` | `civic_archive:rate_limit` | Redis rate limit 키 prefix |
| `RATE_LIMIT_REDIS_WINDOW_SECONDS` | `65` | Redis 고정 윈도우 TTL(초) |
| `RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS` | `5` | Redis 장애 시 재시도 쿨다운(초) |
| `RATE_LIMIT_FAIL_OPEN` | `1` | Redis 장애 시 요청 허용 여부 (`1` 허용 / `0` 차단) |
| `TRUSTED_PROXY_CIDRS` | `` | 신뢰할 프록시 CIDR 목록(쉼표 구분). 설정 시에만 `X-Forwarded-For` 신뢰 |
| `CORS_ALLOW_ORIGINS` | `*` | 허용 Origin 목록(쉼표 구분) |
| `CORS_ALLOW_METHODS` | `GET,POST,DELETE,OPTIONS` | 허용 HTTP 메서드(쉼표 구분) |
| `CORS_ALLOW_HEADERS` | `*` | 허용 헤더(쉼표 구분) |
| `ALLOWED_HOSTS` | `*` | Trusted Host 목록(쉼표 구분) |

## 운영 정책

- 스키마 변경은 Alembic만 사용합니다.
- 앱 런타임 수동 DDL(`CREATE/ALTER/DROP TABLE`)은 금지합니다.
- 배포 파이프라인에서 `python -m alembic upgrade head`를 필수로 실행합니다.

## 보안 기본선

- 기본값(`REQUIRE_API_KEY=0`)은 로컬 개발 편의를 위한 설정입니다.
- 운영 환경에서는 `REQUIRE_API_KEY=1`, `API_KEY=<secret>` 적용을 권장합니다.
- 운영 환경에서는 `REQUIRE_JWT=1`과 scope/role 정책 적용을 권장합니다.
- `SECURITY_STRICT_MODE=1` 또는 `APP_ENV=production`이면 아래 항목이 강제됩니다.
  - 인증 필수 (`REQUIRE_API_KEY=1` 또는 `REQUIRE_JWT=1`)
  - `ALLOWED_HOSTS` wildcard 금지
  - `CORS_ALLOW_ORIGINS` wildcard 금지
  - `RATE_LIMIT_PER_MINUTE > 0`
- `RATE_LIMIT_PER_MINUTE`로 `/api/*` 엔드포인트 요청 제한을 활성화할 수 있습니다.
- 다중 인스턴스 환경에서는 `RATE_LIMIT_BACKEND=redis`, `REDIS_URL=redis://...` 구성을 권장합니다.
- Redis 장애 시 동작은 `RATE_LIMIT_FAIL_OPEN`과 `RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS`로 제어합니다.
- 프록시 환경에서는 `TRUSTED_PROXY_CIDRS`를 명시해 신뢰 경계를 설정해야 합니다.
- 쓰기 요청 과부하 방지를 위해 `INGEST_MAX_BATCH_ITEMS`, `MAX_REQUEST_BODY_BYTES`를 운영 환경에 맞게 조정합니다.

## 마이그레이션

```bash
# 최신 버전 적용
python -m alembic upgrade head

# 새 리비전 생성
python -m alembic revision -m "describe change"

# 1단계 롤백
python -m alembic downgrade -1
```

## 문서

- API 상세: [docs/API.md](docs/API.md)
- 아키텍처/설계: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 성능 정책: [docs/PERFORMANCE.md](docs/PERFORMANCE.md)
- SLO 정책: [docs/SLO.md](docs/SLO.md)
- 운영 런북: [docs/OPERATIONS.md](docs/OPERATIONS.md)
- 버전 정책: [docs/VERSIONING.md](docs/VERSIONING.md)
- 변경 이력: [docs/CHANGELOG.md](docs/CHANGELOG.md)
- 기여 가이드: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 품질 게이트

```bash
# 린트 검사
python -m ruff check app tests scripts

# unit/contract 테스트 + 커버리지 하한
python -m pytest -q -m "not e2e and not integration" --cov=app --cov-report=term --cov-fail-under=85

# 커밋 메시지 정책 검사 (브랜치 기준)
python scripts/check_commit_messages.py --rev-range origin/main..HEAD --mode fail

# 문서-코드 라우트 계약 검사 (API.md 기준 + README 링크 확인)
python scripts/check_docs_routes.py

# 스키마 정책 검사 (런타임 수동 DDL 금지)
python scripts/check_schema_policy.py

# 버전 정책 검사 (단일 소스 + 변경 이력 정합성)
python scripts/check_version_consistency.py

# SLO 정책 문서 검사
python scripts/check_slo_policy.py

# 공급망 보안 점검 (선택)
cyclonedx-py requirements --output-reproducible --of JSON -o sbom-runtime.cdx.json requirements.txt
pip-audit -r requirements.txt -r requirements-dev.txt
```

릴리스 태그(`vX.Y.Z`) 푸시 시 `/.github/workflows/release-tag.yml`에서
태그 형식과 `docs/CHANGELOG.md` 버전 섹션을 자동 검증합니다.

## 통합 테스트 (PostgreSQL)

```bash
docker compose up -d db
python -m alembic upgrade head
RUN_INTEGRATION=1 python -m pytest -m integration

# 배포 전 런타임 헬스 가드
python scripts/check_runtime_health.py --base-url http://localhost:8000
```

## 성능 회귀 체크

대표 조회 쿼리 3종(news/minutes/segments) 응답시간을 측정합니다.

```bash
# staging 프로파일 + 평균/95퍼센타일 공통 임계값(ms) 초과 시 실패
BENCH_PROFILE=staging BENCH_FAIL_THRESHOLD_MS=250 BENCH_FAIL_P95_THRESHOLD_MS=400 python scripts/benchmark_queries.py
```
