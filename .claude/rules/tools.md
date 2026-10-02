---
paths:
  - "tools/**"
  - "tests/tools/**"
  - ".claude/settings.json"
  - ".pre-commit-config.yaml"
---

# 하네스 규칙

원천은 `tools/` 코드와 `tests/tools/`, 훅 등록은 `.claude/settings.json`이다. 아래는 확정된 결정이다. 2026-09-28 감사까지 이 규약은 훅 하나의 주석, 검사의 독스트링, 대기열에 흩어져 있었다.

- 훅은 단독 실행 스크립트다. 서로 import하지 않고 표준 라이브러리만 쓴다. 같은 파싱(heredoc 본문 벗기기, 인용 제거, 제어 연산자 분리)이 여러 훅에 복사되어 있는 것은 그 결정의 비용이다.
- 훅은 stdin을 바이트로 읽는다(`json.load(sys.stdin.buffer)`). 훅 환경에 `PYTHONUTF8`이 있다고 가정하지 않는다 — 없으면 텍스트 stdin은 cp949이고, 한글이 든 페이로드는 조용히 출력 0바이트가 된다. 설정 `env`가 넣는 값을 훅 쪽에서는 재지 못했다(대기열 40). `tools/check_instructions.py`가 판정한다.
- 계기 훅과 막는 훅을 가른다. 계기 훅(`additionalContext`)은 단계를 닫는 순간의 지침에 처음부터 붙인다. 막는 훅(`permissionDecision: deny`, `decision: block`)은 지침으로 적은 뒤에도 어겨진 것이 확인된 뒤에만 더한다(CLAUDE.md 교정 루프). 예외는 실패가 조용하고(어겨진 뒤에야 안다) 패턴이 고정된 것 — 그것은 첫 사건에서 막는 훅으로 간다(대기열 22·25·43, `hook_env_read`). PreToolUse에서 종료 코드 2는 "막아라"이고 stderr가 이유가 된다. 등록이 `python <경로>` 꼴이라 스크립트를 못 찾으면 파이썬이 2로 끝나고(2026-09-29 실측), 경로 오류 하나가 모든 Bash를 막는다. 반대로 훅 안의 예외(종료 코드 1)와 `timeout` 초과는 막지 않고 지나간다(fail-open, 공식 hooks 문서. 이벤트마다 다르니 PreToolUse 기준이다). 막는 훅의 버그는 조용히 문을 연다.
- 훅과 검사의 독스트링에는 무엇을 잡는지와 함께 **못 보는 것**을 적는다. 못 본다고 적은 주장도 잰다(대기열 10).
- 새 훅은 넷을 함께 한다. `.claude/settings.json`에 `${CLAUDE_PROJECT_DIR}`로 등록, `tests/tools/`에 순수 함수 테스트, `tools/hook_payloads.toml`에 발동 하나와 발동하지 말아야 할 **실제** 입력 하나(반례의 축을 빼지 않게, 대기열 24)를 더해 `tools/run_hooks.py`(pre-commit)로 실행 확인(워크트리 세션의 훅으로는 바뀐 파일을 확인할 수 없다 — 주 체크아웃의 파일이 돈다), 덧댄 사본이면 `PATCHED_SKILLS`. 검사의 빨강은 `tools/mutate.py`로 본다.
- `tools/`의 식별자는 영문, 문자열·주석·독스트링은 한국어다. `tests/tools/`는 테스트 함수와 헬퍼 이름을 한국어로 써 왔고 그대로 간다(`CODING_STANDARDS.md`가 테스트 함수명에 요구하는 것의 연장). `check_type_escapes.py`의 한국어 지역 변수는 이 규약 전의 것이라 두고, 새 도구 코드에는 쓰지 않는다(대기열 12).
- 훅 하나가 Bash 호출마다 약 0.2초를 쓴다(2026-09-28 실측 207~217ms, `.venv`가 있을 때). PreToolUse Bash 훅이 여섯이라 합이 약 1.2초이고(함께 도는지 차례로 도는지는 재지 않았다), Bash·PowerShell에는 PostToolUse 하나(`hook_pr_next_session`)가 더 붙는다. PowerShell의 PreToolUse는 둘(`hook_git_main_commit`, `hook_pr_head_sync`), Grep 호출에도 하나(`hook_env_read`)가 붙는다. `hook_pr_head_sync`는 리뷰를 부르는 명령(`gh pr ready`, CodeRabbit 요청 코멘트)에서만 git과 gh를 띄운다(2026-10-02 실측: 그 밖의 명령 226~231ms, 로컬 판정 310~337ms, gh 길 941~998ms, `.scratch/harness/probes/pr_head_sync/time_hook.sh`). Write·Edit에는 PostToolUse 둘(`hook_journal_retro`, `hook_ruff_line_width`)이 붙고, 파이썬 파일이면 뒤의 것이 ruff를 한 번 더 띄워 약 0.33초다(2026-10-01 실측 323~325ms, 마크다운은 197~206ms — ruff 몫이 약 0.12초). Stop에는 하나(`hook_stop_korean`)가 턴마다 붙고 약 0.19초다(2026-10-01 실측 184~195ms, `.scratch/harness/probes/stop_payload/time_hook.sh`). 훅을 더할 때 이 값을 함께 본다.
