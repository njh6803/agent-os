"""pyright 오류를 기대하는 대조군. argon2-cffi 의 서명이 pyright 에 실제로 닿는지 본다.

`time_cost` 는 `int` 인데 글자를 넘긴다. 라이브러리의 타입이 보이면 `reportArgumentType` 이고,
보이지 않으면(타입 표지가 없거나 가져오기가 풀리지 않으면) 이 줄은 그 오류를 내지 않는다.
"""

from argon2 import PasswordHasher

HASHER = PasswordHasher(time_cost="2")
