# 007: `.env` 읽기 훅의 Grep 도구 glob 판정을 실제 rg와 맞대는 시험을 두고 어긋남을 고친다

**What to build:** `tools/hook_env_read.py`의 `deny_reason_for_grep_tool`이 Grep 도구의 glob이 `.env`에 닿는지 판정할 때, 하류인 rg가 그 glob을 읽는 방식과 같게 읽는지를 실제 rg를 띄워 맞대는 시험을 둔다. gitignore 된 가짜 `.env`가 든 임시 폴더에서 glob 사례 표의 glob마다 rg가 `.env`를 내는지와 훅의 판정이 같은지 본다. 먼저 Grep 도구가 rg에 넘기는 인자(숨김 파일, gitignore)와 CI에 rg가 있는지를 확인하고, rg가 없으면 skip이 아니라 실패로 둔다(`.claude/rules/tests.md`). 시험이 찾은 어긋남을 고친다(대기열 422의 Grep 도구 `{.env}`는 PR #349에서 이미 고쳤고, Bash의 `rg -g '{.env}'`는 아직 지나간다). 같은 값을 견주는 Bash의 rg 판정(`-g`)도 같은 표로 맞댄다. 시험이 rg를 전제하게 되므로 그 전제를 ADR 0038로 남긴다(사용자 결정, 일지 2026-10-23-29).

**대기열:** 422

**Status:** done

## 수용 기준

- [x] Grep 도구가 rg에 넘기는 인자(숨김 파일, gitignore, glob 옵션)를 무엇으로 알았는지(손, 코드 읽기, 문서) 밝혀 시험의 머리 주석에 적는다
- [x] CI와 로컬에서 시험이 부를 rg를 찾는 길을 정하고, 찾지 못하면 실패한다(PATH의 `rg`, 없으면 `claude` 실행 파일을 실행 이름 `rg`로. CI는 apt로 깐다)
- [x] glob 사례 표의 glob마다 실제 rg의 결과와 `deny_reason_for_grep_tool`의 판정이 같은지 보는 시험이 있고, 고치기 전 판에서 빨간 사례를 본다(셀프 리뷰를 반영한 표를 고치기 전 판 975bf04c에 통째로 돌려주는 `grep_tool_globs` 껍데기를 붙여 대면 29개가 빨갛다. 처음 적은 28은 다시 셀 수 없었다)
- [x] 어긋난 판정을 고치고, 모듈 독스트링의 못 보는 것과 `_brace_branches` 독스트링을 맞춘다
- [x] ADR 0038을 셀프 리뷰를 반영한 뒤 보여 주고 승인받는다(2026-10-23 승인)
- [x] 검증 명령이 모두 초록이다
