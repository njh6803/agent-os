# 2026-10-13 (56) collect.py --since 창 로직을 tools/로 옮겨 pytest로 고정

브랜치 `chore/sweep-window-to-tools`, 워크트리 `.claude/worktrees/sweep-window-to-tools`. 일지 2026-10-13-42 "다음"의 판정 전
후보다. 이 세션도 레벨 스윕의 갈래다(지시문의 모델 줄 `Opus 5.5 / medium. 레벨 스윕의 갈래`).

> 사용자: "일지 2026-10-13-42의 \"다음\" 절의 판정 전 후보(collect.py --since 창 로직을 tools/로 옮겨 pytest로 고정)를 한다"

## 시작

주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌았다. 루트를 `65685b2`에서 `1fb0fde`(PR #224)로 당겼다. 판정에서 지울
후보는 없었다. 넘긴 것은 지난 일지와 같은 여섯(prunable 둘, `.tidy-probe` 하나, 분리 HEAD 둘, 머리와 끝이 다른
`skill-check-and-retro-section`)이고, 나머지는 잠금 pid·쥔 프로세스·다시 만들 수 없는 무시된 항목·병합된 PR 없음·제목이 그
브랜치인 세션으로 남았다. 그 뒤 `EnterWorktree`로 들어가 브랜치를 바꿨다.

## 구현

- `tools/session_cost_window.py`(새 파일): `collect.py --since`의 창에서 판정하는 부분을 순수 함수로 뗐다. 창 값 읽기
  (`parse_since`, 시각대 없는 값은 UTC), 창 안(`in_window`, 경계 포함), 브랜치의 첫 사람 트리거(`first_humans`, 창과
  관계없이), 첫 지시문(`first_directive`, 창 안만), 사람 개입의 지시문 아닌 메시지(`human_nondirective`, 창 앞 첫 트리거는
  빼지 않는다), `cost-state`를 남길 세션(`cost_state_sessions`)이다. 기록 읽기와 턴 짓기는 `collect.py`에 남기고, 도구는 턴의
  머리(`TurnHead`: 시작, 브랜치, 트리거, 글)만 받는다. 턴과 응답을 어느 시각으로 창에 거는지(턴은 시작, 응답은 응답 시각,
  세션 비용은 창 없이)는 `collect.py`에 남았다. 그 자리를 떼면 `in_window`를 한 번 감싸는 위임 함수만 생겨 떼지 않았다.
- `collect.py`: 위 함수를 부르게 바꿨다. 턴 루프는 머리를 모으고, 첫 사람 트리거·첫 지시문·사람 개입은 루프 뒤에 도구로
  셈한다. meta에 창 도구의 해시(`window_sha256`)를 더했고 `sweep.py` 머리 줄이 그것을 찍는다.
- `failed_names`를 `sweep.py`에서 `tools/model_sweep_judge.py`로 옮겼다(PR #224 claude-review 둘째·셋째 회차의 보류). 창
  로직과 같은 이유(판정 전에 회귀를 잡을 자리가 없다)이고, 일지 42 "남은 틈"이 손으로 다시 보겠다던 둘 가운데 하나다.
  `sweep.py`의 `VERSIONED`에 새 도구를 더했다.
- 테스트 `tests/tools/test_session_cost_window.py`(새 파일, 26개)와 `test_model_sweep_judge.py`의 `failed_names` 넷.
- 변이 `.scratch/harness/probes/session_cost_window_mutations.toml`(스물하나, 새 파일)과
  `model_sweep_judge_mutations.toml`의 넷. 프로브 README 표를 고쳤다.

## 확인

- 테스트를 먼저 썼지만 빨강을 돌려 보기 전에 구현을 이어 써서, 처음 빨강은 보지 않았다. 대신 변이로 테스트가 무는 것을
  봤다. 창 도구 열아홉(셀프 리뷰 뒤 스물하나), 판정 도구 마흔여덟(옛 마흔넷과 새 넷)이 모두 기대대로 빨갰다.
- 옮기기 전후의 `collect.py`를 같은 트랜스크립트 사본(`~/.claude/projects/C--project-agent*` 2.3GB를 스크래치에 복사)과 같은
  `gh` 캐시로 창 있음(`--since 2026-10-13T04:11:21Z`)·없음 둘 다 돌려 `branches.json`이 `collect_sha256`만 빼고 같은 것을
  손으로 봤다(행 217). 창 있음의 사람 개입 합은 2, 없음은 653이라 창 경로가 돌았다. 첫 시도는 사본의 경로가 260자를 넘어
  옛 판과 새 판이 같은 자리에서 2로 끝났고, `\\?\` 접두사로 다시 돌렸다. 셀프 리뷰를 반영한 뒤 두 갈래를 다시 돌려 해시
  칸(`collect_sha256`, 새 `window_sha256`)만 빼고 같은 것을 봤다.
- 첫 커밋의 pre-commit 열여섯이 모두 통과했다(Skipped 없음). PR 직전에 `origin/main`(PR #225·#218·#227)으로 리베이스하며
  `.scratch/retro-queue.md` 238 행이 충돌해 두 쪽 회차를 합쳤다. `git rebase --continue`는 pre-commit을 돌리지 않아, 합친
  상태의 검사는 일지 번호를 46에서 51로 옮긴 둘째 커밋(병합 직전 main에 일지 54가 들어와 다시 56으로 옮겼다)의 pre-commit으로 봤다(main에 일지 47이 들어와 46이 이름순으로 앞섰다).
- `sweep.py prereg`와 `analyze.preregistration()`으로 두 사전 등록 절의 해시가 그대로인 것을 봤다. `sweep.py population`도
  0으로 끝났다.

## 셀프 리뷰

`/code-review`, base `1fb0fde`, 바뀐 파일 7과 미추적 3(커밋 전). 명세 축은 옛 `collect.py`가 판정하던 아홉(창 값 읽기, 경계,
첫 사람 트리거, 첫 지시문, 턴 집계, 사람 개입, `cost-state`, 응답 비용과 세션 비용, `failed_names`)을 목록으로 받아 하나도
풀리지 않았다고 봤다.

- 고친 것
  - [Major, 명세] `collect.py`와 새 도구의 독스트링이 턴·응답의 창까지 도구가 정하고 pytest가 고정한다고 적었다. 그 자리는
    `collect.py`에 남았다. 두 독스트링을 실제 경계로 고쳤다("이 파일이 정하는 것"과 "`collect.py`에 남은 것").
  - [Major, 표준] meta의 해시가 `collect.py` 하나라, 입력을 쓴 뒤 창 도구가 바뀌면 판정이 모른다. `window_sha256`을 더했다.
    `costs.py`의 같은 틈은 옛 것이라 `collect.py`·`sweep.py` 독스트링에 적었다.
  - [Minor] 첫 지시문이 귀속되지 않은 턴도 보는 것을 깨는 변이가 없었고, 지시문 판정이 `다음 작업:`만 본다는 "못 보는 것"을
    고정하는 테스트가 없었다. 변이 둘과 테스트 하나를 더했다. 독스트링의 지시문 문장이 사람 트리거 조건을 빠뜨린 것(Nit)도
    고쳤다.
  - [Nit] `parse_ts` 중복은 `collect.py`가 도구의 것을 쓰게 했고, 창이 없을 때도 `stamps`를 짓던 것은 창이 있을 때만 짓게
    했다(옛 코드도 그랬다).
- 남긴 것
  - [Nit] 첫 사람 트리거를 `tuple[str, str]`로 넘기는 것과 `failed_names`가 표의 열 순서를 자리로 푸는 것(Primitive
    Obsession). 옛 `collect.py`·`sweep.py`의 모양을 그대로 옮긴 것이라 이번 범위에서 바꾸지 않았다.
  - [Nit] 변이 "첫 사람 트리거를 창 안에서만 봄"이 시각을 문자열로 박았다. `first_humans`는 창을 받지 않아 창을 흉내 낼 다른
    자리가 없다. 테스트의 시각을 바꾸면 이 변이를 같이 본다.
- 다시 돌린 것: 변이 둘(창 도구, 판정 도구)과 옮기기 전후 비교 두 갈래. 손으로 치는 검증 다섯은 커밋의 pre-commit으로
  갈음한다.

## PR 리뷰

PR #229. CodeRabbit은 두 번 모두 무료 한도에 걸려 리뷰하지 않았다. 그 사이 main에 PR #228이 들어와 충돌해(대기열 끝 행)
main을 합쳤다. claude-review 두 회차는 동작 변화를 찾지 못했다.

- 첫 회차 Minor(`TurnHead.trigger`의 값이 독스트링에서 읽히지 않는다)는 넷(`human`·`auto`·`interrupt`·`start`)을 적어
  고쳤다. `Literal`로 좁히는 것은 `collect.py`의 `Turn.trigger`부터 좁혀야 해 하지 않았다. 첫 회차 Nit 둘(별칭, 독스트링의
  출처 인용)은 보류했다. 별칭은 `collect.py`의 다른 함수가 그 이름으로 쓰고, 출처 인용은 근거를 적는 이 저장소의 관례다.
- 둘째 회차는 Minor(`parse_ts`가 판정 도구와 같은 본문)와 Nit(`human_nondirective`의 `first`를 따로 받음)뿐이라 규약대로
  보류 이유를 PR 코멘트에 남겼다.

## 회고

후보 넷: 승인 둘, 기각 둘, 넘김 없음.

- 승인(대기열 242, 새 행): `tools/session_cost_window.py`를 테스트 파일 직후에 써서 빨강을 보지 않았다(원칙 II). 사건은 이
  세션의 "확인" 첫 줄이다. 막는 층으로 바로 가기에는 1회차라, 반복을 세는 행으로 두고 어디로 칸에 계기 훅 후보를 적었다. PR
  하나로 되돌린다.
- 승인(대기열 238, 회차 더함): `tidy-checkouts`가 같은 여섯을 넘긴 것이 일지 42와 이 세션에서도 났다. 행이 사람 몫이라
  회차만 더했다(리베이스에서 main 쪽 일지 45의 회차와 합쳐 6회차).
- 기각: 스냅숏 경로가 260자를 넘어 `collect.py`가 실패한 것. 실제 입력(`~/.claude/projects/`)의 경로는 짧아 이 세션의 비교
  사본에서만 나고, `\\?\` 접두사로 바로 풀렸다.
- 기각: 도구 호출 사이의 영어 문장 넷, 큰 heredoc 둘, 스크래치로의 `cd` 하나. 모두 있는 훅(`hook_midturn_korean`,
  `hook_bash_heredoc`, `hook_bash_cd_outside`)이 그 자리에서 잡았다.

## 다음

- 레벨 스윕의 판정은 2026-12-15 0시(UTC) 뒤에 한 번이다(일지 2026-10-13-33 "다음"의 첫 항목 그대로). 명령은 스윕 프로브
  README의 둘이고, 판정의 입력 `branches.json`도 커밋한다. 결과는 ADR 0029 이력 초안으로 올려 승인받는다.
- 남은 틈: `sweep.py`의 두 사전 등록 절 해시 대조는 자동 시험이 없다. 판정 전 마지막 점검에서 절을 한 글자 바꾼 사본으로
  손으로 다시 본다. `collect.py`의 기록 읽기·턴 짓기·귀속과, 턴·응답을 어느 시각으로 창에 거는지는 여전히 프로브 안이라
  자동 시험이 없다(옮기기 전후 비교만 했다). `costs.py`는 meta에 해시가 없어 입력 시점의 판과 견주지 못한다.
- 스윕 뒤의 후보: PR을 연 뒤의 몫만 낮은 모델로 돌리는 것(ADR 0029 이력 2026-10-13).
