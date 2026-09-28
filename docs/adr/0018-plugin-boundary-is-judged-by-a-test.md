---
status: accepted
date: 2026-09-28
---

# 원칙 IV의 플러그인 경계는 import-linter가 아니라 테스트가 판정한다

헌법 원칙 IV는 "플러그인은 `agent_os.sdk`만 import한다. … import-linter가 판정한다"고 적었다. **그 문장의 플러그인 절은 거짓이다.** import-linter는 `root_packages`(`agent_os`) 안의 그래프만 만들고, 플러그인은 `plugins/` 아래에 `__init__.py` 없이 살며 런타임이 `agent_os_plugins.<name>.<module>`이라는 합성 이름으로 로드한다(ADR 0003). 2026-09-28 하네스 감사에서 `lint-imports`가 분석하는 파일(그날 69개)을 세어 보니 플러그인은 0개였다. 그래서 다음 세션이 플러그인에 `from agent_os.core.run import …`을 넣어도 검사 여섯이 전부 초록이고, 헌법은 게이트가 있다고 말하므로 리뷰조차 그 자리를 보지 않는다. 원칙 III에서 ADR 0013이 고친 것과 같은 모양(판정자 주장이 사실보다 넓다)이다. **`tests/test_plugins_boundary.py` 하나를 판정자로 두고, 원칙 IV의 문장을 그 사실에 맞춘다.** 테스트는 `plugins/**/*.py`를 AST로 읽어 `agent_os.*` import가 `agent_os.sdk`와 그 하위뿐인지 단언하고, 파일을 하나도 읽지 않으면 실패한다.

2026-09-28 승인. 테스트는 이 사실을 재는 것이라 먼저 들어갔고, 헌법 문장은 같은 PR(`chore/harness-audit`)에서 고쳤다.

## Considered Options

- **`root_packages`에 `plugins`를 더한다.** 도구 하나로 판정자가 하나가 된다. 그러나 `plugins/`는 패키지가 아니고(`__init__.py` 없음, 디렉터리마다 `plugin.toml`), import-linter가 요구하는 임포트 가능한 루트 패키지가 아니다. 패키지로 만들면 합성 모듈명으로 로드하는 설계(ADR 0003, `sys.path`를 건드리지 않는다)와 어긋난다. 거부했다.
- **grep 한 줄.** `from agent_os\.(core|adapters|channel|admin|http)`를 플러그인에서 찾는다. 싸지만 `import agent_os.core`, `from agent_os import core`, 문자열 안의 문구를 다르게 다뤄야 하고 판정자가 grep이면 ADR 0013이 거부한 이유가 그대로 걸린다. 거부했다.
- **리뷰에 맡긴다(지금까지의 상태).** `claude-code-review.yml`의 경계 항목은 "import-linter가 못 보는 것"으로 셋(서드파티 타입의 누출, `sdk` 계약 변경의 동반 수정, 포트 다섯 밖의 새 포트)을 들고 플러그인은 없다. 헌법이 판정자가 있다고 적어 리뷰어도 그 자리를 보지 않는다. 거부했다.

## Consequences

- **`principles.md`의 원칙 IV 문장이 바뀐다.** "import-linter가 판정한다"가 "플러그인 경계는 `tests/test_plugins_boundary.py`가, 나머지는 import-linter가 판정한다"가 된다(2.5.2). 초안은 import-linter의 몫을 "층 경계와 어댑터·프로바이더 금지"로 열거했는데, 그 목록은 같은 PR에서 더한 core의 파일시스템·DB 계약을 빠뜨린다 — 목록으로 건 규칙은 목록 밖을 놓치므로(대기열 20의 12회차) "나머지"로 적었다. 원칙의 내용(플러그인은 sdk만)은 바뀌지 않으므로 semver의 patch다.
- **판정은 AST다.** `Import`와 `ImportFrom`의 모듈 이름만 본다. `from agent_os import sdk`는 `agent_os.sdk`로 센다. 못 보는 것: `importlib.import_module("agent_os.core")` 같은 동적 import, `plugins/` 밖에서 로드되는 플러그인. 둘 다 지금 없고, 생기면 이 ADR의 이력에 쌓는다.
- **읽은 파일이 0이면 실패한다.** 위반 0이 "플러그인이 없어서"인지 "정말 없어서"인지 가르는 장치다(`tests/sdk/test_manifest.py`와 같은 모양).
- **같은 모양이 원칙 II에도 있었다.** "환경 부재로 skip된 테스트는 초록이 아니다"에 장치가 없었고 `operations.md`가 "CI에서는 에러로 만든다"고 적었다. `tests/conftest.py`가 skip을 세션 실패로 만드는 것을 같은 PR에 넣었다. 원칙 II의 문장은 판정자를 들지 않으므로 헌법 문구는 그대로다.
- **core의 "DB, 구체 파일 경로" 절에도 계약이 없었다.** `pathlib`·`os`·`sqlite3` 금지 계약을 import-linter에 더했다. 문장이 이미 "import-linter가 판정한다"이므로 헌법 수정은 없다.
