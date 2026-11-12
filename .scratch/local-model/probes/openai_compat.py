"""langchain-openai 의 `ChatOpenAI`를 가짜 모델 서버(Chat Completions)에 붙여 본다.

기능 local-model 의 명세(`.scratch/local-model/spec.md`)와 ADR 0057 이 근거로 드는 프로브다. 서버는
같은 폴더의 `fake_server.py`가 루프백(127.0.0.1)의 빈 포트에 사례마다 새로 띄운다. 클라우드도 실제
모델 서버도 실제 키도 쓰지 않는다. 키 자리의 글자는 모두 지어낸 것이다.

모델은 core 가 부르는 길 그대로 부른다. `core/loop.py`의 `model_caller`에 `ToolSpec`을 넘겨
`bind_tools` 뒤 `ainvoke`를 지나고, 돌아온 메시지는 `core/model.py`의 `reply_from`으로도 읽는다.

사례는 질문마다 모듈 하나다. 사례마다 무엇을 표지로 보는지는 그 모듈의 독스트링이 적는다.
- 질문 1(요청의 모양)과 2(환경 변수): `cases_request.py`
- 질문 3(키 함수)과 4(헤더에 실을 수 없는 키): `cases_key.py`
- 질문 5(깨진 도구 호출 인자)와 9(응답 해석): `cases_response.py`
- 질문 6(실패가 닿는 모양): `cases_failure.py`
- 질문 7(어댑터가 사이에 설 수 있는가): `cases_guard.py`, 후보는 `adapter_candidate.py`
- 질문 8(DEBUG 로그): `cases_logs.py`
- 질문 10(모델마다 준 HTTP 클라이언트가 놓일 때): `cases_lifetime.py`

출력. 첫 줄은 돈 환경의 판(`versions.py`)과 프로브가 지운 환경 변수의 이름이다. 그 뒤로
사례마다 JSON 한 줄(`case`, `measured`, `result`와 사례의 관찰), 끝에 `Rounds`의 집계다. `--out
<파일>`을 주면 JSON 줄 전부는 그 파일에 쓰고 화면에는 사례마다 `case`·`measured`·`result`만 찍는다.
표지가 없는 사례나 예외로 끝난 사례가 하나라도 있으면 1 로 끝난다(`tools/probe_kit.py`의 `Rounds`).

사례 전부가 이벤트 루프 하나에서 돈다. `ChatOpenAI`는 httpx 클라이언트를 주소별로 캐시해 나눠 쓰고
(langchain-openai 1.6.2 의 `_cached_async_httpx_client`를 읽었다) 사례마다 포트가 달라 서로 섞이지
않는다. 루프 둘에서 같은 주소로 부르는 것은 `two_loops_*` 사례 셋이 스레드에서 따로 본다.

돌리는 명령과 환경을 만드는 법은 같은 폴더의 `README.md`에 있다.

    <환경의 파이썬> .scratch/local-model/probes/openai_compat.py [--out <파일>] [사례 ...]
    <환경의 파이썬> .scratch/local-model/probes/openai_compat.py --list
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import cases_failure
import cases_guard
import cases_key
import cases_lifetime
import cases_logs
import cases_request
import cases_response
from support import Case, scrub_environment
from versions import environment as probed_environment

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

MODULES = (
    cases_request,
    cases_key,
    cases_response,
    cases_failure,
    cases_guard,
    cases_logs,
    cases_lifetime,
)
BRIEF = ("case", "measured", "result")


def all_cases() -> dict[str, Case]:
    cases: dict[str, Case] = {}
    for module in MODULES:
        for name, case in module.CASES.items():
            if name in cases:
                raise RuntimeError(f"사례 이름이 겹친다: {name}")
            cases[name] = case
    return cases


def emitter(out: Path | None) -> Callable[[Mapping[str, object]], None]:
    """JSON 한 줄을 내는 함수. 파일을 받았으면 전부는 파일에, 화면에는 줄인 줄을 찍는다."""
    if out is not None:
        out.write_text("", encoding="utf-8")

    def emit(line: Mapping[str, object]) -> None:
        full = json.dumps(line, ensure_ascii=False, default=repr)
        if out is None:
            print(full, flush=True)
            return
        with out.open("a", encoding="utf-8") as stream:
            stream.write(full + "\n")
        brief = {name: line[name] for name in BRIEF if name in line} or line
        print(json.dumps(brief, ensure_ascii=False, default=repr), flush=True)

    return emit


async def run(
    cases: Mapping[str, Case],
    selected: Sequence[str],
    rounds: Rounds,
    emit: Callable[[Mapping[str, object]], None],
) -> None:
    for name in selected:
        with rounds.round(name) as current:
            report = await cases[name]()
            emit(
                {"case": name, "measured": report.measured, "result": report.result, **report.data}
            )
            reason = "측정" if report.measured else f"표지가 없다({report.result})"
            current.mark(measured=report.measured, result=reason)


def main() -> int:
    parser = argparse.ArgumentParser(description="ChatOpenAI 를 가짜 모델 서버에 붙여 본다")
    parser.add_argument("cases", nargs="*", help="돌릴 사례 이름. 없으면 전부")
    parser.add_argument("--list", action="store_true", help="사례 이름만 찍는다")
    parser.add_argument("--out", type=Path, help="JSON 줄 전부를 쓸 파일")
    arguments = parser.parse_args()
    cases = all_cases()
    if arguments.list:
        print("\n".join(cases))
        return 0
    unknown = [name for name in arguments.cases if name not in cases]
    if unknown:
        print(f"모르는 사례: {' '.join(unknown)}", file=sys.stderr)
        return 2
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    emit = emitter(arguments.out)
    emit({"environment": probed_environment(), "scrubbed_variables": scrub_environment()})
    rounds = Rounds()
    asyncio.run(run(cases, arguments.cases or list(cases), rounds, emit))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
