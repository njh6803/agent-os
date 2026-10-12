# 2026-10-12 (10) 보이지 않는 공백·서식 문자 검사와 훅 실행 래퍼의 알림을 세션마다 한 번

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 52·174를 한 PR로 닫는다. 52는 PR #174가 둔 줄 구분 문자
검사·훅과 같은 자리이고, 174는 같은 훅 영역의 실행 래퍼다. 세션은 주 체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를
먼저 돈 뒤 `EnterWorktree(name=invisible-chars-and-launch-notice)`로 들어가 `origin/main`(`67dbb4a`, #174)에서
`chore/invisible-chars-and-launch-notice`를 땄다.

> 사용자: "대기열 52·174를 한 PR로 반영한다(보이지 않는 비 ASCII 공백·서식 문자 검사, 훅 실행 래퍼의 알림을 세션마다 한 번)"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `8fcc2a7`에서 `67dbb4a`로 당겼다. 스킬 파일은 바뀌지 않았다.
- **지우지 못한 것(셋 다 종료 1, 망가뜨린 것 없음).** `review-workflow-guards`와 `rewrap-and-separator-hook`은 다른
  프로세스가 폴더를 쥐고 있었다(WinError 32). `spec-pipeline-and-pytest-ids`는 `.venv` 안의 `.pyd`를 지우다
  막혔다(WinError 5). 등록과 `.git`은 남았다.
- **사람에게 넘긴 것.** 분리 HEAD 넷(`agent-canary-58969f7`, `confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`,
  `unruffled-lalande-9017fa`), prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른
  `skill-check-and-retro-section`, 등록 없는 폴더 여섯(대기열 148). 지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **52: 이웃 검사가 아니라 기존 검사를 넓혔다.** 대기열 행은 이웃 검사로 가면 셋째 사본이 되기 전에 `tools/` 공용 모듈과
  ADR을 먼저 정하라고 했다. 넓히면 사본이 늘지 않아 그 결정이 필요 없다. 먼저 스크래치 탐침으로 추적 파일을 훑었다.
  홀로 선 CR은 0, CRLF 파일도 0이었고, ASCII 밖의 Zs·Cf는 `.py`에 0, 저장소 전체에서는 탐침 결과 JSON 하나
  (`.scratch/interrupts/probes/probe_langgraph_types.2026-09-21.json`)의 줄바꿈 없는 공백 12개뿐이었다. 그래서 `.py`에
  걸어도 지금 저장소가 빨개지지 않는다.
- **보이지 않는 문자는 손으로 고른 목록이 아니라 유니코드 일반 범주로 정의했다.** ASCII 밖의 Zs(공백 구분 문자)와
  Cf(서식 문자)다. 정의가 한 문장이라 독스트링과 코드와 시험이 같은 말을 한다. 시험은 모든 코드 포인트를 한 줄에 하나씩
  둔 글을 훑어 `unicodedata`로 다시 뽑은 집합과 견준다. 홀로 선 CR은 줄 구분 문자 쪽에 넣어 모든 텍스트 파일에서 잡는다.
  사고가 `.md` 표에서 났고, CRLF의 CR은 줄 끝이라 정규식의 뒤보기(`(?!LF)`)로 뺐다. 파일 머리의 BOM은 인코딩 표지라
  `.py`에서도 잡지 않고, 머리 뒤의 U+FEFF는 잡는다.
- **범주를 묻는 횟수를 줄였다.** 첫 판은 비 ASCII 글자마다 범주를 물었다. 옛 판과 첫 판을 같은 추적 파일로 도는 스크래치
  스크립트로 손으로 견주니 0.40~0.42초가 약 1.0초가 되었다. 한글이 많은 `.py` 때문이다. 파일의 서로 다른 글자(`set`)에서
  Zs·Cf를 먼저 골라 그 문자만 정규식으로 찾게 바꿨다. 이 비교는 프로브 `line_separators_scan_time.py`로 남겼고, 프로브로
  다시 잰 값은 옛 판 0.282·0.310초, 글자마다 0.521·0.540초, 지금 판 0.346·0.390초다. 첫 손 비교보다 차이가 작은 것은
  프로브가 판마다 세 번 가운데 가장 짧은 시간을 적기 때문으로 본다(재지 않았다).
- **편집 도구의 사고를 피했다.** 정규식과 시험의 CR·U+0080 이상 문자는 모두 `chr()`로 런타임에 짓는다. 역슬래시-r을
  소스에 쓰면 이 사고가 다시 날 수 있다. 시험의 이스케이프 문자열은 역슬래시를 겹쳐 썼고, 쓰는 동안 훅이 한 번도
  울리지 않았다.
- **훅은 같은 판정을 옮겨 적었다.** 훅은 단독 실행이라 검사를 import하지 않는다(`.claude/rules/tools.md`). 지시문이 짚은
  문자 셋 일치 시험(`test_커밋_전_검사와_같은_세_문자를_본다`)은 상수만 견줬다. 판정을 옮겨 적은 쪽이 갈리는 것을 놓치므로,
  모든 코드 포인트와 홀로 선 CR·CRLF를 담은 글에서 두 쪽이 내는 (줄, 열, 코드 포인트)를 견주게 넓히고 이름을
  `test_커밋_전_검사와_같은_문자를_같은_자리에서_본다`로 바꿨다.
- **174: 표지 파일 하나로 첫 알림을 가렸다.** 열쇠는 세션(`session_id`)·에이전트(`agent_id`)·이벤트·이유의 해시다.
  서브에이전트는 세션 ID가 같아도 컨텍스트가 따로이고, Stop처럼 사용자에게만 가는 이벤트에서 먼저 알렸으면 모델은
  모른다. 표지는 임시 디렉터리의 `agent-os-launch-hook/`에 `O_EXCL`로 만든다. 묻기와 기록을 한 호출로 해야 병렬 도구
  호출의 래퍼 둘이 함께 처음이라고 보지 않는다. 세션을 모르거나 표지를 쓰지 못하면 예전처럼 호출마다 알린다. 표지
  디렉터리 자리에 파일이 있으면 `makedirs`가 `FileExistsError`를 내므로 "이미 알렸다"와 따로 잡는다. 러너의 알림 판정은
  세션 없는 페이로드라 커밋마다 같은 출력을 본다. 페이로드는 한 번만 읽어 알림과 열쇠가 함께 쓴다(`payload_strings`).

## 바꾼 것

- `tools/check_line_separators.py`와 `tests/tools/test_check_line_separators.py`: 홀로 선 CR, `.py`의 Zs·Cf.
- `tools/hook_line_separators.py`와 `tests/tools/test_hook_line_separators.py`: 같은 판정, 일치 시험.
- `tools/launch_hook.py`와 `tests/tools/test_launch_hook.py`: 세션마다 한 번.
- `tools/hook_payloads.toml`의 사례 넷(줄바꿈 없는 공백 `.py` 발동, 전각 공백 `.md` 침묵, 홀로 선 CR `.md` 발동, CRLF
  침묵)과 `tools/run_hooks.py`의 자리표시자 `${INVISIBLE_DIR}`.
- `.pre-commit-config.yaml`의 검사 이름, `KICKOFF.md`의 래퍼·훅·검사 항목, `.claude/rules/tools.md`의 래퍼 문장과 비용 줄.
- 프로브: `line_separators_scan_time.py`(새로), 변이 표 셋(`md_checks`·`line_separators_hook`·`launch_hook`), README 행 넷.
- `.scratch/retro-queue.md`: 52·174 닫힘.
- `docs/constitution/operations.md`는 고치지 않았다. ADR 뒤에 쓰는 문서이고, 그 안의 "줄 구분 문자 검사(대기열 22)"는
  그대로 참이다.

## 잔존 grep

"세 문자만", "다른 보이지 않는 문자", "U+2028·U+2029·U+0085"(검사 설명), "호출마다 되풀이", "매처의 호출마다",
"상태를 두지 않는다", 옛 시험 이름을 살아 있는 문서에서 찾았다. 남은 것은 새 문장과 닫힌 대기열 행, 일지의 과거형뿐이다.

## 검사

- 변이: 반영 전 판에서 `line_separators_hook_mutations.toml` 열여덟(더한 것 일곱), `launch_hook_mutations.toml` 서른다섯
  (더한 것 일곱, 원문을 고친 것 둘), `md_checks_mutations.toml` 서른여섯(더한 것 여덟, 원문을 고친 것 하나)이 모두
  기대대로였다. 새 변이는 겨눈 시험에서 빨갰다. 셀프 리뷰 반영 뒤 셋의 원문 확인(`--check`)이 초록이었다.
- 프로브: `line_separators_scan_time.py` 두 번(위 수). `line_separators_hook_time.sh`는 233~305ms였다. 같은 때 옛 훅을
  `tools/`에 잠시 두고 번갈아 손으로 재 보니 옛 판 210~243ms, 새 판 211~245ms(한 번 337ms)로 갈리지 않았다.
- 훅 러너: 페이로드 71건, 어긋남 0, 래퍼 알림 5건 어긋남 0.
- 검증 명령: `ruff check`·`ruff format --check`, `pyright` 0 errors, `lint-imports` 5 kept, `pnpm -C web verify`(28파일
  356개), 지침 검사, 타입 우회 검사가 초록이었다. `uv run pytest -q`는 셀프 리뷰 전 1944 passed(7 deselected)였다. 새
  프로브는 추적 전이라 줄 구분 문자 검사에 이름으로 넘겨 따로 돌렸다. 판정 명령은 파이프 없이 돌리고 로그 파일로 봤다.
- 워크트리라 `pnpm -C web install --frozen-lockfile --offline`을 먼저 쳤다.

## 셀프 리뷰

`/code-review`(기준 `67dbb4a`, 수정 16·미추적 1, 커밋 0). 두 축 모두 Critical·Major가 없었다. 표준 축은 Minor 다섯·Nit
여럿·냄새 셋, 명세 축은 Minor 셋·Nit 셋이었고 둘이 겹친 것이 셋이다.

- **고친 것.**
  - 둘 다: 검사의 "못 보는 것"이 "탭 밖의 C0·C1 제어 문자"라 적었는데 CR(C0)과 U+0085(C1)는 이 검사가 잡는다.
    "탭·개행·CR·U+0085 밖의 Cc"로 고치고, 그 주장과 U+FE0F(Mn)는 모든 코드 포인트를 훑는 등식이 고정한다고 적었다.
  - 둘 다: `MODEL_SUFFIX`의 "이 알림은 이 세션에서 다시 내지 않는다"는 세션을 모르거나 표지를 쓰지 못할 때 거짓이다.
    "세션을 알면"을 붙였다.
  - 둘 다: KICKOFF의 래퍼 문장이 열쇠에서 훅을 뺐다. "세션·에이전트·이벤트·훅마다"로 고쳤다.
  - 표준: `.PY`를 못 본다는 주장을 재는 것이 없었다(대기열 10). 시험에 단언을 더했다.
  - 표준: 손으로 잰 옛 판·새 판 비교에 명령이 없었다(issue-tracker의 근거 절). 프로브 README 행에 명령을 적었다.
  - 표준 Nit: `notice_key` 독스트링이 이유에 늘 `tools/` 경로가 든다고 했지만 인자 오류의 이유에는 없다. KICKOFF는 두
    프로젝트가 섞이지 않는 까닭을 경로로 들었는데 실제로 가르는 것은 세션 ID다. 둘 다 고쳤다.
  - 표준 Nit: 훅 독스트링의 "두 쪽이 갈리면 테스트가 모든 코드 포인트로 잡는다"는 디코드 길과 문자 이름을 견주지 않는다.
    견주는 것(문자와 자리)과 각자 보는 것을 갈라 적었다. 테스트 이름에 든 함수명(`test_main_은_…`)을 뺐다.
  - 표준 냄새: 훅의 `marks_in`은 유니코드 Mark 범주와 헷갈려 `flagged_in`으로 바꿨다. 시험의 페이로드를 손으로 짓던
    자리를 `_페이로드`로 모았다.
  - 명세 Minor: CR의 페이로드 사례가 없었다. 홀로 선 CR이 든 `.md` 표(발동)와 CRLF(침묵)를 더했다.
  - 명세 Minor: 이 일지를 06으로 인용했는데 main(#178)에 `2026-10-12-06`이 이미 있었다. 07로 옮기고 인용 넷을 고쳤다. 커밋 직전 `tools/sibling_overlap.py`가 형제 워크트리(`admin-style-spec`)의 07을 알려 그 도구의 "옮길 번호"대로 10으로 한 번 더 옮겼다.
  - 명세 Nit: 대기열 두 행의 승인 기록을 닫힘 문구가 덮었다. 선례(158행)대로 승인 뒤에 닫힘을 붙였다.
- **남긴 것.** `claim_first_notice`의 CQS(표준 Nit)는 `O_EXCL` 하나가 묻기와 기록을 겸해야 병렬 호출이 함께 처음이 되지
  않는다는 근거를 독스트링에 둔다. `payload_strings`가 `.items()`의 AttributeError로 객체가 아닌 페이로드를 가르는 것(Nit)은
  고치기 전 `notice`의 모양을 옮긴 것이다. `invisibles_in`이 시험에서만 불리는 것(냄새)은 정의를 시험하는 표면이라 두었다가,
  PR 리뷰가 다시 짚어 걷어 냈다(아래 PR 리뷰 반영 절).
- **다시 돌린 것.** 위 검증 명령, 훅 러너(71건 어긋남 0), 변이 표 셋의 원문 확인이 초록이었다. `uv run pytest -q`는
  1944 passed(7 deselected)였다. 반영은 시험 하나의 이름을 바꾸고 단언을 더한 것이라 시험 수는 같다.

## main 합치기

커밋(`ec17788`) 뒤 origin/main(`02b21d0`, #176·#178)을 합쳤다. 프로브 README에서 글자 충돌이 났다. main 쪽은 이
브랜치가 고친 두 행의 옛 판과 새 `claude_md_parent.py` 행이라, 이 브랜치의 세 행 뒤에 그 행을 붙였다. main이 새로 세운
규약은 둘(PR 템플릿의 `.github/` 줄, 카나리아의 서브에이전트 갈래)이고 이 PR에 닿지 않는다. 합친 커밋(`a9a328e`)의
pre-commit이 모두 초록이었다.

## PR 직전 보안·버그·성능 축

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 대체 둘을 돌렸다.

- **보안(`/security-review`).** 발견이 없었다. 기각한 후보 가운데 가장 가까운 것은 공유 임시 디렉터리의 표지
  파일(신뢰도 2)이다. 파일 이름이 해시 16진 64자이고 `O_EXCL`은 심볼릭 링크를 따라가지 않으며, 쓰지 못하면 알림이 늘어나는
  쪽으로 실패한다. `.py`의 Cf를 잡는 것은 방향 제어 문자(Trojan Source)를 잡는 범위를 넓힌다고도 적었다.
- **버그·성능(`bug-perf-review`).** Critical·Major 없이 유효 셋(Minor 하나·Nit 둘), 오탐 아홉이었다. 도구 호출을 마흔 번에서
  멈추라고 적어 넘겼고 서른일곱 번에 보고했다(대기열 169).
  - 고친 것(Minor): `tempfile.gettempdir()`가 `try` 밖이라, 쓸 수 있는 임시 디렉터리 후보가 하나도 없으면
    FileNotFoundError로 래퍼가 1로 끝나 알림이 한 번도 나가지 않았다. 리뷰어가 후보를 없는 경로로 바꿔 손으로 재현했다.
    시험을 먼저 빨갛게 하고 `try` 안으로 옮겼으며, 변이 하나를 더해 그 시험이 잡는 것을 봤다.
  - 남긴 것(Nit 둘): 훅 파일이 없는 길이 `tempfile`을 import해 호출마다 약 22ms를 더한다(리뷰어가 한 번 쟀다). 훅이 꺼진
    저하 경로에서만 일어난다. 매치가 아주 많은 파일(홀로 선 CR 100만 개)에서 검사와 훅이 목록 전체를 짓는다. 실제로 드물다.
  - 오탐으로 둔 것 가운데 셋을 적는다. 리뷰어가 무작위 문자열 약 6만 개로 줄·열 계산을 순진한 구현과 대조해 불일치가 0이었다.
    병렬 호출의 `O_EXCL`이 원자적이다. 시그니처를 바꾼 `problems_in`의 호출부는 하나다.

## PR 리뷰 반영

PR [njh6803/agent-os#179](https://github.com/njh6803/agent-os/pull/179). 첫 푸시(`ea7d602`)에서 CI 일곱이 초록이었다.

> 사용자: "CI 끝났어"

CodeRabbit은 요청 뒤 `02b21d0..ea7d602`(그때의 HEAD)를 보고 지적이 없었다("No actionable comments"). 그 시간의 포함 리뷰
한도를 다 썼다고 적었다. claude-review 1회차는 Critical·Major 없이 Minor 둘·Nit 둘이었다. 이 봇의 첫 리뷰라 지적마다
판단했다.

- 고친 것(Minor): `invisibles_in`이 시험에서만 불린다. 셀프 리뷰 표준 축도 같은 것을 짚었다. 함수를 걷어 내고 시험 넷이
  실제 경로인 `problems_in(…, ".py")`를 거치게 했다. 정의 시험은 `.py`와 `.md` 두 모드를 함께 견주게 됐고, 스윕 글에서
  NUL을 뺐다(이진 판정). 검사 변이 표 서른여섯을 다시 돌려 모두 기대대로였다.
- 그대로 둔 것(이유는 PR 코멘트에): `claim_first_notice`의 CQS(Minor)는 `O_EXCL` 하나가 묻기와 기록을 겸해야 병렬 호출이
  함께 처음이 되지 않는다. `payload_strings`의 AttributeError(Nit)는 `isinstance(data, dict)`로 좁히면 pyright strict가
  원소를 Unknown으로 봐 우회 없이는 지나지 못한다. `tests/` 아래 임시 프로브(`object`로 받아 `isinstance`로 좁히고 키·값도
  `isinstance`로 거른 판)를 pyright 1.1.414에 손으로 물으니 `data.items()`의 키와 값이 `reportUnknownVariableType`이었고,
  프로브는 지웠다(일지 2026-10-12-05에서도 같은 일을 겪었다). 힌트를 `" U+"` 포함으로
  가르는 것(Nit)은 이 PR 전부터의 코드다.
- CodeRabbit은 한도를 다 썼고 이 반영은 시험 정리라 다시 요청하지 않았다.
