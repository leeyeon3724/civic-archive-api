# 변경 이력

이 문서는 프로젝트의 주요 변경 사항을 기록합니다.

형식은 Keep a Changelog를 참고하며, 버전 규칙은 Semantic Versioning을 따릅니다.

## [Unreleased]

### 추가됨

- 기여/버전 정책 문서 추가 (`docs/CONTRIBUTING.md`, `docs/VERSIONING.md`)
- PR 템플릿 및 CODEOWNERS 기본 설정 추가
- Redis 기반 분산 rate limiter 백엔드(`RATE_LIMIT_BACKEND=redis`, `REDIS_URL`) 지원 추가
- 버전 단일 소스/변경이력 정합성 자동 검사 스크립트(`scripts/check_version_consistency.py`) 추가
- 운영 헬스 분리를 위한 `GET /health/live`, `GET /health/ready` 엔드포인트 추가
- `council_speech_segments.dedupe_hash` 및 고유 인덱스(중복 삽입 방지) 마이그레이션 추가
- Redis rate limiter 운영 강화 옵션 추가 (`RATE_LIMIT_FAIL_OPEN`, `RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS`)
- JWT 인증/인가 옵션 추가 (`REQUIRE_JWT`, HS256 검증, 메서드별 scope, admin role 우회)
- trusted proxy 경계 설정 추가 (`TRUSTED_PROXY_CIDRS`, 신뢰 CIDR에서만 `X-Forwarded-For` 사용)
- 공급망 보안 워크플로우 추가 (`.github/workflows/security-supply-chain.yml`: CycloneDX SBOM, pip-audit)
- SLO/운영 문서 추가 (`docs/SLO.md`, `docs/OPERATIONS.md`)
- SLO 정책/배포 가드 스크립트 추가 (`scripts/check_slo_policy.py`, `scripts/check_runtime_health.py`)

### 변경됨

- `routes` 공통 에러 응답 상수와 `repositories` 공통 쿼리 헬퍼를 도입해 중복 코드를 축소함
- 라우트 계층의 저장소 직접 호출을 제거하고 `service` 오케스트레이션 경유 구조로 책임 경계를 정리함
- metrics path 라벨 cardinality 보호를 위해 라우트 미매칭 요청을 `/_unmatched`로 집계
- `/api/segments` 삽입 동작을 정규화 payload 기반 idempotent insert로 변경 (`ON CONFLICT DO NOTHING`)
- metrics cardinality 보호 강화를 위해 알 수 없는 HTTP method 라벨을 `OTHER`로 정규화
- 버전 정합성 검사 강화: changelog 구조 검증(`Unreleased`, 최신 릴리스 섹션) 및 release-tag 워크플로우 연동
- `/api/*` 공통 에러 응답에 `403 (FORBIDDEN)` 계약 추가
- 운영 strict 모드 추가 (`SECURITY_STRICT_MODE=1` 또는 `APP_ENV=production` 시 인증/호스트/CORS/rate-limit 가드 강제)
- CI에 SLO 정책 기준선 검사 단계 추가 (`.github/workflows/docs-contract.yml`)

### 수정됨

- 인코딩 깨짐(mojibake)으로 훼손된 날짜/회의차수 관련 오류 메시지와 문자열 조합 로직 정리

## [0.1.0] - 2026-02-17

### 추가됨

- FastAPI + PostgreSQL 기반 API 초기 버전
- Pydantic 요청/응답 모델 및 OpenAPI 문서화
- 표준 에러 스키마 (`code/message/error/request_id/details`)
- 관측성 기본선 (`request-id`, 구조화 로그, `/metrics`)
- Alembic 마이그레이션 정책 및 CI 품질 게이트
- PostgreSQL 통합 테스트 및 벤치마크 점검 스크립트
