"""release-image 명세가 고를 취약점 점검 도구(Trivy 와 Grype), "고칠 수 있는 심각한 취약점"의 문턱,
SBOM 형식의 재료를 잰다. 고르지는 않고 회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/release-image/probes/release_mechanics/scan_tools.py
        [--trivy-cache <볼륨>] [--grype-cache <볼륨>] [--repeats 2] [--work <원본 출력을 둘 폴더>]

필요한 것. 도는 Docker 데몬과 로컬에 이미 있는 대상 이미지 셋(아래 TARGETS 의 digest 참조). 점검
도구와 보조 이미지는 digest 로 고정했고 없으면 받는다. 대상은 `docker save` 로 `ri-rel-scan-in`
볼륨에 tar 로 두고 도구가 그 tar 를 읽는다(도구에 Docker 소켓을 주지 않는다). DB 는 볼륨에 둔다.
--trivy-cache·--grype-cache 로 이미 받은 볼륨을 주면 그것을 쓰고 지우지 않는다. 주지 않으면
`ri-rel-scan-trivy`·`ri-rel-scan-grype` 를 만들어 받고 끝에 지운다(손으로 본 날 풀어 둔 크기가 Trivy
약 1.7 GB, Grype 약 3.4 GB 였다). Trivy 는 `--skip-version-check`· `--disable-telemetry` 로, Grype
와 Syft 는 앱 갱신 확인을 끄고 돈다. 명령마다 종료 코드와 stderr 는 --work(없으면 시스템 임시
폴더)의 raw.log 에, 점검과 SBOM 의 stdout 은 회차마다 파일로 남긴다. 띄우는 컨테이너는 이름이
`ri-rel-scan-` 로 시작하고 끝에서 지운다.

"고칠 수 있다"는 문턱 플래그가 남기는 것과 같게 센다. Trivy 는 `--ignore-unfixed` 가 버리는
상태(affected, will_not_fix, fix_deferred, end_of_life) 밖의 것, Grype 는 `fix.state` 가 fixed 인
것이다. 건수는 꾸러미와 취약점 식별자의 짝(행)이고 CVE 수는 따로 적는다. Grype 의 GHSA 식별자는 관련
CVE 가 있으면 그 CVE 로 바꿔 센다.

갈래
- db. DB 를 받거나 새 판인지 보는 데 걸린 시간, 받은 자리, 볼륨 크기. 표지는 Trivy `--version` 이 DB
  판을 찍고 Grype `db status` 가 valid 인 것이다.
- scan. 거르지 않은 JSON 점검을 --repeats 번. 걸린 시간(컨테이너를 띄우는 시간 포함)과 고칠 수 있는
  Critical·High 건수. 표지는 JSON 이 풀리고 그 안의 OS 가 대상의 OS(debian 과 주 판)인 것이다.
- gate. 문턱 플래그(Critical 만, Critical 과 High)의 종료 코드와 출력 건수가 거르지 않은 JSON 에서
  따로 센 건수와 맞는가. 표지는 scan 의 표지에 더해 종료 코드가 0 이나 그 도구의 문턱 코드(Trivy 는
  `--exit-code` 로 준 10, Grype 는 2)인 것이다.
- error. 없는 입력을 줬을 때의 종료 코드가 문턱 코드와 갈리는가. 표지는 없는 입력을 탓하는 문구다.
- compare. 같은 대상에서 두 도구가 고칠 수 있는 Critical·High 로 센 CVE 가 어떻게 겹치는가. 표지는
  두 도구의 첫 scan 회차가 측정인 것이다.
- sbom. Syft 와 Trivy 의 SPDX JSON·CycloneDX JSON 의 크기, 판, 꾸러미 수. 표지는 형식의 머리 칸이다.

못 보는 것. GitHub 러너에서의 시간과 DB 받는 시간, 공식 액션(trivy-action, scan-action)을 거친 동작,
amd64 밖의 플랫폼, 다른 날의 DB(건수는 그날 DB 의 것이고 DB 가 바뀌면 바뀐다). 결과는 같은 폴더의
README.md 에 있다.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import secrets
import subprocess
import sys
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeGuard

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

# 2026-11-13 에 받은 이미지다. Trivy 0.76.2, Grype 0.121.3, Syft 1.57.1, alpine 3.22.8.
TRIVY = (
    "ghcr.io/aquasecurity/trivy"
    "@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb"
)
GRYPE = (
    "ghcr.io/anchore/grype@sha256:13113eeceab017260370cf540e1d25442c59665fd07d1b09b66d63bb0c282887"
)
SYFT = (
    "ghcr.io/anchore/syft@sha256:03215d0e98b661d0ecbc8575dbc14d65be1743b5de5df6410aecb7e80f95b060"
)
HELPER = "alpine@sha256:49340b346798875b5592e5d420241f2f9cfba5f47e62ebb1446a1b34734e898f"
IN_VOLUME = "ri-rel-scan-in"
OWN_CACHES = {"trivy": "ri-rel-scan-trivy", "grype": "ri-rel-scan-grype"}
TRIVY_UNFIXED = ("affected", "will_not_fix", "fix_deferred", "end_of_life")
TRIVY_QUIET = ("--no-progress", "--skip-version-check", "--disable-telemetry")
GATE_CODES = {"trivy": 10, "grype": 2}
THRESHOLDS = {"critical": ("CRITICAL",), "critical+high": ("CRITICAL", "HIGH")}
SEVERITY_ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NEGLIGIBLE", "UNKNOWN")
TOOLS = ("trivy", "grype")


@dataclass(frozen=True)
class Target:
    name: str
    reference: str
    major: str  # debian 의 주 판
    role: str


TARGETS = (
    Target(
        "python-3.12.10-slim-bookworm",
        "python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db",
        "12",
        "양성 대조(손 실행에서 두 도구가 고칠 수 있는 Critical 을 냈다)",
    ),
    Target(
        "python-3.12-slim-trixie",
        "python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b",
        "13",
        "후보(Python 3.12.16, 2026-11-05 이미지)",
    ),
    Target(
        "node-24-trixie-slim",
        "node@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0",
        "13",
        "후보(Node 24.22.3, 2026-11-11 이미지)",
    ),
)


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str
    seconds: float

    @property
    def tail(self) -> str:
        lines = [line for line in (self.err or self.out).splitlines() if line.strip()]
        return lines[-1].strip() if lines else ""


@dataclass(frozen=True)
class Finding:
    cve: str
    package: str
    kind: str
    severity: str
    fixable: bool


@dataclass(frozen=True)
class Report:
    done: Done
    findings: tuple[Finding, ...] = ()
    os_seen: str = ""
    parsed: bool = False

    def rows(self, severities: tuple[str, ...]) -> list[Finding]:
        return [one for one in self.findings if one.fixable and one.severity in severities]

    def cves(self, severities: tuple[str, ...]) -> set[str]:
        return {one.cve for one in self.rows(severities)}

    def matches(self, target: Target) -> bool:
        return self.parsed and self.os_seen.startswith(f"debian {target.major}")

    def shape(self) -> tuple[int, int, int]:
        return (
            len(self.rows(("CRITICAL",))),
            len(self.rows(("HIGH",))),
            len(self.findings),
        )


@dataclass
class Probe:
    work: Path
    token: str
    rounds: Rounds = field(default_factory=Rounds)
    count: int = 0

    def name(self) -> str:
        self.count += 1
        return f"ri-rel-scan-{self.token}-{self.count}"

    def run(self, args: list[str], *, timeout: float = 900, keep: str = "") -> Done:
        started = time.monotonic()
        try:
            done = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
            result = Done(done.returncode, done.stdout, done.stderr, time.monotonic() - started)
        except subprocess.TimeoutExpired:
            result = Done(-1, "", f"시간 제한 {timeout}초를 넘겼다", time.monotonic() - started)
        shown = result.out
        if keep:
            (self.work / f"{keep}.out").write_text(result.out, encoding="utf-8", newline="\n")
            shown = f"(stdout {len(result.out.encode('utf-8'))} 바이트는 {keep}.out)"
        with (self.work / "raw.log").open("a", encoding="utf-8", newline="\n") as log:
            log.write(
                f"$ {' '.join(args)}\n[exit {result.code}, {result.seconds:.1f}초]\n"
                f"{shown}\n{result.err}\n"
            )
        return result

    def note(self, slot: Slot, *, measured: bool, result: str) -> None:
        slot.mark(measured=measured, result=result)
        print(f"{'측정' if measured else '측정 아님'}\t{slot.label}\t{result}", flush=True)


def is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def mapping(value: object) -> dict[str, object]:
    return value if is_object(value) else {}


def items(value: object) -> list[object]:
    return list(value) if is_list(value) else []


def load(text: str) -> dict[str, object]:
    try:
        return mapping(json.loads(text))
    except json.JSONDecodeError:
        return {}


def slug(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9.+-]+", "_", label)


def parse_trivy(done: Done) -> Report:
    document = load(done.out)
    if "SchemaVersion" not in document:
        return Report(done)
    system = mapping(mapping(document.get("Metadata")).get("OS"))
    found: list[Finding] = []
    for result in items(document.get("Results")):
        block = mapping(result)
        kind = f"{block.get('Class')}/{block.get('Type')}"
        for entry in items(block.get("Vulnerabilities")):
            vulnerability = mapping(entry)
            status = str(vulnerability.get("Status", ""))
            found.append(
                Finding(
                    str(vulnerability.get("VulnerabilityID")),
                    str(vulnerability.get("PkgName")),
                    kind,
                    str(vulnerability.get("Severity", "")).upper(),
                    fixable=status not in TRIVY_UNFIXED,
                )
            )
    seen = f"{system.get('Family')} {system.get('Name')}"
    return Report(done, tuple(found), seen, parsed=True)


def parse_grype(done: Done) -> Report:
    document = load(done.out)
    if "matches" not in document or "descriptor" not in document:
        return Report(done)
    distro = mapping(document.get("distro"))
    found: list[Finding] = []
    for entry in items(document.get("matches")):
        match = mapping(entry)
        vulnerability = mapping(match.get("vulnerability"))
        artifact = mapping(match.get("artifact"))
        identifier = str(vulnerability.get("id"))
        related = [
            str(mapping(one).get("id")) for one in items(match.get("relatedVulnerabilities"))
        ]
        cves = [one for one in related if one.startswith("CVE-")]
        if not identifier.startswith("CVE-") and cves:
            identifier = cves[0]
        found.append(
            Finding(
                identifier,
                str(artifact.get("name")),
                str(artifact.get("type")),
                str(vulnerability.get("severity", "")).upper(),
                fixable=mapping(vulnerability.get("fix")).get("state") == "fixed",
            )
        )
    seen = f"{distro.get('name')} {distro.get('version')}"
    return Report(done, tuple(found), seen, parsed=True)


def trivy_args(probe: Probe, cache: str, *args: str) -> list[str]:
    return [
        "docker", "run", "--rm", "--name", probe.name(),
        "-v", f"{cache}:/root/.cache/trivy", "-v", f"{IN_VOLUME}:/in:ro", TRIVY, *args,
    ]  # fmt: skip


def grype_args(probe: Probe, cache: str, *args: str) -> list[str]:
    return [
        "docker", "run", "--rm", "--name", probe.name(),
        "-v", f"{cache}:/cache", "-e", "GRYPE_DB_CACHE_DIR=/cache",
        "-e", "GRYPE_DB_AUTO_UPDATE=false", "-e", "GRYPE_CHECK_FOR_APP_UPDATE=false",
        "-v", f"{IN_VOLUME}:/in:ro", GRYPE, *args,
    ]  # fmt: skip


def helper(probe: Probe, volume: str, *command: str) -> Done:
    return probe.run(
        ["docker", "run", "--rm", "--name", probe.name(), "-v", f"{volume}:/c", HELPER, *command],
        timeout=300,
    )


def volume_size(probe: Probe, volume: str) -> str:
    words = helper(probe, volume, "du", "-sk", "/c").out.split()
    if not words or not words[0].isdigit():
        return "모름"
    return f"{int(words[0]) / 1024 / 1024:.2f} GiB"


def save_target(probe: Probe, target: Target) -> bool:
    """대상을 `docker save` 로 볼륨에 tar 로 둔다. 볼륨 안의 크기가 0 보다 크면 참이다."""
    tar = f"{target.name}.tar"
    load_into = [
        "docker", "run", "--rm", "-i", "--name", probe.name(), "-v", f"{IN_VOLUME}:/in",
        HELPER, "sh", "-c", f"cat > /in/{tar}",
    ]  # fmt: skip
    # Popen 의 with 문은 빠져나갈 때 제한 없이 기다려, 데몬이 멈추면 아래 두 제한 시간이 무제한
    # 대기를 막지 못한다. 그래서 with 를 쓰지 않고, 시간을 넘기면 docker save 를 끄고 제한된
    # 시간만 거둔 뒤 예외를 넘긴다. kill 은 pid 가 아니라 거두지 않은 Popen 이 쥔 프로세스에 간다.
    save = subprocess.Popen(
        ["docker", "save", target.reference], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    try:
        loaded = subprocess.run(
            load_into, stdin=save.stdout, capture_output=True, timeout=900, check=False
        )
        if save.stdout is not None:
            save.stdout.close()
        saved = save.wait(timeout=120)
    except subprocess.TimeoutExpired:
        save.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            save.wait(timeout=30)
        raise
    finally:
        if save.stdout is not None:
            save.stdout.close()
    size = helper(probe, IN_VOLUME, "stat", "-c", "%s", f"/c/{tar}").out.strip()
    with (probe.work / "raw.log").open("a", encoding="utf-8", newline="\n") as log:
        log.write(f"$ docker save {target.reference} > {tar}: save {saved}, ")
        log.write(f"싣기 {loaded.returncode}, 크기 {size}\n")
    return saved == 0 and loaded.returncode == 0 and size.isdigit() and int(size) > 0


def scan(probe: Probe, tool: str, cache: str, tar: str, label: str, *extra: str) -> Report:
    if tool == "trivy":
        args = trivy_args(
            probe, cache, "image", "--input", f"/in/{tar}", "--skip-db-update",
            "--scanners", "vuln", *TRIVY_QUIET, "--format", "json", *extra,
        )  # fmt: skip
        return parse_trivy(probe.run(args, keep=slug(label)))
    args = grype_args(probe, cache, f"docker-archive:/in/{tar}", "-o", "json", *extra)
    return parse_grype(probe.run(args, keep=slug(label)))


def gate_flags(tool: str, severities: tuple[str, ...]) -> tuple[str, ...]:
    if tool == "trivy":
        joined = ",".join(severities)
        return ("--ignore-unfixed", "--severity", joined, "--exit-code", str(GATE_CODES[tool]))
    return ("--only-fixed", "--fail-on", "critical" if severities == ("CRITICAL",) else "high")


def section_db(probe: Probe, caches: dict[str, str]) -> None:
    with probe.rounds.round("db/trivy") as slot:
        cache = caches["trivy"]
        got = probe.run(
            trivy_args(probe, cache, "image", "--download-db-only", *TRIVY_QUIET), timeout=1800
        )
        shown = probe.run(trivy_args(probe, cache, "--version"), timeout=300)
        source = re.search(r'repo="([^"]+)"', got.err)
        updated = re.search(r"UpdatedAt: (\S+ \S+)", shown.out)
        probe.note(
            slot,
            measured=got.code == 0 and "Vulnerability DB" in shown.out,
            result=f"{'받았다' if 'successfully downloaded' in got.err else '받지 않았다'}"
            f"{' ' + source.group(1) if source else ''}, {got.seconds:.1f}초, "
            f"DB 갱신 {updated.group(1) if updated else '모름'}, 볼륨 {volume_size(probe, cache)}",
        )
    with probe.rounds.round("db/grype") as slot:
        cache = caches["grype"]
        got = probe.run(grype_args(probe, cache, "db", "update"), timeout=1800)
        status = probe.run(grype_args(probe, cache, "db", "status"), timeout=300)
        built = re.search(r"Built:\s+(\S+)", status.out)
        source = re.search(r"From:\s+(https?://[^/\s]+)", status.out)
        probe.note(
            slot,
            measured=got.code == 0 and re.search(r"Status:\s+valid", status.out) is not None,
            result=f"{'받았다' if 'updated to latest' in got.out else '받지 않았다'}"
            f"{' ' + source.group(1) if source else ''}, {got.seconds:.1f}초, "
            f"DB 지은 때 {built.group(1) if built else '모름'}, 볼륨 {volume_size(probe, cache)}",
        )


def describe(report: Report) -> str:
    critical, high = report.rows(("CRITICAL",)), report.rows(("HIGH",))
    return (
        f"고칠 수 있는 Critical {len(critical)}건(CVE {len({one.cve for one in critical})}), "
        f"High {len(high)}건(CVE {len({one.cve for one in high})}), 전체 {len(report.findings)}건"
    )


def section_scan(
    probe: Probe, caches: dict[str, str], saved: dict[str, bool], repeats: int
) -> dict[tuple[str, str], Report]:
    first: dict[tuple[str, str], Report] = {}
    for target in TARGETS:
        for tool in TOOLS:
            key = (tool, target.name)
            for number in range(1, repeats + 1):
                label = f"scan/{tool}/{target.name}/{number}"
                with probe.rounds.round(label) as slot:
                    report = scan(probe, tool, caches[tool], f"{target.name}.tar", label)
                    measured = saved[target.name] and report.done.code == 0
                    measured = measured and report.matches(target)
                    again = ""
                    if key in first:
                        same = first[key].shape() == report.shape()
                        again = f", 첫 회와 건수가 {'같다' if same else '다르다'}"
                    elif measured:
                        first[key] = report
                    probe.note(
                        slot,
                        measured=measured,
                        result=f"{report.done.seconds:.1f}초, {describe(report)} "
                        f"({report.os_seen or '풀지 못했다'}){again}",
                    )
    return first


def section_gate(
    probe: Probe, caches: dict[str, str], first: dict[tuple[str, str], Report]
) -> None:
    for target in TARGETS:
        for tool in TOOLS:
            base = first.get((tool, target.name))
            for name, severities in THRESHOLDS.items():
                label = f"gate/{tool}/{target.name}/{name}"
                with probe.rounds.round(label) as slot:
                    flags = gate_flags(tool, severities)
                    report = scan(probe, tool, caches[tool], f"{target.name}.tar", label, *flags)
                    expected = len(base.rows(severities)) if base else -1
                    shown = len(report.rows(severities))
                    want = GATE_CODES[tool] if expected > 0 else 0
                    agrees = report.done.code == want and shown == expected
                    allowed = report.done.code in (0, GATE_CODES[tool])
                    probe.note(
                        slot,
                        measured=base is not None and report.matches(target) and allowed,
                        result=f"`{' '.join(flags)}` 종료 {report.done.code}, "
                        f"거르지 않은 JSON 으로 센 것 {expected}건, 문턱 출력 {shown}건, "
                        f"{'맞다' if agrees else '어긋난다'}",
                    )


def section_error(probe: Probe, caches: dict[str, str]) -> None:
    markers = {"trivy": "no such file or directory", "grype": "no source providers"}
    for tool in TOOLS:
        label = f"error/{tool}"
        with probe.rounds.round(label) as slot:
            flags = gate_flags(tool, THRESHOLDS["critical+high"])
            report = scan(probe, tool, caches[tool], "ri-rel-absent.tar", label, *flags)
            code = report.done.code
            apart = code not in (0, GATE_CODES[tool])
            probe.note(
                slot,
                measured=markers[tool] in report.done.err,
                result=f"종료 {code}, 문턱 코드 {GATE_CODES[tool]} 와 "
                f"{'갈린다' if apart else '갈리지 않는다'}",
            )


def rating(report: Report, cve: str) -> str:
    """그 도구가 그 CVE 를 어떻게 냈는지. 가장 높은 심각도와 고칠 수 있는지다."""
    rows = [one for one in report.findings if one.cve == cve]
    if not rows:
        return "내지 않음"
    best = min(rows, key=lambda one: SEVERITY_ORDER.index(one.severity))
    return best.severity + ("" if best.fixable else "(안 고침)")


def section_compare(probe: Probe, first: dict[tuple[str, str], Report]) -> None:
    for target in TARGETS:
        with probe.rounds.round(f"compare/{target.name}") as slot:
            trivy, grype = first.get(("trivy", target.name)), first.get(("grype", target.name))
            if trivy is None or grype is None:
                probe.note(slot, measured=False, result="두 도구의 첫 scan 회차가 측정이 아니다")
                continue
            parts: list[str] = []
            for name, severities in THRESHOLDS.items():
                left, right = trivy.cves(severities), grype.cves(severities)
                parts.append(
                    f"{name} 둘 다 {len(left & right)}, Trivy 만 {len(left - right)}, "
                    f"Grype 만 {len(right - left)}"
                )
            severities = THRESHOLDS["critical+high"]
            only_grype = grype.cves(severities) - trivy.cves(severities)
            only_trivy = trivy.cves(severities) - grype.cves(severities)
            kinds = Counter(one.kind for one in grype.rows(severities) if one.cve in only_grype)
            told = Counter(rating(trivy, cve) for cve in only_grype)
            back = Counter(rating(grype, cve) for cve in only_trivy)
            parts.append(f"Grype 만인 것을 Trivy 는 {dict(told)}, 그 꾸러미 종류 {dict(kinds)}")
            parts.append(f"Trivy 만인 것을 Grype 는 {dict(back)}")
            probe.note(slot, measured=True, result="; ".join(parts))


def section_sbom(probe: Probe, caches: dict[str, str], saved: dict[str, bool]) -> None:
    target = TARGETS[1]
    tar = f"/in/{target.name}.tar"
    for tool, form in (
        ("syft", "spdx-json"),
        ("syft", "cyclonedx-json"),
        ("trivy", "spdx-json"),
        ("trivy", "cyclonedx"),
    ):
        label = f"sbom/{tool}/{form}/{target.name}"
        with probe.rounds.round(label) as slot:
            if tool == "syft":
                args = [
                    "docker", "run", "--rm", "--name", probe.name(), "-v", f"{IN_VOLUME}:/in:ro",
                    "-e", "SYFT_CHECK_FOR_APP_UPDATE=false", SYFT, f"docker-archive:{tar}",
                    "-o", form,
                ]  # fmt: skip
            else:
                args = trivy_args(
                    probe, caches["trivy"], "image", "--input", tar, "--skip-db-update",
                    *TRIVY_QUIET, "--format", form,
                )  # fmt: skip
            done = probe.run(args, keep=slug(label))
            document = load(done.out)
            if "spdxVersion" in document:
                head = str(document["spdxVersion"])
                counted = f"꾸러미 {len(items(document.get('packages')))}, "
                counted += f"파일 {len(items(document.get('files')))}"
            elif document.get("bomFormat") == "CycloneDX":
                head = f"CycloneDX {document.get('specVersion')}"
                counted = f"구성 요소 {len(items(document.get('components')))}"
            else:
                head, counted = "", "풀지 못했다"
            probe.note(
                slot,
                measured=saved[target.name] and done.code == 0 and bool(head),
                result=f"{head or '형식 모름'}, {len(done.out.encode('utf-8'))} 바이트, "
                f"{counted}, {done.seconds:.1f}초",
            )


def cleanup(probe: Probe, volumes: list[str]) -> None:
    listed = probe.run(
        ["docker", "ps", "-a", "--filter", f"name=ri-rel-scan-{probe.token}-",
         "--format", "{{.Names}}"],
        timeout=60,
    )  # fmt: skip
    for name in listed.out.split():
        if name.startswith(f"ri-rel-scan-{probe.token}-"):
            probe.run(["docker", "rm", "-f", name], timeout=120)
    for volume in volumes:
        probe.run(["docker", "volume", "rm", volume], timeout=120)


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--trivy-cache", help="이미 받은 Trivy DB 볼륨(지우지 않는다)")
    parser.add_argument("--grype-cache", help="이미 받은 Grype DB 볼륨(지우지 않는다)")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--work", type=Path)
    arguments = parser.parse_args()
    work = arguments.work or Path(tempfile.mkdtemp(prefix="ri-rel-scan-"))
    work.mkdir(parents=True, exist_ok=True)
    probe = Probe(work=work, token=secrets.token_hex(3))
    caches = {
        "trivy": arguments.trivy_cache or OWN_CACHES["trivy"],
        "grype": arguments.grype_cache or OWN_CACHES["grype"],
    }
    made = [IN_VOLUME, *(caches[tool] for tool in TOOLS if caches[tool] == OWN_CACHES[tool])]
    print(f"원본 출력: {work / 'raw.log'}", flush=True)
    try:
        for volume in made:
            probe.run(["docker", "volume", "create", volume], timeout=60)
        for image in (TRIVY, GRYPE, SYFT, HELPER):
            if probe.run(["docker", "image", "inspect", image], timeout=60).code != 0:
                probe.run(["docker", "pull", "-q", image], timeout=900)
        saved = {target.name: save_target(probe, target) for target in TARGETS}
        section_db(probe, caches)
        first = section_scan(probe, caches, saved, arguments.repeats)
        section_gate(probe, caches, first)
        section_error(probe, caches)
        section_compare(probe, first)
        section_sbom(probe, caches, saved)
    finally:
        cleanup(probe, made)
    print(probe.rounds.summary())
    return probe.rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
