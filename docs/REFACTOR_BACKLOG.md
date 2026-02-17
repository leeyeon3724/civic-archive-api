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
- Status: In Progress
- Tasks:
  - [x] reduce SQL string rendering assertions in tests
  - [x] shift to behavior-focused assertions (params, row mapping, pagination offsets, call counts)
  - keep minimal SQL shape assertions only where contractually necessary
- Done Criteria:
  - repository/service tests do not depend on exact SQL text rendering
  - query builder refactors no longer trigger broad test rewrites
- Risks:
  - too-loose assertions can weaken regression detection if not balanced

### Ticket P2-2: Parsing/Domain Contract Unification

- Priority: P2
- Status: In Progress
- Tasks:
  - [x] unify duplicated date/datetime parsing policy across `schemas` and `utils`
  - introduce typed DTO boundaries for service/repository ports incrementally
  - [x] align error messages and validation semantics across layers
- Done Criteria:
  - single parsing policy implementation is reused across layers
  - `dict[str, Any]` boundary usage is reduced in ports/services
  - compatibility tests pass for existing API contracts
- Risks:
  - API-facing validation messages may change unexpectedly
  - phased migration complexity across routes/services/repositories
