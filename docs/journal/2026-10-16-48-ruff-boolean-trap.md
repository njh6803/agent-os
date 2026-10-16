# 2026-10-16 (48) ruff FBT 켜기 (대기열 285)

next-session 지시문으로 연 새 세션의 하네스 chore다. `CODING_STANDARDS.md`의 불리언 플래그 인자 금지를 린터 층(ruff FBT)으로
옮기는 열린 대기열 행 285를 한 PR로 닫는다.

> 사용자: "대기열 285(ruff에 불리언 플래그 인자 규칙 FBT를 켜는 열린 행)를 chore 한 PR로 반영한다" (지시문의 시작 프롬프트. 범위는 PR과 병합까지)

## 시작

- **tidy-checkouts.** 루트 main을 `30b9f37b`에서 `d71d8c96`으로 당겼다. 끝이 `origin/main`에 있는 로컬 브랜치
  `worktree-01-runner-notice-expectation` 하나를 지웠다. `skill-check-and-retro-section`은 병합된 PR의 머리와 브랜치 끝이
  달라 다시 사람에게 넘겼다. 나머지 워크트리는 병합된 PR이 없거나, 실행 중인 세션·살아 있는 잠금 pid·작업 디렉터리를 쥔
  `claude.exe`가 있거나, 다시 만들 수 없는 무시된 항목(`.claude/plans/`)이 있어 남겼다.
- **워크트리.** `EnterWorktree`(이름 `ruff-boolean-trap`)로 들어가 지시문의 브랜치를 땄다.
- **번호.** `tools/sibling_overlap.py`가 준 다음 빈 번호 48로 이 일지를 만들었다.

## 어떻게 했나

1. **위반 수.** 켜기 전 `uv run ruff check . --select FBT`는 55곳이었다. 규칙별로 FBT001 44, FBT003 9, FBT002 2이고, 폴더별로
   `src/` 2, `tests/` 25, `tools/` 13, `.scratch/**/probes/` 15였다. 일지 2026-10-16-35가 적은 FBT001 44와 같다.
2. **꼴과 고치는 법.** 넷으로 갈렸고, 판정에서 뺀 자리 없이 모두 고쳤다.
   - 포트 메서드 `write_enabled(kind, name, enabled: bool)`(포트, 어댑터, 가짜 다섯): `*, enabled`로 바꿨다. 호출부는
     `admin/http.py` 하나만 위치로 넘겨 키워드로 고쳤다. 포트는 core이고 `sdk/`·`openapi.json` 밖이라 계약 변경이 아니다.
   - pytest 매개변수화 테스트의 불리언 칸: `*` 뒤로 옮겼다. pytest는 키워드 전용 매개변수에도 이름으로 값을 넣는다.
     파일별 제외(`per-file-ignores`)로 `tests/`를 빼는 안은 테스트 도우미(`_결과`, `_record`, `_repository`)까지 빼므로 버렸다.
   - 도구·프로브·테스트 도우미의 불리언 위치 인자: 키워드 전용으로 바꾸고 호출부를 키워드로 고쳤다.
   - 호출의 `True`/`False` 리터럴(FBT003): 데이터클래스 생성자에는 키워드로 넘겼다. 키워드를 받지 않는 ctypes
     `kernel.OpenProcess`에는 Win32 매개변수 이름을 딴 상수 `_INHERIT_HANDLE = False`로 넘겼다.
3. **확인.** pyright는 `.scratch`를 보지 않아, 고친 프로브 여덟 파일을 경로로 넘겨 따로 돌렸고 오류는 0이었다.
   `session_cost/collect.py`는 모은 결과의 meta에 자기 해시(`collect_sha256`)를 남기는데, 그 값을 대조하는 가드는 없다
   (`model_sweep/sweep.py`는 표시만 한다). 시그니처만 바뀌어 출력은 같다.
4. **`CODING_STANDARDS.md`.** 그 줄을 린터가 막는 범위로 줄이고, 린터가 보지 못하는 판단(키워드 전용으로 지나간 플래그,
   갈래를 고르는 데이터클래스의 불리언 칸)만 남겼다.

## 셀프 리뷰

기점 `d71d8c96`, 커밋 없음, 바뀐 파일 33, 미추적 하나(이 일지). 소스가 바뀌어 두 축 모두 기본 모델로 띄웠다.

- **표준 축.** 확정 위반 없음. 55곳의 수, pytest의 키워드 전용 주입(바뀐 매개변수화 테스트 141개 통과), `_INHERIT_HANDLE`
  주석을 재어 맞다고 했다.
- **명세 축.** 요구 셋은 모두 있고 범위 넘침은 없다. Major 하나, Minor 하나, Info 하나.

고친 것:
- [Major, 명세] 표준 줄의 첫 판 "위치 인자의 불리언은 ruff FBT가 막는다"가 린터 범위보다 넓었다. 주석 없는 매개변수,
  `@override` 메서드, 위치로 넘긴 불리언 식·변수(`tools/run_checks.py`의 `Outcome(check, process.returncode == 0, …)`),
  데이터클래스의 불리언 칸(이 행의 사건 `Boundary.candidate`)을 FBT가 보지 못한다. 표준 축도 같은 자리를 판단 항목으로 냈다.
  새 문장: "ruff FBT는 `bool`로 주석한 위치 매개변수와 호출에 위치로 넘긴 `True`/`False` 리터럴만 막는다. 키워드 전용으로 옮겨
  지나간 플래그(`run(request, *, verbose=True)`)는 함수가 두 가지 일을 한다는 신호라 쪼개고, 갈래를 고르는 데이터클래스의 불리언
  칸은 열거로 둔다. 둘 다 린터가 보지 못한다."
- `tools/run_checks.py`의 남은 `Outcome(...)` 호출도 키워드로 맞췄다.
- [Minor, 명세] ADR 0013 본문의 "지금의 ruff select(E, W, F, I, UP, B, DTZ, TD)"를 "그때의"로 고쳤다. ADR 본문은 살아 있는
  문서다(`docs/constitution/operations.md` 문서 위치).
- [판단, 표준] 표준 줄 끝에 머리 규약의 `자체 승인`을 넣었고, 첫 판이 기대값으로 묶은 "견줄 값" 문장은 새 문장에서 빠졌다.
  대기열 닫힘 칸의 "판단만 남겼다"도 새 줄에 맞췄다.

남긴 것:
- [판단, 표준] `_INHERIT_HANDLE = False`가 "물려준다"로 읽힌다는 이름 지적. 상수는 Win32 매개변수 `bInheritHandle`의 이름을
  딴 것이고 주석이 값의 뜻을 적어 두었다. 불리언 값을 담은 어떤 이름도 같은 모양이라 두었다.
- [판단, 표준] 키워드 전용으로만 바꾼 동작 플래그 넷(`session_cost/collect.py`의 `_scan_record(sub)`·`load_gh(refresh)`,
  `enter_worktree_loading.py`의 `measured(first)`, 테스트 도우미 `_repository(merge_ref)`). 셋은 측정을 남긴 프로브의 코드라
  쪼개면 근거 코드가 바뀌고, 하나는 픽스처의 단계를 고른다. 새 표준 줄이 앞으로의 코드에 적용된다.
- [Info, 명세] `.scratch/harness/probes/tidy_checkouts_mutations.toml`의 변이 원문(`judge_branch(..., contains(root, tip, ops.git))`)이
  이제 코드에 없다. `tools/mutate.py` 독스트링이 옛 프로브의 원문은 코드가 바뀌면 썩어도 된다고 적어 두었다.

## 검사
