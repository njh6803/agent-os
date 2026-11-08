# measure-word-journal-scope: 측정 낱말 훅의 범위에 일지를 더한다

**What to build:** `tools/hook_measure_word.py`는 `docs/adr/`, 프로브 README, 대기열 항목 파일에 Write·Edit로 더한 줄이 `쟀다`·`재니`·`실측`을 들면서 같은 줄에 `probes/`도 `손으로`도 없으면 알린다. 일지(`docs/journal/`)는 이 범위 밖이라, 손으로 돌린 스크래치 스크립트(`yaml_probe.py`)로 본 것을 일지에 `쟀다`로 적어도 알림이 없었고 셀프 리뷰 표준 축이 Nit으로 잡았다(대기열 558, 227의 7회차). 일지 계기 `tools/hook_journal_evidence.py`는 세션·에이전트마다 한 번이라 문장마다 짚지 못한다. 이 티켓은 `is_evidence_doc`에 `docs/journal/` 바로 아래의 `.md`를 더해, 일지에서도 근거 표지 없는 측정 낱말 줄을 줄마다 알리게 한다. 반영할 때 `hook_journal_evidence`와 같은 편집에 겹치는지 보라는 항목의 요구대로, 겹침은 독스트링에 적고 시험으로 고정한다.

범위는 이 넷이다.

- 판정: `docs/journal/<이름>.md`(하위 폴더 없이 직계, `.md`만)를 근거 문서로 본다. 비슷한 이름의 폴더(`docs/journals/`), 하위 폴더, `.md`가 아닌 파일은 지나간다. 알림 문장과 무시 조건은 일지의 사용자 프롬프트 인용(`> 사용자:`)이 낱말을 든 줄을 이름으로 든 것으로 읽게 한다
- 겹침: 일지를 고친 편집에는 `hook_journal_evidence`의 알림(세션·에이전트마다 한 번)과 이 훅의 알림(걸릴 때마다)이 함께 날 수 있다. 서로 다른 일을 판정하므로 합치지 않고, 독스트링과 시험이 겹침을 적는다
- 시험·변이: `tests/tools/test_hook_measure_word.py`, `tools/hook_payloads.toml`의 발동·침묵 사례, `.scratch/harness/probes/measure_word_hook_mutations.toml`의 변이를 일지 몫만큼 더한다
- 문서: `docs/agents/issue-tracker.md`의 프로브와 근거 절이 이 훅의 범위를 적은 문장에 일지를 더한다. `.claude/rules/tools.md`의 `hook_measure_word` 항목과 카나리아가 묻는 문구("입력의 글만 보고 파일을 열지 않는다")는 바꾸지 않는다

**대기열:** 558

**Status:** done

## 수용 기준

- [x] 일지 직계 `.md`에 근거 표지 없는 측정 낱말 줄을 더한 Write·Edit에 훅이 알리고, `probes/`나 `손으로`가 같은 줄에 있으면 지나간다. 일지의 하위 폴더, `.md`가 아닌 파일, `docs/journals/`는 지나간다(시험이 단언한다)
- [x] 독스트링이 일지 범위와 `hook_journal_evidence`와의 겹침(세션을 알면 많아야 한 번, 대문자 경로는 이 훅만), 새로 생긴 못 보는 것(Bash heredoc로 쓴 일지는 이 훅이 아니라 `hook_journal_evidence`의 Bash 묶음만 본다)과 경로 깊이를 적고, 적은 항목마다 시험이 하나씩 고정한다
- [x] 일지 몫의 변이가 모두 기대대로이고(`tools/mutate.py`가 `변이 22 모두 기대대로`를 찍었다), 프로브 README의 해당 행이 결과를 적는다
- [x] 페이로드 표(`tools/hook_payloads.toml`)에 일지 발동 하나와 침묵 하나가 있고 `tools/run_hooks.py`가 통과한다(`훅 페이로드 177건, 어긋남 0건`)
- [x] 이슈 트래커 문서의 문장이 일지를 포함한다
- [x] 회고 반영: 대기열 558에 닫힘 표지를 단다
- [x] 검증 명령이 모두 초록이다 (`tools/run_checks.py`: lint-imports·pyright 둘·web-verify 통과, pytest 6582건 통과와 2건 실패. 실패 둘은 실제 프로세스·시간 제한 시험(`tests/channel/cli/test_interrupt.py`, `tests/tools/test_probe_kit.py`)이고 이 변경이 건드리지 않은 파일이며, 부하가 큰 전체 실행(1289초)에서만 났고 단독으로 돌리자 둘 다 통과했다. ruff 린트·포맷도 통과)
