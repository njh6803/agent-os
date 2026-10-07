# Agent OS

플러그인 기반 에이전트 런타임. an agent OS.

규칙은 [docs/constitution/](docs/constitution/README.md), 용어는 [CONTEXT.md](CONTEXT.md), 결정은 [docs/adr/](docs/adr/), 진행 기록은 [docs/journal/](docs/journal/), 전체 계획은 [.scratch/plan.md](.scratch/plan.md).

```bash
uv sync
pnpm -C web install
pnpm -C web exec playwright install --only-shell chromium
uv run pre-commit install
uv run pytest -q
pnpm -C web verify
```

`pre-commit install`은 주 체크아웃에서 한 번만 친다. git 훅은 워크트리와 공유된다. `uv sync`와 `pnpm -C web install --frozen-lockfile`은 워크트리마다 친다. chromium은 `pnpm -C web verify`의 스토리 테스트가 쓰고, 체크아웃마다가 아니라 기계마다 처음과 Playwright 판이 바뀔 때 한 번 친다(Playwright의 브라우저 캐시, Windows는 `%LOCALAPPDATA%\ms-playwright`). 사진 비교(`pnpm -C web visual`, `web/packages/ui`를 건드렸을 때)는 Docker가 있어야 하고, 처음 치면 판을 고정한 Playwright 이미지(받는 양 약 956MB)를 받는다.

## 구조

```
src/agent_os/
  main.py          진입점. run·resume → channel, serve → server. 어댑터를 조립해 넘긴다
  server.py        HTTP 표면의 조립 층. create_app() 하나. 전역 app을 두지 않는다
  sdk/             플러그인이 import하는 유일한 표면. 이벤트, 매니페스트, BaseAgent
  core/            런타임, 로더, 루프, 재생, 포트 선언
  channel/cli/     실행을 일으키는 면. run·resume 과 명령 셋의 인자
  channel/http/    실행을 일으키는 면. router(운영자 채널 /runs 와 두 접두사의 조립), end_user(최종 사용자 면
                   /end-user 의 시작·결정·구독), items(최종 사용자 항목과 투영), bodies(두 면의 요청 본문),
                   runs(실행을 앱의 수명에 묶는 것과 도는 실행의 등록부, 연결마다의 백로그),
                   limits(최종 사용자 경로의 상한. 기본값 일곱과 셈)
  admin/           구성을 바꾸고 관찰하는 면. http(라우터와 관리의 응답 모델), traces(목록과 상세의 모양)
  http/            채널과 관리가 같이 쓰는 HTTP 배관. errors(봉투와 면별 상태 코드 표), routes(에러 문서와 verbatim),
                   auth(fail-closed 인증. 공유 토큰 둘과 사이트가 서명한 토큰), sites(사이트 목록과 서명 토큰 검증),
                   cors(최종 사용자 접두사에만 거는 CORS), paths(접두사 비교)
  adapters/        포트 구현
plugins/
  agents/  mcp/  skills/  models/    각각 <name>/plugin.toml
  disabled.toml    선택. 운영자가 끈 플러그인의 이름(ADR 0017). 없으면 전부 켜짐. 관리 API의 PUT이 쓰고
                   손으로 고쳐도 같다. skill과 model은 로더가 생길 때 그 로더가 켜짐을 본다
tests/             src를 미러링
web/               pnpm 워크스페이스(Node 24, TypeScript 5.9). 파이썬과 루트를 나눈다. 앱은 apps/*, 공유 패키지는 packages/*
  eslint.config.mjs  원칙 III의 TS 판정자와 층 경계. 변이 테스트는 eslint.config.test.ts
  tsconfig.base.json 기준 tsconfig. 다른 tsconfig는 이것을 extends 한다
  tools/           web의 검사. check-tsconfig(strict 계열을 끈 tsconfig를 잡는다), generate-api-client(생성 클라이언트의
                   타입을 openapi.json에서 만들고 --check 로 최신성을 본다), visual(사진 비교를 판을 고정한 Playwright
                   이미지의 Docker 컨테이너에서 돌린다)
  packages/api-client/  생성 클라이언트. src/generated(생성물, 커밋하고 손으로 고치지 않는다), 관리·채널 클라이언트 둘,
                   재개 스트림을 프레임으로 읽는 것(ADR 0021)
  packages/ui/     디자인 시스템(@agent-os/ui). src/styles/(디자인 토큰 CSS theme.css, 글꼴 CSS fonts.css, shadow 보정,
                   판정 스토리), src/components/atoms/(컴포넌트와 스토리, <Name>.md), src/testing/(판정 함수),
                   src/storybook/(앱도 나눠 쓰는 미리보기), .storybook/(Storybook 설정), visual/(사진 비교와 정답
                   사진 snapshots/). 스토리 테스트는 뿌리 vitest.config.ts 의 storybook 프로젝트가 실제 chromium 에서
                   돈다(ADR 0026)
  apps/admin/      관리 화면(Next). app/(라우팅과 레이아웃), components/(아토믹 층, pages/가 화면), api/·hooks/queries/
                   (요청 함수와 SWR 훅), stores/(토큰), next.config.ts(/api 중계), tools/start.ts(루프백에만 띄우는
                   시작 래퍼), testing/(페이지 테스트의 가짜 네트워크와 격리), e2e/(실제 serve 를 지나는 Playwright)
docs/
  constitution/    헌법 (principles, tech, operations)
  adr/  agents/  journal/
.scratch/          로컬 이슈 트래커. plan.md와 기능별 spec·티켓
.claude/
  agents/          프로젝트 서브에이전트. coderabbit-review(트리아지만), spec-reviewer(명세 검토). 둘 다 수정 없음
  rules/           디렉터리별 규칙. 해당 파일을 Read 도구로 열 때만 로드
  skills/          엔지니어링 스킬
  settings.json    훅 등록, 권한(`.env` 읽기 거부), 플러그인, 스킬 덮어쓰기
tools/             배포되지 않는 저장소 유틸. 훅(hook_*)과 그 실행 래퍼(launch_hook), 검사(check_*), 훅 러너(run_hooks + hook_payloads.toml), 변이 도구, OpenAPI 내보내기, Actions 요약
kickoff/           다른 프로젝트용 킥오프 런북(KICKOFF.md)의 템플릿과 부록. 이 프로젝트의 문서가 아니다
.coderabbit.yaml   CodeRabbit 설정. PR 봇과 로컬 CLI가 같이 읽는다
openapi.json       관리 API와 HTTP 채널(운영자와 최종 사용자)의 계약. 손으로 고치지 않고 tools/export_openapi.py로 뽑는다
```

아직 없는 것은 [.scratch/plan.md](.scratch/plan.md)의 목표 배치에 있다.

## 관리 화면

관리 화면(`web/apps/admin`)은 루프백에만 서고, 같은 출처의 `/api/*`를 파이썬 `serve`로 넘기는 중계다(ADR 0019).

```bash
uv run agent-os serve              # 공유 토큰 둘(AGENT_OS_ADMIN_TOKEN, AGENT_OS_CHANNEL_TOKEN)이 환경에 있어야 선다.
                                   # --site-file 은 선택이다(최종 사용자 경로, ADR 0023)
pnpm -C web/apps/admin build
pnpm -C web/apps/admin start       # http://127.0.0.1:3000
```

- **관리 토큰을 넣는다.** 처음 열면 관리 토큰을 넣는 자리다. `serve`에 준 `AGENT_OS_ADMIN_TOKEN`의 값을 넣는다. 토큰은 그 탭의 sessionStorage에만 남아 새로 고쳐도 다시 넣지 않고, 탭을 닫거나 "토큰 지우기"를 누르면 사라진다. 거부되면 "관리 토큰이 거부됐다"를 보이고 저장하지 않는다(ADR 0019).
- **채널 토큰은 선택이다.** 관리 토큰을 넣으면 머리에 채널 토큰을 넣는 자리가 선다. `serve`에 준 `AGENT_OS_CHANNEL_TOKEN`의 값을 넣으면 멈춘 실행에 결정 자리(허가와, 사유를 적는 거부)가 선다. 넣지 않아도 나머지는 모두 쓴다. 채널 토큰은 넣을 때 확인하지 않는다. 틀렸으면 첫 결정이 "채널 토큰이 거부됐다"를 보이고 채널 토큰만 지운다. "토큰 지우기"는 두 토큰을 모두 지운다. 결정의 승인자는 화면이 고르지 않고 `serve`를 띄운 OS 사용자로 기록된다(ADR 0015).
- **`serve`와 상류를 맞춘다.** 관리 화면이 넘기는 곳(상류)은 `AGENT_OS_UPSTREAM`이고, 기본은 `serve`의 기본 주소 `http://127.0.0.1:8000`이다. `serve`를 다른 포트로 띄우면 같은 주소를 `AGENT_OS_UPSTREAM`에 두고 빌드한다.
- **상류 포트를 바꾸면 다시 빌드한다.** 상류는 빌드 산출물에 박힌다. `start` 때 준 값은 판정만 하고 넘기는 곳을 바꾸지 않는다. `dev`(`pnpm -C web/apps/admin dev`)는 설정에서 바로 읽는다.
- **루프백에만 선다.** 관리 화면은 `127.0.0.1`(기본)이나 `::1`에만 서고, 받는 인자는 `--hostname`과 `--port` 둘이다. 상류는 `127.0.0.1`만 받는다. Next가 IPv6 주소로 넘기지 못한다(ADR 0011의 2026-09-30 이력). 원격에서 보려면 SSH 포트 포워딩을 쓴다: `ssh -L 3000:127.0.0.1:3000 <서버>`.

## 원천 표

사실 하나에 원천 하나. 다른 문서는 이 원천을 가리키기만 하고 요약하지 않는다. 두 곳이 다르면 원천이 맞고 나머지가 버그다.

| 사실 | 원천 | 비고 |
|---|---|---|
| 원칙과 거버넌스 | `docs/constitution/principles.md` | `CLAUDE.md`가 임포트 |
| 스택과 의존성의 결정 | `docs/constitution/tech.md` | 구현은 `pyproject.toml`과 `web/package.json`. 둘이 다르면 구현을 맞추거나 ADR |
| 검증·운영 규약 | `docs/constitution/operations.md` | 검증 명령은 `CLAUDE.md`, 실행은 `.pre-commit-config.yaml`과 `.github/workflows/ci.yml`. 명령이 바뀌면 셋 다 |
| 제품 의도와 성공의 정의 | `docs/PRD.md` | 헌법은 원칙 I의 기한만 |
| 용어 | `CONTEXT.md` | 피할 말 포함 |
| 결정과 이유 | `docs/adr/`, 색인 `docs/adr/README.md` | 헌법과 rules는 번호로 인용만 |
| 판단 기준(리뷰) | `CODING_STANDARDS.md` | "규칙으로" 승인분만 |
| 리뷰 파이프라인(누가 언제 무엇을) | `docs/constitution/operations.md` | 봇 설정은 `.coderabbit.yaml`과 `.github/workflows/claude-code-review.yml`. 기준은 CODING_STANDARDS |
| 디렉터리별 규칙 | `.claude/rules/*.md` | 해당 파일을 Read 도구로 열 때만 실림 |
| 지침의 로드 시점 표 | `CLAUDE.md` 교정 루프 절 | ADR 0004는 결정의 기록, 런북 3단계 템플릿은 새 프로젝트용 사본 |
| 현재 구조 | 코드 | 이 README의 트리는 안내 |
| 미래 배치, 기능 순서, 상태 | `.scratch/plan.md` | |
| 기능 명세와 티켓 | `.scratch/<slug>/` | |
| 디스크 형식(매니페스트, 이벤트) | `src/agent_os/sdk/`와 `tests/sdk/` | `rules/sdk.md`는 결정만 |
| 설치된 스킬과 해시 | `skills-lock.json` | |
| 진행 기록 | `docs/journal/` | 이력이지 원천이 아니다 |
| 환경 함정 | `CLAUDE.md`(명령 전에 볼 것), `operations.md`(나머지) | 런북 `kickoff/pitfalls.md`는 새 프로젝트용 사본 |
| 리뷰 봇 실행의 실제 내용 | Actions 로그. `tools/gh_run_summary.py`가 요약 | 체크의 초록은 원천이 아니다 |
