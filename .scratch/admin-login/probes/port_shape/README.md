# port_shape: 포트를 가져오지 않는 어댑터가 타입 검사에서 그 포트를 만족하는가

admin-login의 설계(ADR 0062 결정 "경로와 층")는 운영자 계정의 포트를 `agent_os.http`가 선언하고 PostgreSQL 구현을 `agent_os.adapters`가 든다고 정한다. 그런데 어댑터 층은 `agent_os.http`를 import하지 못한다(원칙 IV, ADR 0016, `pyproject.toml`의 금지 계약 "adapters are not an HTTP surface"). 두 결정이 함께 서려면 어댑터가 포트와 그 포트가 주고받는 값의 타입을 가져오지 않고도 타입 검사가 두 쪽의 모양을 맞대야 한다. 이 프로브는 그 모양 하나를 작은 모듈 둘로 흉내 내 잰다. 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `http_side.py` | `agent_os.http`의 자리. 포트(`AccountStore`)와 포트가 돌려주는 줄(`AccountRow`), 받는 값(`NewAccount`)을 Protocol로 선언하고, 포트를 쓰는 함수 하나를 둔다 |
| `adapter_side.py` | `agent_os.adapters`의 자리. `http_side`를 가져오지 않는다. 줄은 자기 `frozen` 데이터클래스로, 받는 값은 자기 Protocol로 적고 포트의 메서드 셋을 같은 시그니처로 낸다 |
| `assemble.py` | 조립하는 자리(`server`, `main`). 두 쪽을 함께 가져오는 유일한 모듈이고, 어댑터를 포트 자리에 넘긴다 |
| `adapter_drift.py`, `assemble_drift_row.py`, `assemble_drift_arg.py` | 대조군. 포트에서 어긋난 어댑터 둘(돌려주는 줄에 칸 하나가 없다, `find`가 이름을 `bytes`로 받는다)을 포트 자리에 넘긴다 |
| `control_checks.py` | 양성 대조. pyright가 strict로 분석한다는 표지와 타입 우회 검사가 듣는다는 표지를 낸다 |
| `run.py` | 측정. 회차의 셈은 `tools/probe_kit.py`의 `Rounds`다 |
| `pyrightconfig.json` | 이 폴더를 strict, 파이썬 3.12로 본다 |

## 다시 돌리기

저장소 루트에서 친다. 네트워크와 Docker를 쓰지 않고 수 초다.

```bash
uv run python .scratch/admin-login/probes/port_shape/run.py
```

측정이 아닌 회차가 하나라도 있으면 종료 코드가 1이다.

## 잰 판

pyright 1.1.414(저장소 잠금의 판, 프로브가 찍는다), 파이썬 3.12.10(`uv run python --version`을 손으로 봤다), Windows 10. 2026-11-15에 두 번 돌렸고 두 번 모두 아래와 같았다.

## 결과

측정 12회차, 측정 아님 0회차, 종료 코드 0이다(프로브가 다시 낸다).

1. pyright는 이 폴더의 파이썬 파일 8개를 모두 분석했고(`filesAnalyzed 8/8`), 양성 대조에서 strict에서만 나는 `reportMissingParameterType`이 났다.
2. `http_side.py`, `adapter_side.py`, `assemble.py`의 오류는 각각 0이었다. 곧 포트 모듈을 가져오지 않은 어댑터를 조립하는 자리에서 포트 자리에 넘긴 호출이 strict를 지났다.
3. 어긋난 어댑터를 넘긴 두 파일에서는 각각 `reportArgumentType` 하나가 났다. 돌려주는 줄에 칸 하나가 없는 어긋남과 인자의 타입이 다른 어긋남을 조립하는 자리의 타입 검사가 잡았다. 이 규칙은 가져오기가 풀려 두 쪽의 모양을 실제로 맞댔을 때 나는 것이다. 가져오기가 풀리지 않은 편집기의 진단에서는 같은 줄에 `reportUnknownArgumentType`이 났다(손으로 봤다).
4. `adapter_side.py`와 `adapter_drift.py`가 가져오는 모듈은 `__future__`, `dataclasses`, `datetime`, `typing`뿐이었다. AST 확인이 가져오기를 본다는 표지는 `assemble.py`에서 `http_side`가 잡히는 것이다.
5. 재는 세 파일에 타입 우회는 0건이었다(양성 대조에서는 `Any`, `cast`, 억제 주석 셋이 잡혔다).
6. `assemble.py`를 실제로 띄우면 포트를 쓰는 함수가 어댑터를 지나 `{"tier": "admin", "failures": 1}`을 냈다.

이 길이 치르는 값은 코드에서 보인다. 줄의 모양과 받는 값의 모양을 두 모듈이 따로 적는다(`http_side.py`의 `AccountRow`·`NewAccount`와 `adapter_side.py`의 `Row`·`Incoming`, 단계의 `Literal`도 두 번이다). 어댑터 모듈만 봐서는 어긋남이 드러나지 않고, 두 쪽을 함께 가져오는 자리가 있어야 타입 검사가 잡는다.

## 재지 못한 것

- 실제 `agent_os` 패키지와 import-linter를 돌리지 않았다. 금지 계약이 이 모양을 받는지는 어댑터가 포트 모듈을 가져오지 않는다는 AST 확인으로만 봤다.
- PostgreSQL과 드라이버의 타입을 쓰지 않았다. 어댑터는 사전에 담는다.
- 포트의 다른 모양은 재지 않았다. 비동기 메서드, 제네릭, 바꿀 수 있는 줄, 포트가 던지는 예외의 타입, 줄을 여럿 돌려주는 메서드가 그것이다.
- pyright의 다른 판과 다른 타입 검사기, 리눅스는 재지 않았다.
- 테스트 픽스처에 포트 타입을 적어 어긋남을 잡는 길(`.claude/rules/adapters.md`의 지금 규칙)은 돌려 보지 않았다. 조립하는 자리의 호출 하나로만 봤다.
