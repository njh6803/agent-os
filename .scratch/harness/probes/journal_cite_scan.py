"""커밋 하나의 추적 파일 전체에서 `일지 YYYY-MM-DD-NN` 인용을 세고, 없는 번호를 가리킨 것을 가른다.

`tools/sibling_overlap.py` 가 이 브랜치가 더한 줄의 없는 일지 인용을 1로 알리게 하며(대기열 254)
거짓 양성의 크기를 보려고 짓는다. 판정은 그 도구의 `JOURNAL_CITE`·`CODE_SPAN`·`dangling_cites` 를
그대로 불러 쓴다. 있는 번호는 그 커밋의 `docs/journal/` 에 든 파일 이름이다. 커밋을 읽으므로 같은
커밋이면 같은 수가 나온다. 커밋을 주지 않으면 HEAD 다.

출력:
- 읽은 커밋, 읽은 파일 수, 일지 수, `일지 ` 인용의 번호 수(목록 꼴 `·` 의 번호 하나하나).
- 없는 번호를 가리킨 인용(도구가 빼는 자리를 빼기 전)마다 파일:줄, 번호, 자리(인용 블록, 코드 스팬,
  나머지). 펜스 안인지는 가르지 않는다. 아래 줄과 견주어 본다.
- 도구의 `dangling_cites` 가 파일마다 내는 번호(인용 블록, 코드 스팬, 펜스 안을 뺀 뒤). 커밋 전체를
  "이 브랜치가 더한 줄" 로 친 값이다. 실제 도구는 브랜치가 더한 줄만 보므로, `origin/main` 을 주면
  이 줄은 main 에 이미 있어 어느 브랜치에서도 걸리지 않는 자리다.

재려는 상황이 났다는 표지는 읽은 파일과 일지와 인용이 모두 하나 이상인 것이다. 하나라도 0이면
측정이 아니라고 찍고 1로 끝난다. 돌리는 법은 저장소 루트에서
`uv run python .scratch/harness/probes/journal_cite_scan.py [커밋]`. 읽기만 한다.
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.sibling_overlap import CODE_SPAN, JOURNAL_CITE, dangling_cites  # noqa: E402


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def blobs(commit: str) -> dict[str, bytes]:
    """커밋의 추적 파일 경로 → 내용. `git cat-file --batch` 한 번으로 읽는다."""
    paths = [line for line in _git("ls-tree", "-r", "--name-only", commit).splitlines() if line]
    request = "".join(f"{commit}:{path}\n" for path in paths).encode("utf-8")
    raw = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=ROOT, input=request, capture_output=True, check=True
    ).stdout
    found: dict[str, bytes] = {}
    at = 0
    for path in paths:
        end = raw.index(b"\n", at)
        header = raw[at:end].split()
        at = end + 1
        if len(header) != 3 or header[1] != b"blob":
            continue  # 하위 모듈이나 없는 것
        size = int(header[2])
        found[path] = raw[at : at + size]
        at += size + 1
    return found


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    commit = _git("rev-parse", sys.argv[1] if len(sys.argv) > 1 else "HEAD").strip()
    files = blobs(commit)
    known = {PurePosixPath(path).name[:13] for path in files if path.startswith("docs/journal/")}
    read = 0
    total = 0
    raw: list[str] = []
    tool: list[str] = []
    for name, data in files.items():
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        read += 1
        for number, line in enumerate(text.split("\n"), start=1):
            bare = line.rstrip("\r")
            spans = "".join(CODE_SPAN.findall(bare))
            for cite in JOURNAL_CITE.finditer(bare):
                for key in cite[1].split("·"):
                    total += 1
                    if key in known:
                        continue
                    place = "인용 블록" if bare.startswith(">") else "나머지"
                    if place == "나머지" and key in spans:
                        place = "코드 스팬"
                    raw.append(f"{name}:{number} {key} {place}")
        if found := dangling_cites(text, known):
            tool.append(f"{name}: {', '.join(found)}")
    print(f"커밋 {commit[:8]}, 읽은 파일 {read}, 일지 {len(known)}, 일지 인용의 번호 {total}")
    print(f"없는 번호를 가리킨 인용(빼기 전) {len(raw)}:")
    print("\n".join(f"- {row}" for row in raw))
    print(f"도구의 dangling_cites 가 내는 파일 {len(tool)}:")
    print("\n".join(f"- {row}" for row in tool))
    if not (read and known and total):
        print("측정 아님: 읽은 파일, 일지, 인용 가운데 0인 것이 있다")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
