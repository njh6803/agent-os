# 2026-10-14 (02) Claude 세션의 uv 를 복사 링크로 바꾼다(대기열 217)

## 계기

대기열 217. `tidy-checkouts`의 판정 3이 병합된 워크트리 대부분을 다른 워크트리의 파이썬·node가 올린 모듈 때문에 남겼다.
uv가 `.venv`를 캐시에서 하드링크로 채워서라는 어림을 앞 세션이 쟀고, 반영 방식은 사용자가 골랐다.

> 사용자: (지시문의 시작 프롬프트) ".scratch/retro-queue.md의 대기열 217을 반영하는 하네스 chore를 잇는다. 측정은
> 끝났고 반영 방식은 사용자가 골랐다"

## 앞 세션에서 넘겨받은 기록

앞 세션(같은 브랜치)은 일지를 쓰지 않고 지시문에 상태를 넘겼다. 그 세션에서만 알 수 있던 것을 여기 옮긴다.

- 측정: 프로브 `.scratch/harness/probes/venv_link_mode.py`를 세 번 돌렸다(2026-10-13, 파이썬 3.12.10, uv 0.10.8).
  하드링크 `.venv`는 다른 `.venv`의 파이썬이 올린 `pydantic_core`의 `.pyd`(링크 수 74~78)로 `holders_in`에
  잡히고 지우기가 `WinError 5`로 막혔다. 복사 `.venv`는 세 번 모두 빈 목록이었고 지우기가 지났다. 복사
  `.venv` 자신에서 띄운 파이썬은 잡혔다(양성 대조). 첫 실행은 copy-self가 지운 `.pyd`를 다시 채우지 못해
  실패했고 측정에서 뺐다.
- 비용: `uv sync` 하드링크 11~22초 대 복사 105~148초(백신 검사 때문이라는 것은 어림), 워크트리마다 파일
  10780개 146.8MiB. 워크트리 `.venv`는 65개, C: 여유는 360GB였다.
- 결정: 사용자가 AskUserQuestion에서 "Claude 세션만 copy"를 골랐다. `pyproject.toml`에 두어 모든 uv에 거는
  안과 기록만 하는 안은 기각됐다.
- 217의 회차로 셀 자료: 앞 세션 첫 턴의 tidy judge에서 모듈 때문에 남은 워크트리가 24개였다(pid 46968·
  44880·53228). 그 앞 judge에서는 python 일곱과 node 35612, esbuild 2676·55752였다.

## 한 일

- `.claude/settings.json`의 `env`에 `UV_LINK_MODE=copy`를 더했다.
- `docs/constitution/operations.md` 환경 규약 상세에 그 항목과, 새 워크트리의 첫 uv 실행이 2분을 넘길 수 있어
  `timeout` 600000이나 백그라운드로 친다는 것, pnpm `node_modules`는 그대로 하드링크라는 것을 적었다. 헌법 판
  3.0.34.
- `.claude/skills/implement/SKILL.md` 첫 문단의 "새 워크트리에 들어가면 먼저 `uv sync`…를 친다" 바로 뒤에 시간
  제한 구절을 더했다. 그 명령을 치는 자리가 그 스킬이라서다. 지시문은 operations.md만 들었는데, 그곳은 명령을
  치는 순간에 읽히지 않는다.
- `tools/tidy_checkouts.py` 독스트링 판정 3의 하드링크 문단과 판정 4의 4("`.venv` 가 하드링크라")를 고쳤다.
  판정 코드는 바꾸지 않았다. 기존 `.venv`와 사용자 터미널의 uv, pnpm은 그대로 하드링크라 판정 3이 계속 봐야
  한다.
- 프로브 README에 `venv_link_mode.py` 행, 카나리아 명세 `implement_uv_sync_timeout.toml`을 더하고 대기열 217을
  닫았다.

## 잰 것

### 설정 env가 Bash와 그 아래 uv에 닿는지(손으로 봤다)

워크트리 세션은 주 체크아웃의 settings를 읽어 이 세션에서는 볼 수 없다. 워크트리와 주 체크아웃을 작업
디렉터리로 `claude -p`(Haiku, `--allowedTools Bash`)를 띄워 `echo "BASH=[$UV_LINK_MODE]"`와 `uv run --no-sync
python`의 `os.environ`을 찍게 하고, stream-json의 `tool_result`에서 표지를 뽑았다. 워크트리는 `BASH=[copy]`
`PY=[copy]`, 주 체크아웃(대조)은 `BASH=[]` `PY=[]`였다. 첫 판은 명령이 결과를 스크래치의 파일에 쓰게 했는데
자식 세션의 자동 모드 분류기가 두 번 모두 거부했다(한 번은 사유 `Credential Materialization`). 그래서 파일 대신
도구 결과를 판정 근거로 바꿨다. pre-commit은 Bash가 띄운 git의 자식이라 물려받는다고 보고 따로 재지 않았다.

### 환경 변수만으로 uv sync가 복사로 채우는지(손으로 봤다)

프로브는 `--link-mode` 플래그로 쟀으므로, 플래그 없이 `UV_LINK_MODE`만 둔 `uv sync --frozen`을 임시
`UV_PROJECT_ENVIRONMENT`에 한 번씩 쳤다. `hardlink`는 24.9초에 `.pyd` 링크 수 77, `copy`는 93.9초에 1이었다.

### 카나리아

`implement_uv_sync_timeout.toml`. 첫 판은 실험군 1/3이 "없음"으로 답해 실패 1, "없음" 섞인 통과 1이었다. 질문이
다음 문장이 시간 제한을 말하지 않으면 "없음"이라 답하라는 조건부 판단을 시켜서다. 이어지는 두 문장을 판단 없이
옮기게 고친 둘째 판은 통과 4(claude 2.1.296, 갈래 모두 `5f72cdbb`).

### 셀프 리뷰가 부른 측정 둘(손으로 봤다)

- git이 커밋 훅에 값을 넘기는지: 임시 저장소의 `pre-commit` 훅이 `UV_LINK_MODE`를 찍게 하고 값을 둔 커밋과 뺀 커밋을
  쳤다. `HOOK=[copy]`와 `HOOK=[]`였다. 위의 `claude -p` 확인과 이어 pre-commit 경로를 덮는다. 둘을 한 번에 잰
  것은 아니다.
- 끊긴 복사 동기화: 임시 `UV_PROJECT_ENVIRONMENT`에 `UV_LINK_MODE=copy uv sync --frozen`을 띄우고 30초에
  `taskkill /T /F`로 죽였다(파일 7214개가 남았다). 다시 친 sync는 53.6초에 종료 0, `uv sync --check`는 "Would
  make no changes", `pydantic`·`fastapi`·`langchain_core`·`pytest` import가 됐다.

## 셀프 리뷰

`/code-review`, 기점 `5f72cdbb`, 수정 7개, 미추적 3개, 커밋 0. 표준 축은 기본 모델(`tools/` 파일이 들어서), 명세 축은
지시문과 대기열 217 행을 명세로 썼다.

표준 축: 하드 위반 셋(테스트 독스트링 두 곳의 "하드링크로 채워져" 잔존, "다시 만들 때까지 하드링크로 남는다"의
반례(lock이 바뀌면 바뀐 패키지만 복사로 다시 깐다, `--reinstall`), 2분 제한이 `CLAUDE.md` 환경 함정에 없어 `implement`를
거치지 않는 chore 세션의 첫 `uv run`이나 커밋이 경고 없이 걸린다), 판단 여섯(pre-commit 물려받기를 단정문으로
적었다, 프로브가 찍지 않는 uv 판, 수치의 출처, 프로브가 env가 아니라 플래그만 잰다, 같은 수치 묶음이 다섯 곳에
반복된다, 일지의 "다음"이 비었다).

명세 축: 빠진 것 셋(pre-commit 경로를 재지 않았다, 데스크톱 세션 확인은 병합 뒤에야 되는데 적힌 곳이 없다, pnpm 후보가
일지 한 문장뿐이다), 범위 넘침 없음(implement 구절과 판 올림은 정당하다고 봤다), 틀려 보이는 것 여섯(같은 잔존,
같은 2분 제한, "앞의 것"이 가리키는 것이 모호하다, "Claude 세션이 치는 uv는" 보편 주장에 병합 전 워크트리 세션과
클라우드라는 반례, ADR 0027의 `UV_LINK_MODE=copy` uvx 실패 기록이 빠졌다, 클라우드 SessionStart의 복사 동기화
시간을 재지 않았다).

고친 것:
- 테스트 독스트링 두 곳에 "기본으로"를 넣었다. 프로브 `module_holder.py`·`worktree_occupancy.py`의 같은 문장은 그
  측정 때의 맥락이고 uv의 기본 동작으로 맞아 두었다.
- operations.md와 `tidy_checkouts.py` 독스트링의 "다시 만들 때까지"·"만든 `.venv`"를 패키지를 깔 때 정해진다는
  말로 고쳤다.
- pre-commit 경로를 쟀다(위). 단정문을 손으로 본 두 사실과 그 이음으로 나눠 적었다.
- 2분 제한: 끊긴 동기화가 다시 치면 회복되는 것을 쟀다(위). 실패가 보이고(시간 초과 메시지) 다시 치면 이어 까므로
  매 세션 실리는 `CLAUDE.md`에 올리지 않고 operations.md에 회복과 pre-commit 갈래를 적었다. 남은 비용은 한 번의
  헛수고다. retro 후보로 넘긴다(아래 "다음").
- "앞의 것"을 셋으로 나눠 각각 무엇으로 봤는지 적었다. 보편 주장을 "이 설정을 읽은 Claude 세션"으로 좁히고 병합
  전 워크트리 세션과 클라우드(재지 않았다)를 적었다. ADR 0027의 실패 한 번을 적었다.
- 프로브 README의 uv 판을 손으로 본 값이라고 적었다.

남긴 것과 이유:
- 같은 수치 묶음의 반복: 원천은 프로브 README 행이고 다른 곳은 그것을 인용하는 이 저장소의 관행이다(대기열 닫힘
  칸, 일지). operations.md와 독스트링에서 수치를 걷어 내면 근거 문장이 프로브만 가리키게 되는데, 그 정리는 이 PR의
  범위를 넘는다.
- 클라우드 SessionStart의 복사 동기화 시간: 이 PC에서 잴 수 없다. operations.md에 재지 않았다고 적었다.
- 프로브가 env 경로를 재지 않는 것: 손으로 본 한 번(링크 수 1 대 77)으로 두고 그렇게 적었다.

다시 돌린 명령: 커밋의 pre-commit으로 갈음한다(결과는 커밋 뒤 아래 "검사"에 적는다).

## PR 직전

CodeRabbit CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌지 못해 대체 둘을 나란히 돌렸다.

- `/security-review`: 발견 없음. 바뀐 코드는 env 한 줄, 리스트 인자로만 띄우고 자기 임시 폴더만 지우는 프로브, 독스트링이다.
- `bug-perf-review`: 유효 1, 보류 2, 오탐 4, Critical·Major 없음.
  - 유효(Minor): 프로브가 첫 자식의 `spawn` 뒤 `relative_to`를 `try` 밖에서 불러, 거기서 예외가 나면 `.pyd`를 쥔 자식이
    stdin을 기다린 채 남고 임시 폴더가 알림 없이 남는다. `relative_to`를 `try` 안으로 옮겼다. `spawn` 자신이 실패하면
    자식은 이미 끝난 뒤라 그대로 뒀다.
  - 보류(Minor): Bash의 시간 제한에 걸린 명령이 죽지 않고 백그라운드로 넘어가면, 다시 친 uv와 같은 `.venv`에 함께 깐다.
    회복 측정은 프로세스 트리를 죽인 경우다. operations.md에 넘어간 작업이 끝난 뒤에 다시 치라고 적고 함께 까는 경우는
    재지 않았다고 적었다.
  - 보류(Minor): 클라우드 SessionStart의 `uv run pre-commit install`이 복사로 `.venv`를 채운다. 리눅스에서 재지
    않았다. 아래 "다음"에 병합 뒤 확인으로 둔다.
  - 오탐: hard 갈래가 하드링크인지 단언하지 않는다(pid 단언이 거짓 통과를 막는다), copy의 빈 목록이 흔들린다, 지운
    `.pyd`를 복구하지 않는다(`--reinstall-package`가 한다), 런처 때문에 pid가 틀린다(자식이 `os.getpid()`를 찍는다).

## 남은 위험

- pnpm의 `node_modules`도 하드링크이고 이 반영으로 풀리지 않는다. 앞선 judge 한 번에서 `node.exe`·`esbuild.exe`가
  쥔 워크트리가 있었다. pnpm의 `package-import-method`를 `copy`로 두는 길이 있지만 재지 않았다(대기열 258).
- 이미 있는 워크트리 `.venv` 65개는 다시 만들 때까지 하드링크다. 정리 효과는 워크트리가 새것으로 바뀌는 만큼
  천천히 난다.
- 사용자 터미널의 uv가 만든 `.venv`는 이 밖이다.

## 검사

`uv run pytest -q` 2663 passed, 7 deselected. `ruff check`, `ruff format --check`, `pyright`(0 errors),
`lint-imports` 모두 종료 0. `pnpm -C web verify` 종료 0. 셀프 리뷰 반영 뒤에는 커밋 `1617cb3d`의 pre-commit으로
갈음했다. ruff 둘, 병렬 검사(zizmor, check-instructions, lint-imports, check-type-escapes, pyright, run-hooks,
web-verify, pytest), 표·줄 구분 문자, 커밋 메시지가 Passed였다. 변이 표 확인은 커밋에 표가 없어 Skipped였다(이
PR은 변이 표를 고치지 않는다). 인용 대조가 이 일지의 줄 하나를 짚어 따옴표를 뗐다.

## 회고

후보 다섯. 승인 하나, 기각 넷, 넘김 없음.

1. pnpm `node_modules`의 하드링크 — 승인. 사건: 앞 세션의 judge 한 번에서 `node.exe`(35612)와 `esbuild.exe`(2676·
   55752)가 병합된 워크트리를 쥐었다. 층: 설정(pnpm의 `package-import-method`)이고 먼저 잰다. 되돌림: PR 하나. 이
   세션에서 반영하지 않아 대기열 258.
2. `implement`를 거치지 않는 세션의 첫 uv 실행이 Bash 120초 제한에 걸린다 — 기각. 이 세션에서 나지 않았고(이
   워크트리는 이미 `.venv`가 있었다), 걸려도 다시 치면 이어 깐다는 것을 쟀다. 실제로 나면 그때 `CLAUDE.md` 환경
   함정이나 훅을 본다.
3. 자식 `claude -p`의 자동 모드 분류기가 결과를 파일에 쓰는 탐침을 두 번 거부했다 — 기각. stream-json의 도구
   결과로 판정하는 길은 카나리아 러너가 이미 쓰고, 이 세션도 그리로 바꿔 한 번에 지났다.
4. 카나리아 첫 판의 조건부 "없음" 질문으로 실험군 한 회차가 실패했다 — 기각. operations.md 카나리아 항목이 질문의
   자리를 고쳐 다시 돌리라고 이미 정하고, 그대로 따랐다.
5. 잔존 grep에서 본 테스트 독스트링 두 곳을 고치지 않았다 — 기각. 작업 규약 4가 있고 셀프 리뷰 두 축이 모두 잡았다.

## 다음

- 병합하고 주 체크아웃을 당긴 뒤 처음 여는 데스크톱 앱 세션에서 `echo "$UV_LINK_MODE"`가 `copy`인지 본다. 이
  세션은 `claude -p`로만 봤다.
- 다음 클라우드 세션의 시작에서 SessionStart 훅(`hook_session_web_deps`)이 제한 안에 끝나는지 본다. 복사 동기화가
  더해졌다.
- pnpm 쪽은 대기열 258.
