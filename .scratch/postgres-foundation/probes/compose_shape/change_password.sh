# 데이터가 있는 볼륨에서 데이터베이스 비밀번호를 바꾸는 절차다. run.py 의 4번이 이 파일의 명령을 한 줄씩
# bash 로 친다. 먼저 .env 의 AGENT_OS_DATABASE_PASSWORD 줄을 새 비밀번호로 고치고, 묶음을 푼 폴더에서 친다.
docker compose up -d --wait postgres
echo "ALTER ROLE agent_os PASSWORD :'new'" | docker compose exec -T postgres sh -c 'psql -U agent_os -d agent_os -v ON_ERROR_STOP=1 -v new="$POSTGRES_PASSWORD"'
docker compose up -d --wait --wait-timeout 600
