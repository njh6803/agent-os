"""컨테이너 안에서 Docker 내장 DNS(127.0.0.11)에 A 질의 하나를 보내 응답의 TTL 을 찍는다.

    python /srv/dns_ttl.py <이름> [A|AAAA]

한 줄을 낸다. `DNS name=<이름> type=<형> rcode=<코드> answers=<주소:TTL,...> ms=<걸린 밀리초>`.
nginx 의 resolver 는 valid 를 주지 않으면 이 TTL 동안 주소를 기억한다. 도구(dig) 없이 재려고
질의를 손으로 짠다.
"""

from __future__ import annotations

import secrets
import socket
import struct
import sys
import time

TYPES = {"A": 1, "AAAA": 28}


def skip_name(data: bytes, offset: int) -> int:
    while True:
        length = data[offset]
        if length == 0:
            return offset + 1
        if length & 0xC0 == 0xC0:
            return offset + 2
        offset += length + 1


def main() -> int:
    name = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "A"
    labels = b"".join(bytes([len(part)]) + part.encode() for part in name.split("."))
    header = struct.pack(">HHHHHH", secrets.randbits(16), 0x0100, 1, 0, 0, 0)
    query = header + labels + b"\0" + struct.pack(">HH", TYPES[kind], 1)
    began = time.monotonic()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(8)
        client.sendto(query, ("127.0.0.11", 53))
        try:
            data, _ = client.recvfrom(4096)
        except OSError as error:
            took = (time.monotonic() - began) * 1000
            print(f"DNS name={name} type={kind} rcode=? answers= ms={took:.0f} error={error!r}")
            return 1
    took = (time.monotonic() - began) * 1000
    _, flags, questions, answers, _, _ = struct.unpack(">HHHHHH", data[:12])
    offset = 12
    for _ in range(questions):
        offset = skip_name(data, offset) + 4
    found: list[str] = []
    for _ in range(answers):
        offset = skip_name(data, offset)
        rtype, _, ttl, size = struct.unpack(">HHIH", data[offset : offset + 10])
        offset += 10
        rdata = data[offset : offset + size]
        offset += size
        if rtype == 1:
            found.append(f"{socket.inet_ntoa(rdata)}:{ttl}")
        elif rtype == 28:
            found.append(f"{socket.inet_ntop(socket.AF_INET6, rdata)}:{ttl}")
    listed = ",".join(found)
    print(f"DNS name={name} type={kind} rcode={flags & 0xF} answers={listed} ms={took:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
