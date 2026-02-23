# 백로그

완료된 항목은 git log로 관리합니다.

## 미결 항목

### P11-7: JSONB 필드 중첩 깊이 가드

- **리스크**: `tag`, `moderator`, `questioner`, `answerer` 등 `Any` 타입 JSONB 필드에 1000단계 이상 중첩 JSON 입력 시 `_canonical_json_value` 재귀에서 `RecursionError` 가능
- **현재 완화**: `MAX_REQUEST_BODY_BYTES=1MB` 스트리밍 가드
- **착수 조건**: 알려지지 않은 외부 ETL 소스 추가 또는 공개 쓰기 엔드포인트 전환 시

### P11-8: COUNT(*) 페이지네이션 성능 모니터링

- **현황**: 전체 목록 엔드포인트에서 데이터 쿼리 + 카운트 쿼리 2회 실행 (`app/repositories/common.py`)
- **리스크**: `council_speech_segments` 50만 행 초과 시 복합 WHERE `COUNT(*)` 지연 비선형 증가
- **착수 조건**: 세그먼트 행 수 > 500,000 또는 SLO 기준 위반 발생 시 keyset pagination 전환 검토
