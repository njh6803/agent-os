# skill-plugin 프로브

설계 세션(일지 2026-11-03-02)이 ADR 0041의 근거로 들고, 명세 세션(일지 2026-11-03-03)이 명세(`.scratch/skill-plugin/spec.md`)의 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 ADR 0041 Consequences의 "머리말은 PyYAML로 전체를 읽고 두 칸만 본다"와 명세의 절 넷(아래 표)이다.

## 돌리는 법

저장소 루트에서 저장소 `.venv`로 돈다(Windows, Git Bash). 네트워크에 닿지 않고 API 키가 필요 없다. 종료 코드 0은 모든 회차가 측정으로 섰다는 뜻이고, 결론은 출력의 "결과:" 줄로 읽는다(`tools/probe_kit.py`의 `Rounds`).

```sh
PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/yaml_frontmatter.py
PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/frontmatter_split.py
PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/frontmatter_values.py
```

## 결과 (2026-11-03)

아래의 수는 프로브가 다시 내는 것이다. PyYAML이 직접 의존성이 아니라 `langchain-core`의 전이 의존성이라는 전제는 `uv tree --invert --package pyyaml`로 손으로 본 것이고, 프로브는 설치된 판과 자리만 다시 낸다.

### `yaml_frontmatter.py` — 측정 8회차, 측정 아님 0

- **설치된 판.** `import yaml`이 site-packages의 pyyaml 6.0.3을 불러온다. ADR 0041은 이것을 `pyproject.toml`의 직접 의존성으로 올린다.
- **머리말 다섯 모양.** 접힌 여러 줄 설명(`description: >`), 그대로의 여러 줄 설명(`|`), `metadata` 맵, 표준 밖 키(`disable-model-invocation: true`), 따옴표 안의 콜론과 샵. 다섯 모두 `yaml.safe_load`가 `name`과 함께 기대한 값으로 읽었다. 접힌 설명은 줄이 공백으로 합쳐지고 끝에 개행 하나가 남고, 그대로의 설명은 줄 바꿈이 그대로 남으며, `metadata`는 문자열 맵, 표준 밖 키는 불리언 `True`로 풀린다.
- **양성 대조: 닫히지 않은 따옴표.** `description: "닫히지 않은`은 `ScannerError`(`yaml.YAMLError`의 하위)로 거부됐다. "읽힌다"가 아무 입력에나 참인 관찰이 아니라는 표지다.
- **저장소 스킬의 머리말.** `.claude/skills/*/SKILL.md` 18개를 같은 길로 읽어, 필수 두 칸(`name`, `description`)이 없는 파일은 0개이고 표준 밖 키 `disable-model-invocation`을 쓰는 파일은 5개(grill-me, implement, setup-matt-pocock-skills, to-spec, to-tickets)다. 인터뷰 때 Grep으로 본 다섯과 같다.
- 해석은 둘이다. 설치된 PyYAML이 Agent Skills 표준의 머리말 모양을 추가 처리 없이 그대로 읽으므로 두 줄짜리 자체 파서를 둘 까닭이 없다는 것, 그리고 표준 밖 키는 YAML 차원에서 막히지 않으니 "두 칸만 보고 나머지는 무시한다"는 규칙이 런타임의 선택이지 라이브러리의 제약이 아니라는 것이다. 갈래: "읽힌다"와 "무엇이든 읽어 준다"는 양성 대조의 거부가 가른다. 재지 않은 것: 머리말을 본문에서 떼는 자리(`---` 가르기)는 재지 않았고 명세가 정한다(저장소 스킬 회차의 `head_of`는 읽기 위한 가르기일 뿐이다). 표준의 다른 YAML 모양(앵커, 여러 문서, 탭 들여쓰기)과 Windows 줄 끝(`\r\n`)은 넣지 않았다(저장소 스킬 회차의 `read_text`는 텍스트 모드라 `\r\n`을 `\n`으로 바꿔 넘긴다. 파이썬 표준 동작이고 재지 않았다). 두 해석 가운데 "자체 파서를 둘 까닭이 없다"는 측정이 아니라 측정을 읽은 설계 판단이다. 저장소 스킬의 수 18은 이 탐침을 돌린 작업 트리(브랜치 `docs/skill-plugin-design`)의 것이다.

### `frontmatter_split.py` — 측정 26회차, 측정 아님 0 (명세 세션, 2026-11-03·04. 셋째 판)

- **양성 대조: 파일 전체를 YAML로 읽으면 거부.** `---`로 열고 닫은 머리말과 마크다운 본문을 `yaml.safe_load`에 그대로 넘기면 `ComposerError`다(둘째 `---`가 둘째 문서의 시작이라 "하나의 문서"가 아니다). 그래서 YAML에 넘기기 전에 머리말을 떼는 자리가 필요하다.
- **규칙 다섯 모양.** 명세가 정한 줄 단위 규칙(파일의 `split_front_matter`. 첫 줄이 `---` 그대로, 그 뒤 처음 나오는 `---` 그대로인 줄이 닫는 줄, 줄 끝 `\r` 하나는 뗀다, 본문은 닫는 줄의 줄 바꿈 뒤 글 그대로)이 LF, CRLF, 본문 안의 `---` 줄(본문에 남는다), 본문 없음(닫는 줄로 끝남), 닫는 줄 뒤 줄 바꿈 없음의 다섯에서 머리말을 `yaml.safe_load`가 기대한 두 칸으로 읽고 본문이 글자 그대로 기대한 것이었다. 글을 직접 넘긴 CRLF에서는 본문의 `\r\n`이 그대로 남는다(본문은 다듬지 않는다. 파일에서 읽는 길은 아래).
- **머리말 값 안의 `---`(줄 가운데).** `description: 가 --- 나`를 값 그대로 읽고 본문도 그대로다.
- **거부 다섯.** 닫는 줄 없음은 "머리말이 닫히지 않았다", BOM으로 시작·앞의 빈 줄·머리말 없이 본문뿐·첫 줄 끝의 `\r`이 둘(`---\r\r\n`)은 "머리말로 시작하지 않는다"의 `ValueError`다. `\r`은 정확히 하나만 떼므로 둘이면 표지 줄이 아니다.
- **빈 머리말.** `---\n---\n본문`은 규칙이 머리말 `''`을 내고 `yaml.safe_load('')`는 `None`이다. "맵이 아니다"로 거부할 자리다.
- **갈래: 참조 구현의 가르기.** Agent Skills 참조 구현 `skills-ref`의 `parser.py`(github `agentskills/agentskills` main. 2026-11-03에 내장 브라우저로 raw 원문을 읽었다)는 `content.split("---", 2)`로 가른다. 같은 입력 `description: 가 --- 나`에서 그 가르기는 머리말을 `가 `에서 끊어 YAML이 `{'name': 'pdf-processing', 'description': '가'}`를 낸다(셋째 판부터 회차가 끊긴 자리와 이 값을 함께 단언한다). 줄 단위 규칙은 위에서 값 그대로를 냈다. 두 규칙을 가르는 입력이고, 참조 구현이 더 느슨한 것이 아니라 더 틀린다. 참조 구현은 머리말 읽기에 PyYAML이 아니라 strictyaml을 쓴다(같은 원문. 둘째 판에서 읽었다). 이 회차는 가르기만 그 모양으로 흉내 내고 읽기는 PyYAML로 했다. 끊기는 자리는 가르기가 정하므로 읽는 라이브러리와 무관하다.
- **갈래: 머리말 안의 `---` 줄은 YAML이 거부(세 자리)와 그 대조.** 열 0의 `---` 줄이 설 수 있는 자리 셋을 넣었다. 큰따옴표 스칼라 안은 `ScannerError`, 블록 스칼라(`|`) 안과 평문 스칼라의 이어지는 줄은 `ComposerError`(그 줄부터 둘째 문서로 읽혀 "하나의 문서"가 아니다)이고 회차가 그 클래스를 단언한다. 셋 모두 `yaml.YAMLError`의 하위다. 대조로 같은 세 자리에서 `---` 줄만 뺀 모양(평문은 들여쓴 이어지는 줄이고, 거부 입력도 그 들여쓴 줄 앞에 `---` 줄을 둔 것이라 둘은 그 줄만 다르다. 둘째 판의 거부 입력은 들여쓰지 않아 쌍이 아니었고 셋째 판이 맞췄다)은 모두 받아들여져 `description`이 `앞 뒤`(큰따옴표·평문)와 `앞\n뒤\n`(블록)이다. 그래서 거부의 까닭은 그 줄이지 둘러싼 모양이 아니다. 까닭은 PyYAML 스캐너가 토큰을 읽기 전에 열 0의 `---` 뒤에 공백·탭·줄 바꿈·끝이 오면 문서 시작으로 보기 때문이다(설치된 6.0.3의 `yaml/scanner.py` `check_document_start`. 코드를 읽었다). 그래서 줄 단위 규칙이 닫는 줄로 삼는 `---` 줄이 유효한 머리말 안에 있을 수 없고, 규칙이 잃는 유효 입력이 없다.
- **파일에서 읽는 길.** 어댑터가 매니페스트를 읽는 길(`Path.read_text(encoding="utf-8")`. `adapters/filesystem.py`의 `_parse`, 코드를 읽었다)로 CRLF 파일을 읽으면 글에 `\r`이 없고(파이썬의 보편 줄 바꿈) 규칙이 LF 본문을 낸다. 같은 파일을 `read_bytes().decode("utf-8")`로 읽으면 `\r\n`이 남는다. 그래서 어댑터가 같은 길로 읽으면 CRLF 스킬 문서의 본문은 LF가 되고, 규칙의 `\r` 떼기는 글을 직접 넘기는 호출에서 쓰인다. BOM 파일은 `utf-8`로 읽으면 U+FEFF가 첫 글자로 남아 규칙이 "시작하지 않는다"로 거부한다. 대조로 BOM 뒤의 TOML(`schema_version = "1"`)은 `tomllib`이 `TOMLDecodeError`로 거부하므로 매니페스트도 BOM을 받지 않는다. 첫 줄 끝의 `\r`이 둘인 파일과 홀로 선 `\r`(옛 Mac)뿐인 파일은 같은 길이 `\r`을 모두 `\n`으로 바꿔(`---\r\r\n`은 `---\n\n`) 규칙이 받아들인다. 글을 직접 넘기면 둘 다 "머리말로 시작하지 않는다"로 거부된다(위 거부 다섯의 `\r` 둘과, 홀로 선 `\r` 글의 대조 회차). 그래서 그 둘의 거부는 어댑터 경로에서는 나지 않는다(셋째 판이 더했다).
- 해석은 하나다. 줄 단위 `---` 규칙이 표준의 머리말 모양을 모두 읽고 참조 구현의 글자 열 가르기보다 틀리는 입력이 적다. 갈래: "참조 구현과 같은 결과"와 "줄 규칙이 더 맞다"는 값 안의 `---` 회차가 가른다. 재지 않은 것: `utf-8-sig` 같은 다른 인코딩 이름으로 읽는 길(어댑터는 `utf-8`이다), 세 자리 밖에 `---` 줄이 설 자리(주석 줄은 `#`으로 시작해 `---` 그대로일 수 없다. 스캐너 코드로 보면 어느 자리든 같지만 재지 않았다), 구현 티켓이 sdk에 둘 함수가 이 파일의 함수와 같은지(그 티켓의 시험이 같은 사례로 잰다). 결과를 본 뒤 바꾼 것: 첫 판은 큰따옴표 스칼라 한 자리만 넣고 "따옴표 안이어도"로 적었는데, 명세가 그것을 "유효한 머리말 안에 있을 수 없다"로 넓혀 쓰므로 자리 둘을 더해 다시 쟀다. 둘째 판(셀프 리뷰 뒤)은 표지 줄의 `\r`을 `rstrip`으로 여럿 떼던 것을 하나만 떼게 고치고 그 거부 회차를 더했으며, 세 자리 회차가 클래스를 단언하게 하고 대조 셋을 더했고, 파일에서 읽는 길 셋(CRLF, BOM, 매니페스트의 BOM)을 더했다. 16회차에서 23회차가 됐다. 셋째 판(PR 직전 리뷰 뒤)은 평문 갈래의 쌍을 `---` 줄만 다르게 맞추고, 참조 구현 갈래가 YAML 결과 값까지 단언하게 했으며, `\r` 둘과 홀로 선 `\r`의 파일 회차 둘과 홀로 선 `\r` 글의 거부 대조를 더했다. 23회차에서 26회차가 됐다.

### `frontmatter_values.py` — 측정 28회차, 측정 아님 0 (명세 세션, 2026-11-03·04. 셋째 판)

- **설치된 판.** pydantic 2.13.5, pyyaml 6.0.3.
- **받는 셋.** 두 칸이 문자열인 머리말, 표준의 선택 칸 넷(`license`, `compatibility`, `metadata`, `allowed-tools`)과 제품별 키(`disable-model-invocation`)가 섞인 머리말(무시하고 두 칸만 든다), 접힌 여러 줄 설명. 모델은 파일의 `Frontmatter`(`strict=True`, `extra="ignore"`, `frozen=True`, `name`은 `PLUGIN_NAME_PATTERN`, `description`은 `min_length=1`에 공백뿐을 거부하는 검증자).
- **거부 열둘과 표지.** `name: 123`·`true`·`~`·`2026-11-03`(날짜)·`!!binary aGk=`(bytes)과 `description: [a, b]`는 `string_type`, `description: ''`은 `string_too_short`, 공백뿐인 `description`은 `value_error`, `name: PDF-Processing`과 `name: a`(한 글자)는 `string_pattern_mismatch`, 칸이 없으면 `missing`이다. 위치(`loc`)는 그 칸 이름이다. 시험은 이 표지로 실패의 까닭을 단언한다.
- **양성 대조: `ValidationError`의 `str`은 값을 싣는다.** `description: [sk-ant-probe-secret]`의 거부에서 `str(error)`에 그 값이 있고, `errors(include_url=False, include_context=False, include_input=False)`로 만든 문구 `string_type (description): Input should be a valid string`에는 없다. 어댑터의 매니페스트 문구 `_describe`와 같은 길이다.
- **양성 대조: `MarkedYAMLError`의 `str`은 원문 조각을 싣는다.** 닫히지 않은 따옴표 `extra: "sk-ant-probe-secret`의 `ScannerError`에서 `str(error)`에 그 값이 있고, 종류와 줄·칸만 든 문구 `ScannerError (줄 4, 칸 1)`에는 없다.
- **`problem_mark.line`은 넘긴 글 기준 0부터다.** 셋째 줄에 둔 `bad: a: b`의 `ScannerError`가 `line=2`, `column=6`이다. 파일 기준 줄로 옮기려면 여는 `---` 줄만큼(1) 더하고 1부터 세는 줄로 1을 더 더한다. 결과를 본 뒤 바꾼 기준: 첫 판은 이 회차를 닫히지 않은 따옴표로 쟀는데 그 오류의 자리는 깨진 줄이 아니라 스트림 끝(`line=3`)이라 측정 아님으로 끝났다. 자리가 깨진 줄 위에 있는 오류(값 안의 둘째 콜론)로 바꿨고, 닫히지 않은 따옴표는 새는지 보는 회차에만 남겼다.
- **갈래: 명시적 태그의 변환 실패는 `YAMLError`가 아니다(넷)와 그 대조.** `description: !!int sk-ant-probe-secret`은 `ValueError`, `!!float`도 `ValueError`, `!!bool`은 `KeyError`, `!!timestamp`는 `AttributeError`이고 넷 모두 `yaml.YAMLError`가 아니다. 앞의 셋은 `str`에 그 값이 실리고(`invalid literal for int() … 'sk-ant-probe-secret'` 꼴) `!!timestamp`는 실리지 않는다. 대조로 `!!python/name:os.system`은 `ConstructorError`(`YAMLError`의 하위)다. 그래서 `yaml.YAMLError`만 잡는 층은 태그 변환의 예외를 날것으로 올리고, 그 가운데 셋의 `str`에 운영자가 적은 값이 든다. 셀프 리뷰 표준 축이 손으로 쳐 보인 것을 둘째 판이 회차로 더했다.
- **갈래: 쓰지 않는 칸의 명시적 태그 변환 실패도 `safe_load`에서 난다.** 두 칸이 멀쩡하고 `other: !!int sk-ant-probe-secret`만 더한 머리말에서 `ValueError`(`YAMLError` 아님)가 나고 `str`에 그 값이 실린다. `extra="ignore"`는 모델의 좁힘에서 무시할 뿐이라 YAML 단계의 실패는 머리말 전체의 거부다. PR 봇 CodeRabbit이 짚어 셋째 판이 더했다.
- **갈래: 바꿔 던진 예외에 원래 예외가 남는 자리(셋).** 같은 입력의 예외를 `except` 안에서 `raise ValueError(고정 문구) from error`로 이으면 `__cause__`에 원래 예외가 남고 `traceback.format_exception`의 출력에 그 값이 실린다(양성 대조). `from None`으로 바꿔 던지면 `__cause__`는 `None`이고 `__suppress_context__`가 참이라 출력에는 값이 없지만, `__context__`에 원래 예외가 남아 그 `str`에 값이 있다. `except`에서 종류만 뽑고 블록 밖에서 던지면 `__cause__`와 `__context__`가 모두 `None`이고 출력에도 `str`에도 값이 없다. PR 봇 claude-review가 `__cause__`로 이은 원래 예외가 트레이스백으로 새는 것을 짚어 셋째 판이 더했다. 이 셋은 바꿔 던지는 자리만 흉내 내고 sdk의 함수를 부르지 않으며, 출력은 `traceback.format_exception` 하나로만 봤다(`logging.exception`과 pytest의 실패 출력은 재지 않았다).
- 해석은 다섯이다. `strict=True`의 두 `str` 칸이 YAML이 만들 수 있는 문자열 아닌 값(정수, 불린, 널, 날짜, bytes, 목록)을 모두 `string_type`으로 거부하므로 "없거나 비었거나"에 "문자열이 아니거나"를 더하는 데 검증자가 더 필요 없다는 것, 문구에서 값을 빼는 길이 pydantic은 `include_input=False`, PyYAML은 `str`을 쓰지 않고 종류와 줄·칸만 옮기는 것이라는 것, `yaml.safe_load`를 감싸는 층은 `YAMLError`가 아니라 모든 예외를 잡아야 값을 거른다는 것, 쓰지 않는 칸의 YAML 실패도 머리말 전체의 거부라는 것, 그리고 바꿔 던진 예외에 원래 예외를 남기지 않으려면 `from None`이 아니라 `except` 밖에서 던져야 한다는 것이다. 갈래: "문구에 값이 안 샌다"는 두 양성 대조의 `str`에 값이 있는 것이, "`YAMLError`가 거부의 전부다"는 태그 회차 넷이, "무시되는 칸은 거부에 들지 않는다"는 쓰지 않는 칸 회차가, "`from None`이면 원래 예외가 남지 않는다"는 잇기 회차 셋이 가른다. 재지 않은 것: lax 모드의 경계(명세가 strict를 정했다), `description` 길이 상한(범위 밖), `context_mark`의 줄(문구에 싣지 않는다), 넷 밖의 태그(`!!binary`는 글자 수가 base64의 길이 규칙에 맞으면 틀린 글자를 버리고 bytes를 내 YAML 단계에서 거부되지 않고, 맞지 않거나(17자) ASCII 밖의 글자가 있으면 `ConstructorError`인 것을 손으로 봤다. 둘째 판은 앞의 경우만 적었고 PR 직전 리뷰가 뒤의 둘을 보였다). 결과를 본 뒤 바꾼 것: 둘째 판이 태그 회차 넷과 대조 하나를 더했다. 19회차에서 24회차가 됐다. 셋째 판이 쓰지 않는 칸 회차 하나와 잇기 회차 셋을 더했다. 24회차에서 28회차가 됐다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `yaml_frontmatter.py` | 설치된 PyYAML의 판과 자리, Agent Skills 머리말 다섯 모양과 표준 밖 키를 `yaml.safe_load`가 기대한 값으로 읽는지, 닫히지 않은 따옴표의 거부(양성 대조), 저장소 `.claude/skills/*/SKILL.md`의 필수 두 칸과 표준 밖 키의 수 | ADR 0041 Consequences "머리말은 PyYAML로 전체를 읽고 두 칸만 본다" | 위 명령. 1초 안팎 | pyyaml 6.0.3, Python 3.12.10, Windows 10, 2026-11-03 |
| `frontmatter_split.py` | 파일 전체를 YAML로 읽으면 거부되는 것(양성 대조), 줄 단위 `---` 규칙이 LF·CRLF·본문 안의 `---`·본문 없음·값 안의 `---`를 읽는지, 닫는 줄 없음·BOM·앞의 빈 줄·머리말 없음·`\r` 둘의 거부, 빈 머리말이 `None`인 것, 참조 구현 `split("---", 2)`와의 갈래, 머리말 안의 `---` 줄을 YAML이 거부하는 것(큰따옴표·블록·평문 스칼라의 세 자리)과 그 줄만 뺀 대조 셋, 어댑터의 읽기 길(`read_text`)이 CRLF를 LF로 바꾸고 BOM을 남기는 것, BOM 뒤의 TOML을 `tomllib`이 거부하는 것 | 명세 "머리말을 본문에서 떼는 규칙" | 위 명령. 1초 안팎 | pyyaml 6.0.3, Python 3.12.10, Windows 10, 2026-11-03 |
| `frontmatter_values.py` | `strict=True`·`extra="ignore"` pydantic 모델이 두 칸을 받고 거부하는 경계와 표지(열둘), `ValidationError`의 `str`과 거른 문구에 값이 있고 없는 것(양성 대조), `MarkedYAMLError`의 `str`과 줄·칸 문구에 원문 조각이 있고 없는 것(양성 대조), `problem_mark.line`이 0부터인 것, 명시적 태그 넷(`!!int`·`!!float`·`!!bool`·`!!timestamp`)의 변환 실패가 `YAMLError`가 아니고 셋의 `str`에 값이 실리는 것과 `!!python` 태그의 `ConstructorError` 대조, 쓰지 않는 칸의 태그 변환 실패가 같은 `ValueError`인 것, `from error`로 이으면 트레이스백 출력에 값이 실리고 `from None`은 출력에 없지만 `__context__`를 남기며 `except` 밖에서 던지면 둘 다 `None`인 것 | 명세 "머리말의 두 칸과 값의 모양", "머리말 거부를 `PluginError`로 바꾸는 층", "읽지 못한 문구" | 위 명령. 1초 안팎 | pydantic 2.13.5, pyyaml 6.0.3, Python 3.12.10, Windows 10, 2026-11-03·04 |
