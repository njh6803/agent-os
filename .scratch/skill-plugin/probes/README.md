# skill-plugin 프로브

설계 세션(일지 2026-11-03-02)이 ADR 0041의 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 ADR 0041 Consequences의 "머리말은 PyYAML로 전체를 읽고 두 칸만 본다"다. 명세(`.scratch/skill-plugin/spec.md`)는 아직 없고, 명세가 이 프로브를 들면 그 자리도 아래 표에 더한다.

## 돌리는 법

저장소 루트에서 저장소 `.venv`로 돈다(Windows, Git Bash). 네트워크에 닿지 않고 API 키가 필요 없다. 종료 코드 0은 모든 회차가 측정으로 섰다는 뜻이고, 결론은 출력의 "결과:" 줄로 읽는다(`tools/probe_kit.py`의 `Rounds`).

```sh
PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/yaml_frontmatter.py
```

## 결과 (2026-11-03)

아래의 수는 프로브가 다시 내는 것이다. PyYAML이 직접 의존성이 아니라 `langchain-core`의 전이 의존성이라는 전제는 `uv tree --invert --package pyyaml`로 손으로 본 것이고, 프로브는 설치된 판과 자리만 다시 낸다.

### `yaml_frontmatter.py` — 측정 8회차, 측정 아님 0

- **설치된 판.** `import yaml`이 site-packages의 pyyaml 6.0.3을 불러온다. ADR 0041은 이것을 `pyproject.toml`의 직접 의존성으로 올린다.
- **머리말 다섯 모양.** 접힌 여러 줄 설명(`description: >`), 그대로의 여러 줄 설명(`|`), `metadata` 맵, 표준 밖 키(`disable-model-invocation: true`), 따옴표 안의 콜론과 샵. 다섯 모두 `yaml.safe_load`가 `name`과 함께 기대한 값으로 읽었다. 접힌 설명은 줄이 공백으로 합쳐지고 끝에 개행 하나가 남고, 그대로의 설명은 줄 바꿈이 그대로 남으며, `metadata`는 문자열 맵, 표준 밖 키는 불리언 `True`로 풀린다.
- **양성 대조: 닫히지 않은 따옴표.** `description: "닫히지 않은`은 `ScannerError`(`yaml.YAMLError`의 하위)로 거부됐다. "읽힌다"가 아무 입력에나 참인 관찰이 아니라는 표지다.
- **저장소 스킬의 머리말.** `.claude/skills/*/SKILL.md` 18개를 같은 길로 읽어, 필수 두 칸(`name`, `description`)이 없는 파일은 0개이고 표준 밖 키 `disable-model-invocation`을 쓰는 파일은 5개(grill-me, implement, setup-matt-pocock-skills, to-spec, to-tickets)다. 인터뷰 때 Grep으로 본 다섯과 같다.
- 해석은 둘이다. 설치된 PyYAML이 Agent Skills 표준의 머리말 모양을 추가 처리 없이 그대로 읽으므로 두 줄짜리 자체 파서를 둘 까닭이 없다는 것, 그리고 표준 밖 키는 YAML 차원에서 막히지 않으니 "두 칸만 보고 나머지는 무시한다"는 규칙이 런타임의 선택이지 라이브러리의 제약이 아니라는 것이다. 갈래: "읽힌다"와 "무엇이든 읽어 준다"는 양성 대조의 거부가 가른다. 재지 않은 것: 머리말을 본문에서 떼는 자리(`---` 가르기)는 재지 않았고 명세가 정한다(저장소 스킬 회차의 `head_of`는 읽기 위한 가르기일 뿐이다). 표준의 다른 YAML 모양(앵커, 여러 문서, 탭 들여쓰기)과 Windows 줄 끝(`\r\n`)은 넣지 않았다(저장소 스킬 회차의 `read_text`는 텍스트 모드라 `\r\n`을 `\n`으로 바꿔 넘긴다. 파이썬 표준 동작이고 재지 않았다). 두 해석 가운데 "자체 파서를 둘 까닭이 없다"는 측정이 아니라 측정을 읽은 설계 판단이다. 저장소 스킬의 수 18은 이 탐침을 돌린 작업 트리(브랜치 `docs/skill-plugin-design`)의 것이다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `yaml_frontmatter.py` | 설치된 PyYAML의 판과 자리, Agent Skills 머리말 다섯 모양과 표준 밖 키를 `yaml.safe_load`가 기대한 값으로 읽는지, 닫히지 않은 따옴표의 거부(양성 대조), 저장소 `.claude/skills/*/SKILL.md`의 필수 두 칸과 표준 밖 키의 수 | ADR 0041 Consequences "머리말은 PyYAML로 전체를 읽고 두 칸만 본다" | 위 명령. 1초 안팎 | pyyaml 6.0.3, Python 3.12.10, Windows 10, 2026-11-03 |
