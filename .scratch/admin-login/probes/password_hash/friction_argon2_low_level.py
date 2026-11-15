"""pyright 오류를 기대하는 대조군. argon2-cffi 의 타입이 닿지 않는 자리 하나다.

`argon2.low_level` 은 타입 표지가 없는 `_argon2_cffi_bindings` 에서 값을 가져온다. 그 값을 그대로
읽으면 strict 에서 `reportUnknownMemberType` 이다. 후보 모듈(`store_argon2.py`)은 `PasswordHasher`
만 써서 이 자리를 지나지 않는다. `reveal_type` 줄은 `run.py` 의 `types` 가 그대로 낸다.
"""

from typing import reveal_type

from argon2 import Type, low_level

VERSION = low_level.ARGON2_VERSION

reveal_type(low_level.ARGON2_VERSION)
reveal_type(Type.ID)
reveal_type(Type.ID.value)
reveal_type(low_level.hash_secret)
