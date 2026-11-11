# delete-judge-paths-miss-protected-name: **지우는 도구에 보호 이름(`dev`)을 더하며 판정 길 하나(체크아웃되지 않은 브랜치)에만 검사를 넣어, `dev`를 체크아웃한 워크트리를 지우는 길이 셀프 리뷰와 반박을 지나 PR 직전 CodeRabbit에서 Major로 나왔다**(361의 11회차다)

**상태:** 열림
**어디로:** `tests/tools/test_tidy_checkouts.py`에 보호 이름(`PROTECTED_BRANCHES`의 값) × 판정 길(워크트리 `judge`, 체크아웃되지 않은 브랜치 `judge_branch`, `remove`, `remove-branch`)을 가로지르는 시험 하나. 보호 이름을 더하거나 길을 더하면 빠진 칸이 빨개지게 한다. 지우는 도구 항목(`.claude/rules/tools.md`)에 문장을 더하지 않는다
**승인:** 자체 승인 2026-11-12, 361의 11회차(442의 10회차 뒤), 일지 2026-11-12-0409-dev-base-tools.md. ADR 불필요

`tools/tidy_checkouts.py`의 `PROTECTED_BRANCHES`에 `dev`를 더한 앞 세션의 반박은 대소문자 입력(`Dev`)을 `_judge_branch_merged`에서 찾아 고쳤지만, 같은 이름 검사가 워크트리 판정 `judge`에는 없다는 것을 보지 못했다. dev→main 릴리스 PR은 머리 브랜치가 `dev`라 `merged`에 `dev`가 채워지고, 깨끗한 `dev` 워크트리는 `지운다`로 나와 `remove`가 로컬 `dev` 이름까지 지웠을 것이다. `.claude/rules/tools.md`의 361 문장(같은 값을 견주는 다른 자리에도 그 입력을 넣어 본다)과 `hook_deletion_adversarial` 계기가 이미 있는데도 났다. 문장이 아니라 길 × 값의 곱을 시험이 강제하는 층으로 올린다. 이 세션은 `dev` 워크트리 한 칸만 시험으로 고쳤다(`test_반박_dev_를_체크아웃한_워크트리…`, 변이 199번).
