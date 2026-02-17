# 아키텍처

## 기술 스택

- Python 3.12
- FastAPI
- PostgreSQL 16 (SQLAlchemy 2.0 + psycopg)
- pydantic-settings
- Alembic
- prometheus-client
- Redis (선택: 분산 rate limit)
- Docker / docker-compose
- pytest

## 프로젝트 구조

```text
app/
├── __init__.py          # create_app() + 공통 예외 처리
├── main.py              # ASGI 엔트리포인트(app 인스턴스 export)
├── version.py           # 앱 버전 단일 소스(APP_VERSION)
├── config.py            # 환경변수 -> DATABASE_URL
├── database.py          # init_db() 전용 (런타임 DDL 없음)
├── errors.py            # 표준 에러 payload/HTTPException 헬퍼
├── logging_config.py    # JSON 구조화 로깅 설정
├── observability.py     # request-id, 요청 로깅, Prometheus 메트릭
├── security.py          # API key 검증 + rate limit 의존성
├── schemas.py           # Pydantic 요청/응답 모델
├── utils.py             # 파서/페이로드 검증 공통 함수
├── services/            # 입력 정규화/검증 레이어
│   ├── news_service.py
│   ├── minutes_service.py
│   └── segments_service.py
├── repositories/        # SQL 실행/조회 레이어 (PostgreSQL 쿼리)
│   ├── news_repository.py
│   ├── minutes_repository.py
│   └── segments_repository.py
└── routes/
    ├── __init__.py      # APIRouter 등록
    ├── news.py
    ├── minutes.py
    └── segments.py
main.py                  # uvicorn 실행 진입점
alembic.ini
migrations/
└── versions/
    ├── 35f43b134803_initial_schema.py
    └── 0df9d6f13c5a_add_segments_dedupe_hash.py
scripts/
├── bootstrap_db.py      # alembic upgrade head 실행
├── benchmark_queries.py # 대표 조회 쿼리 성능 회귀 체크
├── check_docs_routes.py # API.md 라우트 계약 + README 링크 검사
├── check_schema_policy.py # 런타임 수동 DDL 금지 정책 검사
└── check_version_consistency.py # APP_VERSION <-> app/__init__.py <-> CHANGELOG 정합성 검사
Dockerfile
docker-compose.yml
tests/
├── test_integration_postgres.py # PostgreSQL 컨테이너 기반 통합 테스트
```

## 계층 구조

- route: HTTP 요청/응답 처리
- service: 입력 정규화/비즈니스 검증
- repository: SQL/DB 접근

흐름: `route -> service -> repository`

## 데이터 모델

| 테이블 | 용도 | 중복 처리 | 핵심 필드 |
|--------|------|-----------|-----------|
| `news_articles` | 뉴스/기사 | `url` UNIQUE + upsert | title, url, published_at, content, keywords(JSONB) |
| `council_minutes` | 의회 회의록 | `url` UNIQUE + upsert | council, url, meeting_date, content, tag/attendee/agenda(JSONB) |
| `council_speech_segments` | 발언 단락 | `dedupe_hash` UNIQUE + idempotent insert | council, meeting_date, content, importance, questioner/answerer(JSONB) |

## 앱 초기화 흐름

```text
create_app()
  -> Config() 로드
  -> BOOTSTRAP_TABLES_ON_STARTUP=1 이면 즉시 실패(정책 위반 방지)
  -> CORS/TrustedHost 미들웨어 등록
  -> configure_logging()                # JSON 로그 포맷
  -> init_db(DATABASE_URL)
  -> API 보호 의존성(api-key/rate-limit) 구성
  -> register_observability()           # X-Request-Id + metrics + request logging
  -> register_routes(dependencies=...)  # APIRouter 등록
  -> 예외 핸들러 등록 (표준 에러 스키마)
```

ASGI 엔트리포인트: `app.main:app`

## 마이그레이션 정책

- 표준 스키마 변경은 Alembic revision으로 관리
- 마이그레이션은 SQLAlchemy/Alembic 객체(`op.create_table`, `op.create_index`) 기반으로 관리
- 앱 런타임 수동 DDL(`CREATE/ALTER/DROP TABLE`) 금지
- `BOOTSTRAP_TABLES_ON_STARTUP=0` 고정(1 설정 시 앱 시작 실패)
- 배포/CI 파이프라인에서 `alembic upgrade head` 실행을 필수화

## 주요 설계 결정

- PostgreSQL upsert: `ON CONFLICT ... DO UPDATE`
- 검색: 텍스트 `ILIKE`, JSONB 컬럼은 `CAST(... AS TEXT) ILIKE`로 통합 검색
- 목록 total: `COUNT(*)` 별도 쿼리
- 요청/응답 검증: FastAPI + Pydantic 모델 기반으로 OpenAPI 자동 문서화
- 에러 표준화: `code/message/error/request_id/details` 단일 포맷
- 관측성: request-id 미들웨어, 구조화 로그, `/metrics` 메트릭 (라우트 미매칭은 `/_unmatched`, 알 수 없는 HTTP method는 `OTHER` 라벨로 고정)
- 보안 기본선: API key 선택적 강제(`REQUIRE_API_KEY`), IP rate-limit(`RATE_LIMIT_PER_MINUTE`)
- 분산 rate-limit: `RATE_LIMIT_BACKEND=redis`, `REDIS_URL`로 멀티 인스턴스 환경 지원
- Redis limiter 안정화: 장애 시 쿨다운(`RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS`) + fallback(`RATE_LIMIT_FAIL_OPEN`) 지원
- 성능 회귀 체크: `scripts/benchmark_queries.py` + avg/p95 threshold 검사
- 문서-코드 정합성: `scripts/check_docs_routes.py` + CI
- 버전 정합성: `scripts/check_version_consistency.py` + CI
