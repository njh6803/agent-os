"""임포트와 paths 의 경계 사례. 지침 판정자의 결과와 Claude Code 의 실측을 나란히 낸다.

PR #100 리뷰(CodeRabbit: 여러 줄 HTML 주석 속 허용 임포트)를 검증한 워크플로가 만든 사례를 옮겼다.
쓰는 법(저장소 루트에서, 파이썬은 `PYTHONUTF8=1 uv run python`):
  cases.py judge              사례마다 claude_md_problems / imports_outside_claude_md 결과
  cases.py build <트리>        탐침 트리. 사례마다 임포트된 파일(a<id>.md)이나 rules 파일 하나
  cases.py summarize <훅 로그>  InstructionsLoaded 로그에서 사례마다 대상 파일이 실렸는지
사례 id 는 `tests/tools/test_check_instructions.py` 의 pytest id 와 같다. 트리는 저장소 밖에 만든다.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
import check_instructions as ci  # noqa: E402

ALLOWED = "@docs/constitution/principles.md"
OTHER = "@docs/PRD.md"
RULE_OTHER = "@docs/x.md"

# (id, 자리, 이름, 본문). 자리 claude 는 판정자가 CLAUDE.md 로 보고, 탐침은 루트 CLAUDE.md 가
# 임포트한 파일(a<id>.md)에 넣는다 — 사례마다 루트를 따로 세우지 않으려고다. 루트 CLAUDE.md 에는
# c01 의 모양(t_root)만 있다. rules 는 paths 없는 rules 파일이다. imported 는 판정자가 헌법으로,
# 탐침이 a<id>.md 로 둔다(둘 다 임포트된 파일이다).
CASES: list[tuple[str, str, str, str]] = [
    ("c01", "claude", "여러 줄 블록 주석 안 단독 줄", f"# P\n\n<!--\n{ALLOWED}\n-->\n\n본문\n"),
    ("c02", "claude", "여는 줄에 글이 있는 여러 줄 주석", f"# P\n\n<!-- 메모\n{ALLOWED}\n-->\n"),
    ("c03", "claude", "세 칸 들여쓴 <!--", f"# P\n\n   <!--\n{ALLOWED}\n   -->\n"),
    ("c04", "claude", "네 칸 들여쓴 <!--", f"# P\n\n    <!--\n{ALLOWED}\n-->\n"),
    ("c05", "claude", "문단 바로 뒤에 연 주석", f"원칙:\n<!--\n{ALLOWED}\n-->\n"),
    ("c06", "claude", "닫히지 않은 <!--", f"# P\n\n<!--\n{ALLOWED}\n"),
    ("c07", "claude", "닫히지 않은 펜스", f"# P\n\n```\n{ALLOWED}\n"),
    ("c08", "claude", "백틱 네 개 펜스", f"# P\n\n````\n{ALLOWED}\n````\n"),
    ("c09", "claude", "```` 펜스 안의 ``` 쌍", f"# P\n\n````md\n```\n{ALLOWED}\n```\n````\n"),
    ("c10", "claude", "여러 줄 코드 스팬", f"원칙은 `\n{ALLOWED}\n` 에 있다.\n"),
    ("c11", "claude", "<div> 블록 안", f"# P\n\n<div>\n{ALLOWED}\n</div>\n"),
    ("c12", "claude", "<details> 와 빈 줄로 끊긴 문단", f"<details>\n\n{ALLOWED}\n\n</details>\n"),
    ("c13", "claude", "인용문", f"> {ALLOWED}\n"),
    ("c14", "claude", "목록 항목", f"- {ALLOWED}\n"),
    ("c15", "claude", "문장 속", f"원칙은 {ALLOWED} 에 있다.\n"),
    ("c16", "claude", "앞 두 칸", f"  {ALLOWED}\n"),
    ("c17", "claude", "줄 끝 공백", f"{ALLOWED} \n"),
    ("c23", "claude", "폼피드로 가른 한 줄 주석", f"<!--\x0c{ALLOWED}\x0c-->\n"),
    ("c25", "claude", "주석이 ``` 를 품고 닫힌 뒤", f"<!--\n```\n-->\n{ALLOWED}\n```\n"),
    ("c26", "claude", "펜스 안 <!-- 뒤", f"```\n<!--\n```\n{ALLOWED}\n\n<!-- 끝 -->\n"),
    ("c27", "claude", "주석 둘 사이", f"<!-- a -->\n{ALLOWED}\n<!-- b -->\n"),
    ("c28", "claude", "줄 중간에서 연 주석", f"메모 <!--\n{ALLOWED}\n-->\n"),
    ("c29", "claude", "한 줄 주석 뒤 같은 줄", f"<!-- 메모 --> {ALLOWED}\n"),
    ("c30", "claude", "헌법 뒤 같은 줄 주석", f"{ALLOWED} <!-- 헌법 -->\n"),
    ("c32", "claude", "한 줄 주석 속 다른 경로", f"{ALLOWED}\n\n<!-- 옛 {OTHER} -->\n"),
    ("c33", "claude", "여러 줄 주석 속 다른 경로", f"{ALLOWED}\n\n<!--\n{OTHER}\n-->\n"),
    ("c34", "claude", "들여쓴 코드 속 다른 경로", f"{ALLOWED}\n\n    cat {OTHER}\n"),
    ("c36", "claude", "인용문 안 펜스 속", f"{ALLOWED}\n\n> ```\n> {OTHER}\n> ```\n"),
    ("c37", "claude", "<div> 블록 속", f"{ALLOWED}\n\n<div>\n{OTHER}\n</div>\n"),
    ("c38", "claude", "프론트매터 속", f"---\nnote: {OTHER}\n---\n{ALLOWED}\n"),
    ("c39", "claude", "이중 백틱 스팬 뒤", f"{ALLOWED}\n\n``코드`` {OTHER} `a`\n"),
    ("c40", "claude", "네 칸 들여쓴 ``` 사이", f"{ALLOWED}\n\n    ```\n{OTHER}\n    ```\n"),
    ("c41", "claude", "더 긴 닫는 펜스 뒤", f"{ALLOWED}\n\n```\n코드\n````\n{OTHER}\n```\n"),
    ("c42", "claude", "굵게 쓴 경로", f"{ALLOWED}\n\n참고: **{OTHER}**\n"),
    ("c43", "claude", "링크 글자인 경로", f"{ALLOWED}\n\n[{OTHER}](https://example.com)\n"),
    ("c44", "claude", "인라인 태그 속", f"{ALLOWED}\n\n<b>{OTHER}</b> 참고\n"),
    ("c45", "claude", "#한글 조각", f"{ALLOWED}\n\n{OTHER}#범위 를 본다\n"),
    ("c46", "claude", "한글 파일 이름", f"{ALLOWED}\n\n@docs/회의록.md 를 본다\n"),
    # PR #100 셀프 리뷰가 새 판정자에 넣어 본 반례(c47~).
    ("c47", "claude", "한 줄 주석 다음 줄", f"<!-- 메모 -->\n{ALLOWED}\n"),
    ("c48", "claude", "문단 뒤 네 칸 들여쓴 <!--", f"원칙:\n    <!--\n{ALLOWED}\n-->\n"),
    ("c49", "claude", "문단 뒤 네 칸 들여쓴 ```", f"원칙:\n    ```\n{ALLOWED}\n    ```\n"),
    ("c50", "claude", "목록 표지 펜스 뒤", f"{ALLOWED}\n\n- ```\n  x\n  ```\n\n{OTHER}\n"),
    ("c51", "claude", "<div> 안의 ``` 뒤", f"{ALLOWED}\n\n<div>\n```\n</div>\n\n{OTHER}\n"),
    ("c52", "claude", "빈 줄 넘는 <!--", f"{ALLOWED}\n\n메모 <!-- a\n\n{OTHER}\n\n끝 -->\n"),
    ("c53", "claude", "주석 뒤 같은 줄에서 연 주석", f"<!-- a --> <!--\n{ALLOWED}\n-->\n"),
    ("c54", "claude", "빈 주석 <!-->", f"<!-->\n{ALLOWED}\n-->\n"),
    ("c55", "claude", "문단 속 주석 둘 사이", f"{ALLOWED}\n\n메모 <!-- a --> {OTHER} <!-- b -->\n"),
    ("c56", "claude", "목록 표지 펜스 안", f"# P\n\n- ```\n  {ALLOWED}\n  ```\n"),
    ("c57", "claude", "목록 펜스와 펜스 사이", f"- ```\n  x\n  ```\n\n{OTHER}\n\n```\ny\n```\n"),
    ("c58", "claude", "목록 펜스 뒤 허용", f"# P\n\n- ```\n  x\n  ```\n\n{ALLOWED}\n"),
    ("r01", "rules", "rules 여러 줄 주석 속", f"<!--\n{RULE_OTHER}\n-->\n본문\n"),
    ("r02", "imported", "헌법 한 줄 주석 속", f"# 원칙\n\n<!-- {RULE_OTHER} -->\n"),
]

# 깨진 YAML 과 정상 모양의 paths 규칙. 모두 sub/** 를 뜻하려 했다. 판정은 sub/file.txt 를
# Read 할 때.
PATH_RULES: dict[str, str] = {
    "b1_flow_unclosed": 'paths: ["sub/**"\n',
    "b2_other_key_broken": 'paths:\n  - "sub/**"\nbad: [unclosed\n',
    "b3_quote_unclosed": 'paths: "sub/**\n',
    "b4_tab_indent": 'paths:\n\t- "sub/**"\n',
    "b5_duplicate_key": 'paths: "zzz/**"\npaths: "sub/**"\n',
    "b6_bad_mapping": "paths: sub/**: x: y\n",
    "ok_block": 'paths:\n  - "sub/**"\n',
    "ok_comment_before_item": 'paths:\n  # 설명\n\n  - "sub/**"\n',
    "ok_unquoted": "paths: sub/**\n",
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def judge() -> None:
    for case_id, place, name, body in CASES:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            if place == "claude":
                _write(root / "CLAUDE.md", body)
                problems = ci.claude_md_problems(root)
            else:
                _write(root / "CLAUDE.md", ALLOWED + "\n")
                target = (
                    ".claude/rules/x.md" if place == "rules" else "docs/constitution/principles.md"
                )
                _write(root / target, body)
                problems = ci.imports_outside_claude_md(root)
        verdict = "빨강" if problems else "초록"
        print(f"{case_id} {verdict} at_imports={ci.at_imports(body)} :: {name}")
    for name, front in PATH_RULES.items():
        patterns = ci._paths_patterns("---\n" + front + "---\n")
        print(f"{name} patterns={patterns}")


def build(tree: Path) -> None:
    root_lines = ["카나리아 ROOT-0000", "", "<!--", "@t_root.md", "-->", ""]
    for case_id, place, _name, body in CASES:
        probe = (
            body.replace("docs/constitution/principles.md", f"t{case_id}.md")
            .replace("docs/PRD.md", f"p{case_id}.md")
            .replace("docs/회의록.md", f"k{case_id}회의록.md")
        )
        if place == "rules":
            probe = probe.replace("docs/x.md", f"../../p{case_id}.md")
            _write(tree / ".claude" / "rules" / f"r{case_id}.md", probe)
        else:
            _write(tree / f"a{case_id}.md", probe.replace("docs/x.md", f"p{case_id}.md"))
            root_lines.append(f"@a{case_id}.md")
        for prefix in ("t", "p"):
            _write(tree / f"{prefix}{case_id}.md", f"카나리아 {prefix.upper()}{case_id}\n")
    for name, front in PATH_RULES.items():
        _write(tree / ".claude" / "rules" / f"{name}.md", f"---\n{front}---\n\n카나리아 {name}\n")
    _write(tree / "kc46회의록.md", "카나리아 K46\n")
    _write(tree / "t_root.md", "카나리아 TROOT\n")
    _write(tree / "sub" / "file.txt", "hello\n")
    _write(tree / "CLAUDE.md", "\n".join(root_lines) + "\n")


def summarize(log: Path) -> None:
    loaded: dict[str, str] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.startswith("{") and '"file_path"' in line:
            record = json.loads(line)
            loaded[Path(record["file_path"]).name] = record.get("load_reason", "")
    print(f"root CLAUDE.md 주석 속 @t_root.md: {loaded.get('t_root.md', '안 실림')}")
    # 운반 파일이 실렸는지를 먼저 찍는다. 운반 파일이 안 실렸으면 두 칸의 "안 실림" 은 뜻이 없다.
    for case_id, place, name, body in CASES:
        carrier = f"r{case_id}.md" if place == "rules" else f"a{case_id}.md"
        allowed = loaded.get(f"t{case_id}.md", "안 실림") if ALLOWED in body else "-"
        other = loaded.get(f"p{case_id}.md", loaded.get(f"k{case_id}회의록.md", "안 실림"))
        if OTHER not in body and RULE_OTHER not in body and "회의록" not in body:
            other = "-"
        carried = loaded.get(carrier, "안 실림")
        print(f"{case_id} 운반 {carried} / 허용 {allowed} / 다른 {other} :: {name}")
    for name in PATH_RULES:
        print(f"{name}: {loaded.get(f'{name}.md', '안 실림')}")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "judge":
        judge()
    elif mode == "build":
        build(Path(sys.argv[2]))
    else:
        summarize(Path(sys.argv[2]))
