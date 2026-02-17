# 버전 정책

이 프로젝트는 Semantic Versioning(SemVer)을 따릅니다.

버전 형식:

- `MAJOR.MINOR.PATCH` (`vX.Y.Z`)

## 현재 단계 (`0.x`)

`1.0.0` 이전에는 아래 규칙을 사용합니다.

- 하위 호환이 깨지는 변경: `MINOR` 증가
- 하위 호환 기능 추가: `MINOR` 증가
- 버그 수정/내부 개선: `PATCH` 증가

예시:

- `0.2.3` -> `0.3.0` (기능 추가 또는 breaking change)
- `0.2.3` -> `0.2.4` (버그 수정)

`1.0.0` 이후에는 일반 SemVer 규칙을 엄격히 적용합니다.

## 릴리스 태그 규칙

- Git 태그는 `v` 접두사를 사용합니다.
- 예: `v0.1.0`, `v0.2.1`

## 릴리스 체크리스트

1. 사전 검증
- 기본 검증 항목은 `docs/CONTRIBUTING.md`의 "머지 전 필수 검증"을 따릅니다.

2. 마이그레이션
- 스키마 변경 시 Alembic revision을 포함합니다.
- `upgrade`와 최소 1 step `downgrade` 경로를 확인합니다.

3. 문서/이력
- 버전 릴리스 시 `docs/CHANGELOG.md`에 해당 버전 섹션을 추가합니다.
- API 변경 시 `docs/API.md`, 구조/운영 변경 시 `docs/ARCHITECTURE.md`를 함께 갱신합니다.

4. 태그/배포
- `main`의 릴리스 커밋에서 `vX.Y.Z` 태그를 생성합니다.
- 태그 푸시: `git push origin <tag>`
- 태그 푸시 시 `.github/workflows/release-tag.yml`이 태그 형식과 `docs/CHANGELOG.md` 항목을 자동 검증합니다.

## Breaking Change 표기

- PR 제목 또는 본문에 `BREAKING` 명시
- `docs/CHANGELOG.md`에 영향 범위와 마이그레이션 방법 기록
