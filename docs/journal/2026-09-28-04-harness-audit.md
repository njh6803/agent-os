# 2026-09-28 (04) 하네스 감사와 반영 — 컨텍스트·하네스 엔지니어링 검토, KICKOFF 적합성

사용자가 연 세션이다. 감사는 주 체크아웃에서 읽기 전용으로 했고, 반영은 워크트리 `.claude/worktrees/harness-audit`의
브랜치 `chore/harness-audit`에서 했다. 커밋·PR·병합은 사용자 승인 뒤 이 세션이 했다(아래 "승인 뒤"). 산출물은 셋이다.

- 감사 보고(대화)와 상세 부록(세션 스크래치패드 `harness-audit-2026-09-28.md`, 95건·검증 판정·KICKOFF 유출 88건)
- 반영 diff: 37파일 변경, 10파일 추가. 훅 둘·검사 다섯·테스트 여덟·conftest·계약 하나, 지침·스킬·런북·대기열
- ADR 0018(원칙 IV의 플러그인 경계 판정자. 초안 뒤 같은 세션에서 승인), 헌법 2.5.2

> 사용자: "컨텍스트, 하네스 엔지니어링을 잘하고 있는건지 모르겠어. 현재 프로젝트의 컨텍스트,하네스 엔지니어링을
> 단계적으로 분석하고 검토 후 알려줘. 그리고 KICKOFF.md 파일은 다른 프로젝트에서 사용할 파일인데 현재 프로젝트의 내용이
> 들어가 있는지 확인해주고 다른 프로젝트들을 시작할 때 사용하기에 적합한지 판단해줘."
> 사용자: "다시 시도" (검증자 15개가 모델 한도로 실패한 뒤)
> 사용자: "결과를 바탕으로 개선될 수 있도록 수정해줘"
> 사용자: "병합된 pr확인하고 이어서 진행" (#89·#90이 병합된 뒤. 워크트리를 그 위로 옮기고 대기열 27·29가 닫힌 것을 반영)
> 사용자: "커밋·PR·병합, ADR 0018 승인, 회고 후보 둘 승인"

## 감사

워크플로 하나로 분석가 12명(하네스 8차원, KICKOFF 4관점)을 읽기 전용으로 띄우고, 지적마다 검증자 둘(사실 확인,
이미 알려짐·의도된 설계 여부)이 반박을 시도했다. 지적 95건 중 confirmed 76, disputed 4, refuted 1, Nit 미검증 14.
차원 점수는 구조 축 여섯이 4/5, 교정 루프와 헌법 판정자가 3/5, KICKOFF 넷이 3/5. 가장 반복되는 결함 모양은 "판정자
주장이 사실보다 넓다" — 원칙 IV의 플러그인 절(import-linter 그래프 밖), 원칙 II의 skip 절(장치 없음), `@` 임포트
검사(줄 머리만), operations.md의 "CI에서는 에러로 만든다". 완결성 비평가가 셋을 더했다 — `permissions.deny` 부재,
런북 10단계의 메모리 지시가 저장소가 폐기한 관행이라는 것, 그리고 감사 자체의 부작용(서브에이전트의 저장소 전체 grep
한 번에 `.env`의 키 값이 도구 출력에 실렸다. 값은 어디에도 옮기지 않았고 키 회전은 사용자 판단으로 남겼다).

KICKOFF 판정: 뼈대는 범용이고 (c)·(d) 유출은 54줄/379줄. 이 저장소를 옆에 열어 둔 조건에서만 적합했고 사본 한 장으로는
부족했다 — 교정 루프 원문이 자리표시자, 훅 다섯 중 둘만 이름이 있고 등록 블록 없음, `PATCHED_SKILLS`가 이 저장소의
사본을 박아 새 프로젝트의 첫 커밋이 빨강, 런타임·GitHub·Windows 전제 미표기, CodeRabbit 절이 저장소 문서와 정반대.

## 반영

원칙: 승인이 필요한 것(헌법 문구, 계약, ADR이 필요한 대기열 4·13·17·31·34·36)과 사용자만 할 수 있는 것(`/context`
실측, 키 회전, 워크트리·브랜치 삭제, `npx skills add`)은 손대지 않고, 나머지를 강제력이 가장 높은 층에 넣었다.

- **훅·검사.** `tools/check_instructions.py`에 다섯: 문장 속 `@` 임포트, 임포트된 파일의 형제 상대 경로(대기열 32),
  역방향 센티널, 훅의 텍스트 stdin(대기열 25), 시험 가능한 시그니처. 훅 넷을 바이트 stdin으로. `hook_journal_retro`
  조건을 대기열 28대로. 새 훅 둘 — `hook_git_main_commit`(main 위 커밋 deny, 대기열 15), `hook_bash_gate_pipe`(게이트가
  파이프·체인에 묻히면 경고, 대기열 19·11). `.claude/settings.json`에 둘을 등록하고 `permissions.deny`에 `.env`.
- **아키텍처 테스트·설정.** `tests/test_plugins_boundary.py`(플러그인은 sdk만, ADR 0018),
  `tests/conftest.py`가 skip을 세션 실패로(원칙 II), import-linter에 core→`pathlib`·`os`·`sqlite3` 금지 계약,
  `--strict-markers`. `tests/tools/`에 테스트 여덟 파일(새 검사·훅·commit-msg 경계값·conftest의 pytester 시험).
- **지침.** CLAUDE.md의 사본 문장 넷을 지우고 환경 함정을 정리했다(94줄). rules 넷의 import 경계 열거를 pyproject
  포인터로, 독스트링과 글자 그대로 겹치던 셋을 포인터로, tests.md의 상시 문장 사본 넷 삭제, `rules/tools.md` 신설(훅
  규약, 대기열 12). operations.md에 LLM 테스트 계기(대기열 1), `fix/` 접두사(23), 일지 이름 규약, 리뷰 축 이름의 원천,
  skip 판정자, 권한 거부 문장, 그리고 Claude Code Review 건너뛰기 조건의 정정.
- **스킬·에이전트.** next-session(대기열 2·21·37·39, HEAD 대조, 배치 결정표 행, 워크트리 정리, 다음 절 캐시 금지,
  open-session 없는 환경의 대체 줄), retro 5단계(행 형식, 영구 번호), code-review(대기열 3·20·26), implement(35),
  to-spec(3·30·38)·to-tickets(3·7)에 센티널을 붙여 `PATCHED_SKILLS`가 여섯, spec-reviewer(38), coderabbit-review(좌석).
- **문서.** principles.md의 형제 상대 경로 셋을 전체 경로로(대기열 32, 승인분), 헌법 README 2.5.1(#75·#76 소급 포함),
  CONTEXT.md 포트 포인터, plan.md 매달린 참조, issue-tracker.md 상태 전이, README 트리와 원천 표, PR 템플릿
  (대기열 5·10·14·24), 일지 2026-09-22-11의 재번호 참조 넷에 당시·지금 번호. 대기열 25행에 취소선, 42 새 줄, 머리말에
  영구 번호 규칙. ADR 0018(당시 초안)과 색인. `tools/protection.json`(실제 보호 설정 내보내기).
- **KICKOFF.md.** 서두에 원격·전제 셋·"두 번째 실행이 검증", 3단계에 교정 루프 원문과 지도 열네 행, 7단계를 "파일마다
  바꿀 자리" 목록으로(훅 일곱·등록 블록·`PATCHED_SKILLS`·runtime·retro-queue·spec-reviewer·protection.json), 8단계
  좌석 확인, 9단계 3번의 헌법 원칙 일반화, 10단계 메모리 지시를 저장소 원천으로, 체크리스트에 산출 단계 표기, 부록 A에
  환경 라벨과 새 행 넷, 부록 C(플랜·플랫폼 사실과 확인일). 379줄에서 438줄로 늘었다 — 구멍을 메운 값이고 분리는 다음.
- **메모리.** `agent-os-kickoff-state.md`가 되풀이하던 기전 문단을 포인터 하나로 줄이고 2026-09-27 사고를 훅 독스트링으로
  옮겼다. `sibling-agent-repos.md`의 죽은 위키링크 제거.

## 실제 실행으로 확인한 하네스

훅 일곱을 `PYTHONUTF8` 없는 자식 프로세스로 열네 페이로드에 돌렸다. 발동 여덟, 침묵 여섯이 전부 기대와 같았고 한글
45줄 heredoc 페이로드가 바이트 stdin으로 deny를 냈다. `check_instructions.py`는 고치기 전 실제 저장소에서 다섯을
잡았다(principles.md 상대 경로 셋, 센티널 없는 to-spec·to-tickets) — 새 검사의 빨강을 실제 데이터로 봤다. 이 세션의
heredoc 훅이 56줄 heredoc을 막았고 Write로 돌아갔다. 워크트리 가드가 `git`이 든 복합 Bash 명령 셋을 거부해 단순 명령과
스크립트 파일로 나눴다.

## 셀프 리뷰

두 축(표준·명세) 서브에이전트에 대기열 20의 주장 검증 줄을 처음으로 넣어 돌렸다. 표준 축이 하드 위반 여섯(훅 독스트링의
"못 보는 것" 거짓 둘, 이 diff가 바꾼 CLAUDE.md 문장을 다른 훅이 옛 문구로 인용한 둘, "두 번" 사실 오류, "7회차" 수,
테스트 헬퍼의 한국어 식별자가 새 tools.md 규약과 충돌)과 판단 항목 여섯, 명세 축이 누락 열둘과 오류 일곱을 냈다. 주장 검증은
표준 축 16건 중 9건, 명세 축 20건 중 7건을 틀렸다고 판정했다 — 브리프 한 줄이 넣은 첫 세션에서 틀린 주장 열여섯을 잡았다.

반영한 것: 위 하드 위반 여섯 전부, 오류 일곱 전부(hook_git_main_commit의 사건 서술, next-session의 감시 전제, 헌법 README의
ADR 범위, ADR 0018의 "만", KICKOFF의 수치 둘, tools.md의 "에만", code-review 센티널 회차), 누락 중 일곱(일지 참조 넷 주석,
next-session 대체 줄, 0단계 완료 표시, 순서 원칙 문장, `gh_run_summary.py` 복사 목록, README 원천 표 행, 대기열 20 15회차
구절). `text_stdin_lines`에 `from sys import stdin` 검출과 못 보는 것 절, gate_pipe 함수 분리와 `python -m` 판정,
conftest의 공개 `pytest.TerminalReporter`.

남긴 것과 이유: `.claude/rules/http.md` 22~26행의 독스트링 중복(결정 문장이라 어느 쪽을 원천으로 할지 판단 필요),
`claude_md_problems`의 바이트·긴 줄 경고(pre-commit이 성공 출력을 숨겨 경고 채널이 없다), KICKOFF의 400자 단락 셋과 역사
문장(구조 분리는 다음 세션), check_instructions에 런북 언급 대조 항목(거짓 양성이 많다), 헌법 원칙 IV 문구(ADR 0018 승인
뒤 — 승인은 이 세션에서 났고 아래 "승인 뒤"에 반영했다). 요구 밖으로 들어간 것은 unverified-nit 여섯(`--strict-markers`, 슬라이스 라벨 삭제, 게이트 셈 문구, 일지 이름 규약,
상태 전이, 200줄 문장 삭제)과 완결성 비평가의 셋(`permissions.deny`, 비밀 문단, 부록 A 행)이다. 전부 남겼다.

## 갈린 곳

- **커밋하지 않았다.** 이 저장소의 리듬은 리뷰 뒤 커밋·PR이지만, 사용자 요청이 "수정해줘"라 커밋과 PR은 사용자가 말할
  때로 두었다. 워크트리에 미커밋 상태다.
- **원칙 IV 문구.** 감사 권고는 "테스트를 만들고 문장을 고친다"였다. 문장은 헌법이라 ADR 0018 초안을 두고 승인을 기다린다.
  그동안 operations.md와 sdk.md는 실제 판정자(테스트)를 적어 원천이 둘이다 — 표준 축이 짚었고 승인 뒤 하나가 된다.
  승인은 이 세션 안에서 났다(아래 "승인 뒤").
- **python_stub 훅의 플랫폼 가드.** 감사 권고는 `sys.platform` 가드였다. 맨 python이 어느 OS에서든 `.venv`가 아니라는
  논증으로 가드 대신 독스트링을 고쳤다. 명세 축이 논증은 성립한다고 판정했다.
- **KICKOFF 분리.** 감사가 절 단위 분리와 9·10단계의 스킬 이동을 권했지만, 구멍 메우기를 먼저 하고 분리는 다음 세션으로
  넘겼다. to-tickets 사본에 순서를 두고 9단계는 "사본"이라 표시했다.
- **대기열 40(`PYTHONUTF8` 설정 env).** "반영 전에 실제로 먹는지 잰다"는 조건이 있어 손대지 않았다. 세션 재시작이 필요한
  측정이다.

## 번복하거나 고친 것

- 다른 세션이 PR #89·#90을 병합해 base가 두 커밋 앞섰다. 워크트리를 `origin/main`으로 옮기고 겹치는 파일 일곱을 다시 읽었다.
  `PATCHED_SKILLS`에 grilling이 이미 들어 있었고, 대기열 27·29가 닫혀 있었다.
- 감사 지적 "두 번 main에 들어갔다"를 그대로 훅 독스트링에 옮겼다가 표준 축이 잡았다 — PR #46은 다른 세션의 커밋이 내
  피처 브랜치에 얹힌 반대 방향이었다. 감사 결과도 원천이 아니라 인용이었다.
- 내가 CLAUDE.md의 함정 문구 둘을 고치면서 그 문장을 인용한 훅 독스트링 둘을 두었다. 작업 규약 4의 잔존 grep이 인용까지
  가지 않았다. 대기열 42(따옴표 인용 기계 대조)가 잡을 모양이다.
- 닫힌 수 주장을 여섯 냈다(67개, 약 120곳, 여덟, 39KB, 두 번, 38 중 2). 주장 검증 줄을 브리프에 넣은 리뷰가 전부 잡았다.
- retro-queue.md를 `write_text`로 고쳐 CRLF가 됐다. 대기열 29의 4회차 함정 그대로다. 바이트로 되돌렸다.
- Edit 도구가 일시 오류로 열두 번 거부됐고 같은 내용으로 다시 넣었다.
- 커밋의 pre-commit에서 `test_hook_git_main_commit`의 둘이 실패했다(`uv run pytest`는 초록). git이 워크트리의
  훅 자식에 `GIT_DIR`을 내보내 테스트의 `git init`이 임시 디렉터리 대신 이 저장소를 재초기화했고, 공유
  `.git/config`의 `core.bare`가 true가 되어 주 체크아웃까지 work tree를 잃었다. `tests/conftest.py`가 저장소
  위치 변수를 벗기고 훅도 `GIT_DIR`을 무시한다. 복구 `git config core.bare false`는 자동 모드 분류기가 공유
  자원 수정으로 막아 사용자에게 넘겼다. "검사 도구가 내가 생각하는 것을 실제로 봤는지"의 네 번째다 — 같은
  pytest가 환경에 따라 다른 저장소를 봤다.

## 회고

후보만 낸다. 대기열에는 사용자 승인 뒤 적는다.

1. **[검사] `.env`를 Bash로 읽는 명령을 막는 PreToolUse 훅.** `permissions.deny`는 Read·Edit만 막고 `cat .env`·저장소 전체
   grep은 막지 못한다. 1회차지만 실패가 조용하고(키가 도구 출력에 실린 뒤에야 안다) 패턴이 고정돼 검사다(선례 대기열
   22·25). 명령 위치의 `cat|grep|sed|head|tail|less|rg` 인자에 `.env`가 있으면 deny, `.env.example`은 제외.
2. **[지침] 워크트리 세션의 Bash 가드 함정 한 줄.** 앱이 워크트리 세션에서 `git`이 든 복합 명령(파이프·서브셸·`$(…)`)을
   거부한다. 이 세션에서 세 번 걸렸고 매번 단순 명령이나 스크립트 파일로 나눠 풀었다. `CLAUDE.md` 환경 함정 또는
   operations.md 환경 규약 상세 한 줄.
3. **[근거] 대기열 42에 근거를 더한다.** 같은 PR 안에서 문장을 고치고 그 문장의 인용 둘을 두었다. 리뷰가 잡았지만 기계
   대조가 있었으면 커밋 전에 잡힌다.
4. **[근거] 대기열 20의 효과.** 주장 검증 줄을 두 축에 넣은 첫 세션에서 틀린 주장 열여섯을 잡았다. 20은 닫혔으니 일지에만.
5. **[사용자] 승인·실행이 필요한 것.** ADR 0018 승인(원칙 IV 문구 patch), `/context` 실측(ADR 0004), `.env`의 키 회전,
   잔재 워크트리 둘과 옛 브랜치 여섯 삭제, grill-me의 락 편입(`npx skills add … -s grill-me`), tdd가 부르는
   codebase-design 설치 여부, `skillOverrides`에 플러그인 스킬 끄기 실측, 대기열 40 실측.

**승인(같은 세션).** 사용자가 1·2와 5의 ADR 0018을 승인했다. 1은 대기열 43. 2는 한 문장이라 대기열을
거치지 않고 `CLAUDE.md` 환경 함정의 커밋 메시지 줄에 바로 넣었다. 3·4는 근거 후보라 일지에만 남는다.

## 승인 뒤

- **원칙 IV 문장.** "import-linter가 판정한다"를 "플러그인 경계는 `tests/test_plugins_boundary.py`가, 나머지는
  import-linter가 판정한다"로. ADR 초안과 지난 턴의 "다음"이 적었던 문구("층 경계와 어댑터·프로바이더 금지는
  import-linter가")는 같은 PR에서 더한 core의 파일시스템·DB 계약을 빠뜨리는 열거라 "나머지"로 좁혔다. 이유는
  ADR 0018의 결과 절에. 헌법 2.5.2(판정자만 바뀌어 patch), ADR 0018 accepted, 색인·operations.md·테스트
  독스트링의 "초안"을 지웠다.
- **PR 직전 CLI 축.** `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 돌리지 않았다
  (operations.md 리뷰 파이프라인 2). PR 체크리스트에 그대로 적었다.
- **커밋 하나, PR 하나, squash 병합.** 첫 커밋 시도는 위 번복 절의 pre-commit 실패로 멈췄고, 공유 config를
  사용자가 복구한 뒤 다시 한다. 워크트리라 `git-pr-merge`의 `git checkout main`은 하지 않고
  next-session 1단계(대기열 39)대로 원격 브랜치 삭제와 `git fetch origin`만.

## 검사

`uv run ruff check .`·`ruff format --check .`·`pyright`·`lint-imports`(5 kept)·`pytest -q`(712 passed, 4 deselected)·
`tools/check_instructions.py`·`tools/check_type_escapes.py` 전부 초록. 승인 뒤의 편집과 `GIT_DIR` 누출 수정 뒤에도 같은
일곱을 다시 돌려 초록. 가짜 `GIT_DIR`을 세운 채 그 테스트 파일을 돌려 conftest가 벗기는 것(가짜 저장소가 생기지 않는다)을
봤다. `-m llm`은 돌리지 않았다 — LLM 테스트가 지나는 코드를 건드리지 않았다(`src/`는 `sdk/ids.py` 독스트링 한 곳).

## 다음

- **web-admin 설계 인터뷰**(`/grill-with-docs`)는 그대로 프론티어다(일지 03의 다음).
- 남은 하네스 chore: 40(`PYTHONUTF8` env 실측, 세션 재시작이 필요), 41(ADR 뒤), 42(인용 기계 대조), 43(`.env`를
  Bash로 읽는 명령을 막는 훅). KICKOFF의 절 분리. 사용자만 할 수 있는 것은 위 회고 5(ADR 0018은 끝났다).
