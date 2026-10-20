# mcp-shutdown 프로브

명세·ADR이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/mcp-shutdown/spec.md`와 ADR 0034의 2026-10-17 이력이다.

## 돌리는 법

닫기와 serve 종료의 프로브는 저장소 `.venv`가 아니라 mcp 판마다 따로 만든 환경에서 돈다. 저장소의 mcp는 1.30.0이고 2.3.0은 `langchain-mcp-adapters`와 함께 설치되지 않는다. 이 PC의 uv 0.10.8에서는 `uv run --isolated --with`의 임시 환경이 `pywin32` 312 휠을 설치하지 못해(scripts 폴더의 임시 항목을 거부했다) `uv venv`로 만든다. 환경을 두는 폴더(`<환경>`)는 저장소 밖 어디든 된다.

```sh
uv venv <환경>/env-2.3.0 --python 3.12
uv pip install --python <환경>/env-2.3.0/Scripts/python.exe mcp==2.3.0 anyio==4.15.1 uvicorn==0.53.0 starlette==1.6.0
```

1.30.0도 같다(`mcp==1.30.0`). 저장소 루트에서 돈다(Windows, Git Bash).

```sh
PYTHONUTF8=1 <환경>/env-2.3.0/Scripts/python.exe .scratch/mcp-shutdown/probes/close_paths.py
PYTHONUTF8=1 <환경>/env-2.3.0/Scripts/python.exe .scratch/mcp-shutdown/probes/close_paths.py --python venv cancel exit_child_normal
PYTHONUTF8=1 <환경>/env-2.3.0/Scripts/python.exe .scratch/mcp-shutdown/probes/close_paths.py --cli-handler force cli_ctrl_c cli_ctrl_c_twice
PYTHONUTF8=1 <환경>/env-2.3.0/Scripts/python.exe .scratch/mcp-shutdown/probes/serve_shutdown.py
PYTHONUTF8=1 <환경>/env-2.3.0/Scripts/python.exe .scratch/mcp-shutdown/probes/everything.py
PYTHONUTF8=1 uv run python .scratch/mcp-shutdown/probes/full_stack.py
```

Linux는 Docker 컨테이너에서 돈다. `linux.sh`가 컨테이너 안에 두 환경을 만들어 대조군(1.30.0)을 한 번, 2.3.0을 런처 없이·`launcher.py`(kill)·`launcher.py --watch-parent`(watch)로 세 번 돈다. `close_paths`이면 끝에 bash가 보는 종료 코드 둘을 찍는다. `linux_full_stack.sh`는 저장소 루트를 붙여 `full_stack.py`를 돈다. 둘 다 네트워크로 패키지를 받는다.

```sh
MSYS_NO_PATHCONV=1 docker run --rm --init -v "<저장소 루트>/.scratch/mcp-shutdown/probes:/probes:ro" python:3.12.10-slim-bookworm sh /probes/linux.sh close_paths
MSYS_NO_PATHCONV=1 docker run --rm --init -v "<저장소 루트>/.scratch/mcp-shutdown/probes:/probes:ro" python:3.12.10-slim-bookworm sh /probes/linux.sh close_paths --cli-handler force cli_ctrl_c cli_ctrl_c_twice
MSYS_NO_PATHCONV=1 docker run --rm --init -v "<저장소 루트>/.scratch/mcp-shutdown/probes:/probes:ro" python:3.12.10-slim-bookworm sh /probes/linux.sh serve_shutdown
MSYS_NO_PATHCONV=1 docker run --rm --init -v "<저장소 루트>:/repo:ro" python:3.12.10-slim-bookworm sh /repo/.scratch/mcp-shutdown/probes/linux_full_stack.sh
```

`stale_parent.py`는 `full_stack.py`가 Linux 사본에서 부른다. 표준 라이브러리만 쓰므로 시제품 폴더를 지금 폴더로 주면 패키지 없이 홀로도 돈다.

```sh
MSYS_NO_PATHCONV=1 docker run --rm --init -v "<저장소 루트>:/repo:ro" -w /repo/.scratch/mcp-shutdown/probes/prototype python:3.12.10-slim-bookworm python /repo/.scratch/mcp-shutdown/probes/stale_parent.py --expect refused
```

`--init`은 컨테이너의 첫 프로세스가 고아가 된 프로세스를 거두게 한다. 없으면 상류의 그룹 기다림이 끝난 좀비를 산 것으로 볼 수 있다(mcp 2.3.0의 `terminate_posix_process_tree` 독스트링을 읽었다. 없는 판으로는 재지 않았다).

프로브는 남은 프로세스를 번호만 보고 끄지 않는다. 가짜 프로세스는 멈춤 파일이나 60초 수명으로 스스로 끝나고, `everything.py`는 번호·만든 시각·명령줄이 연 뒤의 목록과 모두 같은 것만 다시 확인한 뒤 끈다(번호는 다시 쓰여 남의 프로세스를 끌 수 있다. 일지 2026-10-16-36 "사고"). 프로브가 스스로 띄운 자식(`Popen`의 핸들을 쥔 것)은 시간이 넘으면 그 핸들로 끈다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `close_paths.py`(가짜 프로세스 `fakes.py`, 런처 시제품 `launcher.py`, Linux 실행 `linux.sh`) | mcp의 `stdio_client`와 `ClientSession`을 직접 열어 닫는 길마다 서버와 그 자식이 내려가는지와 닫는 데 걸린 시간. 사례는 도구 호출 도중의 기한(`cancel`), 정상 닫기(`stay_normal`), 자식을 남기는 서버(`exit_child_normal`), 세션 안의 예외(`raise_inside`), 다른 태스크에서 닫아 닫기 자체가 예외로 끝남(`close_fails`), SIGTERM을 무시하는 서버(`sigterm_ignored_cancel`, POSIX), 없는 명령(`missing_command`), CLI처럼 `asyncio.run`으로 도는 자식의 Ctrl+C 한 번(`cli_ctrl_c`)과 닫는 도중의 둘째(`cli_ctrl_c_twice`, 10초 뒤에도 살아 있으면 셋째)와 그 자식의 종료 코드. `--cli-handler force`는 두 CLI 사례를 명세가 정한 처리기의 시제품(`_run_with_force_exit`)으로 돈다. 하트비트 파일이 0.6초 사이에 자랐는지로 산 것을 가른다. 1.30.0이 양성 대조다(서버가 남는다). 표지는 독스트링 | `spec.md`의 "닫는 데 드는 시간", "서버를 여는 실패", "경계를 넘는 예외", "CLI의 Ctrl+C", "결말 뒤 닫기의 예외", Testing Decisions. ADR 0034의 2026-10-17 이력 | 위 명령. 사례 하나에 5~15초, 전부 1~2분 | mcp 1.30.0·2.3.0, anyio 4.15.1, Python 3.12.10. Windows 10(이 PC)과 Docker의 Debian bookworm(WSL2 커널 6.18), 2026-10-17 |
| `serve_shutdown.py`(같은 `fakes.py`·`launcher.py`·`linux.sh`) | serve처럼 uvicorn(`timeout_graceful_shutdown=5`)으로 띄운 앱의 수명(`Runs.lifespan`과 같은 모양)이 실행 하나(입력이 닫혀도 끝나지 않는 서버)를 쥔 채 멈출 때, 서버가 내려가는지와 신호에서 수명 닫기·실행 끝·프로세스 끝까지의 시간. 사례는 신호 하나(`graceful`), SIGINT 둘(`force`, POSIX), 수명 닫기 도중의 셋째(`force_then_interrupt`, POSIX), 강제 종료(`sigkill`) | `spec.md`의 "serve 종료", "Linux 런처"의 끄는 때. ADR 0034의 2026-10-17 이력 | 위 명령. 사례 하나에 10~20초 | 위와 같고 uvicorn 0.53.0, starlette 1.6.0 |
| `everything.py` | 실제 `npx`의 everything(`plugins/mcp/everything`과 같은 명령)으로 도구 호출 도중의 기한과 정상 닫기 뒤 자손 프로세스(번호·만든 시각·명령줄)가 남는지. 이벤트 루프를 살려 둔 채 1초·4초·`gc.collect()` 뒤에 보고, 루프를 닫은 뒤에 한 번 더 본다. Windows만 | `spec.md`의 Problem Statement, ADR 0034의 "검증"(재현 프로브) | Node와 npx, 네트워크(처음 받을 때). 사례 하나에 15~25초 | 위 판과 Node 24.19.0, npx 11.17.0, `@modelcontextprotocol/server-everything` 1.0.0(npx 캐시의 package.json) |
| `full_stack.py`(시제품 `prototype/`, Linux 실행 `linux_full_stack.sh`) | 저장소 사본의 의존성을 `mcp>=2.3,<3`으로 바꾸고 시제품(어댑터, 런처, 픽스처 서버, 닫기 테스트의 가짜 프로세스, 쪽 나눔 가짜 서버, CLI 처리기, 어댑터와 처리기의 테스트)을 얹은 뒤 시제품 파일의 ruff 검사와 포맷, pyright strict, 타입 우회 검사, lint-imports, `tests/adapters`·`tests/core`·`tests/channel`이 지나는지와 두 테스트 파일의 시간. 사본에서 `write_failure.py --expect closed`를, POSIX에서는 `stale_parent.py --expect refused`도 돈다. 대조군(양성 대조)은 두 OS에서 처리기를 `asyncio.run` 그대로로 바꾼 사본과 어댑터가 겉봉을 벗기지 않는 사본(여기서는 `write_failure.py --expect escaped`), POSIX에서 런처를 뺀 사본과 부모 감시를 뺀 사본(여기서는 `stale_parent.py --expect spawned`)이다. 기대한 테스트만 기대한 까닭(실패 요약 줄의 문구)으로 빨간지 본다. 어긋남이 없으면 만든 임시 폴더를 지운다 | `spec.md`의 "경계를 넘는 예외", "소비 지점까지 잰 것", Testing Decisions의 "빨강을 먼저 본다"와 "시간" | 위 명령. `--source <트리>`로 다른 커밋의 트리를 줄 수 있다(`git archive <커밋> \| tar -x -C <트리>`로 푼 것. Linux는 그 트리를 `/src`에 붙이고 `linux_full_stack.sh /src`). 패키지를 받고 테스트를 돌려 Windows 8~14분(부하에 따라), Linux 8~10분 | mcp 2.3.0, mcp-types 2.3.0, anyio 4.15.1, pydantic 2.13.5, pyright 1.1.414, ruff 0.16.8, 저장소 `83f09401`(앞선 회차는 `30949cfc`, `aa93cf7b`, `8a2163eb`) |
| `stale_parent.py` | POSIX 런처 시제품이, 자기를 띄운 프로세스가 런처가 뜨기 전에 이미 끝났으면 서버를 띄우지 않는지. 중간 프로세스가 갈라 낸 자식(`fork`)이 새 세션을 열고 중간 프로세스의 번호를 넘기며 런처로 바뀐다(`exec`). 중간 프로세스가 곧바로 끝나고 자식은 부모가 바뀐 것을 본 뒤에 바뀌는 `died`와, 중간 프로세스가 자식을 기다리는 `alive`(양성 대조: 런처가 서버를 띄우고 그룹을 SIGKILL로 꺼 -9)를 세 회차씩 돈다. `--expect refused`는 런처의 거부 문구("이미 끝나")가 있고 서버의 표지 파일이 없는 것, `--expect spawned`(부모와 견주는 두 자리를 지운 런처)는 서버의 표지가 생기는 것이다. 우두머리가 아니라서 띄우지 않은 것과는 런처의 문구로 가른다. 표지는 독스트링 | `spec.md`의 "Linux 런처"(견주는 번호), Testing Decisions의 "모듈" | `full_stack.py`가 Linux 사본에서 돈다. 홀로는 위 명령. 10초 안팎 | Python 3.12.10, Docker의 Debian bookworm. 시제품은 위 `full_stack.py`의 판 |
| `write_failure.py` | core `run()`에 진짜 MCP 어댑터를 물려, 연결이 열린 채 트레이스 쓰기가 실패한 실행(둘째 쓰기 `write_2`, 셋째 쓰기 `write_3`), 에이전트가 예외를 낸 실행(`raise`), 실패하는 도구를 부른 에이전트가 런타임의 `ToolError`를 잡지 않은 실행(`tool_error`)이 어떻게 끝나는지. 트레이스의 기록, `run()`이 낸 이벤트, `run_failed`의 글과 원인, `run()` 밖으로 나온 예외를 찍는다. 지금 폴더의 트리를 쓰므로 저장소에서 돌면 지금 판을, `full_stack.py`의 사본에서 돌면 시제품을 잰다. 표지(도구가 불렸고 실패시키려던 차례에 그 이벤트의 쓰기를 시도했다)와 판정(글, 원인, 겉봉 안의 `GeneratorExit`)은 독스트링 | `spec.md`의 Solution, 사용자 스토리 11, "경계를 넘는 예외" | 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/mcp-shutdown/probes/write_failure.py --expect escaped`. 지금 판은 그룹을 올려 `escaped`가 기대다. 10초 안팎 | 지금 판은 mcp 1.30.0, langchain-mcp-adapters 0.3.2, 저장소 `30949cfc`, Windows(이 PC). 시제품은 위 `full_stack.py`의 판 |

## 2026-10-21 결과

PR 직전 리뷰(보안 축과 버그·성능 축)를 반영한 뒤 돈 회차다. 보안 축은 지적이 없었다. 버그·성능 축이 짚어 시제품을 넷 고쳤다. 어댑터는 도구 목록에서 빈 커서를 끝으로 보고 1000쪽을 넘으면 실패한다(쪽 나눔 가짜 서버 `mcp_paged_server.py`와 테스트 둘을 더했다). 런처는 어댑터가 넘긴 번호와 견주고 뜨자마자 한 번 견준다(그것을 재는 `stale_parent.py`를 더했다). CLI 처리기는 표준 출력이나 에러를 쓰다 `OSError`가 나도 끝나는 꼴을 지킨다. 닫기 테스트의 가짜 프로세스는 하트비트 쓰기가 한 번 실패해도 쓰는 스레드가 죽지 않는다. `full_stack.py`에는 POSIX 단계와 대조군 하나(둘 다 `stale_parent.py`)와 임시 폴더 지우기(대기열 392)를 더했다. `close_paths.py`·`serve_shutdown.py`·`everything.py`는 다시 돌리지 않았다.

### `full_stack.py`

이 브랜치가 합친 `83f09401` 위에서 두 OS가 함께 돌았다(`30949cfc`와 사이에 `src`와 어댑터·core·채널의 테스트는 바뀌지 않았다). 두 OS 모두 기대와 어긋난 단계가 없어 임시 폴더를 지웠다(`"removed": true`). 패키지는 앞선 회차와 같은 84개다. 시제품 파일 여덟의 ruff 검사와 포맷 0건, pyright strict 0건, 타입 우회 검사 0건, import 계약 다섯 유지, `tests/adapters`·`tests/core`·`tests/channel` 658개 통과(앞 회차 656개와 쪽 나눔 테스트 둘, 1개는 `llm` 표지로 빠졌다). 사본의 `write_failure.py --expect closed`는 네 사례 모두 `run_failed`로 끝났고 밖으로 나온 예외가 없었다.

대조군 넷은 앞 회차와 같은 테스트가 같은 까닭으로 빨갰다(위 2026-10-20 표). 더한 것은 `stale_parent.py`다.

| 런처(Linux, 프로브의 첫 판) | `died`(부모가 런처를 띄우자마자 끝남) 세 회차 | `alive`(양성 대조) 세 회차 |
|---|---|---|
| 시제품, `--expect refused` | 모두 런처가 "이미 끝나" 한 줄을 남기고 서버를 띄우지 않았다 | 모두 서버가 뜨고 런처가 -9로 끝났다 |
| 부모를 보지 않는 사본, `--expect spawned` | 모두 서버가 떴다(부모가 끝난 것을 본 때 서버의 표지는 아직 없었다) | 같다 |

- 이 프로브는 full_stack에 엮기 전에 시제품 폴더를 그대로 붙인 컨테이너에서 손으로 두 기대를 한 번씩 돌렸고 같은 값이었다. 지금 런처에 `--expect spawned`를 주자 `died` 세 회차가 어긋남으로 잡혔다.
- 쪽 나눔 테스트 둘은 고치기 전의 어댑터를 얹은 사본(앞 회차가 남긴 것)에서 둘 다 기한 30초에 걸려 `TimeoutError`로 빨갰다(같은 쪽을 거듭 물은 것은 코드를 읽은 추론이다). 고친 어댑터로는 같은 Windows 사본에서 홀로 2.94초(1000쪽)와 2.34초(빈 커서)에 지났고, 셀프 리뷰 뒤 다시 돌려 2.51초와 1.64초였다(손으로 봤다. full_stack의 대조군에는 넣지 않았다).

### 셀프 리뷰 뒤 다시 돈 Linux 회차

명세의 둘째 셀프 리뷰(일지 2026-10-20-36의 "2026-10-21 셀프 리뷰를 이어받은 세션")가 `stale_parent.py` 첫 판의 표지가 재려는 상황을 보이지 못한다고 짚었다. 첫 판은 중간 프로세스가 런처를 띄우자마자 끝나 런처의 파이썬이 뜨는 시간과 겨뤘고, `spawned`의 표지(부모가 끝난 것을 본 때 서버의 표지가 아직 없었다)는 런처가 띄울지 정한 순간에 부모가 이미 없었다는 것까지 보이지 못했다. 지금 판은 갈라 낸 자식이 부모가 바뀐 것을 본 뒤에 런처로 바뀌고 그 사실을 파일로 남긴다(독스트링). 그 판으로 `full_stack.py`를 Linux에서만 다시 돌렸다(`83f09401`. Windows는 그 프로브를 돌지 않고, 시제품의 다른 변경은 독스트링과 주석뿐이다).

- 어긋난 단계가 없어 임시 폴더를 지웠다. 시제품 파일 여덟의 ruff 검사와 포맷 0건, pyright strict 0건, 타입 우회 검사 0건, import 계약 다섯 유지, 658개 통과, `write_failure.py` 네 사례 기대대로, 대조군 넷은 위와 같은 테스트가 같은 까닭으로 빨갰다.
- `stale_parent.py`는 두 기대 모두 `died` 세 회차의 표지(부모가 바뀐 것을 본 뒤에 런처로 바뀌었다)가 섰다. 지금 런처는 세 회차 모두 "이미 끝나" 한 줄을 남기고 서버를 띄우지 않았고, 부모를 보지 않는 사본의 런처는 세 회차 모두 서버를 띄웠다. `alive`는 두 런처 모두 서버가 뜨고 런처가 -9로 끝났다.
- full_stack에 엮기 전에 시제품 폴더를 붙인 컨테이너에서 홀로 돌려 같은 값을 봤고, 지금 런처에 `--expect spawned`를 주자 `died` 세 회차가 어긋남으로 잡혔다.

새 테스트의 시간(`--durations`, 초). 같은 때 두 회차가 함께 돌았고, Windows는 시간이 바뀌지 않은 픽스처 테스트도 앞 회차보다 길었다.

| 테스트 | Windows | Linux |
|---|---|---|
| 도구 호출 도중의 기한 | 12.76 | 5.65 |
| 연결을 연 프로세스가 갑자기 죽음 | 14.28 | 5.12 |
| 연결 안의 예외 | 9.37 | 4.99 |
| 자식을 남기는 서버의 닫기 | 7.91 | 3.16 |
| 도구 호출 도중에 서버가 죽음 | 3.78 | 0.95 |
| 연결 안에서 던진 예외 그룹 | 3.54 | 1.40 |
| yield에 멈춘 제너레이터 | 3.11 | 1.15 |
| 뜨자마자 끝나는 서버 | 0.36 | 0.08 |
| 끝나지 않는 도구 목록(1000쪽) | 6.13 | 2.64 |
| 빈 커서 | 5.48 | 1.24 |
| Ctrl+C 한 번 | 12.45 | 5.67 |
| Ctrl+C 두 번 | 9.22 | 2.78 |
| 있던 픽스처 테스트 넷(목록, 호출, 실패, 없는 도구) | 3.85~6.05씩 | 1.15~1.40씩 |

### 다시 돌리기 전에 고칠 것

PR 직전 버그·성능 축이 짚었고 이번 회차에는 닿지 않아 고치지 않았다. 둘 다 프로브가 끝나지 않거나 프로세스를 남기는 길이라 측정값은 바꾸지 않는다.

- `full_stack.py`의 `_run`은 `subprocess.run(capture_output=True, timeout=…)`이다. 시간이 넘으면 `uv`만 끄고, Windows에서는 그 뒤 시간 제한 없는 `communicate()`로 출력을 거둔다. `uv`가 띄운 pytest가 파이프를 쥐고 있으면 끝을 보지 못해 프로브가 끝나지 않고 pytest가 남는다(Python 3.12.10의 `subprocess.run` 소스를 읽었다. 끝나지 않는 것은 재지 않았다). 출력을 파일로 받거나 시간 제한이 걸리는 읽기로 바꾼다.
- `serve_shutdown.py`는 서버가 30초 안에 뜨지 않거나 `/start` 응답이 오류면 `urlopen`의 예외로 추적을 남기고 끝난다. 그때 띄운 uvicorn 자식은 멈춤 파일도 부모 감시도 없어 남고 포트를 쥔다. 그 자식을 쥔 `Popen` 핸들로 끄는 `finally`를 둔다(이 폴더의 프로세스를 끄는 규칙은 위 "프로브는 남은 프로세스를 번호만 보고 끄지 않는다").

## 2026-10-20 결과

main이 `30949cfc`로 나아간 뒤 돈 회차다. `full_stack.py`와 `write_failure.py`는 지금의 스크립트로 두 OS에서 돌았다. `close_paths.py`와 `everything.py`는 ruff의 try 문 규칙(PLW0717)에 맞춰 사례의 본문을 안쪽 함수로 뺐고 동작은 바꾸지 않았다. 그래서 바뀐 함수가 지나는 사례만 mcp 2.3.0으로 다시 돌렸고(Windows), 앞선 회차와 같은 값이 나왔다. `close_paths.py`는 `cancel` 2.046초, `raise_inside` 2.016초(두 겹 그룹), `close_fails` 2.0초, `cli_ctrl_c` 2.215초(종료 코드 3221225786)였고 모두 내려갔다. `everything.py`는 `cancel`이 2.032초였고 1초 뒤 남은 것이 없었다. 이번 회차의 npx는 everything 2.0.0을 받았다(앞선 회차는 1.0.0). 아래 2026-10-17 결과의 나머지 표는 다시 돌리지 않았다.

### `full_stack.py`

`30949cfc` 위에서 두 번 돌았고 두 번 모두 두 OS에서 기대와 어긋난 단계가 없었다. 둘째는 명세의 셀프 리뷰가 시제품(어댑터의 예외 기억을 객체 하나로, 처리기의 상태를 객체 하나로, 처리기 테스트가 도구 호출의 시작과 취소를 표지로 본다)과 `write_failure.py`(넷째 사례 `tool_error`, 판정이 글·원인·겉봉 안의 `GeneratorExit`·실패시킨 쓰기의 이벤트를 본다)를 고친 뒤의 회차이고 아래 수는 그 회차의 것이다. Windows와 Docker의 회차가 함께 돌았다. `uv lock`의 변화는 앞선 회차와 같고 패키지는 84개다. 시제품 파일의 ruff 검사와 포맷 0건, pyright strict 0건, 타입 우회 검사 0건, import 계약 다섯 유지, `tests/adapters`·`tests/core`·`tests/channel` 656개 통과(지금 646개와 새 테스트 열 개, 1개는 `llm` 표지로 빠졌다). 사본의 `write_failure.py --expect closed`는 네 사례 모두 `run_failed`로 끝났고 밖으로 나온 예외가 없었다.

| 대조군 | 실패한 테스트(실패 요약 줄) | 기대 |
|---|---|---|
| 처리기 없음(`asyncio.run` 그대로), 두 OS | 처리기의 두 테스트. 한 번은 중단의 한 줄 대신 KeyboardInterrupt의 추적이 찍혔고, 두 번은 30초 안에 끝나지 않았다 | 같다 |
| 겉봉을 벗기지 않는 어댑터, 두 OS | 뜨자마자 끝나는 서버와 연결 안의 예외(`[single exception in ExceptionGroup]`), 연결 안에서 던진 예외 그룹(두 겹 그룹의 단언), yield에 멈춘 제너레이터(`[single exception in BaseExceptionGroup]`). 그 사본의 `write_failure.py --expect escaped`는 쓰기 사례 둘에서 `GeneratorExit`를 든 `BaseExceptionGroup`을 올렸고 예외 사례 둘은 벗기는 어댑터와 같았다 | 같다 |
| 런처를 쓰지 않는 어댑터, Linux | 자식을 남기는 서버, 프로세스가 갑자기 죽음 | 같다 |
| 부모를 보지 않는 런처, Linux | 프로세스가 갑자기 죽음 | 같다 |

새 테스트의 시간(`--durations`, 초). 앞의 두 열이 둘째 회차이고, 괄호 안은 첫 회차(Windows는 CPU가 89%로 붐비던 때)다.

| 테스트 | Windows | Linux |
|---|---|---|
| 도구 호출 도중의 기한 | 7.74 (14.12) | 6.98 (6.36) |
| 연결을 연 프로세스가 갑자기 죽음 | 9.72 (14.69) | 5.73 (5.64) |
| 연결 안의 예외 | 6.41 (12.46) | 5.25 (5.85) |
| 자식을 남기는 서버의 닫기 | 4.27 (8.51) | 3.48 (3.20) |
| 도구 호출 도중에 서버가 죽음 | 1.69 (3.99) | 1.16 (1.88) |
| 연결 안에서 던진 예외 그룹 | 1.83 (4.70) | 1.40 (1.44) |
| yield에 멈춘 제너레이터 | 1.88 (4.11) | 1.36 (1.88) |
| 뜨자마자 끝나는 서버 | 0.11 (0.41) | 0.09 (0.09) |
| Ctrl+C 한 번 | 8.90 (14.03) | 7.18 (7.20) |
| Ctrl+C 두 번 | 6.16 (10.94) | 2.79 (4.78) |
| 있던 픽스처 테스트 넷(목록, 호출, 실패, 없는 도구) | 1.79~2.76씩 (4.28~5.56씩) | 1.41~2.36씩 (1.47~1.71씩) |

- 이 판보다 한 걸음 앞선 회차는 두 OS에서 테스트와 대조군이 모두 기대대로였지만, ruff 검사가 시제품 CLI 테스트의 import 정렬로 빨갰고 Linux에서는 pyright가 같은 파일의 import 하나를 쓰지 않은 것으로 짚었다. ruff 0.16.8은 모듈 경로 전체가 `src`에 있어야 1st-party로 본다(`ruff check -v`의 `Categorized … SourceMatch` 줄). 그래서 저장소의 `src`에 없는 시제품 모듈 `agent_os.channel.cli.interrupt`를 이 폴더에서는 3rd-party로, 사본에서는 1st-party로 봐 서로 다른 정렬을 요구했다. pyright는 모듈 수준의 `sys.platform` 비교에서 윈도 갈래를 닿지 않는 코드로 보아, 그 갈래만 쓰던 import를 짚었다. 모듈째 가져오게 고쳐 둘 다 풀렸다.
- 그보다 앞선 회차는 사례 5가 하트비트를 20초 안에 보지 못해 빨갰다. 다른 세션의 테스트와 겹친 부하(CPU 86%)에서 그 사례만 홀로 돌려도 12.5초 걸려, 기다리는 상한을 30초로, 가짜 프로세스의 수명을 120초로 늘렸다.

### `write_failure.py` — 지금 판(저장소 `30949cfc`, Windows)

| 사례 | 트레이스에 쓴 것 | `run_failed`의 글(원인) | `run()` 밖으로 나온 예외 |
|---|---|---|---|
| `write_2` | `run_started`, `run_failed` | `OSError: 트레이스를 쓸 수 없다: 디스크가 가득 찼다`(그 밖) | `BaseExceptionGroup[BaseExceptionGroup[GeneratorExit]]` |
| `write_3` | `run_started`, `tool_called`, `run_failed` | 같다 | 같다 |
| `raise` | `run_started`, `tool_called`, `run_failed` | `ValueError: 에이전트가 낸 예외, 도구 결과 4`(에이전트 코드) | 없음 |
| `tool_error` | `run_started`, `tool_called`, `run_failed` | `ToolError: Error executing tool fail: 도구가 낸 실패`(도구 실패) | 없음 |

- 시제품(두 OS, 위 `full_stack.py`의 사본)은 네 사례의 기록과 글이 같고 밖으로 나온 예외가 없었다. 겉봉을 벗기지 않는 시제품은 지금 판과 같았다.
- `tool_error` 사례와 판정의 넷째 조건(겉봉 안의 `GeneratorExit` 등)은 명세의 셀프 리뷰가 더했다. 더한 뒤 지금 판에 반대 기대(`--expect closed`)를 주자 쓰기 사례 둘이 어긋남으로 잡혔다(`"unexpected": ["write_2", "write_3"]`).

## 2026-10-17 결과

그날의 스크립트로 돌린 회차다. `close_paths.py`와 `full_stack.py`는 셀프 리뷰를 반영한 판(`close_fails`, 표지 강화, 처리기의 끝나는 꼴, 처리기 테스트와 그 대조군)으로 다시 돌았고, `serve_shutdown.py`와 `everything.py`는 그 앞의 회차다(두 스크립트와 그것이 쓰는 `fakes.py`·`launcher.py`는 그 뒤 바뀌지 않았다). "남음"은 닫은 뒤(CLI와 serve는 프로세스가 끝난 뒤) 3초에 하트비트가 0.6초 사이에 자랐다는 것이다. 닫은 직후의 판정은 마지막 몇 번의 쓰기를 잡을 수 있어(Linux 런처의 부모 감시는 0.2초마다 본다) 표에 쓰지 않았다. 멈춤 파일을 만든 뒤에는 모든 회차에서 모든 하트비트가 멈췄다.

### `close_paths.py` — Windows(이 PC)

| 사례 | 1.30.0 | 2.3.0 |
|---|---|---|
| `cancel`(기한 → 호출자의 예외까지) | 0.0초, `TimeoutError`. 감싼 프로세스는 꺼지고 서버 남음 | 2.047초, `TimeoutError`. 모두 내려감 |
| `cancel`, `--python venv` | 0.031초, 서버 남음 | 2.047초, 모두 내려감 |
| `stay_normal`(닫기) | 2.015초, 모두 내려감 | 2.156초, 모두 내려감 |
| `exit_child_normal`(닫기) | 0.094초, 자식도 내려감 | 0.203초, 자식도 내려감(`--python venv` 0.421초) |
| `raise_inside`(닫기) | 2.016초. 호출자에게 `ExceptionGroup[ExceptionGroup[ProbeError]]`. 모두 내려감 | 2.078초. 같은 모양. 모두 내려감 |
| `close_fails`(다른 태스크에서 닫기) | 2.016초. 닫기가 `RuntimeError: Attempted to exit cancel scope in a different task than it was entered in`로 끝남. 모두 내려감 | 2.031초. 같다. 모두 내려감 |
| `missing_command` | `FileNotFoundError: [WinError 2]` | 같다 |
| `cli_ctrl_c`(SIGINT → 자식 끝) | 2.409초, 모두 내려감. 종료 코드 3221225786 | 2.424초, 모두 내려감. 같은 코드 |
| `cli_ctrl_c_twice` | 둘째 뒤 0.313초에 끝남, 모두 내려감. 같은 코드 | 끝나지 않음. 셋째 SIGINT(둘째 10초 뒤)에 KeyboardInterrupt를 냈지만 60초에 프로브가 껐다. 표지(자식이 스스로 끝났다)가 서지 않아 측정 아님으로 세었고 프로브가 1로 끝났다 |

- 1.30.0에서 기한이 끊은 닫기는 첫 기다림에서 멈춰 0초 만에 호출자에게 왔고, 감싸는 프로세스만 꺼져 서버가 남았다. venv 파이썬이 한 겹 더 껴도(`--python venv`) 같았다. 이 PC에서 그 겹을 손으로 보니 `env/Scripts/python.exe`가 기본 파이썬(`Python312\python.exe`)을 자식으로 띄웠다(`Get-CimInstance Win32_Process`로 부모를 봤다).
- 종료 코드 3221225786(0xC000013A, `STATUS_CONTROL_C_EXIT`)은 처리하지 않은 KeyboardInterrupt로 끝난 파이썬의 것이다.
- 앞선 회차(표지를 강화하기 전의 판)의 값도 같은 모양이었다(1.30.0의 `cli_ctrl_c_twice`는 둘째 뒤 0.118초).
- `cli_ctrl_c_twice`(2.3.0)의 앞선 회차 하나는 프로브가 자식의 스택을 남기게 고친 뒤 돌렸다. 20초에 찍힌 스택에서 주 스레드는 `asyncio.runners._cancel_all_tasks`의 `run_until_complete` 안에 있었다(둘째 SIGINT의 KeyboardInterrupt로 `asyncio.run`이 남은 태스크를 취소하고 기다리는 자리). 상류의 출력 비우기(`_drain_stdout`)가 취소에서 보호된 채 살아 있는 서버의 출력 끝을 기다려 그 태스크가 끝나지 않는 것으로 본다(코드를 읽은 어림, 그 태스크의 스택은 찍히지 않는다). 셋째 SIGINT 뒤에도 끝나지 않은 까닭(anyio의 작업 스레드를 기다리는 것으로 보인다. 스택에 그 스레드가 있었다)은 가르지 않았다. 프로브가 자식을 끈 뒤(TerminateProcess) 서버는 Job Object와 함께 내려갔다.

### `serve_shutdown.py` — Windows(이 PC)

신호는 CTRL_BREAK(uvicorn 이 SIGBREAK 로 받는다)다. 시각은 신호에서 잰 초다.

| 사례 | 1.30.0 | 2.3.0 |
|---|---|---|
| `graceful` | 수명 닫기 5.177, 실행 끝 5.262, 프로세스 끝 5.277. 프로세스가 끝나며 서버도 내려감(Job Object) | 수명 닫기 5.203, 실행 끝 7.336, 프로세스 끝 7.403. 모두 내려감 |
| `sigkill`(TerminateProcess) | 0.002초에 끝남. 모두 내려감 | 0.003초에 끝남. 모두 내려감 |

### `everything.py` — Windows(이 PC)

연 뒤의 자손은 네 회차 모두 `cmd.exe`(npx.CMD) → `node.exe`(npx-cli.js) → `cmd.exe`(mcp-server-everything) → `node.exe`(server-everything의 index.js)였다.

| 갈래 | `normal`(닫기) | `cancel`(기한 → 예외) | `cancel` 뒤 1초 | 4초 | `gc.collect()` 뒤 |
|---|---|---|---|---|---|
| raw, 1.30.0 | 0.047초, 남은 것 없음 | 0.016초, `TimeoutError` | node 둘과 cmd 하나 남음 | 없음 | 없음 |
| repo(지금 어댑터), 1.30.0 | 0.063초, 남은 것 없음 | 0.015초, `TimeoutError` | node 둘과 cmd 하나 남음 | 없음 | 없음 |
| raw, 2.3.0 | 0.031초, 남은 것 없음 | 2.032초, `TimeoutError` | 없음 | 없음 | 없음 |

- 1.30.0에서 기한이 끊은 닫기는 맨 위 `cmd.exe`만 껐고, 그 아래 셋은 1초 뒤에 살아 있다가 4초 뒤에는 없었다. 끊긴 연결의 입력 파이프가 곧 닫혀 everything이 입력의 끝을 보고 스스로 끝난 것으로 본다(어림, 가르지 않았다). 2026-10-15 인터뷰는 core `run()`을 거친 실행에서 12초 넘게 남고 `gc.collect()` 뒤에야 내려가는 것을 손으로 봤다. 이 프로브의 두 갈래(상류를 직접 연 것, 지금 어댑터)는 그 모양을 재현하지 못했다. 입력이 닫혀도 끝나지 않는 서버(`close_paths.py`)로는 1.30.0에서 3초 뒤에도 남는 것을 두 OS에서 봤다.
- 2.3.0에서는 기한 뒤 2.0초에 호출자가 `TimeoutError`를 받았고, 그때 이미 넷 모두 없었다.
- 첫 판(루프를 닫은 뒤에 보던 판, raw 만)의 회차도 같았다(1.30.0: 1초 뒤 셋 남고 4초 뒤 없음. 2.3.0: 2.0초, 1초 뒤 없음).

### `close_paths.py` — Linux(Docker)

대조군(1.30.0)은 `cancel`·`exit_child_normal`·`close_fails`·`cli_ctrl_c`·`cli_ctrl_c_twice`만 돈다. 2.3.0의 셋은 런처 없이(none), 서버가 끝날 때만 끄는 런처(kill), 부모도 보는 런처(watch)다.

| 사례 | 1.30.0 | 2.3.0 none | 2.3.0 kill | 2.3.0 watch |
|---|---|---|---|---|
| `cancel` | 0.004초, 서버 남음 | 2.014초, 모두 내려감 | 2.014초, 모두 내려감 | 2.022초, 모두 내려감 |
| `stay_normal` | | 2.021초, 내려감 | 2.020초, 내려감 | 2.015초, 내려감 |
| `exit_child_normal` | 0.327초, 자식 남음 | 0.455초, 자식 남음 | 0.176초, 자식도 내려감 | 0.341초, 자식도 내려감 |
| `raise_inside` | | 2.021초. 두 겹 그룹. 내려감 | 2.017초. 같다 | 2.021초. 같다 |
| `close_fails` | 2.103초. 닫기가 `RuntimeError`(다른 태스크)로 끝남. 내려감 | 2.012초. 같다 | 2.013초. 같다 | 2.014초. 같다 |
| `sigterm_ignored_cancel` | | 4.006초, 내려감 | 4.013초, 내려감 | 4.013초, 내려감 |
| `missing_command` | | `FileNotFoundError: [Errno 2] …` | `ExceptionGroup[ExceptionGroup[MCPError: Connection closed]]`. 표준 에러에 런처의 한 줄 | 같다 |
| `cli_ctrl_c` | 5.975초, 내려감 | 2.173초, 내려감 | 2.220초, 내려감 | 2.197초, 내려감 |
| `cli_ctrl_c_twice` | 둘째 뒤 2.216초에 끝남. 서버 남음 | 둘째 뒤 끝나지 않고 셋째 뒤 0.388초에 끝남. 서버 남음 | 셋째 뒤 0.169초. 서버 남음 | 셋째 뒤 0.155초. 모두 내려감 |

- 모든 CLI 회차의 종료 코드(`Popen`이 보는 값)는 -2(SIGINT로 죽음)였다. 같은 컨테이너의 bash는 처리하지 않은 KeyboardInterrupt로 끝난 파이썬과, SIGINT를 기본 처리로 되돌려 자기에게 보낸 파이썬(처리기 시제품이 끝나는 꼴)을 모두 130으로 봤다(`linux.sh`의 끝 두 줄).
- 1.30.0의 `cli_ctrl_c`는 앞선 회차에서 2.350초였다. 이번의 5.975초를 가르지는 않았다(같은 때 Windows에서 다른 프로브가 돌았다).
- 1.30.0의 `cli_ctrl_c_twice`는 Windows(둘째 뒤 0.3초, 모두 내려감)와 달랐다. 둘째 KeyboardInterrupt 뒤 남은 태스크를 다시 취소하자 1.30.0의 닫기가 끊긴 것으로 본다(어림, 가르지 않았다).
- `missing_command`의 런처 뒤 실패는 이 프로브의 런처(`launcher.py`)가 띄우기 실패를 표준 에러에 한 줄로 남기고 127로 끝난 것이다. 시제품의 어댑터는 띄우기 전에 명령을 찾아본다(`full_stack.py`의 서버 기동 실패 테스트가 두 OS에서 초록이었다).
- 앞선 회차(가짜 서버가 출력 쓰기의 오류로 스스로 끝나던 첫 판의 `fakes.py`, Linux의 `cli_ctrl_c`가 보조 스레드에서 SIGINT를 올리던 첫 판)는 표에서 뺐다. 첫 판의 `cli_ctrl_c`는 신호가 주 스레드의 대기를 깨우지 못해 `slow(30)`이 돌아온 뒤에야 처리되어 30초를 쟀다. 지금 판은 그 회차를 표지(도구가 돌아오기 전에 끝났다)로 측정 아님으로 센다.

### CLI 처리기 시제품 — `close_paths.py --cli-handler force`

처리기는 `asyncio.run` 앞에 단 SIGINT 처리기다. 첫 번째는 주 태스크를 한 번 취소하고, 두 번째는 한 줄을 남기고 곧바로 끝난다. 끝나는 꼴은 처리하지 않은 KeyboardInterrupt로 끝나는 파이썬과 같다(POSIX는 SIGINT를 기본 처리로 되돌려 자기에게 보내고, Windows는 `os._exit`에 `STATUS_CONTROL_C_EXIT`). 시간은 첫 SIGINT(두 번이면 둘째)에서 자식이 끝나기까지다. 종료 코드는 모든 회차에서 처리기 없는 회차와 같았다(Windows 3221225786, Linux -2).

| 자리 | `cli_ctrl_c`(한 번) | `cli_ctrl_c_twice`(두 번) |
|---|---|---|
| Windows, 1.30.0 | 2.017초, 모두 내려감 | 둘째 뒤 0.011초. 모두 내려감(Job Object) |
| Windows, 2.3.0 | 2.016초, 모두 내려감 | 둘째 뒤 0.013초. 모두 내려감(Job Object) |
| Linux, 1.30.0 | 2.109초, 내려감 | 둘째 뒤 0.006초. 서버 남음 |
| Linux, 2.3.0 none | 2.022초, 내려감 | 둘째 뒤 0.007초. 서버 남음 |
| Linux, 2.3.0 kill | 2.025초, 내려감 | 둘째 뒤 0.006초. 서버 남음 |
| Linux, 2.3.0 watch | 2.030초, 내려감 | 둘째 뒤 0.006초. 3초 뒤 모두 내려감 |

- 이번 회차의 첫 Windows 2.3.0 회차는 시제품이 `os._exit(0xC000013A)`를 불러 C int를 넘는 값의 `OverflowError`로 제대로 끝나지 못했다(한 번이면 서버를 닫았지만 종료 코드가 1이었고, 두 번이면 끝나지 않아 60초에 프로브가 껐다. 두 번의 회차는 표지가 서지 않아 측정 아님으로 세었다). 같은 32비트를 부호 있는 값으로 주게 고친 뒤 다시 돈 것이 위 값이다. 같은 결함이 시제품(`prototype/src/agent_os/channel/cli/interrupt.py`)에도 있어 함께 고쳤다.
- 앞선 회차(두 번째에 `os._exit(130)`, 첫 번째에 `sys.exit(130)`이던 판)는 한 번이면 2.26~2.42초, 두 번이면 둘째 뒤 0.006~0.025초였다. 한 번일 때 이번이 0.2~0.4초 짧은 것은 이번 판이 인터프리터의 마무리를 건너뛰기 때문으로 본다(어림).

### `serve_shutdown.py` — Linux(Docker)

시각은 신호에서 잰 초다(수명 닫기 / 실행 끝 / 프로세스 끝). "남음"은 프로세스가 끝나고 3초 뒤의 판정이다.

| 사례 | 1.30.0 | 2.3.0 none | 2.3.0 kill | 2.3.0 watch |
|---|---|---|---|---|
| `graceful` | 5.189 / 5.194 / 5.433. 서버 남음 | 5.108 / 7.124 / 7.438. 내려감 | 5.200 / 7.226 / 7.386. 내려감 | 5.184 / 7.208 / 7.337. 내려감 |
| `force` | 5.170 / 5.177 / 5.331. 서버 남음 | 5.139 / 7.165 / 7.336. 내려감 | 5.133 / 7.154 / 7.335. 내려감 | 5.194 / 7.216 / 7.385. 내려감 |
| `force_then_interrupt` | 측정 아님(셋째 전에 닫기가 끊겨 끝났다). 서버 남음 | 5.169 / 없음 / 5.684. 남음 | 5.193 / 없음 / 5.685. 남음 | 5.122 / 없음 / 5.634. 내려감 |
| `sigkill` | 0.007초에 끝남. 남음 | 0.007초. 남음 | 0.008초. 남음 | 0.007초. 내려감 |

- `force`의 시각이 `graceful`과 같은 것은 둘째 SIGINT(1초 뒤)가 uvicorn의 강제 종료를 걸었는데도 Python 3.12의 `Server.wait_closed`가 열린 스트림을 기다려 유예 5초가 그대로 든 것으로 본다(어림, uvicorn 0.53.0 `server.py`의 `_wait_tasks_to_complete`를 읽었다). 그 뒤 수명 닫기는 건너뛰었고, serve가 돌아온 뒤 asyncio가 남은 태스크를 취소하고 기다리는 동안 앱의 수명의 `finally`가 돌았다(수명 닫기 시각이 그때다).
- `force_then_interrupt`의 셋째 SIGINT는 수명 닫기가 시작한 0.3초 뒤에 보냈고 그때 실행의 닫기는 끝나지 않았었다(표지). 프로세스는 그 0.2초 안팎 뒤에 닫기를 마치지 못한 채 끝났다.
- 1.30.0의 `force_then_interrupt`는 셋째 신호를 보내기 전에 닫기가 이미 끊겨 실행이 끝나 있었다. 표지가 서지 않아 프로브가 1로 끝났다.

### `full_stack.py`

`aa93cf7b`(이 명세를 쓰는 동안의 origin/main) 위에서 두 OS 모두 같았다. `uv lock`이 mcp를 2.3.0으로 올리고 `mcp-types` 2.3.0·`opentelemetry-api` 1.45.1을 더하며 `langchain-mcp-adapters`·`httpx-sse`·`pydantic-settings`·`python-dotenv`를 뺐다(82개). pyright strict 0건, 타입 우회 검사 0건, import 계약 다섯 유지, `tests/adapters`·`tests/core`·`tests/channel` 571개 통과(1개는 `llm` 표지로 빠졌다).

| 대조군(Linux) | 실패한 테스트 | 기대 |
|---|---|---|
| 런처를 쓰지 않는 어댑터 | 자식을 남기는 서버, 프로세스가 갑자기 죽음 | 같다 |
| 부모를 보지 않는 런처 | 프로세스가 갑자기 죽음 | 같다 |

어댑터 테스트 파일의 테스트마다 걸린 시간(`--durations=0`, 초).

| 테스트 | Windows | Linux |
|---|---|---|
| 도구 호출 도중의 기한 | 7.82 | 5.61 |
| 연결을 연 프로세스가 갑자기 죽음 | 7.87 | 4.27 |
| 연결 안의 예외 | 5.64 | 4.53 |
| 자식을 남기는 서버의 닫기 | 4.29 | 2.37 |
| 도구 호출 도중에 서버가 죽음 | 1.51 | 0.86 |
| 새 닫기 테스트 다섯의 합 | 27.13 | 17.64 |
| 지금 있던 픽스처 테스트 넷(목록, 호출, 실패, 없는 도구) | 2.44~3.30씩 | 0.99~1.03씩 |

- 앞선 회차(`8a2163eb` 위)도 두 OS에서 초록이었다(543개 통과. 지금 538개와 새 다섯). Linux의 첫 회차는 pyright가 내려받은 node가 `libatomic1`이 없어 뜨지 못해(종료 코드 127) `linux_full_stack.sh`가 그것을 먼저 설치하게 고쳤다.
