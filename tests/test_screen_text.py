"""실제 모델 e2e의 비교 규칙(`tests/screen_text.py`)을 모델 없이 시험한다.

위젯과 위젯 미리보기 페이지의 실제 모델 시험(`-m llm_widget`, `-m llm_portal`)은 화면에 선 출력을
트레이스의 출력과 견준다. 화면은 마크다운 부품이 그리므로 기호가 빠지고 부품이 쓰는 문구가
붙는다(ADR 0053). 규칙은 그 시험 둘이 함께 부르는 함수 하나이고, 손으로 치는 시험만으로는 함수가 늘
지나는 결함이 드러나지 않아 여기서 본다.
"""

from pathlib import Path

from tests.screen_text import HIDDEN_PHRASES, screen_matches_output

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_DOC = Path("web/packages/ui/src/components/molecules/Markdown.md")
OUTPUT = "**2 더하기 3**은 5입니다."


def test_기호가_빠진_화면_글은_원문의_부분열이라_지난다() -> None:
    assert screen_matches_output("출력: 2 더하기 3은 5입니다.", OUTPUT)


def test_화면_글이_원문과_글자_그대로_같아도_지난다() -> None:
    assert screen_matches_output("2 더하기 3은 5입니다.", "2 더하기 3은 5입니다.")


def test_화면_글에_원문에_없는_글자가_있으면_부분열이_아니라_걸린다() -> None:
    # 화면 글을 다른 사례의 출력에서 온 것으로 바꿔 넣은 짝이다(비교가 아무것도 걸러내지 못하는지
    # 본다).
    assert not screen_matches_output("출력: 2 더하기 3은 6입니다.", OUTPUT)
    assert not screen_matches_output("출력: 배송은 내일 도착합니다.", OUTPUT)


def test_글자의_차례가_원문과_다르면_걸린다() -> None:
    assert not screen_matches_output("출력: 5입니다 2 더하기 3은", OUTPUT)


def test_화면_글이_비어_있으면_걸린다() -> None:
    assert not screen_matches_output("", OUTPUT)
    assert not screen_matches_output("출력: ", OUTPUT)
    assert not screen_matches_output("출력: ** | -", OUTPUT)


def test_링크의_새_탭_문구와_이미지_자리의_말을_어디서든_지우고_견준다() -> None:
    output = "[조회 페이지](https://example.com)에서 보세요. ![배송 지도](x.png)"
    screen = "출력: 조회 페이지(새 탭에서 열림)에서 보세요. 이미지: 배송 지도"

    assert screen_matches_output(screen, output)


def test_지우는_말이_든_화면_글도_그_말을_지운_뒤의_글자가_원문에_없으면_걸린다() -> None:
    assert not screen_matches_output("출력: 조회 페이지(새 탭에서 열림) 다른 글", "조회 페이지")


def test_원문이_지우는_말뿐이면_지운_뒤_화면_글이_비어_걸린다() -> None:
    # 부분열은 깨지지 않지만 "화면 글이 비면 걸린다"와 겹치는 경계다. 모델이 그림만 내는 출력은
    # 드물다.
    assert not screen_matches_output("출력: 이미지", "이미지")
    assert not screen_matches_output("출력: (새 탭에서 열림)", "(새 탭에서 열림)")


def test_지우는_말은_부품의_쓰임_문서가_적은_화면_문구와_같은_글자다() -> None:
    document = (REPO_ROOT / MARKDOWN_DOC).read_text(encoding="utf-8")

    assert HIDDEN_PHRASES == ("(새 탭에서 열림)", "이미지")
    assert '"(새 탭에서 열림)"' in document
    assert '"이미지: "' in document
