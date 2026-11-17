"""`.github/workflows/release.yml` 의 모양 시험.

판 내기의 첫 실제 실행(2026-11-17)이 `시험한 이미지와 올린 이미지 대조` 단계에서 시작도 못 하고
`Argument list too long` 으로 죽었다. 그 단계는 bake 액션의 `metadata` 출력(이미지 넷의 digest와
출처 증명에 든 GitHub 컨텍스트 전체. 실패 로그에서 줄 접두를 뗀 값이 약 185KB)을 환경 변수
`METADATA` 로 받았고, 리눅스의 환경 변수 하나는 커널 상한(`MAX_ARG_STRLEN`, 128KiB로 본다. 러너에서
재지 않았다) 을 넘으면 `bash` 를 띄우지 못한다. 이 시험은 단계의 출력이 통째로 환경 변수에 실리는
같은 모양을 막는다. 크기는 입력이 정하므로 작은 날의 CI로는 보이지 않는다.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release.yml"

# `${{ steps.<id>.outputs.metadata }}` 꼴의 표현식. bake 액션의 출력 이름이 `metadata` 다.
_METADATA_EXPRESSION = re.compile(r"\$\{\{\s*steps\.[\w-]+\.outputs\.metadata\s*\}\}")


def metadata_expression_lines(text: str) -> list[str]:
    """워크플로 글에서 bake의 `metadata` 출력을 끌어 쓰는 줄을 모은다.

    못 보는 것: 출력을 `toJSON` 등으로 감싸거나 대괄호 꼴(`steps['push'].outputs.metadata`)로 쓰거나
    다른 이름의 출력으로 다시 내보내 환경 변수에 싣는 길, `metadata` 가 아닌 다른 큰 출력. 이 이름
    하나만 막는다. 환경 변수 자리만 가리지 않고 줄 안 어디든 쓰면 잡으므로 YAML 주석에 적은 표현식도
    잡는다(거짓 양성)."""
    return [line.strip() for line in text.splitlines() if _METADATA_EXPRESSION.search(line)]


def test_이_저장소의_판_내기_워크플로는_bake_메타데이터_출력을_표현식으로_쓰지_않는다() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    # 범위가 비면 위반 0으로 조용히 초록이다. 이 단계가 있는 파일을 읽었는지 먼저 본다.
    assert "시험한 이미지와 올린 이미지 대조" in text
    assert metadata_expression_lines(text) == []


def test_이_저장소의_판_내기_워크플로는_올린_digest를_해시_태그에서_읽는다() -> None:
    # 옛 모양을 막는 위 시험은 해시 태그 읽기를 지워도 초록이다. 새 모양이 있음을 따로 본다.
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'imagetools inspect "$NAMESPACE/$repo:$HASH_TAG"' in text


def test_이_저장소의_판_내기_워크플로는_올리는_태그와_읽는_태그를_한_변수에서_받는다() -> None:
    # 읽는 쪽 단언만으로는 잡의 HASH_TAG 정의를 지우거나 올리기 단계의 TAG 를 틀리게 해도 초록이다.
    # 올린 태그와 읽는 태그가 갈라지는 회귀를 막으려고 정의와 올리는 쪽을 따로 본다.
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "HASH_TAG: sha-${{ github.sha }}" in text
    assert "TAG: ${{ env.HASH_TAG }}" in text
    assert text.count("sha-${{ github.sha }}") == 1


def test_bake_메타데이터를_환경_변수로_받는_줄을_잡는다() -> None:
    text = "\n".join(
        [
            "        env:",
            "          NUMBER: ${{ steps.plan.outputs.number }}",
            "          METADATA: ${{ steps.push.outputs.metadata }}",
        ]
    )
    assert metadata_expression_lines(text) == ["METADATA: ${{ steps.push.outputs.metadata }}"]


def test_번호처럼_작은_출력은_잡지_않는다() -> None:
    text = "          NUMBER: ${{ steps.plan.outputs.number }}"
    assert metadata_expression_lines(text) == []
