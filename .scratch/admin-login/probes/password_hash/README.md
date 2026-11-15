# admin-login password_hash 프로브

`admin-login` 이 관리자 계정의 비밀번호를 어떤 방식으로 저장할지(해시 알고리즘과 라이브러리) 고르는 데 쓸 사실을 잰 프로브다. 후보는 둘이다. 표준 라이브러리 `hashlib.scrypt`(새 의존성 없음)와 `argon2-cffi` 의 Argon2id(새 의존성 하나). bcrypt, PBKDF2, `pwdlib` 같은 감싸는 라이브러리는 재지 않았다. 보는 것은 넷이다. argon2-cffi 와 딸려 오는 것의 판·라이선스·휠·타입 표지, 후보마다 세 동작(저장할 문자열 만들기, 저장된 문자열과 비밀번호 견주기, 저장된 문자열의 매개변수가 지금 설정보다 약해 다시 해시해야 하는지 판정)을 하는 작은 모듈이 pyright strict 와 타입 우회 검사를 우회 없이 지나는지, OWASP 권고 매개변수로 해시 한 번에 걸리는 시간과 메모리(그리고 `hashlib.scrypt` 의 기본 `maxmem`), 해시하는 동안 서버의 이벤트 루프가 막히는지. 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md` 의 "프로브와 근거"다.

결과는 2026-11-15 에 `run.py` 를 항목 셋 전부로 한 번 돌린 것이다(실행 토큰 `ca9b00`, 측정 363 회차, 측정 아님 30 회차, 종료 코드 1). 측정 아님 30 은 모두 이벤트 루프의 parallel 갈래다. 그 갈래의 양성 대조가 호스트 CPU 부하 91~100% 아래에서 기대대로 나오지 않아 읽지 않았다("이벤트 루프" 절). 같은 날의 다른 실행 넷은 범위를 적을 때만 함께 든다. `b285cf`(항목 셋 전부, 측정 375·측정 아님 15, 부하 79~100%), `281b88`(다시 돌리기를 확인하며 `--sections loop` 만, 측정 168·측정 아님 15, 돌리기 몇 분 전에 손으로 본 부하 100%), `eee7bb`(호스트만 2 회차씩, 부하 21~23%), `aaa95c`(리눅스만 2 회차씩, 부하 43→29%)다. `b285cf` 뒤에 `run.py` 에 `install` 을 더하고 이미지의 설치 층을 회차로 세던 줄을 뺐다(그 줄은 캐시된 층을 "이번 빌드에서 돌았다"고 적었다). `ca9b00` 뒤에는 `--sections` 로 고르기와 앞선 빌드의 이미지 지우기를 더했고 `281b88` 이 그 판으로 돈 것이다. 재는 스크립트(`bench.py`, `loop_block.py`, `peak_memory.py`, `scrypt_maxmem.py`, `exercise.py`, 후보 모듈 둘)는 다섯 실행 내내 그대로다(손으로 봤다, 파일의 고친 시각이 첫 실행 `eee7bb` 보다 앞선다). `run.py` 의 문턱은 첫 실행 전에 적은 뒤 고치지 않았다. 해시로 고정한 것은 아니고 손으로 지킨 것이다.

근거의 종류는 다섯이다. 프로브가 다시 낸다(`run.py` 가 표지를 보고 센 회차), 손으로 봤다(명령과 함께 적는다), 코드를 읽었다(파일과 줄), 원문을 내려받아 봤다(주소), 어림. 원문을 내려받지 않은 웹 요약은 쓰지 않았다.

## 요약

고를 때 쓸 한 줄씩이다. 근거와 갈래는 결과 절에 있다.

1. 패키지: argon2-cffi 25.1.0(MIT)은 argon2-cffi-bindings 26.2.0(MIT, Argon2 C 코드를 품은 컴파일된 휠) 하나를 끌어온다. 그 아래의 cffi 2.1.1 과 pycparser 3.0 은 저장소 잠금에 이미 있다. 잠금의 패키지는 84 에서 86 이 되고 이미 잠긴 판은 바뀌지 않았다. 손으로 봤다, 코드를 읽었다.
2. 휠: 윈도(`win_amd64`)와 리눅스 컨테이너(`manylinux_2_26_x86_64`) 모두 `--no-build`(소스를 짓지 않는다)로 깔렸다. 맞는 휠이 없는 플랫폼을 준 대조는 같은 명령이 거부됐다. `py.typed` 는 argon2-cffi 에만 있다. 프로브가 다시 낸다.
3. 타입: 두 후보의 모듈 모두 pyright strict 오류 0, 타입 우회 0 이다(호스트 플랫폼과 `--pythonplatform Linux`). 코드 줄 수는 `store_scrypt.py` 83, `store_argon2.py` 19 다. scrypt 쪽은 저장 문자열의 형식과 읽기를 모듈이 직접 정한다. 프로브가 다시 낸다.
4. 다시 해시 판정: argon2-cffi 의 `check_needs_rehash` 는 "약한가"가 아니라 "지금 설정과 다른가"다. 지금 설정보다 센 매개변수로 만든 문자열에도 참을 냈다. 프로브가 다시 낸다, 코드를 읽었다.
5. 시간(해시 한 번, OWASP 요약 줄의 매개변수): scrypt N=2^17,r=8,p=1 은 호스트 CPU 부하 21~23% 때 514~522ms(2 회차), 부하 65~100% 때 윈도 627~1034ms, 리눅스 컨테이너 639~2270ms 였다. Argon2id m=19456,t=2,p=1 은 부하 21~23% 때 28ms(2 회차), 부하 65~100% 때 윈도 32~65ms, 리눅스 컨테이너 38~76ms 였다. 측정 내내 다른 세션이 같은 PC 를 써서 조용한 때의 값은 2 회차뿐이다. 프로브가 다시 낸다.
6. `maxmem`: `hashlib.scrypt` 는 `maxmem` 을 주지 않으면 OWASP 의 scrypt 다섯 줄 가운데 앞의 셋(N=2^17, 2^16·p=2, 2^15·p=3)을 `memory limit exceeded` 로 거부했다. 한도는 32 MiB 다. N=2^17,r=8,p=1 이 지나는 가장 작은 값은 134220800 바이트(`128·r·(N+p+2)`)였다. 두 곳 모두. 프로브가 다시 낸다.
7. 메모리(해시 한 번이 더 쓴 상주 메모리): scrypt N=2^17 은 128.0 MiB, Argon2id m=19456 은 19.0 MiB 였다. 두 곳 모두 그 줄이 적은 값과 0.2 MiB 안에서 같았다. 프로브가 다시 낸다.
8. 이벤트 루프: 두 후보 모두 코루틴 안에서 바로 부르면 해시가 끝날 때까지 같은 루프의 다른 코루틴이 한 번도 돌지 않았고, `anyio.to_thread.run_sync` 로 넘기면 계속 돌았다(두 곳, 모든 실행). 해시 넷을 한꺼번에 스레드로 넘긴 갈래는 대조가 선 실행(윈도 둘)에서 한 번의 1.07~1.98 배 시간에 끝났고(한 회차만 3.42 배), 리눅스 컨테이너에서는 세 실행 모두 대조가 서지 않아 읽지 못했다(호스트 CPU 부하 100% 때다). 프로브가 다시 낸다.

## 파일

| 파일 | 무엇 |
|---|---|
| `requirements.in` | 재는 후보의 판 고정(`argon2-cffi==25.1.0`, 2026-11-15 의 PyPI 최신 안정판) |
| `store_scrypt.py`, `store_argon2.py` | 후보 모듈. 세 동작(`hash_password`, `verify_password`, `needs_rehash`)을 한다. 재는 대상이다 |
| `rows.py` | 재는 매개변수 줄(OWASP 사본의 줄 번호와 함께)과, 줄 하나를 후보 모듈에 묶는 도우미 |
| `exercise.py` | 후보 모듈의 세 동작 한 바퀴. 지금·약한·센 설정으로 만든 문자열, 깨진 입력, `hashlib.scrypt` 가 던지는 예외의 종류 |
| `bench.py` | 줄마다 해시 한 번과 견줌 한 번의 시간 |
| `scrypt_maxmem.py` | `hashlib.scrypt` 의 `maxmem`. 기본값에서의 거부, 지나는 가장 작은 값, 기본 한도의 자리, 인자의 위 끝 |
| `peak_memory.py` | 프로세스 하나에 줄 하나. 해시 한 번이 더 쓴 상주 메모리와 64 MiB 양성 대조 |
| `loop_block.py` | 해시하는 동안 같은 이벤트 루프의 틱 코루틴이 도는지. 스레드로 넘김, 바로 부름, 넷을 한꺼번에, 대조 둘 |
| `versions.py` | 깔린 패키지의 판, 라이선스 칸, 휠 태그, `py.typed`, 경로의 컴파일러 |
| `control_checks.py` | pyright strict 와 타입 우회 검사가 이 폴더를 실제로 본다는 양성 대조 |
| `friction_argon2_arg.py`, `friction_scrypt_arg.py`, `friction_argon2_low_level.py` | pyright 오류를 기대하는 대조군. 타입이 인자를 막는 자리 둘과 argon2-cffi 의 타입이 닿지 않는 자리 하나 |
| `reveal.py` | 후보의 호출이 돌려준 값을 pyright 가 무슨 타입으로 보는지 찍는다 |
| `Dockerfile`, `Dockerfile.dockerignore` | 리눅스 갈래의 이미지. `python:3.12-slim-trixie` 에 저장소 잠금과 후보를 `uv sync --no-build` 로 깐다 |
| `typecheck.py`, `pyrightconfig.json` | 이 폴더를 pyright strict 로 보는 도우미와 설정 |
| `run.py` | 측정 전체. 항목마다 무엇을 표지로 보는지와 문턱은 독스트링에 있다 |

## 다시 돌리기

저장소의 `pyproject.toml` 과 `uv.lock` 은 고치지 않는다. 후보는 저장소 밖 폴더의 사본에 더해 저장소의 잠금과 함께 푼다. 아래에서 `<tree>` 는 저장소 밖의 빈 폴더다. 저장소 루트에서 친다.

```sh
cp pyproject.toml uv.lock README.md <tree>/
uv add --project <tree> --no-sync -r .scratch/admin-login/probes/password_hash/requirements.in
uv sync --project <tree> --frozen --no-install-project --no-build
uv run --project <tree> --no-sync python .scratch/admin-login/probes/password_hash/run.py --tree <tree>
```

- 위 네 줄은 폴더 자리만 `<tree>` 로 바꿔 적은 것이다. 결과를 낸 실행 뒤에 빈 폴더로 앞의 세 줄을 그대로 다시 쳤고(`uv add` 가 86 개로 풀었고 `uv sync` 가 84 개를 1분 58초에 깔았다), 마지막 줄은 `--sections loop` 를 붙여 돌렸다(실행 `281b88`. `types` 항목은 그 폴더의 환경으로 전부 돌았고, 리눅스 parallel 회차 15 가 측정 아님이라 종료 코드는 1 이었다). 손으로 봤다, 2026-11-15. 리눅스 호스트에서는 돌려 보지 않았다.
- 필요한 것: 도는 Docker 데몬(리눅스 엔진, BuildKit), 네트워크(PyPI, Docker Hub, `ghcr.io/astral-sh/uv`), 이미지 `python:3.12-slim-trixie`(없으면 받는다), 경로의 `uv`. LLM 은 부르지 않는다. DB 도 쓰지 않는다.
- 하는 일: 리눅스 갈래의 이미지 `admin-login-pwhash-probe-linux` 를 짓고 그 컨테이너 안에서 호스트와 같은 스크립트를 돈다. 컨테이너는 이름이 `admin-login-pwhash-probe-<실행 토큰>-` 으로 시작하고 `--rm` 으로 뜨며, 끝에서 그 접두로 찾아 남은 것을 지운다. 네트워크와 볼륨은 만들지 않는다. 이미지는 남긴다. 파일이 바뀌어 새로 지으면 빌드 직전에 그 이름이 가리키던 이미지를 지운다. 모든 명령의 원본 출력은 `--work`(없으면 시스템 임시 폴더) 아래 `raw-<실행 토큰>.log` 에 남고, `install` 은 같은 폴더에 `fresh-<실행 토큰>-*` 폴더 둘을 남긴다.
- `--items types,host,linux` 로 항목을, `--sections versions,install,exercise,maxmem,bench,memory,loop` 로 `host` 와 `linux` 안에서 돌 것을 고른다. `--rounds`(요약 줄의 시간 회차, 기본 10), `--other-rounds`(나머지 줄, 기본 5), `--memory-rounds`(기본 2), `--loop-rounds`(기본 5), `--bare-python`(argon2-cffi 가 없는 환경의 파이썬, 기본은 저장소의 `.venv`). 측정이 아닌 회차가 하나라도 있으면 종료 코드가 1 이다.
- `uv run --with-requirements …` 로 후보를 얹는 길은 쓰지 않았다. 선례 `../pg_stack/README.md` 가 이 PC 에서 실패했다고 적고 있어 같은 길(사본 폴더)로 갔고, 이 프로브에서 다시 해 보지는 않았다.
- 항목 셋 전부가 한 번에 16~18분 걸렸다(실행 `ca9b00` 01:21:30~01:37:11, `b285cf` 00:57:41~01:15:05. 손으로 봤다, 원본 기록의 첫 줄과 끝 줄의 시각. 이미지와 빌드 캐시가 있고 호스트 CPU 부하가 65~100% 이던 때다).
- 타입 검사만: `uv run --project <tree> --no-sync python .scratch/admin-login/probes/password_hash/typecheck.py`(pyright 의 JSON 을 낸다. 기대한 오류 10 이 있어 종료 코드는 1 이다. 손으로 봤다). 린트: `uv run ruff check .scratch/admin-login/probes/password_hash`, `uv run ruff format --check .scratch/admin-login/probes/password_hash`.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-15 | |
| 호스트 | Windows 10 Home 10.0.19045, AMD Ryzen 7 3700X(코어 8, 논리 CPU 16) | 세션 환경 정보, 손으로 봤다(`Get-CimInstance Win32_Processor`) |
| Docker | 엔진 29.9.2(Docker Desktop, linux/x86_64), 커널 `6.18.58.1-microsoft-standard-WSL2`, CPU 16, 메모리 16.7GB, 저장 드라이버 overlay2. 컨테이너에 CPU·메모리 한도를 주지 않았다 | 손으로 봤다(`docker info`), 코드를 읽었다(`run.py` 의 `docker run` 인자) |
| 부하 | 측정 내내 다른 세션들이 같은 PC 와 같은 Docker 데몬을 썼다. 호스트 CPU 부하는 실행 `ca9b00` 의 호스트 시간 측정 시작 때 91%, 끝 때 65%, 리눅스 시간 측정 시작과 끝 때 100% 였다. `b285cf` 는 79%→94%, 100%→100%, `eee7bb` 는 21%→23%, `aaa95c` 는 43%→29% 였다. 측정 사이에 손으로 본 다섯 번은 97, 88, 63, 82, 58% 와 100% 다섯 번이었다 | 프로브가 찍은 값(`host_load`, 회차로 세지 않는다), 손으로 봤다(`(Get-CimInstance Win32_Processor).LoadPercentage`) |
| 파이썬 | 호스트 3.12.10, 리눅스 이미지 3.12.16 | 프로브(`versions.py`) |
| OpenSSL(`hashlib.scrypt` 의 구현) | 호스트 `OpenSSL 3.0.16 11 Feb 2025`, 리눅스 이미지 `OpenSSL 3.5.7 9 Jun 2026` | 프로브(`versions.py` 가 찍는 `ssl.OPENSSL_VERSION`). scrypt 의 거부 글이 OpenSSL 의 것(`[digital envelope routines]`)이다 |
| Argon2 | 알고리즘 판 번호 19(`$argon2id$v=19$`), 품은 C 코드의 커밋 `f57e61e` | 프로브(`versions.py`), 코드를 읽었다(깔린 `argon2_cffi_bindings-26.2.0.dist-info/METADATA` 54 줄) |
| uv | 호스트 0.10.8 | 손으로 봤다(`uv --version`) |
| 저장소 잠금의 도구 | pyright 1.1.414, anyio 4.15.1 | 프로브(`versions.py`) |
| 리눅스 바탕 | `python:3.12-slim-trixie` = `python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`(`.scratch/release-image/spec.md` 가 serve 의 바탕으로 고른 것) | 프로브(`docker image inspect`) |
| 이벤트 루프 | 호스트 `ProactorEventLoop`, 리눅스 `_UnixSelectorEventLoop`. `anyio.run` 이 띄운 것이다. AnyIO 기본 스레드 한도 40, `sys.getswitchinterval()` 0.005 | 프로브(`loop_block.py` 의 첫 줄) |

## 결과

### OWASP 가 권하는 매개변수

OWASP Password Storage Cheat Sheet 의 사본(`https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html`, 2026-11-14 에 내려받아 글만 뽑은 `pwstore.html.txt`)에서 읽었다. 원문을 내려받아 봤다. 줄 번호는 그 사본의 것이다. 사본은 세션 스크래치패드에 있어 저장소에 없다.

- 210 줄: "Use Argon2id with a minimum configuration of 19 MiB of memory, an iteration count of 2, and 1 degree of parallelism."
- 211 줄: Argon2id 를 쓸 수 없으면 scrypt 를 CPU/메모리 비용 2^17, 블록 크기 8(1024 바이트), 병렬 1 이상으로.
- 253 줄: "As a general rule, calculating a hash should take less than one second." 같은 줄이 맞는 값은 그 서버에서 재서 정하라고 적는다.
- 267~271 줄(Argon2id, 같은 수준의 방어이고 CPU 와 RAM 의 맞바꿈이라고 272 줄이 적는다): m=47104,t=1,p=1 / m=19456,t=2,p=1 / m=12288,t=3,p=1 / m=9216,t=4,p=1 / m=7168,t=5,p=1.
- 276~280 줄(scrypt): N=2^17,r=8,p=1 / N=2^16,r=8,p=2 / N=2^15,r=8,p=3 / N=2^14,r=8,p=5 / N=2^13,r=8,p=10.

아래에서 "요약 줄"은 210 줄과 211 줄이 든 것(Argon2id m=19456,t=2,p=1 과 scrypt N=2^17,r=8,p=1)이다. 열한 번째 줄 m=65536,t=3,p=4 는 OWASP 의 줄이 아니라 argon2-cffi 25.1.0 의 `PasswordHasher()` 기본값이다(코드를 읽었다, 깔린 `argon2/_password_hasher.py` 20~26 줄과 `argon2/profiles.py` 49~57 줄의 `RFC_9106_LOW_MEMORY`). 견주려고 함께 쟀다.

### 후보별 표

실행 `ca9b00` 의 값이다. 시간은 최소 / 중앙 / 최대이고 괄호는 그때의 호스트 CPU 부하다. 프로브가 다시 낸다.

| | `hashlib.scrypt` | `argon2-cffi` Argon2id |
|---|---|---|
| 판 | 표준 라이브러리. 호스트 파이썬 3.12.10(OpenSSL 3.0.16), 리눅스 이미지 3.12.16(OpenSSL 3.5.7) | argon2-cffi 25.1.0 + argon2-cffi-bindings 26.2.0 |
| 라이선스(메타데이터) | 파이썬과 함께 온다(따로 읽지 않았다) | 둘 다 MIT. 품은 Argon2 C 코드는 CC0 |
| 잠금에 새로 드는 패키지 | 0 | 2 |
| pyright strict 오류 | 0 | 0(argon2-cffi 가 없는 환경에서는 19) |
| 타입 우회 | 0 | 0 |
| 모듈의 코드 줄 수 | 83 | 19 |
| 요약 줄의 매개변수 | N=2^17,r=8,p=1(사본 211·276 줄) | m=19456,t=2,p=1(사본 210·268 줄) |
| 해시 한 번, 윈도 호스트(ms) | 626.5 / 717.3 / 804.9(부하 91→65%, 10 회차) | 31.7 / 36.6 / 53.8(같은 때, 10 회차) |
| 해시 한 번, 리눅스 컨테이너(ms) | 639.4 / 754.9 / 2270.3(부하 100%, 10 회차) | 38.0 / 49.7 / 68.5(같은 때, 10 회차) |
| 해시 한 번이 더 쓴 상주 메모리 | 128.0 MiB(윈도), 127.9 MiB(리눅스) | 19.0 MiB(윈도), 18.9 MiB(리눅스) |
| 기본 `maxmem` | 요약 줄을 거부한다. `maxmem` 을 134220800 바이트 이상으로 줘야 지난다 | 해당 없음 |
| 바로 부르면 이벤트 루프가 | 막힌다(두 곳, 5/5) | 막힌다(두 곳, 5/5) |
| `anyio.to_thread.run_sync` 로 넘기면 | 돈다(두 곳, 5/5) | 돈다(윈도 5/5. 리눅스 3/5 이고 2 는 해시가 짧아 가르지 못했다. 같은 호출 길의 긴 판은 두 곳 5/5) |

### 후보의 판과 라이선스, 휠

판은 2026-11-15 에 `uv pip compile` 이 고른 PyPI 최신 안정판이다(손으로 봤다). 올라온 날은 argon2-cffi 25.1.0 이 2025-06-03, argon2-cffi-bindings 26.2.0 이 2026-11-13(이 측정의 이틀 전)이다(코드를 읽었다, 사본 폴더의 `uv.lock` 의 `upload-time`). 라이선스와 휠 태그와 타입 표지는 깔린 배포판의 메타데이터에서 `versions.py` 가 읽었다(프로브가 낸다. 회차로 세지 않는 출력이다).

| 패키지 | 판 | 라이선스(메타데이터) | `py.typed` | 깔린 휠의 태그 | 저장소 잠금에 |
|---|---|---|---|---|---|
| argon2-cffi | 25.1.0 | MIT | 있음 | `py3-none-any` | 없다(새로 든다) |
| argon2-cffi-bindings | 26.2.0 | MIT | 없음 | 윈도 `cp310-abi3-win_amd64`, 리눅스 `cp310-abi3-manylinux_2_26_x86_64`(같은 휠에 `manylinux_2_28_x86_64`) | 없다(새로 든다) |
| cffi | 2.1.1 | MIT-0 | 없음 | 윈도 `cp312-cp312-win_amd64`, 리눅스 `cp312-cp312-manylinux_2_17_x86_64` | 이미 있다 |
| pycparser | 3.0 | BSD-3-Clause | 없음 | `py3-none-any` | 이미 있다 |

- 끌어오는 것. argon2-cffi 는 argon2-cffi-bindings 하나를, 그것은 cffi 를(파이썬 3.14 미만에서 `cffi>=1.0.1`), cffi 는 pycparser 를 요구한다(프로브가 낸다, `versions.py` 의 `requires`). 저장소 잠금은 cffi 2.1.1 과 pycparser 3.0 을 이미 갖고 있다. cryptography 50.0.1 이 cffi 를 요구한다(코드를 읽었다, 저장소 `uv.lock` 130·221~226·748 줄). 후보 한 줄을 잠금의 사본에 더하면 패키지가 84 에서 86 이 되고, `git diff --no-index --stat` 가 45 줄 추가에 삭제 0 이라 이미 잠긴 판은 하나도 바뀌지 않았다(손으로 봤다).
- argon2-cffi-bindings 는 Argon2 의 C 코드를 품고 CFFI 의 API 모드로 컴파일한 것이다. 소스에서 지으려면 C 컴파일러와 CMake 가 있어야 한다고 적는다. 품은 C 코드는 CC0 이다(코드를 읽었다, 깔린 `argon2_cffi_bindings-26.2.0.dist-info/METADATA` 54·68·72·139~147 줄). 휠의 `licenses/` 에는 MIT 의 `LICENSE` 하나만 있다(프로브가 낸다).
- 올라와 있는 argon2-cffi-bindings 26.2.0 의 휠은 `cp310-abi3` 로 macOS arm64, manylinux_2_26 의 x86_64·aarch64, manylinux_2_34 의 riscv64, musllinux_1_2 의 x86_64·aarch64·riscv64, win32, win_amd64, win_arm64 이고, 같은 플랫폼들에 `cp315-abi3.abi3t` 가 하나씩 더 있다(코드를 읽었다, 사본 폴더의 `uv.lock` 133~153 줄). 이 프로브가 실제로 깐 것은 win_amd64 와 manylinux x86_64 둘뿐이다.
- 컴파일러 없이 깔리는가. 두 곳에서 빈 폴더에 `uv pip install --target … --no-build argon2-cffi==25.1.0 argon2-cffi-bindings==26.2.0` 을 돌렸다. `--no-build` 는 소스 배포판을 짓지 않게 하는 인자다. 두 곳 모두 `+ argon2-cffi-bindings==26.2.0` 줄과 함께 깔렸다. 양성 대조는 같은 명령에 맞는 휠이 없는 플랫폼(`--python-platform x86_64-manylinux_2_17`)을 준 것이고, 두 곳 모두 `argon2-cffi-bindings==26.2.0 has no usable wheels` 와 `building from source is disabled` 로 거부됐다. 그래서 깔린 것은 소스를 지은 것이 아니라 휠이다(프로브가 다시 낸다, `run.py` 의 `install`). 리눅스 이미지에는 경로에 `cc`·`gcc`·`clang` 이 없었다(프로브가 낸다). 윈도 호스트의 경로에도 `cl`·`gcc`·`clang` 이 없었으나, 경로 밖에 깔린 Visual Studio 가 있는지는 보지 않았으므로 윈도의 근거는 `--no-build` 쪽이다.
- 저장소 잠금 전체를 `uv sync --frozen --no-install-project --no-build` 로 까는 것도 두 곳에서 됐다. 윈도는 빈 폴더 둘에 84 개(2분 2초, 1분 58초. 손으로 봤다), 리눅스는 이미지 빌드의 설치 층에서 82 개가 깔렸다(실행 `aaa95c` 의 원본 기록에 `Installed 82 packages` 와 `+ argon2-cffi-bindings==26.2.0`. 손으로 봤다). 그 뒤의 실행들에서 그 층은 캐시였고 프로브가 그렇게 적는다.
- 판을 못 박지 않고 `--python-platform x86_64-manylinux_2_17 --no-build argon2-cffi==25.1.0` 만 주면 거부되지 않고 argon2-cffi-bindings 21.2.0 으로 물러서 깔렸다(손으로 봤다, 2026-11-15). 26.2.0 의 리눅스 휠은 glibc 2.26 이상을 요구한다는 뜻이다. `--frozen` 으로 26.2.0 을 못 박은 잠금은 그보다 낮은 glibc 에서 물러설 데가 없다(어림. 그런 바탕에서 돌려 보지 않았다).
- 새로 풀면 pycparser 는 3.12 로 풀렸다(프로브의 `install` 출력). 저장소 잠금의 3.0 은 그대로다.

### 타입

`types` 항목이다. 프로브가 다시 낸다. 분석했다는 표지는 `filesAnalyzed 16/16` 과 양성 대조 `control_checks.py` 의 `reportMissingParameterType` 이고, 타입 우회 검사가 듣는다는 표지는 같은 파일에서 `Any`·`cast`·억제 주석이 잡힌 것이다.

| 파일 | pyright strict(호스트 플랫폼) | pyright strict(`--pythonplatform Linux`) | 타입 우회 | argon2-cffi 가 없는 환경 |
|---|---|---|---|---|
| `store_scrypt.py` | 오류 0 | 오류 0 | 0 | 오류 0 |
| `store_argon2.py` | 오류 0 | 오류 0 | 0 | 오류 19(`reportMissingImports`, `reportUnknown…`) |
| 나머지 도우미 열 | 오류 0 | 오류 0 | 0 | |

- argon2-cffi 가 없는 환경은 저장소의 `.venv` 다. 그 환경을 실제로 봤다는 표지가 `reportMissingImports` 다. `store_argon2.py` 의 오류 0 은 argon2-cffi 가 실어 온 타입(`py.typed`)에 기댄 것이고, 따로 스텁 패키지는 없었다.
- `reveal.py` 를 pyright 가 푼 것. `hashlib.scrypt(…)` 는 `bytes`, `PasswordHasher.hash` 는 `str`, `PasswordHasher.verify` 는 `Literal[True]`, `check_needs_rehash` 는 `bool`, `extract_parameters` 는 `Parameters`, `PasswordHasher.memory_cost` 는 `int` 다. `Any` 로 드러난 값은 없었다.
- 타입이 막는 자리(대조군이 그 오류를 다시 낸다). `PasswordHasher(time_cost="2")` 와 `hashlib.scrypt("text", …)` 는 `reportArgumentType` 이다.
- 타입이 닿지 않는 자리. `argon2.low_level` 은 타입 표지가 없는 `_argon2_cffi_bindings` 에서 값을 가져온다(코드를 읽었다, 깔린 `argon2/low_level.py` 17·31·47~49 줄). `low_level.ARGON2_VERSION` 과 `Type.ID.value` 는 `Unknown` 이고 그대로 읽으면 strict 에서 `reportUnknownMemberType` 이다(`friction_argon2_low_level.py` 가 오류 4 를 낸다). `low_level.hash_secret` 같은 함수의 서명은 타입이 있다. `store_argon2.py` 는 `PasswordHasher` 만 써서 이 자리를 지나지 않는다.

### 세 동작

`exercise` 다. 두 곳에서 같았다. 프로브가 다시 낸다. 표지는 지금·약한·센 설정으로 만든 문자열 셋이 저마다 제 매개변수의 머리를 갖고 맞는 비밀번호만 통과하는 것이다.

| | `store_scrypt.py` | `store_argon2.py` |
|---|---|---|
| 저장 문자열 | `$scrypt$ln=17,r=8,p=1$<소금>$<키>`, 88 자. 형식은 이 모듈이 정했다(표준 라이브러리는 바이트만 준다) | `$argon2id$v=19$m=19456,t=2,p=1$<소금>$<키>`, 97 자. 라이브러리가 만든다 |
| 같은 비밀번호를 두 번 해시 | 문자열이 다르다(소금 16 바이트) | 문자열이 다르다(소금 16 바이트) |
| 다시 해시 판정: 지금 설정으로 만든 것 | 거짓 | 거짓 |
| 약한 설정으로 만든 것 | 참(ln=14) | 참(m=7168,t=1) |
| 센 설정으로 만든 것 | 거짓(ln=18) | 참(m=47104,t=3) |
| 깨진 저장 문자열 | 아홉 가지 모두 견줌이 거짓, 예외 없음 | 여덟 가지 가운데 ASCII 가 아닌 글자가 든 문자열에서 `verify` 가 `UnicodeEncodeError` 를 던졌다 |

- 센 설정의 차이. argon2-cffi 의 `check_needs_rehash` 는 `self._parameters != extract_parameters(hash)`, 곧 같지 않음이다(코드를 읽었다, 깔린 `argon2/_password_hasher.py` 262~287 줄). `store_scrypt.py` 의 판정은 이 프로브가 "어느 하나라도 지금보다 작으면"으로 적은 것이라 라이브러리의 성질이 아니다.
- 새는 예외. `verify` 는 저장 문자열을 `ascii` 로 바꾸는 줄(같은 파일 252 줄)이 `InvalidHashError` 를 잡는 자리 앞에 있다. `store_argon2.py` 는 `VerificationError` 와 `InvalidHashError` 만 잡게 적었다. `UnicodeEncodeError` 와 `InvalidHashError` 는 둘 다 `ValueError` 의 하위다(코드를 읽었다, 깔린 `argon2/exceptions.py` 40 줄. 앞의 것은 파이썬의 예외 계층이고 이 프로브에서 따로 확인하지 않았다).
- `hashlib.scrypt` 가 던지는 예외의 종류는 매개변수에 따라 셋이었다. `n=3` 과 `r=0` 은 `ValueError`, `n=2^100` 은 `TypeError`, `maxmem` 이 2^31 이상이면 윈도에서 `OverflowError`, 리눅스에서 `ValueError`(`maxmem must be positive and smaller than 2147483647`)였다. 저장 문자열에서 읽은 매개변수를 그대로 넣는 견줌은 이 셋을 다 잡아야 예외가 새지 않았다(`store_scrypt.py` 의 첫 판은 `TypeError` 를 놓쳤고 손으로 본 뒤 더했다).

### 시간

`bench` 다. 줄마다 해시 한 번(`hash_password`)과 견줌 한 번(`verify_password`, 맞는 비밀번호)을 `time.perf_counter` 로 쟀고 줄들을 번갈아 돌았다. 회차의 표지는 만든 문자열의 머리가 그 줄의 매개변수이고 맞는 비밀번호만 통과하는 것이다. 단위는 ms, 값은 최소 / 중앙 / 최대다. 프로브가 다시 낸다.

요약 줄의 해시 한 번, 실행마다.

| 실행(호스트 CPU 부하) | scrypt N=2^17,r=8,p=1 윈도 | scrypt 리눅스 컨테이너 | Argon2id m=19456,t=2,p=1 윈도 | Argon2id 리눅스 컨테이너 |
|---|---|---|---|---|
| `ca9b00`(윈도 91→65%, 리눅스 100%), 10 회차 | 626.5 / 717.3 / 804.9 | 639.4 / 754.9 / 2270.3 | 31.7 / 36.6 / 53.8 | 38.0 / 49.7 / 68.5 |
| `b285cf`(윈도 79→94%, 리눅스 100%), 10 회차 | 684.8 / 846.0 / 1033.8 | 649.9 / 791.6 / 991.6 | 37.3 / 44.8 / 65.4 | 37.7 / 47.2 / 75.5 |
| `eee7bb`(윈도 21→23%), 2 회차 | 514.3, 521.5 | | 28.2, 28.5 | |
| `aaa95c`(리눅스 43→29%), 2 회차 | | 472.7, 998.5 | | 26.6, 73.2 |

모든 줄, 실행 `ca9b00`. 견줌은 해시와 같은 계산을 한 번 하므로 시간이 비슷했다.

| 줄(사본의 줄) | 윈도 해시 | 윈도 견줌 | 리눅스 해시 | 리눅스 견줌 | 회차 |
|---|---|---|---|---|---|
| scrypt N=2^17,r=8,p=1(211·276) | 626.5 / 717.3 / 804.9 | 570.9 / 745.5 / 814.5 | 639.4 / 754.9 / 2270.3 | 684.5 / 740.5 / 1146.2 | 10 |
| scrypt N=2^16,r=8,p=2(277) | 575.1 / 645.5 / 728.2 | 567.5 / 647.3 / 675.2 | 576.8 / 622.9 / 876.4 | 545.8 / 599.1 / 774.8 | 5 |
| scrypt N=2^15,r=8,p=3(278) | 421.0 / 477.2 / 743.2 | 427.1 / 462.2 / 552.6 | 431.5 / 469.0 / 724.7 | 408.8 / 491.6 / 875.9 | 5 |
| scrypt N=2^14,r=8,p=5(279) | 356.3 / 389.1 / 421.7 | 328.9 / 388.3 / 470.7 | 311.6 / 387.4 / 533.9 | 341.2 / 374.8 / 429.3 | 5 |
| scrypt N=2^13,r=8,p=10(280) | 356.9 / 410.9 / 479.8 | 341.1 / 409.6 / 487.1 | 296.0 / 327.9 / 412.9 | 312.5 / 359.3 / 393.1 | 5 |
| Argon2id m=19456,t=2,p=1(210·268) | 31.7 / 36.6 / 53.8 | 33.0 / 37.8 / 57.2 | 38.0 / 49.7 / 68.5 | 37.8 / 47.6 / 54.2 | 10 |
| Argon2id m=47104,t=1,p=1(267) | 51.0 / 55.1 / 74.5 | 51.9 / 54.6 / 77.5 | 104.5 / 130.8 / 146.0 | 88.8 / 120.2 / 130.2 | 5 |
| Argon2id m=12288,t=3,p=1(269) | 30.7 / 31.3 / 55.5 | 26.4 / 33.6 / 44.0 | 35.5 / 45.6 / 59.2 | 36.0 / 49.8 / 52.0 | 5 |
| Argon2id m=9216,t=4,p=1(270) | 25.4 / 28.8 / 39.4 | 28.3 / 31.7 / 37.1 | 38.6 / 43.7 / 53.6 | 29.4 / 40.4 / 50.6 | 5 |
| Argon2id m=7168,t=5,p=1(271) | 23.7 / 28.9 / 35.7 | 24.3 / 33.5 / 38.1 | 36.2 / 41.1 / 44.5 | 36.5 / 38.4 / 42.7 | 5 |
| Argon2id m=65536,t=3,p=4(argon2-cffi 기본값) | 70.1 / 78.2 / 93.1 | 67.3 / 77.9 / 117.0 | 135.1 / 156.5 / 370.1 | 143.2 / 176.1 / 289.9 | 5 |

- 읽는 법. 부하가 실행마다 달랐고 다른 세션의 것이라 고를 수 없었다. 조용한 때에 가장 가까운 값은 `eee7bb` 의 2 회차뿐이다. 부하가 큰 때의 값은 "바쁜 서버에서 얼마나 늘어나는가"의 한 예로 읽고, 줄 사이의 비는 같은 실행 안에서만 견준다.
- 요약 줄끼리의 비는 같은 실행의 중앙값으로 윈도 18.9~19.6 배, 리눅스 15.2~16.8 배였고(scrypt 가 길다), 부하가 낮던 `eee7bb` 의 2 회차로는 18.3 배다(위 표의 값으로 한 셈).
- scrypt 요약 줄의 해시가 1 초를 넘긴 회차는 `b285cf` 윈도의 10 가운데 1(1033.8ms), `ca9b00` 리눅스의 10 가운데 2(2270.3ms, 1345.6ms)였고 나머지 두 자리(`ca9b00` 윈도, `b285cf` 리눅스)에는 없었다. 같은 두 실행에서 Argon2id 요약 줄의 가장 긴 해시는 75.5ms 였다.
- 리눅스 컨테이너의 Argon2id m=47104 와 m=65536 은 윈도의 두 배쯤이었고 작은 줄들은 그만큼 벌어지지 않았다. 부하가 달랐던 때라(윈도 91→65%, 리눅스 100%) 플랫폼 차이인지 부하 차이인지 가르지 못했다.

### `hashlib.scrypt` 의 `maxmem`

`maxmem` 은 scrypt 가 쓸 메모리의 위 끝을 바이트로 주는 인자다. 파이썬 문서는 서명을 `maxmem=0` 으로, 뜻을 "maxmem limits memory (OpenSSL 1.1.0 defaults to 32 MiB)"로 적는다(원문을 내려받아 봤다, `https://docs.python.org/3/library/hashlib.html` 의 2026-11-14 사본 271·278 줄). 아래는 두 곳에서 같았다. 프로브가 다시 낸다.

| OWASP 줄 | `128·r·(N+p+2)` 바이트 | `maxmem` 을 주지 않으면 |
|---|---|---|
| N=2^17,r=8,p=1 | 134220800 | 거부 |
| N=2^16,r=8,p=2 | 67112960 | 거부 |
| N=2^15,r=8,p=3 | 33559552 | 거부 |
| N=2^14,r=8,p=5 | 16784384 | 통과 |
| N=2^13,r=8,p=10 | 8400896 | 통과 |

- 거부의 글은 `ValueError: [digital envelope routines] memory limit exceeded` 다. 그 거부가 한도 탓이라는 표지는 같은 매개변수가 식의 값에서 통과하고 그보다 1 작은 값에서 같은 글로 거부되는 것이다(줄마다 봤다). 대조 N=2^14,r=8,p=1 은 기본값에서 통과했다.
- N=2^17,r=8,p=1 이 지나는 가장 작은 `maxmem` 을 이분법으로 찾으면 134220800 이고 식의 값과 같았다. 128 MiB(134217728)보다 3072 바이트 크다.
- 기본 한도의 자리. N=2,r=52428,p=1(식의 값 33553920)은 기본값에서 통과하고 r=52429(33554560)는 거부됐다. 32 MiB 는 33554432 다.
- 인자의 위 끝. `maxmem=2^31-1` 은 받고 2^31 은 윈도에서 `OverflowError`, 리눅스에서 `ValueError: maxmem must be positive and smaller than 2147483647` 이다. r=8 에서 식의 값이 이 끝을 넘는 것은 N=2^21 부터다(셈).
- `store_scrypt.py` 는 매개변수마다 식의 값을 `maxmem` 으로 준다.

### 메모리

`memory` 다. 줄마다 새 프로세스에서, 가져오기와 아주 작은 해시 한 번을 먼저 끝낸 뒤의 최고 상주 메모리와, 그 줄의 해시 한 번과 견줌 두 번을 차례로 한 뒤의 최고 상주 메모리의 차다. 윈도는 `GetProcessMemoryInfo` 의 `PeakWorkingSetSize`, 리눅스는 `/proc/self/status` 의 `VmHWM` 이다. 양성 대조는 64 MiB 를 잡아 쪽마다 쓴 프로세스이고 두 곳에서 64.00~64.01 MiB 로 읽혔다(그 읽기가 쓴 메모리를 본다는 표지). 실행 `ca9b00`, 줄마다 2 회차. 프로브가 다시 낸다.

| 줄 | 그 줄이 적은 값(MiB) | 윈도(MiB) | 리눅스 컨테이너(MiB) |
|---|---|---|---|
| scrypt N=2^17,r=8,p=1 | 128 | 128.0 | 127.9 |
| scrypt N=2^16,r=8,p=2 | 64 | 64.0 | 63.9 |
| scrypt N=2^15,r=8,p=3 | 32 | 32.0 | 31.9~32.0 |
| scrypt N=2^14,r=8,p=5 | 16 | 16.0 | 15.9 |
| scrypt N=2^13,r=8,p=10 | 8 | 8.0 | 7.8~7.9 |
| Argon2id m=19456,t=2,p=1 | 19 | 19.0 | 18.9 |
| Argon2id m=47104,t=1,p=1 | 46 | 46.0 | 45.9 |
| Argon2id m=12288,t=3,p=1 | 12 | 12.0 | 11.9 |
| Argon2id m=9216,t=4,p=1 | 9 | 9.0 | 8.9 |
| Argon2id m=7168,t=5,p=1 | 7 | 7.0 | 6.7~6.9 |
| Argon2id m=65536,t=3,p=4 | 64 | 64.1 | 63.6~63.8 |

- scrypt 의 p 를 2~10 으로 올린 줄도 더 쓴 메모리는 N 이 정한 값이었다(p 배가 아니었다).
- 한꺼번에 도는 해시의 수만큼 이 값이 겹친다고 보면, AnyIO 기본 스레드 한도 40(프로브가 찍은 값)에서 scrypt 요약 줄은 5120 MiB, Argon2id 요약 줄은 760 MiB 다. 곱셈으로 한 어림이고, 그만큼을 한꺼번에 돌려 재지는 않았다.

### 이벤트 루프

`loop` 다. 틱 코루틴 하나가 `anyio.sleep(0)` 으로 루프에 차례를 넘기며 돌 때마다 시각을 적고, 작업 하나가 도는 동안의 틱 수와 틱 사이의 가장 긴 틈을 작업 시간과 견준다. 회차의 표지는 작업의 결과가 진짜인 것(해시면 그 줄의 문자열이 맞는 비밀번호만 통과), 작업 앞 0.3초에 틱 100 개 이상, 작업 뒤에 틱 1 개 이상이다. 갈래와 문턱은 `run.py` 의 독스트링에 있다. 가장 긴 틈이 작업 시간의 0.8 배 이상이면 "막힌다", 0.2 배 이하이고 틱이 100 개 이상이면 "돈다", 그 사이는 "가르지 못했다"다. 문턱은 코드의 상수이고 해시로 고정한 사전 등록이 아니다. 그래서 잰 값을 함께 적는다. 프로브가 다시 낸다.

해석과 대조.

- "스레드로 넘긴 해시 동안 틱이 이어지면 해시가 GIL 을 놓는다"로 읽으려면, 이 틱이 GIL 을 쥔 스레드를 알아봐야 한다. 대조 `sum(range(10_000_000))`(한 번의 C 호출 안에서 GIL 을 쥔다고 보고 골랐다)을 같은 길로 스레드에 넘기면 모든 실행의 모든 회차에서 "막힌다"였다(가장 긴 틈이 작업 시간과 같다). GIL 을 놓는 대조 `time.sleep(0.3)` 은 모든 회차에서 "돈다"였다. 해시의 thread 회차는 이 둘이 그 실행의 모든 회차에서 기대대로일 때만 측정으로 센다.
- 다른 해석 "해시가 짧아서 틈이 안 보였다"는 문턱이 작업 시간에 견준 비라 걸러진다. Argon2id 요약 줄은 수십 ms 라 잡음 하나에 판정이 흔들릴 수 있어, 같은 호출 길을 길게 한 판(m=262144,t=4,p=1. 권고 줄이 아니다)을 함께 봤다.
- "바로 부르면 막힌다"의 표지는 가장 긴 틈이 작업 시간과 같은 것이다(틱이 작업 동안 0 개).

thread 와 direct 갈래. 값은 판정과, 괄호 안에 작업 시간의 범위와 가장 긴 틈의 범위(ms)다. 실행 `ca9b00`, 갈래마다 5 회차.

| 작업 | 윈도 thread | 윈도 direct | 리눅스 thread | 리눅스 direct |
|---|---|---|---|---|
| scrypt N=2^17,r=8,p=1 | 돈다 5(작업 553~1337, 틈 0.5~12.2) | 막힌다 5(작업 584~801, 틈 584~801) | 돈다 5(작업 710~1051, 틈 9.8~11.9) | 막힌다 5(작업 821~1593, 틈 821~1594) |
| Argon2id m=19456,t=2,p=1 | 돈다 5(작업 38~43, 틈 0.1~0.5) | 막힌다 5(작업 36~50, 틈 36~50) | 돈다 3, 가르지 못했다 2(작업 25~84, 틈 0.3~11.5) | 막힌다 5(작업 23~99, 틈 23~99) |
| Argon2id m=262144,t=4,p=1(긴 판) | 돈다 5(작업 881~1218, 틈 0.9~13.9) | 막힌다 5(작업 951~1299, 틈 951~1299) | 돈다 5(작업 1687~4054, 틈 11.2~30.1) | 막힌다 5(작업 1644~3863, 틈 1645~3863) |
| 대조 `sum(range)`(GIL 을 쥔다) | 막힌다 5(작업 152~306, 틈 151~306) | | 막힌다 5(작업 208~786, 틈 207~786) | |
| 대조 `time.sleep`(GIL 을 놓는다) | 돈다 5(작업 301~321, 틈 0.6~11.2) | | 돈다 5(작업 301~307, 틈 5.3~11.5) | |

- 다른 실행에서도 같았다. `b285cf` 는 윈도 thread 가 셋 다 돈다 5, 리눅스 thread 가 scrypt 돈다 5, Argon2id 요약 줄 돈다 4·가르지 못했다 1, 긴 판 돈다 5 였다. `281b88` 은 윈도 thread 가 scrypt 돈다 5, Argon2id 요약 줄 돈다 4·가르지 못했다 1, 긴 판 돈다 5, 리눅스 thread 가 scrypt 돈다 5, Argon2id 요약 줄 돈다 3·가르지 못했다 2, 긴 판 돈다 5 였다. direct 는 세 실행의 두 곳 모두 막힌다 5 였다.
- "가르지 못했다"가 난 여섯 회차는 모두 Argon2id 요약 줄이고, 작업이 45~65ms 인데 가장 긴 틈이 10~28ms 였다. 리눅스의 다섯 회차는 아무것도 시키지 않은 작업 앞 0.3초의 가장 긴 틈도 10~12ms 였고(부하 100% 때다), 윈도의 한 회차는 틈이 28.3ms(작업 앞은 1.2ms)였다. thread 갈래에서 막힌 회차(틈이 작업 시간과 같다)는 어느 실행에도 없었다.
- 서버의 루프도 같은 종류다. 선례 `../pg_stack/README.md` 가 `uvicorn.run` 의 루프를 윈도 `ProactorEventLoop`, 리눅스 `_UnixSelectorEventLoop` 로 쟀다. 이 프로브는 `anyio.run` 으로 띄웠고 uvicorn 의 요청 길에서는 재지 않았다.

parallel 갈래. 같은 작업 넷을 `anyio.to_thread.run_sync` 넷으로 한꺼번에 넘겨, 걸린 시간을 같은 작업의 thread 갈래 중앙값으로 나눈다. 2.0 배 이하면 "함께 돈다", 3.2 배 이상이면 "차례로 돈다"다. 해시의 회차는 대조가 그 실행의 모든 회차에서 기대대로일 때만 측정이다(`sum(range)` 가 "차례로 돈다", `time.sleep` 이 "함께 돈다").

| 실행 | 자리 | 대조 `sum(range)` 의 배수 | 대조가 섰나 | scrypt 요약 줄 | Argon2id 요약 줄 | Argon2id 긴 판 |
|---|---|---|---|---|---|---|
| `b285cf` | 윈도 | 3.63~4.38 | 섰다 | 함께 돈다 5(1.09~1.98) | 함께 돈다 4, 차례로 돈다 1(1.24~3.42) | 함께 돈다 5(1.21~1.86) |
| `281b88` | 윈도 | 3.51~4.19 | 섰다 | 함께 돈다 5(1.11~1.26) | 함께 돈다 5(1.07~1.43) | 함께 돈다 5(1.25~1.70) |
| `ca9b00` | 윈도 | 2.70~4.78 | 서지 않았다 | 측정 아님(1.05~1.38) | 측정 아님(1.08~1.49) | 측정 아님(1.25~1.37) |
| `b285cf` | 리눅스 | 2.63~3.58 | 서지 않았다 | 측정 아님(1.80~5.25) | 측정 아님(0.84~1.67) | 측정 아님(1.38~2.08) |
| `ca9b00` | 리눅스 | 1.72~3.18 | 서지 않았다 | 측정 아님(1.13~4.11) | 측정 아님(1.24~4.25) | 측정 아님(1.61~2.69) |
| `281b88` | 리눅스 | 3.05~4.38 | 서지 않았다 | 측정 아님(1.24~5.12) | 측정 아님(1.21~4.35) | 측정 아님(1.11~9.10) |

- 대조가 서지 않은 실행에서는 GIL 을 쥔 넷이 네 배가 아니라 1.72~3.18 배로 읽히기도 했다. 그 실행(`ca9b00` 리눅스)에서 나누는 값인 `sum(range)` 한 번의 시간이 208~786ms 로 세 배 넘게 흔들렸다(배수가 낮게 읽힌 것이 그래서라고 보는 것은 어림이다). 그런 실행의 해시 회차는 읽지 않았고 괄호의 배수는 참고로만 적는다.
- 윈도에서 대조가 선 두 실행으로는 해시 넷이 한 번의 1.07~1.98 배 시간에 끝났다(Argon2id 요약 줄의 한 회차만 3.42 배. 작업이 수십 ms 인 줄이다).
- 리눅스 컨테이너의 parallel 은 세 실행 모두 읽지 못했다. 읽지 않은 회차들의 배수는 0.84~9.10 으로 넓게 퍼졌다. 실행 `281b88` 에서는 scrypt 넷이 5262ms, 긴 Argon2id 넷이 19537ms 걸린 회차가 있었고, scrypt 넷의 한 회차는 틱 사이의 가장 긴 틈이 2663ms 였다(그 회차의 넷은 3910ms). 해시 하나를 넘긴 thread 갈래의 리눅스 회차에서 가장 긴 틈은 세 실행을 통틀어 153.6ms 였다. 그 긴 틈이 호스트 부하 100% 탓인지, 128 MiB 넷을 한꺼번에 잡은 탓인지, 다른 까닭인지는 가르지 못했다.
- 틱 코루틴은 쉬지 않고 돌아 주 스레드가 GIL 을 거의 내내 쥔다. thread 갈래의 작업 시간에는 작업 스레드가 GIL 을 넘겨받기를 기다린 시간이 섞이므로, 해시 한 번의 시간은 "시간" 절의 것을 쓴다.
- 해시가 GIL 을 놓는 자리(CPython 의 `hashlib.scrypt` 구현, cffi 의 호출 길)는 코드로 읽지 않았다. 위는 관찰이다.

## 재지 못한 것

- 부하가 없는 때의 시간. 측정 내내 다른 세션이 같은 PC 와 같은 Docker 데몬을 썼다. 부하 21~23% 때의 값은 요약 줄 2 회차뿐이다.
- 배포 환경의 시간과 메모리. 이 PC(Ryzen 7 3700X)와 그 위의 Docker Desktop(WSL2)에서만 쟀고, 컨테이너에 CPU·메모리 한도를 주지 않았다. 한도를 건 컨테이너에서 scrypt 128 MiB 가 어떻게 되는지는 재지 않았다.
- 리눅스 컨테이너에서 해시 넷을 한꺼번에 스레드로 넘긴 갈래. 대조가 서지 않았다.
- uvicorn 의 실제 요청 길(로그인 요청이 오는 동안 다른 요청과 SSE 스트림의 지연). 틱 코루틴 하나로만 봤다.
- 여러 해시를 한꺼번에 돌릴 때의 메모리 합과, 스레드 한도를 좁혔을 때의 대기.
- 해시가 잡았다가 쓰지 않은 메모리. 상주 메모리만 읽었다.
- arm64, musl(Alpine), 윈도 arm64, macOS 의 휠 설치와 시간. 올라와 있는 휠의 목록만 읽었다.
- 소스에서 짓는 설치(휠이 없는 플랫폼), 시스템의 libargon2 를 쓰는 설치(`ARGON2_CFFI_USE_SYSTEM`).
- 파이썬 3.12 밖의 판. 저장소의 `requires-python` 과 리눅스 바탕이 3.12 다.
- OpenSSL 이 scrypt 없이 지어진 파이썬(`hashlib.scrypt` 가 없는 환경). 두 곳 모두 있었다.
- OWASP 권고보다 센 매개변수를 고를 때의 시간(Argon2id 는 argon2-cffi 기본값 한 줄만 더 봤다).
- 비밀번호 길이와 글자(긴 비밀번호, NUL, 유니코드 정규화)에 따른 동작. 짧은 ASCII·한글 비밀번호 하나씩만 썼다.
- 틀린 비밀번호의 견줌 시간이 맞는 비밀번호와 같은지(시간 차 공격). 재지 않았다.
- bcrypt, PBKDF2, `pwdlib` 등 다른 후보. 범위 밖이다.
- import-linter 계약과 층 배치(해시 모듈을 어느 층에 둘지). 범위 밖이다.

## 남긴 것

- 이미지: `admin-login-pwhash-probe-linux`(503MB, 이 프로브가 지었다. 지우려면 `docker image rm admin-login-pwhash-probe-linux`). 받은 것은 없다. 바탕 둘(`python:3.12-slim-trixie`, `ghcr.io/astral-sh/uv:latest`)은 이미 있었다(손으로 봤다, 설치 층이 처음 돈 실행 `aaa95c` 의 원본 기록에서 두 `FROM` 이 0.0초에 끝났고 내려받는 줄이 없었다). 앞선 빌드가 남긴 이름 없는 이미지 둘은 지웠다(하나는 그 이미지의 `PYTHONPATH` 가 이 폴더인 것을 보고 손으로, 하나는 `run.py` 가).
- 컨테이너, 네트워크, 볼륨: 없다. 실행마다 끝에서 "정리: 컨테이너 0" 이었다(프로브가 낸다).
- 저장소 밖: 세션 스크래치패드의 사본 폴더 둘(가상 환경 포함)과 원본 기록. 세션과 함께 사라진다.
