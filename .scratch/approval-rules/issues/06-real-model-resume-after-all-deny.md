# 06: 실제 모델 시험 — 멈춘 사이 모두 deny가 된 재개가 끝까지 간다

**What to build:** 운영자가 calc의 everything 도구를 묻게 두어 실행이 멈춘 뒤, 멈춘 사이 규칙 파일을 고쳐 그 도구를 모두 deny로 돌려도, 승인자가 승인한 재개가 실제 모델과 실제 CLI로 끝까지 간다(스토리 20). 재개는 지금 디스크의 규칙을 다시 읽어 멈춘 호출을 부르지 않고 `운영자가 거부했다: everything:<도구>`로 기록한 뒤, 도구 정의 없는 모델 호출로 이어져 `run_finished`로 끝난다. 명세의 프로브는 손으로 지은 대화로 도구 정의 없는 요청을 API가 받는다는 것을 쟀고(`.scratch/approval-rules/probes/README.md`), 실제 재개 길을 지나지 않았다. 이 시험이 그 바깥 증거다.

06은 04 뒤이고 05와 나란히 돈다. 05와 고치는 파일이 겹치지 않을 것이다(어림). 겹치면 뒤에 병합되는 쪽이 앞의 것을 합친다. 05가 먼저 병합돼도 이 시험은 그대로 초록이어야 한다. everything 서버의 매니페스트에는 `secret_args`가 없어 마스킹과 묻기의 충돌에 걸리지 않고, `[agents.calc]`의 줄은 calc의 `mcp`에 있는 서버를 가리켜 에이전트 표의 검사를 지나며, 멈춘 도구와 재개 때의 도구가 같은 서버라 서버의 대조도 지난다(코드와 매니페스트를 읽은 어림).

**병합 뒤의 틈은 없다.** 이 티켓은 행동을 바꾸지 않고 시험 하나만 더한다.

근거는 `.scratch/approval-rules/spec.md`의 "모두 deny인 재개"와 "실제 모델 시험 하나", "고칠 자리의 묶음"의 D 줄과 그 2026-11-06 명세 검토 주석, Testing Decisions의 "좋은 시험"이다. 측정은 `.scratch/approval-rules/probes/all_deny_resume_call.py`와 그 `README.md`이고 다시 돌리지 않는다. 앞선 결정은 ADR 0044의 2026-11-05 이력 "명세가 정한 것과 잰 것"(구현 티켓의 `-m llm` 시험 하나가 실제 재개로 다시 잰다)과 ADR 0009의 2026-11-05 이력(운영자의 deny가 재개의 결정을 이긴다)이다.

**Blocked by:** 04 (런타임이 규칙 파일을 도구 호출마다 집행한다 — 막고, 묻고, 그냥 부른다). 04의 저장소 `plugins/rules.toml`, `rules.toml`도 복사하는 `_copy_repo_plugins`, 재개의 규칙 다시 읽기와 운영자 deny 우선을 쓴다

**Status:** ready-for-agent

- [ ] **`tests/test_main.py`에 `-m llm` 시험 하나를 더한다.** 저장소 `plugins/`를 임시 루트에 복사하고(04가 고친 `_copy_repo_plugins`가 `rules.toml`도 옮긴다) 그 `rules.toml`을 `[agents.calc] ask = ["everything:*"]`로 바꿔 실제 CLI로 calc를 돌린다. 첫 도구 호출에서 멈추고 `run_paused.rule`이 `ask`, `server`가 `everything`인 것을 본다
- [ ] **멈춘 뒤 파일을 `[agents.calc] deny = ["everything:*"]`로 바꾸고 다른 프로세스에서 승인으로 재개한다.** 선례는 같은 파일의 `test_멈춘_실행은_그_프로세스가_끝난_뒤_다른_프로세스가_재개해_끝까지_간다`다
- [ ] **단언은 셋이다.** 트레이스의 끝이 `run_finished`이고, 재개 뒤의 `tool_called`가 `ok=false`·`rule="deny"`·내용 `운영자가 거부했다: everything:<도구>`이며, `run_failed`가 없다. 멈추는 자리를 보는 단언은 모델이 첫 호출로 `add`를 부르는 데 기대지 않고 어느 도구든 멈춘 것을 본다. 도구 이름은 결과이지 표지가 아니다
- [ ] **이 하나가 재개의 규칙 다시 읽기, 운영자 deny가 결정을 이기는 것, 도구 정의 없는 모델 호출을 API가 받는 것을 실제 길에서 함께 잰다.** 다른 모델이나 다른 날의 API가 도구 정의 없는 요청을 거부하면 결말은 지금 실패 정책대로 원인 `model_call`의 `run_failed`이고, 그때 이 시험의 빨강은 측정이 바뀌었다는 표지다. 시험을 고치지 않고 멈춰 보고한다(헌법 원칙 II)
- [ ] **나머지 `-m llm` 시험은 저장소의 예시 규칙 파일로 그대로 지나간다.** `-m llm` 시험의 수는 이 하나만 는다
- [ ] **환경이 없으면 skip이 아니라 실패다**(`.claude/rules/tests.md`). `ANTHROPIC_API_KEY`가 없으면 실패한다
- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 04가 병합된 main에서는 행동이 이미 있으므로, 단언 하나를 일부러 틀리게 두어 시험이 그 자리를 실제로 보는지 확인한 뒤 되돌린다. 무엇을 틀리게 두었는지와 그 빨강의 출력을 PR 본문에 적는다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 `uv run --env-file .env pytest -m llm`이다. 워크트리에서 쓸 `.env` 경로는 `docs/constitution/operations.md`의 LLM 테스트다
