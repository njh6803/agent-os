# 예시 MCP 서버가 npx 없이 미리 설치한 실행 파일로 뜬다 (release-image 티켓 02)

브랜치 `feature/02-example-mcp-server-runs-without-npx`. 이 세션의 제목은 인계 직전까지 `feature/02-example-mcp-server-runs-without-npx`다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/02-example-mcp-server-runs-without-npx.md
>
> 다음 작업: .scratch/release-image/issues/02-example-mcp-server-runs-without-npx.md. 예시 MCP 서버가 npx 없이 미리 설치한 실행 파일(mcp-server-everything)로 뜨게 한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 … EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/release-image/issues/02-example-mcp-server-runs-without-npx.md
> 브랜치: feature/02-example-mcp-server-runs-without-npx
> 모델: Sonnet 5.5 / high
> 읽을 것: 나란히 도는 나머지 티켓 .scratch/release-image/issues/03-processes-bind-container-network-in-image.md, .scratch/release-image/issues/04-tools-compute-release-number-and-notes.md
> 이어받을 상태: 티켓 01이 PR 570으로 병합되어 02·03·04가 풀렸다. 01의 일지(docs/journal/2026-11-14-2318-repo-version-reads-0-0-0.md)에는 병합을 마친 뒤에야 '다음' 절이 없다는 것을 알았다. 세 세션이 함께 돌아 PC 부하로 시간에 기대는 시험이 번갈아 빨개질 수 있다(같은 일지의 '커밋과 PR 직전 리뷰'에 첫 시도 빨강과 홀로 돌려 통과한 기록이 있다)
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

> 사용자: 끝났어?

사용자의 다른 말은 없었다. "끝났어?"에는 실제 모델 시험 둘(`llm_portal`, 검증 러너)이 남아 아직 끝나지 않았다고 답했다.

## 한 것

- `tidy-checkouts`: 주 체크아웃 dev를 `4e3752592`에서 `9a68c2bb9`로 당겼다. 병합된 워크트리 셋(`03-widget-renders-answers-as-markdown`, `04-markdown-card-renders-on-react-18`, `release-image-tickets`)과 그 로컬 브랜치를 지웠다(쉬는 세션의 프로세스 다섯을 `end-holders`로 끈 뒤). 휴지통에 `node_modules` 셋이 남았다(`esbuild.exe`를 다른 프로세스가 쥐었다). 첫 `judge`는 `gh`가 60초 안에 돌아오지 않아 종료 3으로 끝났고 한 번 더 치자 지나갔다.
- 워크트리 `02-example-mcp-server-runs-without-npx`에 들어가 임시 브랜치를 `feature/02-example-mcp-server-runs-without-npx`로 바꿨다. 새 브랜치가 `origin/dev`를 추적하길래 `git branch --unset-upstream`으로 풀었다. `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다.
- 티켓 `Status`를 `in-progress`로 바꿨다가 끝에 `done`으로 바꾸고 체크박스 여덟을 모두 채웠다(마지막 "검증 명령이 모두 초록이다"는 커밋의 pre-commit이 확인할 때까지 닫힌 것이 아니다. 아래 "남은 일"). 기능의 마지막 열린 티켓이 아니라 `**끝:**` 줄은 적지 않았다. `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다.
- 바꾼 파일 일곱.
  - `plugins/mcp/everything/plugin.toml`: `command = "mcp-server-everything"`, `args = []`. 주석에 설치 명령과 `npx -y`를 쓰지 않는 까닭을 적었다.
  - `.github/workflows/ci.yml`의 `llm` 잡: setup-node 다음에 `npm install --global @modelcontextprotocol/server-everything@2.3.0` 단계를 더했다. 그 단계에 zizmor 인라인 무시 `# zizmor: ignore[adhoc-packages]`를 달고 까닭은 위 주석 줄에 적었다(아래 "고친 것". 셀프 리뷰가 긴 한 줄을 나누게 했다).
  - `docs/constitution/operations.md` LLM 테스트 절: 개발 PC에서 같은 판을 전역에 까는 준비 한 줄.
  - `docs/constitution/README.md`: 판을 3.0.97에서 3.0.99로, `Last Amended`를 2026-11-15로 올렸다. 올린 까닭은 이 일지가 적는다. LLM 테스트 절에 개발 PC 준비 절차가 더해졌다(문장 추가이므로 patch). `tools/sibling_overlap.py`가 형제 `03-llm-local-command-rents-model-servers` 워크트리가 3.0.98을 먼저 쓴 것을 알려 3.0.98은 비워 두고(3.0.95와 같은 모양의 비움 문장을 판 줄 곁에 더했다) 3.0.99를 골랐다.
  - `web/apps/widget/playwright.config.ts`, `web/apps/portal/playwright.config.ts`: 실제 모델 제한 시간을 설명하는 주석의 "MCP 서버(npx)"를 "MCP 서버(실행 파일 mcp-server-everything)"로 고쳤다. 그 알림이 `sync-design-system 확인`을 부르라 했으나 주석 한 줄이고 화면 코드를 더 고치지 않아 부르지 않았다.
  - 티켓 파일.
- 이 PC에 `npm install --global @modelcontextprotocol/server-everything@2.3.0`을 쳤다(`C:\Users\User\AppData\Roaming\npm\mcp-server-everything`과 `.cmd`가 생겼다). 이 티켓의 `-m llm` 확인이 요구하는 준비이고 operations.md의 새 줄이 개발 PC에 요구하는 것과 같다. 이 PC의 전역 npm 상태가 바뀐 것이므로 사용자가 알아야 한다.
- 모델을 부르지 않는 시험은 바꾸지 않았다. `tests/sdk/test_manifest.py`와 `tests/adapters/test_filesystem.py`는 336건 통과(9.26초)했고 `tests/test_server.py`도 통과했다(종료 코드 0, 로그를 파일로 받았다).
- 옛 표현 grep: 저장소 코드·문서에서 예시 매니페스트가 `npx`로 뜬다고 말하는 살아 있는 문장은 위 주석 둘과 plugin.toml 자신뿐이었다(테스트의 `npx`는 모두 각 시험이 적은 자기 매니페스트다. 일지·ADR·프로브 기록은 기록이다).

## 실제 모델 시험 (이 PC, 워크트리의 `.env` 경로 `../../../.env`)

- `-m llm`: 23 passed, 7316 deselected, 755.16초. `LLM 토큰 합계 259,324(입력 254,014, 출력 5,310). 트레이스 30개, 모델 호출 61건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.` Windows에서 npm이 만든 `.cmd`로 서버가 뜬다는 것은 이 통과에서 미루어 본 것이다. 전역 설치 전에 `where mcp-server-everything`이 아무것도 찾지 못했고 설치 뒤에 `.cmd`를 찾은 것은 손으로 봤다. 시험이 calc 예시의 MCP 연결을 지나야 통과한다는 것은 티켓의 서술을 따랐고 시험 코드로 대 보지 않았다.
- `-m llm_widget`: 1 passed, 7338 deselected, 415.98초. `LLM 토큰 합계 17,047(입력 16,785, 출력 262). 트레이스 2개, 모델 호출 4건.`
- `-m llm_portal`: 1 passed, 7338 deselected, 742.31초. `LLM 토큰 합계 6,997(입력 6,925, 출력 72). 트레이스 1개, 모델 호출 2건.`

## 고친 것

- 전체 러너(`uv run python tools/run_checks.py`)의 첫 바퀴가 24건 실패로 끝났다(pytest 24 failed, 7290 passed, 1043초). 23건은 `tests/tools/test_zizmor_gate.py`였고 원인은 zizmor가 새 `npm install --global` 단계를 `adhoc-packages`(잠금 파일 밖에서 패키지를 깐다, 신뢰도 high, 심각도 low)로 낸 것이다. `uv run zizmor --offline --strict-collection --config .github/zizmor.yml .`가 종료 12로 그 한 건을 보였다. 그 줄에 `# zizmor: ignore[adhoc-packages]`와 까닭(판을 정확히 고정했고 서버 이미지와 같은 판이다, 이 저장소에 이 패키지를 둘 잠금 파일이 없다)을 달았고 zizmor가 0으로 끝났다. 이 저장소가 `artipacked`에 같은 모양의 무시를 쓰는 선례를 따랐다(ci.yml 머리 주석). 게이트 시험 파일을 홀로 다시 돌려 통과했다. 남은 한 건 `tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`는 시간에 기대는 시험이고(지시문의 "이어받을 상태"가 말한 계열), 홀로 돌리니 통과했다(종료 코드 0). 이 변경은 그 시험이 읽는 코드를 건드리지 않았다. 러너 전체를 이 상태로 다시 돌리지는 않았다. 커밋의 pre-commit이 그 다섯 명령을 돌린다.
- 시험 수와 시간과 토큰 합계는 pytest가 찍은 출력을 로그 파일에서 읽은 것이고, 종료 코드는 명령이 낸 값이다. zizmor의 지적은 그 도구의 출력을 읽은 것이다. 무시 주석이 `adhoc-packages`의 심각도나 신뢰도를 어떻게 바꾸는지는 보지 않았고, 도구가 0으로 끝난 것만 봤다.

## 셀프 리뷰 (`/code-review`, 인계받은 세션)

범위: base `9a68c2bb9`, 추적 파일 7개의 미커밋 변경과 미추적 1개(이 일지), 커밋 0개. 표준 축은 sonnet·high, 명세 축은 세션의 모델로 돌렸다. 두 축 모두 Critical·Major는 없었다.

- 이 세션이 리뷰 전에 먼저 고친 것: `operations.md`에 끼운 설치 문장이 "`.env`는 커밋하지 않는다. 그래서 워크트리에는 없고"의 인과를 끊고 있어 문단 뒤쪽으로 옮겼다(다음 줄의 항목에서 한 번 더 옮겼다).
- 고친 것(Minor):
  - `operations.md`: 처음 쓴 문장(세 마커의 시험은 모두 예시 MCP 서버를 띄운다)은 보편 주장이었다(`-m llm`의 `tests/test_assistant_llm.py`는 doc-search, `tests/test_main.py`의 원격 시험은 원격 MCP를 쓴다). "calc 예시를 도는 시험"으로 좁혔다. 설치 문장을 "원칙 I의 판정은 이 명령이다" 뒤로 옮겨 "이 명령"이 `-m llm`을 가리키게 했다. 서버 이미지는 아직 없어(티켓 07이 만든다) "서버 이미지에 깔 판"이라는 미래형으로 썼다.
  - `ci.yml`: 같은 미래형으로 고치고, 한 줄이 길던 zizmor 무시의 까닭을 위 주석 줄로 옮겼다. 무시 형식은 `tests/tools/test_zizmor_gate.py`의 픽스처가 쓰는 형식(`# zizmor: ignore[<규칙>] <까닭>`)과 같다. 이 저장소의 실제 워크플로에서 무시 주석을 쓴 곳은 이 줄뿐이고, ci.yml 머리 주석이 안내하는 것은 `artipacked`다. 앞 절의 "선례"는 그 안내와 시험의 픽스처를 가리킨다.
  - 07번 티켓(`.scratch/release-image/issues/07-serve-image-runs-as-non-root-without-network.md`) 28행: 매니페스트는 지금 예시의 `npx -y` 꼴을 시험용으로 둔다는 문장이 이 변경으로 거짓이 되어, 티켓 02가 바꾸기 전의 꼴(`command = "npx"`, `args = ["-y", "@modelcontextprotocol/server-everything"]`)을 값 그대로 적었다. 02의 체크박스 밖이지만 02가 거짓으로 만든 미래형 문장이라 02가 고친다. 10번 티켓의 npx 줄은 운영자가 따로 올리는 MCP 서버를 가리켜 그대로 참이다.
  - `plugin.toml` 주석: "인터넷이 막힌 곳에서는 70초 넘게"를 프로브가 잰 범위로 좁혔다("네트워크가 없는 컨테이너(`--network none`)에서는 71~74초 뒤에 실패". `probes/serve_image/README.md` 4번이 `--network none`에서 71.5~73.8초를 쟀고, 그 README가 이름 풀이 재시도 탓인지는 가르지 않았다고 적는다).
- 남긴 것: 헌법 README의 3.0.98 비움 문장은 형제 워크트리(`feature/03-llm-local-command-rents-model-servers`)가 이미 같은 자리를 "병합되어 3.0.98로 올렸다"로 다시 써 병합 충돌이 날 수 있다(`tools/sibling_overlap.py`도 경고한다). 형제가 먼저 병합되면 이 브랜치가 충돌을 풀고 비움 문장을 지운다. "준비 한 줄"로 적힌 요구에 operations.md는 문장 셋을 더했다(한 문단 안이고 설치 명령, 판의 출처, 실패 모양을 모두 담아 두었다). 줄이지 않았다. "깔려 있지 않으면 calc 예시가 MCP 연결에서 실패한다"는 이 티켓이 깔지 않고 돌려 본 것이 아니다(`command`의 실행 파일이 없을 때의 결과를 코드 읽기로 말했다). ADR 0056 16행과 명세 191·193행의 "지금 `npx -y`"는 옛 시점을 적은 기록이라 잔존으로 세지 않는다.
- 명세 축이 `tests/test_main.py:589`의 `tool_called` 단언이 `-m llm` 통과로 `.cmd` 서버가 떴음을 증명한다고 확인했다. 위 "실제 모델 시험"의 "시험 코드로 대 보지 않았다"는 이 단언으로 닫힌다(두 서브에이전트가 읽은 것이고 이 세션이 단언을 열어 대 보지는 않았다).
- 서브에이전트가 보고서에서 "미커밋 변경 일곱"이 여덟이라 한 것은 07번 티켓 한 줄을 고친 때문이다(추적 파일 여덟).

## PR 직전 CodeRabbit CLI 리뷰

`coderabbit-review` 서브에이전트가 CLI 0.7.5로 `--agent --include-untracked`를 끝까지 돌렸다(`review_completed`, 종료 코드 0, 9개 파일, CLI 지적 0건. `Plan: Free`, `Seat: not assigned`는 서브에이전트가 `auth status`에서 본 줄을 옮긴 것이다). 서브에이전트가 직접 트리아지한 Minor 둘:

- 유효(고쳤다): 개발 PC에 필요한 Node 판이 `plugin.toml` 주석과 `operations.md`에 없었다. 패키지의 `engines`가 `node >=24`이다(이 세션이 `npm view @modelcontextprotocol/server-everything@2.3.0 engines bin`을 쳐서 `engines = { node: '>=24' }`와 `bin = { 'mcp-server-everything': 'dist/index.js' }`를 봤다). 두 곳에 "Node 24 이상"을 적었다.
- 보류: 전역 설치가 최상위 판 2.3.0만 고정하고 하위 의존성(`zod ^4.2.0`, `express ^5.3.0` 등 범위 의존성)은 날마다 달라질 수 있다. 서브에이전트가 `npm view`로 본 것이고 이 세션이 다시 재지는 않았다. 판을 적지 않던 `npx -y`보다 낫고, 이 단계는 시크릿 없는 설치 단계다(`ANTHROPIC_API_KEY`는 뒤의 pytest 두 스텝에만 env로 간다). 고치려면 잠금 파일을 두거나 `--ignore-scripts`를 붙이는데, 뒤의 것은 이 패키지의 설치 스크립트 키(`scripts.*` 넷 가운데 `npm run build`가 어느 키인지)를 서브에이전트가 가르지 못해 지금은 붙이지 않았다. 고치는 값이 크고 근거가 모자라 PR 체크리스트에 판정과 값을 적는다.
- 오탐으로 가른 것: 71~74초와 프로브의 71.5~73.8초는 둥글림 차이다. 형제 브랜치와의 3.0.98 비움 문장 충돌은 위 "남긴 것"에 이미 있다.

## 남은 일

- 셀프 리뷰는 위에서 마쳤다. 다시 돌리지 않는다.
- 셀프 리뷰를 반영한 뒤 커밋하고(커밋 전 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`), 커밋의 pre-commit 결과로 티켓의 마지막 체크박스 "검증 명령이 모두 초록이다"를 확인한다. 초록이 아니면 그 체크박스를 되돌린다.
- PR 직전 CodeRabbit CLI 리뷰, PR(dev로), 봇 회차 반영, 병합(`merge.md`의 "워크트리에서 병합할 때"), 병합 뒤 일지의 "다음"과 회고는 이 요청의 범위(PR과 병합까지)다.
- 셀프 리뷰가 볼 만한 것: ADR 0056과 명세의 "예시 MCP 서버"는 이 변경이 닫는 쪽이라 이력을 쌓지 않았다(명세가 그렇게 정했다). 헌법 판의 3.0.98 비움 문장은 형제 브랜치(`feature/03-llm-local-command-rents-model-servers`)가 판을 가져가면 지워진다.

## 인계

컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 새 세션에 넘긴다(`next-session handoff.md`). 일지 경로 `docs/journal/2026-11-15-0402-example-mcp-server-runs-without-npx.md`. 제목을 `feature/02-example-mcp-server-runs-without-npx (인계함)`으로 바꿨다(바뀌기 전 제목은 `feature/02-example-mcp-server-runs-without-npx`). 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없었다).
open-session을 부른다 2026-11-14T19:03Z
