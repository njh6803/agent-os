# llm-local-scope-misread-for-comment-only-change: 주석만 고친 `src/agent_os/main.py`가 로컬 모델 시험의 범위 경로인데, 앞 세션이 "변경 경로에 LLM 호출 코드가 없다"며 건너뛴다고 적었다

**상태:** 열림
**어디로:** `tools/llm_local.py`(범위 경로와 `git diff --name-only <기준>...HEAD`를 견주어 겹치는 경로를 찍는 걸음. `run`을 `--yes` 없이 칠 때 함께 찍는 것이 가장 작다). 범위의 원천은 `docs/constitution/operations.md` LLM 테스트의 "범위"이고 그 문장은 바꾸지 않는다.
**승인:** 자체 승인 2026-11-28, 1회차, 일지 2026-11-28-0125-build-closes-frame-ancestors-and-start-fills-them.md. ADR 불필요

앞 세션은 PR의 변경 파일 마흔여 개를 보고 "변경 경로에 `tools/llm_local.py`·`tools/llm_local_server/`·LLM 호출 코드가 없다"며 로컬 모델 시험을 건너뛴다고 일지에 적었다. 범위는 `main.py`를 이름으로 들고, 이 PR은 `main.py`의 주석 두 줄을 고쳤다. 이어받은 세션이 경로 대조를 다시 해서 잡았고, 사용자에게 비용 확인을 받아 시험을 돌렸다(통과 4, A40 하나, 390.5초). 범위가 읽는 사람의 기억에 기대는 목록이라 큰 PR에서 한 줄이 빠진다. 경로 대조는 기계가 할 수 있다. 같은 사건이 되풀이되면 이 항목이 회차를 센다.
