# 010: 일지를 쓸 때 결과 문장의 근거 종류를 밝히라고 짚고, Glob이 무시된 폴더를 훑지 않게 한다

**What to build:** 일지(`docs/journal/*.md`)를 Write·Edit로 쓰거나 고칠 때 세션·에이전트마다 한 번, 결과 문장마다 근거의 종류(탐침이 단언하거나 찍은 것, 손으로 본 것과 그 명령, 코드 읽기, 어림)를 밝히고 문서에서 읽은 것은 그 문서를 출처로 적으라는 계기를 넣는 PostToolUse 훅 `tools/hook_journal_evidence.py`를 더한다. 알림은 `docs/agents/issue-tracker.md` 프로브와 근거 절을 가리킨다. 프로브 README의 계기(`tools/hook_probe_conclusion.py`)에 얹지 않고 따로 둔다. 판정하는 경로와 알림 문장이 다르고, `tools/hook_report.py`가 훅 파일마다 발동을 세어 두 계기를 따로 갈라야 하기 때문이다. 같은 `.claude/settings.json`을 고치는 대기열 370도 묶는다. 설정 `env`에 `CLAUDE_CODE_GLOB_NO_IGNORE=false`를 넣어 Glob이 `.gitignore`를 따르게 하고, `CLAUDE.md` 환경 함정의 Glob 줄을 남는 함정만으로 줄인다.

**대기열:** 445, 370

**Status:** done

## 수용 기준

- [x] `tests/tools/test_hook_journal_evidence.py`를 먼저 써서 빨간 것을 본다. 일지 경로의 판정(맞는 경로, 일지 폴더 밖, 하위 폴더, `.md`가 아닌 파일), 알림 문장의 근거 몫, 알림이 가리키는 절 제목이 그 문서에 있는지, 표지로 세션·에이전트마다 한 번인지를 본다
- [x] 훅 독스트링에 왜(대기열 445의 사례), 따로 둔 까닭, 판정, 한 번, 못 보는 것을 적고, 못 보는 것 항목마다 시험 하나로 고정한다
- [x] `.claude/settings.json`의 첫 `Write|Edit` 묶음에 래퍼 모양으로 등록하고, `tools/hook_payloads.toml`에 발동 하나와 실제 침묵 입력을 더해 `tools/run_hooks.py`가 어긋남 없이 돈다
- [x] `.scratch/harness/probes/`에 이 훅의 변이 표를 더해 빨강을 보고, 그 프로브 README에 행을 둔다
- [x] `.claude/rules/tools.md`의 Write·Edit PostToolUse 훅 목록과 `docs/agents/issue-tracker.md` 프로브와 근거 절의 계기 문장이 새 훅과 맞는다
- [x] `.claude/settings.json`의 `env`에 `CLAUDE_CODE_GLOB_NO_IGNORE=false`가 있고, 그 설정이 Glob에 닿는 것을 새 `claude -p` 세션에서 손으로 본다. 무시된 자리를 찾던 길이 어떻게 바뀌는지도 본다(`.venv`로 봤다. 루트에서는 찾지 않고, 파일이 든 하위 폴더 `.venv/Lib/site-packages`를 `path`로 주면 찾는다. `.venv` 자체를 주면 찾지 않는다. 그 안의 `.gitignore`(`*`) 때문이라고 어림한다. `.scratch/token-report/`는 같은 `.gitignore` 규칙이라 따로 보지 않았다)
- [x] `CLAUDE.md` 환경 함정의 Glob 줄이 남는 함정만 적는다
- [x] 대기열 445·370 행을 이 티켓으로 닫는다
- [x] 검증 명령이 모두 초록이다
