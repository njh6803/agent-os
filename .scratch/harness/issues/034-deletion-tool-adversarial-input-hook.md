# 034: 지우는 호출을 쓰는 편집에 커밋 전 판정을 깨는 입력으로 반박하라는 알림을 넣는다

**What to build:** `.claude/rules/tools.md`의 "지우거나 덮어쓰는 도구" 항목은 지우는 도구를 커밋하기 전에 임시 저장소에서 판정을 깨려는 입력(커밋하지 않은 파일, 윈도 경로 정규화가 바꾸는 이름, 지우는 자리 안의 링크)으로 반박하라고 적는다. 그런데 `tools/tidy_checkouts.py`, `tools/canary.py`, `web/tools/judge-trees.ts`에서 이 항목을 읽은 뒤에도 반박 시험이 그런 입력을 넣지 않아, 지우는 길이 셀프 리뷰를 지나 PR 직전 `bug-perf-review`에서야 나왔다(대기열 361의 열 번째 회차이자 442의 여덟 번째 회차). 그 항목은 `tools/`나 `tests/tools/`의 파일을 Read로 열 때만 실리므로, 지우는 호출을 막 써 넣은 순간에는 모델이 그 문장을 보고 있다는 보장이 없다.

그래서 쓰는 순간에 알리는 계기 훅을 더한다(`.claude/rules/tools.md`의 계기 훅·막는 훅 가름: 막지 않는다. 지우는 호출이 임시 폴더만 지우는 정리인지, 사람이 지은 폴더에 닿는지는 모델이 가른다). `tools/`나 `web/tools/` 아래 파일(시험 파일은 뺀다)을 Write·Edit로 고쳐 지우는 호출(`rmSync`, `shutil.rmtree`, `unlink`, `git worktree remove` 등)이 든 줄을 더하면, 세션·에이전트마다 한 번 다섯 입력을 짚는 문장을 컨텍스트에 넣는다. 다섯은 그 항목과 대기열 442가 든 것이다. 같은 꼴 이름의 사람 폴더와 그 안의 커밋하지 않은 파일, 윈도 경로 정규화가 바꾸는 이름, 지우는 자리 안의 링크, MAX_PATH를 넘는 경로, 찾은 입력을 같은 값을 견주는 다른 자리에도 넣어 보기다. 대상 경로, 호출 목록, 문장은 이 티켓이 정한다.

**대기열:** 442

**Status:** done

## 수용 기준

- [x] `tools/hook_deletion_adversarial.py`(PostToolUse Write|Edit)가 `tools/`·`web/tools/` 아래 파일(`tests/tools/`와 시험 파일은 제외)에 더한 줄이 지우는 호출을 들면, 다섯 입력을 짚는 문장을 세션·에이전트마다 한 번 낸다
- [x] 독스트링이 왜, 판정(대상 경로·호출 목록), 한 번, 못 보는 것을 적고, 못 보는 것마다 시험 하나가 고정한다. 놓치는 것은 지나간다고, 잘못 알리는 것은 알린다고 단언한다
- [x] `.claude/settings.json`에 래퍼 모양으로 등록하고(첫 `Write|Edit` 묶음), `tests/tools/`에 순수 함수와 표지 시험, `tools/hook_payloads.toml`에 발동 하나와 침묵 하나(실제 입력)를 더해 `tools/run_hooks.py`가 실행을 확인한다
- [x] `.claude/rules/tools.md`의 훅별 시간 항목에 새 훅의 문장을 더하고, 규칙이 새 세션에 실린 것을 카나리아로 본다
- [x] 판정을 하나씩 깨는 변이 표(`.scratch/harness/probes/deletion_adversarial_hook_mutations.toml`)가 `tools/mutate.py`에서 모두 빨갛고, 프로브 `README.md`에 한 줄이 있다
- [x] 검증 명령이 모두 초록이다

## Comments
