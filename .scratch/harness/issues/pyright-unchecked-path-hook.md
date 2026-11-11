# pyright-unchecked-path-hook: pyright가 분석하지 않는 경로를 받으면 "0 errors"가 판정이 아니라고 알린다

**What to build:** Bash 명령이 `pyright`에 파일이나 폴더 인자를 주었는데 그 경로가 pyright가 기본으로 건너뛰는 자리(점으로 시작하는 폴더, `node_modules`, `__pycache__` 아래)에 있으면, 그 경로는 분석되지 않아 출력의 `0 errors`가 판정이 아니라고 알리는 PostToolUse 계기 훅 `tools/hook_pyright_unchecked_path.py`를 더한다. 알림은 사본을 점 없는 폴더(`tests/` 아래)에 두고 `--outputjson`의 `summary.filesAnalyzed`가 0이 아닌지 보라고 말한다. 계기 훅이라 막지 않고(`.claude/rules/tools.md`의 계기·막는 훅 가름), 세션·에이전트마다 한 번 알린다. 등록은 PostToolUse의 `Bash` 묶음이다(PowerShell로 친 `pyright`는 이번에 넓히지 않고 독스트링의 못 보는 것에 적는다).

**대기열 항목의 전제를 고친다.** 대기열 431은 "검사 범위(`[tool.pyright]`의 `include`) 밖이거나 점 디렉터리 아래"라고 적었고 `docs/constitution/operations.md` 환경 규약 상세의 pyright 프로브 항목도 "점 디렉터리와 `include` 밖"이라고 적었다. 이 브랜치에서 pyright 1.1.414(`uv run pyright --outputjson <경로>`, 파일 하나씩 만들어 손으로 봤다)는 `include` 밖이지만 점 없는 폴더인 `docs/_pp/a.py`와 폴더 인자 `docs/_pp`를 분석했고(`filesAnalyzed` 1), 저장소 밖 파일도 분석했다(1). 분석하지 않은 것은 `.scratch/_pp/a.py`와 폴더 인자 `.scratch/_pp`(둘 다 0), `docs/_pp/node_modules/a.py`(0), `docs/_pp/__pycache__/a.py`(0)였다. 그래서 이 훅의 판정은 명시한 경로 인자에 점 폴더·`node_modules`·`__pycache__` 성분이 있는지다. `include` 밖은 알리지 않는다. 같은 줄을 operations.md에서도 고친다. 이 측정은 커밋한 프로브가 아니므로 쟀다고 적지 않았고, 훅 독스트링과 operations.md에도 손으로 봤다고 명령과 함께 적는다.

**대기열:** 431

**Status:** done

## 수용 기준

- [x] 알림이 나는 입력: `pyright`(`uv run pyright`, `python -m pyright`, `.venv`의 `pyright.exe` 포함)에 준 파일·폴더 인자의 프로젝트 루트 기준 경로에 `.`으로 시작하는 성분(`.`과 `..`는 제외), `node_modules`, `__pycache__`가 든 때. 절대 경로는 루트 기준으로 바꿔 본다(워크트리의 절대 경로는 `.claude`를 품지만 루트 기준으로는 아니므로 알리지 않는다). 갈래마다 `tests/tools/` 시험이 있다
- [x] 알리지 않는 입력: 점 없는 경로(`tests/…`, `docs/…`, `src/…`), `pyright` 단독이나 `pyright .`, 리다이렉트 대상(`> .scratch/out.json`)과 옵션 값(`--project`를 쓰면 판정을 건너뛴다), `grep pyright .scratch/x.py`처럼 `pyright`가 명령 낱말이 아닌 명령. 거짓 양성과 거짓 음성 모두 독스트링의 못 보는 것에 적고 시험으로 고정한다
- [x] 세션·에이전트마다 한 번 알리는 표지(`hook_journal_evidence`와 같은 모양)와, 세션을 모르면 호출마다 알리는 길을 시험이 임시 폴더로 본다
- [x] `.claude/settings.json`의 PostToolUse `Bash` 묶음에 래퍼 모양 등록이 있고, `tools/hook_payloads.toml`에 발동 하나(대기열 431의 사건 꼴: `.scratch` 아래 프로브)와 침묵 하나(`tests/` 아래 파일)가 있어 `tools/run_hooks.py`가 통과한다
- [x] `tools/mutate.py`로 판정의 갈래를 하나씩 깨는 변이 표(`.scratch/harness/probes/pyright_unchecked_path_hook_mutations.toml`)를 두고 모두 기대대로 빨갛다
- [x] `docs/constitution/operations.md`의 pyright 프로브 항목을 위 측정대로 고치고 이 훅을 가리킨다. `.claude/rules/tools.md`의 훅 시간 목록(Bash·PowerShell의 PostToolUse 훅 수)에 이 훅을 더한다. 옛 표현("점 디렉터리와 `include` 밖")의 잔존은 살아 있는 문서(operations.md, tools.md)에 0이다. `.scratch/`에서 `include` 밖이 검사 없이 0 errors라고 적은 곳은 프로브 기록 세 폴더 네 자리다(`.scratch/interrupts/probes/README.md`, `.scratch/web-widget/probes/jwt_verify/check_types.py`의 주석, `.scratch/end-user-channel/probes/check_types.py`의 주석과 같은 폴더 `README.md`. `include.{0,6}밖`과 `검사 없이 0 errors`로 Grep해 센 것이라 다른 낱말로 쓴 곳은 더 있을 수 있다). 그때의 프로브 기록이고 쓰는 방법(`tests/` 아래로 복사)은 그대로 맞아 두었다
- [x] `uv run python tools/hook_report.py`의 뺄 후보에 이 훅과 비슷한 것이 없음을 봤다(2026-11-11에 돌렸고 뺄 후보는 `hook_session_web_deps.py` 하나였다)
- [x] 검증 명령이 모두 초록이다(손으로 치는 다섯은 커밋의 pre-commit이 갈음한다. 일지 2026-11-11-1050-pyright-unchecked-path-hook)
