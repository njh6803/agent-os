# 컨테이너 네트워크 예외 픽스처

`serve`, 위젯 관리 서버(`widget-admin serve`), 관리 화면, 위젯, 위젯 미리보기 페이지가 이미지 안의 명시적 설정이 있을 때만 `0.0.0.0`에 묶이고, 관리 화면의 상류가 그때만 `serve`를 받는다는 것을 두 언어의 시험이 같은 표로 고정하는 자리다(release-image 티켓 03, ADR 0056 결정 "루프백 규칙의 예외"). 다섯 프로세스가 같은 규칙을 따로 들고 있으므로(앱 사이 import는 층 경계가 막는다), 한 곳의 판정만 바뀌면 그 곳의 시험이 빨개지게 하는 것이 이 표의 일이다. 선례는 `tests/fixtures/site_file/`이다.

읽는 시험은 `tests/test_main.py`(`serve`의 `--host`), `tests/widget_admin/test_loopback.py`(`widget-admin serve`의 `--host`. 진단의 까닭 줄 하나만 `serve`와 다르다), `web/apps/admin/tools/loopback.test.ts`·`start.test.ts`·`start.spawn.test.ts`·`next.config.test.ts`(관리 화면의 `--hostname`과 상류), `web/apps/widget/tools/start.test.ts`·`start.spawn.test.ts`(위젯의 `--hostname`), `web/apps/portal/server/config.test.ts`(위젯 미리보기 페이지의 `portal.host`)다. 파이썬은 `binding`만 읽고, 상류는 TS만 가진다.

## 입력

- `marker`: 표지 파일 `/etc/agent-os/image`가 있는가. 판정은 이 값을 인자로 받는 순수 함수이고, 표지 파일을 실제로 읽는 길은 이미지를 띄우는 시험(티켓 07·08·09)이 본다.
- `env`: 환경 변수 `AGENT_OS_CONTAINER_NETWORK`의 값. `null`은 없음이다.
- `verdicts`: 호스트 → 판정의 종류. `binding`은 듣는 주소(`--host`, `--hostname`, `portal.host`)를, `upstream`은 관리 화면의 상류 `AGENT_OS_UPSTREAM`의 호스트를 뜻한다.

## 판정의 종류

예외는 `marker`가 참이고 `env`가 `"1"`일 때만 켜진다. 환경 변수가 없거나 빈 값이면 꺼진 것이고, 그 밖의 값(`true`, `0` 등)은 호스트와 상관없이 구성 오류다.

| 종류 | 뜻 |
|---|---|
| `ok` | 받는다 |
| `loopback` | 거부한다. 예외가 꺼져 있고 아래 두 안내가 걸리지 않는 기본 진단이다. 지금의 루프백 진단 그대로다 |
| `env-hint` | 거부한다. 표지 파일만 있고 환경 변수가 없는데 예외로 열리는 주소(`binding`은 `0.0.0.0`, `upstream`은 `serve`)를 받았다. 기본 진단에 환경 변수를 알리는 한 줄이 더 있다 |
| `outside-image` | 거부한다. 환경 변수는 `"1"`인데 표지 파일이 없고 예외로 열리는 주소를 받았다. 이미지 밖에서는 켜지지 않는다고 말한다 |
| `container` | 거부한다. 예외가 켜졌는데 열리는 주소가 아닌 주소(다른 IPv4, `::`, 이름)를 받았다. 받는 주소에 `0.0.0.0`(상류는 `serve`)이 더해졌다고 말한다 |
| `invalid-env` | 거부한다. 환경 변수의 값이 `1`도 빈 값도 아니다. 진단은 받은 값을 싣고 호스트는 말하지 않는다 |

`localhost`는 `::1`로도 풀릴 수 있어 루프백이라는 보장이 없으므로 거부한다(`serve`의 선례). 환경 변수가 `"1"`인데 표지 파일이 없어도 호스트가 루프백이면 받는다. 개발 PC에서 그 변수를 내보내도 아무것도 달라지지 않는다.

## 진단의 신호

`binding_signals`와 `upstream_signals`가 종류마다 진단에 있어야 할 글(`contains`)과 없어야 할 글(`excludes`)을 든다. `{host}`는 받은 호스트로, `{env}`는 받은 환경 변수의 값으로 바꾼다. 앞의 글(`--host`, `--hostname`, `portal.host`)은 프로세스마다 달라서 신호에 넣지 않았다. 같은 글이어야 할 곳은 표의 신호가 든 자리이고, 문장 전체가 같아야 한다는 뜻은 아니다.
