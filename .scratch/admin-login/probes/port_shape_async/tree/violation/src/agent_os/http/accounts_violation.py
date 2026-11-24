"""양성 대조(port_shape_async). 포트 모듈이 SQLAlchemy 의 타입을 쓰면 계약이 깨지는지 본다.

임시 사본의 위반 나무에만 둔다. import-linter 의 금지 계약 "only the adapters import DB libraries"
가 이 가져오기를 잡아야 한다. 포트가 SQLAlchemy 의 행 타입을 주고받을 수 없다는 뜻이다.
"""

from __future__ import annotations

from sqlalchemy.engine import Row

PORT_ROW = Row
