"""매니페스트가 디스크 형식의 규약을 지키는지. 종류별 필드 자리와 형식 버전."""

import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_os.sdk import (
    McpServer,
    ModelProvider,
    PluginKind,
    PluginManifest,
    PluginName,
    approval_conflicts,
    parse_manifest,
)

AGENT = """
schema_version = "1"
kind = "agent"
name = "echo"
version = "0.1.0"
entrypoint = "echo.agent:EchoAgent"
"""

MCP = """
schema_version = "1"
kind = "mcp"
name = "fs"
version = "0.1.0"

[server]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-everything"]
"""


def _top_level(manifest: str, line: str) -> str:
    """[server] 표 앞에 넣는다. 표 뒤에 붙이면 그 표의 키가 되어 다른 이유로 거부된다."""
    return manifest.replace("[server]", f"{line}\n\n[server]", 1)


def test_agent_manifest_parses() -> None:
    manifest = parse_manifest(AGENT)
    assert manifest.kind is PluginKind.AGENT
    assert manifest.entrypoint == "echo.agent:EchoAgent"


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('kind = "agent"', 'kind = "graph"'))


def test_entrypoint_belongs_to_agent_only() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(MCP + 'entrypoint = "x:y"\n')
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('entrypoint = "echo.agent:EchoAgent"\n', ""))


def test_형식_버전이_없으면_거부한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('schema_version = "1"\n', ""))


def test_모르는_형식_버전은_거부한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('schema_version = "1"', 'schema_version = "2"'))


def test_플러그인_종류는_넷이고_model이_있다() -> None:
    assert {kind.value for kind in PluginKind} == {"agent", "mcp", "skill", "model"}


def test_에이전트는_MCP_서버를_안_적으면_빈_목록이다() -> None:
    assert parse_manifest(AGENT).mcp == ()


def test_에이전트는_쓸_MCP_서버_이름을_적는다() -> None:
    manifest = parse_manifest(AGENT + 'mcp = ["everything"]\n')
    assert manifest.mcp == ("everything",)


def test_에이전트가_아니면_MCP_서버_목록을_갖지_못한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(_top_level(MCP, "mcp = []"))


def test_mcp는_서버_실행_명령과_인자를_가진다() -> None:
    manifest = parse_manifest(MCP)
    assert manifest.server is not None
    assert manifest.server.command == "npx"
    assert manifest.server.args == ("-y", "@modelcontextprotocol/server-everything")


def test_mcp는_서버_표가_없으면_거부한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(MCP.split("[server]")[0])


def test_mcp가_아니면_서버_표를_갖지_못한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT + '[server]\ncommand = "npx"\n')


def test_에이전트는_승인이_필요한_도구를_안_적으면_빈_목록이다() -> None:
    assert parse_manifest(AGENT).requires_approval == ()


def test_에이전트는_승인_없이는_부를_수_없는_도구_이름을_적는다() -> None:
    manifest = parse_manifest(AGENT + 'requires_approval = ["send_email"]\n')

    assert manifest.requires_approval == ("send_email",)


def test_에이전트가_아니면_승인_목록을_갖지_못한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(_top_level(MCP, "requires_approval = []"))


def test_mcp_서버는_마스킹할_인자를_안_적으면_비어_있다() -> None:
    manifest = parse_manifest(MCP)

    assert manifest.server is not None
    assert manifest.server.secret_args == {}


def test_mcp_서버는_트레이스에_마스킹할_인자를_도구별로_적는다() -> None:
    manifest = parse_manifest(MCP + '\n[server.secret_args]\nsend_email = ["api_key"]\n')

    assert manifest.server is not None
    assert manifest.server.secret_args == {"send_email": ("api_key",)}


def _server(secret_args: str = "") -> McpServer:
    manifest = parse_manifest(MCP + secret_args)
    assert manifest.server is not None
    return manifest.server


def test_마스킹된_인자를_가진_도구는_승인_대상이_될_수_없다() -> None:
    agent = parse_manifest(AGENT + 'requires_approval = ["send_email", "read_inbox"]\n')
    servers = {PluginName("mailer"): _server('\n[server.secret_args]\nsend_email = ["api_key"]\n')}

    assert approval_conflicts(agent, servers) == ("send_email",)


def test_마스킹이_걸리지_않은_도구는_승인_대상이_될_수_있다() -> None:
    agent = parse_manifest(AGENT + 'requires_approval = ["read_inbox"]\n')
    servers = {PluginName("mailer"): _server('\n[server.secret_args]\nsend_email = ["api_key"]\n')}

    assert approval_conflicts(agent, servers) == ()


def test_승인_대상이_없으면_마스킹이_있어도_성립한다() -> None:
    agent = parse_manifest(AGENT)
    servers = {PluginName("mailer"): _server('\n[server.secret_args]\nsend_email = ["api_key"]\n')}

    assert approval_conflicts(agent, servers) == ()


def test_마스킹할_인자가_실제로_없으면_승인_대상이_될_수_있다() -> None:
    """빈 목록은 마스킹이 아니다. 복원할 수 없는 인자가 없으므로 금지의 근거가 없다."""
    agent = parse_manifest(AGENT + 'requires_approval = ["send_email"]\n')
    servers = {PluginName("mailer"): _server("\n[server.secret_args]\nsend_email = []\n")}

    assert approval_conflicts(agent, servers) == ()


# 저장소의 플러그인 디렉터리. 아래 테스트 하나만 디스크를 읽는다 — 재는 것이 코드가 아니라 저장소다.
REPO_PLUGINS = Path(__file__).resolve().parents[2] / "plugins"


def test_저장소의_매니페스트_중_secret_args_를_선언한_것이_없다() -> None:
    """관리 API 의 트레이스 상세가 마스킹되지 않은 이벤트를 내보내도 된다는 판단이 기댄 사실을
    불변식으로 바꾼다(ADR 0009 의 2026-09-22 이력). 처음 선언하는 날 이 테스트가 빨개지고, 그 순간이
    곧 열린 문제 셋을 닫을지 정해야 하는 순간이다. 막는 것은 선언이 아니라 결정 없이 지나가는
    것이고, 이 테스트를 지우는 것이 그 결정을 내리는 방법이다.

    파일마다 파싱하므로 읽히지 않는 매니페스트는 선언이 있는지 판정할 수 없어 여기서 함께 실패한다.
    mcp 매니페스트를 하나라도 읽었는지 보는 이유는 이 검사가 아무것도 읽지 않고 초록이 되는 길을
    막기 위해서다 — `secret_args` 는 mcp 에만 있다."""
    paths = sorted(REPO_PLUGINS.glob("*/*/plugin.toml"))
    manifests = [parse_manifest(path.read_text(encoding="utf-8")) for path in paths]
    declaring = [
        manifest.name
        for manifest in manifests
        if manifest.server is not None and manifest.server.secret_args
    ]

    assert any(manifest.kind is PluginKind.MCP for manifest in manifests), "mcp 를 읽지 않았다"
    assert declaring == []


# --- 대화 요약의 한도(ADR 0008 의 2026-10-03 이력) ----------------------------------


def test_한도를_적지_않으면_없음이고_형식_버전은_1_그대로다() -> None:
    manifest = parse_manifest(AGENT)

    assert manifest.conversation_limit is None
    assert manifest.schema_version == "1"


@pytest.mark.parametrize("value", ["1", "20000"])
def test_한도는_1_이상의_정수를_받는다(value: str) -> None:
    manifest = parse_manifest(AGENT + f"conversation_limit = {value}\n")

    assert manifest.conversation_limit == int(value)


@pytest.mark.parametrize(
    "value",
    ["0", "-1", "true", '"300"', "2.0", "1.5"],
    ids=["0", "음수", "불린", "숫자 문자열", "정수 값의 실수", "실수"],
)
def test_0_음수_불린_숫자_문자열_실수_한도는_읽는_단계에서_거부한다(value: str) -> None:
    """pydantic 의 느슨한 정수 검증은 `true` 를 1 로, `"300"` 을 300 으로, `2.0` 을 2 로 받는다.
    0 을 받으면 모든 이어 가기가 요약되고 원문이 남지 않는다(명세 "한도 값의 규칙")."""
    with pytest.raises(ValidationError):
        parse_manifest(AGENT + f"conversation_limit = {value}\n")


@pytest.mark.parametrize("kind", ["mcp", "skill", "model"])
def test_에이전트가_아니면_한도를_갖지_못한다(kind: str) -> None:
    """`requires_approval` 과 같은 규칙이다."""
    manifest = (
        _top_level(MCP, "conversation_limit = 100")
        if kind == "mcp"
        else f'schema_version = "1"\nkind = "{kind}"\nname = "x-{kind}"\nversion = "0.1.0"\n'
        "conversation_limit = 100\n"
    )

    with pytest.raises(ValidationError, match="conversation_limit"):
        parse_manifest(manifest)


# --- 모델 플러그인의 칸과 에이전트의 model(ADR 0040, ADR 0008 의 2026-10-31 이력) ----------

MODEL = """
schema_version = "1"
kind = "model"
name = "claude-opus-5"
version = "0.1.0"
provider = "anthropic"
model_id = "claude-opus-5"
"""

_MODEL_FIELDS = ("provider", "model_id", "max_tokens", "temperature")


def _error_types(manifest: str) -> list[str]:
    with pytest.raises(ValidationError) as caught:
        parse_manifest(manifest)
    return [str(error["type"]) for error in caught.value.errors()]


def test_제공사는_닫힌_열거이고_값은_anthropic_하나다() -> None:
    assert {provider.value for provider in ModelProvider} == {"anthropic"}


def test_모델은_공통_넷에_제공사와_모델_id만_적어도_받는다() -> None:
    manifest = parse_manifest(MODEL)

    assert manifest.kind is PluginKind.MODEL
    assert manifest.provider is ModelProvider.ANTHROPIC
    assert manifest.model_id == "claude-opus-5"
    assert manifest.max_tokens is None
    assert manifest.temperature is None
    assert manifest.schema_version == "1"


def test_모델은_토큰_상한과_온도를_적는다() -> None:
    manifest = parse_manifest(MODEL + "max_tokens = 16000\ntemperature = 0.5\n")

    assert manifest.max_tokens == 16000
    assert manifest.temperature == 0.5


@pytest.mark.parametrize("value", ["0", "1"])
def test_온도의_정수_0과_1은_실수로_받는다(value: str) -> None:
    """TOML 은 `0` 과 `0.0` 을 다른 타입으로 읽는다. 엄격한 실수가 정수를 거부하면 운영자가
    `temperature = 0` 이라고 쓴 파일이 거부된다."""
    manifest = parse_manifest(MODEL + f"temperature = {value}\n")

    assert manifest.temperature == float(value)
    assert isinstance(manifest.temperature, float)


def test_토큰_상한_1은_받는다() -> None:
    assert parse_manifest(MODEL + "max_tokens = 1\n").max_tokens == 1


@pytest.mark.parametrize(
    ("extra", "error_type"),
    [
        ("max_tokens = 0", "greater_than_equal"),
        ("max_tokens = 2.0", "int_type"),
        ("max_tokens = true", "int_type"),
        ('max_tokens = "16"', "int_type"),
        ("temperature = 1.5", "less_than_equal"),
        ("temperature = -0.1", "greater_than_equal"),
        ('temperature = "0.5"', "float_type"),
        ("temperature = true", "float_type"),
        ("top_p = 0.9", "extra_forbidden"),
    ],
    ids=[
        "토큰 0",
        "정수 값의 실수 토큰",
        "불린 토큰",
        "숫자 문자열 토큰",
        "온도 1 초과",
        "음수 온도",
        "숫자 문자열 온도",
        "불린 온도",
        "모르는 칸",
    ],
)
def test_범위_밖의_값과_모르는_칸은_읽는_단계에서_거부한다(extra: str, error_type: str) -> None:
    """엄격 검증이 아니면 `true` 가 1 로, `"16"` 이 16 으로, `2.0` 이 2 로 받힌다."""
    assert _error_types(MODEL + f"{extra}\n") == [error_type]


def test_모르는_제공사는_거부한다() -> None:
    assert _error_types(MODEL.replace('"anthropic"', '"openai"')) == ["enum"]


def test_빈_모델_id는_거부한다() -> None:
    assert _error_types(MODEL.replace('model_id = "claude-opus-5"', 'model_id = ""')) == [
        "string_too_short"
    ]


def test_모델_id가_문자열이_아니면_거부한다() -> None:
    assert _error_types(MODEL.replace('model_id = "claude-opus-5"', "model_id = 5")) == [
        "string_type"
    ]


@pytest.mark.parametrize("missing", ["provider", "model_id"])
def test_모델은_제공사와_모델_id가_없으면_거부한다(missing: str) -> None:
    lines = [line for line in MODEL.splitlines() if not line.startswith(missing)]

    with pytest.raises(ValidationError, match=f"model 플러그인은 {missing}가 필요하다"):
        parse_manifest("\n".join(lines))


def test_공통_넷만_적은_모델_매니페스트는_거부한다() -> None:
    """옛 모델 파일의 모양이다. 필수 칸이 없어 읽는 단계에서 거부되고 형식 버전은 1 그대로다."""
    old = 'schema_version = "1"\nkind = "model"\nname = "sonnet"\nversion = "0.1.0"\n'

    with pytest.raises(ValidationError, match="model 플러그인은 provider가 필요하다"):
        parse_manifest(old)


def _other_kind(kind: str, line: str) -> str:
    """에이전트·mcp·스킬·모델 가운데 `kind` 의 매니페스트에 최상위 한 줄을 더한다."""
    if kind == "agent":
        return AGENT + f"{line}\n"
    if kind == "mcp":
        return _top_level(MCP, line)
    if kind == "model":
        return MODEL + f"{line}\n"
    return f'schema_version = "1"\nkind = "{kind}"\nname = "x-{kind}"\nversion = "0.1.0"\n{line}\n'


_FIELD_VALUE = {
    "provider": '"anthropic"',
    "model_id": '"claude-opus-5"',
    "max_tokens": "10",
    "temperature": "0.5",
}


@pytest.mark.parametrize("field", _MODEL_FIELDS)
@pytest.mark.parametrize("kind", ["agent", "mcp", "skill"])
def test_모델이_아니면_모델의_칸을_갖지_못한다(kind: str, field: str) -> None:
    """`requires_approval` 과 같은 규칙이다."""
    manifest = _other_kind(kind, f"{field} = {_FIELD_VALUE[field]}")

    with pytest.raises(ValidationError, match=f"{kind} 플러그인은 {field} 을 갖지 않는다"):
        parse_manifest(manifest)


def test_에이전트는_model을_안_적으면_없음이다() -> None:
    assert parse_manifest(AGENT).model is None


def test_에이전트는_쓸_모델_플러그인_이름을_적는다() -> None:
    assert parse_manifest(AGENT + 'model = "claude-opus-5"\n').model == "claude-opus-5"


def test_에이전트의_model이_이름_패턴을_어기면_읽는_단계에서_거부한다() -> None:
    assert _error_types(AGENT + 'model = "Opus"\n') == ["string_pattern_mismatch"]


@pytest.mark.parametrize("kind", ["mcp", "skill", "model"])
def test_에이전트가_아니면_model을_갖지_못한다(kind: str) -> None:
    manifest = _other_kind(kind, 'model = "claude-opus-5"')

    with pytest.raises(ValidationError, match=f"{kind} 플러그인은 model 을 갖지 않는다"):
        parse_manifest(manifest)


def test_직렬화_스키마에서_새_다섯_칸은_모두_required이고_null을_허락한다() -> None:
    """관리 API 의 응답 타입 그대로라 늘 실리는 칸이 required 로 나간다(ADR 0010 의 2026-09-23
    이력). `conversation_limit` 과 같은 장치다."""
    schema = PluginManifest.model_json_schema(mode="serialization")
    five = ("model", "provider", "model_id", "max_tokens", "temperature")

    assert set(five) <= set(schema["required"])
    for name in five:
        assert {"type": "null"} in schema["properties"][name]["anyOf"], name


def test_제공사는_이름_있는_정의로_스키마에_선다() -> None:
    schema = PluginManifest.model_json_schema(mode="serialization")

    assert schema["$defs"]["ModelProvider"]["enum"] == ["anthropic"]
    assert {"$ref": "#/$defs/ModelProvider"} in schema["properties"]["provider"]["anyOf"]


def test_sdk_매니페스트를_불러와도_보호_이름_공간_경고가_없다() -> None:
    """`model_id` 는 pydantic 의 보호 이름 공간 `model_` 에 걸릴 수 있는 이름이다(`model` 은 그
    접두가 아니다). 설치된 판이 기본 설정으로 경고를 내면 import 가 오류로 끝나 이 시험이 빨개진다
    (명세 "모델 매니페스트의 칸", 프로브 manifest_fields.py 가 2.13.5 에서 쟀다)."""
    done = subprocess.run(
        [sys.executable, "-I", "-W", "error", "-c", "import agent_os.sdk.manifest"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr
