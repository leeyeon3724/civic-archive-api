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

Conventional Commits를 사용하며, 즉시 강제 규칙은 아래와 같습니다.

- 필수 형식: `<type>(<scope>): <subject>`
- 허용 type: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `ci`, `build`, `perf`, `revert`
- 허용 scope: `p<digit...>`, `api`, `db`, `ops`, `security`, `deps`, `docs`, `ci`, `release`, `bench`, `infra`
- subject 규칙:
  - 시작 문자는 소문자/숫자
  - 마침표(`.`)로 끝나면 안 됨
  - 최대 72자

예시:

- `feat(p5): add profile-based benchmark guardrails`
- `docs(api): update payload size guard behavior`
- `chore(ci): add commit message validation workflow`

적용 범위:

- 기존 `main` 히스토리는 소급 수정하지 않습니다.
- 정책은 신규 커밋(푸시/PR 범위)에 즉시 적용됩니다.

검사 명령:

- `python scripts/check_commit_messages.py --rev-range origin/main..HEAD --mode fail`

로컬 훅 설치(권장):

- `powershell -ExecutionPolicy Bypass -File scripts/install_git_hooks.ps1`

## Pull Request 작성 규칙

PR 본문에 아래 항목을 포함합니다.

- 변경 배경/목적
- 핵심 변경점
- 검증 방법과 결과
- 리스크와 롤백 방법

## 머지 전 필수 검증

- `python scripts/check_commit_messages.py --rev-range origin/main..HEAD --mode fail`
- `python -m ruff check app tests scripts`
- `python -m pytest -q -m "not e2e and not integration" --cov=app --cov-report=term --cov-fail-under=85`
- `python scripts/check_docs_routes.py`
- `python scripts/check_schema_policy.py`
- `python scripts/check_version_consistency.py`
- `python scripts/check_slo_policy.py`

추가 검증 규칙:

- 스키마 변경 PR
  - Alembic revision 포함
  - `python -m alembic upgrade head` 검증
  - `python -m alembic downgrade -1` 검증
- API 계약 변경 PR
  - `docs/API.md` 업데이트
  - 변경된 요청/응답/에러 예시 반영
- 성능 민감 변경 PR
  - `python scripts/benchmark_queries.py --profile staging` 결과 첨부
  - baseline 대비 benchmark delta(`ms` 또는 `%`)를 PR 본문에 기록
  - 처리량/성능 가드 변경 시 oversized payload(`413 PAYLOAD_TOO_LARGE`) 동작 확인 결과 첨부
- 보안/공급망 변경 PR
  - `pip-audit -r requirements.txt -r requirements-dev.txt`
  - 필요 시 SBOM 갱신/첨부 (`cyclonedx-py requirements ...`)
- 운영/가용성 변경 PR
  - `python scripts/check_runtime_health.py --base-url <target>`

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
