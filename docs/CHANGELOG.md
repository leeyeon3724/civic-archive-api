# 변경 이력

Keep a Changelog 형식 기반. Semantic Versioning 준수.

## [Unreleased]

### 추가
- JSONB 필드 중첩 깊이 가드: `_canonical_json_value`에 `_MAX_CANONICAL_JSON_DEPTH=20` 초과 시 `400` 반환(P11-7).
- COUNT(*) 페이지네이션 제약 문서화 및 운영 모니터링 항목 추가(P11-8).
- 계층 경계용 TypedDict DTO 모듈 (`app/ports/dto.py`).
- 운영 보안 기본값 Docker Compose (`docker-compose.prod.yml`).
- 검색 전략 분리: trigram(`ILIKE`+`pg_trgm`) + FTS(`to_tsvector/websearch_to_tsquery`) + GIN 인덱스.
- 시작 시 불변 보안 검증: strict mode + memory backend 조합 차단, 인증 미설정 경고, 기본 DB 패스워드 감지(P11-1/2/6).
- 레거시 dedupe 해시 관측성: `civic_archive_segment_legacy_hash_variant_total` Prometheus 카운터(P11-4).

### 변경
- 보안 모듈 분리: `security_jwt.py`, `security_rate_limit.py`, `security_proxy.py`, `security_dependencies.py`.
- `published_at`: UTC-aware 저장 정책(`TIMESTAMPTZ` + UTC 정규화).
- 라우트 문서 게이트: 라우터 자동 탐색 방식으로 전환 (`scripts/check_docs_routes.py`).
- repository/service 포트: `dict[str, Any]` → TypedDict DTO 계약으로 전환.
- `list_*` 필터 팬아웃 제거: route → service → repository 전 계층 query TypedDict 단일화(P11-3).

### 제거
- `JWT_ALGORITHM` 설정 필드 제거 — HS256 하드코딩으로 알고리즘 혼동 공격 방지(P11-5).

### 수정
- 테스트: SQL 렌더링 텍스트 의존 제거, 동작 중심 어서션으로 전환.
- JWT secret 최소 길이 검증 강화 (strict/REQUIRE_JWT 경로).

## [0.1.0] - 2026-02-17

### 추가
- FastAPI + PostgreSQL 초기 릴리스.
- 뉴스, 의회 회의록, 발언 단락 도메인 API (수집/목록/상세/삭제).
- Alembic 마이그레이션 워크플로우 및 CI 품질/정책 게이트.
- 표준 에러 스키마 및 request-id 기반 관측성.
