"""후보를 설치하면 무엇이 들어오는지, 네이티브 확장이 있는지, 저장소 락에 이미 있는지 본다.

두 가지를 잰다.

1. 후보 환경(`make_envs.py`)에 깔린 배포마다 판과 wheel 의 `Root-Is-Purelib`·`Tag`를 읽어, 저장소
   `uv.lock`의 같은 이름과 견준다.
2. `pyproject.toml`·`uv.lock`·`README.md`를 임시 디렉터리로 복사해 그 사본에서 `uv add --no-sync`를
   돌리고, 락의 패키지 집합이 어떻게 바뀌는지 본다. 저장소의 두 파일은 건드리지 않는다. PyPI 에
   닿는다.

저장소 루트에서 돈다. 인자 둘은 환경 루트와 락 사본을 둘 작업 디렉터리다.

    PYTHONUTF8=1 uv run python .scratch/web-widget/probes/jwt_verify/deps.py <환경> <작업>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

# uv add 에 넘기는 꼴. 판을 주지 않는다 — 실제로 `uv add`를 치면 무엇이 잠기는지가 측정 대상이다.
SPECS = {"pyjwt": "pyjwt[crypto]", "joserfc": "joserfc", "jwcrypto": "jwcrypto"}

LIST_DISTS = """
import importlib.metadata as m, json
rows = []
for d in m.distributions():
    lines = (d.read_text("WHEEL") or "").splitlines()
    purelib = [l.split(":", 1)[1].strip() for l in lines if l.startswith("Root-Is-Purelib")]
    tags = [l.split(":", 1)[1].strip() for l in lines if l.startswith("Tag")]
    rows.append({"name": d.metadata["Name"], "version": d.version,
                 "purelib": purelib[0] if purelib else "?", "tags": tags})
print(json.dumps(rows))
"""


def interpreter(env: Path) -> Path:
    windows = env / "Scripts" / "python.exe"
    return windows if windows.exists() else env / "bin" / "python"


def normalize(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def locked(lock: Path) -> dict[str, str]:
    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    return {normalize(p["name"]): p["version"] for p in data["package"] if "version" in p}


def installed(env_root: Path, name: str) -> list[dict[str, object]]:
    python = interpreter(env_root / name / ".venv")
    done = subprocess.run(
        [str(python), "-c", LIST_DISTS], capture_output=True, text=True, check=True
    )
    return json.loads(done.stdout)


def simulate_add(work: Path, name: str, spec: str, before: dict[str, str]) -> None:
    copy = work / name
    if copy.exists():
        shutil.rmtree(copy)
    copy.mkdir(parents=True)
    for file in ("pyproject.toml", "uv.lock", "README.md"):
        shutil.copyfile(ROOT / file, copy / file)
    done = subprocess.run(
        ["uv", "add", "--no-sync", spec], cwd=copy, capture_output=True, text=True
    )
    if done.returncode != 0:
        print(f"  uv add 실패: {done.stderr.strip()}")
        return
    after = locked(copy / "uv.lock")
    added = {k: v for k, v in after.items() if k not in before}
    removed = {k: v for k, v in before.items() if k not in after}
    changed = {k: (before[k], v) for k, v in after.items() if k in before and before[k] != v}
    project = tomllib.loads((copy / "pyproject.toml").read_text(encoding="utf-8"))
    declared = [d for d in project["project"]["dependencies"] if d.split("[")[0].startswith(name)]
    print(f"  pyproject 에 적힌 줄: {declared}")
    print(f"  락에 새로 든 패키지: {added if added else '없음'}")
    print(f"  락에서 빠진 패키지: {removed if removed else '없음'}")
    print(f"  판이 바뀐 패키지: {changed if changed else '없음'}")


def main() -> int:
    if len(sys.argv) != 3:
        print("인자: <환경 루트> <작업 디렉터리>", file=sys.stderr)
        return 2
    env_root = Path(sys.argv[1]).resolve()
    work = Path(sys.argv[2]).resolve()
    before = locked(ROOT / "uv.lock")
    print(f"저장소 uv.lock 패키지 {len(before)}개")
    for name in ("cryptography", "cffi", "pycparser", "pyjwt", "joserfc", "jwcrypto"):
        print(f"  락의 {name}: {before.get(name, '없음')}")
    for name, spec in SPECS.items():
        print(f"\n== {name}: 후보 환경에 깔린 것")
        for row in sorted(installed(env_root, name), key=lambda r: normalize(str(r["name"]))):
            key = normalize(str(row["name"]))
            lock = before.get(key)
            where = "락에 없음" if lock is None else f"락 {lock}"
            native = "순수 파이썬" if row["purelib"] == "true" else "네이티브"
            raw_tags = row["tags"]
            tags = ",".join(str(t) for t in raw_tags) if isinstance(raw_tags, list) else "?"
            print(f"  {row['name']} {row['version']} | {native} ({tags}) | {where}")
        print(f"== {name}: 락 사본에서 `uv add --no-sync {spec}`")
        simulate_add(work, name, spec, before)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
