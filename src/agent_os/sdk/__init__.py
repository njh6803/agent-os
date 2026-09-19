"""플러그인이 import하는 유일한 공개 표면. 원칙 IV.

여기 있는 것만 플러그인에 보인다. core의 어떤 것도 여기로 새지 않는다.
"""

from agent_os.sdk.agent import BaseAgent
from agent_os.sdk.events import BaseEvent
from agent_os.sdk.manifest import PluginKind, PluginManifest, parse_manifest

__all__ = ["BaseAgent", "BaseEvent", "PluginKind", "PluginManifest", "parse_manifest"]
