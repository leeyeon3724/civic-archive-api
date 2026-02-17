# 변경 이력

이 문서는 프로젝트의 주요 변경 사항을 기록합니다.

형식은 Keep a Changelog를 참고하며, 버전 규칙은 Semantic Versioning을 따릅니다.

## [Unreleased]

### 추가됨

- 기여/버전 정책 문서 추가 (`docs/CONTRIBUTING.md`, `docs/VERSIONING.md`)
- PR 템플릿 및 CODEOWNERS 기본 설정 추가

### 변경됨

- `routes` 공통 에러 응답 상수와 `repositories` 공통 쿼리 헬퍼를 도입해 중복 코드를 축소함
- 라우트 계층의 저장소 직접 호출을 제거하고 `service` 오케스트레이션 경유 구조로 책임 경계를 정리함

## [0.1.0] - 2026-02-17

### 추가됨

- FastAPI + PostgreSQL 기반 API 초기 버전
- Pydantic 요청/응답 모델 및 OpenAPI 문서화
- 표준 에러 스키마 (`code/message/error/request_id/details`)
- 관측성 기본선 (`request-id`, 구조화 로그, `/metrics`)
- Alembic 마이그레이션 정책 및 CI 품질 게이트
- PostgreSQL 통합 테스트 및 벤치마크 점검 스크립트
