"""agent-os 명령의 진입점. 조합 층.

채널, 관리, 어댑터를 조립해 넘기는 유일한 자리다. 슬라이스 2에서 `serve`가
`agent_os.server`를 부른다.
"""

from __future__ import annotations

from agent_os.channel.cli.main import build_parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
