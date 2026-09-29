# 하네스 프로브

하네스(`tools/`, `.claude/`)의 코드 주석이 근거로 든 측정 스크립트다. 기능이 아니라 slug 자리에
`harness`를 쓴다. 규약은 `docs/agents/issue-tracker.md`. 2026-09-28에 세션 스크래치패드에서
옮겼다(대기열 29). 옮기기 전의 근거는 프로브를 "실측"으로 가리킨다. 이 표가 그 말을 파일로 잇는다.

`probe_*.ps1` 둘은 Claude 데스크톱 창의 접근성 트리를 읽기만 하고 아무것도 누르지 않는다. 창이 하나 떠 있어야 한다.
`probe_tree.ps1`은 화면의 글이 곧 측정 대상이라 대화 원문의 앞부분을 찍는다. 출력을 옮기기 전에 비밀이
없는지 본다. `probe_send.ps1`은 입력창 값의 길이만 찍는다(PR #89 CodeRabbit, CWE-532).
돌리는 법은 `pwsh -File .scratch/harness/probes/<파일>`이다.

`.claude/rules/tools.md`의 "스크립트를 못 찾으면 파이썬이 2로 끝나고(2026-09-29 실측)"는 파일이 없는 한 줄이다. `uv run python C:/nonexistent/hook_missing.py < /dev/null; echo $?`가 `can't open file`과 함께 2를 냈다.

`md_tables_vs_cmark.py`는 저장소 루트에서 `PYTHONUTF8=1 uv run --with cmarkgfm==2025.10.22 --with cffi==2.1.1 python .scratch/harness/probes/md_tables_vs_cmark.py`로 돈다.
cmarkgfm은 uv의 일회용 환경에만 들어가고 프로젝트 의존성이 아니다. 처음 한 번은 내려받는다. 버전을 고정하지 않으면 실행마다 최신 판을 받아 기록의 기준이 바뀐다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `probe_send.ps1` | 이름이 "보내기"/"Send"인 요소의 개수·종류·활성 여부·패턴, 그리고 입력창 값의 길이 | `tools/open_session.ps1`의 보내기 버튼 고르기 주석("(2026-09-22 실측,") | Claude 창 하나 |
| `probe_tree.ps1` | 창의 Text·Button·Edit·Document 요소를 훑어 지시문이 화면에 어떻게 보이는지 | `tools/open_session.ps1`의 진단 주석과 슬래시 명령 주석("(2026-09-23 실측)", "(2026-09-23 실측,") | Claude 창 하나 |
| `md_checks_mutations.toml` | `tools/check_md_tables.py`·`tools/check_line_separators.py`의 규칙 하나씩을 뺀 변이 28(대체 리뷰의 성능 넷 포함). 돌리는 법은 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/md_checks_mutations.toml` | 일지 2026-09-28-08의 변이 줄 | 검사나 그 테스트를 고칠 때. 원문이 한 번 있어야 하므로 코드가 바뀌면 변이도 고친다 |
| `md_tables_vs_cmark.py` | `tools/check_md_tables.py`와 cmark-gfm의 표 모양(끝 줄, 본문 행)과 한 줄의 칸 수. 저장소 마크다운 전부와 무작위 문서 | `tools/check_md_tables.py` 독스트링의 차분 대조 문단과 코드 주석("차분 대조가 찾았다") | 검사를 고칠 때. 어긋나면 줄인 문서를 찍는다 |
| `instruction_loading/` | Claude Code가 지침 파일을 언제 싣는지. 카나리아를 넣은 임시 트리(루트 CLAUDE.md, 하위 CLAUDE.md와 그 안의 `@` 임포트, `paths` 규칙, 하위 폴더의 규칙)를 `run.sh --setup`으로 만들고 `claude -p`를 돌려 `InstructionsLoaded` 훅 로그로 판정한다. `results.txt`는 그 로그의 요약이다. R1 시작, R2 `sub/file.txt` Read(`nested_traversal`·`include`·`path_glob_match`), R3 다른 폴더 Read, R4·R5는 cwd가 `sub`라 탐침 트리의 `.claude/settings.json` 훅이 0건(조상의 설정은 읽지 않는다), R4b·R5b는 같은 실행을 `--settings`로(하위 CLAUDE.md가 시작 시 실리고 `paths` 규칙은 루트 기준), R6 `claudeMdExcludes`. 2026-09-29 claude 2.1.281, Windows | `tools/check_instructions.py`의 실측 주석, ADR 0004·0021의 2026-09-29 이력, `kickoff/facts.md` | 판을 올렸을 때. `claude` CLI와 인증이 든다. 트리를 저장소 안에 만들지 않는다(중첩 CLAUDE.md가 지침 검사에 걸리고 Read하면 실린다). 사용자 전역 훅(Stop 알림 등)이 탐침 실행에도 돈다 |
| `import_comments/` | 임포트와 `paths`의 경계 사례에서 지침 판정자와 Claude Code가 어떻게 갈리는지. `cases.py`가 사례(HTML 주석·펜스·코드 스팬·HTML 블록·굵게·한글 경로, 깨진 YAML의 `paths`)를 담고 `judge`로 판정자 쪽을, `run.sh <저장소 밖 디렉터리>`가 트리를 만들어 `claude -p`의 `InstructionsLoaded` 로그로 실측 쪽을 낸다. `results.txt`는 둘을 나란히 둔 요약이다. 2026-09-29 claude 2.1.281(haiku), Windows | `tools/check_instructions.py`의 `_without_blocks`·`_without_code`·`at_imports`·`_paths_patterns` 독스트링, `tests/tools/test_check_instructions.py`의 사례 id, `kickoff/facts.md` | 판을 올렸을 때, 판정자를 고칠 때. `claude` CLI와 인증이 든다. `--setting-sources project,local`로 사용자 전역 훅을 뺀다 |
| `env_deny_probe.md` | `.env` deny를 넓히기 전후에 Read·Bash·PowerShell의 읽기 모양이 막히는지. 가짜 `.env`로 쟀고 결과표만 남긴다(스크립트 없음) | `tools/hook_env_read.py` 독스트링, `docs/constitution/operations.md` 가드레일, `kickoff/facts.md` | `.claude/settings.json`의 deny를 바꿀 때. 진짜 `.env`로 재지 않는다 |
| `instruction_check_mutations.toml` | `tools/check_instructions.py`의 새 판정 넷(rules 재귀, 임포트 끝 경계, rules·헌법 안의 `@`, 그 배관)과 PR #100 리뷰 반영 열(블록 주석의 들여쓰기, 들여쓴 코드 줄의 문단 속 주석, 펜스 안의 `<!--`, 한 줄 블록 주석의 닫힘, HTML 블록의 끝, 세는 쪽의 닫히지 않은 펜스, 목록 표지 펜스, 문단 속 주석의 비탐욕, `paths` 블록의 멈춤, 따옴표 여는 자리). 돌리는 법은 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/instruction_check_mutations.toml` | 일지 2026-09-29-04의 변이 줄과 PR #100 리뷰 반영 절 | 검사나 그 테스트를 고칠 때 |
