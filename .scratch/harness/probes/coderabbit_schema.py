"""`.coderabbit.yaml` 을 CodeRabbit 설정 스키마(v2)로 검증하고, 독스트링 사전 검사의 키를 찍는다.

대기열 69 에서 키 이름(`reviews.pre_merge_checks.docstrings.mode`)과 값("off")을 이것으로
확인했다. 설정 주석의 "YAML 1.1 파서는 맨 off 를 불리언 false 로 읽는다"도 여기서 잰다(PyYAML 이
YAML 1.1 이다).
스키마는 최상위에서만 모르는 키를 막고(`additionalProperties: false`) `reviews` 아래는 막지 않는다
(2026-09-30 대조군 "키 오타"가 0건). 그래서 검증 0건은 `reviews` 아래 값의 모양만 보증하고, 키
이름은 스키마와 설정을 같은 경로 이름으로 따라가는 것(없으면 KeyError)이 보증한다.
2026-09-30 결과: 검증 0건, 대조군 맨 off 2건(문자열이 아니다, enum 밖), 키 오타 0건.

사용: 저장소 루트에서
    curl -sSL -o <스크래치>/schema.v2.json https://coderabbit.ai/integrations/schema.v2.json
    uv run --with jsonschema==4.26.0 --with pyyaml==6.0.3 python \
        .scratch/harness/probes/coderabbit_schema.py <스크래치>/schema.v2.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import yaml


def _resolve(schema: dict[str, object], node: object) -> object:
    while isinstance(node, dict) and "$ref" in node:
        target: object = schema
        for part in str(node["$ref"]).lstrip("#/").split("/"):
            assert isinstance(target, dict)
            target = target[part]
        node = target
    return node


def _child(schema: dict[str, object], node: object, key: str) -> object:
    resolved = _resolve(schema, node)
    assert isinstance(resolved, dict)
    properties = resolved["properties"]
    assert isinstance(properties, dict)
    return _resolve(schema, properties[key])


def _errors(validator: jsonschema.protocols.Validator, config: object) -> list[str]:
    return sorted(
        f"{'/'.join(map(str, error.absolute_path))} — {error.message}"
        for error in validator.iter_errors(config)
    )


def main(schema_path: str) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    text = Path(".coderabbit.yaml").read_text(encoding="utf-8")
    config = yaml.safe_load(text)

    reviews = _child(schema, schema, "reviews")
    docstrings = _child(schema, _child(schema, reviews, "pre_merge_checks"), "docstrings")
    print("스키마의 docstrings:", json.dumps(docstrings, ensure_ascii=False))
    print("설정의 값:", repr(config["reviews"]["pre_merge_checks"]["docstrings"]["mode"]))
    print("맨 off 를 YAML 1.1 로 읽으면:", repr(yaml.safe_load("mode: off")["mode"]))

    validator = jsonschema.validators.validator_for(schema)(schema)
    print("검증기:", type(validator).__name__)
    errors = _errors(validator, config)
    for error in errors:
        print("검증 오류:", error)
    print(f"검증 오류 {len(errors)}건")

    # 대조군: 검증기가 실제로 잡는지 본다. 둘 다 0건이면 위의 0건도 아무것도 말하지 않는다.
    unquoted = yaml.safe_load(text.replace('mode: "off"', "mode: off"))
    typo = yaml.safe_load(text.replace("pre_merge_checks:", "pre_merge_check:"))
    print("대조군 맨 off:", _errors(validator, unquoted))
    print("대조군 키 오타:", _errors(validator, typo))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
