# 데이터가 있는 볼륨에서 데이터베이스 비밀번호를 바꾸는 절차다. 먼저 .env 의 AGENT_OS_DATABASE_PASSWORD 줄을
# 새 비밀번호로 고치고, 묶음을 푼 폴더에서 아래 네 줄을 그대로 붙여 넣는다. 첫 줄은 셸에 남은 같은 이름의 변수가
# .env 를 덮지 못하게 지운다. 뒤의 세 줄은 && 로 이어져, 앞 줄이 0 이 아니면 다음 줄을 치지 않는다.
# run.py 의 4번은 이 파일을 읽어 첫 줄을 뒤의 줄마다 앞에 붙여 bash 로 한 줄씩 치고, 0 이 아닌 줄에서 멈춘다.
unset AGENT_OS_DATABASE_PASSWORD
docker compose up -d --wait postgres &&
docker compose exec -T postgres sh -c 'printf "%s\n%s\n" "$POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" | psql -U agent_os -d agent_os -v ON_ERROR_STOP=1 -c "\password agent_os"' &&
docker compose up -d --wait --wait-timeout 600
