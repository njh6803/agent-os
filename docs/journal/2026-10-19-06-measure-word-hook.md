# 2026-10-19 (06) 측정 낱말을 쓴 줄에 프로브와 근거 절을 알리는 계기 훅 (대기열 227)

브랜치 `chore/measure-word-hook`. 이 세션의 지금 제목은 `chore/measure-word-hook`이다(인계 직전에 `(인계함)`을 붙인다).

## 사용자 프롬프트

> 사용자: 대기열 227(docs/adr/, probes/README.md, retro-queue.md에 더한 줄이 측정 낱말을 들면서 probes/ 경로도 "손으로"도 없으면 근거 절을 알리는 PostToolUse 계기 훅)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
>
> 다음 작업: 기능 harness. 대기열 227(측정 낱말을 쓴 줄에 프로브와 근거 절을 알리는 계기 훅)을 반영한다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 measure-word-hook)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: 대기열 227(docs/adr/, probes/README.md, retro-queue.md에 더한 줄이 측정 낱말을 들면서 probes/ 경로도 "손으로"도 없으면 근거 절을 알리는 PostToolUse 계기 훅)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
> 브랜치: chore/measure-word-hook
> 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-19-01-full-checks-via-runner.md의 "다음"
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## tidy-checkouts

- 루트: main을 e8d35a75에서 ebd09fbb(origin/main)로 당겼다. 당긴 커밋은 tidy-checkouts 스킬을 바꾸지 않았다.
- 지운 워크트리·브랜치: 없다.
- 넘긴다(사람에게, 답은 기다리지 않았다): `confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`, `vigorous-mahavira-ebe993`(분리 HEAD이고 그 커밋이 origin/main에 없다), `skill-check-and-retro-section`(병합된 PR의 머리와 브랜치 끝이 다르다).
- 남긴다: 병합된 PR이 없는 일곱(`bug-perf-review-batch`, `hook-choice-facts`, `mcp-shutdown-spec`, `mutate-ctrl-c-under-load`, `pre-commit-batch`, `wait-ci-review-limit`, `web-widget-spec`), 제목 세션이 도는 `full-checks-via-runner`, 쥔 프로세스가 있는 `next-session-handoff-batch`(claude.exe 둘)와 `ruff-try-statements`(tail.exe).

## 한 것(커밋하지 않았다)

- `tools/hook_measure_word.py`: PostToolUse Write·Edit 계기 훅. 세 자리(`docs/adr/` 아래, `.scratch/` 아래의 `probes/README.md`, `.scratch/retro-queue.md`)에 더한 줄 가운데 `쟀다`·`재니`·`실측`을 들고 같은 줄에 `probes/`도 `손으로`도 없는 줄을 골라, `docs/agents/issue-tracker.md`의 "프로브와 근거" 절을 알리고 걸린 줄을 셋까지 160자로 잘라 싣는다. 더한 줄은 Edit면 `new_string`에서 `old_string`에 없던 줄, Write면 `content`에서 결과의 `originalFile`(문자열일 때)에 없던 줄이다.
- 결정: 형제 훅(`hook_scratch_probe_rule`)과 달리 세션마다 한 번의 표지를 두지 않고 걸릴 때마다 알린다. 알림이 걸린 줄을 보여 주기 때문이다. 근거 표지는 행의 "어디로" 칸대로 같은 줄만 본다. 줄을 바꿔 적은 근거(ADR의 감긴 문단)에도 알리는 것은 못 보는 것에 적었다. 저장소의 세 자리에서 낱말을 들고 같은 줄에 표지가 없는 줄은 이미 80줄 있다(ADR 53, 대기열 10, 프로브 README 17. 이어받은 세션이 훅의 `is_evidence_doc`·`flagged_lines`를 부르는 커밋하지 않은 스크래치 스크립트로 손으로 셌다. 처음 적은 63줄은 셀프 리뷰 두 축이 다시 세어 틀린 것을 잡았다). 더한 줄만 보므로 옛 줄은 고쳐 쓸 때만 다시 걸린다.
- 시험 `tests/tools/test_hook_measure_word.py`(17건), 등록(`.claude/settings.json`의 첫 `Write|Edit` 묶음), 페이로드 표 두 사례(발동은 대기열 227의 꼴, 침묵은 ADR 0014의 실제 줄), 변이 표 `.scratch/harness/probes/measure_word_hook_mutations.toml`과 그 README 행, `docs/agents/issue-tracker.md` 근거 항목과 `.claude/rules/tools.md` 시간 항목의 훅 언급, 대기열 227 닫음.

## 검사

- 시험을 먼저 썼지만, 첫 pytest가 새 워크트리의 환경 설치로 늦게 시작해 훅 파일이 생긴 뒤에 돌았다. 그래서 모듈이 없는 빨강은 보지 못했고, 등록 시험 하나만 빨강(등록 전)이었다.
- `tests/tools/test_hook_measure_word.py` 17 passed. `tests/tools/test_run_hooks.py`를 함께 돌린 회차(549초, 이 PC에 다른 세션이 여럿 돌던 때)에서 `test_사용량_저장소의_요약은_시작한_세션에_한_번_보이고_이어_하기는_침묵이다` 하나가 장부 줄 둘(기대 셋)로 실패했고, 그 시험만 홀로 다시 돌리니 초록이었다(33초). 이 변경이 닿지 않는 훅의 시험이라 부하 아래의 흔들림으로 본다. 원인은 재지 않았다.
- `tools/run_hooks.py`: 훅 페이로드 129건, 어긋남 0건(이 훅의 두 사례 ok).
- 변이: 첫 회차는 열하나 가운데 둘(`retro-queue.md`의 부모, 프로브 README의 `.scratch` 조상)이 초록이라 반례 둘(`docs/retro-queue.md`, `web/probes/README.md`)을 시험에 더했고, 다시 돈 회차는 열하나 모두 기대대로였다.
- ruff check·format, pyright(두 파일), `check_type_escapes`, `check_instructions` 초록. 전체 pytest·lint-imports·web verify는 아직 돌지 않았다(커밋의 pre-commit이 갈음한다).
- `sibling_overlap`: 번호 겹침 없음. 카나리아 알림: `.claude/rules/tools.md`를 바꿨으니 그 파일을 원천으로 든 카나리아 명세를 돌리거나 고친다(아직 하지 않았다). 형제 `hook-choice-facts`가 같은 파일 다섯(`.claude/rules/tools.md`, `.claude/settings.json`, 프로브 README, 대기열, 페이로드 표)을 고쳐 병합 순서에 따라 글자 충돌 후보다.

## 인계

셀프 리뷰 직전 경계에서 인계 계기(컨텍스트 204,806 토큰)가 왔다. 다섯 예외에 들지 않아(요청 범위는 PR과 병합까지, 이어받을 상태는 없음, `인계 못함` 줄 없음, `get_session`의 `self`에 `parentSessionId` 없음) 넘긴다. `/code-review`는 새 세션이 한다.

### 지시문

```
다음 작업: 기능 harness. 대기열 227(측정 낱말을 쓴 줄에 프로브와 근거 절을 알리는 계기 훅)을 반영한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 227(docs/adr/, probes/README.md, retro-queue.md에 더한 줄이 측정 낱말을 들면서 probes/ 경로도 "손으로"도 없으면 근거 절을 알리는 PostToolUse 계기 훅)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/measure-word-hook
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-06-measure-word-hook.md(이 세션이 한 것, 검사, 남은 일)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main, 명세는 대기열 227 행의 "어디로" 칸)부터 한다. 그 뒤 카나리아 알림(.claude/rules/tools.md를 원천으로 든 명세)을 처리하고 커밋·PR·병합까지 간다. 일지 docs/journal/2026-10-19-06-measure-word-hook.md
확인할 선행 조건: 형제 hook-choice-facts가 같은 파일 다섯(.claude/rules/tools.md, .claude/settings.json, 프로브 README, 대기열, 페이로드 표)을 고쳐 먼저 병합되면 글자 충돌이 난다. 커밋 전 sibling_overlap을 다시 친다
이번 요청 범위: PR과 병합까지
```

인계 직전 제목: `chore/measure-word-hook`.

open-session을 부른다 2026-10-18T23:48:56Z

## 이어받은 세션

> 사용자: 대기열 227(docs/adr/, probes/README.md, retro-queue.md에 더한 줄이 측정 낱말을 들면서 probes/ 경로도 "손으로"도 없으면 근거 절을 알리는 PostToolUse 계기 훅)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
>
> (위 지시문과 같은 칸들. 이번 요청 범위: PR과 병합까지)

- `EnterWorktree(path)`로 이 워크트리에 들어왔다.
- 카나리아: 형제 훅의 `tools_rule_scratch_probe_hook.toml`을 본떠 `.scratch/harness/probes/canary/tools_rule_measure_word_hook.toml`을 지었다(다섯째 훅의 괄호 설명을 묻는다). `--preflight` 통과 1. 실제 회차는 셀프 리뷰 반영 뒤에 돌린다.
- 셀프 리뷰: 기점 `ebd09fbb`, 파일 10개(수정 6, 미추적 4), 커밋 0. 표준 축은 Major 2·Minor 4·Nit 4, 명세 축은 Major 1·Minor 5·Nit 2를 냈다. 가장 무거운 것은 두 축이 같은 자리를 짚었다. Edit 조각이 줄의 일부이면 같은 줄의 나머지에 든 `probes/`를 보지 못해 잘못 알리고, 알림 문구를 그대로 따르면 맞게 쓴 근거(감긴 문단, 프로브 README 행)와 지난 기록(취소선)을 고치게 된다.

### 고친 것

- Edit도 결과의 `originalFile`에 `old_string`→`new_string` 교체(`replace_all`이면 모두)를 적용해 쓴 뒤 파일을 다시 만들고 줄 전체로 판정한다. `originalFile`이 문자열이 아니거나 조각이 그 안에 없으면 조각 둘을 본다. 근거는 프로브 README `journal_number_hook/` 행의 2026-10-16 결과(Edit 결과의 키에 `originalFile`·`replaceAll`이 있다). `_texts`를 `_before_after`로 바꿨다.
- 알림 문구: "절대로"를 "절이 정한 대로"로 고치고, 무시할 경우를 셋(낱말을 이름으로만 든 것, 옛 줄의 다른 자리만 고친 것, 근거가 같은 줄 밖에 있는 것)으로 넓혔다.
- 독스트링의 판정 문단과 못 보는 것(옛 줄 고쳐 쓰기, 같은 줄 밖의 근거와 프로브 README 행, `손으로` 부정문, 정규화하지 않는 경로와 아무 깊이의 `docs/adr`, 알림이 모델에게 닿는지 재지 않았다)을 고치고, 시험으로 고정할 수 있는 항목마다 시험을 더했다(17건에서 23건).
- 시험 이름 하나를 단언에 맞게 바꾸고 `originalFile: None` 사례를 더했다. 시험과 페이로드 표의 ADR 0035 경로를 실제 파일 이름으로 고치고, 페이로드 표의 발동 사례에 `originalFile`을 실었다.
- 변이 표: 자르기 변이를 수와 글자로 나누고 Edit의 `originalFile`·`replace_all` 변이를 더했으며, 대조군을 바뀐 문구로 옮겼다(열넷).
- 일지의 63줄을 80줄로 고쳤다. 대기열 227 닫힘 표지에 일지와 tools.md·카나리아를 더했다. issue-tracker 근거 항목의 훅 괄호를 새 무시 조건에 맞췄다.

PR 직전 리뷰에 밀 새 문장(원문):
- 훅 독스트링: "Edit 의 조각은 줄의 일부일 수 있어, 조각만 보면 같은 줄의 나머지에 든 `probes/` 를 보지 못한다", "`originalFile` 이 없는 Edit 은 조각만 보므로 거꾸로 낱말이 조각 밖에 있으면 지나간다", "거꾸로 `docs/adr` 토막은 어느 깊이에 있든, 확장자가 무엇이든 받는다", "알림이 실제 세션의 모델에게 닿는지. 아직 재지 않았다"
- 알림: "다음 셋이면 고치지 않고 이 알림은 무시한다. 낱말을 이름으로 든 것뿐이다. 이미 있던 줄의 다른 자리만 고쳤다(취소선, 닫힘 표지). 근거 프로브가 같은 줄 밖(감긴 문단의 앞뒤 줄, 프로브 README 행의 첫 칸)에 있다."
- issue-tracker: "근거가 같은 줄 밖에 있는 문장, 낱말을 이름으로만 든 줄, 옛 줄의 다른 자리만 고친 것에도 알리고, 알림이 그 셋이면 무시하라고 적는다"
- 이 일지의 80줄 문장과 프로브 README 행의 "열넷 모두 기대대로"

### 남긴 것

- 알림이 실제 세션의 모델에게 닿는지는 재지 않았다(형제 `hook_scratch_probe_rule`과 같다). 독스트링의 못 보는 것에 적었다. `claude -p` 회차가 드는 확인이라 이 PR에서는 하지 않는다.

### 다시 돌린 명령

- `tests/tools/test_hook_measure_word.py` 23 passed. 변이 열넷 모두 기대대로. ruff check·format, pyright(두 파일) 초록. `tools/run_hooks.py` 훅 페이로드 129건, 어긋남 0건. 나머지는 커밋의 pre-commit이 갈음한다.

### 카나리아

- `tools_rule_measure_word_hook.toml` 첫 판(규칙 파일의 첫 제목과 다섯째 훅의 괄호 설명을 한 물음에 묶었다)은 실험군 세 번이 모두 "없음"이라 실패였고 대조군은 "없음"이었다. operations.md의 "없음" 항목대로 통과한 `tools_rule_edit_during_commit.toml`처럼 번호 둘로 나눠 자리를 짚게 고치고, 카나리아를 괄호 설명과 "둘 다 시간은 재지 않았고"로 바꿨다. 다시 돈 회차는 통과 4, "없음" 섞임 0이었다(셀프 리뷰를 반영한 작업 트리, 러너가 찍은 커밋 ebd09fbb).
- 형제 `tools_rule_scratch_probe_hook.toml`도 첫 판과 같은 꼴의 물음이고 실제 회차를 돈 적이 없다(사전 확인만). 같은 까닭으로 "없음"일 수 있다. 이 PR의 범위 밖이라 돌리지 않았다.

### 커밋

- `ae50a9ee`. 직전에 `git branch --show-current`가 `chore/measure-word-hook`, `sibling_overlap`이 번호 겹침 없음(origin/main은 ebd09fbb 그대로. 글자 충돌 후보에 `bug-perf-review-batch`의 `.claude/settings.json`·`tools/hook_payloads.toml`이 새로 들었다). pre-commit은 ruff 둘, check-instructions, lint-imports, check-type-escapes, zizmor, pyright, run-hooks, pytest(506초), web-verify, 표·줄 구분 문자·변이 표·인용·커밋 메시지 검사가 모두 Passed였고 Skipped는 없었다.

## 인계 2

커밋 뒤 경계에서 인계 계기(컨텍스트 255,297 토큰)가 왔다. 다섯 예외에 들지 않는다. 커밋은 성공했고, 요청 범위는 PR과 병합까지, 넘겨받은 경계는 `셀프 리뷰 직전`이라 다르고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `chore/measure-word-hook`이다. 아직 푸시하지 않았고 PR도 없다.

### 지시문

```
다음 작업: 기능 harness. 대기열 227(측정 낱말을 쓴 줄에 프로브와 근거 절을 알리는 계기 훅)을 반영한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 227(docs/adr/, probes/README.md, retro-queue.md에 더한 줄이 측정 낱말을 들면서 probes/ 경로도 "손으로"도 없으면 근거 절을 알리는 PostToolUse 계기 훅)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/measure-word-hook
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-06-measure-word-hook.md(셀프 리뷰 반영, 카나리아, 커밋, 이 인계)
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영과 카나리아(통과 4)를 실은 커밋 ae50a9ee까지 했고 푸시하지 않았으며 PR이 없다. 남은 단계는 푸시, PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 밀 주장은 일지의 "PR 직전 리뷰에 밀 새 문장"), PR 열기, 봇 회차, 병합이다. 일지 docs/journal/2026-10-19-06-measure-word-hook.md
확인할 선행 조건: 형제 hook-choice-facts(.claude/rules/tools.md, .claude/settings.json, 프로브 README, 대기열, 페이로드 표)와 bug-perf-review-batch(.claude/settings.json, 페이로드 표, 프로브 README, 대기열)가 같은 파일을 고쳐 먼저 병합되면 글자 충돌이 난다. 푸시 전 sibling_overlap을 다시 친다
이번 요청 범위: PR과 병합까지
```

인계 직전 제목: `chore/measure-word-hook`. 잠금 풀기는 `is not locked`(이미 풀려 있었다).

open-session을 부른다 2026-10-19T01:01:13Z

## 이어받은 세션

> 사용자: 대기열 227(docs/adr/, probes/README.md, retro-queue.md에 더한 줄이 측정 낱말을 들면서 probes/ 경로도 "손으로"도 없으면 근거 절을 알리는 PostToolUse 계기 훅)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다

워크트리 `measure-word-hook`에 들어가 이었다. `sibling_overlap`은 번호 겹침 없음, origin/main은 ebd09fbb 그대로였다. 푸시한 뒤 PR 직전 리뷰를 돌렸다(CodeRabbit CLI는 좌석이 없어 대체 둘).

### PR 직전 리뷰

- `/security-review`: 지적 없음. 훅은 subprocess·파일 열기·eval이 없고, 출력은 additionalContext 하나다.
- `bug-perf-review`: 유효 2(Minor), 보류 1. 밀었던 주장(독스트링 셋, 알림의 세 예외, 변이 열넷)은 모두 코드·시험과 맞는다고 대조했다.
  - 유효: 프로브 README 행 앞머리가 변이를 "열"로 적었다. 실제는 빨강 기대 열셋과 대조군 하나다. "열셋"으로 고치고 자르기 변이를 둘로 나눠 적었다.
  - 유효: `test_슬래시_꼴과_대소문자가_다른_경로도_본다`의 `QUEUE.replace("\scratch\\", …)`가 바꿀 글자가 없어 아무것도 시험하지 않았다(`QUEUE`에는 `\.scratch\`가 있다). `\.scratch\`→`\.Scratch\`로 고치고 `docs\ADR` 줄을 더했다.
  - 보류→오탐: CRLF `originalFile`에서 여러 줄 `old_string`이 맞지 않을 수 있다는 지적. `.gitattributes`가 `* text=auto eol=lf`라 작업 트리 문서가 LF이고, 맞지 않아도 알림만 더 날 뿐 막지 않는다.
- 다시 돌린 것: 훅 시험 23 passed, 변이 열넷 모두 기대대로.

### PR #296 봇 첫 회차

PR은 `gh pr create`가 GraphQL 연결 오류(TLS 시간 초과, HTTP 499)로 두 번 실패해 REST(`gh api repos/.../pulls`)로 열었다. 검사 다섯 모두 통과, CodeRabbit `Review completed`.

- CodeRabbit Minor(고침): 페이로드 표의 침묵 사례가 비어 있지 않은 ADR에 빈 `old_string`이라 성공한 Edit 입력이 아니었다. 발동 사례와 같은 꼴(`## 이력\n` 조각과 `originalFile`)로 고쳤다. `tools/run_hooks.py` 129건 어긋남 0건.
- CodeRabbit Minor(보류): 변이 열셋에 `expect_output`이 없다는 지적. `tools/mutate.py` 출력이 변이마다 실패한 시험 하나의 이름을 찍고, 열셋 모두 그 변이가 노린 시험이었다(이 일지의 PR 직전 리뷰 절 회차). 저장소의 변이 표 대부분도 `expect_output` 없이 시험 이름으로 가른다. 표지를 고르려면 변이마다 실패 출력을 손으로 봐야 해 값이 이 PR의 남은 일보다 크다.
- CodeRabbit 보안 구조(오탐): 알림이 문서 줄을 컨텍스트에 옮긴다는 우려. 그 줄은 같은 세션의 모델이 방금 저장소 문서에 쓴 글이고, 세션 밖으로 나가지 않는다.
- claude-review Nit 둘(보류): 경로 토막 분해를 형제 훅과 모으기는 훅이 서로 import하지 않는 규약(`.claude/rules/tools.md` 첫 항목)과 맞지 않는다. 독스트링 "판정" 절과 코드의 중복은 형제 훅과 같은 방식이다.
