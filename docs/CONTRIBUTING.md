# 기여 가이드

이 문서는 `civic-archive-api`의 브랜치 전략, 커밋 규칙, PR 규칙, 릴리스 절차를 정의합니다.

## 기본 원칙

- `main` 브랜치에는 직접 push하지 않고 Pull Request로만 반영합니다.
- 변경은 작게 쪼개고 코드/테스트/문서를 함께 업데이트합니다.
- DB 스키마 변경은 Alembic migration으로만 수행합니다.

## 브랜치 전략

- 기준 브랜치: `main`
- 브랜치 이름 규칙:
  - `feat/<short-topic>`
  - `fix/<short-topic>`
  - `refactor/<short-topic>`
  - `docs/<short-topic>`
  - `chore/<short-topic>`
  - `hotfix/<short-topic>`

## 커밋 메시지 규칙

Conventional Commits를 사용합니다.

예시:

- `feat: add request-id propagation in middleware`
- `fix: handle validation error payload consistently`
- `docs: update api security headers`
- `chore: tighten benchmark thresholds`

## Pull Request 작성 규칙

PR 본문에 아래 항목을 포함합니다.

- 변경 배경/목적
- 핵심 변경점
- 검증 방법과 결과
- 리스크와 롤백 방법

## 머지 전 필수 검증

- `python -m pytest -q -m "not e2e and not integration"`
- `python scripts/check_docs_routes.py`
- `python scripts/check_schema_policy.py`
- `python scripts/check_version_consistency.py`

추가 검증 규칙:

- 스키마 변경 PR
  - Alembic revision 포함
  - `python -m alembic upgrade head` 검증
  - `python -m alembic downgrade -1` 검증
- API 계약 변경 PR
  - `docs/API.md` 업데이트
  - 변경된 요청/응답/에러 예시 반영
- 성능 민감 변경 PR
  - `python scripts/benchmark_queries.py` 결과 첨부

## 코드 리뷰 포인트

- 동작 회귀 여부
- 입력 검증/에러 포맷 일관성
- migration 안전성(업/다운)
- 문서 동기화 여부
- 테스트 적절성

## 릴리스

버전/태그 정책은 `docs/VERSIONING.md`를 따릅니다.

릴리스 태그 검증 권장 명령:

- `EXPECTED_VERSION=<X.Y.Z> python scripts/check_version_consistency.py`
