"""`openapi.json` 생성기. 계약 파일은 저장소 루트에 커밋된다(ADR 0010).

슬라이스 3 의 `packages/api-client` 가 이 파일에서 생성되므로, 파일이 앱과 어긋나면 생성된
클라이언트가 조용히 틀린다. 최신성은 pytest 하나가 판정한다 — 검사 명령 넷이 그대로 게이트이고
새 훅을 만들지 않는다.

    PYTHONUTF8=1 uv run python tools/export_openapi.py

포트를 스텁으로 세우는 이유는 스키마가 포트를 읽지 않기 때문이다. 진짜 어댑터를 만들면 어댑터를
조립하는 자리가 `main.py` 와 `server.py` 말고 셋째가 생기고(ADR 0010), 뜻 없는 디렉터리 경로가
이 파일에 나타난다.
"""

from __future__ import annotations

import io
import json
from collections.abc import Sequence
from pathlib import Path

from agent_os.core.ports import (
    Cursor,
    ManifestRow,
    PluginSource,
    RunRow,
    RunStatus,
    Trace,
    TraceStore,
)
from agent_os.sdk import BaseAgent, Event, PluginKind, PluginManifest, PluginName, RunId
from agent_os.server import create_app

ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = ROOT / "openapi.json"

# 스키마는 토큰을 읽지 않는다. 이 값들은 앱을 세우기 위한 자리표시자이고 어떤 서버에도 쓰이지
# 않는다. 빈 문자열이나 같은 값을 쓸 수 없는 이유는 `create_app` 이 그런 앱을 거부하기 때문이다.
_PLACEHOLDER_ADMIN_TOKEN = "openapi-export-only-admin"
_PLACEHOLDER_CHANNEL_TOKEN = "openapi-export-only-channel"


class _SchemaOnlyPlugins:
    """스키마를 뽑는 동안 아무것도 열지 않는다. 불리면 그 자체가 결함이라 터뜨린다."""

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        raise NotImplementedError("스키마 추출은 포트를 부르지 않는다")

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        raise NotImplementedError("스키마 추출은 포트를 부르지 않는다")

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        raise NotImplementedError("스키마 추출은 포트를 부르지 않는다")


class _SchemaOnlyTrace:
    def write(self, event: Event) -> None:
        raise NotImplementedError("스키마 추출은 포트를 부르지 않는다")

    def read(self, run_id: RunId) -> Trace | None:
        raise NotImplementedError("스키마 추출은 포트를 부르지 않는다")

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> Sequence[RunRow]:
        raise NotImplementedError("스키마 추출은 포트를 부르지 않는다")


def document() -> str:
    """계약 파일의 내용. 테스트가 이것과 커밋된 파일을 비교한다.

    키를 정렬하는 이유는 diff 를 안정시키기 위해서다 — 파이썬 사전의 순서는 삽입 순서라
    프레임워크가 필드를 더하는 자리에 따라 파일 전체가 흔들린다. ASCII 로 이스케이프하지 않는
    이유는 한국어 설명이 그대로 읽혀야 하기 때문이고, 파일은 UTF-8 이다.
    """
    plugins: PluginSource = _SchemaOnlyPlugins()
    trace: TraceStore = _SchemaOnlyTrace()
    app = create_app(
        plugins=plugins,
        trace=trace,
        admin_token=_PLACEHOLDER_ADMIN_TOKEN,
        channel_token=_PLACEHOLDER_CHANNEL_TOKEN,
        stderr=io.StringIO(),
    )
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> None:
    # 줄 끝을 고정한다. 기본값은 플랫폼에 따라 CRLF 가 되어 계약 파일이 OS 마다 달라진다.
    OPENAPI_PATH.write_text(document(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
