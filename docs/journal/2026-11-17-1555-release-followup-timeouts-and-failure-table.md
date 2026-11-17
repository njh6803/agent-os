# 판 내기 첫 성공 뒤 후속 정리: 실패 표 문구, 제한 시간, release.yml 정리 (harness release-followup-timeouts-and-failure-table)

브랜치 `chore/release-followup-timeouts-and-failure-table`, 기준은 `origin/dev` `327b8e413`다. 모델 Sonnet 5.5. 앞 세션 일지 `2026-11-16-2249-ci-publishes-release-from-main.md`의 "다음" 2가 넘긴 후속이다.

## 사용자 프롬프트 원문

앞 세션이 보고에 실패한 일이 둘 있다며 선택 화면을 띄웠다.

> 질문: 보고에 실패한 일이 둘 있었습니다. 어느 쪽을 다시 시도할까요?
>
> 사용자가 고른 라벨: 새 세션으로 후속 정리 열기
> 설명: 앞서 자동 모드 분류기가 거부한 새 세션 열기를 다시 시도합니다. 이번 요청이 사용자가 직접 한 것이라 통과할 수 있다고 보지만(어림), 분류기가 다시 거부하면 열리지 않고 이 세션에서 이어 갑니다.

## ADR 0056 이력의 승인

`docs/constitution/operations.md` 실패 표의 대조 줄을 고치므로 ADR 0056의 이력(66행부터의 `## 이력` 절)에 남길지를 이 세션이 선택 화면으로 물었다.

> 질문: 운영 문서(operations.md)의 실패 표 한 줄을 사실에 맞게 고칩니다. 판 내기 결정 기록(ADR 0056)의 이력 절에도 이 고침을 남길까요?
>
> 사용자가 고른 라벨: 남기지 않는다 (추천)
> 설명: 이미 병합된 동작(PR 599)을 문서가 따라가는 문구 정정이라 결정이 바뀌지 않습니다. 헌법 판 번호(지금 3.1.0)만 3.1.1로 올리고 이유는 티켓과 일지에 적습니다.

그래서 ADR은 건드리지 않고 헌법 판만 3.1.0 → 3.1.1(문구 수정은 patch)로 올렸다. `origin/dev`의 판도 3.1.0이다(손으로 `git show origin/dev:docs/constitution/README.md`를 봤다).

## 한 것

- 티켓 `.scratch/harness/issues/release-followup-timeouts-and-failure-table.md`.
- `release.yml`: 이미지 올리기 단계의 쓰지 않던 `id: push`를 지웠다. `TAG: sha-${{ github.sha }}`는 두 단계에 있던 것을 잡의 `env.HASH_TAG` 하나로 모으고 이미지 올리기 단계가 `TAG: ${{ env.HASH_TAG }}`로 받는다. 대조 단계는 `$HASH_TAG`를 바로 쓴다. 시험 `tests/tools/test_release_workflow.py`의 `$TAG` 문자열 단언을 `$HASH_TAG`로 맞췄다(`steps.push` 문자열은 변이 예시 글일 뿐 워크플로를 가리키지 않아 그대로 뒀다).
- `operations.md` 실패 표의 대조 줄에 "올린 색인의 digest를 읽지 못할 때"를 더했다.
- 프로브 `.scratch/harness/probes/ci_job_durations.py`: 조건부 잡 `e2e-standalone`(시험 스텝이 성공한 실행만 측정으로 센다)과 `--release`(release 워크플로의 `build`·`publish`, 표지 스텝 `아티팩트 올리기`·`공개`)를 더하고 gh 호출을 세 번까지 다시 치게 했다. 첫 판의 120개 실행 측정이 HTTP 502 하나로 죽어 다시 치기를 더했고, 판정 기준은 바꾸지 않았다.
- 프로브 결과(프로브 출력): ci 성공한 실행 120개 모두 측정이었고 `e2e-standalone`은 시험이 든 실행 넷이 2.5·3.0·3.0분, release는 `build` 5.4분과 `publish` 1.0분(n=1)이다. 전체 표는 프로브 README 행.
- `timeout-minutes`: `e2e-standalone` 45→15, `build` 90→30, `publish` 30→10. 근거(배수)는 `ci.yml`과 `release.yml`의 주석과 티켓.
- 헌법 판 3.1.0 → 3.1.1(`operations.md`를 고쳤다). `uv run python tools/sibling_overlap.py`는 번호 겹침 없음.

## 검증

- `uv run python tools/run_checks.py` 종료 0(pytest 453.7초, web-verify 557.5초, zizmor 포함 열한 검사 모두 Passed). `uv run ruff check .`와 `uv run ruff format --check .`도 통과했다. 손으로 쳤다.
- 이 PR은 dev로 가서 판 내기를 일으키지 않는다. 바뀐 `release.yml`(`HASH_TAG`, 줄인 제한 시간)은 아직 실제로 돈 적이 없다(돌려 보지 않았다). 다음 출시 PR이 병합될 때 처음 시험된다.
- 범위 밖으로 남긴 것: ci의 python 잡 최대 14.3분이 제한 15분에 닿아 있고(1.05배), web(15/5.2, 2.9배)과 visual(20/8.1, 2.5배)도 머리 주석의 "최대의 네 배 이상"에 못 미친다(프로브 출력과 손으로 한 나눗셈). 후속 티켓이 필요하다.

## 다음

1. PR을 병합하면 다음 출시 PR이 `release.yml`을 처음 실제로 돌린다. 그 실행을 지켜보며 `build`·`publish`의 시간이 새 제한(30분, 10분) 안인지 본다.
2. ci의 python·web·visual 잡의 `timeout-minutes`(15, 15, 20)를 잰 시간(최대 14.3, 5.2, 8.1분)의 네 배 이상으로 올린다.

## 셀프 리뷰 (이 세션)

base `327b8e413`, 파일 7개 수정, 미추적 2개, 커밋 0개. 표준 축(sonnet·high)과 명세 축을 병렬로 돌렸다. Critical·Major는 없었다. 두 축은 프로브를 다시 돌려(`ci_job_durations.py 120`, `--release 40`) README와 같은 값을 냈고 `gh run view`로 실행 시각과 8.3분을 손으로 맞췄다고 보고했다.

고친 것:
- 시험이 약했다(명세 축 Minor). `$HASH_TAG`로 읽는 단언만으로는 잡의 `HASH_TAG` 정의나 올리기 단계의 `TAG`를 틀리게 해도 초록이다. `test_이_저장소의_판_내기_워크플로는_올리는_태그와_읽는_태그를_한_변수에서_받는다`를 더해 정의, 올리기 쪽 `TAG: ${{ env.HASH_TAG }}`, `sha-${{ github.sha }}`가 한 곳뿐임을 본다.
- `operations.md` 78행의 "원인이 첫 값인 `timeout-minutes`의 어림이면"이 낡았다(이제 잰 값이다). "잰 시간에 정한 `timeout-minutes`가 모자란 것이면 … (값의 근거는 `release.yml` 머리 주석)"으로 고쳤다.
- 프로브의 집계(표준 축, `probes.md` 첫 항목). 시험 안 돈 실행 21개만 세고 120개 가운데 나머지 95개는 어디에도 세지 않았다. 지금은 "시험이 든 4 + 시험 안 돈 21 + 그 잡이 없거나 성공이 아닌 95 = 120"을 찍고, 조건부 잡의 측정이 0이면 1로 끝낸다. `ci_job_durations.py 120`을 다시 돌려 합 120을 봤다(프로브 출력). 판정 기준(무엇을 측정으로 세는지)은 바뀌지 않았고 집계만 더했다. `Rounds`는 쓰지 않았다.
- 프로브의 죽은 코드 `raise AssertionError`를 지웠고 독스트링에 표지가 스텝 이름의 부분 문자열이라 깨질 수 있는 자리(이름 없는 시험 스텝, `공개`)를 "못 보는 것"으로 적었다.
- 닫힌 서술의 반례(표준 축). "python만 네 배에 못 미친다"고 적었지만 web은 15/5.2=2.9배, visual은 20/8.1=2.5배다. README, 티켓, 일지의 서술과 "다음"을 세 잡으로 고쳤다(손으로 나눴다).

남긴 것: `TAG: ${{ env.HASH_TAG }}`의 한 겹 간접은 두었다(bake 액션이 `TAG`라는 이름으로 읽고, 대조 단계는 `HASH_TAG`를 쓰는 두 이름을 한 정의가 이어 준다). `measure_ci`·`measure_release`의 집계 중복(냄새, 판단 항목)은 프로브가 두 번 돌 일이 드물어 합치지 않았다. 대조 단계가 `imagetools inspect --raw`나 `release_ci.py` 실패로 `::error::` 없이 죽을 수 있는 불완전은 이 변경 이전부터이고 범위 밖이다.

다시 돌린 명령: `uv run pytest -q tests/tools/test_release_workflow.py`(5개 통과), 프로브의 `ruff check`·`ruff format`. 전체 게이트는 커밋의 pre-commit으로 갈음하고 결과는 PR 본문에 적는다.
