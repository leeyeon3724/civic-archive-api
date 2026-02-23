# 아키텍처

## 기술 스택

- Python 3.12
- FastAPI
- PostgreSQL 16 (SQLAlchemy 2.0 + psycopg)
- pydantic-settings
- Alembic
- prometheus-client
- Redis (선택: 분산 rate limit)
- Docker / docker-compose
- pytest

## 프로젝트 구조

```text
app/
├── __init__.py          # create_app() 조합/오케스트레이션 엔트리포인트
├── main.py              # ASGI 엔트리포인트(app 인스턴스 export)
├── version.py           # 앱 버전 단일 소스(APP_VERSION)
├── config.py            # 환경변수 -> database_url
├── database.py          # init_db() 전용 (런타임 DDL 없음)
├── errors.py            # 표준 에러 payload/HTTPException 헬퍼
├── logging_config.py    # JSON 구조화 로깅 설정
├── observability.py     # request-id, 요청 로깅, Prometheus 메트릭
├── security.py          # 보안 호환 facade (기존 import/patch 포인트 유지)
├── security_dependencies.py # API key/JWT FastAPI dependency 빌더
├── security_jwt.py      # JWT claim 검증/인가 보조 로직
├── security_proxy.py    # trusted proxy/XFF 기반 client key 해석
├── security_rate_limit.py # rate limiter 구현/백엔드 헬스체크
├── parsing.py           # 날짜/시간 파싱 공통 정책
├── bootstrap/           # 앱 부트스트랩 경계(검증/미들웨어/시스템 라우트/예외 핸들러)
│   ├── contracts.py
│   ├── validation.py
│   ├── middleware.py
│   ├── routes.py
│   ├── system_routes.py
│   └── exception_handlers.py
├── schemas.py           # Pydantic 요청/응답 모델
├── utils.py             # 파서/페이로드 검증 공통 함수
├── ports/               # 서비스/리포지토리 포트 인터페이스 (Protocol)
│   ├── dto.py           # 계층 경계용 TypedDict DTO
│   ├── repositories.py
│   └── services.py
├── services/            # 입력 정규화/검증 레이어
│   ├── providers.py     # FastAPI Depends용 서비스 provider
│   ├── news_service.py
│   ├── minutes_service.py
│   └── segments_service.py
├── repositories/        # SQL 실행/조회 레이어 (PostgreSQL 쿼리)
│   ├── session_provider.py # DB 연결 scope provider 계약 (필수 provider 검증/오픈)
│   ├── news_repository.py
│   ├── minutes_repository.py
│   └── segments_repository.py
└── routes/
    ├── __init__.py      # APIRouter 등록
    ├── news.py
    ├── minutes.py
    └── segments.py
main.py                  # uvicorn 실행 진입점
alembic.ini
migrations/
└── versions/
    ├── 35f43b134803_initial_schema.py
    ├── 0df9d6f13c5a_add_segments_dedupe_hash.py
    ├── 9c4f6e1a2b7d_make_news_published_at_timestamptz.py
    └── b7d1c2a4e8f9_add_search_strategy_indexes.py
scripts/
├── bootstrap_db.py      # alembic upgrade head 실행
├── benchmark_queries.py # 대표 조회 쿼리 성능 회귀 체크
├── check_commit_messages.py # 커밋 메시지 정책 검사 (Conventional Commits + scope)
├── check_docs_routes.py # API.md 라우트 계약 + README 링크 검사
├── check_mypy.py        # mypy phase-2 타입체크 래퍼 (blocking 기본)
├── check_schema_policy.py # 런타임 수동 DDL 금지 정책 검사
├── check_slo_policy.py  # SLO 정책 문서 기준선 검사
├── check_runtime_health.py # 배포 전 liveness/readiness 가드 검사
├── check_version_consistency.py # APP_VERSION <-> app/__init__.py <-> CHANGELOG 정합성 검사
└── install_git_hooks.ps1 # commit-msg 훅 설치 스크립트
Dockerfile
docker-compose.yml
tests/
├── test_integration_postgres.py # PostgreSQL 컨테이너 기반 통합 테스트
```

## 계층 구조

- route: HTTP 요청/응답 처리 (`Depends`로 서비스 주입)
- service: 입력 정규화/비즈니스 검증 (생성자/팩토리 기반 DI)
- repository: SQL/DB 접근 (`connection_provider` 주입 가능)

흐름: `route -> service -> repository`

## 데이터 모델

| 테이블 | 용도 | 중복 처리 | 핵심 필드 |
|--------|------|-----------|-----------|
| `news_articles` | 뉴스/기사 | `url` UNIQUE + upsert | title, url, published_at(TIMESTAMPTZ, UTC), content, keywords(JSONB) |
| `council_minutes` | 의회 회의록 | `url` UNIQUE + upsert | council, url, meeting_date, content, tag/attendee/agenda(JSONB) |
| `council_speech_segments` | 발언 단락 | `dedupe_hash` UNIQUE + idempotent insert | council, meeting_date, content, importance, questioner/answerer(JSONB) |

## 앱 초기화 흐름

```text
create_app()
  -> Config() 로드
  -> validate_startup_config()             # 환경/보안/운영 가드 검증
  -> register_core_middleware()            # CORS/TrustedHost + request_size_guard
  -> configure_logging()                # JSON 로그 포맷
  -> init_db(database_url + pool/timeout runtime tuning)
  -> app.state.db_engine / app.state.connection_provider 설정
  -> API 보호 의존성(api-key/jwt/rate-limit) 구성
  -> register_observability()           # X-Request-Id + metrics + request logging
  -> register_domain_routes(...)        # APIRouter 등록
  -> register_system_routes(...)        # /health, /api/echo 등 시스템 라우트 등록
  -> register_exception_handlers(...)   # 표준 에러 스키마 핸들러 등록
```

ASGI 엔트리포인트: `app.main:app`

## 마이그레이션 정책

- 표준 스키마 변경은 Alembic revision으로 관리
- 마이그레이션은 SQLAlchemy/Alembic 객체(`op.create_table`, `op.create_index`) 기반으로 관리
- 앱 런타임 수동 DDL(`CREATE/ALTER/DROP TABLE`) 금지
- `BOOTSTRAP_TABLES_ON_STARTUP=0` 고정(1 설정 시 앱 시작 실패)
- 배포/CI 파이프라인에서 `alembic upgrade head` 실행을 필수화

## 주요 설계 결정

**데이터/쿼리**
- upsert: `ON CONFLICT ... DO UPDATE` (뉴스/회의록); 세그먼트는 `ON CONFLICT DO NOTHING` (dedupe_hash 기반 멱등 insert)
- 배치 ingest: `jsonb_to_recordset` 단일 SQL
- 검색: trigram(`ILIKE`+`pg_trgm`) + FTS(`to_tsvector/websearch_to_tsquery`) 분리; GIN 인덱스(trigram/FTS) + 필터/정렬 복합 btree 인덱스
- 페이지네이션: `COUNT(*)` 별도 쿼리 (50만 행 초과 시 keyset pagination 전환 검토 → `docs/BACKLOG.md`)

**요청/응답/관측성**
- 검증: FastAPI + Pydantic (OpenAPI 자동 문서화)
- 에러: `{code, message, error, request_id, details}` 단일 포맷
- 관측성: request-id 미들웨어 + JSON 구조화 로그 + `/metrics` (미매칭 경로 `/_unmatched`, 알 수 없는 method `OTHER`)
- 요청 크기: `MAX_REQUEST_BODY_BYTES` 초과 시 `413`, `INGEST_MAX_BATCH_ITEMS` 배치 상한

**보안**
- 인증: API key(`REQUIRE_API_KEY`) + JWT/RBAC(`REQUIRE_JWT` + scope/role 분리, `JWT_ADMIN_ROLE` bypass)
- Rate limit: IP 기준 `RATE_LIMIT_PER_MINUTE`; 다중 인스턴스는 `RATE_LIMIT_BACKEND=redis`; 장애 시 쿨다운 + `RATE_LIMIT_FAIL_OPEN`
- 프록시: `TRUSTED_PROXY_CIDRS` 매칭 IP에서만 `X-Forwarded-For` 신뢰
- Strict 모드: `SECURITY_STRICT_MODE=1` 또는 `APP_ENV=production`에서 인증/ALLOWED_HOSTS/CORS/rate-limit 강제
- 시작 검증: strict + memory backend 조합 차단, 인증 미설정 경고, 기본 DB 패스워드 감지

**DI/아키텍처**
- DB: `app.state.connection_provider` 단일 소스 → repository 명시적 주입 (전역 엔진 의존 제거)
- 서비스: `app/services/providers.py` request 단위 provider → route `Depends`
- 포트: `app/ports/services.py`, `app/ports/repositories.py` Protocol + TypedDict DTO 계약
- DB 튜닝: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT_SECONDS`, `DB_CONNECT_TIMEOUT_SECONDS`, `DB_STATEMENT_TIMEOUT_MS`

**품질 게이트**
- 타입: `mypy.ini` + `scripts/check_mypy.py` (phase-2 blocking)
- 성능: `scripts/benchmark_queries.py` + avg/p95 프로파일(`dev`/`staging`/`prod`) → `docs/PERFORMANCE.md`
- 문서 정합성: `scripts/check_docs_routes.py`
- 커밋 정책: `scripts/check_commit_messages.py` + `.github/workflows/commit-message.yml`
- 버전 정합성: `scripts/check_version_consistency.py`
- 공급망: CycloneDX SBOM + pip-audit (`.github/workflows/security-supply-chain.yml`)
- SLO/운영: `scripts/check_slo_policy.py`, `scripts/check_runtime_health.py` → `docs/SLO.md`, `docs/OPERATIONS.md`
