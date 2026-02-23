# Civic Archive API

한국 지방의회 시민 아카이브 데이터 수집/조회 API.
FastAPI + PostgreSQL 기반으로 뉴스, 회의록, 발언 단락 저장/검색을 제공합니다.

## 퀵스타트

```bash
# 1) 의존성 설치
pip install -r requirements-dev.txt

# 2) DB 마이그레이션 반영 (필수)
python scripts/bootstrap_db.py

# 3) 테스트 (unit/contract)
python -m pytest

# 4) 로컬 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5) Docker Compose (PostgreSQL + API)
docker compose up --build

# 6) Production Compose (strict security on)
docker compose -f docker-compose.prod.yml up --build -d
```

## 환경 변수

`.env.example`을 복사해 값을 설정하세요 (`Copy-Item .env.example .env`).

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `POSTGRES_HOST` | `127.0.0.1` | DB 호스트 |
| `POSTGRES_PORT` | `5432` | DB 포트 |
| `POSTGRES_USER` | `app_user` | DB 사용자 |
| `POSTGRES_PASSWORD` | `change_me` | DB 비밀번호 (**운영 시 반드시 변경**) |
| `POSTGRES_DB` | `civic_archive` | DB 이름 |
| `DB_POOL_SIZE` | `10` | SQLAlchemy 커넥션 풀 크기 |
| `DB_MAX_OVERFLOW` | `20` | 풀 초과 허용 커넥션 수 |
| `DB_POOL_TIMEOUT_SECONDS` | `30` | 풀 커넥션 획득 대기 시간(초) |
| `DB_POOL_RECYCLE_SECONDS` | `3600` | 유휴 커넥션 재생성 주기(초) |
| `DB_CONNECT_TIMEOUT_SECONDS` | `3` | DB TCP 연결 타임아웃(초) |
| `DB_STATEMENT_TIMEOUT_MS` | `5000` | PostgreSQL statement timeout(ms) |
| `INGEST_MAX_BATCH_ITEMS` | `200` | `POST /api/*` 최대 batch 수 |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | write 요청 최대 payload 크기(bytes) |
| `DEBUG` | `0` | debug/reload 모드 |
| `APP_ENV` | `development` | 실행 환경 (`development`/`staging`/`production`) |
| `SECURITY_STRICT_MODE` | `0` | `1`이면 운영 보안 가드 강제 |
| `PORT` | `8000` | 서버 포트 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `LOG_JSON` | `1` | JSON 구조화 로그 |
| `REQUIRE_API_KEY` | `0` | `1`이면 `/api/*`에 `X-API-Key` 필수 |
| `API_KEY` | `` | API 키 값 |
| `REQUIRE_JWT` | `0` | `1`이면 `/api/*`에 `Authorization: Bearer` 필수 |
| `JWT_SECRET` | `` | JWT HMAC secret (최소 32 bytes, HS256 고정) |
| `JWT_LEEWAY_SECONDS` | `0` | `exp`/`nbf` 클레임 허용 오차(초) |
| `JWT_AUDIENCE` | `` | 지정 시 `aud` 클레임 검증 |
| `JWT_ISSUER` | `` | 지정 시 `iss` 클레임 검증 |
| `JWT_SCOPE_READ` | `archive:read` | GET/HEAD 권한 scope |
| `JWT_SCOPE_WRITE` | `archive:write` | POST/PUT/PATCH 권한 scope |
| `JWT_SCOPE_DELETE` | `archive:delete` | DELETE 권한 scope |
| `JWT_ADMIN_ROLE` | `admin` | 이 role 보유 시 scope 검사 우회 |
| `RATE_LIMIT_PER_MINUTE` | `0` | IP 기준 분당 요청 제한 (`0`이면 비활성) |
| `RATE_LIMIT_BACKEND` | `memory` | `memory` 또는 `redis` |
| `REDIS_URL` | `` | Redis 연결 URL (`RATE_LIMIT_BACKEND=redis`일 때 필수) |
| `RATE_LIMIT_REDIS_PREFIX` | `civic_archive:rate_limit` | Redis 키 prefix |
| `RATE_LIMIT_REDIS_WINDOW_SECONDS` | `65` | Redis 고정 윈도우 TTL(초) |
| `RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS` | `5` | Redis 장애 시 재시도 쿨다운(초) |
| `RATE_LIMIT_FAIL_OPEN` | `1` | Redis 장애 시 요청 허용(`1`) / 차단(`0`) |
| `TRUSTED_PROXY_CIDRS` | `` | 신뢰할 프록시 CIDR(쉼표 구분). 설정 시에만 `X-Forwarded-For` 신뢰 |
| `CORS_ALLOW_ORIGINS` | `*` | 허용 Origin(쉼표 구분) |
| `CORS_ALLOW_METHODS` | `GET,POST,DELETE,OPTIONS` | 허용 HTTP 메서드 |
| `CORS_ALLOW_HEADERS` | `*` | 허용 헤더 |
| `ALLOWED_HOSTS` | `*` | Trusted Host 목록(쉼표 구분) |

## 운영 정책

- 스키마 변경은 Alembic만 사용합니다 (`BOOTSTRAP_TABLES_ON_STARTUP=0` 고정).
- 배포 파이프라인에서 `python -m alembic upgrade head`를 필수로 실행합니다.

## 보안 기본선

기본값(`REQUIRE_API_KEY=0`)은 로컬 개발 편의용입니다. 운영 환경에는 반드시 인증을 활성화하세요.

| 항목 | 설정 |
|------|------|
| 인증 | `REQUIRE_API_KEY=1`+`API_KEY` 또는 `REQUIRE_JWT=1`+`JWT_SECRET`(≥32 bytes) |
| Strict 모드 | `SECURITY_STRICT_MODE=1`: 인증 필수·`ALLOWED_HOSTS`/`CORS_ALLOW_ORIGINS` wildcard 금지·`RATE_LIMIT_PER_MINUTE > 0` 강제 |
| Rate limit | 다중 인스턴스 환경은 `RATE_LIMIT_BACKEND=redis` 사용 (`memory`는 단일 워커 전용) |
| 프록시 | `TRUSTED_PROXY_CIDRS` 명시 시에만 `X-Forwarded-For` 신뢰 |
| 요청 크기 | 운영 환경에 맞게 `MAX_REQUEST_BODY_BYTES`, `INGEST_MAX_BATCH_ITEMS` 조정 |

## 마이그레이션

```bash
python -m alembic upgrade head          # 최신 버전 적용
python -m alembic revision -m "..."     # 새 리비전 생성
python -m alembic downgrade -1          # 1단계 롤백
```

## 문서

| 문서 | 내용 |
|------|------|
| [docs/API.md](docs/API.md) | API 엔드포인트 레퍼런스 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 아키텍처 및 설계 결정 |
| [docs/TESTING.md](docs/TESTING.md) | 테스트 및 품질 게이트 |
| [docs/PERFORMANCE.md](docs/PERFORMANCE.md) | 성능 정책 및 임계값 |
| [docs/SLO.md](docs/SLO.md) | SLO/SLI/에러 버짓 정책 |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | 운영 런북 |
| [docs/VERSIONING.md](docs/VERSIONING.md) | 버전 및 릴리스 정책 |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | 변경 이력 |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | 기여 가이드 |
| [docs/BACKLOG.md](docs/BACKLOG.md) | 미결 항목 |
