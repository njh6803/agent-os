이 판부터 단독 배포가 위젯 관리 서버와 그 전용 데이터베이스(PostgreSQL)를 함께 띄웁니다. 위젯이 읽는 위젯 설정을 이 서버가 `/widget-settings/<사이트 이름>` 주소로 내어 줍니다. Agent OS의 기존 데이터베이스와 표는 바뀌지 않으므로 올리기 전에 새로 해야 할 백업은 없지만, 평소처럼 백업해 두기를 권합니다. 위젯 쪽 데이터베이스는 이번에 새로 만들어져 비어 있습니다.

1. 묶음을 푼 폴더의 `compose.yaml`과 `proxy/site.conf`를 새 묶음의 것으로 통째로 바꿉니다. 운영자가 바꾼 것은 `compose.override.yaml`에 두었으므로 통째로 바꿔도 잃는 것이 없습니다.
2. `.env`에 위젯 쪽 데이터베이스 비밀번호 줄 `WIDGET_ADMIN_DATABASE_PASSWORD=<값>`을 더합니다. Agent OS 쪽 비밀번호(`AGENT_OS_DATABASE_PASSWORD`)와 다른 값을 `openssl rand -hex 32`로 만들어 씁니다(영문자와 숫자만). 이 값은 처음 띄울 때 위젯 쪽 데이터베이스에 정해지므로, 나중에 바꿀 때는 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 따릅니다.
3. `.env`의 `AGENT_OS_VERSION`을 새 판 번호로 바꾸고 `docker compose up -d --wait --wait-timeout 600`을 칩니다. 위젯 쪽 데이터베이스가 만들어지고 `widget-admin-migrate`가 표를 올린 뒤 `widget-admin`이 뜹니다.
4. 프록시를 다시 읽힙니다. 프록시 컨테이너는 정의가 그대로라 `up -d`가 다시 만들지 않고, 묶음의 `proxy/site.conf`는 읽는 폴더에 얹혀 있을 뿐이라 그대로는 옛 설정으로 답합니다. 배포 안내 "프록시 설정을 고칠 때"의 두 명령을 차례로 칩니다. 먼저 `docker compose exec proxy nginx -c /etc/agent-os/proxy/nginx.conf -t`로 문법을 보고, 이상이 없으면 `docker compose exec proxy nginx -c /etc/agent-os/proxy/nginx.conf -s reload`를 칩니다. 이 단계를 빠뜨리면 `/widget-settings/<사이트 이름>`이 기본 경로의 404로 답합니다.

새로 열리는 호스트 포트는 없습니다. 위젯 관리 서버는 프록시 안쪽에만 있고, 밖에서는 방문자 포트(443)의 `/widget-settings/` 주소 하나만 닿습니다. 위젯 설정을 읽는 이 주소는 토큰 없이 열려 있고, 다른 출처의 페이지에서도 읽을 수 있습니다.

비밀번호 줄이 없거나 비어 있으면 compose가 `.env 에 WIDGET_ADMIN_DATABASE_PASSWORD 가 없다`를 찍고 컨테이너를 하나도 만들지 않습니다. 인터넷이 막힌 서버로 이미지를 옮긴다면 새 이미지 `agent-os-widget-admin`도 함께 옮겨야 합니다(PostgreSQL 이미지는 기존 것을 그대로 씁니다). 판마다 배포 안내의 "인터넷이 막힌 서버로 이미지 옮기기"를 따릅니다.
