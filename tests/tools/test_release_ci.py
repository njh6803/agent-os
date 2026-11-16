"""tools/release_ci.py 의 시험. 판 내기 워크플로가 부르는 판정 도구다.

번호와 노트와 묶음은 tools/release.py(test_release.py)가 맡고, 여기는 워크플로의 단계가 넘기는 값을
읽는 순수 판정을 본다. 이미지 아이디는 `docker save` 가 만드는 두 꼴(옛 저장 방식의 `<아이디>.json`
과 containerd 저장 방식의 `blobs/sha256/<해시>`)을 모두 만들어 넣는다. 올린 이미지 색인의 꼴은
`docker buildx imagetools inspect --raw` 가 내는 OCI 색인이다.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

import pytest
from tools.release import ReleaseError
from tools.release_ci import (
    BAKE_FILE,
    IMAGES,
    PrecheckAction,
    bake_repositories,
    bake_repository,
    image_config_digest,
    main,
    manifest_config_digest,
    platform_manifest_digest,
    precheck,
    verify_files,
)

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
SHA = "1" * 40
OTHER_SHA = "2" * 40


def _tar(path: Path, members: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


CONFIG = (
    b'{"architecture":"amd64","config":{"Env":["A=1"]},"rootfs":{"type":"layers","diff_ids":[]}}'
)


def test_옛_저장_방식의_저장_파일에서_설정_파일의_해시를_읽는다(tmp_path: Path) -> None:
    tar = _tar(
        tmp_path / "old.tar",
        {
            "manifest.json": json.dumps([{"Config": "abc.json", "Layers": []}]).encode(),
            "abc.json": CONFIG,
        },
    )
    assert image_config_digest(tar) == _digest(CONFIG)


def test_containerd_저장_방식의_저장_파일에서도_같은_해시를_읽는다(tmp_path: Path) -> None:
    hex_ = hashlib.sha256(CONFIG).hexdigest()
    tar = _tar(
        tmp_path / "oci.tar",
        {
            "manifest.json": json.dumps(
                [{"Config": f"blobs/sha256/{hex_}", "Layers": []}]
            ).encode(),
            f"blobs/sha256/{hex_}": CONFIG,
        },
    )
    assert image_config_digest(tar) == _digest(CONFIG)


def test_ENV만_다른_두_이미지는_설정_해시가_다르다(tmp_path: Path) -> None:
    other = CONFIG.replace(b"A=1", b"A=2")
    one = _tar(
        tmp_path / "one.tar",
        {"manifest.json": json.dumps([{"Config": "c.json"}]).encode(), "c.json": CONFIG},
    )
    two = _tar(
        tmp_path / "two.tar",
        {"manifest.json": json.dumps([{"Config": "c.json"}]).encode(), "c.json": other},
    )
    assert image_config_digest(one) != image_config_digest(two)


@pytest.mark.parametrize(
    ("members", "reason"),
    [
        ({}, "저장 파일에 manifest.json 이 없다"),  # 매니페스트가 없다
        ({"manifest.json": b"[]"}, "이미지 하나를 가리키지"),  # 이미지가 없다
        (
            {"manifest.json": json.dumps([{"Config": "a"}, {"Config": "b"}]).encode()},
            "이미지 하나를 가리키지",  # 이미지가 둘
        ),
        (
            {"manifest.json": json.dumps([{"Config": "없는.json"}]).encode()},
            "저장 파일에 없는.json 이 없다",  # 설정 파일이 없다
        ),
        ({"manifest.json": b"not json"}, "JSON 이 아니다"),
    ],
)
def test_저장_파일에서_설정을_하나로_고르지_못하면_실패한다(
    tmp_path: Path, members: dict[str, bytes], reason: str
) -> None:
    with pytest.raises(ReleaseError, match=reason):
        image_config_digest(_tar(tmp_path / "bad.tar", members))


def _index(*manifests: dict[str, object]) -> str:
    return json.dumps({"schemaVersion": 2, "manifests": list(manifests)})


def _entry(digest: str, os: str, arch: str, *, attestation: bool = False) -> dict[str, object]:
    entry: dict[str, object] = {
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "digest": digest,
        "platform": {"os": os, "architecture": arch},
    }
    if attestation:
        entry["annotations"] = {"vnd.docker.reference.type": "attestation-manifest"}
    return entry


def test_올린_색인에서_증명이_아닌_리눅스_amd64_매니페스트를_고른다() -> None:
    text = _index(
        _entry(DIGEST_A, "linux", "amd64"),
        _entry(DIGEST_B, "unknown", "unknown", attestation=True),
    )
    assert platform_manifest_digest(text) == DIGEST_A


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        (_index(_entry(DIGEST_A, "linux", "arm64")), "하나가 아니다"),  # 플랫폼이 맞지 않는다
        (
            _index(_entry(DIGEST_A, "linux", "amd64"), _entry(DIGEST_B, "linux", "amd64")),
            "하나가 아니다",  # 둘이다
        ),
        (
            _index(_entry(DIGEST_A, "linux", "amd64", attestation=True)),
            "하나가 아니다",  # 증명뿐이다
        ),
        (
            json.dumps({"schemaVersion": 2, "config": {"digest": DIGEST_A}}),
            "manifests 가 없다",  # 색인이 아니다
        ),
        ("not json", "JSON 이 아니다"),
    ],
)
def test_색인에서_매니페스트를_하나로_고르지_못하면_실패한다(text: str, reason: str) -> None:
    with pytest.raises(ReleaseError, match=reason):
        platform_manifest_digest(text)


def test_매니페스트의_설정_해시를_읽는다() -> None:
    text = json.dumps({"schemaVersion": 2, "config": {"digest": DIGEST_A}, "layers": []})
    assert manifest_config_digest(text) == DIGEST_A


@pytest.mark.parametrize("text", ["{}", '{"config": {}}', '{"config": {"digest": "sha256:x"}}'])
def test_매니페스트에_설정_해시가_없거나_꼴이_틀리면_실패한다(text: str) -> None:
    with pytest.raises(ReleaseError, match="config.digest"):
        manifest_config_digest(text)


def test_공개_릴리스가_이_커밋을_가리키면_더_할_일_없이_끝난다() -> None:
    plan = precheck(published=True, tag_commit=SHA, drafts=[], sha=SHA)
    assert plan.action is PrecheckAction.DONE
    assert plan.delete == ()


def test_공개_릴리스가_다른_커밋을_가리키면_실패한다() -> None:
    with pytest.raises(ReleaseError, match="다른 커밋"):
        precheck(published=True, tag_commit=OTHER_SHA, drafts=[], sha=SHA)


def test_공개_릴리스의_태그를_찾지_못해도_실패한다() -> None:
    with pytest.raises(ReleaseError, match="찾지 못한 커밋"):
        precheck(published=True, tag_commit="", drafts=[], sha=SHA)


def test_공개_릴리스_없이_git_태그만_있으면_실패한다() -> None:
    with pytest.raises(ReleaseError, match="git 태그"):
        precheck(published=False, tag_commit=SHA, drafts=[], sha=SHA)


def test_이_커밋의_남은_초안은_지우고_새로_만든다() -> None:
    plan = precheck(published=False, tag_commit="", drafts=[("11", SHA), ("12", SHA)], sha=SHA)
    assert plan.action is PrecheckAction.PROCEED
    assert plan.delete == ("11", "12")
    assert plan.replaced is True


def test_다른_커밋의_초안이_있으면_실패한다() -> None:
    with pytest.raises(ReleaseError, match="초안"):
        precheck(published=False, tag_commit="", drafts=[("11", OTHER_SHA)], sha=SHA)


def test_아무것도_없으면_그대로_진행한다() -> None:
    plan = precheck(published=False, tag_commit="", drafts=[], sha=SHA)
    assert plan.action is PrecheckAction.PROCEED
    assert plan.delete == ()
    assert plan.replaced is False


def _files(directory: Path, number: str, *, skip: str | None = None) -> None:
    names = [f"agent-os-{number}.tar.gz", "notes.md", "release.json"]
    for image in IMAGES:
        names += [f"grype-{image}.json", f"sbom-{image}.spdx.json"]
    for name in names:
        if name != skip:
            (directory / name).write_text("{}" if name != "notes.md" else "# 노트\n", "utf-8")
    if skip != "release.json":
        manifest = {
            "number": number,
            "revision": SHA,
            "images": {image: DIGEST_A for image in IMAGES},
        }
        (directory / "release.json").write_text(json.dumps(manifest), "utf-8")


def _digests() -> dict[str, str]:
    return dict.fromkeys(IMAGES, DIGEST_A)


def test_받은_파일이_다_있고_번호와_해시가_같으면_지난다(tmp_path: Path) -> None:
    _files(tmp_path, "0.1.0-rc.1")
    verify_files(tmp_path, "0.1.0-rc.1", SHA, _digests())


def test_받은_파일이_하나라도_빠지면_실패한다(tmp_path: Path) -> None:
    _files(tmp_path, "0.1.0-rc.1", skip="grype-portal.json")
    with pytest.raises(ReleaseError, match="grype-portal.json"):
        verify_files(tmp_path, "0.1.0-rc.1", SHA, _digests())


def test_받은_파일의_판_번호가_다르면_실패한다(tmp_path: Path) -> None:
    _files(tmp_path, "0.1.0-rc.1")
    manifest = {"number": "0.1.0-rc.2", "revision": SHA, "images": _digests()}
    (tmp_path / "release.json").write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(ReleaseError, match="번호"):
        verify_files(tmp_path, "0.1.0-rc.1", SHA, _digests())


def test_받은_파일의_이미지_해시가_다르면_실패한다(tmp_path: Path) -> None:
    _files(tmp_path, "0.1.0-rc.1")
    digests = _digests() | {"admin": DIGEST_B}
    with pytest.raises(ReleaseError, match="admin"):
        verify_files(tmp_path, "0.1.0-rc.1", SHA, digests)


def test_받은_파일의_커밋이_다르면_실패한다(tmp_path: Path) -> None:
    _files(tmp_path, "0.1.0-rc.1")
    with pytest.raises(ReleaseError, match="커밋"):
        verify_files(tmp_path, "0.1.0-rc.1", OTHER_SHA, _digests())


def test_명령줄의_번호_태그_판정은_조회_출력을_표준_입력으로_받는다(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("ERROR: x: not found\n"))
    assert main(["judge", "--exit-code", "1", "--digest", DIGEST_A]) == 0
    assert capsys.readouterr().out.strip() == "attach"


def test_명령줄의_판정은_다른_해시를_거부로_읽는다(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    text = f"Name: x\nMediaType: y\nDigest:    {DIGEST_B}\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    assert main(["judge", "--exit-code", "0", "--digest", DIGEST_A]) == 0
    assert capsys.readouterr().out.strip() == "reject"


def test_명령줄의_초안_확인은_출력_줄을_내고_실패하면_1로_끝난다(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = ["precheck", "--published", "false", "--sha", SHA, "--draft", f"11={SHA}"]
    assert main(args) == 0
    out = capsys.readouterr().out.splitlines()
    assert "action=proceed" in out
    assert "delete=11" in out
    assert "replaced=true" in out
    bad = ["precheck", "--published", "false", "--sha", SHA, "--tag-commit", SHA]
    assert main(bad) == 1
    assert capsys.readouterr().err.startswith("release: ")


def test_명령줄의_파일_확인은_빠진_파일을_1로_알린다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _files(tmp_path, "0.1.0-rc.1", skip="notes.md")
    args = ["verify-files", "--dir", str(tmp_path), "--number", "0.1.0-rc.1", "--sha", SHA]
    for image in IMAGES:
        args += ["--digest", f"{image}={DIGEST_A}"]
    assert main(args) == 1
    assert "notes.md" in capsys.readouterr().err


def test_명령줄의_이미지_설정_해시는_저장_파일에서_읽어_낸다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tar = _tar(
        tmp_path / "old.tar",
        {"manifest.json": json.dumps([{"Config": "c.json"}]).encode(), "c.json": CONFIG},
    )
    assert main(["image-id", str(tar)]) == 0
    assert capsys.readouterr().out.strip() == _digest(CONFIG)


def test_명령줄의_매니페스트_고르기와_설정_읽기는_파일을_읽어_해시를_낸다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    index = tmp_path / "index.json"
    index.write_text(_index(_entry(DIGEST_A, "linux", "amd64")), "utf-8")
    assert main(["platform-manifest", str(index)]) == 0
    assert capsys.readouterr().out.strip() == DIGEST_A
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"config": {"digest": DIGEST_B}}), "utf-8")
    assert main(["manifest-config", str(manifest)]) == 0
    assert capsys.readouterr().out.strip() == DIGEST_B


def test_명령줄은_읽지_못하는_파일을_1로_알린다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["platform-manifest", str(tmp_path / "없다.json")]) == 1
    assert "읽지 못했다" in capsys.readouterr().err


def test_명령줄은_커밋_해시가_아닌_sha를_받지_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["precheck", "--published", "true", "--sha", ""]) == 1
    assert "커밋 해시 40자" in capsys.readouterr().err
    _files(tmp_path, "0.1.0-rc.1")
    args = ["verify-files", "--dir", str(tmp_path), "--number", "0.1.0-rc.1", "--sha", "abc"]
    assert main(args) == 1
    assert "커밋 해시 40자" in capsys.readouterr().err


def test_명령줄은_이름_값_꼴이_아닌_초안과_해시를_받지_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad_draft = ["precheck", "--published", "false", "--sha", SHA, "--draft", "11"]
    assert main(bad_draft) == 1
    assert "이름=값" in capsys.readouterr().err
    _files(tmp_path, "0.1.0-rc.1")
    bad_digest = ["verify-files", "--dir", str(tmp_path), "--number", "0.1.0-rc.1", "--sha", SHA]
    assert main([*bad_digest, "--digest", "serve"]) == 1
    assert "이름=값" in capsys.readouterr().err


def test_첫째_잡이_이미지_해시를_하나도_넘기지_않으면_실패한다(tmp_path: Path) -> None:
    manifest: dict[str, object] = {"number": "0.1.0-rc.1", "revision": SHA, "images": {}}
    _files(tmp_path, "0.1.0-rc.1")
    (tmp_path / "release.json").write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(ReleaseError, match="해시가 없다"):
        verify_files(tmp_path, "0.1.0-rc.1", SHA, {})


# ---------- Docker Hub 저장소 이름 ----------

ROOT = Path(__file__).resolve().parents[2]
BAKE = ROOT / BAKE_FILE
COMPOSE = ROOT / "deploy" / "standalone" / "compose.yaml"
FIXTURE_COMPOSE = ROOT / "web" / "packages" / "e2e-standalone" / "compose.fixtures.yaml"
STANDALONE_README = ROOT / "deploy" / "standalone" / "README.md"

_BAKE_SAMPLE = """\
target "_web" {
  context = "web"
}

target "one" {
  inherits = ["_web"]
  tags     = ["${NAMESPACE}/agent-os-one:${TAG}"]
}
"""


def _repositories() -> dict[str, str]:
    return bake_repositories(BAKE.read_text("utf-8"))


def test_짓기_목록은_이미지_넷마다_저장소_이름_하나를_정한다() -> None:
    repositories = _repositories()
    assert set(repositories) == set(IMAGES)
    assert len(set(repositories.values())) == len(IMAGES)


def test_짓기_목록의_태그가_없는_바탕_대상은_건너뛴다() -> None:
    assert bake_repositories(_BAKE_SAMPLE) == {"one": "agent-os-one"}


@pytest.mark.parametrize(
    "tags",
    [
        '["${NAMESPACE}/a:${TAG}", "${NAMESPACE}/b:${TAG}"]',
        '["${NAMESPACE}/a:latest"]',
        '["docker.io/a:${TAG}"]',
        "[]",
    ],
)
def test_태그가_이름공간_저장소_태그_한_줄이_아니면_실패한다(tags: str) -> None:
    text = f'target "one" {{\n  tags = {tags}\n}}\n'
    with pytest.raises(ReleaseError, match="한 줄이 아니다"):
        bake_repositories(text)


def test_짓기_목록에_없는_대상의_저장소를_물으면_있는_대상을_알리며_실패한다() -> None:
    with pytest.raises(ReleaseError, match="저장소 이름이") as raised:
        bake_repository(_BAKE_SAMPLE, "none")
    assert "'none'" in str(raised.value)
    assert "['one']" in str(raised.value)


def test_명령줄은_짓기_대상의_저장소_이름을_낸다(capsys: pytest.CaptureFixture[str]) -> None:
    for target, repository in _repositories().items():
        assert main(["repository", target, "--bake", str(BAKE)]) == 0
        assert capsys.readouterr().out.strip() == repository


def test_명령줄은_다른_짓기_파일과_없는_대상을_다룬다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bake = tmp_path / "bake.hcl"
    bake.write_text(_BAKE_SAMPLE, "utf-8")
    assert main(["repository", "one", "--bake", str(bake)]) == 0
    assert capsys.readouterr().out.strip() == "agent-os-one"
    assert main(["repository", "portal", "--bake", str(bake)]) == 1
    assert "저장소 이름이" in capsys.readouterr().err
    assert main(["repository", "one", "--bake", str(tmp_path / "없다.hcl")]) == 1
    assert "읽지 못했다" in capsys.readouterr().err


def _compose_images(path: Path) -> dict[str, str]:
    """compose 파일의 서비스마다 `image:` 줄에서 `<이름공간>/<저장소>:<태그>` 의 저장소를 읽는다."""
    found: dict[str, str] = {}
    service = ""
    for line in path.read_text("utf-8").splitlines():
        header = re.fullmatch(r"  ([a-z][a-z0-9-]*):\s*", line)
        if header is not None:
            service = header.group(1)
        image = re.fullmatch(r"    image: \$\{AGENT_OS_NAMESPACE[^}]*\}/([a-z0-9-]+):\$\{.*", line)
        if image is not None:
            found[service] = image.group(1)
    return found


def test_배포_compose의_이미지_줄은_짓기_목록의_저장소_이름과_같다() -> None:
    assert _compose_images(COMPOSE) == _repositories()


def test_단독_배포_시험_픽스처의_이미지_줄은_serve의_저장소_이름과_같다() -> None:
    assert _compose_images(FIXTURE_COMPOSE) == {"fixtures": _repositories()["serve"]}


def test_배포_안내의_대응표는_짓기_목록의_저장소_이름과_같다() -> None:
    rows = re.findall(
        r"^\| `([a-z]+)` \|[^|]*\| `<이름공간>/([a-z0-9-]+)` \|$",
        STANDALONE_README.read_text("utf-8"),
        flags=re.M,
    )
    assert dict(rows) == _repositories()
