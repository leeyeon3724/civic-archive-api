# Refactor Backlog

## Scope

- Criteria: quality attributes (performance, scalability, reliability, availability, safety, security, resilience, correctness, usability, portability)
- Objective: strengthen operational stability and data correctness first, then extend to performance and security hardening

## Priority Roadmap

| Priority | Theme | Tasks | Status |
|----------|-------|-------|--------|
| P1 | Operational baseline and correctness | readiness (DB/Redis), segments idempotency, mojibake cleanup | In Progress |
| P2 | Data and query performance | FTS/trigram indexes, keyset pagination, bulk write optimization | Pending |
| P3 | Security and operations hardening | JWT/RBAC, trusted proxy chain validation, SBOM/vulnerability scan | Pending |
| P4 | SLO and observability ops | SLI/SLO, error budget policy, alert policy | Pending |

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
