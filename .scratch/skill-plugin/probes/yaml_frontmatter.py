"""SKILL.md 머리말을 설치된 PyYAML 이 그대로 읽는지 재는 탐침. ADR 0041 이 근거로 든다.

재는 것은 셋이다. (1) 이 가상 환경에서 `import yaml` 이 되고 그 판이 무엇인지. `pyproject.toml` 의
직접 의존성에 없고 `langchain-core` 의 전이 의존성으로 깔린 것을 읽는다(`uv tree --invert --package
pyyaml` 로 손으로 봤다). (2) Agent Skills 표준의 머리말 모양 — 접힌 여러 줄 설명(`>`), 그대로의 여러
줄 설명(`|`), `metadata` 맵, 따옴표 안의 콜론과 샵 — 과 표준 밖 키(`disable-model-invocation`)를
`yaml.safe_load` 가 기대한 값으로 읽는지. (3) 양성 대조 — 닫히지 않은 따옴표의 머리말은
`yaml.YAMLError` 로 거부되는지. 거부가 나야 "읽힌다" 가 아무 입력에나 참인 관찰이 아니다. 그리고 이
저장소의 `.claude/skills/*/SKILL.md` 머리말을 같은 길로 읽어 필수 두 칸이 있는지와 표준 밖 키를 쓰는
파일의 수를 센다.

표지. 머리말 회차는 풀린 값이 기대한 값과 같고 `name` 도 함께 읽혔을 때만 측정이다. 같지 않거나
예외로 끝나면 측정이 아니다. 양성 대조는 `yaml.YAMLError` 의 하위 타입이 났을 때만 측정이다. 저장소
스킬 회차는 파일을 하나 이상 읽었을 때만 측정이고, 필수 칸이 없는 파일은 결과의 수로 적는다.

전제와 못 보는 것. 머리말을 본문에서 떼는 일(`---` 로 가르기)은 재지 않는다. 머리말 회차는 머리말
글을 바로 넘기고, 저장소 스킬 회차의 `head_of` 는 읽기 위한 가르기일 뿐 재는 대상이 아니다. 어디서
가를지는 명세가 정한다. 표준의 다른 YAML 모양(앵커, 여러 문서, 탭)은 넣지 않았다. 저장소 스킬의 수는
이 탐침을 돌린 작업 트리를 읽은 것이다.

돌리는 법: 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/yaml_frontmatter.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

NAME = "pdf-processing"
FOLDED = f"name: {NAME}\ndescription: >\n  여러 줄\n  설명이다.\n"
LITERAL = f"name: {NAME}\ndescription: |\n  첫 줄\n  둘째 줄\n"
METADATA = f'name: {NAME}\ndescription: 한 줄\nmetadata:\n  author: example-org\n  version: "1.0"\n'
EXTRA_KEY = f"name: {NAME}\ndescription: 한 줄\ndisable-model-invocation: true\n"
QUOTED = f'name: {NAME}\ndescription: "주의: 이것은 # 샵이 아니다"\n'
BROKEN = f'name: {NAME}\ndescription: "닫히지 않은\n'
NONSTANDARD_KEY = "disable-model-invocation"

CASES: list[tuple[str, str, str, object]] = [
    ("접힌 여러 줄 설명", FOLDED, "description", "여러 줄 설명이다.\n"),
    ("그대로의 여러 줄 설명", LITERAL, "description", "첫 줄\n둘째 줄\n"),
    ("metadata 맵", METADATA, "metadata", {"author": "example-org", "version": "1.0"}),
    ("표준 밖 키", EXTRA_KEY, NONSTANDARD_KEY, True),
    ("따옴표 안의 콜론과 샵", QUOTED, "description", "주의: 이것은 # 샵이 아니다"),
]


def head_of(text: str) -> str | None:
    """`---` 로 감싼 첫 블록. 저장소 스킬을 읽는 데만 쓰고 재는 대상이 아니다."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rounds = Rounds()

    with rounds.round("설치된 판") as current:
        location = Path(yaml.__file__)
        if "site-packages" in location.parts:
            current.mark(measured=True, result=f"pyyaml {yaml.__version__}")

    for label, text, key, expected in CASES:
        with rounds.round(label) as current:
            parsed = yaml.safe_load(text)
            if (
                isinstance(parsed, dict)
                and parsed.get("name") == NAME
                and parsed.get(key) == expected
            ):
                current.mark(measured=True, result="기대한 값으로 읽힘")

    with rounds.round("양성 대조: 닫히지 않은 따옴표") as current:
        try:
            yaml.safe_load(BROKEN)
        except yaml.YAMLError as error:
            current.mark(measured=True, result=f"거부 {type(error).__name__}")

    with rounds.round("저장소 스킬의 머리말") as current:
        files = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
        missing: list[str] = []
        nonstandard: list[str] = []
        for file in files:
            head = head_of(file.read_text(encoding="utf-8"))
            parsed = yaml.safe_load(head) if head is not None else None
            if not isinstance(parsed, dict) or "name" not in parsed or "description" not in parsed:
                missing.append(file.parent.name)
                continue
            if NONSTANDARD_KEY in parsed:
                nonstandard.append(file.parent.name)
        if files:
            current.mark(
                measured=True,
                result=(
                    f"스킬 {len(files)}개, "
                    f"필수 두 칸 없음 {len(missing)}개 ({', '.join(missing)}), "
                    f"표준 밖 키 {len(nonstandard)}개 ({', '.join(nonstandard)})"
                ),
            )

    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
