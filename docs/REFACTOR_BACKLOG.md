# 리팩터링 백로그

## 완료 단계 요약

| 단계 | 주제 | 상태 |
|------|------|------|
| P1 | 운영 기반 (readiness 분리, 세그먼트 멱등성, 인코딩 수정) | 완료 |
| P2 | 운영 강화 (Redis 레이트 리미터, 메트릭 카디널리티, 버전 정책) | 완료 |
| P3 | 보안 강화 (JWT/RBAC, 프록시 검증, 공급망 보안) | 완료 |
| P4 | SLO/관측성 운영 (SLI/SLO, 에러 버짓, 알림 정책, 런북) | 완료 |
| P5 | 성능/확장성 기준선 (DB 풀 튜닝, 쿼리 지연 가드, 처리량 제한) | 완료 |
| P6 | 런타임 검증 강화 (스트리밍 요청 가드, 관측성 레이블, E2E 개선) | 완료 |
| P7 | 엔지니어링 품질 (설정 안전성, 쿼리 정확성, lint/coverage 게이트) | 완료 |
| P8 | 아키텍처 분리 (create_app 모듈화, 부트스트랩 경계, DI 마이그레이션) | 완료 |
| P9 | 로드맵 갱신 (테스트 결정성, 타입 게이트 확장, 보안 모듈 분리, 검색 전략, 운영 Compose) | 완료 |
| P10 | 데이터 정확성 (JWT secret 최소 길이, published_at UTC 정규화) | 완료 |
| Post-P8 | DB DI 완성, 배치 쓰기 최적화, 관측성/품질 게이트 follow-up | 완료 |

---

## P11 리스크 기반 강화

### 우선순위 매트릭스

| 티켓 | 설명 | 점수 | 상태 |
|------|------|------|------|
| P11-1 | 메모리 레이트 리미터 다중 워커 안전성 | 20 | **완료** |
| P11-2 | 보안 기본값 시작 시 불변 검증 | 15 | **완료** |
| P11-3 | 필터 파라미터 팬아웃 제거 (query TypedDict) | 15 | **완료** |
| P11-4 | 레거시 dedupe 해시 관측 가능성 | 12 | **완료** |
| P11-5 | `JWT_ALGORITHM` 설정 필드 제거 | 12 | **완료** |
| P11-6 | 기본 DB 패스워드 시작 시 경고 | 9 | **완료** |
| P11-7 | JSONB 필드 중첩 깊이 가드 | 9 | 보류 |
| P11-8 | COUNT(*) 페이지네이션 성능 모니터링 | 12 | 보류 |

### P11-1: 메모리 레이트 리미터 다중 워커 안전성 (완료)

`InMemoryRateLimiter`는 프로세스 로컬이므로 `--workers N` 환경에서 실제 허용량이 `RATE_LIMIT_PER_MINUTE × N`이 되어 레이트 리밋이 무력화됨.

- strict mode + `RATE_LIMIT_BACKEND=memory` + `RATE_LIMIT_PER_MINUTE > 0` 조합 → 시작 시 `RuntimeError`
- 비 strict 환경에서 memory backend 선택 시 `WARNING` 로그 출력

### P11-2: 보안 기본값 시작 시 불변 검증 (완료)

환경 변수 누락 시 인증 없이 전체 API가 공개될 수 있는 위험.

- strict mode + 인증 전무 → `RuntimeError`
- strict mode + `RATE_LIMIT_PER_MINUTE=0` → `RuntimeError`
- non-dev 환경에서 인증 미설정 시 `WARNING` 로그

### P11-3: 필터 파라미터 팬아웃 제거 (완료)

`list_segments` 기준 13개 파라미터가 route → service → repository 5개 레이어에 중복 선언됨.

- `NewsListQuery`, `MinutesListQuery`, `SegmentsListQuery` TypedDict를 `app/ports/dto.py`에 정의
- 전 레이어의 `list_*` 함수 시그니처를 단일 query 객체로 통합
- API 계약 변경 없음 (라우트 Query 파라미터 유지)

### P11-4: 레거시 dedupe 해시 관측 가능성 (완료)

`_build_legacy_segment_dedupe_hash`(None → `""` 치환)와 canonical 해시 불일치 시 유효 레코드가 무경고 드롭될 위험.

- `civic_archive_segment_legacy_hash_variant_total` Prometheus 카운터 추가
- 정규화 시점에 두 해시 불일치 감지 및 카운터 증가

> **폐기 타임라인**: 운영에서 레거시 해시 마지막 사용일로부터 90일 후 `dedupe_hash_legacy` 컬럼 DROP 마이그레이션 진행.

### P11-5: `JWT_ALGORITHM` 설정 필드 제거 (완료)

`JWT_ALGORITHM=RS256` 설정 시 실제로는 HS256으로 검증되는 침묵적 잘못된 설정 위험.

- `app/config.py`에서 `JWT_ALGORITHM` 필드 제거
- `app/security_jwt.py`에 HS256 하드코딩 이유 주석 추가 (알고리즘 혼동 공격 방지)
- `.env.example`, `docker-compose.prod.yml`에서 해당 항목 제거

### P11-6: 기본 DB 패스워드 시작 시 경고 (완료)

`POSTGRES_PASSWORD="change_me"` 기본값이 환경 변수 미설정 시 그대로 사용되어 침묵적 마스킹 발생.

- non-dev 환경에서 기본 패스워드 감지 시 `WARNING` 로그 출력
- strict mode에서는 `RuntimeError`로 상향 (시작 차단)

---

## 보류 항목

### P11-7: JSONB 필드 중첩 깊이 가드

- **리스크**: 1000단계 이상 중첩 JSON 입력 시 `_canonical_json_value` 재귀에서 `RecursionError` 가능
- **현재 완화**: `MAX_REQUEST_BODY_BYTES=1MB` 스트리밍 가드
- **조건**: 외부 공개 쓰기 엔드포인트 전환 또는 알려지지 않은 ETL 소스 추가 시 `max_depth` 가드 구현 검토

### P11-8: COUNT(*) 페이지네이션 성능 모니터링

- **현황**: 전체 목록 엔드포인트에서 데이터 쿼리 + 카운트 쿼리 2회 실행
- **리스크**: `council_speech_segments` 50만 행 초과 시 복합 WHERE `COUNT(*)` 지연 비선형 증가
- **조건**: 행 수 > 500,000 또는 SLO 기준 위반 시 keyset pagination 도입 검토
