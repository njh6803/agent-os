"""포트의 접속 확인 메서드를 쓰지 않는 가짜의 바탕. 시험 파일들이 나눠 쓴다.

도구 포트와 모델 포트에 접속 확인 메서드가 늘었다(ADR 0067). 실행을 미는 시험의 가짜는 그
메서드를 쓰지 않으므로, 불리면 결함이라고 터뜨리는 바탕을 상속해 시그니처만 채운다. 이 바탕은
포트가 아니라서 가짜가 포트를 상속하지 않는다는 규칙(`.claude/rules/tests.md`)을 어기지 않고,
포트 타입으로 적는 픽스처가 적합성을 검증하는 것도 그대로다. 접속 확인을 미는 시험은
`tests/test_server.py` 의 자기 가짜를 쓴다.
"""

from __future__ import annotations

from agent_os.core.ports import CheckOutcome
from agent_os.sdk import HttpServer, PluginManifest, PluginName, StdioServer


class UnusedToolChecks:
    """도구 포트의 접속 확인 메서드 둘. core 의 런타임은 부르지 않으므로 불리면 결함이다."""

    async def check_remote(self, name: PluginName, server: HttpServer) -> CheckOutcome:
        raise NotImplementedError("이 시험은 접속 확인을 부르지 않는다")

    async def check_stdio(self, name: PluginName, server: StdioServer) -> CheckOutcome:
        raise NotImplementedError("이 시험은 접속 확인을 부르지 않는다")


class UnusedModelCheck:
    """모델 포트의 접속 확인 메서드. core 의 런타임은 부르지 않으므로 불리면 결함이다."""

    async def check(self, manifest: PluginManifest) -> CheckOutcome:
        raise NotImplementedError("이 시험은 접속 확인을 부르지 않는다")
