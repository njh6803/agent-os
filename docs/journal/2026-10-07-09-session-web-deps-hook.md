# 2026-10-07 (09) 클라우드 세션이 시작될 때 web 의존성을 까는 SessionStart 훅

일지 2026-10-07-08의 세션이 이어서 했다. 같은 클라우드 세션, 같은 브랜치 `claude/funny-planck-itf28j`다.

## 계기

일지 08의 답 끝에서 대기열 138의 남은 일(`pnpm -C web install --frozen-lockfile`을 새 세션마다 두는 자리)을
SessionStart 훅으로 할지 물었다.

> 사용자: "원해"

## 어떻게 했나

- **훅.** `tools/hook_session_web_deps.py`. 판정은 셋이다. 환경 변수 `CLAUDE_CODE_REMOTE`가 `true`이고, 페이로드의
  `source`가 `startup`·`resume`이고, 프로젝트 루트 아래 `web/pnpm-lock.yaml`이 있을 때만 `shutil.which`로 찾은 pnpm을
  띄운다. 루트는 `CLAUDE_PROJECT_DIR`이 먼저이고, 없으면 페이로드의 `cwd`다. 공식 문서(code.claude.com의
  cloud-environments, 2026-10-07에 읽었다)는 설정 스크립트를 VM을 갖추는 자리로, 프로젝트 설치를 SessionStart 훅의
  자리로 가르고, 클라우드 세션에서만 깔려면 `CLAUDE_CODE_REMOTE`가 `true`인지 보는 예를 든다. 성공하면 아무것도 내지
  않는다. 실패, pnpm 없음, 시간 초과(240초, 등록의 300초보다 짧고 테스트가 대조한다)는 모델에게 `additionalContext`로,
  사용자에게 `systemMessage`로 web의 절대 경로를 든 명령과 함께 알리고 0으로 끝난다.
- **등록.** `.claude/settings.json`의 SessionStart, 매처 `startup|resume`, 래퍼 모양, `timeout` 300.
- **훅 러너.** 자식 환경에서 `CLAUDE_CODE_REMOTE`를 벗기고(`CLAUDE_CODE_ENTRYPOINT`를 벗기는 것과 같은 까닭이다),
  페이로드 표의 사례가 `env`를 가질 수 있게 했다(`tools/run_hooks.py`의 `Case.env`, 자리표시자를 바꾼 뒤 자식 환경에
  덧씌운다). 자리표시자 `${BROKEN_WEB}`을 더했다. `web/package.json`의 의존성이 `web/pnpm-lock.yaml`에 없어, 진짜
  pnpm이 네트워크 없이 곧 실패한다(`pnpm -C <픽스처>/web install --frozen-lockfile`을 손으로 봤다. `packageManager`가
  없어 전역 pnpm 10.28.0이 돌았고 0.35초에 종료 1, `ERR_PNPM_OUTDATED_LOCKFILE`). 표에는 발동 하나(클라우드 세션의
  이어짐, `cwd`는 루트 아래라 `CLAUDE_PROJECT_DIR`로 루트를 찾아야 실패를 알린다)와 침묵 하나(로컬 세션, 변수 없음)를
  두었다.
- **문서.** `KICKOFF.md`의 훅 목록과 등록 매처와 계기 훅 분류, `README.md`의 클론 뒤 설치, `.claude/rules/tools.md`의
  훅별 시간, 설정 스크립트 원본의 머리 주석. 대기열 138을 닫았다. `docs/constitution/operations.md`의 "체크아웃마다,
  워크트리를 팔 때마다 한다"는 클라우드 세션에서도 참이라(훅이 그것을 대신 칠 뿐이다) 고치지 않았다. ADR과 헌법 판도
  그대로다.

## 잰 것

모두 이 클라우드 컨테이너에서 셸의 `date`로 손으로 봤다.

- **이미 깔린 상태.** `pnpm -C web install --frozen-lockfile`이 세 번 0.81~0.85초였다.
- **세션 시작을 흉내 냈다.** `web/node_modules`를 스크래치로 옮기고, 실제 등록과 같은 명령(`uv run --project … --no-sync
  python tools/launch_hook.py hook_session_web_deps.py`)에 `source: startup` 페이로드를 넣어 불렀다. 약 3초에 종료 0이었고
  `web/node_modules`가 다시 생겼다. 출력 139바이트는 uv의 `UV_NATIVE_TLS` 경고 한 줄(stderr)뿐이었다. 같은 명령을
  `source: resume`으로 다시 부르면 약 1초에 0이었다. 이 흉내는 리뷰 반영(루트를 `CLAUDE_PROJECT_DIR`로 찾기) 전의 훅으로
  했다. 이 셸에는 `CLAUDE_PROJECT_DIR`이 없어 반영 뒤에도 같은 `cwd` 길을 탄다.
- **빈 스토어.** 이 세션 앞 단계에서 pnpm 스토어(`/root/.local/share/pnpm/store/v11`, 약 700MB)가 이미 찼으므로, 위의
  3초는 새 VM보다 짧을 수 있다. `--store-dir`로 빈 스토어를 주고 `web/node_modules`를 치운 뒤 pnpm을 돌리자 패키지
  441개를 내려받아 4.8초에 0이었다. 240초의 시간 제한까지 여유가 크다. 잰 뒤 빈 스토어로 만든 `node_modules`를 지우고
  원래 것을 돌려놓았다.

못 본 것: 클라우드 세션이 실제로 이 훅을 부르는지와 그때의 `CLAUDE_PROJECT_DIR`·`cwd`·환경은 이 훅을 병합한 뒤의 새
세션에서 처음 본다. 이 세션의 훅은 세션이 시작될 때 실린 설정이라 새 등록을 싣지 않았다.

## 변이

`.scratch/harness/probes/session_web_deps_mutations.toml`의 20개가 모두 빨갰다(`PYTHONUTF8=1 timeout 600 uv run python
tools/mutate.py …`). 훅 쪽 15개(클라우드 판정, source 판정, `CLAUDE_PROJECT_DIR` 무시, 잠금 파일 판정, `--frozen-lockfile`
빼기, 손으로 칠 명령의 상대 경로, 시간 제한 빼기, 훅 안의 시간 제한을 등록보다 길게, `OSError` 안 잡기, 실패 출력 빼기,
모델과 사용자에게 명령 빼기 둘, 실패 삼키기, pnpm 없음을 조용히 넘기기, 실패에 종료 2)와 러너 쪽 5개(사례 env 버리기,
넘기지 않기, 자리표시자 안 바꾸기, `CLAUDE_CODE_REMOTE` 물려주기, 잠금 파일을 맞추기)다. `--frozen-lockfile` 빼기는 처음
테스트로는 잡히지 않을 것이라 가짜 명령이 인자를 대조하는 테스트를 먼저 더했다.

## 바꾼 것

- `tools/hook_session_web_deps.py`, `tests/tools/test_hook_session_web_deps.py`(13건, 새 파일).
- `tools/run_hooks.py`(`Case.env`와 그 자리표시자, `CLAUDE_CODE_REMOTE` 벗기기, `${BROKEN_WEB}`),
  `tests/tools/test_run_hooks.py`(3건), `tools/hook_payloads.toml`(2건).
- `.claude/settings.json`(SessionStart 등록).
- `KICKOFF.md`, `README.md`, `.claude/rules/tools.md`, `.scratch/harness/cloud-setup.sh`, `.scratch/retro-queue.md`(138 닫힘).
- `.scratch/harness/probes/session_web_deps_mutations.toml`과 프로브 README의 행.
- 회고 반영: `.claude/rules/tools.md`의 디렉터리 항목, 카나리아 명세 `.scratch/harness/probes/canary/tools_rule_hook_dirs.toml`,
  대기열 115의 회차.

## 번호를 옮겼다

처음에는 열린 PR #158(design-system 티켓 02)이 일지 `2026-10-07-03`, 대기열 135·136, 헌법 3.0.17을 쓰는 것을 보고도,
#158이 아직 병합되지 않아 번호를 옮기지 않으려 했다. 커밋 직전의 fetch에서 PR #159가 병합돼 있었다. #159는 #158의
번호를 비워 두고 일지 04와 대기열 137을 썼다(그 일지의 "순번은 03을 형제 워크트리 `02-visual-comparison-gate`의 일지가 이미 써서 04다"). 같은 규약을
따라 main을 병합하며 이 브랜치의 일지 03~07을 05~09로, 대기열 행 135~137을 138~140으로, 헌법 판 3.0.17을 3.0.18로
옮겼다. 고친 인용은 이 브랜치가 들인 줄에 있는 것뿐이다(`git diff origin/main -U0`의 더한 줄). 이 브랜치가 고친 main의
줄(프로브 README의 카나리아 행)에 든 main 쪽 인용 "일지 2026-10-07-04"는 그대로 두었다. 짧은 표기("일지 03", 제목의
번호)와 바뀐 번호에 맞지 않게 된 조사는 손으로 고쳤고, 앞선 이동을 적은 역사 문장은 그때의 번호로 되돌린 뒤 이번 이동을
덧붙였다. 병합의 글자 충돌은 대기열(main의 137 뒤에 이 브랜치의 세 행)과 프로브 README의 카나리아 행(main의 행에 이
브랜치의 명세 하나)이었다. `README.md`의 클론 뒤 설치 문단과 `tools/hook_bash_gate_pipe.py`의 게이트 정규식은 #158과
같은 줄을 고쳐, 둘 중 나중에 병합하는 쪽에서 글자 충돌이 난다.

## 검사

- 반영 뒤 `uv run ruff check .`, `uv run ruff format --check .`, 검사 러너 `uv run python tools/run_checks.py`(pyright,
  import-linter, pytest, 지침 검사, 타입 우회 검사, 훅 러너 63건, web verify)가 모두 초록이었다. 마크다운 표, 줄 구분 문자,
  인용 대조, 변이 표 원문 확인도 바꾼 파일에 돌렸다.
- 바꾼 규칙(`.claude/rules/tools.md`)은 새 `claude -p` 세션에서 불러 봤다. `uv run python tools/canary.py
  .scratch/harness/probes/canary/tools_rule_hook_dirs.toml <스크래치>`가 통과 4, 실패 0이었다(claude 2.1.292, sonnet).
  실험군 셋은 `paths` 안의 `tools/hook_env_read.py` 하나만 읽고 규칙 파일의 제목과 더한 항목의 문장 둘을 옮겼고, 대조군은
  `README.md`를 읽고 "없음"이라 답했다. 시간 줄은 같은 항목 목록의 다른 줄이라 이 카나리아가 재지 않았다.
- main(PR #159)을 병합한 뒤, 러너가 필수로 만든 `source` 칸(`.claude/rules/tools.md`)을 명세에 더해 다시 돌렸다. 돌리기 전의
  원천 확인을 지났고 결과는 같은 통과 4, 실패 0이었다.

## 셀프 리뷰

`/code-review`를 두 축의 서브에이전트로 돌렸다. 범위는 `c62063a` 뒤의 커밋하지 않은 변경 10파일과 미추적 4파일이다.

- **고쳤다, 명세 Major.** 훅이 루트를 페이로드의 `cwd`로만 찾았다. 공식 hooks 문서는 `cwd`가 Claude의 `cd`를 따라가고
  `CLAUDE_PROJECT_DIR`은 세션이 시작된 루트에 머문다고 적는다. 서브에이전트가 `cwd=<루트>/src`로 부르자 설치도 알림도
  없이 0으로 끝났다. 루트를 `CLAUDE_PROJECT_DIR`이 먼저인 순서로 찾고, 테스트와 표의 발동 사례를 루트 아래 `cwd`로 바꿨다.
- **고쳤다, 명세.** 손으로 칠 명령이 상대 경로(`-C web`)였고, pnpm이 없을 때도 같은 pnpm 명령을 안내했다. 명령에 web의
  절대 경로를 넣고, pnpm이 없으면 pnpm을 갖춘 뒤에 치라고 적는다. 훅 안의 시간 제한이 등록의 것보다 짧은지 테스트가
  대조한다. 변이 "실패하면 세션을 막는다"는 이름이 틀렸다. SessionStart는 종료 2로도 막지 못한다(공식 hooks 문서). 그래서
  "종료 2로 끝난다"로 고쳤다. 표의 침묵 사례가 빈 값(`CLAUDE_CODE_REMOTE = ""`)이라 실제 로컬 입력(변수 없음)과 달랐다.
  러너가 그 변수를 벗기고, 침묵 사례는 `env`를 갖지 않는다. 대기열 138의 닫힘에 `operations.md`를 고치지 않은 까닭을
  적었다. `tools.md`의 "세션마다 한 번"은 이어질 때마다 다시 도는 것과 맞지 않아 고쳤다.
- **고쳤다, 표준.** "손으로 쟀다"가 `docs/agents/issue-tracker.md`의 근거 규약(쟀다·실측은 커밋한 프로브에만)에 어긋났다.
  명령과 함께 "손으로 봤다"로 고치고, 0.85초는 다시 세 번 봐 `tools.md` 한 곳에 범위로 두었다. "`uv sync`는 첫 `uv run`이
  한다"는 훅 등록의 `uv run --no-sync`가 sync하지 않으므로 "`--no-sync` 없는 첫 `uv run`"으로 고쳤다. "설정 스크립트가 돌 때
  저장소가 어디 있는지 보장되지 않는다"는 공식 문서에 없었다. 문서가 드는 까닭(설정 스크립트는 VM을 갖추는 자리이고 환경
  캐시가 있으면 건너뛴다)으로 바꿨다. 픽스처의 pnpm 판(11.24.0 → 10.28.0)을 고쳤다. KICKOFF는 이 훅을 계기 훅에 넣었다.
  설치 인자를 `INSTALL_ARGS` 하나로 묶었다.
- **남겼다.** `install()`이 실패를 예외가 아니라 `str | None`으로 돌려준다(`CODING_STANDARDS.md`의 CQS). 실패를 알리고
  막지 않는 훅이라 까닭 문자열이 곧 출력이므로 두었다. 매처 `startup|resume`과 `INSTALL_SOURCES`가 같은 것을 두 곳에
  든다. 매처를 넓혀 등록해도 훅이 `compact`·`clear`에서 다시 깔지 않게 하는 방어라 두었다. 테스트 헬퍼 이름(`_web`,
  `_python`, `_cli`)은 영문이다. 기존 파일들도 섞여 있어 두었다.

## 회고

일지의 "다음"을 쓰기 전에 retro를 돌렸다. 후보 둘을 냈고 둘 다 승인됐다.

> 사용자(질문에 답): "115에 회차를 더한다 (Recommended)", "이 세션에서 반영한다 (Recommended)"

1. **열린 PR과 번호가 또 겹쳤다(대기열 115, 5회차).** 위 "번호" 절의 사건이다. `CLAUDE.md`의 커밋 전 대조는 `origin/main`과
   형제 워크트리를 보는데, 클라우드 세션의 형제는 워크트리가 아니라 다른 클라우드 세션의 열린 PR이다. 이번에는 MCP로 열린 PR의
   파일 목록을 받아 잡았다. 처방은 115 그대로이고 회차만 더했다.
2. **훅이 디렉터리를 고를 때 `CLAUDE_PROJECT_DIR`과 페이로드의 `cwd`를 가른다(이 세션에서 반영).** 셀프 리뷰가 잡은 Major의
   원인은 두 값의 차이를 몰랐던 것이다. 같은 문서에 있던 "SessionStart는 종료 2로 막지 못한다"도 변이 이름을 틀리게 했다.
   `.claude/rules/tools.md`에 공식 hooks 문서의 사실로 한 항목을 더했다. 새 `claude -p` 세션의 카나리아로 실리는지 봤다(아래
   "검사").

## 다음

- PR은 사용자가 원할 때 연다. 열린 PR #158과는 번호가 더 겹치지 않지만, `README.md`의 클론 뒤 설치 문단과
  `tools/hook_bash_gate_pipe.py`의 게이트 정규식에서 글자가 충돌한다. 나중에 병합하는 쪽이 푼다.
- 이 브랜치가 병합된 뒤의 첫 클라우드 세션에서 훅이 실제로 도는지 본다. 세션이 시작될 때 `web/node_modules`가 있거나, 없으면
  훅이 낸 알림(손으로 칠 명령)이 컨텍스트에 있어야 한다. 둘 다 없으면 훅이 불리지 않은 것이다.
- 일지 08의 "다음"(사용자가 Setup script 칸을 `.scratch/harness/cloud-setup.sh`의 내용으로 바꾼다)은 사용자 쪽의 일이다.
  바꿨는지는 이 세션에서 보이지 않는다.
- 대기열 139(변이 도구의 시간 제한)와 140(붙여 넣을 값을 코드 블록으로)은 그대로다.
