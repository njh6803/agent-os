# release-followup-timeouts-and-failure-table: 판 내기 첫 성공 뒤 후속 정리 셋

**What to build:** CI 판 내기(`.github/workflows/release.yml`)가 2026-11-17에 처음 성공해 릴리스 `v0.1.0-rc.1`이 공개되었다(실행 44012310177). 그 일지 `docs/journal/2026-11-16-2249-ci-publishes-release-from-main.md`의 "다음" 2가 넘긴 후속 셋을 한 PR로 고친다.

1. `docs/constitution/operations.md`의 실패 표에서 `시험한 이미지와 올린 이미지 대조` 줄이 "두 이미지의 설정 해시가 다를 때"만 실패한다고 적는다. 핫픽스 PR 599 뒤에는 올린 색인의 digest를 레지스트리에서 읽지 못할 때도 `::error::`로 실패한다. 줄에 그 경우를 더한다.
2. `timeout-minutes`를 잰 시간에 맞춰 줄인다(`release.yml` 잡 `build`와 `publish`, `ci.yml` 잡 `e2e-standalone`). 근거가 되는 프로브 `.scratch/harness/probes/ci_job_durations.py`에 `e2e-standalone`과 release 워크플로의 두 잡을 더해 다시 잰다.
3. `release.yml`의 작은 정리: 이미지 올리기 단계의 쓰지 않는 `id: push`와 두 단계에 중복인 `TAG: sha-${{ github.sha }}`.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 실패 표의 대조 줄이 "설정 해시가 다를 때"와 "올린 색인의 digest를 읽지 못할 때"를 모두 적는다
- [x] 헌법 판(`docs/constitution/README.md`)을 올린다(operations.md 변경이므로, 3.1.0 → 3.1.1). ADR 0056 이력은 사용자가 남기지 않기로 했다(2026-11-17, 선택 화면. 일지에 원문)
- [x] 프로브가 `e2e-standalone`(시험을 돈 실행만)과 release의 `build`·`publish`를 재고 README 행에 결과를 적는다
- [x] 세 `timeout-minutes`가 근거와 함께 정해진다: `e2e-standalone` 45→15(잰 최대 3.0분의 5배), `build` 90→30(캐시가 빈 실행 8.3분의 3.6배, 잰 5.4분의 5.6배), `publish` 30→10(1.0분의 10배). 두 워크플로의 주석이 근거를 적는다
- [x] `release.yml`에서 `id: push`를 지우고 `TAG`가 잡의 `env.HASH_TAG` 한 곳에서 정해진다. `tests/tools/test_release_workflow.py`는 `$TAG` 단언을 `$HASH_TAG`로 맞췄고, `steps.push`는 변이 예시 글일 뿐이라 그대로다
- [x] 검증 명령이 모두 초록이다(`uv run python tools/run_checks.py` 종료 0, ruff 둘, zizmor)
- [ ] PR 본문 "남긴 위험"에 다음 출시 PR이 실제 판 내기로 이 변경을 처음 시험한다는 점을 적는다

## 확인한 근거 (2026-11-17)

- 프로브 출력(`ci_job_durations.py 120`, `--release 40`)과 배수의 계산은 `.scratch/harness/probes/README.md`의 그 프로브 행에 있다.
- 캐시가 빈 `build` 8.3분과 `e2e-standalone`의 캐시 빈 몫 "5분 안팎"은 앞 세션 일지가 `gh run view`로 손으로 읽은 값에서 뺀 어림이다(점검 2분 29초, 올리기 39초를 8분 17초에서 뺐다). 이 잡의 캐시가 빈 실행은 재지 못했다.
- 같은 프로브가 python 잡의 최대 14.3분이 그 잡의 제한 15분에 닿는 것을 보였고, web(15/5.2)과 visual(20/8.1)도 네 배에 못 미친다(손으로 나눴다). 이 티켓의 범위 밖이라 고치지 않고 PR 본문과 일지에 남겼다.
