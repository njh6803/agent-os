이 판부터 단독 배포가 데이터베이스(PostgreSQL)를 함께 띄웁니다. 올리기 전에 데이터베이스를 백업하십시오. 되돌리려면 그 백업을 복원합니다. 백업과 복원의 절차는 아직 배포 안내에 없습니다.

1. 묶음을 푼 폴더의 `compose.yaml`을 새 묶음의 `compose.yaml`로 통째로 바꿉니다. 운영자가 바꾼 것은 `compose.override.yaml`에 두었으므로 통째로 바꿔도 잃는 것이 없습니다.
2. `.env`에 데이터베이스 비밀번호 줄 `AGENT_OS_DATABASE_PASSWORD=<값>`을 더합니다. 값은 `openssl rand -hex 32`로 만든 것(영문자와 숫자만)을 씁니다. 이 값은 처음 띄울 때 데이터베이스에 정해지므로, 나중에 바꿀 때는 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 따릅니다.
3. `.env`의 `AGENT_OS_VERSION`을 새 판 번호로 바꾸고 `docker compose up -d --wait --wait-timeout 600`을 칩니다. 데이터베이스가 만들어지고 `migrate`가 표를 올린 뒤 `serve`가 뜹니다.

비밀번호 줄이 없거나 비어 있으면 compose가 `.env 에 AGENT_OS_DATABASE_PASSWORD 가 없다`를 찍고 컨테이너를 하나도 만들지 않습니다. 인터넷이 막힌 서버로 이미지를 옮긴다면 PostgreSQL 이미지도 함께 옮겨야 합니다(배포 안내의 "인터넷이 막힌 서버로 이미지 옮기기").
