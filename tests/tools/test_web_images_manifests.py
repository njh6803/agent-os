"""web 이미지 셋(admin, widget, portal)의 Dockerfile 이 pnpm 작업공간과 어긋나지 않는지 보는 저장소
상태 시험.

세 Dockerfile 의 `manifests` 단계는 작업공간의 모든 패키지 매니페스트를 먼저 복사해
설치(`pnpm install --frozen-lockfile`)의 층을 소스와 가른다. 작업공간에 패키지가 하나 늘면
세 파일에 그 줄을 더해야 하는데, 빠뜨리면 이미지 빌드가 잠금 파일과 어긋나 실패한다. 그 실패는
이미지를 지을 때에야 드러나므로(CI 의 단독 배포 e2e 가 처음 본다) 여기서 Docker 없이 먼저 잡는다.
`corepack prepare pnpm@<판>` 도 `web/package.json` 의 `packageManager` 와 같아야 한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "web"
IMAGES = REPO / "deploy" / "images"
WEB_IMAGES = ("admin", "widget", "portal")

_COPY = re.compile(r"^COPY\s+(\S+)\s+(\S+)\s*$")
_PREPARE = re.compile(r"corepack prepare pnpm@(\S+)\s+--activate")


_WORKSPACE_ENTRY = re.compile(r"""^\s*-\s*["']?([^"'\s*]+)/\*["']?\s*$""")


def workspace_groups(web: Path) -> list[str]:
    """`pnpm-workspace.yaml` 의 `packages:` 가 가리키는 묶음 폴더(`apps/*` 면 `apps`)."""
    groups: list[str] = []
    inside = False
    for line in (web / "pnpm-workspace.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("packages:"):
            inside = True
            continue
        if inside:
            found = _WORKSPACE_ENTRY.match(line)
            if found is not None:
                groups.append(found.group(1))
            elif line.strip() != "" and not line.lstrip().startswith("#"):
                inside = False
    return groups


def workspace_manifests(web: Path) -> set[str]:
    """작업공간 패키지의 매니페스트 경로(web 기준, 슬래시 구분)."""
    found: set[str] = set()
    for group in workspace_groups(web):
        for child in sorted((web / group).iterdir()):
            if (child / "package.json").is_file():
                found.add(f"{group}/{child.name}/package.json")
    return found


def manifest_copies(dockerfile: str) -> set[str]:
    """`manifests` 단계가 패키지별로 복사하는 매니페스트 경로. 루트 파일 줄은 뺀다."""
    stage: list[str] = []
    inside = False
    for line in dockerfile.splitlines():
        if line.startswith("FROM "):
            inside = line.rstrip().endswith(" AS manifests")
            continue
        if inside:
            stage.append(line)
    copies: set[str] = set()
    for line in stage:
        found = _COPY.match(line)
        if found is not None and found.group(1) == found.group(2) and "/" in found.group(1):
            copies.add(found.group(1))
    return copies


def prepared_pnpm(dockerfile: str) -> str | None:
    found = _PREPARE.search(dockerfile)
    return None if found is None else found.group(1)


def package_manager_version(web: Path) -> str:
    declared = json.loads((web / "package.json").read_text(encoding="utf-8"))["packageManager"]
    name, _, version = declared.partition("@")
    assert name == "pnpm", declared
    return version.split("+")[0]


def test_이_저장소의_web_이미지_셋은_작업공간_패키지_매니페스트를_모두_복사한다() -> None:
    expected = workspace_manifests(WEB)
    # 훑은 범위가 비면 위반 0 으로 조용히 초록이다.
    assert len(expected) >= 8, expected
    for image in WEB_IMAGES:
        text = (IMAGES / f"{image}.Dockerfile").read_text(encoding="utf-8")
        copied = manifest_copies(text)
        assert copied, f"{image}.Dockerfile 의 manifests 단계를 찾지 못했다"
        assert copied == expected, (
            f"{image}.Dockerfile 의 manifests 단계가 작업공간과 다르다: "
            f"빠진 것 {sorted(expected - copied)}, 남는 것 {sorted(copied - expected)}"
        )


def test_이_저장소의_web_이미지_셋은_package_json_의_pnpm_판을_쓴다() -> None:
    expected = package_manager_version(WEB)
    for image in WEB_IMAGES:
        text = (IMAGES / f"{image}.Dockerfile").read_text(encoding="utf-8")
        assert prepared_pnpm(text) == expected, f"{image}.Dockerfile 의 corepack prepare 판"


def test_작업공간에_패키지가_늘었는데_Dockerfile_에_줄이_없으면_잡는다(tmp_path: Path) -> None:
    for name in ("a", "b"):
        (tmp_path / "packages" / name).mkdir(parents=True)
        (tmp_path / "packages" / name / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "apps").mkdir()
    (tmp_path / "pnpm-workspace.yaml").write_text(
        'packages:\n  - "apps/*"\n  - "packages/*"\nallowBuilds:\n  esbuild: false\n',
        encoding="utf-8",
    )
    dockerfile = (
        "FROM base AS manifests\n"
        "COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./\n"
        "COPY packages/a/package.json packages/a/package.json\n"
        "FROM manifests AS deps\n"
        "COPY packages/b/package.json packages/b/package.json\n"
    )
    # 다음 단계의 줄은 manifests 단계로 세지 않는다. b 가 빠진 것이 보여야 한다.
    assert workspace_manifests(tmp_path) - manifest_copies(dockerfile) == {
        "packages/b/package.json"
    }


def test_작업공간_묶음은_packages_키_아래만_읽는다(tmp_path: Path) -> None:
    (tmp_path / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'apps/*'\n  # 주석\n  - tools/*\nallowBuilds:\n  - extra/*\n",
        encoding="utf-8",
    )
    assert workspace_groups(tmp_path) == ["apps", "tools"]


def test_corepack_prepare_판이_어긋나면_잡는다() -> None:
    assert prepared_pnpm("RUN corepack prepare pnpm@11.1.0 --activate") == "11.1.0"
    assert prepared_pnpm("RUN echo 없음") is None
