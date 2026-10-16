"""PostToolUse 훅이 Read·Bash·PowerShell 에서 받는 `tool_response` 의 모양과, 같은 호출의 기록
`tool_result` 본문 길이를 견준다(티켓 06, 명세 "큰 결과 알림 훅"의 크기).

명세는 `tool_response` 가 모델이 받는 글이 아니라 도구의 구조화된 출력이라고 공식 hooks 문서의
PostToolBatch 절을 들어 적었다. 훅(`tools/hook_large_result.py` 의 `result_chars`)은 그 출력에서
모델이 받는 글의 길이를 셈하고, 이 프로브는 그 셈이 기록에 남은 본문 길이와 맞는지 본다.

픽스처는 저장소 밖 출력 디렉터리 아래 `fixture/` 다. `lines.txt` 는 1200줄(줄 번호가 한 자리에서 네
자리까지)로 2만 자를 넘고, `korean.txt` 는 한글 줄이며, `pixel.png` 는 1×1 그림이다. 모델에게 차례로
부르게 하는 호출은 `CALLS` 다. 범위를 준 Read, 3만 자를 넘는 Bash 출력(`seq 1 8000`, 38893자. Claude
Code 가 긴 출력을 자르는 구간이 있으면 여기서 갈린다), stdout 과 stderr 가 둘 다 있는 Bash,
PowerShell 출력이 든다.

`run` 은 탐침 훅(`dump_posttool.py`)만 붙인 `claude -p`(haiku) 하나를 저장소 밖에서
`--setting-sources project,local` 로 띄운다. 세션이 끝나면 탐침 기록의 호출마다 그 페이로드의
`transcript_path` 를 열어 같은 `tool_use_id` 의 `tool_result` 를 찾고, 본문 길이(글 블록의 글자 수
합. `.scratch/token-usage/probes/measure.py` 의 `text_len` 과 같은 셈)와 앞뒤 200자, 그림 블록이
있는지를 페이로드 옆에 붙여 `<출력>/payloads.jsonl` 에 쓴다. `--save` 를 주면 그 파일을 이
디렉터리의 `payloads.jsonl` 로 옮겨 적는다(커밋하는 원본).

`judge` 는 claude 를 띄우지 않고 `payloads.jsonl`(인자가 없으면 이 디렉터리의 것)을 다시 판정한다.
`CALLS` 의 호출이 모두 한 번씩 기록에 있고 그 기록에 `tool_result` 가 있을 때 측정이다. 호출마다
훅의 셈과 기록 길이를 찍고, 셈이 기록과 다른 호출을 차이와 함께 적는다. 다른 것이
기대(`EXPECT_DIFF`) 밖이면 1로 끝난다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/token-usage/probes/large_result/run.py run <저장소 밖 디렉터리> [--save]`,
또는 `... run.py judge [payloads.jsonl]`. `claude` CLI 와 인증이 들고 haiku 세션 하나다.
"""

from __future__ import annotations

import io
import json
import shutil
import struct
import subprocess
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LINES = 1200
SEQ_SMALL = 2000
SEQ_LARGE = 8000
POWERSHELL_ROWS = 3000


@dataclass(frozen=True)
class Call:
    label: str
    tool: str
    instruction: str


def calls(fixture: Path) -> list[Call]:
    lines = (fixture / "lines.txt").as_posix()
    korean = (fixture / "korean.txt").as_posix()
    pixel = (fixture / "pixel.png").as_posix()
    return [
        Call("read_whole", "Read", f"Read 로 '{lines}' 를 범위 없이 읽는다"),
        Call("read_ranged", "Read", f"Read 로 '{lines}' 를 offset 1000, limit 50 으로 읽는다"),
        Call("read_korean", "Read", f"Read 로 '{korean}' 를 범위 없이 읽는다"),
        Call("read_image", "Read", f"Read 로 '{pixel}' 를 읽는다"),
        Call("bash_small", "Bash", f"Bash 로 `seq 1 {SEQ_SMALL}` 을 돌린다"),
        Call("bash_large", "Bash", f"Bash 로 `seq 1 {SEQ_LARGE}` 을 돌린다"),
        Call("bash_stderr", "Bash", "Bash 로 `echo out-line; echo err-line >&2` 를 돌린다"),
        Call(
            "powershell_rows",
            "PowerShell",
            f'PowerShell 로 `1..{POWERSHELL_ROWS} | ForEach-Object {{ "row $_" }}` 를 돌린다',
        ),
    ]


# 훅의 셈이 기록과 다를 것으로 기대하는 호출과 그 까닭. 결과를 본 뒤 채운다.
EXPECT_DIFF: dict[str, str] = {
    "bash_large": (
        "3만 자를 넘는 출력은 파일로 옮겨지고 모델은 경로와 미리보기만 받는다. 훅은 그 결과"
        "(`persistedOutputPath` 가 있다)를 0자로 센다"
    ),
}


def write_png(path: Path) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00\xff\x00\x00")
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")
    )


def write_fixture(out: Path) -> Path:
    fixture = out / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"line {n} of the large result probe" for n in range(1, LINES + 1))
    (fixture / "lines.txt").write_text(body + "\n", encoding="utf-8", newline="\n")
    korean = "\n".join(f"{n}번째 줄은 한글로 채운 줄이다" for n in range(1, 21))
    (fixture / "korean.txt").write_text(korean + "\n", encoding="utf-8", newline="\n")
    write_png(fixture / "pixel.png")
    return fixture


def run_session(out: Path, fixture: Path) -> None:
    log = (out / "posttool.jsonl").as_posix()
    hook = {
        "type": "command",
        "command": (
            f'uv run --project "{ROOT.as_posix()}" --no-sync python'
            f' "{(HERE / "dump_posttool.py").as_posix()}" "{log}"'
        ),
        "timeout": 30,
    }
    settings = out / "settings.json"
    settings.write_text(
        json.dumps(
            {"hooks": {"PostToolUse": [{"matcher": "Read|Bash|PowerShell", "hooks": [hook]}]}}
        ),
        encoding="utf-8",
    )
    (out / "posttool.jsonl").unlink(missing_ok=True)
    steps = "\n".join(f"{n}. {call.instruction}" for n, call in enumerate(calls(fixture), start=1))
    prompt = (
        "아래 도구 호출을 적힌 차례대로 하나씩, 한 번에 하나만 부른다. 결과를 설명하지 않는다.\n"
        f"{steps}\n모두 마치면 '끝' 이라고만 답한다."
    )
    tools = "Read,Bash,PowerShell"
    with (out / "stream.jsonl").open("wb") as stream, (out / "stream.err").open("wb") as err:
        # 프롬프트는 stdin 으로 준다. `--tools` 뒤에 두면 가변 인자가 삼킨다(canary_init).
        subprocess.run(
            [
                "claude",
                "-p",
                "--setting-sources",
                "project,local",
                "--strict-mcp-config",
                "--model",
                "haiku",
                "--output-format",
                "stream-json",
                "--verbose",
                "--max-turns",
                "20",
                "--tools",
                tools,
                "--allowed-tools",
                tools,
                "--settings",
                str(settings),
            ],
            input=prompt.encode("utf-8"),
            stdout=stream,
            stderr=err,
            cwd=out,
            check=False,
            timeout=900,
        )


def read_jsonl(path: Path) -> list[dict[str, object]]:
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


def result_block(transcript: Path, tool_use_id: str) -> dict[str, object] | None:
    for record in read_jsonl(transcript):
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_result"
                and block.get("tool_use_id") == tool_use_id
            ):
                return {str(key): value for key, value in block.items()}
    return None


def block_text(block: dict[str, object]) -> tuple[str, bool]:
    """본문의 글(글 블록을 이은 것)과 그림 블록이 있는지."""
    content = block.get("content")
    if isinstance(content, str):
        return content, False
    if not isinstance(content, list):
        return "", False
    texts: list[str] = []
    image = False
    for part in content:
        if isinstance(part, dict) and part.get("type") == "text":
            texts.append(str(part.get("text", "")))
        elif isinstance(part, dict) and part.get("type") == "image":
            image = True
    return "".join(texts), image


def enrich(out: Path) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for payload in read_jsonl(out / "posttool.jsonl"):
        transcript = payload.get("transcript_path")
        tool_use_id = payload.get("tool_use_id")
        block = (
            result_block(Path(transcript), tool_use_id)
            if isinstance(transcript, str) and isinstance(tool_use_id, str)
            else None
        )
        record: dict[str, object] = {"payload": payload}
        if block is not None:
            text, image = block_text(block)
            record["recorded"] = {
                "chars": len(text),
                "head": text[:200],
                "tail": text[-200:],
                "image": image,
                "is_error": block.get("is_error", False),
            }
        enriched.append(record)
    return enriched


def label_of(payload: dict[str, object], fixture_calls: list[Call]) -> str | None:
    """페이로드가 `CALLS` 의 어느 호출인지. 입력으로 가른다."""
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    fields = tool_input if isinstance(tool_input, dict) else {}
    if tool == "Read":
        path = str(fields.get("file_path", "")).replace("\\", "/")
        ranged = "offset" in fields or "limit" in fields
        if path.endswith("lines.txt"):
            return "read_ranged" if ranged else "read_whole"
        if path.endswith("korean.txt"):
            return "read_korean"
        if path.endswith("pixel.png"):
            return "read_image"
        return None
    command = str(fields.get("command", ""))
    if tool == "Bash":
        if f"seq 1 {SEQ_LARGE}" in command:
            return "bash_large"
        if f"seq 1 {SEQ_SMALL}" in command:
            return "bash_small"
        if "err-line" in command:
            return "bash_stderr"
        return None
    if tool == "PowerShell" and f"1..{POWERSHELL_ROWS}" in command:
        return "powershell_rows"
    del fixture_calls
    return None


def judge(path: Path) -> int:
    sys.path.insert(0, str(ROOT))
    from tools.hook_large_result import HookPayload, result_chars

    records = read_jsonl(path)
    expected = [call.label for call in calls(Path("fixture"))]
    seen: dict[str, int] = {}
    problems: list[str] = []
    for record in records:
        payload = record.get("payload")
        recorded = record.get("recorded")
        if not isinstance(payload, dict):
            continue
        label = label_of(payload, [])
        response = payload.get("tool_response")
        keys = sorted(response) if isinstance(response, dict) else type(response).__name__
        hook_payload: HookPayload = json.loads(json.dumps(payload))
        counted = result_chars(hook_payload)
        if label is None:
            print(f"? {payload.get('tool_name')} {payload.get('tool_input')} — CALLS 밖의 호출")
            continue
        seen[label] = seen.get(label, 0) + 1
        if not isinstance(recorded, dict):
            problems.append(f"{label}: 측정 아님 — 기록에 그 tool_result 가 없다")
            continue
        chars = recorded.get("chars")
        print(
            f"{label}: tool_response 키 {keys}\n"
            f"  훅의 셈 {counted}, 기록 {chars}, 그림 {recorded.get('image')},"
            f" 오류 {recorded.get('is_error')}\n"
            f"  기록 앞 {str(recorded.get('head'))[:80]!r}\n"
            f"  기록 끝 {str(recorded.get('tail'))[-80:]!r}"
        )
        if counted != chars:
            gap = f"차이 {counted - chars if isinstance(chars, int) else '?'}"
            if label in EXPECT_DIFF:
                print(f"  기대한 차이({gap}): {EXPECT_DIFF[label]}")
            else:
                problems.append(f"{label}: 훅의 셈 {counted} 와 기록 {chars} 가 다르다({gap})")
        elif label in EXPECT_DIFF:
            problems.append(f"{label}: 다를 것으로 기대했는데 같다")
    for label in expected:
        if seen.get(label, 0) != 1:
            problems.append(f"{label}: 측정 아님 — 기록이 {seen.get(label, 0)}건이다")
    for problem in problems:
        print(f"[문제] {problem}")
    print(f"기록 {len(records)}건, 문제 {len(problems)}건.")
    return 1 if problems else 0


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args[:1] == ["judge"]:
        return judge(Path(args[1]) if len(args) > 1 else HERE / "payloads.jsonl")
    if args[:1] != ["run"] or len(args) < 2:
        print("쓰는 법: run.py run <저장소 밖 디렉터리> [--save] | run.py judge [payloads.jsonl]")
        return 2
    out = Path(args[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    fixture = write_fixture(out)
    run_session(out, fixture)
    target = out / "payloads.jsonl"
    with target.open("w", encoding="utf-8", newline="\n") as file:
        for record in enrich(out):
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    if "--save" in args:
        shutil.copyfile(target, HERE / "payloads.jsonl")
    return judge(target)


if __name__ == "__main__":
    raise SystemExit(main())
