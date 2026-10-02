# 2026-10-02 (02) 훅 등록의 실행 래퍼 — 대기열 91

하네스 chore다. 지시문은 일지 2026-10-02-01의 "다음"이 가리킨 next-session 지시문에서 왔다. 브랜치는
`chore/hook-registration-fail-open`이다. 데스크톱 앱 세션이 당긴 주 체크아웃(`5e4fb4c`, 작업 트리 깨끗함)에서 시작했고,
`EnterWorktree`로 만든 워크트리에서 브랜치 이름을 바꿔 일했다. 세션 제목은 UserPromptSubmit 훅의 지시대로 브랜치 이름으로
바꿨다.

> 사용자: ".scratch/retro-queue.md의 91(훅 등록 명령이 스크립트가 없을 때 막지 않고 지나가게)을 chore PR 하나로 반영한다"

앞 PR의 끝을 여기 남긴다. PR #120은 3회차(`7b7fc9b`)에서 검사 여섯이 초록이었고 `5e4fb4c`로 병합됐다. 3회차 지적 셋은
고치지 않았다. claude-review Minor(분할 코드가 훅 셋에 복사됨)는 `.claude/rules/tools.md`가 받아들인 비용이라 두었고,
같은 입력을 여러 훅에 넣는 대조 테스트는 후보로 남는다. claude-review Nit(두 거부 이유의 꼬리 문장 중복)도 두었다.
CodeRabbit Minor(일지 회고의 91 제목이 지금 동작과 반대)는 대기열 행과 같은 목표 문장이라 오탐이다. 주 체크아웃의 임시
위임 파일은 앞 세션이 지우고 당겼다(이 세션 시작 때 `git status`가 깨끗했다).

선행 조건(일지 08의 "다음")은 반만 봤다. UserPromptSubmit 훅이 제목 지시를 넣었고, PreToolUse 훅이 돌았다 —
`hook_bash_python_stub`이 내 명령 둘을 막았다(회고의 일지에만). Bash·PowerShell이 막히지 않았으니 옛 모양으로 등록된
`hook_pr_head_sync`도 파일을 찾았다. Stop 훅의 판정은 이 세션의 첫 턴 끝, 곧 이 일지를 쓴 뒤라 아직이다.

## 자리를 정한 것

- **래퍼를 골랐다.** 대기열 91의 "어디로"는 등록 모양을 바꾸는 안과 실행 래퍼 안을 둘 다 들었다. 등록에 셸 문법
  (`[ ! -f … ] || uv run …`)을 넣으면 훅을 돌리는 셸에 기댄다. 래퍼는 등록 명령의 모양을 그대로 두고 스크립트 자리에
  `tools/launch_hook.py`를, 끝에 훅 이름을 둔다. 래퍼는 훅 파일이 없으면 0으로 끝나고, 있으면 `runpy.run_path`로 같은
  프로세스에서 `__main__`으로 돌린다. 러너(`tools/run_hooks.py`)는 등록 명령이 `REGISTRATION` 모양과 글자 그대로 같은지
  대조하고(다르면 ValueError) 같은 모양으로 자식을 띄운다.
- **`os.path`와 `runpy`.** 첫 판(`pathlib`+`runpy`)이 훅 한 번에 약 20ms를 더해 세 판을 손으로 견줬다. `hook_env_read`의
  침묵 입력을 일곱 번씩 돌렸고, 바로 209~211ms, `pathlib`+`runpy` 225~236ms, `os.path`+`runpy` 217~235ms, 모듈을 손으로
  만들어 `exec` 210~222ms였다. 직접 `exec`는 `runpy`가 해 주는 `sys.modules["__main__"]` 교체를 손으로 다시 짜야 해
  `os.path`+`runpy`를 골랐다. 셀프 리뷰 표준 축이 `-X importtime`으로 본 `pathlib`의 몫은 7.4~8.8ms였고, `pathlib`을 이미
  import하는 훅 셋(journal_retro, prompt_directive, ruff_line_width)에서는 0이다.
- **래퍼 모양이 아닌 등록은 모두 거절한다.** 저장소 파일을 부르지 않는 훅(`echo …`)도 거절한다.
  `tools/check_instructions.py`는 그런 훅을 받지만, 러너는 그 전에도 표에 없는 훅을 빈자리로 세어 커밋을 막았다. 모든
  등록이 `tools/`의 훅이라는 전제는 같고, 그것을 `REGISTRATION` 주석에 적었다.
- **래퍼 자체가 없는 창은 구조로 없애지 않았다.** 주 체크아웃이 이 래퍼를 들인 커밋보다 뒤에 있으면 등록 열하나가 모두
  2로 끝난다. 이 PR이 병합된 뒤 당기기 전이 그 창이다. `uv run --directory "${CLAUDE_PROJECT_DIR}" … python -m
  tools.launch_hook`이면 없는 모듈이 1(막지 않는 오류)로 끝나 창이 없어진다. 그러나 훅 프로세스의 현재 디렉터리가 바뀌어
  `hook_env_read`가 입력에 `cwd`가 없을 때 물러나는 자리(`os.getcwd()`)가 달라지고, `site-packages`에 같은 이름의 `tools`
  정규 패키지가 있으면 그쪽이 이긴다(PEP 420의 탐색 규칙을 읽었다, 재지 않았다). 그래서 두지 않고, 래퍼 독스트링과 rules에 창과 "병합 직후 주 체크아웃을 당긴다"를
  적었다.

## 잰 것

- **`claude -p` 세션 넷**(`.scratch/harness/probes/hook_registration/run.sh`, haiku, claude 2.1.286). A 저장소의 등록
  그대로 `echo canary-A`가 돌았다. B 없는 훅을 래퍼로 더해도 `echo canary-B`가 돌았다. C 같은 없는 훅을 옛 모양으로 더하면
  `PreToolUse:Bash hook error`와 `can't open file '…\hook-registration-fail-open\tools\hook_absent.py'`로 막혔다. 그 경로로
  보아 자식 세션의 `${CLAUDE_PROJECT_DIR}`은 이 워크트리였다. D 맨 `python --version`에는 래퍼를 거친
  `hook_bash_python_stub`의 거부 이유가 도구 결과로 왔다.
- **시간**(`time_launch.sh`). `hook_env_read` 한 번이 바로 210~217ms, 래퍼 222~230ms다. 셀프 리뷰 두 축이 다시 돌려
  216~225/224~233ms와 216~265/221~315ms(첫 회 이상치)를 냈다.
- **변이 아홉**(`launch_hook_mutations.toml`). 없는 훅에서 2, 파일 확인 없음, 인자 수 확인 없음, 훅에 래퍼 인자,
  `__main__` 아닌 이름, 러너가 훅을 바로, 앞부분만 맞춤, 옛 이름 읽기, 루트 자리 안 바꿈. 모두 빨강이다. 이 표는 한 번
  어긋났다(셀프 리뷰 절).
- **바꾼 규칙의 카나리아**(손으로 봤다, 스크래치 스크립트). `operations.md` 환경 규약 상세의 명령에 sonnet으로 세 번씩
  물었다. 실험군은 `tools/hook_env_read.py`를 Read한 세션이고, 셋 모두 새 줄의 값(약 10ms, 210~217ms, 222~230ms)을
  옮겼다. 대조군은 `paths` 밖의 `README.md`를 Read한 세션이고, 셋 모두 "없음"이었다.

## 셀프 리뷰

`/code-review`, base `5e4fb4c`, 수정 파일 14, 미추적 4(디렉터리 하나 포함), 커밋 0. `tools/`와 `tests/`의 파이썬이 바뀌어
두 축 모두 기본 모델이다. 명세는 대기열 91 행과 지시문이고, 설계 선택과 이 세션이 더한 문서는 리뷰어 참고로 갈랐다.

- **두 축이 같은 Major를 따로 냈다.** 변이를 돌린 뒤 `ruff format`이 러너의 ValueError f-문자열을 한 줄로 합쳐, 변이 표
  "옛 판"의 원문이 코드에서 사라졌다. `mutate.py --check`가 2로 끝났고, 프로브 README의 "아홉 모두 빨강"을 커밋한 표로
  다시 낼 수 없었다(회고 92).
- **표준 축의 그 밖.** Minor: 프로브 README 13행이 인용한 rules 문장("…2로 끝나고(…)")이 바뀌었다. 새 README 줄이
  근거 자리로 든 rules 막기 문장이 이 프로브를 가리키지 않았다. 래퍼를 빠뜨리면 모든 훅이 2로 끝나 막는다던 KICKOFF의 첫 판과
  러너·테스트 독스트링의 "그 매처의 모든 호출을 막는다"는 PreToolUse에서만 참이다. Nit: 테스트 헬퍼 이름이 영문,
  래퍼 독스트링의 "stderr도 같다"(예외의 traceback에 래퍼와 runpy 프레임이 더해진다), `pathlib` 몫, 창의 범위,
  `kickoff/facts.md`의 근거 칸. 판단 항목: 러너 대조와 지침 검사의 겹침(Duplicated Code), `REGISTRATION` 문자열의 세 가공
  (Primitive Obsession), `_REGISTERED`·`TOOLS`(Mysterious Name), 러너가 등록 계약을 함께 진다(Divergent Change), 테스트
  이름의 "말없이".
- **명세 축의 그 밖.** (a) 이 PR이 스스로 여는 틈(래퍼 부재 창)과 그 완화가 어디에도 없다, 바꾼 rules의 카나리아가 손으로
  돌린 목록에 없다. 카나리아는 브리프를 쓸 때 돌고 있었다. (b) `echo` 훅까지 거절하는 것이 지침 검사의 근거 문장과 어긋난다.
  (c) 변이 표, 인용 잔존, KICKOFF의 과장, `--settings`의 훅이 프로젝트의 훅에 더해진다던 `run.sh`·README의 첫 판(C는 실렸다는
  것만 보인다).
- **고친 것.** 변이 표 원문, README 13행의 인용, rules 막기 문장이 `run.sh`를 가리키게, 래퍼 부재 창과 병합 직후 당기기를
  래퍼 독스트링과 rules에, KICKOFF·러너·테스트 독스트링의 "막는다"를 PreToolUse로 좁혔다, 테스트 헬퍼와 테스트 이름,
  traceback과 `pathlib` 몫, `facts.md` 근거 칸, `--settings` 문장을 어림으로, `_REGISTRATION_PATTERN`·`TOOLS_DIR`로 이름을
  바꿨다, `echo` 훅 거절의 근거를 `REGISTRATION` 주석에. 고친 뒤 `mutate.py --check`와 변이 아홉을 다시 돌렸다.
- **남긴 것.** 러너 대조와 `hooks_with_relative_paths`의 겹침은 두었다. 지침 검사는 임시 트리 테스트와 다른 프로젝트로
  복사되는 검사라 상대 경로를 따로 본다. `REGISTRATION`의 세 가공은 원천 하나에서 나온다. 러너가 등록 계약을 지는 것은
  러너가 그 모양으로 띄우기 때문이다. 래퍼 부재 창은 위 "자리를 정한 것"대로 두었다.

## 검사

- 리뷰 반영 뒤: `uv run pytest -q` 1215 passed(경고 3은 기존 pytest-asyncio 설정 경고), `uv run ruff check .`·`uv run
  ruff format --check .` 통과, `uv run pyright` 0 errors, `uv run lint-imports` 5 kept, `tools/check_instructions.py`·
  `tools/check_type_escapes.py` 통과, `tools/run_hooks.py` 52건 어긋남 0, `tools/mutate.py --check`와 변이 아홉.
  `pnpm -C web verify`는 반영 전에 통과(Vitest 263 passed)했고 커밋의 pre-commit이 다시 돈다. 워크트리에 web 의존성이 없어
  `pnpm -C web install --frozen-lockfile`을 한 번 했다. `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.
- 처음 전체 pytest에서 `tests/tools/test_hook_pr_next_session.py`의 매처 대조 하나가 빨갰다. 등록 명령에서
  `tools/hook_pr_next_session.py`라는 글자로 자기 훅을 찾았는데 새 모양에는 훅 이름만 남는다. 러너에
  `registration_command`를 두고 그 테스트가 등록 명령 전체와 대조하게 했다.

## 보고 언어

도구 호출 사이의 중간 문장 셋을 영어로 썼다("Now the runner tests: …", "Now I'll edit the KICKOFF lines.", "Now the
mutation table's old-version entry …"). 사용자가 고치지는 않았다. Stop 훅은 마지막 텍스트만 받아 이 자리를 보지 못한다.

## 회고

후보 셋을 냈고 하나가 새 항목으로 승인됐다.

> 사용자(질문에 답): "기록만", "새 항목 (Recommended)", "기록만 (Recommended)"

- **기록만: 중간 문장을 영어로 썼다.** 위 보고 언어 절이다. Stop 훅(83)이 닫힌 뒤에도 일지 08·09·01에 이어 넷째 세션이다.
  추천은 트랜스크립트의 직전 텍스트를 보는 계기 훅(PreToolUse 시점에 그 텍스트가 기록되는지 탐침이 먼저)이었고, 답은
  기록만이었다.
- **92(새로): 커밋에 든 변이 표의 원문이 코드에 있는지 pre-commit이 본다.** 위 셀프 리뷰의 Major다. 고정된 패턴이라
  1회차지만 검사로 간다.
- **기록만: 래퍼 자체가 없는 창.** 래퍼 독스트링과 rules에 적었고, 이 PR 병합 직후 주 체크아웃을 당기면 닫힌다.
- 일지에만: `hook_bash_python_stub`이 내 grep 패턴의 `python`(따옴표 안의 `|` 뒤)을 두 번 막았다. 대기열 82가 적은 거짓
  양성 그대로다. 워크트리 가드가 `$@`가 든 복합 명령을 거부해 스크립트 파일로 옮겼다(기억과 `CLAUDE.md`에 이미 있다).
  명세 축 브리프를 쓸 때 돌고 있던 규칙 카나리아를 브리프에 넣지 않아 누락으로 나왔다.

## 다음

- 이 PR의 마지막 CI와 병합은 다음 일지에 한 줄 남긴다.
- **병합 직후 주 체크아웃을 당긴다.** 그 전에 이 워크트리 세션이나 새 main에서 뜬 워크트리 세션이 다시 시작되면 등록
  열하나가 모두 2로 끝난다(래퍼 부재 창).
- Stop 훅의 첫 세션 확인(일지 08의 "다음")은 이 세션의 턴 끝 판정이다. 결과는 다음 일지에 적는다.
- 다음 chore 후보는 92(이번 회고, pre-commit 한 줄), 84(워크플로 파일이라 별도 PR), 88·49(ADR 본문과 이력의 표시
  규약, 같은 대상)다.
