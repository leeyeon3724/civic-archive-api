## 변경 요약

- 어떤 변경을 왜 했는지 작성해주세요.

## 관련 이슈

- Issue: #

## 변경 유형

- [ ] feat
- [ ] fix
- [ ] refactor
- [ ] docs
- [ ] chore
- [ ] breaking change

## 기본 체크리스트

- [ ] `python scripts/check_commit_messages.py --rev-range origin/main..HEAD --mode fail` 실행
- [ ] `python -m pytest -q -m "not e2e and not integration"` 실행
- [ ] `python scripts/check_docs_routes.py` 실행
- [ ] `python scripts/check_schema_policy.py` 실행
- [ ] 동작/API 변경 시 문서 업데이트
- [ ] 변경 사항에 맞는 테스트 추가/수정

## DB / 마이그레이션

- [ ] 스키마 변경 없음
- [ ] Alembic revision 포함
- [ ] `python -m alembic upgrade head` 검증
- [ ] `python -m alembic downgrade -1` 검증

Revision:

- 

## API 계약

- [ ] API 계약 변경 없음
- [ ] `docs/API.md` 업데이트
- [ ] 에러 스키마 호환성 확인

## 성능

- [ ] 성능 민감 변경 아님
- [ ] `python scripts/benchmark_queries.py --profile staging` 실행
- [ ] benchmark delta 작성 (baseline 대비)

### Benchmark Delta (성능 민감 변경 시)

| Scenario | Baseline p95(ms) | Current p95(ms) | Delta |
|----------|------------------|-----------------|-------|
| news_list |  |  |  |
| minutes_list |  |  |  |
| segments_list |  |  |  |

## 리스크 / 롤백

- 리스크:
- 롤백 계획:
