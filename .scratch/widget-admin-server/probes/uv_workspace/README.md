# uv_workspace 프로브

사용자가 설치 묶음을 둘로 나누기로 골라서(명세 "설치 묶음과 패키지와 명령"), 둘째 묶음 `widget-admin`을 uv 워크스페이스의 멤버로 둘 때 검사 도구와 시험과 명령과 이미지 빌드가 서는지 잰다. 무엇을 어떻게 재는지(사본 나무, 갈래, 표지, 쓰임, 못 보는 것)는 `run.py`의 독스트링이 원천이고, 이 파일은 결과와 그 해석을 적는다. 결과는 모두 셋째 실행(2026-11-24, 사본 나무 `C:/project/uvws3`)의 것이고, `run.py`가 찍은 회차 줄과 사본 나무의 `.probe-logs/`에 남은 명령 출력이 원본이다. 그 실행은 측정 29회차, 측정 아님 0회차로 0으로 끝났다.

장난감은 표 하나(`widget_settings`), 공개 경로 하나(`/widget-settings/{site}`), 마이그레이션 `0001` 하나, 시험 하나다. 명세가 정한 표와 경로의 모양을 따르지 않는다. 이 프로브가 재는 것은 묶음 둘이 도구와 빌드에서 서는지이고, 서버의 행동이 아니다.

## 결과

아래에서 "쟀다"는 `run.py`의 회차가 표지를 보고 센 결과다. 표지는 `run.py`의 각 `mark` 호출 앞의 조건이다.

### sync

| 회차 | 설정 | 결과 | 표지 |
|---|---|---|---|
| 대조 | 개발 묶음에 멤버를 넣지 않고 `uv lock` 뒤 `uv sync --frozen` | `widget_admin`을 찾지 못했다(`importlib.util.find_spec`이 `None`) | 두 명령이 0으로 끝나고 찾기 스크립트가 줄을 찍었다 |
| 대조 | 같은 설정에 `uv sync --frozen --all-packages` | 멤버의 `src`에서 찾았다 | 같다 |
| 넣은 판 | 개발 묶음에 멤버를 넣고 `uv lock` | 잠금에 더해진 항목은 `widget-admin 0.0.0` 하나, 빠진 항목 없음, `manifest.members`는 `agent-os`와 `widget-admin` | `uv lock`이 0이고 더해진 항목에 `widget-admin`이 있다 |
| 넣은 판 | `uv lock --check` | 0으로 끝났다 | 출력에 `Resolved`가 있다 |
| 넣은 판 | `uv sync --frozen` | 멤버의 `src`에서 찾았고, `.venv`에 `widget-admin` 명령이 섰다 | 명령이 0이고 찾기 스크립트가 줄을 찍었다 |

결론: 개발 묶음에 멤버를 넣으면 CI와 러너와 README가 치는 `uv sync --frozen` 그대로 멤버가 깔린다. 넣지 않으면 깔리지 않는다. "멤버가 잘못 지어져 깔리지 않는다"는 다른 해석은 같은 설정의 `--all-packages` 갈래가 가른다. 그 갈래에서는 깔렸다.

### tools

| 회차 | 설정 | 결과 | 표지 |
|---|---|---|---|
| 넣은 판 | `ruff check .` | 0 | `All checks passed!` 또는 `Found` |
| 넣은 판 | `ruff format --check .` | 0 | `already formatted` |
| 넣은 판 | `ruff check --no-cache -v` 장난감 시험 하나 | `widget_admin`을 `Known(FirstParty) (SourceMatch("…\widget-admin\src"))`로 판정, import 순서 지적 없음 | `-v`가 찍은 `Categorized 'widget_admin…' as …` 줄 |
| 대조 | 같은 명령, ruff의 `src`에 멤버를 넣지 않음 | `Known(ThirdParty) (NoMatch)`로 판정, `unsorted-imports` 지적 있음 | 같다 |
| 넣은 판 | `pyright --outputjson` | 오류 0 | JSON의 `summary`를 풀었다 |
| 넣은 판 | `pyright --outputjson --pythonplatform Linux` | 오류 0 | 같다 |
| 대조 | pyright의 `extraPaths`를 적지 않음 | 오류 5, 모두 `Stub file not found for "widget_admin…"` | 그 진단이 하나 이상 |
| 대조 | pyright의 `extraPaths`에 멤버의 `src`만 적음 | 오류 269, 모두 `Stub file not found for "agent_os…"` | 같다 |
| 양성 대조 | 멤버에 `value: int = "글"`을 심음 | 그 파일의 `reportAssignmentType`을 잡았다 | 진단이 심은 파일의 `reportAssignmentType`(파일 이름만이 아니라 규칙까지 본다) |
| 대조 | 심은 채로 pyright의 `include`에 멤버를 넣지 않음 | 심은 오류를 잡지 못했다, 오류 0 | JSON의 `summary`를 풀었다(pyright가 돌았다) |
| 넣은 판 | `lint-imports` | 0, `Contracts: 9 kept, 0 broken.` | 집계 줄과 독립 계약의 `KEPT` |
| 양성 대조 | 멤버에 `import agent_os`를 심음 | 1 | 독립 계약의 `BROKEN`과 `widget_admin.planted_import -> agent_os` |
| 양성 대조 | `agent_os`에 `import widget_admin`을 심음 | 1 | 독립 계약의 `BROKEN`과 `agent_os.planted_import -> widget_admin` |
| 넣은 판 | `tools/check_type_escapes.py` | 0건 | 0으로 끝나고 출력이 비었다 |
| 양성 대조 | 멤버에 `Any` 두 줄을 심음 | 그 파일의 줄 2 | 줄 머리가 심은 파일의 경로 |

결론과 갈래.

- ruff의 `src`에 멤버를 넣어야 ruff가 `widget_admin`을 이 저장소의 것으로 본다. 넣은 판과 뺀 대조가 판정 줄의 까닭(`SourceMatch`와 `NoMatch`)까지 갈렸고, 뺀 대조에서만 import 순서 지적이 났다.
- pyright의 `include`에 멤버를 넣어야 멤버의 코드가 검사된다. 뺀 대조에서 pyright가 돌았다는 것(요약을 풀었다)과 심은 오류를 잡지 못했다는 것이 함께 나와, "pyright가 돌지 못했다"는 해석과 갈린다.
- pyright의 `extraPaths`에는 루트의 `src`와 멤버의 `src`를 함께 적어야 한다. 적지 않은 대조는 `widget_admin`만, 멤버만 적은 대조는 `agent_os`만 스텁 없음 진단을 냈다. 두 대조를 함께 보면, pyright는 `extraPaths`가 없을 때는 루트의 `src`를 저절로 제 코드의 자리로 찾고, `extraPaths`를 적으면 적은 자리만 본다. 이 해석은 이 판(1.1.414)과 이 설정에서 세 갈래가 낸 것이고, pyright의 문서와는 대 보지 않았다.
- 독립 계약은 두 방향의 import를 모두 막는다. 양성 대조 둘이 그 계약의 `BROKEN`과 그 import의 줄을 찍었다. 다른 계약이 깨져 1이 났다는 해석은 표지가 계약 이름과 줄을 함께 보아 가른다.
- 타입 우회 검사는 따로 고치지 않아도 멤버를 본다. 양성 대조가 심은 파일의 줄을 잡았다.

### pytest

| 회차 | 결과 | 표지 |
|---|---|---|
| 위젯 시험(`tests/widget_admin`) 홀로 | 시험이 받은 데이터베이스 이름이 `widget_admin_test_`로 시작 | 시험이 찍은 `PROBE-DATABASE` 줄과 `1 passed` |
| 위젯 시험과 `tests/test_migrate_command.py`를 한 실행에 `-n 2` | 0, `13 passed in 166.31s (0:02:46)` | 마지막 줄의 통과 수가 경로마다 `--collect-only`로 모은 시험 수의 합과 같다(위젯 시험 1과 `tests/test_migrate_command.py` 12의 합 13) |
| `tests/test_repo_version.py` | 통과, 잠금의 자기 항목 `agent-os 0.0.0`과 `widget-admin 0.0.0` | `3 passed` |

장난감 시험의 `conftest.py`는 `tests/database.py`의 픽스처 함수에 접두 `widget_admin`과 장난감의 마이그레이션 함수를 넘긴다. 한 실행 회차의 시간은 다른 세션의 실행과 겹친 때의 값이다(둘째 실행에서는 57.24초였다). 판 번호 시험은 지금 판 그대로이고, 멤버의 판을 보는 사례는 아직 없다(명세 "판 번호와 출시"가 더한다).

### command

| 회차 | 결과 | 표지 |
|---|---|---|
| 저장소 밖 임시 폴더에서 `python -m widget_admin.main migrate` | 0 | 출력의 `표를 올렸다` |
| 같은 폴더에서 `widget-admin migrate`(같은 데이터베이스에 두 번째) | 0 | 같다 |

데이터베이스는 `tools/database_for_tests.py create widget_admin`으로 만들고 끝에 `drop`으로 지웠다. 장난감의 `migrate`는 alembic의 `upgrade head`를 부른 뒤 늘 `표를 올렸다`를 찍으므로, 표지는 명령이 그 끝까지 돌았다는 것이고 둘째 회차가 판을 올렸다는 것이 아니다.

### images

| 회차 | 결과 | 표지 |
|---|---|---|
| 위젯 관리 서버 이미지(`images/widget-admin.Dockerfile`, 멤버 하나만 깔고 판 `0.1.0-rc.1`을 넣는다) | 안에 `agent-os` 묶음과 `agent_os` 패키지와 `langchain_core`가 없다. 깔린 묶음 20개, `widget-admin` 판 `0.1.0-rc.1`, 마이그레이션 `0001`, `widget-admin` 명령 있음 | 이미지 안의 파이썬이 찍은 확인 줄 |
| 대조: serve 파이썬 단계를 지금 꼴(루트 `pyproject.toml`만 들인다)로 | 지어지지 않았다. `Failed to parse entry in group \`dev\`: \`widget-admin\``와 `` `widget-admin` references a workspace in `tool.uv.sources` … but is not a workspace member `` | 빌드 출력에 `not a workspace member`가 든 줄 |
| serve 파이썬 단계에 멤버의 `pyproject.toml`을 들이면 | 지어졌다. 안에 `agent-os` 판 `0.1.0-rc.1`, 깔린 묶음 67개, `langchain_core` 있음, `widget-admin` 묶음과 패키지와 명령 없음 | 이미지 안의 파이썬이 찍은 확인 줄 |
| 크기(`docker image inspect`의 `Size`, 10의 6제곱으로 나눴다) | 바탕 `python` 119MB, 위젯 관리 서버 228MB, serve 파이썬 단계 339MB | 셋 다 수가 나왔다 |

serve 쪽 두 회차는 serve 이미지의 파이썬 단계까지만 지은 장난감이고(`images/serve-sync*.Dockerfile`), 실제 `deploy/images/serve.Dockerfile`을 지은 것이 아니다. 위젯 관리 서버 이미지는 표지 파일과 앱 사용자와 상태 확인을 두지 않았고, 이미지를 띄워 서버를 부르지 않았다.

## 실행의 이력과 고친 것

결과를 본 뒤 바꾼 것은 넣은 판의 설정 하나와 탐침 하나다. 판정 기준(표지)은 바꾸지 않았다.

- 첫 시도는 세션 스크래치패드 아래의 사본 나무에서 윈도의 경로 길이 한도(260자)에 걸려 풀지 못했다. 그 뒤로 사본 나무를 `C:/project/uvws<번호>`처럼 짧은 경로에 둔다.
- 첫 실행(`C:/project/uvws1`)의 넣은 판은 pyright의 `extraPaths`를 적지 않아 `widget_admin`의 스텁 없음 진단 5건이 났다. 둘째 실행(`C:/project/uvws2`)은 멤버의 `src`만 적어 `agent_os`의 같은 진단 269건이 났다. 셋째 실행은 둘을 함께 적었고, 앞의 두 설정은 대조 회차로 남겼다.
- 둘째 실행의 ruff 묶음 판정 회차는 측정 아님이었다. 캐시가 맞아 ruff가 그 파일을 다시 판정하지 않았고 판정 줄을 찍지 않았다. 셋째 실행부터 그 회차에 `--no-cache`를 붙였다.
- 실행 사이에 장난감 파일의 import 순서와 줄 길이를 고쳤고, 장난감 앱에서 타입 우회 주석을 지웠다. 이 고침은 표지를 바꾼 것이 아니라, 넣은 판의 검사가 도구 설정이 아닌 장난감의 글 때문에 빨개지지 않게 한 것이다.
- 셋째 실행을 마친 뒤 PR 봇 회차(2026-11-24)가 짚어 표지 셋을 좁히고 로그 한 줄을 뺐다. 양성 대조는 파일 이름에 더해 규칙 `reportAssignmentType`을 보고, 대조 이미지는 `widget-admin`이 든 줄이 아니라 `not a workspace member`가 든 줄을 보며, `-n 2` 회차는 경로마다 모은 시험 수의 합을 통과 수와 맞대고(그 두 번의 `--collect-only`가 늘었다), `database-create`의 표준 출력은 비밀번호가 들어 있어 로그에 싣지 않는다. 좁힌 뒤에는 다시 돌리지 않았다. 대신 잰 실행의 로그가 좁힌 조건을 만족하는지 손으로 봤다. 사본 나무 셋째의 `.probe-logs/18-pyright-planted.log`에 `reportAssignmentType`이 심은 파일의 진단으로 있었고, `37-build-control.log`에 `not a workspace member`가 있었으며, 위젯 시험 하나(`25-pytest-widget.log`의 `1 passed`)와 `uv run pytest --collect-only -q tests/test_migrate_command.py`가 낸 12개의 합이 `26-pytest-both.log`의 `13 passed`와 같았다. 표지를 좁힌 `run.py`가 다시 도는 것은 구현 티켓이 이 프로브를 다시 돌릴 때 처음 본다. 타입 우회 검사 회차의 표지(종료 0과 빈 출력)는 좁히지 않았다. 그 검사기는 정상이면 아무것도 찍지 않고, 같은 사본 나무에서 심은 `Any`를 잡는 양성 대조 회차(`24-escapes-planted.log`)가 따로 있다.

## 재지 못한 것

- CI의 리눅스와 CI가 받는 uv 판. 워크플로가 `setup-uv`에 판을 적지 않았다. 이 PC의 uv는 0.10.8이고, 이미지 안 uv는 0.13.8이다. 잠금은 이 PC의 uv가 지었다.
- pre-commit 러너(`tools/run_checks.py`)를 통째로 도는 것. 도구마다 따로 돌렸다.
- 출시 도구(`tools/release.py`, `tools/release_ci.py`, `deploy/images/docker-bake.hcl`). 돌리지 않았다.
- 읽기 전용 루트에서 실제 위젯 관리 서버가 뜨는 것과 이미지의 실행 단계(표지 파일, uid 10001, 상태 확인). 장난감 이미지는 파이썬 단계까지다.
- 명세가 정한 표와 경로와 답의 모양. 장난감은 그 모양을 따르지 않는다.

## 다시 돌리기

저장소 루트에서 테스트 컨테이너를 띄우고(`docker compose -f compose.test.yaml up -d --wait`) Docker 데몬이 도는 채로 아래를 친다. 넘기는 폴더는 없거나 비어 있어야 하고, 윈도에서는 짧은 경로가 낫다. 프로브는 폴더를 지우지 않으므로 다 본 사본 나무는 손으로 지운다.

```bash
uv run python .scratch/widget-admin-server/probes/uv_workspace/run.py C:/project/uvws4
```

`--sections sync,tools`처럼 갈래를 고를 수 있다. `sync`가 뒤의 갈래가 쓰는 가상 환경을 지으므로 늘 앞에 둔다. 사본 나무는 어느 브랜치에서 돌려도 기준 커밋 `7770ac0c1`(`run.py`의 `BASE_COMMIT`)에서 시작한다. 구현 티켓이 루트 `pyproject.toml`을 고친 뒤에도 고치기 전의 판에서 대조 갈래를 다시 세우려는 것이다. 셋째 실행은 이 상수를 두기 전의 판이 `HEAD`를 풀었고, 그때 `HEAD`가 같은 커밋이었다(이 브랜치는 리뷰 때까지 커밋이 없었고 기준이 그 커밋이다. `git log`와 `git merge-base`를 손으로 봤다).
