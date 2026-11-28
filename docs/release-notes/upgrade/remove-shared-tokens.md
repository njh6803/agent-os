이 판부터 관리 API와 운영자 채널(`/runs`)은 공유 토큰이 아니라 운영자 계정의 로그인으로만 열립니다. 이전 판에서 `Authorization` 머리에 관리 토큰이나 채널 토큰을 실어 이 경로를 부르던 프로그램은 이 판부터 401을 받습니다. 그런 프로그램이 있으면 올리기 전에 로그인 쿠키로 바꾸거나 쓰지 않게 하십시오.

1. `.env`의 `AGENT_OS_ADMIN_TOKEN`과 `AGENT_OS_CHANNEL_TOKEN` 두 줄을 지웁니다. 남겨 두면 `serve`가 변수마다 "더 쓰지 않습니다. 지워도 됩니다." 한 줄을 찍지만 그대로 뜹니다.
2. `.env`의 `AGENT_OS_VERSION`을 새 판 번호로 바꾸고 `docker compose up -d --wait --wait-timeout 600`을 칩니다.
3. 올린 뒤 첫 계정을 만듭니다. `docker compose exec serve agent-os operator system-admin <계정 이름>`을 치면 비밀번호를 두 번 묻습니다. 그 뒤 SSH 포트 포워딩으로 연 `http://127.0.0.1:3000/`에서 그 계정으로 로그인합니다. 이미 계정이 있으면 이 단계는 필요 없고 그 계정으로 로그인합니다.
