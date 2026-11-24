"""양성 대조(port_shape_async). 어댑터가 포트를 `agent_os.http` 에서 가져오면 계약이 깨지는지 본다.

임시 사본의 위반 나무에만 둔다. import-linter 의 금지 계약 "adapters are not an HTTP surface" 가
이 가져오기를 잡아야 한다.
"""

from __future__ import annotations

from agent_os.http.accounts import AccountStore

PORT = AccountStore
