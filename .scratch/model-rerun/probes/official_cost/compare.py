"""회차 기록의 세션·모델마다 세션 기록 파일의 응답 셈과 `modelUsage`의 `costUSD`를 대 본다.

티켓 11의 "공식 단가 셈을 Opus로 대 본다". 기록 파일의 응답만으로 셈한 값(채우기 전, 07의 첫 판)과
`modelUsage`의 토큰과의 칸마다 차이, 그 차이를 같은 단가로 채운 값을 캐시 쓰기 5분·1시간 배수로
찍는다. 남는 차가 0이면 단가와 배수는 Claude Code의 셈과 같고, 어긋남은 기록 파일에 남은 토큰이다.

    uv run python .scratch/model-rerun/probes/official_cost/compare.py \
        --records .scratch/model-rerun/probes/records \
        --projects C:/Users/User/.claude-rerun/projects \
        --condition 2

기록 파일은 전용 설정 폴더(`--projects`) 아래에만 있고 커밋하지 않는다. 출력은 같은 폴더의
`<날짜>.log`로 커밋한다. 세션·모델 하나가 회차이고, 그 모델의 응답이 기록 파일에 있어 두 셈을
견준 것이 측정이다. 기록 파일이 없거나 응답이 없는 회차는 측정이 아니라고 세고, 그런 회차가 있거나
견준 것이 없으면 종료 1이다(`tools/probe_kit.py`의 `Rounds`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

from tools import rerun_cost as rc  # noqa: E402


def per_model(lines: list[str]) -> dict[str, list[float]]:
    """모델마다 [응답 셈 달러, 입력, 출력, 캐시 읽기, 5분 쓰기, 1시간 쓰기]."""
    out: dict[str, list[float]] = {}
    for r in rc._responses(lines):
        model = rc._canonical(r.model)
        price = rc._price(model)
        w5, w1 = rc._cache_writes(r.usage)
        i = rc._int(r.usage.get("input_tokens"))
        o = rc._int(r.usage.get("output_tokens"))
        c = rc._int(r.usage.get("cache_read_input_tokens"))
        if model == rc.HAIKU and i + c + w5 + w1 > rc.HAIKU_LONG_PROMPT:
            price = rc.HAIKU_LONG_PRICE
        a = out.setdefault(model, [0.0, 0, 0, 0, 0, 0])
        a[0] += rc._usd(price, i, o, c, w5, w1)
        for k, v in enumerate((i, o, c, w5, w1), start=1):
            a[k] += v
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--projects", type=Path, required=True)
    parser.add_argument("--condition", type=int, required=True)
    args = parser.parse_args()
    rounds = Rounds()
    for rec in sorted(args.records.glob("*.json")):
        d = json.loads(rec.read_text(encoding="utf-8"))
        if d.get("condition_version") != args.condition:
            continue
        for s in d["sessions"]:
            found = list(args.projects.glob(f"*/{s['session_id']}.jsonl"))
            if not found:
                print(f"{rec.name} {s['session_id']} 기록 파일 없음")
                rounds.record(
                    f"{rec.name} {s['session_id']}", measured=False, result="기록 파일 없음"
                )
                continue
            got = per_model(rc.transcript_lines(found[0]))
            for u in s["model_usage"]:
                model = rc._canonical(u["model"])
                a = got.get(model)
                cc = u["cost_usd"]
                if a is None:
                    print(f"{rec.name} {model} 응답 없음(대신 셈) costUSD={cc:.4f}")
                    rounds.record(f"{rec.name} {model}", measured=False, result="응답 없음")
                    continue
                d_in = u["input_tokens"] - a[1]
                d_out = u["output_tokens"] - a[2]
                d_read = u["cache_read_tokens"] - a[3]
                d_write = u["cache_write_tokens"] - a[4] - a[5]
                print(
                    f"{rec.name} {model} costUSD={cc:.4f} 응답셈={a[0]:.4f} 비={a[0] / cc:.4f} "
                    f"5분쓰기={a[4]:.0f} 1시간쓰기={a[5]:.0f} 생각={u['thinking_tokens']}"
                )
                print(
                    f"    모자란 칸: 입력 {d_in:.0f} 출력 {d_out:.0f} "
                    f"읽기 {d_read:.0f} 쓰기 {d_write:.0f}"
                )
                p = rc._price(model)
                left: dict[str, float] = {}
                for label, mult in (("5분", rc.WRITE_5M), ("1시간", rc.WRITE_1H)):
                    fill = (
                        d_in * p.input
                        + d_out * p.output
                        + d_read * p.cache_read
                        + d_write * p.input * mult
                    ) / 1e6
                    left[label] = cc - a[0] - fill
                    print(f"    채운 쓰기 {label}: 남는 차 {left[label]:+.4f}")
                # 표지: 기록 파일에 그 모델의 응답이 있어 두 셈을 견줬다. 결과는 5분 갈래가
                # 맞았는지.
                verdict = "5분 갈래 0" if abs(left["5분"]) < 0.00005 else "5분 갈래 남음"
                rounds.record(f"{rec.name} {model}", measured=True, result=verdict)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
