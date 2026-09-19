"""agent-os 명령의 진입점."""

from __future__ import annotations

import argparse
from importlib.metadata import version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-os", description="플러그인 기반 에이전트 런타임")
    parser.add_argument("--version", action="version", version=version("agent-os"))
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
