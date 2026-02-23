# Refactor Backlog

## Scope

- Criteria: quality attributes (performance, scalability, reliability, availability, safety, security, resilience, correctness, usability, portability)
- Objective: strengthen operational stability and data correctness first, then extend to performance and security hardening

## Priority Roadmap

| Priority | Theme | Tasks | Status |
|----------|-------|-------|--------|
| P1 | Operational baseline and correctness | readiness (DB/Redis), segments idempotency, mojibake cleanup | Completed |
| P2 | Operations hardening | Redis rate limiter hardening, metrics cardinality protection, version policy automation | Completed |
| P3 | Security and operations hardening | JWT/RBAC, trusted proxy chain validation, SBOM/vulnerability scan | Completed |
| P4 | SLO and observability ops | SLI/SLO, error budget policy, alert policy | Completed |
| P5 | Performance and scalability baseline | DB pool/runtime timeout tuning, query latency guardrails | Completed |
| P6 | Runtime verification hardening | streaming request guard, observability label accuracy, integration/e2e reliability | Completed |
| P7 | Engineering quality hardening | config safety, query correctness, quality gates uplift | Completed |
| P8 | Architecture decomposition | create_app modularization, bootstrap boundaries, DI prep | Completed |

## P10 Backlog (Current Scope)

### 1) P0 Security Hardening (JWT Secret Strength)

- [x] Add minimum JWT secret length validation (`JWT_SECRET >= 32 bytes`) when `REQUIRE_JWT=1`
- [x] Keep strict mode policy alignment (strict mode + JWT path also enforces minimum length)
- [x] Add regression tests for short-secret rejection paths

### 2) P0 Data Correctness Hardening (`published_at` UTC Consistency)

- [x] Normalize `published_at` parser outputs to UTC-aware datetime
- [x] Enforce DB session timezone as UTC at connection options level
- [x] Add Alembic migration converting `news_articles.published_at` to `TIMESTAMPTZ`
- [x] Update API/architecture docs to reflect UTC normalization and storage semantics
- [x] Extend tests for timezone-aware parsing and runtime wiring assertions

## Definition of Done (P10-Current)

- Unit/contract tests pass
- Integration tests pass (`RUN_INTEGRATION=1`)
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- Migration upgrade path passes (`alembic upgrade head`)

## P1 Backlog (Current Scope)

### 1) Readiness Probe Split

- [x] Add `GET /health/live` (liveness)
- [x] Add `GET /health/ready` (DB/Redis readiness)
- [x] Return `503` with per-check details on readiness failure
- [x] Update API documentation

### 2) Segments Idempotency

- [x] Add dedupe key (`dedupe_hash`) to `council_speech_segments`
- [x] Apply `ON CONFLICT DO NOTHING` on insert
- [x] Generate deterministic hash from normalized payload in service layer
- [x] Add migration and tests

### 3) Mojibake Cleanup

- [x] Fix encoding-corrupted user-facing error messages and meeting number text
- [x] Confirm with full required test suite

## Definition of Done (P1)

- Unit/contract tests pass
- Documentation-route contract check passes
- Schema policy check passes
- Version consistency check passes
- `docs/CHANGELOG.md` updated

## P2 Backlog (Current Scope)

### 1) Redis Rate Limiter Hardening

- [x] Add Redis failure cooldown to avoid per-request Redis retry storms
- [x] Add configurable fallback mode (`RATE_LIMIT_FAIL_OPEN`)
- [x] Keep readiness behavior explicit for Redis backend health
- [x] Add regression tests for fail-open/fail-closed cooldown behavior

### 2) Metrics Cardinality Protection Deepening

- [x] Normalize unknown HTTP methods to a bounded label (`OTHER`)
- [x] Keep path labels bounded (`/_unmatched`, max-length guard)
- [x] Normalize invalid status labels to bounded fallback (`000`)
- [x] Add regression test for method-label cardinality guard

### 3) Version Single-Source Verification Hardening

- [x] Extend `check_version_consistency.py` with changelog structure checks
- [x] Add `EXPECTED_VERSION` support for release-tag validation
- [x] Enforce release workflow to run version consistency script
- Note: dedicated script-unit coverage is tracked as cross-cutting tooling backlog.

## Definition of Done (P2)

- Unit/contract tests pass
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- `docs/CHANGELOG.md` updated

## P3 Backlog (Current Scope)

### 1) Trusted Proxy Chain Validation

- [x] Add trusted proxy CIDR configuration (`TRUSTED_PROXY_CIDRS`)
- [x] Use `X-Forwarded-For` only when remote peer is in trusted CIDR
- [x] Add regression tests for trusted/untrusted proxy behavior

### 2) JWT + RBAC

- [x] Add optional JWT authentication (`REQUIRE_JWT`, `JWT_SECRET`, HS256 validation)
- [x] Add claim validation (`exp`, optional `aud`, optional `iss`)
- [x] Add method-scope authorization (`JWT_SCOPE_READ/WRITE/DELETE`)
- [x] Add admin role bypass (`JWT_ADMIN_ROLE`)
- [x] Add regression tests for unauthorized/forbidden/authorized flows

### 3) Safety Guardrails (Ops Defaults)

- [x] Add startup validation for JWT config and algorithm support
- [x] Extend common error contracts with `403 FORBIDDEN`
- [x] Add production profile presets for strict defaults (`SECURITY_STRICT_MODE`/`APP_ENV=production`)

### 4) Supply Chain Baseline

- [x] Add SBOM generation/check workflow
- [x] Add vulnerability scanning workflow

## Definition of Done (P3-Current)

- Unit/contract tests pass
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- `docs/CHANGELOG.md` updated

## P4 Backlog (Current Scope)

### 1) SLI/SLO Policy

- [x] Define SLI/SLO targets for availability and latency
- [x] Define readiness objective (`/health/live`, `/health/ready`)
- [x] Add dedicated SLO policy document (`docs/SLO.md`)

### 2) Error Budget Policy

- [x] Define monthly error budget from availability target
- [x] Define burn-rate based action policy
- [x] Link budget policy to deployment freeze conditions

### 3) Alert and Incident Policy

- [x] Define page/warn alert thresholds
- [x] Add operations runbook (`docs/OPERATIONS.md`)
- [x] Add rollback and incident handling checklist

### 4) Deployment Guardrails

- [x] Add runtime health guard script (`scripts/check_runtime_health.py`)
- [x] Add SLO policy baseline checker (`scripts/check_slo_policy.py`)
- [x] Integrate SLO policy check into CI (`docs-contract.yml`)

## Definition of Done (P4-Current)

- Unit/contract tests pass
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- `docs/CHANGELOG.md` updated

## P5 Backlog (Current Scope)

### 1) DB Runtime Tuning Baseline

- [x] Add DB pool sizing configuration (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT_SECONDS`, `DB_POOL_RECYCLE_SECONDS`)
- [x] Add DB connectivity/runtime timeout configuration (`DB_CONNECT_TIMEOUT_SECONDS`, `DB_STATEMENT_TIMEOUT_MS`)
- [x] Enforce startup validation for invalid DB runtime tuning values
- [x] Add regression tests for DB runtime tuning wiring/validation

### 2) Query Latency Guardrails

- [x] Define endpoint-level latency budgets and threshold mapping (news/minutes/segments)
- [x] Add benchmark scenario tags and threshold profiles (dev/staging/prod)
- [x] Add release-note template item for benchmark delta reporting

### 3) Throughput and Load Safety

- [x] Define batch ingest limits and fallback behavior for oversized payloads
- [x] Add request-size/load-shedding guard policy draft
- [x] Link throughput guardrails to runbook checklist

## Definition of Done (P5-Current)

- Unit/contract tests pass
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- `docs/CHANGELOG.md` updated

## Deferred Cross-Cutting Backlog

- Add dedicated unit tests for remaining policy scripts (including `check_version_consistency.py`)

## P6 Backlog (Current Scope)

### 1) Streaming Request Guard Hardening

- [x] Refactor request-size guard to avoid preloading full request body in middleware
- [x] Enforce payload limit with streamed chunk accumulation and early abort (`413`)
- [x] Add regression tests for chunked/stream-like oversized payloads

### 2) Observability Label Accuracy

- [x] Resolve route-template labels for middleware early-return responses
- [x] Prevent `/_unmatched` overuse for known routes under pre-route guard failures
- [x] Add regression tests for metrics labels on payload-guard `413` responses

### 3) Integration Coverage Expansion (Security/Ops Paths)

- [x] Add integration tests for runtime JWT authorization path (unauthorized/forbidden/authorized)
- [x] Add integration tests for payload guard behavior (`413` + standard error shape)
- [x] Add integration test for metrics label correctness on guarded failures

### 4) E2E Reliability Improvement

- [x] Improve e2e fixture to skip gracefully when target server is unreachable
- [x] Keep explicit base-url targeting for live-server validation
- [x] Prevent false-negative CI/local failures caused by missing live target

## Definition of Done (P6-Current)

- Unit/contract tests pass
- Integration tests pass (`RUN_INTEGRATION=1`)
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- `docs/CHANGELOG.md` updated

## P7 Backlog (Current Scope)

### 1) Configuration Safety Hardening

- [x] Build DB connection URL with safe encoding for credentials containing reserved characters
- [x] Add regression test for special-character password parsing correctness

### 2) Query Correctness Hardening

- [x] Fix `GET /api/news` date range boundary behavior to keep `to` filter inclusive at day granularity
- [x] Add regression coverage for same-day (`from == to`) news filtering

### 3) Quality Gates Uplift

- [x] Add lint gate (`ruff check`) to CI
- [x] Add coverage gate (`pytest --cov --cov-fail-under`) to CI
- [x] Remove current lint violations from scripts/tests
- [x] Phase-1 mypy rollout execution (non-blocking baseline)
  - scope: `app/config.py`, `app/security.py`, `app/services/*`, `app/ports/*`, `scripts/*`
  - rollout: CI `warn` mode (`scripts/check_mypy.py --mode warn`) with later promotion to `fail`

### 4) Maintainability Refactor Preparation

- [x] Define `create_app()` decomposition target modules (validation/middleware/routes/handlers)
  - target modules: `app/bootstrap/validation.py`, `app/bootstrap/middleware.py`, `app/bootstrap/routes.py`, `app/bootstrap/errors.py`
- [x] Identify global engine dependency migration path for DI/session factory
  - path: `database.engine` 직접 참조 -> `session factory/provider` 도입 -> repository 의존성 주입 전환

## Definition of Done (P7-Current)

- Unit/contract tests pass
- Integration tests pass (`RUN_INTEGRATION=1`)
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- Lint gate (`ruff`) passes
- Coverage gate (`--cov-fail-under`) passes
- `docs/CHANGELOG.md` updated

## P8 Backlog (Current Scope)

### 1) create_app Decomposition

- [x] Extract startup config validation into `app/bootstrap/validation.py`
- [x] Extract core middleware registration into `app/bootstrap/middleware.py`
- [x] Extract system route registration into `app/bootstrap/system_routes.py`
- [x] Extract exception handler registration into `app/bootstrap/exception_handlers.py`
- [x] Keep `app.create_app()` as composition/orchestration entrypoint only

### 2) Bootstrap Boundary Contracts

- [x] Add dedicated tests for each bootstrap module (validation/middleware/system-routes/handlers)
- [x] Define explicit contract for dependency injection surface between bootstrap and route/service layers
  - contract: `register_domain_routes(api, protected_dependencies=...)` forwards auth/rate-limit dependencies
  - contract: `register_system_routes(..., protected_dependencies=..., rate_limit_health_check=...)` receives injected health dependency

### 3) DI Migration Preparation

- [x] Introduce session provider abstraction replacing direct `database.engine` usage in repositories
- [x] Prepare phased migration plan: global engine -> provider -> repository injection
  - phase 1 (completed): `app/repositories/session_provider.py` default provider wraps global engine scope
  - phase 2 (completed): repository functions support optional injected `connection_provider`
  - phase 3 (completed): service layer constructor/provider injection + route `Depends` wiring
  - phase 3.1 (completed): service/repository port interfaces extracted to `app/ports/*`
  - test migration (completed): endpoint tests use dependency override fixture for service DI

### 4) Typecheck Scope Expansion (Phase-1)

- [x] Add mypy config/wrapper (`mypy.ini`, `scripts/check_mypy.py`)
- [x] Extend phase-1 target scope to include service layer and ports
- [x] Add CI phase-1 mypy step in warn mode (non-blocking baseline)

## Definition of Done (P8-Current)

- Unit/contract tests pass
- Integration tests pass (`RUN_INTEGRATION=1`)
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- `create_app()` responsibilities are split across bootstrap modules
- `docs/CHANGELOG.md` updated

## Post-P8 Execution Backlog

### P0) DB DI Finalization

- [x] Remove global `database.engine` runtime dependency from app/service/repository paths
- [x] Wire DB access through `app.state.connection_provider` (request/runtime DI single source)
- [x] Unify test fixtures to provider-based injection instead of engine monkeypatch pattern

### P1) Batch Write Optimization

- [x] Refactor news/minutes upsert to JSON recordset based single-statement execution
- [x] Refactor segments insert to JSON recordset based batch execution
- [x] Preserve insert/update counting contract in batch path

### P1) E2E CI Workflow

- [x] Add executable E2E workflow using Docker Compose (`db` + `api`)
- [x] Add strict mode (`E2E_REQUIRE_TARGET=1`) so unreachable target fails CI (no silent skip)
- [x] Keep local/manual skip behavior for non-CI live-target runs

### P1) Observability and Quality Gate Follow-up

- [x] Split observability middleware internals into pure functions (status/log-payload/metrics observer)
- [x] Add dedicated exception-path focused observability unit tests
- [x] Promote mypy gate to phase-2 blocking mode (scope: `services/ports/repositories/observability`)
- [x] Refactor repository list query builders to SQLAlchemy expressions and remove Bandit `B608` temporary skip

## P9 Execution Tickets (Roadmap Refresh)

### Ticket P0-1: Test Determinism Baseline

- Priority: P0
- Status: Completed
- Tasks:
  - [x] add test-only config factory that disables `.env` loading and pins deterministic defaults
  - [x] migrate test bootstrap paths from direct `Config()` construction to test config factory
  - [x] add regression test proving environment variables do not silently change test runtime config
- Done Criteria:
  - [x] all `tests/*.py` app bootstrap paths use test config factory (no direct `Config()` in tests)
  - [x] `pytest -m "not e2e and not integration"` passes with coverage gate
  - [x] mypy/ruff gates pass
- Risks:
  - integration test operators may rely on implicit environment-based DB overrides
  - fixture bootstrap change can reveal hidden test coupling

### Ticket P1-1: Type Gate Expansion to Bootstrap/Routes

- Priority: P1
- Status: Completed
- Tasks:
  - [x] remove `mypy.ini` ignore blocks for `app.__init__`, `app.bootstrap.*`, `app.routes.*` in phases
  - [x] annotate `app.state` access and dependency contracts to reduce `Any` leakage
  - [x] add/adjust typing tests for startup and route wiring paths
- Done Criteria:
  - [x] mypy blocking scope includes app bootstrap and route modules
  - [x] no `ignore_errors = True` remains for bootstrap/routes
  - [x] CI docs-contract workflow remains green
- Risks:
  - short-term PR velocity drop while annotations are introduced
  - additional refactor may be needed in FastAPI dependency signatures

### Ticket P1-2: Security Module Decomposition

- Priority: P1
- Status: Completed
- Tasks:
  - [x] split `app/security.py` into jwt/rate-limit/proxy/dependency modules
  - [x] keep public behavior and config surface backward compatible
  - [x] add module-level focused unit tests
- Done Criteria:
  - security responsibilities are separated into focused modules
  - existing security regression tests pass without behavior drift
  - architecture docs updated
- Risks:
  - accidental behavior drift in auth/rate-limit edge cases
  - import cycle risk while extracting shared helpers

### Ticket P1-3: Search Strategy Split and Index Redesign

- Priority: P1
- Status: Completed
- Tasks:
  - [x] split search condition into trigram(`ILIKE` + `pg_trgm`) and FTS(`to_tsvector/websearch_to_tsquery`)
  - [x] add table-level `*_search_trgm`/`*_search_fts` GIN indexes for news/minutes/segments
  - [x] add filter+sort composite indexes for primary list query paths
  - [x] validate migration + integration search behavior
- Done Criteria:
  - search query behavior remains backward-compatible on API contracts
  - benchmark and integration paths remain green
  - architecture/performance docs updated
- Risks:
  - index bloat and write amplification due to additional GIN indexes
  - locale/stemming expectations may differ under `simple` text search config

### Ticket P1-4: Docs-Route Contract Auto Discovery

- Priority: P1
- Status: Completed
- Tasks:
  - [x] replace hardcoded route file list in `scripts/check_docs_routes.py` with app tree auto-discovery
  - [x] keep existing API.md/README contract diff behavior
  - [x] add script-focused regression tests
- Done Criteria:
  - new routers are checked without script-maintenance edits
  - docs-contract CI gate remains green
- Risks:
  - future non-route decorators may require parser exclusion rules

### Ticket P1-5: Production Compose Safety Baseline

- Priority: P1
- Status: Completed
- Tasks:
  - [x] add `docker-compose.prod.yml`
  - [x] enable strict security defaults (auth/rate-limit/host/cors constraints) in prod compose
  - [x] require secret env variables for runtime safety
  - [x] document production compose usage in runbook/README
- Done Criteria:
  - prod compose starts with strict-mode compatible defaults
  - required secrets missing case fails fast at compose level
- Risks:
  - operators must provide explicit host/origin/secret values before startup

### Ticket P2-1: Test Resilience Against SQL Rendering Changes

- Priority: P2
- Status: Completed
- Tasks:
  - [x] reduce SQL string rendering assertions in tests
  - [x] shift to behavior-focused assertions (params, row mapping, pagination offsets, call counts)
  - [x] keep minimal SQL shape assertions only where contractually necessary
- Done Criteria:
  - repository/service tests do not depend on exact SQL text rendering
  - query builder refactors no longer trigger broad test rewrites
- Risks:
  - too-loose assertions can weaken regression detection if not balanced

### Ticket P2-2: Parsing/Domain Contract Unification

- Priority: P2
- Status: Completed
- Tasks:
  - [x] unify duplicated date/datetime parsing policy across `schemas` and `utils`
  - [x] introduce typed DTO boundaries for service/repository ports incrementally
  - [x] align error messages and validation semantics across layers
- Done Criteria:
  - single parsing policy implementation is reused across layers
  - `dict[str, Any]` boundary usage is reduced in ports/services
  - compatibility tests pass for existing API contracts
- Risks:
  - API-facing validation messages may change unexpectedly
  - phased migration complexity across routes/services/repositories

---

## P11 Backlog — Risk-Driven Hardening

### Scope

리스크 가중 기술 부채 분석 결과 도출된 항목.
배포 모델(단일 서버 Docker Compose) 유지. 아키텍처 변경 없음.
우선순위 기준: Impact × Likelihood 점수 (분석 보고서 기준).

### Risk-Weighted Priority Matrix (P11 범위)

| Ticket | Description                                              | Impact | Likelihood | Score  | Classification    |
|--------|----------------------------------------------------------|--------|------------|--------|-------------------|
| P11-1  | 메모리 레이트 리미터 다중 워커 안전성                    | 4      | 5          | **20** | Refactor Now      |
| P11-2  | 보안 기본값 미설정 — 시작 시 불변 검증                   | 5      | 3          | **15** | Refactor Now      |
| P11-3  | 필터 파라미터 팬아웃 제거 (segments/minutes/news)        | 3      | 5          | **15** | Refactor Now      |
| P11-4  | 레거시 dedupe 해시 — 관측 가능성 및 폐기 경로            | 4      | 3          | **12** | Refactor Now      |
| P11-5  | `JWT_ALGORITHM` 설정 필드 미사용 정리                    | 3      | 4          | **12** | Monitor / Cleanup |
| P11-6  | 기본 DB 패스워드 시작 시 경고                            | 3      | 3          | **9**  | Monitor / Cleanup |
| P11-7  | JSONB 필드 중첩 깊이 가드                                | 3      | 3          | **9**  | Deferred          |
| P11-8  | COUNT(*) 페이지네이션 성능 모니터링 정책                 | 3      | 4          | **12** | Deferred          |

---

### Ticket P11-1: 메모리 레이트 리미터 다중 워커 안전성 (Score: 20)

- Priority: P0
- Status: Completed
- 리스크 시나리오:
  - `InMemoryRateLimiter`는 프로세스 로컬 `threading.Lock` 기반이므로 uvicorn `--workers N` 환경에서 각 워커가 독립적인 카운터를 보유함
  - 결과: 실제 허용량이 `RATE_LIMIT_PER_MINUTE × N`이 되어 레이트 리미팅이 무력화됨
  - 실패 모드: 헬스 체크와 단일 프로세스 테스트에서는 정상으로 보이지만 실제 운영 배포에서는 보호 효과 없음
  - 근거 코드: `app/security_rate_limit.py:37–68`
- Tasks:
  - [ ] `app/bootstrap/validation.py`에 시작 시 검증 추가: `SECURITY_STRICT_MODE=True` AND `RATE_LIMIT_BACKEND=memory` AND `RATE_LIMIT_PER_MINUTE > 0` → `RuntimeError` 발생
  - [ ] `RATE_LIMIT_BACKEND=memory` 선택 시 구조화 `WARNING` 로그 출력: 단일 워커 전용임을 명시
  - [ ] `.env.example` 주석 보강: 다중 워커 환경에서는 반드시 `RATE_LIMIT_BACKEND=redis` 사용
  - [ ] `docker-compose.prod.yml` 주석 보강: Redis 백엔드 선택 이유 명시
  - [ ] 검증 경로에 대한 단위 테스트 추가 (strict mode + memory backend 조합)
- Done Criteria:
  - strict mode + memory backend 조합 시 시작 시 `RuntimeError` 발생
  - 비 strict 환경에서 memory backend 선택 시 WARNING 로그 출력 (정상 가동)
  - 단위/컨트랙트 테스트 통과
  - 스키마 정책, 버전 일관성 검사 통과
- Risks:
  - 기존 단일 워커 개발 환경에는 영향 없음 (strict mode off)
  - strict mode 배포 중 memory backend 사용 중인 경우: 의도된 breaking change — Redis 전환 필요

---

### Ticket P11-2: 보안 기본값 미설정 — 시작 시 불변 검증 (Score: 15)

- Priority: P0
- Status: Completed
- 리스크 시나리오:
  - `REQUIRE_API_KEY=False`, `REQUIRE_JWT=False`가 기본값이므로 환경 변수 누락 시 전체 API가 인증 없이 공개됨
  - `SECURITY_STRICT_MODE` 미설정 시 strict mode가 `APP_ENV` 문자열 매칭 휴리스틱에 의존 (`{"prod", "production"}`만 인식)
  - 결과: `APP_ENV=live`, `APP_ENV=prod-kr` 등의 값에서 strict mode 미활성화, 쓰기/삭제 엔드포인트 무인증 노출
  - 근거 코드: `app/config.py:39–51`, `app/config.py:115–118`, `app/security_dependencies.py:15–21`
- Tasks:
  - [ ] `app/bootstrap/validation.py`에 시작 시 불변 조건 추가:
    - `strict_security_mode=True` AND `REQUIRE_API_KEY=False` AND `REQUIRE_JWT=False` → `RuntimeError` (최소 하나의 인증 수단 필요)
    - `strict_security_mode=True` AND `RATE_LIMIT_PER_MINUTE == 0` → `RuntimeError` (strict mode에서 레이트 리밋 필수)
  - [ ] `APP_ENV != "development"` AND 인증 비활성화 상태에서 구조화 `WARNING` 로그 출력
  - [ ] 각 불변 조건 경로에 대한 단위 테스트 추가
  - [ ] `.env.example` 및 `docker-compose.prod.yml` 주석 보강: strict mode 체크리스트 명시
- Done Criteria:
  - 두 가지 불변 조건 각각에 대한 `RuntimeError` 검증 테스트 통과
  - 비 strict 환경에서 인증 미설정 시 WARNING 로그 출력 (시작 차단 없음)
  - 단위/컨트랙트 테스트, 스키마 정책, 버전 일관성 검사 통과
- Risks:
  - strict mode 하에 인증 없이 운영 중인 경우: 의도된 breaking change
  - 검증 시점(시작 vs. 요청)에 따른 테스트 픽스처 조정 필요

---

### Ticket P11-3: 필터 파라미터 12개 팬아웃 제거 (Score: 15)

- Priority: P1
- Status: Completed
- 리스크 시나리오:
  - `list_segments` 파라미터 목록(q, council, committee, session, meeting_no, importance, party, constituency, department, date_from, date_to, page, size — 13개)이 route → service module function → service class method → repository module function → repository class method 총 5곳에 중복 정의됨
  - 필터 하나 추가/삭제 시 최소 5개 파일, 8개 지점 수정 필요
  - 실패 모드: 레이어 간 파라미터 부분 누락 시 Python 런타임 에러 또는 필터 무시 — 타입 검사 미통과 시 침묵적 결함
  - 근거 코드: `app/repositories/segments_repository.py:151–263`, `app/repositories/segments_repository.py:309–341`, `app/services/segments_service.py:179–210`, `app/services/segments_service.py:242–275`, `app/routes/segments.py:60–97`
- Tasks:
  - [ ] `app/ports/dto.py`에 `SegmentsListQuery` TypedDict 정의 (모든 필터 파라미터 포함)
  - [ ] `app/ports/dto.py`에 `MinutesListQuery` TypedDict 정의
  - [ ] `app/ports/dto.py`에 `NewsListQuery` TypedDict 정의
  - [ ] 각 레이어(route → service → repository)의 `list_*` 함수 시그니처를 단일 query object로 교체
  - [ ] `app/ports/repositories.py`, `app/ports/services.py` Protocol 인터페이스 동기화
  - [ ] API 라우트 `Query()` 파라미터는 변경 없음 — query object 생성은 route handler 내부에서만 수행
  - [ ] 파라미터 전달 정확성 검증 회귀 테스트 추가
- Done Criteria:
  - API 계약 변경 없음 (라우트 시그니처 동일)
  - `list_*` 함수 시그니처 중복 제거 (5곳 → query object 단일 정의)
  - 필터 파라미터 전달 통합 테스트 통과
  - mypy, ruff, 단위/컨트랙트 테스트 통과
- Risks:
  - 대규모 기계적 리팩터링으로 PR 리뷰 부담 증가 — 레이어별 단계적 적용 권장
  - Protocol 구조적 타이핑 범위 확장으로 mypy 오류 일시 증가 가능

---

### Ticket P11-4: 레거시 dedupe 해시 — 관측 가능성 및 폐기 경로 (Score: 12)

- Priority: P1
- Status: Completed
- 리스크 시나리오:
  - `_build_legacy_segment_dedupe_hash`는 `None` 필드를 `""` 로 치환하여 현재 해시와 다른 값을 생성함
  - `insert_segments` SQL의 `NOT EXISTS` 조건이 `s.dedupe_hash = p.dedupe_hash_legacy`도 검사하므로, 레거시 해시가 기존 레코드의 canonical 해시와 우연히 일치할 경우 유효한 새 레코드가 무경고로 드롭됨
  - 폐기 타임라인이 정의되지 않아 레거시 경로가 무기한 유지될 위험 존재
  - 근거 코드: `app/services/segments_service.py:55–86`, `app/repositories/segments_repository.py:128–135`
- Tasks:
  - [ ] Prometheus 카운터 추가: `legacy_hash_fallback_total` — `NOT EXISTS` 에서 canonical 해시가 아닌 legacy 해시로 매칭된 건수 계측
  - [ ] 회귀 테스트 추가: `_build_segment_dedupe_hash(item_with_none_fields) != _build_legacy_segment_dedupe_hash(item_with_none_fields)` — 두 함수가 동일 입력에 대해 다른 해시를 생성함을 보장
  - [ ] `CHANGELOG.md` 및 본 백로그에 폐기 타임라인 기록 (예: 레거시 해시 마지막 운영 사용일로부터 90일)
  - [ ] 폐기 완료 후 실행할 Alembic 마이그레이션 계획 수립: `dedupe_hash_legacy` 컬럼 DROP, `SegmentUpsertDTO`에서 해당 필드 제거, SQL `NOT EXISTS` 분기 단순화
- Done Criteria:
  - `legacy_hash_fallback_total` 메트릭이 readiness probe 와 별개로 `/metrics` 에서 노출됨
  - 두 해시 함수 불일치 보장 테스트 통과
  - 폐기 타임라인이 문서화됨
  - 단위/컨트랙트 테스트, 메트릭 카디널리티 테스트 통과
- Risks:
  - 메트릭 추가 자체는 zero-risk
  - 컬럼 DROP 마이그레이션은 파이프라인이 레거시 해시를 더 이상 생성하지 않음을 운영에서 확인한 후 별도 PR로 진행

---

### Ticket P11-5: `JWT_ALGORITHM` 설정 필드 미사용 정리 (Score: 12)

- Priority: P2
- Status: Completed
- 리스크 시나리오:
  - `app/config.py:43`의 `JWT_ALGORITHM: str = "HS256"` 설정이 정의되어 있으나 `app/security_jwt.py:58`에서 알고리즘 목록이 `["HS256"]`로 하드코딩됨
  - 운영자가 `JWT_ALGORITHM=RS256` 설정 시 실제 적용되지 않고 여전히 HS256으로 검증됨 — 침묵적 잘못된 설정
  - 근거 코드: `app/config.py:43`, `app/security_jwt.py:58–66`
- Tasks:
  - [ ] `app/config.py`에서 `JWT_ALGORITHM` 필드 제거
  - [ ] `.env.example`에서 `JWT_ALGORITHM` 항목 제거
  - [ ] `app/security_jwt.py`의 `validate_jwt_hs256` 함수에 알고리즘 하드코딩 이유 주석 추가: 알고리즘 혼동 공격(`alg:none`, RS256→HS256 다운그레이드) 방지
  - [ ] `app/bootstrap/validation.py`의 JWT 관련 시작 검증에서 알고리즘 설정 참조 코드가 있다면 제거
  - [ ] 설정 변경에 대한 회귀 테스트 추가 (필드 부재 시 정상 동작 확인)
- Done Criteria:
  - `JWT_ALGORITHM` 설정 필드가 코드베이스에서 완전 제거됨
  - 기존 JWT 인증 회귀 테스트 전부 통과
  - ruff, mypy 통과
- Risks:
  - `.env` 파일에 `JWT_ALGORITHM` 설정 중인 운영 환경은 무시되는 값이 제거됨 (동작 영향 없음)

---

### Ticket P11-6: 기본 DB 패스워드 시작 시 경고 (Score: 9)

- Priority: P2
- Status: Completed
- 리스크 시나리오:
  - `app/config.py:21`의 `POSTGRES_PASSWORD: str = "change_me"` 기본값이 환경 변수 미설정 시 그대로 사용됨
  - 개발 DB가 기본 패스워드로 생성되어 있다면 환경 변수 없이 연결이 성공하여 미설정 상태를 침묵적으로 마스킹
  - 근거 코드: `app/config.py:21`
- Tasks:
  - [ ] `app/bootstrap/validation.py`에 시작 시 조건 추가: `POSTGRES_PASSWORD == "change_me"` AND `APP_ENV != "development"` → 구조화 `WARNING` 로그 출력 (`level=WARNING`, `event=default_db_password_detected`)
  - [ ] strict mode에서는 WARNING이 아닌 `RuntimeError`로 상향 (운영자가 명시적으로 변경 강제)
  - [ ] 해당 경고/에러 경로에 대한 단위 테스트 추가
- Done Criteria:
  - 비 development 환경에서 기본 패스워드 사용 시 WARNING 로그 출력
  - strict mode에서 기본 패스워드 사용 시 `RuntimeError` 발생으로 시작 차단
  - 단위 테스트, ruff, mypy 통과
- Risks:
  - 영향 없음 (경고만 출력, 동작 변경 없음) — strict mode 제외

---

### Deferred: JSONB 필드 중첩 깊이 가드 (R9, Score: 9)

- 대상 필드: `tag`, `moderator`, `questioner`, `answerer` (`Any` 타입, 스키마 검증 없음)
- 리스크: 1000단계 이상 중첩 JSON 입력 시 `_canonical_json_value` 재귀 함수에서 Python `RecursionError` 발생 가능
- 현재 완화 수단: `MAX_REQUEST_BODY_BYTES=1MB` 스트리밍 가드가 일정 수준의 보호 제공
- 조건: 알려진 ETL 파이프라인 외부 소스가 추가되거나 API가 공개 쓰기 엔드포인트로 전환되는 시점에 `_canonical_json_value` 내 `max_depth` 가드 구현 검토

---

### Deferred: COUNT(*) 페이지네이션 성능 모니터링 정책 (R8, Score: 12)

- 현황: 모든 목록 엔드포인트가 데이터 쿼리 + 전체 카운트 쿼리 2회 실행 (`app/repositories/common.py:44–52`)
- 리스크: `council_speech_segments` 테이블이 50만 행 이상에서 복합 WHERE 조건의 `COUNT(*)` 지연 비선형 증가
- 조치 기준:
  - 세그먼트 테이블 행 수 > 500,000 또는 `check_slo_policy.py` SLO 기준 위반 발생 시 커서 기반 페이지네이션(keyset pagination) 도입 검토
  - `docs/PERFORMANCE.md`에 현재 이중 쿼리 구조의 제약 조건과 확장 임계값 문서화
  - `docs/OPERATIONS.md` 운영 체크리스트에 테이블 행 수 모니터링 항목 추가

---

## Definition of Done (P11)

- 단위/컨트랙트 테스트 통과
- 통합 테스트 통과 (`RUN_INTEGRATION=1`)
- Docs-route 계약 검사 통과
- 스키마 정책 검사 통과
- 버전 일관성 검사 통과
- SLO 정책 검사 통과
- lint 게이트 (`ruff`) 통과
- 커버리지 게이트 (`--cov-fail-under`) 통과
- `docs/CHANGELOG.md` 업데이트
