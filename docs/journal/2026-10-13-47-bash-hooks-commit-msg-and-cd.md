# 2026-10-13 (47) Bash 훅 둘: 커밋 메시지 제목을 먼저 대 보고, 하위 폴더 cd 를 알린다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 222·225를 한 PR로 닫는다. 둘 다 `tools/`의 Bash PreToolUse 훅이다.
세션은 주 체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈 뒤
`EnterWorktree(name=bash-hooks-commit-msg-and-cd)`로 들어가 `origin/main`(`d280aa6`)에서
`chore/bash-hooks-commit-msg-and-cd`를 땄다. 일지 번호는 `tools/sibling_overlap.py`가 준 37이었고, 병합 직전에 main이 두 번 움직여 43, 47로 옮겼다.

> 사용자: "대기열 222·225를 한 PR로 반영한다(tools/의 Bash PreToolUse 훅: 커밋 메시지 파일의 제목을 commit-msg 판정으로 먼저 대 보기, 체크아웃 안 하위 폴더로 옮기는 cd도 알리기). 두 행의 "어디로" 칸이 원천이다"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `72656b2`에서 `d280aa6`(#222)으로 당겼다. 당긴 커밋은 이 스킬 파일을 바꾸지 않았다.
- **지운 것.** 없다. `지운다` 판정은 등록 없는 폴더 `mutate-any-runner` 하나였는데, 지우기 직전의 재판정에서 그 아래 모듈을 올린
  `python.exe`(pid 18592)가 있어 종료 1로 남았다.
- **남긴 것.** 잠금 pid가 살아 있는 것, 모듈을 올린 `python.exe` 둘(pid 17324·48584) 때문에 남은 병합된 워크트리, 작업 디렉터리를
  쥔 `claude.exe`가 있는 것, 병합된 PR이 없는 것, 다시 만들 수 없는 무시된 항목이 있는 것, 실행 중 세션의 브랜치 하나.
- **사람에게 넘긴 것.** prunable 둘, 옆 이름에 남은 `spec-pipeline-and-pytest-ids.tidy-probe`, 분리 HEAD 둘, PR 머리가 다른
  `skill-check-and-retro-section`. 지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **225: 막는 판정을 그대로 두고 알림을 그 뒤에 붙였다.** `hook_bash_cd_outside`의 판정은 `cd`마다 풀린 자리를 차례로 따라간다.
  그 자리 목록(`Destination`)을 한 번 만들어, 하나라도 체크아웃 밖이면 막고(옛 판정), 막을 것이 없고 하나라도 체크아웃 루트가
  아니면 알린다(`decision`). 마지막 자리만 보지 않는 까닭은 막는 판정과 같다. `&&` 중간이 실패하면 돌아오는 `cd ..`가 돌지 않는다.
  그래서 `;`로 이어 늘 돌아오는 것도 알린다(거짓 양성, 문장 하나).
- **222: "알린다"가 아니라 막는다.** 대기열 행은 "알린다"였다. PreToolUse의 additionalContext는 도구 결과 옆에 들어가고 Claude는
  다음 모델 요청에서 읽는다(공식 hooks 문서 `https://code.claude.com/docs/en/hooks.md`를 2026-10-13에 `curl`로 내려받아 "next to the
  tool result"와 "Claude reads the reminder on the next model request"를 글자 그대로 대 봤다). 커밋이 게이트를 다 돈 뒤에야 모델이
  알림을 보니 행의 "무엇"(게이트를 두 번 도는 것)을 줄이지 못한다. 명세 축 셀프 리뷰도 이 결정을 타당하다고 봤다.
- **222: 판정을 옮겨 적지 않았다.** 훅끼리 import하지 않는 규약(`.claude/rules/tools.md`)을 지키면서 같은 판정이 정의로 서도록,
  커밋하는 저장소의 `tools/check_commit_msg.py`를 자식 프로세스로 띄운다. 첫 판은 훅 옆의 스크립트를 썼는데, 셀프 리뷰가 commit-msg
  판정이 없는 저장소(`git -C <다른 저장소>`)에서도 막는다고 짚어 커밋 폴더의 가장 가까운 `.git` 조상에서 찾게 바꿨다. 그 루트의
  `.pre-commit-config.yaml`이 그 스크립트를 부를 때만 판정한다. 워크트리 세션에서는 훅 파일이 주 체크아웃의 것이어도 판정은 그
  워크트리의 스크립트가 한다.

## 셀프 리뷰

`/code-review`(기점 `d280aa6`, 커밋 없음, 수정 아홉과 미추적 다섯)를 두 축으로 돌렸다.

- **표준 축(Major급).** 첫 판의 독스트링은 막는 자리를 앞당길 뿐 새로 막는 것은 없다고 했는데, 리뷰어가 임시 저장소에서 git과
  훅을 직접 돌려 반례 다섯을 냈다. `-F bad -F good`(git은 마지막 `-F`를 쓴다), `--squash=HEAD -F bad`(제목이 `squash! `로 시작해
  commit-msg가 통과시킨다), 같은 명령에서 먼저 쓰는 파일(옛 내용으로 막는다), `-e -F`, commit-msg 훅이 없는 저장소다. 명세 축은
  `SKIP=commit-msg`와 다른 저장소, 브랜치에서 바꾼 판정 스크립트를 더 냈다. 막는 훅의 거짓 양성은 비용이 커서 모두 판정에서 뺐다.
  마지막 `-F`만 보고, `--no-verify`·`-n`·`SKIP=…commit-msg…`·`-e`·`--edit`·`--squash`·`--fixup`·`--cleanup`이 있거나, 파일 인자가 같은
  명령의 다른 단순 명령에도 나오거나, 커밋 앞에 `cd`·`pushd`가 있으면 보지 않는다.
- **표준 축.** 독스트링의 따옴표 인용 "지침 뒤에도 어겨진 뒤에만 막는다"가 `.claude/rules/tools.md` 원문과 달랐다. 인용을 없애고
  원문의 뜻으로 풀었다. "못 보는 것" 항목마다 테스트 하나로 고정하라는 규약을 지키지 않은 항목 다섯(앞의 `cd`, 다른 이름의 `git`,
  `--cleanup`, 시간 초과·판정 문장 없음, heredoc 본문의 작은따옴표)에 테스트를 더하고, 그사이 판정에서 뺀 것은 "보지 않는 커밋"으로
  옮겨 그 입력도 고정했다.
- **두 축(Major).** 시간 프로브가 출력을 단언하지 않아, 래퍼가 훅을 못 찾고 지나가도 수가 찍혔다. 갈래마다 기대한 출력(deny,
  침묵)이 아니면 1로 끝나게 고치고 다시 쟀다. 첫 판의 수는 버렸다.
- **명세 축.** 줄 끝 역슬래시로 이은 `git commit -F \`+경로를 shlex가 이스케이프된 줄바꿈 값으로 읽어 놓쳤다. 리뷰어가
  트랜스크립트에서 약 350회 쓰인 모양이라고 셌다. 이은 줄을 한 줄로 보게 고쳤다. 옛 시간 프로브 `cd_outside_hook_time.sh`와 그 README
  행이 `cd web && ls`를 "침묵"이라 적은 것이 이 변경으로 거짓이 되어 잰 때의 사실로 고쳤다. "약 8분(484초) … 세 번"은 일지
  2026-10-13-12·30이 약 7분이라 "약 7~8분"으로 고쳤다.
- **표준 축(판단).** cd 훅이 막는 판정을 두 번 돌고 이름 없는 4-튜플을 넘기던 것을 `decision` 한 번과 `Destination`으로 묶었다.
  하위 폴더 알림의 실제 침묵 입력(하위 폴더에 남은 셸이 루트로 돌아오는 `cd`)을 페이로드 표에 더했다.
- **남긴 것.** `_native`·`resolve`가 cd 훅과 겹치는 것은 훅끼리 import하지 않는 규약의 비용이라 두었다.

## PR 직전 리뷰

첫 커밋 `52eb4a4` 뒤에 돌렸다. `coderabbit auth status`가 `Seat : not assigned`라 대체 둘을 돌렸다.

- **`bug-perf-review`(버그·성능).** Minor 다섯, Critical·Major 없음. 다섯 모두 고쳤다.
  - 같은 명령에서 쓰는 파일을 글자 그대로 견줘 `> ./m.txt`와 `-F m.txt`를 다른 파일로 봤다. 정규화한 경로로 견준다.
  - `git commit -F f && rm f`를 건너뛰었다. 커밋 뒤의 명령은 커밋이 읽는 내용을 바꾸지 않으므로 커밋 앞의 명령만 본다.
  - `--dry-run`(그리고 `--help`·`-h`)은 커밋하지 않는데 막았다. 보지 않는다.
  - heredoc 본문의 `git commit -F` 줄을 커밋으로 읽었다. 본문 줄을 비운다. 그 덕에 본문의 작은따옴표가 파싱을 깨던 못 보는 것도
    사라졌다.
  - 앞 명령의 `export SKIP=commit-msg`와 `git -c core.hooksPath=…`를 보지 않았다. 둘 다 보지 않는 커밋으로 더했다. 앞 호출에서
    `export`한 `SKIP`은 여전히 모른다(못 보는 것, 거짓 양성).
- **내장 `/security-review`(보안).** 식별 서브태스크가 하나를 냈다. 이 훅은 커밋하는 저장소의 판정 스크립트를 권한 확인 전에
  띄우는데, 그 저장소가 이 프로젝트인지 보지 않는다(Medium, 신뢰도 7). 거르기 서브태스크는 거짓 양성(신뢰도 3)으로 판정했다.
  공격자가 이 개인 훅을 알고 그 저장소에서 `-F` 커밋이 제안되어야 하며, 그런 저장소에서는 이미 테스트 등으로 그 코드를 돌린다는
  것이다. 신뢰도 8 미만이라 보고에서 뺐다. 고치지 않았고, 신뢰 경계로 훅 독스트링과 PR 본문의 남긴 위험에 적었다.

## PR 봇

[PR #225](https://github.com/njh6803/agent-os/pull/225)의 첫 푸시(`a649927`)에서 CI 여섯이 모두 초록이었다. CodeRabbit은 무료 리뷰
한도에 걸려 리뷰하지 않았다(`@coderabbitai review`도 한도로 거절). claude-review의 첫 회차는 Minor 하나와 Nit 둘을 냈다.

- Nit(`_LONG_WITH_VALUE`의 `--fixup`·`--squash`·`--cleanup`은 `_LONG_UNJUDGED`가 먼저 접어 닿지 않는다): 뺐다.
- Minor(테스트가 `decision`이 아니라 투영 둘을 잰다): 보류했다. 투영은 `decision`의 결과를 고르는 한 줄이고, `main`의 실제 출력은
  `tools/run_hooks.py`의 cd 훅 사례 여섯이 잰다.
- Nit(`deny_reason`의 추상화 수준이 섞였다): 보류했다. 리뷰어도 아직 읽을 만하다고 했다.

## 바꾼 것

- `tools/hook_bash_commit_msg.py`(새 훅)와 `tests/tools/test_hook_bash_commit_msg.py`.
- `tools/hook_bash_cd_outside.py`: `decision`, `Destination`, `subfolder_notice`, 독스트링의 알림 문단과 못 보는 것.
  `tests/tools/test_hook_bash_cd_outside.py`에 알림 시험.
- `.claude/settings.json`: Bash PreToolUse에 새 훅 등록.
- `tools/hook_payloads.toml`: cd 훅의 알림·침묵 사례 둘, 새 훅의 deny·침묵 사례 둘. `tools/run_hooks.py`: 자리표시자
  `${COMMIT_MSGS}`(commit-msg 판정을 부르는 임시 저장소).
- `.claude/rules/tools.md`: 시간 문단에 새 훅의 값. `KICKOFF.md`: 훅 목록의 두 훅과 계기·막는 훅 분류, 바꿀 곳.
- `.scratch/harness/probes/`: 변이 표 `bash_hooks_commit_msg_cd_mutations.toml`, 시간 프로브 `commit_msg_hook/time_hook.py`, README
  세 행, `cd_outside_hook_time.sh` 머리 주석.
- `.scratch/retro-queue.md`: 222·225를 닫았다.

## 검사

- `uv run pytest -q`: 셀프 리뷰 전 판에서 2466 통과(7 deselected). 리뷰 반영 뒤 두 훅의 시험은 69 통과. 전체는 커밋의 pre-commit이
  다시 돈다.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`(0 errors): 리뷰 반영 뒤 초록. `uv run lint-imports`, 지침
  검사, 타입 우회 검사는 리뷰 전 판에서 초록.
- `uv run python tools/run_hooks.py`: 리뷰 반영 뒤 페이로드 87건, 어긋남 0.
- 변이 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/bash_hooks_commit_msg_cd_mutations.toml`: 셀프 리뷰
  반영 뒤 열일곱 모두 기대대로(중간에 `-m`의 값 하나가 초록이라 시험 입력을 고쳤다), PR 직전 리뷰 반영 뒤 스물셋 모두 기대대로.
- 시간 프로브(PR 직전 리뷰 반영 뒤): 출력이 모두 기대대로, `commit` 글자 없음 210~225ms, `-F` 없는 커밋 199~219ms, 맞는 제목
  302~375ms, 긴 제목 281~314ms.
- 첫 커밋 `52eb4a4`의 pre-commit: 모두 Passed(pytest 453.3초, web-verify 251.0초). 인용 대조가 이 일지의 따옴표 하나(지운 첫 판
  독스트링의 문장)를 경고해 따옴표를 뗐다.
- 새 훅이 실제 세션에서 도는지는 워크트리 세션의 훅으로 볼 수 없다(주 체크아웃의 파일이 돈다, `.claude/rules/tools.md`). 병합 뒤
  주 체크아웃을 당긴 세션에서 처음 돈다.
- 둘째 커밋 `a649927`의 pre-commit: 모두 Passed(pytest 364.2초). PR의 CI 여섯도 초록이었다.
- 병합 직전 main(`1fb0fde`)이 움직여 `tools/sibling_overlap.py`가 겹침을 알렸다. 일지 37→43(뒤에 47), 대기열 235→239로 옮기고 main을
  합쳤다. 충돌은 대기열 표와 프로브 README 표의 끝에 양쪽이 더한 행, 그리고 main이 3회차로 올린 223뿐이었다.

## 회고

후보 일곱, 승인 둘, 기각 다섯, 넘김 없음.

1. **승인, 대기열 239(새로).** 막는 훅이 하류 판정(git, commit-msg 훅)을 앞당길 뿐이라고 첫 판 독스트링에 적으면서, 하류가 입력을
   바꾸거나 판정을 건너뛰는 길을 나열하지 않았다. 셀프 리뷰가 여섯, PR 직전 리뷰가 다섯 더 찾았다. 사건이 있고, 행동이 일어나는
   자리(`.claude/rules/tools.md`의 막는 훅 항목)에 더하는 문장이며, PR 하나로 되돌릴 수 있다. 이 PR의 범위를 넓히지 않으려고
   대기열에 두었다.
2. **승인, 대기열 223에 4회차.** (회고를 쓸 때는 3회차였는데, 병합 직전에 합친 main이 일지 2026-10-13-39로 이미 3회차를 더해
   4회차가 되었다.) 시간 프로브 `commit_msg_hook/time_hook.py`의 첫 판이 출력의 표지를 단언하지 않아, 래퍼가 훅을
   못 찾고 지나가도 수가 찍혔다(셀프 리뷰 두 축이 잡았다). 223과 같은 모양이다. 프로브 규칙이 `docs/agents/issue-tracker.md`에만
   있어 프로브를 쓰는 자리에 실리지 않는다.
3. **기각.** 도구 호출 사이 문장을 영어로 쓴 것(여러 번)은 `hook_midturn_korean`이 잡았다.
4. **기각.** 일지에 지운 첫 판 독스트링의 문장을 따옴표로 옮긴 것은 인용 대조가 잡았다.
5. **기각.** 마지막 `-F`만 보게 바꾼 뒤 `-m` 변이를 가린 약한 시험 입력은 `tools/mutate.py`가 잡았다.
6. **기각.** `$(git merge-base …)`를 든 복합 git 명령이 워크트리 가드에 거부됐다. `CLAUDE.md` 환경 함정에 이미 있다.
7. **기각.** 84줄 heredoc으로 변이 표에 덧붙이려다 `hook_bash_heredoc`이 막았다. 훅이 설계대로 잡았다.

## 다음

- **이 PR 뒤의 다음 작업은 대기열 223이다.** 223이 4회차로 결정표의 chore 배치 조건을 채운다. 열린 항목 가운데 회차 3 이상은
  189·217·223이고, 189와 217은 "어디로" 칸이 먼저 잴 것을 요구한다.
- **그다음 후보는 훅 묶음이다.** 130·145·162·216은 모두 `tools/hook_payloads.toml`·`tools/run_hooks.py` 둘레라 "대상 파일이 같은
  항목 셋 이상" 조건을 채운다. 72도 같은 표를 건드리지만, 행이 "가르는 법은 반영 때 정한다"는 설계 몫을 남겨 그 묶음에서 뺐다.
- **새 훅 `hook_bash_commit_msg`는 병합 뒤 주 체크아웃을 당긴 세션에서 처음 돈다.** 그 세션이 `git commit -F`로 커밋할 때 막혀야 할
  제목에서 막히는지, 지나가야 할 커밋을 막지 않는지 처음 볼 수 있다. 막히면 그 명령의 모양을 일지에 남긴다.
- **claude-review가 보류된 지적 둘**(cd 훅 테스트가 투영을 재는 것, `deny_reason` 분리)은 PR 코멘트에 이유를 남겼다. 다음에 두
  훅을 고칠 때 함께 본다.
