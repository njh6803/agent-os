"""CLI 채널의 파서. 실행을 요청하는 명령(run)이 여기에 붙는다."""

from __future__ import annotations

import argparse
from importlib.metadata import version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-os", description="플러그인 기반 에이전트 런타임")
    parser.add_argument("--version", action="version", version=version("agent-os"))
    return parser
