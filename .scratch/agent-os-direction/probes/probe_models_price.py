"""Anthropic Models API(`GET /v1/models`, `GET /v1/models/{id}`)의 응답에 단가 칸이 있는지 본다.

토큰을 쓰지 않는 GET 둘이다. 회차는 둘(목록의 첫 항목, 그 id 의 단건)이고, 재려는 상황이 났다는
표지는 "응답이 실제 모델 객체다"이다. 문서가 적은 칸 `id`(비지 않은 문자열)와
`max_input_tokens`(정수)가 있고 단건은 요청한 id 를 되돌려 줄 때만 측정으로 센다. 키가 없거나
네트워크가 끊겨 예외로 끝난 회차는 측정이 아니다. 결과의 갈래는 응답 JSON 의 모든 키(중첩 포함)에
price·pricing·cost·usd·dollar 가운데 하나라도 들어 있는지다. 이름 검색의 양성 대조는 없고, 대신
최상위 키 전부를 RESULT 줄에 찍어 사람이 본다.

실행: 저장소 루트에서
`uv run --env-file .env python .scratch/agent-os-direction/probes/probe_models_price.py`
(워크트리에서는 주 체크아웃의 `.env`를 `--env-file ../../../.env`로).
결과 한 줄은 `RESULT ` 로 시작하는 JSON 이다.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import anthropic  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

NEEDLES = ("price", "pricing", "cost", "usd", "dollar")


def _keys(value: object, prefix: str = "") -> list[str]:
    """중첩된 사전의 키를 점으로 이은 경로로 모은다."""
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, inner in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            found.append(path)
            found.extend(_keys(inner, path))
    elif isinstance(value, Sequence) and not isinstance(value, str):
        for index, inner in enumerate(value):
            found.extend(_keys(inner, f"{prefix}[{index}]"))
    return found


def _is_model_object(data: Mapping[str, object]) -> bool:
    identifier = data.get("id")
    window = data.get("max_input_tokens")
    return isinstance(identifier, str) and identifier != "" and isinstance(window, int)


def _price_keys(data: Mapping[str, object]) -> list[str]:
    return [key for key in _keys(data) if any(needle in key.lower() for needle in NEEDLES)]


def main() -> int:
    rounds = Rounds()
    client = anthropic.Anthropic()
    report: dict[str, object] = {"anthropic_sdk": anthropic.__version__}

    first_id = ""
    with rounds.round("list-first-item") as current:
        first = next(iter(client.models.list()))
        data = first.to_dict()
        if _is_model_object(data):
            first_id = str(data["id"])
            hits = _price_keys(data)
            report["list_top_level_keys"] = sorted(data.keys())
            report["list_price_keys"] = hits
            current.mark(measured=True, result="price_present" if hits else "price_absent")
        else:
            current.mark(measured=False, result="not a model object")

    with rounds.round("retrieve-by-id") as current:
        if first_id == "":
            current.mark(measured=False, result="no id from the list round")
        else:
            single = client.models.retrieve(first_id).to_dict()
            if _is_model_object(single) and single.get("id") == first_id:
                hits = _price_keys(single)
                report["retrieve_id"] = first_id
                report["retrieve_top_level_keys"] = sorted(single.keys())
                report["retrieve_price_keys"] = hits
                current.mark(measured=True, result="price_present" if hits else "price_absent")
            else:
                current.mark(measured=False, result="not the requested model object")

    report["rounds"] = [
        {"label": entry.label, "measured": entry.measured, "result": entry.result}
        for entry in rounds.measured + rounds.unmeasured
    ]
    print("RESULT " + json.dumps(report, ensure_ascii=False, sort_keys=True))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
