"""zizmor 를 워크플로 하드닝의 판정자로 들일 때 ADR 0027 이 근거로 드는 측정.

저장소 루트에서
`uv run python .scratch/harness/probes/zizmor_gate.py [--zizmor 경로] [--ref 리비전] [--install N]`.
zizmor 는 `--zizmor` 로 주거나 PATH 에서 찾는다(`uv sync` 뒤의 `uv run` 이면 가상 환경의 것이다).
모두 `--offline` 으로 돌고 네트워크를 쓰지 않는다. `--install` 만 PyPI 에 닿는다.

  first-run  `--ref`(기본 61884df, 도입 전 main)의 `.github/workflows/*.yml` 과
             `.pre-commit-config.yaml` 을 임시 디렉터리로 꺼내, 설정 없이(zizmor 기본값)
             regular·auditor 페르소나로, 그리고 GitHub 소유 액션만 태그 고정을 허용하는 정책으로
             돌린 감사별 건수와 종료 코드
  mutation   작업 트리의 워크플로에서 `persist-credentials: false` 줄을 하나씩 지운 사본마다(비게
             된 `with:` 도 지운다) 저장소 설정(`.github/zizmor.yml`, 있으면)으로 돌려, 그 체크아웃
             단계를 가리키는 artipacked 가 나오고 종료 코드가 0 이 아닌지. 지우지 않은 사본에는
             artipacked 가 없다
  severity   체크아웃 하나만 둔 워크플로에서 checkout 판(v4~v7)과 upload-artifact 유무에 따른
             artipacked 의 등급
  strict     깨진 YAML 하나와 멀쩡한 워크플로 하나를 둔 트리에서 `--strict-collection` 이 없을
             때와 있을 때의 종료 코드. 없으면 깨진 파일을 경고만 하고 건너뛴다
  timing     작업 트리 전체(`.`)를 세 번 돈 시간
  install    `--install N` 을 주면, 이 PC 에서 uvx 한 번과 zizmor 를 dev 의존성으로 둔 임시
             프로젝트의 `uv sync` N 번(마지막 하나는 `--no-cache`)이 실행 파일을 남기는지
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
BASE_REF = "61884df"
POLICY = (
    "rules:\n  unpinned-uses:\n    config:\n      policies:\n"
    '        "actions/*": ref-pin\n        "*": hash-pin\n'
)
PERSIST = re.compile(r"^\s*persist-credentials:\s*false\s*$")


def zizmor(exe: str, args: list[str], cwd: Path) -> tuple[int, list, str]:
    """`--format json` 으로 돌려 종료 코드, 발견 목록, stderr 를 돌려준다."""
    proc = subprocess.run(
        [exe, "--offline", "--format", "json", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    findings = json.loads(proc.stdout) if proc.stdout.strip() else []
    return proc.returncode, findings, proc.stderr


def tally(findings: list) -> str:
    counts: Counter[str] = Counter()
    for finding in findings:
        counts[f"{finding['ident']}({finding['determinations']['severity']})"] += 1
    return ", ".join(f"{key} {n}" for key, n in sorted(counts.items())) or "없음"


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True
    )
    return proc.stdout


def first_run(exe: str, ref: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        (tree / ".github" / "workflows").mkdir(parents=True)
        names = git("ls-tree", "--name-only", f"{ref}:.github/workflows").split()
        for name in [f".github/workflows/{n}" for n in names] + [".pre-commit-config.yaml"]:
            (tree / name).write_text(git("show", f"{ref}:{name}"), encoding="utf-8")
        policy = tree / "policy.yml"
        policy.write_text(POLICY, encoding="utf-8")
        print(f"first-run ({ref}, 워크플로 {len(names)}개와 .pre-commit-config.yaml)")
        for label, args in (
            ("설정 없음, regular", ["--no-config", "."]),
            ("설정 없음, auditor", ["--no-config", "--persona", "auditor", "."]),
            ("GitHub 소유만 태그 허용, regular", ["--config", str(policy), "."]),
        ):
            code, findings, _ = zizmor(exe, args, tree)
            print(f"  {label}: 종료 {code}, {len(findings)}건 — {tally(findings)}")
            if label.startswith("GitHub"):
                for finding in findings:
                    feature = finding["locations"][0]["concrete"]["feature"]
                    uses = next(s for s in feature.splitlines() if "uses:" in s)
                    print(f"    {uses.strip()}")


def drop_line(lines: list[str], index: int) -> list[str]:
    """index 줄을 지우고, 그래서 빈 매핑이 된 바로 위의 `with:` 도 지운다."""
    out = lines[:index] + lines[index + 1 :]
    above = index - 1
    if above >= 0 and out[above].strip() == "with:":
        indent = len(out[above]) - len(out[above].lstrip())
        following = out[above + 1] if above + 1 < len(out) else ""
        if not following.strip() or len(following) - len(following.lstrip()) <= indent:
            del out[above]
    return out


def checkout_routes(text: str) -> set[tuple[str, int]]:
    """persist-credentials 가 false 가 아닌 actions/checkout 단계의 (잡, 단계 번호)."""
    workflow = yaml.safe_load(text)
    routes: set[tuple[str, int]] = set()
    for job_name, job in workflow["jobs"].items():
        for index, step in enumerate(job.get("steps", [])):
            if not str(step.get("uses", "")).startswith("actions/checkout@"):
                continue
            if (step.get("with") or {}).get("persist-credentials") is not False:
                routes.add((job_name, index))
    return routes


def artipacked_routes(findings: list, name: str) -> set[tuple[str, int]]:
    routes: set[tuple[str, int]] = set()
    for finding in findings:
        if finding["ident"] != "artipacked":
            continue
        for location in finding["locations"]:
            symbolic = location["symbolic"]
            path = str(symbolic["key"]["Local"]["verbatim_path"]).replace("\\", "/")
            keys = symbolic["route"]["route"]
            if path.endswith(name) and len(keys) >= 4 and keys[0] == {"Key": "jobs"}:
                routes.add((keys[1]["Key"], keys[3]["Index"]))
    return routes


def mutation(exe: str) -> None:
    config = ROOT / ".github" / "zizmor.yml"
    print(f"mutation (작업 트리, 설정 {'.github/zizmor.yml' if config.exists() else '없음'})")
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    args = gate_args()
    misses = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        (tree / ".github" / "workflows").mkdir(parents=True)
        if config.exists():
            shutil.copy(config, tree / ".github" / "zizmor.yml")
        for path in workflows:
            shutil.copy(path, tree / ".github" / "workflows" / path.name)
        code, findings, _ = zizmor(exe, args, tree)
        baseline = sum(1 for f in findings if f["ident"] == "artipacked")
        print(f"  지우지 않음: 종료 {code}, artipacked {baseline}건 — {tally(findings)}")
        for path in workflows:
            original = path.read_text(encoding="utf-8")
            lines = original.splitlines(keepends=True)
            target = tree / ".github" / "workflows" / path.name
            for index, line in enumerate(lines):
                if not PERSIST.match(line):
                    continue
                total += 1
                mutated = "".join(drop_line(lines, index))
                expected = checkout_routes(mutated) - checkout_routes(original)
                target.write_text(mutated, encoding="utf-8")
                code, findings, err = zizmor(exe, args, tree)
                got = artipacked_routes(findings, path.name)
                ok = code != 0 and bool(expected) and expected <= got
                misses += not ok
                verdict = "맞음" if ok else "어긋남"
                print(f"  {path.name}:{index + 1} 지움 → 기대 {sorted(expected)}, ", end="")
                print(f"종료 {code}, artipacked {sorted(got)} {verdict}")
                if not findings and err.strip():
                    print(f"    stderr: {err.strip().splitlines()[-1]}")
            target.write_text(original, encoding="utf-8")
    print(f"  어긋남 {misses}/{total}")


def strict(exe: str) -> None:
    print("strict (깨진 YAML 하나와 멀쩡한 워크플로 하나)")
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        workflows = tree / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "broken.yml").write_text(
            "on: push\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - with: [\n",
            encoding="utf-8",
        )
        (workflows / "ok.yml").write_text(
            "name: ok\non: push\npermissions: {}\njobs:\n  a:\n    name: a\n"
            "    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n",
            encoding="utf-8",
        )
        for label, args in (
            ("없음", ["--no-config", "."]),
            ("있음", ["--no-config", "--strict-collection", "."]),
        ):
            code, findings, _ = zizmor(exe, args, tree)
            print(f"  --strict-collection {label}: 종료 {code}, {len(findings)}건")


def severity(exe: str) -> None:
    """artipacked 의 등급이 checkout 의 판과 upload-artifact 의 유무에 따라 어떻게 갈리는지."""
    print("severity (설정 없음, 체크아웃 하나와 upload-artifact 유무)")
    upload = (
        "      - uses: actions/upload-artifact@v4\n"
        "        with:\n          name: x\n          path: .\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        workflows = tree / ".github" / "workflows"
        workflows.mkdir(parents=True)
        for version in ("v4", "v5", "v6", "v7"):
            cells = []
            for with_upload in (False, True):
                (workflows / "w.yml").write_text(
                    "name: w\non: push\npermissions: {}\njobs:\n  a:\n    name: a\n"
                    "    runs-on: ubuntu-latest\n    steps:\n"
                    f"      - uses: actions/checkout@{version}\n" + (upload if with_upload else ""),
                    encoding="utf-8",
                )
                _, findings, _ = zizmor(exe, ["--no-config", "."], tree)
                grades = [
                    f["determinations"]["severity"] for f in findings if f["ident"] == "artipacked"
                ]
                cells.append(f"업로드 {'있음' if with_upload else '없음'} {grades}")
            print(f"  checkout@{version}: " + ", ".join(cells))


def gate_args() -> list[str]:
    """게이트의 인자(`tools/run_checks.py`). 설정이 없던 도입 전 트리에서는 `--config` 를 뺀다."""
    if (ROOT / ".github" / "zizmor.yml").exists():
        return ["--strict-collection", "--config", ".github/zizmor.yml", "."]
    return ["--strict-collection", "."]


def timing(exe: str) -> None:
    seconds = []
    for _ in range(3):
        start = time.monotonic()
        zizmor(exe, gate_args(), ROOT)
        seconds.append(time.monotonic() - start)
    print("timing (작업 트리 전체): " + ", ".join(f"{s:.2f}s" for s in seconds))


def last_line(proc: subprocess.CompletedProcess[str]) -> str:
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    return lines[-1] if lines else ""


def install(version: str, rounds: int) -> None:
    print(f"install (zizmor=={version})")
    uv = shutil.which("uv")
    assert uv is not None
    proc = subprocess.run(
        [uv, "tool", "run", f"zizmor@{version}", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    print(f"  uvx: 종료 {proc.returncode} — {last_line(proc)}")
    for round_ in range(1, rounds + 1):
        no_cache = round_ == rounds
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "pyproject.toml").write_text(
                '[project]\nname = "syncprobe"\nversion = "0"\nrequires-python = "==3.12.*"\n\n'
                f'[dependency-groups]\ndev = ["zizmor=={version}"]\n',
                encoding="utf-8",
            )
            proc = subprocess.run(
                [uv, "sync", "-q", *(["--no-cache"] if no_cache else [])],
                cwd=project,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            found = any((project / ".venv").glob("*/zizmor*"))
            note = "" if proc.returncode == 0 else f" — {last_line(proc)}"
            label = f"uv sync {round_}{' --no-cache' if no_cache else ''}"
            exe = "있음" if found else "없음"
            print(f"  {label}: 종료 {proc.returncode}, 실행 파일 {exe}{note}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zizmor", default=shutil.which("zizmor"))
    parser.add_argument("--ref", default=BASE_REF)
    parser.add_argument("--install", type=int, default=0)
    args = parser.parse_args()
    if args.zizmor is None:
        raise SystemExit("zizmor 를 찾지 못했다. --zizmor 로 경로를 준다")
    proc = subprocess.run([args.zizmor, "--version"], capture_output=True, text=True, check=True)
    version = proc.stdout.split()[-1]
    print(f"zizmor {version} ({args.zizmor})")
    first_run(args.zizmor, args.ref)
    mutation(args.zizmor)
    severity(args.zizmor)
    strict(args.zizmor)
    timing(args.zizmor)
    if args.install:
        install(version, args.install)


if __name__ == "__main__":
    main()
