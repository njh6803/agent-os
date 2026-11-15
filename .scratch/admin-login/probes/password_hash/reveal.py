"""후보의 호출이 돌려준 값을 pyright 가 무슨 타입으로 보는지 찍는다. 실행하지 않는다.

`reveal_type` 은 pyright 의 정보 진단으로 나오고 `run.py` 의 `types` 가 그 줄을 그대로 낸다.
"""

import hashlib
from typing import reveal_type

import store_argon2
import store_scrypt
from argon2 import PasswordHasher, extract_parameters

HASHER = PasswordHasher()
ENCODED = HASHER.hash("sample")

reveal_type(hashlib.scrypt(b"sample", salt=b"salt-of-16-bytes", n=2, r=8, p=1))
reveal_type(ENCODED)
reveal_type(HASHER.verify(ENCODED, "sample"))
reveal_type(HASHER.check_needs_rehash(ENCODED))
reveal_type(extract_parameters(ENCODED))
reveal_type(HASHER.memory_cost)
reveal_type(store_scrypt.hash_password("sample"))
reveal_type(store_scrypt.verify_password("stored", "sample"))
reveal_type(store_argon2.hash_password("sample"))
reveal_type(store_argon2.verify_password("stored", "sample"))
reveal_type(store_argon2.needs_rehash("stored"))
