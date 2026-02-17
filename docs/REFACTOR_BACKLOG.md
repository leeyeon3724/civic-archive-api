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
| P6 | Runtime verification hardening | streaming request guard, observability label accuracy, integration/e2e reliability | In Progress |

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

- [ ] Refactor request-size guard to avoid preloading full request body in middleware
- [ ] Enforce payload limit with streamed chunk accumulation and early abort (`413`)
- [ ] Add regression tests for chunked/stream-like oversized payloads

### 2) Observability Label Accuracy

- [ ] Resolve route-template labels for middleware early-return responses
- [ ] Prevent `/_unmatched` overuse for known routes under pre-route guard failures
- [ ] Add regression tests for metrics labels on payload-guard `413` responses

### 3) Integration Coverage Expansion (Security/Ops Paths)

- [ ] Add integration tests for runtime JWT authorization path (unauthorized/forbidden/authorized)
- [ ] Add integration tests for payload guard behavior (`413` + standard error shape)
- [ ] Add integration test for metrics label correctness on guarded failures

### 4) E2E Reliability Improvement

- [ ] Improve e2e fixture to skip gracefully when target server is unreachable
- [ ] Keep explicit base-url targeting for live-server validation
- [ ] Prevent false-negative CI/local failures caused by missing live target

## Definition of Done (P6-In Progress)

- Unit/contract tests pass
- Integration tests pass (`RUN_INTEGRATION=1`)
- Docs-route contract check passes
- Schema policy check passes
- Version consistency check passes
- SLO policy check passes
- `docs/CHANGELOG.md` updated
