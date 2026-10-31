# model-plugin 프로브

명세가 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/model-plugin/spec.md`다. ADR 0040이 든 수(`ChatAnthropic.model_fields` 36개, `temperature`의 수용과 거부)는 설계 세션이 `uv run python -c`로 손으로 본 것이다. 그 가운데 `temperature`의 수용과 거부는 `manifest_fields.py`가 다시 쟀고, 36개는 어느 프로브도 다시 세지 않았다(손으로 본 수 그대로다).

## 돌리는 법

저장소 루트에서 저장소 `.venv`로 돈다(Windows, Git Bash). 둘 다 네트워크에 닿지 않고 API 키가 필요 없다. `build_without_key.py`는 프로세스 안에서 `ANTHROPIC_API_KEY`와 기본 주소 환경변수 둘을 걷어내므로 `.env`를 싣지 않고 돈다. 종료 코드 0은 모든 회차가 측정으로 섰다는 뜻이고, 결론은 출력의 "결과:" 줄로 읽는다(`tools/probe_kit.py`의 `Rounds`).

```sh
PYTHONUTF8=1 uv run python .scratch/model-plugin/probes/manifest_fields.py
PYTHONUTF8=1 uv run python .scratch/model-plugin/probes/build_without_key.py
```

## 결과 (2026-10-31)

아래의 수는 두 프로브가 다시 내는 것이다. 전제로 적은 라이브러리 안쪽의 모양(`cached_property`, `SecretStr` 기본값)은 설치된 판의 코드를 읽은 것이고, 각 프로브의 독스트링이 줄 번호를 든다.

### `manifest_fields.py` — 측정 29회차, 측정 아님 0

- **받기와 거부.** 받은 사례 7은 모두 기대한 값과 타입이다. TOML의 정수 `0`·`1`은 `temperature`에서 실수 `0.0`·`1.0`으로 받힌다. 거부한 사례 19는 모두 기대한 표지로 거부됐다(`provider` 모르는 값 `enum`, `model_id` 빈 글 `string_too_short`·숫자 `string_type`, `max_tokens` 0 `greater_than_equal`·`2.0`·`true`·`"16"` `int_type`, `temperature` 1.5 `less_than_equal`·-0.1 `greater_than_equal`·`"0.5"`·`true` `float_type`, 모르는 칸 `extra_forbidden`, 에이전트 `model` 패턴 위반 `string_pattern_mismatch`, 종류에 맞지 않는 칸은 검증자의 `ValueError`). 해석은 pydantic 2.13.5의 엄격 검증이 ADR 0040 Consequences "모델 매니페스트의 모양"의 규칙을 그대로 낸다는 것이다. 갈래: "거부됐다"가 다른 까닭(모르는 칸, 빠진 공통 칸, 오류 여럿)인 해석은 오류가 하나이고 그 `type`이 기대한 것일 때만 측정으로 세어 갈랐다.
- **직렬화 JSON 스키마.** 다섯 칸(`model`, `provider`, `model_id`, `max_tokens`, `temperature`)이 모두 `required`에 들고 `null`을 허락하며, `provider`는 `$defs`의 `ModelProvider`를 가리킨다. 그래서 `openapi.json`에서 생성한 TS 타입은 다섯 칸을 `… | null`의 필수로 받을 것이고, 관리 화면의 스토리·테스트에 있는 매니페스트 리터럴은 지금 `conversation_limit: null`을 적는 것처럼(`web/apps/admin`을 grep으로 손으로 봤다) 다섯 칸의 `null`을 적어야 할 것이다. 스키마의 `required`와 `null` 허락과 이름 있는 정의는 쟀고, 생성기를 돌리지 않았으니 TS 리터럴이 깨진다는 것은 어림이다.
- **칸 이름.** 기본 설정에서 `model_id`·`model`을 가진 클래스를 만들 때 pydantic의 보호 이름 공간 경고가 없다. 양성 대조로 `protected_namespaces=("model_",)`를 준 같은 클래스는 경고 하나(`Field 'model_id' in 'Manifest' conflicts with protected namespace 'model_'`)를 낸다. 잡는 길이 살아 있는 채로 기본 설정이 경고를 내지 않으니, sdk가 `protected_namespaces`를 손댈 필요가 없다.

### `build_without_key.py` — 측정 14회차, 측정 아님 0

- **만들기 10회**(키 없음 5, 아무도 듣지 않는 로컬 주소 5). 중앙 0.1ms, 최대 0.3ms이고(명세 세션의 두 실행. 앞 세션의 두 판은 최대 0.2ms였다) `_client`·`_async_client`를 만들지 않았다(인스턴스 `__dict__`에 없다). 결과를 본 뒤 표지를 한 번 바꿨다. 첫 판의 표지는 `anthropic_api_key is None`이었는데 첫 실행이 만들기 10회차를 모두 측정 아님으로 세어(값이 빈 `SecretStr`이었다), 1.7.2의 기본값이 `SecretStr("")`인 것을 코드에서 읽고(`chat_models.py` 1136줄) 표지를 "빈 글"로 바꿨다. 클라이언트를 만들지 않았다는 결과와 시간은 두 판에서 같았다.
- **양성 대조 `invoke_dead_base_url` 2회.** 자리 표시 키와 `max_retries=0`으로 그 주소에 `ainvoke`하면 `anthropic.APIConnectionError`로 끝난다(2.0~2.3초. 이 시간의 까닭은 재지 않았다). 주소가 실제로 쓰이고 네트워크는 호출에서 탄다는 표지다. 그리고 호출 뒤에는 `_async_client`가 `__dict__`에 있다(2회 모두, 탐침이 찍었다). 만들기 회차의 "클라이언트 안 만듦"을 읽는 `__dict__` 탐지가 만들어진 클라이언트를 실제로 잡는다는 양성 대조이고, 셀프 리뷰가 이 대조가 없는 것을 짚어 더했다(회차 수는 14 그대로다).
- **`invoke_no_key` 2회.** 키 없이 `ainvoke`하면 2.5~2.9ms에 `TypeError: Anthropic authentication failed: no API key or authorization credentials were provided. Set the ANTHROPIC_API_KEY environment variable, pass api_key=... to Chat…`로 끝난다. 네트워크에 닿기 전이다(위 양성 대조의 접속 오류가 2초 걸린 것과 견준다).
- 해석은 둘이다. 모델 객체를 어댑터와 같은 인자로 만드는 일은 키도 네트워크도 요구하지 않고 실행마다 만들어도 비용이 1ms 아래(중앙 0.1ms)라는 것, 그리고 키 없음은 만들 때가 아니라 첫 호출에서 langchain-anthropic의 `TypeError`로 드러난다는 것이다. 갈래: "만들기가 네트워크를 안 탄다"와 "이 프로브가 네트워크를 보지 못한다"는 양성 대조가 가른다. 측정이 가는 범위는 설치된 판(아래 표)에서 어댑터의 factory와 같은 인자에 `temperature`를 더한 것까지다. 런타임이 `bind_tools`로 묶은 모델을 부르는 길(`core/loop.py`를 읽었다)의 묶기 자체는 재지 않았다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `manifest_fields.py` | sdk `PluginManifest`와 같은 설정의 시제품에 모델 칸 넷과 에이전트 `model` 칸을 더해, TOML 사례 26개의 받기·거부와 그 표지(pydantic 오류 `type`·검증자 문구), 직렬화 JSON 스키마의 `required`·`null`·이름 있는 정의, 칸 이름의 보호 이름 공간 경고(양성 대조 포함) | `spec.md`의 "모델 매니페스트의 칸", "계약", Testing Decisions | 위 명령. 1초 안팎 | pydantic 2.13.5, Python 3.12.10, 2026-10-31 |
| `build_without_key.py` | `ChatAnthropic`을 어댑터와 같은 인자로 키 없이·죽은 주소로 만들 때 걸리는 시간과 클라이언트를 만드는지, 죽은 주소로의 호출(양성 대조)과 키 없는 호출이 어떤 예외로 끝나는지 | `spec.md`의 "모델 만들기는 실행마다", "API 키", Testing Decisions | 위 명령. 네트워크 없음, 10초 안팎 | langchain-anthropic 1.7.2, anthropic 1.7.0, Python 3.12.10, Windows 10, 2026-10-31 |
| `prepare_mutations.toml` | `_prepare`의 모델 고르기·꺼짐 판정·만들기 자리가 빨강을 볼 수 있는지(변이 3. 에이전트가 고른 모델을 무시, 만들기를 import 앞으로 당김, 꺼진 모델을 기본 모델의 이름으로 봄) | 티켓 04의 "빨강을 먼저 본다" | `uv run python tools/mutate.py .scratch/model-plugin/probes/prepare_mutations.toml`. 수 초 | Python 3.12.10, Windows 10, 2026-11-01 |
| `startup_check_mutations.toml` | `main.py`의 시작 때 확인(`_model_problem`)이 꺼진 기본 모델을 막으면 구현 전부터 초록이던 "꺼진 기본 모델은 `serve`의 시작을 막지 않는다"가 빨강을 보는지(변이 1) | 티켓 05의 "꺼진 기본 모델은 시작을 막지 않는다" | `uv run python tools/mutate.py .scratch/model-plugin/probes/startup_check_mutations.toml`. 수 초 | Python 3.12.10, Windows 10, 2026-11-01 |
