# 2026-10-13 (60) 회차 감시 행 여섯의 자리를 사다리로 정한다

브랜치 `chore/third-recurrence-rules`, 워크트리 `.claude/worktrees/third-recurrence-rules`. 레벨 스윕의 갈래다(지시문의 모델 줄
`Opus 5.5 / medium. 레벨 스윕의 갈래`).

> 사용자: "대기열 109·110·111·116·119·140(어디로 칸이 \"3회차가 되면 규칙 후보로 자리를 정한다\"인 회차 감시 행 여섯)의 자리를 교정 루프의 사다리로 정해 chore 한 PR로 반영한다"

## 시작

주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌았다. 루트를 `25fe55e`에서 `c170046`(PR #229)으로 당겼다. 첫 판정은 지울
후보를 여럿 냈지만(출력의 앞부분이 잘려 수는 세지 못했다), 출력을 파일로 받으려고 다시 친 판정에서는 같은 후보가 모두 "모듈을 올린 프로세스"(python·node·esbuild)로
남김이 되어 지우지 않았다. 넘긴 것은 지난 일지와 같은 일곱(분리 HEAD 셋, prunable 둘, `.tidy-probe` 하나, 머리와 끝이 다른
`skill-check-and-retro-section`)이다. 그 뒤 `EnterWorktree`로 들어가 브랜치를 바꿨다.

## 자리를 정한 근거

지시문의 "다음 작업" 줄은 여섯을 3회차에 이른 행이라 적었지만(그 줄은 일지에 옮긴 시작 프롬프트 밖이라 저장소에 원문이 없다),
대기열과 일지에는 1회차 넷(109·110·111·140)과 2회차 둘(116·119)뿐이다. 그래도 자리를 정하는 것이 맞다. 여섯은 모두 2026-10-12 retro 개정(일지 2026-10-12-41) 전에 들어온 행이다. 개정 뒤의 retro
4단계는 "세 번째 반복"의 문턱을 `CODING_STANDARDS.md`의 줄에만 걸고, 검사가 잡을 수 있는 것은 검사로, 행동이 일어나는 자리(그
단계의 스킬, 그 경로의 rules)의 문장은 사건 하나로 반영한다. 여섯 가운데 코드 리뷰의 판단 기준(`CODING_STANDARDS.md`)에 갈
것은 없었다.

| # | 자리 | 사다리의 층과 이유 |
|---|---|---|
| 111 | `tools/hook_env_read.py`의 Bash 거부 문구 | 훅. 막기는 호출 단위라 묶은 편집도 돌지 않는다. 그 사실을 막는 순간에 알린다. 묶음을 미리 막는 판정은 편집과 검색을 가려낼 고정 패턴이 없어 두지 않았다 |
| 116 | `.claude/rules/tools.md` + `tidy-checkouts` 스킬의 "하지 않는 것" | 경로 rules와 스킬. 첫 사건은 그 스킬의 대체 절차(도구가 생기기 전), 둘째는 `tools/tidy_checkouts.py`다 |
| 119 | `.claude/rules/channel.md` + `.claude/rules/core.md` | 경로 rules. 첫 사건은 채널 구독의 `_concluded`, 둘째는 `core/run.py`의 결말 가드다 |
| 109·110 | `CLAUDE.md` 환경 함정(한 줄) | 행동이 일어나는 경로나 스킬이 없다. 워크플로와 백그라운드 작업은 어느 단계에서나 쓴다 |
| 140 | `CLAUDE.md` 원칙 | 사람에게 주는 답의 꼴이라 경로나 스킬이 없다. 같은 절의 대기열 114 줄 옆이다 |

`CLAUDE.md`에 둘을 더한 것은 매 세션의 컨텍스트 비용이다. 109·110을 한 줄로 묶어 줄 수를 줄였다(100줄에서 102줄).

## 구현

- `tools/hook_env_read.py`: Bash 판정이 막을 때 이유 끝에 `WHOLE_CALL_NOTE`("이 Bash 호출 전체가 돌지 않았다…")를 붙인다.
  Grep 도구의 이유에는 붙이지 않는다(호출에 다른 명령이 없다). 판정(무엇을 막나)은 그대로다.
- 테스트 `test_Bash_를_막으면_묶은_다른_명령도_돌지_않았다고_알린다`를 먼저 써서 빨강(문구 없음)을 본 뒤 구현했다.
- `.claude/rules/tools.md`, `.claude/rules/core.md`, `.claude/rules/channel.md`, `tidy-checkouts` 스킬, `CLAUDE.md`에 한 항목씩
  더하고, `.scratch/retro-queue.md`의 여섯 행을 닫았다.

## 셀프 리뷰

`/code-review origin/main`(base `c170046`, 바뀐 파일 여섯과 미추적 일지 하나, 커밋 0). 두 축이 같은 Major 셋을 냈다.

- 고쳤다(Major): 119와 116의 첫 사건이 처음 고른 rules의 `paths` 밖에서 났다. 119의 `_concluded`는 채널 코드였고(일지
  2026-10-06-01), 116의 첫 사건은 `tools/tidy_checkouts.py`가 생기기 전 스킬의 절차였다. 119는 `channel.md`에, 116은
  `tidy-checkouts` 스킬에 한 줄씩 더했다. 위 표의 근거 칸도 그에 맞게 고쳤다.
- 고쳤다(Major): `CLAUDE.md` 109·110 줄의 "자기 말로"가 원문 "자기에게 온 말로"(일지 2026-10-05-05)와 뜻이 달랐다.
- 고쳤다(Minor): `tools.md`의 116 사건 서술을 원문(`_long`의 `abspath` 정규화, 잡은 것은 `bug-perf-review`)에 맞췄다. 일지의
  근거 없는 따옴표 인용을 뺐다. 닫은 대기열 행의 꼴(어디로 칸에 취소선 없음, 닫힘 표지는 승인 칸 끝)을 기존 행에 맞췄다.
- 남겼다(Minor): 109·110을 `CLAUDE.md` 환경 함정에 둔 것. 그 절의 머리("명령을 치기 전에 알아야")와 110이 꼭 맞지는 않지만
  경로·스킬이 없는 매 세션 지침의 자리는 그 절과 원칙 절뿐이고, 원칙 절은 답과 문서의 꼴을 다룬다.
- 남겼다(Nit): 111의 안내가 `hook_env_read` 하나에만 붙은 것. 호출 단위로 막는 다른 Bash 훅도 같지만 사건은 그 훅에서 났다.
  같은 묶음이 다른 훅에서 다시 막히면 그때 넓힌다.

## 확인

- `uv run pytest -q`: 2663 통과. `ruff check`, `ruff format --check`, 바꾼 파이썬 파일의 `pyright`, `tools/check_instructions.py`
  초록. 나머지 게이트는 커밋의 pre-commit이 돈다.
- 바꾼 rules와 `CLAUDE.md`는 새 `claude -p` 세션(Haiku 5.5, 워크트리에서)에서 `core/run.py`와 `tools/mutate.py`를 Read로
  열게 한 뒤, 새 문장 넷을 원문 그대로 옮기는 것을 손으로 봤다. 셀프 리뷰 반영 뒤에는 또 하나의 새 세션에서
  `channel/http/end_user.py`를 열어 `channel.md`의 새 문장이, Skill 도구로 부른 `tidy-checkouts`에 새 행이 실린 것을 같은 식으로
  봤다.
- 셀프 리뷰를 반영한 뒤의 검증 명령은 커밋의 pre-commit으로 갈음한다(결과는 PR 본문).

## PR 리뷰

PR #233. PR 직전 리뷰는 CodeRabbit 좌석이 없어(`Seat: not assigned`) 대체 둘을 돌렸고 둘 다 0건이었다(`/security-review`,
`bug-perf-review`). PR 봇의 CodeRabbit은 무료 한도로 리뷰가 없었다. claude-review 첫 회차는 Minor 하나와 Nit 둘이었다.

- 고쳤다(Minor): `channel.md`와 `core.md`가 같은 규칙과 사건을 두 번 적었다. 본문과 사건은 `core.md`에 두고 `channel.md`는
  행동 문장 하나와 포인터로 줄였다. 채널 파일을 열 때도 행동 문장은 실린다.
- 고쳤다(Nit): `channel.md`의 새 항목에 이웃 항목처럼 굵은 머리 문장을 달았다.
- 남겼다(Nit): 거부 문구의 "(대기열 111)". 같은 훅의 다른 거부 문구도 "(대기열 43)"을 싣는 관례이고, 모델이 그 번호로
  대기열의 사건을 찾아갈 수 있다.
