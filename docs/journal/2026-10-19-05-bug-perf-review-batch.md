# 2026-10-19 (05) bug-perf-review 정의에 대기열 250·320을 반영하고 214를 재어 ADR로 넘긴다

next-session 지시문으로 연 새 세션이다. 주 체크아웃이 낡아 `tidy-checkouts`를 먼저 돌고 워크트리에 들어갔다.

> 사용자: "대기열 214·250·320(대상 파일이 .claude/agents/bug-perf-review.md인 열린 행 셋)을 chore 한 PR로 반영한다. 각
> 행의 "어디로" 칸이 원천이고 ADR이 필요한 행은 빼고 ADR 초안으로 따로 둔다"

## 정리

주 체크아웃은 깨끗한 main이었고 `655b19a8`에서 `e8d35a75`(그때의 origin/main)로 당겼다. 당긴 커밋은 `tidy-checkouts` 스킬
파일을 바꾸지 않았다. 판정은 지울 워크트리를 내지 않았다. 체크아웃되지 않은 브랜치 `worktree-hook-choice-facts`와
`worktree-wait-ci-review-limit`은 커밋이 모두 origin/main에 있어 지웠다. 사람에게 넘긴 것은 넷이다. 분리 HEAD이고 그 커밋이
origin/main에 없는 `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`·`vigorous-mahavira-ebe993`, 병합된 PR의 머리와 브랜치
끝이 다른 `skill-check-and-retro-section`이다. 지시문대로 답을 기다리지 않았다. 나머지 워크트리는 병합된 PR이 없거나 쥔
프로세스가 있어 남겼다. 워크트리에 들어와 브랜치 이름을 바꾼 뒤 #294가 병합되어 `ebd09fbb`로 빨리 감았다.

## 세 줄 계획

(1) 250: `bug-perf-review`·`coderabbit-review` 정의의 보고 형식에 받은 턴에 일지로 옮기라는 끝 줄을 더한다. 계기 훅과 내장
`/security-review`를 덮는 자리를 먼저 잰다. (2) 320: 가드가 거부하는 모양을 먼저 재고 트리아지 단계에 함수를 부르는 길을
적는다. (3) 214: 셈을 고친 뒤의 기록을 재고, 하네스가 세는 훅으로 가야 하면 그 자리를 정한다. 계약(`sdk/`, `openapi.json`,
헌법)에 닿지 않는다.

## 측정과 결정

### 214: 예산 40을 넘긴 리뷰

세는 법을 들인 PR #206이 병합된 뒤의 기록을 `reviewer_call_count.py --since 2026-10-12T15:47:23 --until 2026-10-18T23:00`으로
쟀다. 측정 90회차 가운데 아홉이 40번을 넘겼다(41~62번). 아홉 모두 행의 계기("표지가 40에 닿은 뒤에도 이어 부르면")가
아니었다. 셋은 마지막 `[호출 n]` 표지가 40인데 실제 누적이 41~42번이었고, 여섯은 마지막 표지가 25~38인데 실제가 41~62번이었다.
나란히 부른 도구를 하나로 센 것으로 보인다(어림). 표지가 40에 닿은 일곱 가운데 넷은 실제로도 40번에서 멈췄다. 처음에는
`--until 2026-10-19T00:00`으로 쟀는데 이 세션의 320 측정 서브에이전트가 섞여 92회가 나와, 창을 줄여 다시 쟀다.

그래서 넘김은 모델이 예산을 무시해서가 아니라 모델이 스스로 센 수가 틀려서 난 것으로 보인다(아홉·셋·여섯의 가름은 프로브
출력을 스크래치 스크립트로 손으로 갈랐고, 까닭은 어림이다). 예산 문단은 이미 "한 응답에서 나란히 부른 도구는 하나씩
더하고"라고 적는다. 셈 지침을 적은 뒤에도 셈이 틀렸으므로
하네스가 세는 PreToolUse 훅이 맞는 층이다(`.claude/rules/tools.md`). 그런데 그 훅을 어디에 등록할지가 구조 결정이다. 모든
세션의 `settings.json`에 두면 서브에이전트가 아닌 도구 호출마다 훅 프로세스가 하나씩 더 뜨고, 그 서브에이전트 정의의
frontmatter `hooks`에 두면 `tools/run_hooks.py`의 등록 대조(지금은 `settings.json`만 본다)와 등록 규약이 새로 든다. 그래서
지시문대로 이 행은 이 PR에서 빼고 ADR 초안으로 따로 둔다. 정의의 예산 문단은 바꾸지 않았다.

### 250: 보고를 받는 순간에 일지로 옮기기

계기 훅을 먼저 쟀다. 탐침 `.scratch/harness/probes/agent_report_hook/run.py`가 본 세션의 Agent 호출에 PostToolUse 훅을 붙였다.
세 회차 모두 측정이었고, 실험군 둘 다 훅이 낸 표지가 모델의 답에 들었다. 그러나 하나는 `isAsync=True status=async_launched`라
훅이 서브에이전트를 띄울 때 돌았고 보고는 따로 왔다. 다른 하나는 `status=completed`라 보고를 받을 때 돌았다. 백그라운드로
띄울지는 모델과 하네스가 정하므로 그 훅으로는 보고를 받는 순간을 늘 잡지는 못한다. 셀프 리뷰가 짚은 대로 Agent 도구
결과의 성공을 표지로 더해 다시 돌린 판에서는 실험군 둘 다 `completed`였다(아래 셀프 리뷰 절). 백그라운드 회차가 늘
나지는 않는다는 뜻이고, 앞 판에서 난 회차가 없어지지는 않는다.

그래서 보고 자체의 끝 줄로 정했다. 보고를 받는 턴에 본 세션이 반드시 읽는 글은 그 보고다. 두 정의의 보고 형식 절 끝에
`받는 본 세션에게: …` 한 줄을 글자 그대로 적게 했다. 내장 `/security-review`는 고칠 수 없고 보고를 본 세션이 스스로 써서
받는 도구 호출이 없다. 그 명령을 돌리기 직전에 본 세션이 읽는 글은 `coderabbit-review`가 CLI를 돌리지 못했을 때 보고 끝에
붙이는 대체 둘 줄이라, 그 줄에 두 보고도 받은 턴에 옮긴다는 문장을 더했다. 셀프 리뷰 명세 축이 그 줄은 흔한 길에서
읽히지 않는다고 짚어, `/security-review`는 그 명령을 부르는 Skill 호출의 계기 훅으로 덮었다(아래 셀프 리뷰 절).

### 320: 가드에 막힌 함수 부르기

이 워크트리에서 띄운 `bug-perf-review` 서브에이전트에게 명령 다섯을 글자 그대로 치게 했다. 저장소 루트의 `uv run python -c`,
스크래치 시험 파일의 `uv run python -m pytest`, 스크래치 스크립트 실행, heredoc 쓰기가 모두 거부되지 않고 돌았다. 맨
`uv run pytest <저장소 밖 파일>`도 거부되지 않았지만 `ModuleNotFoundError: No module named 'tools'`로 수집에서 멈췄다. 저장소
루트가 import 경로에 없어서다. 이 다섯은 git 명령 글이 들지 않은 명령이었다. 2026-10-16에 거부된 것은 git 글이 든
명령이었다는 것을 셀프 리뷰 명세 축이 짚어, 아래 셀프 리뷰 절에서 다시 쟀다.

그래서 거부되는 모양을 피하는 대신 길의 차례를 적었다. 트리아지 단계에 `uv run python -c`, 그다음 heredoc으로 저장소 밖
`/tmp/bug-perf-review/`에 쓴 시험 파일을 `uv run python -m pytest`로 돌리는 길을 두고, 앞 길이 거부되면 한 번만 바꾸며, 둘 다
거부되면 그 지적의 근거에 적고 `보류`로 둔다. 2단계 밀 주장의 "코드의 동작" 항목도 이 길을 가리키게 했다.

## 고친 것

- `.claude/agents/bug-perf-review.md`: 머리 문단의 Bash 쓰임, 2단계 밀 주장의 코드 동작 항목, 3단계 트리아지의 함수를 부르는
  길과 실패·거부 갈래, 보고 형식 절 끝의 `받는 본 세션에게` 줄과 그 까닭(250·320).
- `.claude/agents/coderabbit-review.md`: 대체 둘 줄의 일지 문장과 그 줄이 맡는 몫, "이슈 없음" 문장, findings를 낸 보고의
  끝 줄(250).
- 새 계기 훅 `tools/hook_security_review_journal.py`와 시험 `tests/tools/test_hook_security_review_journal.py`,
  `.claude/settings.json`의 PreToolUse Skill 매처 등록, `tools/hook_payloads.toml`의 발동 둘·비발동 하나,
  `.claude/rules/tools.md` 훅 시간 항목의 Skill 문장 둘(250).
- 탐침 `.scratch/harness/probes/agent_report_hook/`(`run.py`, `hook.py`)와 `security_review_hook/run.py`, 프로브 README의
  두 행. README의 `reviewer_call_count.py` 행 끝에 2026-10-19 결과(214).
- 카나리아 `bug_perf_review_report_line_and_call_paths.toml`, `coderabbit_review_journal_line.toml`,
  `tools_rule_security_review_hook.toml`.
- 대기열 250·320을 닫고 214의 승인 칸에 측정과 ADR로 넘긴 것을 적었다.

## 카나리아와 선행 조건

지시문은 행 287을 맡은 `chore/pre-commit-batch` 세션이 `tools/canary.py`를 고칠 수 있으니 카나리아 전에 그 PR이 병합됐는지
보라고 했다. 그 브랜치에는 PR이 없었다(`gh pr list --head chore/pre-commit-batch`가 비었다). 기다리지 않고 지금 러너로 돌렸다.

두 카나리아 모두 통과 4였다(실험군 3, 대조군 1, 대조군은 주 체크아웃 `ebd09fbb`). 대조군은 두 물음 모두 "없음"이라 갈렸다.
`bug-perf-review` 실험군 셋째 회차는 서브에이전트가 `async_launched`로 떴고, 답의 `<파일>`이 `&lt;파일&gt;`로 옮겨졌다.
기대 문장은 그 앞에서 끝나 판정은 그대로다.

셀프 리뷰를 반영한 뒤 셋을 다시 돌렸다. 두 정의의 카나리아는 다시 통과 4였다. `bug-perf-review` 실험군 셋은 모두
`completed`였고, 둘째 물음의 답은 브랜치 폴더가 든 `uv run python -m pytest -q -p no:cacheprovider
/tmp/bug-perf-review/<브랜치>/<파일>`이었다. 새로 지은 `tools_rule_security_review_hook.toml`(`.claude/rules/tools.md`에
더한 Skill 문장)은 통과 4였다. 실험군 셋이 `# 하네스 규칙`과 계기의 구절을 옮겼고 대조군은 "없음"만 답했다. 실험군 둘에
붙은 `"없음" 섞임` 표시는 답이 옮긴 규칙 문장의 `(매처 없음)` 때문이다.

## 셀프 리뷰

base `ebd09fbb`, 바뀐 파일 4개, 커밋 0개, 미추적 5개(탐침 둘, 카나리아 둘, 이 일지).

표준 축: Major 둘, Minor 열, Nit 셋. 주장 검증에서 맨 `uv run pytest`가 `No module named 'tools'`로 멈추고
`uv run python -m pytest`가 통과하는 것, 214의 수, 일지의 정리 사실은 다시 대 보고 맞다고 했다.
- Major: 3단계 둘째 길이 거부가 아니라 실패(시험의 오타, 수집 오류)로 끝나는 갈래가 없다. `agent_report_hook/run.py`의
  대조군은 Agent 도구 결과가 성공했는지 보지 않아, 호출이 거부돼도 `NONE`이 측정으로 센다.
- Minor: "`code-review` 6단계 끝에만 있어"의 반례(`next-session` 1단계 4), "그 순간을 잡지 못한다"의 과한 일반화,
  `coderabbit-review` 대체 둘 줄의 덜 끝난 문장과 `/security-review` 근거 종류, 같은 파일의 "이슈 없음" 문장과 새 끝 줄의
  충돌, 둘째 길의 heredoc 40줄 한도·지우는 함수·고정 폴더 공유, 214 칸의 "정의를 바꾸지 않았다", 일지의 단정과 대기열의
  손으로 가른 셈, README의 "표지 35개 응답", 턴 한도에 잘린 보고.
- Nit: 두 정의의 같은 끝 줄, `run.py`의 함수 이름과 CQS, "손으로 봤다"의 근거 종류.

명세 축: Major 둘, Minor 넷, Nit 셋. 214의 수와 탐침의 훅 기록은 다시 대 보고 맞다고 했다. 범위 넘침은 없다.
- Major: 250의 `/security-review`를 덮는 자리를 재지 않았고, 고른 자리(`coderabbit-review`의 대체 둘 줄)는 흔한 길에서
  읽히지 않는다. 본 세션이 `coderabbit auth status`를 직접 쳐 좌석이 없으면 곧바로 대체 둘로 간다. 2026-10-12 뒤
  `bug-perf-review`를 띄운 세션 114개 가운데 `coderabbit-review`도 띄운 세션은 1개였다(그 축이 트랜스크립트를 셌다).
  320의 거부 모양을 재지 않았고 "같은 모양이 지나갔다"는 거짓이다. 2026-10-16에 거부된 것은 코드나 heredoc 본문에
  git 명령 글이 든 명령이었다.
- Minor: 같은 "6단계 끝에만" 반례, 214에서 "ADR 불필요"였던 행을 다시 판정한 근거를 사용자에게 보일 것, 예산 40과
  3단계 함수 부르기의 충돌, 고정 폴더 공유.
- Nit: 한 번만 바꾸는 단위, 대기열·일지의 인용 "이어 부르기", 카나리아 결과 줄에 러너 판.

판정. 근거를 열어 본 것:
- 명세 Major 250: 유효. PR 템플릿 56행이 좌석을 `coderabbit auth status` 한 줄로 보라고 하고, 대체 둘을 부르라는
  문장은 그 줄과 `operations.md` 리뷰 파이프라인 2에만 있다. 지난 세션 기록 142개가 `/security-review`를 Skill
  도구(`"skill":"security-review"`)로 불렀다(grep으로 셌다). 그래서 Skill 매처 계기 훅으로 덮는다. 선례는
  `hook_grill_design_check`다.
- 명세 Major 320: 유효. 2026-10-16 서브에이전트 기록(`agent-aad475db1cfeb1000`)에서 거부 넷을 봤다. `-c` 둘은 코드에
  `git commit -m …`이 들어 "cannot be shown not to be git"이었고, heredoc 둘은 같은 글이 든 본문이라 "too complex"였다.
  git 글이 든 갈래와 들지 않은 갈래를 나눠 다시 잰다. 이 일지 절을 Bash heredoc으로 붙이려던 명령도 "too complex"로
  거부됐다(본문에 git 명령 글이 들었다).
- 표준 Major 둘: 유효. 둘째 길의 실패 갈래를 적고, 탐침 대조군에 Agent 도구 결과의 성공을 표지로 더해 다시 돌린다.
- 214의 ADR 판정: 유지한다. 예산 문단은 이미 "한 응답에서 나란히 부른 도구는 하나씩 더하고"라고 적는다. 셈이 그
  지침을 적은 뒤에도 틀렸으므로 문단을 더 고치는 것이 아니라 하네스가 세는 훅이고, 그 등록 자리가 구조 결정이다.
  근거는 사용자에게 하는 보고에서 보인다.
- README의 "표지 35개 응답": 표지를 단 응답이 35개라는 뜻이라 수는 맞다(`호출 62 응답 36 표지 35`). 읽는 이가
  응답 수로 읽었으니 "응답 36개 가운데 35개에 표지"로 풀어 쓴다.

고친 것:
- 명세 Major 250: `/security-review`를 부르는 Skill 호출에 PreToolUse 계기 훅 `hook_security_review_journal`을 걸고, 새 훅의
  넷(등록, 시험, 페이로드, 러너 확인)을 함께 했다. `coderabbit-review`의 대체 둘 줄은 그 정의를 거치는 길의 몫으로 줄이고,
  흔한 길은 `bug-perf-review` 보고의 끝 줄과 이 훅이 맡는다고 적었다.
- 명세 Major 320: git 글이 든 명령으로 다시 쟀다(아래 다시 돌린 것). 거부되는 꼴을 고를 수 없어, 정의의 가드 문장을 어느
  명령이 거부될지 미리 알 수 없다는 것과 두 날의 관찰로 바꿨다.
- 표준 Major 둘: 3단계에 거부가 아닌 실패의 갈래(길을 바꾸지 않고, 시험 쪽 실패는 한 번 고쳐 다시 치고, 그래도 실패하면
  `보류`)를 적었다. 탐침 `agent_report_hook/run.py`에 본 세션의 Agent 호출과 짝이 맞는 오류 없는 도구 결과를 표지로 더했다.
- 표준 Minor: "`code-review` 6단계 끝에만" → "6단계 끝과 PR을 연 뒤에 실리는 `next-session` 1단계 4에", "그 순간을 잡지
  못한다" → "늘 잡지는 못한다", 대체 둘 줄을 끝맺은 문장으로, "이슈 없음" 문장에 끝 줄을 붙였고, heredoc 40줄 한도와 지우는
  함수는 시험 폴더 안의 입력으로만 부른다는 것과 시험 폴더를 브랜치마다 가르는 것을 적었다. 214 칸은 "정의의 예산 문단을
  바꾸지 않았다"로, 일지의 까닭은 어림으로, README는 "응답 36개 가운데 35개"로, 근거 괄호는 무엇을 손으로 봤는지로 고쳤다.
- 명세 Minor: 예산 40에 닿은 뒤에는 함수를 새로 부르지 않는다고 3단계에 적었다. "6단계 끝에만"과 고정 폴더 공유는 위와 같다.
- Nit: 한 번만 바꾸는 단위를 "그 지적에서"로, 대기열·일지의 인용을 행의 원문 "표지가 40에 닿은 뒤에도 이어 부르면"으로,
  카나리아 결과 줄에 러너 판(`ebd09fb`의 `tools/canary.py`)을 적었다.

남긴 것과 이유:
- 표준 Minor 턴 한도에 잘린 보고: `maxTurns`에 닿아 보고 없이 끝나면 끝 줄도 없다. 정의 문장으로 다룰 수 없는 자리이고,
  호출 수를 하네스가 세는 214의 훅이 그 앞에서 멈추게 하는 자리다.
- 표준 Nit 두 정의의 같은 끝 줄: 서브에이전트는 자기 정의만 실어 둘이 함께 읽을 자리가 없다.
- 표준 Nit `run.py`의 함수 이름과 CQS: 커밋한 스크래치 탐침이라 게이트 밖이고 측정에 영향이 없다.
- 명세 Minor 214의 ADR 판정: 위 판정대로 유지하고, 근거는 사용자에게 하는 보고에서 보인다.

다시 돌린 것:
- 가드: 이 워크트리에서 띄운 `bug-perf-review`에게 git 글이 없는 다섯에 git 글이 든 짧은 `-c`와 heredoc 시험 파일을 더해
  일곱 명령을 치게 했다. 일곱 모두 지나갔다. 본 세션에서는 git 글이 든 짧은 `-c` 둘이 지나갔고, 10-16에 거부된 `-c`
  하나(`h.boundary_of('Bash', {'command': 'git commit -m -h'})`를 찍는 명령)는 글자 그대로 쳐도 거부됐다. 이 절을 쓰는 중에
  이 세션 기록을 추리려던 긴 `-c`(코드에 거부 문구를 찾는 문자열이 들어 `git` 낱말이 있었다)도 거부되어 스크래치 파일로
  돌렸다.
- `agent_report_hook/run.py`(표지 넷): 실험군 둘 다 `status=completed`이고 훅의 표지가 답에 들었다. 대조군은 `NONE`, 측정
  아님 0건이다.
- `security_review_hook/run.py`: 훅 두 회차는 훅의 첫 문장을 답에 옮겼고 훅 없는 회차는 `NONE`이었다. 측정 아님 0건, 종료
  0이다.
- `uv run pytest -q tests/tools/test_hook_security_review_journal.py tests/tools/test_hook_grill_design_check.py`: 20 passed.
- `uv run python tools/run_hooks.py`: 훅 페이로드 130건 어긋남 0건, 래퍼 알림 5건 어긋남 0건, 표의 빈자리 0건.
- 카나리아 셋: 위 카나리아 절.

PR 직전 리뷰에 밀 주장(셀프 리뷰를 반영하며 새로 쓴 사실 문장):
1. `bug-perf-review.md` 3단계: "2026-10-16에 이 리뷰가 거부당한 넷은 모두 코드나 heredoc 본문에 git 명령 글(`git commit -m
   …`)이 든 명령이었다." "2026-10-19에는 git 글이 든 짧은 `-c`와 heredoc 시험 파일이 이 리뷰에서 지나갔고, 10-16에 거부된
   짧은 `-c` 하나는 본 세션에서 다시 쳐도 거부됐다."
2. 같은 단계: "맨 `uv run pytest <파일>`은 저장소 루트를 import 경로에 넣지 않아 `ModuleNotFoundError: No module named
   'tools'`로 수집에서 멈춘다." "heredoc 본문은 40줄을 넘기지 않는다(`tools/hook_bash_heredoc.py`가 막는다)."
3. 같은 정의 보고 형식: "`code-review` 6단계 끝과 PR을 연 뒤에 실리는 `next-session` 1단계 4에 있어", "2026-10-19 도구
   결과의 표지를 더하기 전 판의 실험군 두 회차 가운데 하나였고, 더한 판의 실행에서는 두 회차 모두 보고를 받을 때 돌았다."
4. `coderabbit-review.md`: "본 세션이 `coderabbit auth status`로 좌석이 없는 것을 먼저 보고 이 정의를 부르지 않는 흔한 길".
5. `tools/hook_security_review_journal.py` 독스트링: "그 호출의 입력은 `{"skill": "security-review"}`가 146번, `args`가 붙은
   것이 한 번이었고 접두가 붙은 이름은 없었다", "그 문장은 셀프 리뷰 때 실리는 스킬과 PR 뒤에 실리는 `next-session` 1단계
   4에 있어".
6. `.claude/rules/tools.md`: "Skill에는 PreToolUse `hook_grill_design_check`·`hook_security_review_journal`·
   `hook_midturn_korean`(매처 없음)과 함께 훅이 넷 붙는다."
7. 대기열 214 승인 칸과 이 일지 214 절: "측정 90회차 가운데 아홉이 40번을 넘겼다(41~62번)." "셋은 마지막 `[호출 n]` 표지가
   40인데 실제 누적이 41~42번이었고, 여섯은 마지막 표지가 25~38인데 실제가 41~62번이었다."
