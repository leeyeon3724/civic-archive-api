# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]

### Added
- Typed DTO boundary module for service/repository contracts (`app/ports/dto.py`).
- Production compose baseline (`docker-compose.prod.yml`) with strict security defaults.
- Search strategy split (trigram + FTS) and related index design for list endpoints.

### Changed
- Security module decomposition into focused modules:
  `security_jwt.py`, `security_rate_limit.py`, `security_proxy.py`, `security_dependencies.py`.
- `published_at` storage and parsing policy aligned to UTC-aware semantics (`TIMESTAMPTZ` + UTC normalization).
- Route docs gate upgraded to router auto-discovery (`scripts/check_docs_routes.py`).
- Repository/service interfaces migrated from broad `dict[str, Any]` contracts to typed DTO contracts.

### Fixed
- Tests decoupled from SQL rendering text shape where not contractually required.
- JWT secret minimum length enforcement under strict/required JWT paths.

## [0.1.0] - 2026-02-17

### Added
- Initial FastAPI + PostgreSQL API release.
- Domain APIs for news, council minutes, and speech segments (ingest/list/detail/delete).
- Alembic migration workflow and CI quality/policy gates.
- Standardized error schema and request-id based observability.

