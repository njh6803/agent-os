"""`run.sh` 의 출력 디렉터리를 읽어 변형마다 잰 것을 찍고, 재려는 상황이 났는지 단언한다.

- A_payload: 탐침 훅이 받은 입력마다 이벤트·도구 이름, 입력 키, `tool_response` 의 키와 타입, code,
  bytes, 결과의 글자·UTF-8 바이트 수와 bytes 와의 일치를 찍는다. 세 주소가 모두 찍혔고, 본문 통과
  문서는 200 에 일치, 요약 문서는 200 에 불일치, 리다이렉트 주소는 3xx 일 때 측정이다.
- B_summary·C_passthrough: 같은 호출의 탐침 기록(요약이었는지 통과였는지)과 모델의 마지막 답을
  찍는다. B 는 요약이고 답이 훅의 첫 문장(`tools/hook_webfetch_summary.py` 의 `LEAD`)을 옮겼을 때,
  C 는 통과이고 답이 그 문장 없이 '알림 없음' 일 때 기대대로다. 탐침 기록이 없거나 그 호출이
  요약·통과가 아니었으면 측정이 아니다. 스트림이 아니라 답으로 판정하는 까닭도 B 가 찍는다. 모델의
  답(assistant·result 이벤트) 밖의 줄에 훅 문장이나 `additionalContext` 가 있는지다. 훅은
  `json.dumps` 의 기본값으로 한글을 이스케이프해 내므로 이스케이프한 첫 문장도 찾는다. 없으면
  stream-json 이 훅의 additionalContext 를 싣지 않은 것이다.

측정이 아닌 변형, 기대와 다른 변형, 모르는 변형 이름이 하나라도 있으면 1로 끝난다.
돌리는 법:
`uv run python .scratch/harness/probes/webfetch_payload/summarize.py <출력 디렉터리> [변형 ...]`.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PASSTHROUGH = "https://code.claude.com/docs/en/large-codebases.md"
SUMMARIZED = "https://code.claude.com/docs/en/hooks"
REDIRECTED = "https://docs.claude.com/en/docs/claude-code/hooks"
RESPONSE_KEYS = ["bytes", "code", "codeText", "durationMs", "result", "url"]
NO_NOTICE = "알림 없음"
VARIANTS = ("A_payload", "B_summary", "C_passthrough")


def read_jsonl(path: Path) -> list[dict[str, object]]:
    """한 줄에 JSON 하나인 파일. 없거나 깨진 줄은 건너뛴다."""
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append({str(key): value for key, value in record.items()})
    return records


def response_of(entry: dict[str, object]) -> dict[str, object]:
    response = entry.get("tool_response")
    return (
        {str(key): value for key, value in response.items()} if isinstance(response, dict) else {}
    )


def final_answer(stream: list[dict[str, object]]) -> str:
    """stream-json 의 마지막 `result` 이벤트의 답."""
    answers = [str(event.get("result", "")) for event in stream if event.get("type") == "result"]
    return answers[-1] if answers else ""


def hook_text_outside_answer(stream_path: Path, lead: str) -> int:
    """모델의 답(assistant·result 이벤트) 밖의 줄 가운데 훅 문장(날것이나 이스케이프한 것)이나
    `additionalContext` 가 든 줄의 수."""
    if not stream_path.exists():
        return 0
    escaped = json.dumps(lead)[1:-1]
    count = 0
    for line in stream_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") in ("assistant", "result"):
            continue
        if lead in line or escaped in line or "additionalContext" in line:
            count += 1
    return count


def check_payload(out: Path) -> list[str]:
    entries = read_jsonl(out / "A_payload_posttool.jsonl")
    problems: list[str] = []
    by_url = {str(entry.get("url")): entry for entry in entries}
    for entry in entries:
        response = response_of(entry)
        types = response.get("types")
        keys = sorted(types) if isinstance(types, dict) else None
        print(
            f"A {entry.get('hook_event_name')} {entry.get('tool_name')} {entry.get('url')}\n"
            f"  입력 키 {entry.get('payload_keys')}\n"
            f"  tool_response 키 {keys} code {response.get('code')} bytes {response.get('bytes')}"
            f" 결과 {response.get('result_chars')}자 {response.get('result_utf8')}바이트"
            f" 일치 {response.get('utf8_equals_bytes')}\n"
            f"  결과 앞 {response.get('result_head')!r}"
        )
        if entry.get("hook_event_name") != "PostToolUse" or entry.get("tool_name") != "WebFetch":
            problems.append(f"A: 이벤트·도구가 다르다 {entry.get('url')}")
        if keys != RESPONSE_KEYS:
            problems.append(f"A: tool_response 키가 다르다 {entry.get('url')} {keys}")
    expected = (
        (PASSTHROUGH, lambda r: r.get("code") == 200 and r.get("utf8_equals_bytes") is True),
        (SUMMARIZED, lambda r: r.get("code") == 200 and r.get("utf8_equals_bytes") is False),
        (
            REDIRECTED,
            lambda r: isinstance(r.get("code"), int) and 300 <= int(str(r.get("code"))) < 400,
        ),
    )
    for url, holds in expected:
        entry = by_url.get(url)
        if entry is None:
            problems.append(f"A: 측정 아님 — {url} 의 PostToolUse 기록이 없다")
        elif not holds(response_of(entry)):
            problems.append(f"A: 측정 아님 — {url} 이 기대한 갈래(통과·요약·리다이렉트)가 아니었다")
    return problems


def check_notice(out: Path, name: str, lead: str) -> list[str]:
    summary = name == "B_summary"
    entries = read_jsonl(out / f"{name}_posttool.jsonl")
    answer = final_answer(read_jsonl(out / f"{name}.jsonl"))
    print(f"{name} 탐침 기록 {len(entries)}건\n  답 {answer!r}")
    if summary:
        outside = hook_text_outside_answer(out / f"{name}.jsonl", lead)
        print(f"  모델의 답 밖 줄에 훅 문장·additionalContext {outside}")
    if len(entries) != 1:
        return [f"{name}: 측정 아님 — WebFetch 의 PostToolUse 기록이 {len(entries)}건이다"]
    equal = response_of(entries[0]).get("utf8_equals_bytes")
    if equal is not (not summary) or response_of(entries[0]).get("code") != 200:
        return [f"{name}: 측정 아님 — 그 호출이 {'요약' if summary else '통과'}가 아니었다"]
    if summary and lead not in answer:
        return [f"{name}: 답이 훅의 첫 문장을 옮기지 않았다"]
    if not summary and (lead in answer or NO_NOTICE not in answer):
        return [f"{name}: 통과에 훅이 알렸거나 답이 '{NO_NOTICE}' 가 아니다"]
    return []


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    out = Path(sys.argv[1])
    variants = sys.argv[2:] or list(VARIANTS)
    problems = [f"모르는 변형 {name} — 재지 않았다" for name in variants if name not in VARIANTS]
    if "A_payload" in variants:
        problems += check_payload(out)
    notice_variants = [name for name in variants if name in ("B_summary", "C_passthrough")]
    if notice_variants:
        sys.path.insert(0, str(ROOT))
        from tools.hook_webfetch_summary import LEAD

        for name in notice_variants:
            problems += check_notice(out, name, LEAD)
    for problem in problems:
        print(f"[문제] {problem}")
    print(f"변형 {len(variants)}개, 문제 {len(problems)}건.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
