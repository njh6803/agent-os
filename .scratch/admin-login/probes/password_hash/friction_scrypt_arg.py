"""pyright 오류를 기대하는 대조군. `hashlib.scrypt` 의 서명이 pyright 에 실제로 닿는지 본다.

비밀번호 자리는 바이트인데 글자를 넘긴다. 표준 라이브러리 스텁의 서명이 보이면
`reportArgumentType` 이다.
"""

import hashlib

KEY = hashlib.scrypt("text", salt=b"salt-of-16-bytes", n=2, r=8, p=1)
