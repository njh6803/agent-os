"""모델 매니페스트에 설 칸 넷(`provider`, `model_id`, `max_tokens`, `temperature`)과 에이전트
매니페스트의 `model` 칸이 ADR 0040 Consequences 의 검증 규칙대로 받고 거부하는지를, sdk 의
`PluginManifest` 와 같은 설정(`extra="forbid"`, `frozen=True`,
`json_schema_serialization_defaults_required=True`)의 시제품으로 잰다. 셋을 본다.

- 받기와 거부. TOML 원문을 `tomllib` 으로 풀어 시제품에 넣는다. 받은 사례는 칸의 값과 타입을,
  거부한 사례는 pydantic 오류의 `type`(`enum`, `int_type`, `greater_than_equal` 등)이나 종류별
  검증자의 `ValueError` 문구를 표지로 본다. "거부됐다"만 보면 다른 까닭의 거부(모르는 칸, 빠진
  공통 칸)가 기대와 맞는다. 거부 사례는 오류가 하나일 때만 측정으로 센다.
- 직렬화 JSON 스키마. 다섯 칸이 `required` 에 들고 `null` 을 허락하는지, `provider` 가 이름 있는
  정의(`$defs` 의 `ModelProvider`)로 나오는지. 관리 API 계약(`openapi.json`)에서 생성한 TS 타입이
  그 칸들을 필수로 받아 매니페스트 리터럴이 지금의 `conversation_limit` 처럼 `null` 을 적어야
  하는지와, 열거를 재사용하는지의 근거다.
- 칸 이름 `model_id` 와 `model` 이 pydantic 의 보호 이름 공간 경고를 내는지. 양성 대조로
  `protected_namespaces=("model_",)` 를 준 같은 클래스가 경고를 내는 것을 본다. 경고를 잡는 길이
  실제로 잡는다는 표지다.

쓰임: 저장소 루트에서 `uv run python .scratch/model-plugin/probes/manifest_fields.py`
"""

from __future__ import annotations

import sys
import tomllib
import warnings
from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

from agent_os.sdk.ids import PLUGIN_NAME_PATTERN  # noqa: E402
from agent_os.sdk.manifest import PluginKind  # noqa: E402

COMMON = 'schema_version = "1"\nkind = "{kind}"\nname = "{name}"\nversion = "0.1.0"\n'
MODEL_FIELDS = ("model", "provider", "model_id", "max_tokens", "temperature")
NAMESPACE_WARNING = "protected namespace"


class ModelProvider(StrEnum):
    ANTHROPIC = "anthropic"


def build_prototype(protected: tuple[str, ...] | None = None) -> type[BaseModel]:
    """sdk 의 `PluginManifest` 와 같은 설정에 새 칸 다섯을 더한 시제품. 함수 안에서 정의하는 까닭은
    클래스를 만들 때 나는 경고를 부르는 쪽이 잡기 위해서다."""
    config = ConfigDict(
        extra="forbid", frozen=True, json_schema_serialization_defaults_required=True
    )
    if protected is not None:
        config["protected_namespaces"] = protected

    class Manifest(BaseModel):
        model_config = config

        schema_version: Literal["1"]
        kind: PluginKind
        name: str = Field(pattern=PLUGIN_NAME_PATTERN)
        version: str
        entrypoint: str | None = None
        # 에이전트만. 쓸 모델 플러그인의 이름. 없으면 기본 모델
        model: str | None = Field(default=None, pattern=PLUGIN_NAME_PATTERN)
        # 모델만. 앞 둘은 필수, 뒤 둘은 선택
        provider: ModelProvider | None = None
        model_id: str | None = Field(default=None, min_length=1)
        max_tokens: int | None = Field(default=None, strict=True, ge=1)
        temperature: float | None = Field(default=None, strict=True, ge=0, le=1)

        @model_validator(mode="after")
        def _fields_belong_to_their_kind(self) -> Self:
            if self.kind is PluginKind.MODEL:
                for required in ("provider", "model_id"):
                    if getattr(self, required) is None:
                        raise ValueError(f"model 플러그인은 {required}가 필요하다")
            else:
                for field in ("provider", "model_id", "max_tokens", "temperature"):
                    if field in self.model_fields_set:
                        raise ValueError(f"{self.kind} 플러그인은 {field}을 갖지 않는다")
            if self.kind is not PluginKind.AGENT and "model" in self.model_fields_set:
                raise ValueError(f"{self.kind} 플러그인은 model을 갖지 않는다")
            return self

    return Manifest


def model_toml(extra: str) -> str:
    return COMMON.format(kind="model", name="claude-opus-5") + extra


def agent_toml(extra: str) -> str:
    return COMMON.format(kind="agent", name="calc") + extra


FULL = 'provider = "anthropic"\nmodel_id = "claude-opus-5"\n'

# (회차 이름, TOML, 받은 뒤 기대하는 칸의 값. 타입까지 같아야 한다)
ACCEPTED: list[tuple[str, str, dict[str, object]]] = [
    (
        "model_minimal",
        model_toml(FULL),
        {
            "provider": ModelProvider.ANTHROPIC,
            "model_id": "claude-opus-5",
            "max_tokens": None,
            "temperature": None,
        },
    ),
    (
        "model_full",
        model_toml(FULL + "max_tokens = 16000\ntemperature = 0.5\n"),
        {"max_tokens": 16000, "temperature": 0.5},
    ),
    ("temperature_int_0", model_toml(FULL + "temperature = 0\n"), {"temperature": 0.0}),
    ("temperature_int_1", model_toml(FULL + "temperature = 1\n"), {"temperature": 1.0}),
    ("max_tokens_1", model_toml(FULL + "max_tokens = 1\n"), {"max_tokens": 1}),
    ("agent_model", agent_toml('model = "claude-opus-5"\n'), {"model": "claude-opus-5"}),
    ("agent_without_model", agent_toml(""), {"model": None}),
]

# (회차 이름, TOML, 기대하는 표지. `value_error:` 뒤는 검증자 문구에 들어야 할 글)
REJECTED: list[tuple[str, str, str]] = [
    ("provider_unknown", model_toml('provider = "openai"\nmodel_id = "gpt"\n'), "enum"),
    ("provider_missing", model_toml('model_id = "claude-opus-5"\n'), "value_error:provider"),
    ("model_id_missing", model_toml('provider = "anthropic"\n'), "value_error:model_id"),
    ("model_id_empty", model_toml('provider = "anthropic"\nmodel_id = ""\n'), "string_too_short"),
    ("model_id_number", model_toml('provider = "anthropic"\nmodel_id = 5\n'), "string_type"),
    ("max_tokens_zero", model_toml(FULL + "max_tokens = 0\n"), "greater_than_equal"),
    ("max_tokens_float", model_toml(FULL + "max_tokens = 2.0\n"), "int_type"),
    ("max_tokens_bool", model_toml(FULL + "max_tokens = true\n"), "int_type"),
    ("max_tokens_string", model_toml(FULL + 'max_tokens = "16"\n'), "int_type"),
    ("temperature_over", model_toml(FULL + "temperature = 1.5\n"), "less_than_equal"),
    ("temperature_negative", model_toml(FULL + "temperature = -0.1\n"), "greater_than_equal"),
    ("temperature_string", model_toml(FULL + 'temperature = "0.5"\n'), "float_type"),
    ("temperature_bool", model_toml(FULL + "temperature = true\n"), "float_type"),
    ("unknown_field", model_toml(FULL + "top_p = 0.9\n"), "extra_forbidden"),
    ("model_with_model", model_toml(FULL + 'model = "claude-opus-5"\n'), "value_error:model"),
    ("agent_model_pattern", agent_toml('model = "Opus"\n'), "string_pattern_mismatch"),
    (
        "mcp_with_model",
        COMMON.format(kind="mcp", name="everything") + 'model = "claude-opus-5"\n',
        "value_error:model",
    ),
    ("agent_with_provider", agent_toml('provider = "anthropic"\n'), "value_error:provider"),
    ("agent_with_max_tokens", agent_toml("max_tokens = 10\n"), "value_error:max_tokens"),
]


def marker_of(error: ValidationError) -> str:
    first = error.errors()[0]
    if first["type"] == "value_error":
        return "value_error:" + str(first["msg"])
    return str(first["type"])


def matches(marker: str, expected: str) -> bool:
    if expected.startswith("value_error:"):
        wanted = expected.removeprefix("value_error:")
        return marker.startswith("value_error:") and wanted in marker
    return marker == expected


def define_and_catch(protected: tuple[str, ...] | None) -> tuple[type[BaseModel], list[str]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        prototype = build_prototype(protected)
    return prototype, [
        str(entry.message) for entry in caught if NAMESPACE_WARNING in str(entry.message)
    ]


def main() -> int:
    rounds = Rounds()
    results: list[str] = []

    with rounds.round("field_names_default_namespaces") as current:
        prototype, texts = define_and_catch(None)
        current.mark(
            measured="model_id" in prototype.model_fields and "model" in prototype.model_fields,
            result="경고 없음" if not texts else f"경고 {len(texts)}",
        )
        results.append(f"기본 보호 이름 공간: {texts or '경고 없음'}")
    with rounds.round("field_names_model_namespace_control") as current:
        prototype, texts = define_and_catch(("model_",))
        current.mark(
            measured="model_id" in prototype.model_fields and bool(texts),
            result="경고 있음" if texts else "경고 없음",
        )
        results.append(f"양성 대조 model_: {texts or '경고 없음'}")

    manifest = build_prototype()
    for label, text, expected in ACCEPTED:
        with rounds.round(f"accept:{label}") as current:
            parsed = manifest.model_validate(tomllib.loads(text))
            mismatches = [
                f"{key}={getattr(parsed, key)!r}"
                for key, value in expected.items()
                if getattr(parsed, key) != value or type(getattr(parsed, key)) is not type(value)
            ]
            current.mark(
                measured=True,
                result="받음(기대대로)" if not mismatches else f"받음(값 어긋남: {mismatches})",
            )
    for label, text, expected in REJECTED:
        with rounds.round(f"reject:{label}") as current:
            try:
                manifest.model_validate(tomllib.loads(text))
            except ValidationError as error:
                marker = marker_of(error)
                if len(error.errors()) != 1:
                    current.mark(measured=False, result=f"오류 {len(error.errors())}개: {marker}")
                else:
                    current.mark(
                        measured=matches(marker, expected),
                        result="거부(기대한 표지)"
                        if matches(marker, expected)
                        else f"거부(다른 표지: {marker})",
                    )
            else:
                current.mark(measured=False, result="거부되지 않았다")

    with rounds.round("schema_serialization") as current:
        schema = manifest.model_json_schema(mode="serialization")
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        present = [name for name in MODEL_FIELDS if name in required]
        nullable = [
            name
            for name in MODEL_FIELDS
            if {"type": "null"} in properties.get(name, {}).get("anyOf", [])
        ]
        named = "ModelProvider" in schema.get("$defs", {})
        current.mark(
            measured="required" in schema and all(name in properties for name in MODEL_FIELDS),
            result=f"required {len(present)}/5, null 허락 {len(nullable)}/5, "
            f"ModelProvider 정의 {'있음' if named else '없음'}",
        )
        results.append(f"required: {required}")
        results.append(f"provider 스키마: {properties.get('provider')}")

    for entry in rounds.entries:
        print(f"{entry.label}: {entry.result}")
    print("\n".join(results))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
