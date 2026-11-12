# 02: 인자가 깨진 도구 호출 — 모델이 낸 도구 호출의 인자가 올바른 JSON이 아니면 실행이 원인 `model_call`의 실패로 끝난다

**What to build:** 운영자가 모델과 서버 옵션의 조합이 맞지 않아 모델이 도구 호출의 인자를 깨진 JSON으로 냈을 때, 실행이 빈 최종 답으로 끝나지 않고 원인 `model_call`의 `run_failed`로 끝난다. 실패 내용은 `ValueError: 모델이 낸 도구 호출의 인자가 올바른 JSON 이 아니다: add`처럼 어느 도구였는지를 들고, 깨진 인자의 글은 싣지 않는다(스토리 10·11). 멀쩡한 호출과 깨진 호출이 섞인 응답도 같은 실패이고, 이름이 빈 깨진 호출은 `(이름 없음)`으로 적힌다. 그 모델 호출의 `llm_called`는 남지 않고 도구도 불리지 않는다. 지금은 라이브러리가 그런 호출을 예외 없이 메시지의 `invalid_tool_calls`로 옮기고 `reply_from`이 `tool_calls`만 읽어, 루프가 그 응답을 빈 최종 답으로 받는다. Anthropic 모델의 실행은 바뀌지 않는다. `ChatAnthropic`은 비스트리밍 응답에서 그 칸을 채우지 않는다(명세 검토가 langchain-anthropic 1.7.2를 읽었다).

01과 나란히 돈다. 계약에 기대지 않고 core의 `reply_from` 하나에 선다. 어댑터 없이 서므로 시험은 지금 core 시험의 가짜 모델이 깨진 호출이 든 메시지를 내게 해서 본다. 실제 라이브러리와 어댑터를 지나 그 메시지가 만들어지는 길 전체는 05가 둘로 본다. 어댑터의 응답 시험이 라이브러리가 깨진 인자를 `invalid_tool_calls`에 그 도구 이름으로 넣는 모양을 고정하고, CLI 시험이 가짜 모델 서버의 첫 응답을 깨진 `add` 호출로 바꿔 이 실패를 본다. 01과는 `tests/core/test_model.py`를 함께 고칠 수 있다(01은 import 한 줄. 명세의 어림). 나중에 병합하는 쪽이 개발 브랜치를 합쳐 푼다. 이 티켓이 고치는 `core/model.py`는 로컬 모델 시험의 병합 조건 범위에 들지만, 돌릴 시험이 아직 없어 조건이 붙지 않는다(ADR 0058 결정 "첫 적용"). 05의 로컬 모델 시험이 이 변경까지 지난다.

근거는 `.scratch/local-model/spec.md`의 "인자가 깨진 도구 호출"과 그 2026-11-12 명세 검토 주석, "고칠 자리의 묶음"의 B 줄과 그 뒤 문단, Testing Decisions의 "core(B)"다. 측정은 `.scratch/local-model/probes/openai_compat.py`의 사례 `tool_args_broken`, `tool_args_broken_empty_name`, `tool_args_mixed`, `tool_args_empty_string`, `tool_args_null`, `tool_args_valid_empty_name`, `tool_call_missing_id`와 그 `README.md`이고 다시 돌리지 않는다. 앞선 결정은 ADR 0057의 결정 "인자가 깨진 도구 호출"과 범위 밖의 "깨진 도구 호출을 모델에 되돌려 다시 시키는 것", "새 실패 원인"이다. 실패 원인의 자리는 `.claude/rules/core.md`의 실패 정책이다.

**Blocked by:** None (can start immediately)

**Status:** done

### 확인

- [x] 확인하는 자리는 `core/model.py`의 `reply_from`이다. 메시지의 `invalid_tool_calls`가 비어 있지 않으면 `ValueError("모델이 낸 도구 호출의 인자가 올바른 JSON 이 아니다: <이름들>")`을 던진다. `<이름들>`은 깨진 호출의 도구 이름을 응답의 순서대로 쉼표로 이은 것이고, 이름이 비었으면 `(이름 없음)`이다. 깨진 인자의 글과 라이브러리의 `error` 글은 싣지 않는다(뒤의 것도 받은 글을 싣는다). 도구 이름은 서버가 정한 값이라, 서버가 그 이름에 키 값을 실어 보내면 `run_failed`에 남는다. `reply_from`은 키를 모르고 스토리 10·11이 이름을 싣기를 요구하므로 이 티켓은 이름을 가리지 않는 한계로 둔다. 가리자는 요청이 오면 명세 "인자가 깨진 도구 호출"의 결정을 바꾸는 일이라 사용자에게 다시 묻는다
- [x] 멀쩡한 호출과 깨진 호출이 섞인 응답도 같은 실패다. 멀쩡한 것만 부르지 않는다
- [x] 확인은 `invalid_tool_calls`만 본다. 이름만 빈 멀쩡한 호출과 `id`가 없는 호출은 지금처럼 읽혀 루프로 간다(앞의 것은 루프가 연결에 없는 이름으로 `tool_called(ok=false)`를 모델에 돌려준다)
- [x] 확인은 제공사를 가리지 않는다. 제공사마다 같은 확인을 어댑터에 따로 두지 않는다
- [x] `_ask`가 `reply_from`을 `blamed("model_call")` 안에서 부르므로 원인은 `model_call`이고, 그 모델 호출의 `llm_called`는 쓰이지 않는다. 그 대가로 그 호출의 토큰 수가 트레이스에 남지 않는 것은 명세가 받아들였다. 새 실패 원인을 더하지 않는다

### 시험

- [x] core 시험이 명세 Testing Decisions의 "core(B)" 사례를 덮는다. 가짜 모델 소스(`tests/fake_models.py`의 `FakeModels`)에 `invalid_tool_calls`가 든 응답을 내는 가짜 모델을 주면 실행이 원인 `model_call`의 `run_failed`로 끝나고, 메시지가 도구 이름을 들며 깨진 인자의 글을 싣지 않고, 그 호출의 `llm_called`와 `tool_called`가 트레이스에 없다. 섞인 응답과 이름이 빈 깨진 호출도 같은 것을 본다
- [x] 이름만 빈 멀쩡한 호출이 이 확인에 걸리지 않는 것을 본다

### 문서

- [x] `.claude/rules/core.md`의 실패 정책에 깨진 도구 호출 한 줄을 더한다(자리는 `reply_from`이고 원인은 `model_call`, 문구는 도구 이름만 든다)
- [x] rules를 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`). 고친 rules는 새 세션에서 불러 본다(작업 규약 3)

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 위 core 시험이다. 지금은 빈 최종 답의 `run_finished`로 끝난다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 `-m llm`을 친다. `reply_from`은 실제 모델의 모든 응답이 지나는 자리다
