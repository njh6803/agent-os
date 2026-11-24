# agent-os 단독 배포 안내

이 문서는 서버 한 대에 agent-os를 올리는 운영자를 위한 안내입니다. 묶음을 푼 폴더 안에서 아래 순서대로 따라 하면 인증서와 키, 사이트 파일, 위젯 테스트 페이지 설정, 환경 변수 파일을 채워 띄우고, 떴는지 확인하고, 관리 화면에 닿을 수 있습니다.

## 1. 시작하기 전에

### 보증하는 환경

- 리눅스 x86-64 서버의 Docker Engine 28.3.3 이상과 Docker Compose 2.20.2 이상입니다. Engine 28.3.3에서 관리 화면을 서버의 `127.0.0.1`에만 열어 두는 보호가 서는 것을 확인했습니다. Engine 27.5.1에서는 보호가 서지 않아, 같은 네트워크 구간의 이웃 호스트가 관리 화면에 닿았습니다. 28.0.0과 28.3.3 사이의 판은 재지 않았고, 최소 판을 28.3.3으로 정한 이유는 아래 경고 둘이 적습니다.
- Compose는 상태 확인에 유예 동안의 짧은 확인 간격(`start_interval`)을 쓰기 때문에 2.20.2부터입니다.
- 0.1 판의 범위 밖입니다: Podman, RHEL 계열 전용 바탕 이미지, ARM 서버.
- 경고 하나. `DOCKER_INSECURE_NO_IPTABLES_RAW=1`을 준 데몬에서는 `127.0.0.1`에 발행한 포트에 같은 로컬 네트워크의 다른 호스트가 닿을 수 있다고 Docker 28.0.2의 릴리스 노트가 적습니다. 그 변수를 주지 마십시오.
- 경고 둘. Docker 28.0.0보다 오래된 판에서는 같은 네트워크 구간의 다른 호스트가 localhost에 발행한 포트에 닿는다고 Docker 문서가 적습니다. 28.3.3의 릴리스 노트는 firewalld를 다시 읽은 뒤 루프백에만 발행한 포트가 로컬 네트워크에서 닿던 문제(CVE-2025-54388)를 고쳤다고 적습니다. 그래서 최소 판이 28.3.3입니다.
- rootless 모드의 Docker와, firewalld나 ufw를 쓰는 서버에서는 관리 화면을 `127.0.0.1`에만 열어 두는 보호를 확인하지 못했습니다. 그런 서버에서는 올린 뒤 다른 호스트에서 서버 주소의 3000번 포트가 닫혀 있는지 직접 확인하십시오.
- rootless 모드와 사용자 네임스페이스 재매핑(`userns-remap`)에서는 컨테이너의 GID가 호스트의 같은 번호와 대응하지 않습니다. 3-2와 3-3이 정한 키 파일의 그룹(101, 10001)이 컨테이너 안에서 읽히지 않아 프록시나 위젯 테스트 페이지가 시작에서 끝날 수 있습니다. 이 두 모드는 보증하는 환경이 아닙니다.

### 서버의 메모리

위젯은 뜰 때마다 사이트 파일로 빌드하며, 그동안 메모리를 1.6GiB 가까이 씁니다. 스왑 없이 2GiB로 제한한 컨테이너에서는 떴고 1GiB 이하로 제한하면 빌드 도중 메모리 부족으로 죽었습니다. 그래서 compose 파일은 컨테이너에 메모리 제한을 두지 않습니다. 서버에 이만큼의 여유가 있는지 보고, 메모리 제한을 새로 걸지 마십시오.

### 공개 출처를 둘 도메인

방문자가 위젯과 위젯 테스트 페이지에 닿을 도메인(이 안내는 `agent.example.com`으로 적습니다)이 필요합니다.

- 그 도메인이 속한 등록 도메인 아래의 모든 호스트(형제 도메인 포함)를 같은 운영자가 믿을 수 있게 쥐고 있어야 합니다. agent-os는 도메인을 검사하지 않습니다.
- 도메인에는 IPv4 주소(A 레코드)만 등록하십시오. 이 배포는 443과 80을 서버의 IPv4 주소에만 열기 때문에, IPv6 주소(AAAA 레코드)를 함께 등록하면 IPv6로만 접속하는 방문자가 닿지 못합니다.
- 서버 방화벽에서 열 포트는 443과 80, 둘입니다. 80은 443으로 넘기기만 합니다.
- 서버에서 443, 80, 3000번 포트가 비어 있어야 합니다. 다른 프로그램이 쥐고 있으면 컨테이너가 뜨지 못합니다. 3000번은 관리 화면이 서버의 `127.0.0.1`에만 엽니다.

## 2. 묶음 풀기

릴리스에서 받은 `agent-os-<판 번호>.tar.gz`를 서버에서 풉니다. 풀면 같은 이름의 폴더가 하나 나옵니다. 이 안내의 명령은 모두 그 폴더 안에서 칩니다.

```bash
tar xzf agent-os-<판 번호>.tar.gz
cd agent-os-<판 번호>
```

폴더에는 아래가 있습니다.

- `compose.yaml`: 고치지 않습니다(7절).
- `.env.example`: 환경 변수 파일의 틀입니다. 판 번호와 이미지 이름공간은 채워져 있습니다.
- `tls/`: 인증서와 키를 두는 폴더입니다.
- `site/sites.toml`: 사이트 파일의 틀입니다.
- `portal/portal.toml`, `portal/keys/`: 위젯 테스트 페이지 설정의 틀과 개인 키를 두는 폴더입니다.
- `proxy/`: 프록시 설정입니다. 처음에는 고치지 않습니다.
- `README.md`: 이 문서입니다.

## 3. 채우기

### 3-1. 환경 변수 파일

```bash
cp .env.example .env
chmod 600 .env
```

`.env`에는 비밀 값이 들어갑니다. 운영자만 읽을 수 있게 두십시오(위의 `chmod 600`). 이 파일을 통째로 받는 컨테이너는 `serve` 하나이고, 데이터베이스 비밀번호는 compose가 PostgreSQL 컨테이너와 `migrate`에도 넘깁니다. 아래 칸을 채웁니다.

- `AGENT_OS_ADMIN_TOKEN`: 관리 API 토큰입니다. 관리 화면에서 입력합니다.
- `AGENT_OS_CHANNEL_TOKEN`: 채널 토큰입니다. 관리 API 토큰과 다른 값이어야 합니다.
- `AGENT_OS_DATABASE_PASSWORD`: 데이터베이스의 비밀번호입니다. 토큰처럼 아래 명령으로 만든 값을 씁니다. 영문자와 숫자만 쓰십시오. compose가 이 값을 그대로 끼워 데이터베이스의 주소를 짓기 때문에, `@`가 들면 주소를 읽지 못하고 `%` 뒤에 16진수 두 자리가 오면 다른 비밀번호로 풀립니다.
- `AGENT_OS_MODEL`: 기본 모델 플러그인의 이름입니다. 틀의 값을 그대로 써도 됩니다.
- `ANTHROPIC_API_KEY`: 모델 제공사의 API 키입니다. 이 키로 모델을 부르므로 새어 나가지 않게 하십시오.

토큰 두 개와 데이터베이스 비밀번호는 아래 명령으로 만든 값을 쓰면 됩니다. 세 번 쳐서 서로 다른 값을 받습니다.

```bash
openssl rand -hex 32
```

데이터베이스 비밀번호는 처음 띄울 때 데이터베이스 안에 정해집니다. 그 뒤에 `.env`의 이 줄만 바꾸면 `migrate`와 `serve`가 데이터베이스에 접속하지 못합니다. 바꿀 때는 12절을 따릅니다.

`AGENT_OS_VERSION`과 `AGENT_OS_NAMESPACE`는 판을 낼 때 채워져 있으므로 고치지 않습니다. 끝자리만 오른 판으로 올릴 때는 `AGENT_OS_VERSION` 한 줄만 바꿉니다(11절).

### 3-2. 인증서와 키

프록시는 `tls/fullchain.pem`(인증서에 중간 인증서를 이어 붙인 것)과 `tls/privkey.pem`(키)을 읽습니다. 사내 인증 기관이 발급한 인증서도 같은 이름으로 두면 됩니다.

내 인증서가 없으면 시험 삼아 스스로 서명한 인증서를 만들어 먼저 띄워 볼 수 있습니다. 브라우저가 이 인증서를 믿지 않으므로 경고가 뜹니다. 공개하기 전에는 실제 인증서로 바꾸십시오.

```bash
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout tls/privkey.pem -out tls/fullchain.pem -days 30 \
  -subj "/CN=agent.example.com" \
  -addext "subjectAltName=DNS:agent.example.com"
```

어느 쪽이든 키 파일의 소유와 권한을 아래처럼 맞춥니다. 프록시는 uid 101로 돌기 때문에 `root`만 읽는 키(`root:root`, 0600)는 읽지 못해 프록시가 시작에서 종료 1로 끝납니다. 키의 주인은 root로 두고 그룹 101에 읽기만 엽니다.

```bash
sudo chown root:101 tls/privkey.pem
sudo chmod 640 tls/privkey.pem
```

인증서는 시간이 지나면 만료됩니다. 갱신은 운영자가 합니다. 새 파일을 같은 이름으로 `tls/`에 둔 뒤, 새 키 파일에도 위의 `chown`과 `chmod`를 다시 치고 6절의 차례대로 프록시 설정을 다시 읽게 하십시오. 새 키가 `root`만 읽는 파일이면 프록시가 읽지 못합니다.

### 3-3. 위젯 테스트 페이지의 개인 키

위젯 테스트 페이지는 방문자에게 줄 토큰에 이 키로 서명합니다. 서명을 확인하는 공개 키는 사이트 파일(3-4)에 들어갑니다.

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out portal/keys/portal.pem
sudo chown root:10001 portal/keys/portal.pem
sudo chmod 640 portal/keys/portal.pem
```

위젯 테스트 페이지는 uid·gid 10001로 돕니다. 위의 소유(주인 root, 그룹 10001)와 권한(640)으로 두어야 그 컨테이너가 키를 읽습니다. root만 읽는 0600의 키는 위젯 테스트 페이지가 시작에서 끝납니다. 공개 키는 아래 명령이 출력합니다. 이 명령도 키를 읽으므로 `sudo`가 필요합니다.

```bash
sudo openssl pkey -in portal/keys/portal.pem -pubout
```

### 3-4. 사이트 파일과 위젯 테스트 페이지 설정

두 파일의 값은 서로 맞아야 합니다.

`site/sites.toml`에서 고칠 칸입니다.

- `issuer`: 사이트를 가리키는 이름입니다. 주소 꼴(`https://www.example.com`)로 적고, `portal/portal.toml`의 `issuer`와 같은 값으로 둡니다.
- `allowed_origins`: 위젯을 끼워 넣을 수 있는 출처입니다. 위젯 테스트 페이지의 공개 출처(`https://agent.example.com`)도 여기 들어야 합니다.
- `agents`: 이 사이트의 방문자가 열 수 있는 에이전트입니다. 틀의 `calc`는 이미지에 든 예시 에이전트입니다. 운영자가 자기 에이전트로 바꾸십시오. 에이전트는 플러그인 폴더(8절)에 둔 것의 이름입니다. 틀에 쓰지 않은 `assistant`는 문서 검색 서버가 이 묶음 밖에 따로 있어야 답합니다.
- `[[sites.public_keys]]`의 `pem`: 3-3에서 출력한 공개 키를 `-----BEGIN PUBLIC KEY-----`부터 `-----END PUBLIC KEY-----`까지 붙여 넣습니다. `kid`는 `portal/portal.toml`의 `kid`와 같은 값입니다.
- 선택 `[sites.limits]`의 `request_chars`: 한 번에 받는 요청의 글자 수 상한입니다. 적지 않으면 기본 상한 20,000자를 씁니다. 17만 자 남짓보다 크게 올리면 프록시의 본문 크기 상한(1MiB)이 먼저 413으로 답할 수 있습니다.

`portal/portal.toml`에서 고칠 칸입니다.

- `public_origin`: 방문자가 닿을 공개 출처입니다. `https://`로 시작하고 포트를 붙이지 않습니다. `site/sites.toml`의 `allowed_origins`에도 들어 있어야 합니다.
- `private_key`: 이 설정 파일이 있는 폴더 기준의 개인 키 경로입니다. 3-3처럼 만들었다면 틀의 `keys/portal.pem`을 그대로 씁니다.
- `[[sites]]`의 `agent`: `site/sites.toml`의 `agents`에 든 에이전트 하나입니다. 이 값도 `calc`에서 운영자의 에이전트로 바꾸고, 두 파일에서 같은 값으로 맞추십시오.
- `host`와 `port`: 바꾸지 않습니다. 컨테이너 안에서 `0.0.0.0:3000`에 서야 프록시가 닿습니다.

## 4. 띄우기와 확인

```bash
docker compose up -d --wait --wait-timeout 600
```

처음에는 이미지 넷과 프록시 이미지, PostgreSQL 이미지를 받고, 위젯이 뜰 때 사이트 파일로 빌드하므로 몇 분이 걸립니다. 위젯은 빌드하는 동안 확인이 실패한 채 `starting`이다가 서고 나서 `healthy`가 됩니다. 데이터베이스가 준비되면 `migrate`가 데이터베이스의 표를 이 판까지 올리고 끝나며, 그 뒤에 `serve`가 뜹니다.

`compose.yaml`의 서비스 이름과 Docker Hub의 저장소 이름은 다릅니다. 이미지를 직접 받거나 옮길 때는 아래 표로 찾으십시오. `<이름공간>`은 `.env`의 `AGENT_OS_NAMESPACE`이고, 태그는 `.env`의 `AGENT_OS_VERSION`입니다.

| 서비스 이름 | 하는 일 | Docker Hub 이미지 |
|---|---|---|
| `serve` | 런타임. 에이전트를 실행합니다 | `<이름공간>/agent-os-runtime` |
| `admin` | 관리 화면 | `<이름공간>/agent-os-admin` |
| `widget` | 위젯 | `<이름공간>/agent-os-widget` |
| `portal` | 위젯 테스트 페이지 | `<이름공간>/agent-os-widget-test-page` |
| `postgres` | 데이터베이스 | Docker Hub의 공식 이미지 `postgres`(digest로 고정) |
| `migrate` | 데이터베이스의 표를 올리고 끝납니다 | `<이름공간>/agent-os-runtime` |

```bash
docker compose ps
```

컨테이너 다섯(`serve`, `admin`, `widget`, `portal`, `postgres`. 위 표의 서비스 이름)이 모두 `healthy`이고 프록시가 `Up`이면 떴습니다. 프록시는 상태 확인이 없어 `Up`만 보이고 `healthy`가 붙지 않습니다. 떴는지는 컨테이너 기록의 `Ready` 줄이 아니라 이 상태로 보십시오. 관리 화면은 `Ready` 줄을 찍은 뒤에 서버로 가는 연결을 확인하다 실패할 수 있습니다.

`migrate`는 표를 올리고 끝나므로 `docker compose ps`에는 보이지 않습니다. `docker compose ps -a`에는 `Exited (0)`으로 남는데, 이것은 고장이 아니라 일을 마친 상태입니다. `docker compose up -d`를 칠 때마다 `migrate`가 다시 돌고, 올릴 것이 없으면 그대로 끝납니다.

`up`이 `service "migrate" didn't complete successfully: exit 1`로 끝나면 `serve`는 뜨지 않습니다. 까닭은 아래 명령이 찍습니다.

```bash
docker compose logs migrate
```

까닭은 마지막 줄이 아닐 수 있습니다. 데이터베이스가 늦게 준비되면 다시 시도한다는 알림 한 줄이 먼저 찍히고, 그 뒤에 멈춘 까닭을 적은 첫 줄이 섭니다. 첫 줄 뒤에는 대개 할 일을 적은 설명 줄이 붙고, 표를 올리다 실패했으면 첫 줄(`표를 올리다 실패했습니다`로 시작합니다) 뒤에 자세한 기록이 길게 붙습니다. 그래서 마지막 줄이 아니라 멈춘 까닭을 적은 그 첫 줄과 설명 줄을 보십시오.

`serve`가 뜨지 않아 관리 화면을 볼 수 없을 때 먼저 칠 명령과 기록의 글을 읽는 법은 13절에 있습니다.

방문자가 닿는 쪽은 브라우저로 `https://agent.example.com/`을 열어 봅니다. 위젯 테스트 페이지가 뜨고 질문에 답이 오면 됩니다. 명령으로 보려면 아래를 칩니다. 이 명령은 인증서를 검증하므로, 만료됐거나 도메인이 다른 인증서면 응답을 받기 전에 실패합니다. 스스로 서명한 인증서를 시험 삼아 쓸 때만 `curl`에 `-k`를 덧붙여 검증을 끕니다.

```bash
curl -sS -L -o /dev/null -w '%{http_code}\n' https://agent.example.com/
curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' http://agent.example.com/
```

첫 줄은 200이고(`/`는 위젯 테스트 페이지로 넘겨지므로 `-L`로 따라갑니다), 둘째 줄은 308과 `https://` 주소입니다.

### 관리 화면에 닿기

관리 화면은 서버의 `127.0.0.1:3000`에만 열려 있어 인터넷에서는 닿지 않습니다. 내 PC에서 SSH 포트 포워딩으로 닿습니다.

```bash
ssh -L 3000:127.0.0.1:3000 <사용자>@<서버 주소>
```

이 SSH 연결을 열어 둔 채, 내 PC의 브라우저로 `http://127.0.0.1:3000/`을 열고 `AGENT_OS_ADMIN_TOKEN`의 값을 입력합니다. 관리 화면에서 플러그인을 켜고 끌 수 있습니다.

### 띄우기가 끊겼을 때

`up`이 도는 동안 Docker나 서버가 다시 켜지면 `up`이 1로 끝나고, `migrate`나 `serve`가 만들어지기만 한 채(`Created`) 남을 수 있습니다. Docker는 다시 켜질 때 그런 컨테이너를 띄우지 않습니다. 아래 명령을 다시 치면 됩니다.

```bash
docker compose up -d --wait
```

처음 띄우는 `up`이 데이터베이스를 만드는 도중에 전원이 끊기면 데이터베이스가 반쯤 만들어진 채 남을 수 있습니다. 그 뒤로는 `up`을 다시 쳐도 `migrate`가 데이터베이스가 접속을 허락하지 않았다는 글이나 데이터베이스가 없다는 글로 멈추거나, `docker compose logs postgres`가 `could not open file "global/pg_filenode.map"`을 되풀이합니다. 이때는 아직 담긴 데이터가 없으므로 데이터베이스의 볼륨을 지우고 다시 띄웁니다.

```bash
docker compose down
docker volume rm agent-os_database
docker compose up -d --wait
```

이 길은 처음 띄우기가 한 번도 끝나지 않은 배치에만 쓰십시오. 한 번이라도 뜬 데이터베이스는 전원이 끊겨도 다음에 뜰 때 스스로 복구하며, 그 볼륨을 지우면 데이터를 모두 잃습니다. `docker compose down -v`는 플러그인 폴더와 기록 폴더의 볼륨까지 지우므로 쓰지 않습니다.

## 5. 설정을 고친 뒤

설정을 고친 뒤 서비스를 다시 띄울 때는 `docker compose restart`가 아니라 `docker compose up -d`를 칩니다. `up -d`는 설정이 바뀐 컨테이너만 다시 만들고 나머지는 그대로 둡니다. `restart`는 데이터베이스가 준비되기를 기다리지 않고 모든 컨테이너를 한꺼번에 다시 띄웁니다. `docker stop`이나 `docker kill`로 멈춘 PostgreSQL 컨테이너는 저절로 다시 뜨지 않으므로 이때도 `docker compose up -d`로 띄웁니다.

### 사이트 파일이나 위젯 테스트 페이지 설정을 고쳤을 때

위젯은 뜰 때 사이트 파일로 빌드하고, `serve`와 위젯 테스트 페이지도 그 파일을 읽습니다. 고친 뒤에는 세 컨테이너를 다시 띄웁니다.

```bash
docker compose restart serve widget portal
```

위젯이 다시 빌드하는 동안 위젯은 응답하지 않고 프록시가 502로 답합니다. 재 본 서버에서는 10초에서 30초 사이였고, 서버의 사양에 따라 더 걸릴 수 있습니다. 고친 허용 출처가 듣지 않을 때는 이 세 컨테이너를 다시 띄웠는지 먼저 보십시오.

### 컨테이너를 다시 만들거나 판을 올린 직후

컨테이너 하나를 다시 만들거나 판을 올린 직후 약 10초 동안은 그 컨테이너로 가는 요청이 매달리거나 502로 끝날 수 있습니다. 프록시가 새 주소를 다시 찾는 시간입니다. 프록시를 다시 시작할 필요는 없습니다.

## 6. 프록시 설정을 고칠 때

프록시 설정은 `proxy/` 폴더째 컨테이너에 읽기 전용으로 얹혀 있어서, 호스트에서 파일을 고치면(편집기의 저장이나 `sed -i`도 같습니다) 컨테이너에 보입니다. 고친 뒤에는 먼저 문법을 보고, 이상이 없을 때만 다시 읽힙니다.

```bash
docker compose exec proxy nginx -c /etc/agent-os/proxy/nginx.conf -t
docker compose exec proxy nginx -c /etc/agent-os/proxy/nginx.conf -s reload
```

설정이 깨져 있으면 첫 명령이 종료 1로 끝나고, 둘째 명령을 쳐도 옛 설정이 계속 답합니다. 인증서나 키 파일을 바꾼 뒤에도 같은 두 명령을 칩니다.

## 7. 고치지 말 것

`compose.yaml`은 고치지 않습니다. 특히 아래 셋입니다.

- `ports`: 밖에 열리는 것은 프록시의 443과 80, 서버의 `127.0.0.1`에만 열리는 관리 화면의 3000, 셋뿐입니다.
  - `serve`나 관리 화면을 호스트의 모든 주소에 발행하면 로그인 없는 관리 API가 암호화 없이 인터넷에 열립니다.
  - https를 443이 아닌 호스트 포트로 발행하면 80의 넘김이 닿지 않는 443을 가리킵니다.
  - 프록시의 `0.0.0.0:`을 지우면 Docker의 기본 설정(userland-proxy를 켬)에서 IPv6로 온 방문자가 모두 안쪽 게이트웨이 주소 하나로 보입니다. 그러면 토큰 끝점의 요청 한도(접속 주소마다 분당 30번)를 IPv6 방문자 전체가 함께 씁니다.
  - PostgreSQL(`postgres`)은 어느 주소에도 발행하지 않습니다. 발행하면 데이터베이스가 비밀번호 하나로 서버 밖에 열립니다.
- `user:`: 우리 이미지 넷(`serve`, `admin`, `widget`, `portal`)과 `migrate`에는 더하지 않습니다. 이미지가 정한 사용자(uid 10001)로 돌아야 합니다. 프록시에 이미 적힌 `user:`도 바꾸지 않습니다. passwd 항목이 없는 uid로 띄우면 `serve`가 시작할 때 `KeyError: 'getpwuid(): uid not found'`로 끝납니다. PostgreSQL에 적힌 `user: "999:999"`도 바꾸지 않습니다. 데이터베이스의 데이터 폴더가 처음 띄울 때 그 uid의 소유로 만들어지므로, 바꾸면 PostgreSQL이 자기 데이터 폴더를 읽지 못합니다.
- 안쪽 네트워크의 IPv6: 켜지 않습니다. 443과 80이 IPv4에만 열려야 접속 주소별 요청 한도가 맞게 섭니다.

## 8. 데이터를 담는 볼륨

플러그인 폴더(`/app/plugins`)와 기록 폴더(`/data/traces`)는 compose가 만드는 이름 있는 볼륨(`agent-os_plugins`, `agent-os_traces`)입니다. 판을 바꿔도 운영자가 설치한 플러그인과 기록이 남습니다.

데이터베이스의 데이터는 이름 있는 볼륨 `agent-os_database`에 듭니다. 판을 바꾸거나 `docker compose down` 뒤에 다시 띄워도 남습니다. 데이터베이스를 백업하고 복원하는 절차는 이 안내가 아직 다루지 않습니다.

- 플러그인 볼륨은 처음 붙을 때만 이미지 안의 예시 플러그인으로 채워집니다. 판을 올려도 이미 붙은 볼륨은 새 이미지의 예시 플러그인으로 갱신되지 않고, 운영자가 켜고 끈 상태와 설치한 플러그인이 보존됩니다. 새 판의 예시 플러그인이 필요하면 볼륨을 새로 만들거나(운영자가 설치한 플러그인도 사라지므로 먼저 백업하십시오) 필요한 파일을 직접 복사하십시오.
- 인터넷이 막힌 서버에서는 운영자가 `npx`로 띄우는 MCP 서버가 서지 않습니다. `npx`가 인터넷의 레지스트리에 묻다 실패하기 때문입니다. 이미지에 미리 설치된 예시 MCP 서버는 인터넷 없이 돕니다.

### 이름 있는 볼륨 대신 호스트 폴더를 쓰려면

백업 같은 이유로 두 자리를 호스트의 폴더로 바꾸려면 `compose.yaml`을 고치지 않고 같은 폴더에 `compose.override.yaml`을 둡니다. 이 절은 플러그인 폴더와 기록 폴더만 다룹니다. 데이터베이스의 볼륨(`agent-os_database`)은 호스트 폴더로 바꾸지 마십시오. 이 절차는 처음 띄우기 전용입니다. 이미 띄워 쓰던 배포에서 바꾸면 이름 있는 볼륨에 든 설치한 플러그인과 기록이 서비스에서 보이지 않게 되고, 이 안내는 그 내용을 호스트 폴더로 옮기는 절차를 다루지 않습니다. 쓰던 배포에서는 바꾸지 마십시오. 띄우기 전에 아래 세 가지를 먼저 해야 합니다. 빠뜨리면 상태 확인은 `healthy`인데 플러그인을 끄고 켜는 요청과 실행이 500으로 끝납니다.

1. 이미지의 예시 플러그인을 호스트 폴더로 옮깁니다. 빈 폴더를 붙이면 기본 모델 플러그인이 없다며 `serve`가 시작에서 끝납니다.
2. 두 폴더의 소유를 `10001:10001`로 넘깁니다.
3. 폴더가 없는 채로 띄우지 않습니다. 없는 경로를 주면 Docker가 root 소유로 만들어 컨테이너가 쓰지 못합니다.

```bash
NS=$(grep '^AGENT_OS_NAMESPACE=' .env | cut -d= -f2)
VER=$(grep '^AGENT_OS_VERSION=' .env | cut -d= -f2)
mkdir -p data/plugins data/traces
docker run --rm --user 0 --entrypoint cp -v "$PWD/data/plugins:/dest" "$NS/agent-os-runtime:$VER" -a /app/plugins/. /dest/
sudo chown -R 10001:10001 data/plugins data/traces
```

```yaml
# compose.override.yaml
services:
  serve:
    volumes:
      - ./data/plugins:/app/plugins
      - ./data/traces:/data/traces
```

## 9. 인터넷이 막힌 서버로 이미지 옮기기

인터넷이 되는 PC에서 이미지를 받아 파일 하나로 저장하고, 그 파일을 서버로 옮겨 불러옵니다. 아래는 묶음을 푼 폴더에서 치는 명령입니다. 인터넷이 되는 PC에도 같은 묶음을 풀어 두십시오.

프록시 이미지와 PostgreSQL 이미지는 digest로 고정되어 있는데(`compose.yaml`의 `nginx@sha256:…`와 `postgres@sha256:…`), 파일로 저장했다가 불러오면 그 digest가 남지 않습니다. 서버의 Docker가 그 이름의 이미지를 찾지 못해 이미지를 받으려다 실패하므로, 두 이미지에는 태그(`agent-os-proxy:local`, `agent-os-postgres:local`)를 붙여 옮기고 서버에서 `compose.override.yaml`로 그 태그를 쓰게 합니다.

인터넷이 되는 PC에서:

이미 설정한 `.env`가 있는 폴더에서는 이 명령이 그 값을 지우지 않도록, `.env`가 없을 때만 복사합니다. 이 PC는 아무것도 띄우지 않으므로 `.env`의 데이터베이스 비밀번호 칸을 채우지 않습니다. 대신 앞의 두 명령을 위해서만 붙이는 값(`AGENT_OS_DATABASE_PASSWORD=unused`)을 붙입니다. 붙이지 않으면 비밀번호 칸이 비었다며 두 명령이 1로 끝납니다. 이 값은 그 두 명령에만 쓰이고 서버로 옮기지 않습니다.

```bash
[ -f .env ] || cp .env.example .env
AGENT_OS_DATABASE_PASSWORD=unused docker compose pull
AGENT_OS_DATABASE_PASSWORD=unused docker compose config --images | sort -u > images.txt
docker tag "$(grep '^nginx@' images.txt)" agent-os-proxy:local
docker tag "$(grep '^postgres@' images.txt)" agent-os-postgres:local
grep -v -e '^nginx@' -e '^postgres@' images.txt > save.txt
echo agent-os-proxy:local >> save.txt
echo agent-os-postgres:local >> save.txt
docker save -o agent-os-images.tar $(cat save.txt)
sha256sum agent-os-images.tar > agent-os-images.tar.sha256
for i in $(cat save.txt); do echo "$(docker image inspect --format '{{.Id}}' $i) $i"; done > images.id
```

`agent-os-images.tar`, `agent-os-images.tar.sha256`, `save.txt`, `images.id`와 묶음 폴더를 서버로 옮깁니다. 서버의 묶음 폴더에서:

```bash
sha256sum -c agent-os-images.tar.sha256
docker load -i agent-os-images.tar
for i in $(cat save.txt); do echo "$(docker image inspect --format '{{.Id}}' $i) $i"; done | diff - images.id && echo 이미지가 같다
```

서버에 `compose.override.yaml`이 아직 없으면 아래로 만듭니다. 8절에서 이미 만들었다면 `services:` 아래에 `proxy:` 항목과 `postgres:` 항목만 더합니다.

```yaml
# compose.override.yaml
services:
  proxy:
    image: agent-os-proxy:local
  postgres:
    image: agent-os-postgres:local
```

대조하는 해시는 둘입니다. 파일의 해시(`sha256sum`)는 옮기는 도중 파일이 망가지지 않았는지 봅니다. 이미지의 ID(`docker image inspect`가 보이는 `sha256:` 값)는 서버에서 불러온 이미지가 인터넷이 되는 PC에서 받은 이미지와 같은지 봅니다. 레지스트리의 digest는 불러온 이미지에는 남지 않으므로 대조에 쓰지 않습니다.

## 10. Docker Hub에서 받는 횟수 제한

이미지는 Docker Hub에서 받습니다. Docker Hub는 받는 횟수를 제한합니다. Docker 문서(<https://docs.docker.com/docker-hub/usage/pulls/>)의 표에서 읽은 값은, 로그인하지 않으면 6시간에 IPv4 주소나 IPv6 /64마다 100회이고, 무료 개인 계정은 6시간에 200회입니다. 이미지를 내려받는 GET 요청만 세고 HEAD 요청은 세지 않는다고 적혀 있습니다. 같은 IPv4 주소 뒤의 여러 서버는 로그인하지 않은 몫을 함께 씁니다. 이 수치는 Docker가 바꿀 수 있으므로 Docker의 현재 문서를 보십시오. 여러 서버에 받다가 막히면 9절처럼 한 PC에서 받아 옮기거나 `docker login`으로 로그인한 뒤 받으십시오.

## 11. 판을 바꿀 때

판을 바꾸기 전에 먼저 그 판의 릴리스 노트에서 "올릴 때 할 일"을 읽으십시오. 끝자리만 오른 판은 올릴 때 손댈 것이 없고, `.env`의 `AGENT_OS_VERSION` 한 줄만 새 판 번호로 바꾼 뒤 `docker compose up -d`를 치면 됩니다. 가운데 자리가 오른 판은 그 노트가 무엇을 무엇으로 바꾸라고 적습니다. 판을 올리는 절차 전체는 이 안내가 다루지 않습니다.

- 데이터베이스의 표를 새 판에 맞게 올리는 일은 `docker compose up -d`가 `migrate`로 합니다. 운영자가 따로 칠 명령은 없습니다.
- 노트의 "올릴 때 할 일"이 `compose.yaml`을 바꾸라고 적은 판은 새 묶음의 `compose.yaml`로 통째로 바꿉니다. 운영자가 바꾼 것은 7절대로 `compose.override.yaml`에 두었으므로 통째로 바꿔도 잃는 것이 없습니다.
- 표를 바꾼 판에서 그 앞의 판으로 되돌리면, 옛 판의 `migrate`가 `데이터베이스가 이 판보다 새롭습니다.`로 멈추고 `serve`가 뜨지 않습니다. 되돌리는 길은 올리기 전에 받아 둔 데이터베이스의 백업을 복원하는 것이고, 그 절차는 아직 이 안내에 없습니다.

## 12. 데이터베이스 비밀번호 바꾸기

데이터베이스의 비밀번호는 처음 띄울 때 데이터베이스 안의 계정에 정해집니다. 그 뒤에 `.env`의 `AGENT_OS_DATABASE_PASSWORD`만 바꾸면 `up -d`가 1로 끝나고, `docker compose logs migrate`에 데이터베이스가 계정이나 비밀번호를 받아들이지 않았다는 글이 찍히며, `serve`는 뜨지 않습니다. 그래서 `.env`와 데이터베이스 안의 계정을 둘 다 바꿉니다.

먼저 `.env`의 `AGENT_OS_DATABASE_PASSWORD`를 새 값(`openssl rand -hex 32`로 만든 값)으로 고칩니다. 그다음 묶음을 푼 폴더에서 아래 네 줄을 고치지 말고 그대로 붙여 넣습니다.

```bash
unset AGENT_OS_DATABASE_PASSWORD COMPOSE_ENV_FILES
docker compose up -d --wait postgres &&
docker compose exec -T postgres sh -c 'printf "%s\n%s\n" "$POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" | psql -U agent_os -d agent_os -v ON_ERROR_STOP=1 -c "\password agent_os"' &&
docker compose up -d --wait --wait-timeout 600
```

- 첫 줄은 셸에 남은 같은 이름의 변수를 지웁니다. compose는 셸의 값을 `.env`의 값보다 먼저 씁니다. 앞서 그 이름을 셸에 내보냈다면(`export`) 옛 값으로 PostgreSQL을 다시 만듭니다. `COMPOSE_ENV_FILES`가 다른 파일을 가리키면 compose가 `.env`를 읽지 않으므로 그것도 지웁니다.
- 둘째 줄은 PostgreSQL 컨테이너만 새 `.env`로 다시 만듭니다. 데이터는 볼륨에 남습니다.
- 셋째 줄은 PostgreSQL 컨테이너 안에서 계정의 비밀번호를 새 값으로 바꿉니다. 새 값은 그 컨테이너의 환경 변수에서 오고, 운영자가 치는 명령줄에는 실리지 않습니다. `psql`의 `\password`는 값을 되돌릴 수 없게 바꾼 꼴(해시)로 보내므로, 바꾸다 실패해도 데이터베이스의 기록에 새 비밀번호가 그대로 남지 않습니다. 이 줄은 묻는 글 두 줄(`Enter new password for user "agent_os":`, `Enter it again:`)을 찍지만 입력을 기다리지 않습니다.
- 넷째 줄은 `migrate`와 `serve`를 새 비밀번호로 다시 띄웁니다.
- 뒤의 세 줄은 `&&`로 이어져, 한 줄이 실패하면 다음 줄을 치지 않습니다.

이 절차가 도는 동안에는 몇 초 동안 요청이 실패할 수 있습니다. 둘째 줄이 PostgreSQL을 다시 만드는 동안 `serve`의 접속이 모두 끊기고, 셋째 줄이 비밀번호를 바꾼 때부터 넷째 줄이 `serve`를 다시 띄울 때까지는 옛 `serve`가 새로 붙지 못합니다. 이 절차를 `serve`와 `migrate`의 대역 컨테이너로 여러 번 쟀을 때 `serve`의 새 접속 줄 사이의 가장 긴 틈은 2.7초에서 6.8초 사이였습니다. 실제 `serve`는 더 걸릴 수 있습니다.

셋째 줄이나 넷째 줄이 실패하면 그 줄이 찍은 까닭을 고친 뒤, 같은 새 `.env`로 네 줄을 처음부터 다시 칩니다. 셋째 줄은 지금의 비밀번호를 묻지 않고 같은 새 값을 다시 넣으므로, 비밀번호가 이미 바뀐 뒤에 다시 쳐도 됩니다.

비밀번호를 문장에 직접 넣는 `ALTER ROLE agent_os PASSWORD '…'`로 바꿔 치지 마십시오. 데이터베이스가 그 문장을 거절하면 문장이 평문 비밀번호째 데이터베이스의 기록에 남습니다.

## 13. 문제 해결

이 절은 `serve`가 뜨지 않아 관리 화면을 볼 수 없을 때를 다룹니다. 관리 화면이 `serve`에서 받아 보이는 앱이라, `serve`가 죽으면 화면 안의 도구는 쓸 수 없고 서버에서 명령으로 봐야 합니다. `migrate`가 멈췄을 때 까닭을 읽는 법은 4절에, 처음 띄우기가 끊긴 배치를 되살리는 법은 4절의 "띄우기가 끊겼을 때"에, 데이터베이스 비밀번호를 바꾸는 법은 12절에 있어서 여기에 옮기지 않고 가리키기만 합니다.

### 먼저 칠 명령

서버에서 묶음을 푼 폴더로 가서 아래 두 명령을 칩니다.

```bash
docker compose ps --all
docker compose logs serve
```

`docker compose ps --all`은 끝난 컨테이너까지 서비스마다 상태를 보입니다. `docker compose logs` 뒤에는 서비스 이름(4절 표의 이름과 `proxy`)을 붙여, 그 서비스가 남긴 글을 봅니다. 상태는 이렇게 읽습니다.

- `healthy`가 붙은 `Up`은 뜬 것입니다. 프록시는 상태 확인이 없어 `Up`만 보이고, 그것도 뜬 것입니다.
- `migrate`의 `Exited (0)`은 표를 올리고 일을 마친 것입니다. 고장이 아니므로 고치려 들지 않습니다.
- 그 밖의 `Exited`와 `Restarting`과 `Created`는 봐야 할 상태입니다. `Restarting`은 컨테이너가 시작하다 끝나서 Docker가 다시 띄우는 중이라는 뜻입니다. `Created`는 만들어지기만 하고 뜨지 않은 것입니다. `migrate`가 멈추면 `serve`가 `Created`로 남고, 띄우기가 끊긴 때에도 그렇게 남습니다(4절).

### `serve`와 `migrate`가 멈출 때 찍는 글

`serve`와 `migrate`는 시작하다 멈출 때와 다시 시도할 때 아래 글을 찍습니다. `docker compose logs serve`나 `docker compose logs migrate`에서 찾아 같은 글의 행을 읽으십시오. 표에서 `<자리>`는 데이터베이스의 `호스트:포트/데이터베이스`(이 묶음에서는 `postgres:5432/agent_os`)이고, `<까닭>`은 `오류 번호 28P01` 같은 오류 번호나 `ConnectionRefusedError`, `gaierror`, `TimeoutError` 같은 오류의 이름이며, `<판>`은 데이터베이스 표의 판 번호입니다(표가 없으면 `없음`). 표의 글에는 계정도 비밀번호도 데이터베이스 드라이버가 낸 글도 들지 않습니다. 다만 맨 아래 `표를 올리다 실패했습니다`의 줄 뒤에 붙는 자세한 기록은 이 표 밖이고, 그 기록에는 마이그레이션이 다루던 값이 실릴 수 있습니다.

| 기록에 찍히는 글 | 찍는 쪽 | 종료 코드 | 뜻과 할 일 |
|---|---|---|---|
| `AGENT_OS_DATABASE_URL 이 비어 있습니다. serve 와 migrate 는 PostgreSQL 데이터베이스가 있어야 돕니다.` `단독 배포에서는 compose 가 .env 의 AGENT_OS_DATABASE_PASSWORD 로 이 값을 짓습니다. 개발 PC 의 값은 README 에 있습니다.` | `serve`, `migrate` | 1 | 데이터베이스의 주소가 서버에 전해지지 않았습니다. 묶음의 `compose.yaml`로 띄우면 compose가 짓는 값이라 보통 나오지 않습니다. `compose.yaml`을 고쳤는지 보십시오(7절). |
| `AGENT_OS_DATABASE_URL 을 읽지 못했습니다. postgresql://계정:비밀번호@호스트:포트/데이터베이스 꼴이어야 합니다.` `값에는 비밀번호가 들어 있어 여기 찍지 않습니다. 비밀번호에 @ 가 들면 주소를 읽지 못하므로, 비밀번호는 영문자와 숫자만 씁니다.` | `serve`, `migrate` | 1 | 주소의 꼴이 틀렸습니다. 흔한 까닭은 `.env`의 `AGENT_OS_DATABASE_PASSWORD`에 `@`나 영문자와 숫자가 아닌 글자가 든 것입니다(3-1). 이미 데이터베이스가 만들어진 배치에서 비밀번호를 바꿀 때는 12절을 따릅니다. |
| `데이터베이스(<자리>)에 아직 닿지 못해 최대 30초 동안 다시 시도합니다.` | `serve`, `migrate` | 없음 | 멈춘 것이 아닙니다. 데이터베이스가 아직 준비되지 않아 첫 시도가 실패했고, 30초까지 1초 간격으로 다시 시도합니다. 그 안에 닿으면 이 한 줄만 남고 그대로 뜹니다. |
| `데이터베이스(<자리>)에 닿지 못했습니다. 30초 동안 다시 시도했습니다(<까닭>).` | `serve`, `migrate` | `serve` 3, `migrate` 1 | 30초를 기다려도 닿지 못했습니다. `docker compose ps --all`로 `postgres`가 `healthy`인지 보고 `docker compose logs postgres`를 봅니다. `gaierror`는 주소의 이름을 찾지 못한 것이고, `ConnectionRefusedError`는 그 주소에서 듣는 데이터베이스가 없는 것입니다. |
| `데이터베이스(<자리>)가 계정이나 비밀번호를 받아들이지 않았습니다(<까닭>).` `.env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다. 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.` | `serve`, `migrate` | `serve` 3, `migrate` 1 | `.env`의 비밀번호가 데이터베이스 안의 비밀번호와 다릅니다. 12절을 따릅니다. |
| `데이터베이스(<자리>)가 이 접속을 허락하지 않았습니다(<까닭>).` `처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.` | `serve`, `migrate` | `serve` 3, `migrate` 1 | 처음 띄우는 도중에 전원이 끊긴 배치일 수 있습니다. 4절의 "띄우기가 끊겼을 때"를 따릅니다. 한 번이라도 뜬 배치에서는 그 절의 볼륨 지우기를 쓰지 마십시오. |
| `데이터베이스(<자리>)가 없습니다(<까닭>). 주소의 데이터베이스 이름을 확인하십시오.` `처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.` | `serve`, `migrate` | `serve` 3, `migrate` 1 | 위와 같이 4절의 "띄우기가 끊겼을 때"를 따릅니다. 이 묶음에서는 데이터베이스 이름을 compose가 정하므로 `compose.yaml`을 고치지 않았는지도 봅니다. |
| `데이터베이스(<자리>)에 접속하지 못했습니다(<까닭>).` | `serve`, `migrate` | `serve` 3, `migrate` 1 | 위의 어느 갈래에도 들지 않는 접속 실패입니다. `<까닭>`을 적어 두고 `docker compose logs postgres`와 함께 봅니다. |
| `데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오.` `표의 판은 <판>이고 이 판의 마지막 판은 <판>입니다.` | `serve` | 3 | `migrate`가 표를 올리지 않은 채 `serve`만 떴습니다. `docker compose up -d`를 다시 치면 `migrate`가 먼저 돌고 `serve`가 뜹니다. |
| `데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.` `표의 판은 <판>이고 이 판이 아는 마지막 판은 <판>입니다.` | `serve`, `migrate` | `serve` 3, `migrate` 1 | 표를 바꾼 판에서 앞의 판으로 되돌렸습니다. 11절을 읽고, 올리기 전에 받아 둔 백업을 복원하거나 새 판으로 돌아가십시오. |
| `데이터베이스(<자리>)를 확인하다 뜻밖의 오류로 멈췄습니다(<까닭>).` `이 판의 결함일 수 있습니다. 예외의 글과 역추적은 비밀번호가 섞일 수 있어 찍지 않습니다.` | `serve`, `migrate` | `serve` 3, `migrate` 1 | 위 어느 갈래도 아닌 뜻밖의 오류입니다. 이 판의 결함일 수 있으니 `<까닭>`과 떠 있는 판의 번호(아래 "지금 떠 있는 판")를 함께 알리십시오. |
| `데이터베이스(<자리>)의 연결을 닫다 오류가 났습니다(<까닭>).` | `serve` | 바뀌지 않음 | 서버를 끄는 도중에 연결을 닫다 난 오류입니다. 종료 코드는 이 글 때문에 바뀌지 않습니다. 되풀이되면 `<까닭>`을 적어 둡니다. |
| `표를 <판>에서 <판>으로 올렸습니다.` | `migrate` | 0 | 표를 새 판으로 올리고 끝났습니다. 정상입니다. |
| `표가 이미 마지막 판(<판>)입니다.` | `migrate` | 0 | 올릴 것이 없어 그대로 끝났습니다. 정상입니다. |
| `표를 올리다 실패했습니다(<까닭>). 표의 판은 올리기 전 그대로 <판>입니다.` | `migrate` | 1 | 표를 올리다 실패했습니다. 표는 올리기 전 그대로입니다. 이 줄 뒤에 오류의 자세한 기록이 길게 붙는데, 이 판의 결함이므로 첫 줄과 그 기록을 떠 있는 판의 번호(아래 "지금 떠 있는 판")와 함께 알리십시오. 그 기록은 남에게 보내기 전에 한 번 훑어보십시오. |

`serve`가 3으로 멈출 때는 글 앞뒤에 웹 서버가 붙이는 줄이 따라옵니다. 아래는 비밀번호가 틀린 때 실제 컨테이너에서 찍힌 기록입니다.

```text
INFO:     Started server process [7]
INFO:     Waiting for application startup.
ERROR:    데이터베이스(postgres:5432/agent_os)가 계정이나 비밀번호를 받아들이지 않았습니다(오류 번호 28P01).
  .env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다. 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.
ERROR:    Application startup failed. Exiting.
```

첫 `ERROR:`는 웹 서버가 까닭 앞에 붙인 머리이고, 끝의 `ERROR:    Application startup failed. Exiting.`은 웹 서버가 붙이는 줄이라 까닭이 아닙니다. 까닭은 그 사이의 글입니다. 다시 시도하는 알림 한 줄도 그 사이에 찍힐 수 있습니다. `serve`는 멈춰도 Docker가 다시 띄우므로(`restart: unless-stopped`), 같은 기록이 되풀이될 수 있습니다. `migrate`는 다시 띄우지 않고 종료 1로 끝나며, `up`이 그것을 알립니다(4절).

### 위젯과 관리 화면

위젯이 종료 1로 끝났으면 대개 사이트 파일(`site/sites.toml`)이 없거나 깨졌거나 읽히지 않는 것입니다. 까닭은 `docker compose logs widget`에 글로 찍힙니다. 3-4를 보고 고친 뒤 5절대로 다시 띄웁니다.

관리 화면은 컨테이너 기록에 `Ready` 줄을 찍은 뒤에도 `serve`로 가는 연결을 확인하다 실패할 수 있습니다. 그래서 `Ready` 줄이 보여도 떴다고 보지 말고 `docker compose ps --all`의 상태로 보십시오(4절에서 상태를 보는 것과 같되, 끝난 컨테이너까지 보입니다). 상태의 `Exited (숫자)`에서 숫자가 종료 코드이고, 0이 아니면 오류로 끝난 것입니다. 까닭은 `docker compose logs admin`의 `Ready` 줄 뒤에 있습니다.

### 지금 떠 있는 판

```bash
docker compose ps
docker compose exec serve agent-os --version
```

`docker compose ps`의 이미지 칸에 떠 있는 컨테이너의 이미지 태그가 보입니다. 두 번째 명령은 떠 있는 `serve` 컨테이너 안에서 판 번호를 찍습니다. `.env`의 `AGENT_OS_VERSION`은 다음에 띄울 판입니다. `.env`를 고친 뒤 `docker compose up -d`로 다시 띄우지 않았으면 떠 있는 판과 다를 수 있습니다.

### 남에게 보내면 안 되는 출력

도움을 청하려고 출력을 남에게 보낼 때 아래 두 명령의 출력은 보내지 마십시오.

- `docker compose config`: `.env`의 값을 펼쳐 평문으로 찍습니다. 데이터베이스 비밀번호가 그대로 보이고, 쓰는 Compose 판에 따라 관리 토큰, 채널 토큰, API 키도 보일 수 있습니다.
- 컨테이너에 대한 `docker inspect`: 컨테이너의 환경 변수를 찍습니다. `serve`는 `.env`를 통째로 받으므로 그 값들이 그대로 보입니다.

이미지 이름과 태그만 필요하면 `docker compose config --images`는 그 한 줄씩만 찍습니다. 위 표의 글에는 비밀번호가 없습니다. 그래도 기록 전체를 남에게 보내기 전에는 한 번 훑어보십시오.

### `serve`는 떴는데 에이전트가 답하지 않을 때

`serve`가 `healthy`인데 에이전트가 답하지 않으면 관리 화면(4절의 "관리 화면에 닿기")의 플러그인 화면을 엽니다. 켜 둔 원격 MCP 서버와 모델마다 행에 접속 확인이 보이고, 화면을 열어 둔 동안 30초마다 다시 확인합니다. stdio로 띄우는 MCP 서버는 확인할 때 프로세스를 띄우므로 행의 `접속 확인` 버튼을 눌러야 확인합니다.

- `붙음`: 그 서버가 답했고 키를 받아들였으며 그 이름의 모델을 안다는 데까지입니다. 그 키로 모델을 부를 수 있는지(사용 한도, 권한, 모델을 부르는 쪽의 장애)는 가르지 못합니다. `붙음`인데 답이 없으면 실행 화면에서 그 실행의 기록을 봅니다.
- `붙지 못함`: 행 옆의 글이 까닭입니다. 읽는 예는 셋입니다.
  - `서버에 닿지 못했다`가 든 모델 행은 모델 서버가 꺼졌거나 주소가 틀린 것입니다.
  - `키를 받아들이지 않았다(HTTP 401)`가 든 모델 행은 `.env`의 `ANTHROPIC_API_KEY`처럼 그 모델이 읽는 키가 틀렸거나 만료된 것입니다.
  - 원격 MCP 서버 행의 글이 `(HTTP 401 Unauthorized)`로 끝나면 그 서버가 보낸 토큰을 받아들이지 않은 것입니다.

두 가지는 `붙지 못함`으로 보이는데 실제로는 실행되는 경우입니다. 처음 띄울 때 내려받는 stdio 서버는 20초를 넘기면 `붙지 못함`으로 보일 수 있고, 내려받은 뒤에 다시 누르면 `붙음`이 됩니다. 환경 변수(`ANTHROPIC_API_URL`)로 주소를 바꿔 다른 중계 서버에 붙인 `anthropic` 모델은, 그 서버가 모델 하나를 묻는 요청을 모르면 실행은 되는데 `붙지 못함`으로 보일 수 있습니다.

### 원격 MCP 서버의 주소

원격 MCP 서버의 주소(`url`)에 토큰을 넣지 마십시오. 로그 수준을 INFO 이하로 낮추면 HTTP 라이브러리가 요청마다 주소 전체를 기록하므로, 주소의 `?` 뒤에 넣은 토큰이 기록 파일에 남습니다. 토큰은 주소가 아니라 헤더(MCP 플러그인의 `[server.headers]`, 헤더 이름과 토큰을 담은 환경 변수의 이름)에 둡니다.
