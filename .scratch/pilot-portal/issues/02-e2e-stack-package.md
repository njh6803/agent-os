# 02: 위젯 e2e의 준비를 `@agent-os/e2e-stack`으로 뽑고 트레이스 폴더를 시험에 넘긴다

**What to build:** 위젯 e2e를 돌리는 기여자에게는 바뀌는 것이 없다. `pnpm -C web/apps/widget exec playwright test`가 같은 `serve`, 같은 사이트 파일로 빌드한 위젯 Next, 같은 중계를 띄우고 같은 사례가 초록이다. 달라지는 것은 그 준비의 몸통이 새 워크스페이스 패키지 `@agent-os/e2e-stack`(`web/packages/e2e-stack`)에 있다는 것이다. 패키지에는 중계, 픽스처 플러그인(저장소 플러그인 복사 포함), `serve` 띄우기와 빈 포트·기다리기·끄기 도우미, 사이트 키와 토큰 서명(`token.ts`)이 들고, 두 앱(위젯과 06의 질문 페이지)의 devDependency다. 그리고 준비가 `serve`의 트레이스 폴더를 시험에 넘기는 길이 하나 생겨, 시험이 실행의 주체를 트레이스에서 읽을 수 있다(스토리 14).

02는 01 뒤이고 03과 06을 막는다. 같은 `package.json`과 잠금 파일을 01과 함께 고치므로 01 뒤에 선다. 03(위젯 문구)은 이 티켓이 옮기거나 고치는 위젯 e2e 파일을 다시 고치므로 이 티켓 뒤에 선다. 06은 이 패키지로 질문 페이지의 e2e 준비를 짓는다. 04와는 나란히 돈다. 둘 다 README의 트리, `docs/constitution/tech.md` 웹 행, 헌법의 판, `web/pnpm-lock.yaml`을 고칠 수 있으니, 나중에 병합하는 쪽이 main을 받아 그 파일을 맞추고 헌법의 판은 먼저 병합된 판보다 높게 고른다. 명세의 이야기 16("패키지를 뽑는 변경이 첫 티켓 하나에")은 to-tickets에서 사용자가 아홉 장 분할을 골라 01과 이 티켓 둘로 바뀌었다. 위젯 e2e는 이 티켓의 한 커밋에서 바뀐다.

근거는 `.scratch/pilot-portal/spec.md`의 "앱과 패키지"와 그 2026-11-10 명세 검토 주석 둘째, "띄우기와 타입 검사"의 주석 첫째, "함께 쓰는 e2e 준비와 중계"와 그 주석, "고칠 자리의 묶음"의 A 줄과 그 주석이다. 앞선 결정은 ADR 0050의 결정 "함께 쓰는 코드"(관리 화면 e2e의 사본은 그대로 둔다)다.

**Blocked by:** 01 (사이트 파일 읽기와 디자인 시스템 서브패스를 패키지로 뽑는다). 01이 만든 패키지 자리와 `nodenext` tsconfig의 선례, 같은 `package.json`과 잠금 파일을 쓴다

**Status:** ready-for-agent

### `@agent-os/e2e-stack`

- [ ] **위젯 e2e의 `relay.ts`, `plugins.ts`, `token.ts`와 `stack.ts`·`env.ts`의 준비 몸통을 패키지로 옮긴다.** 위젯의 사이트 서버(`site.ts`, `element-site.ts`)와 사례 파일은 위젯만의 시험 페이지라 옮기지 않는다(명세 "앱과 패키지"). 위젯의 `stack.ts`는 패키지의 도우미로 다시 쓰되 사례와 사이트 서버는 그대로이고, Playwright 설정은 앱마다 두고 `globalSetup`만 패키지를 쓴다(명세 "함께 쓰는 e2e 준비와 중계")
- [ ] **중계는 지금 모양 그대로 옮긴다.** 셋째 상류(질문 페이지)와 그 `upstreamOf` 사례는 06이 더한다(명세 "함께 쓰는 e2e 준비와 중계"의 주석 둘째)
- [ ] **환경 변수 이름은 패키지가 박지 않고 앱이 준다.** 위젯은 지금의 `AGENT_OS_WIDGET_LLM`·`AGENT_OS_WIDGET_TRACES`(`e2e/env.ts`)를 그대로 쓰고, 09의 질문 페이지는 `AGENT_OS_PORTAL_LLM`·`AGENT_OS_PORTAL_TRACES`를 쓴다(명세 "실제 모델 e2e 하나")
- [ ] **패키지의 tsconfig는 01의 `site-file`처럼 `nodenext`이고 진입점과 상대 import에 확장자가 있다**(명세 "띄우기와 타입 검사"의 주석 첫째). `web/tools/check-tsconfig.ts`가 새 tsconfig를 보는지 그 출력으로 확인한다

### 트레이스 폴더를 시험에 넘기는 길

- [ ] **준비가 `serve`에 준 트레이스 폴더를 시험이 읽을 수 있게 넘긴다.** 지금 위젯 e2e의 준비는 트레이스를 `AGENT_OS_WIDGET_TRACES`가 준 폴더(주지 않으면 작업 폴더 아래)에 남기고, Playwright 사례에는 그 자리를 넘기지 않는다. 그 변수는 실제 모델 래퍼(`tests/test_widget_llm.py`)가 준다(명세 "함께 쓰는 e2e 준비와 중계"의 주석 첫째). 07의 트레이스 주체 사례가 이 길을 쓴다
- [ ] **위젯 e2e 사례 하나가 그 길로 트레이스를 열어, 그 요청의 실행 주체가 `<발급자>|<사이트 토큰의 sub>`인 것을 본다.** 이 길을 07 전에 아무 사례도 쓰지 않는 채로 두지 않기 위해서다(to-tickets가 정했다). 주체 이름의 꼴은 ADR 0023이 정했다

### 참조와 문서

- [ ] **옛 경로(`web/apps/widget/e2e/relay.ts`, `plugins.ts`, `token.ts`, 그리고 옮긴 몸통을 가리키는 `stack.ts`·`env.ts`)의 grep 잔존이 살아 있는 문서와 코드에서 0이다.** 명세 "앱과 패키지"의 주석 둘째와 묶음 A가 든 자리를 포함한다. `web/apps/widget/EMBED.md`(129줄의 `e2e/token.ts`), `tests/test_widget_llm.py`의 독스트링(`e2e/stack.ts`, `e2e/env.ts`), `web/apps/admin/e2e/stack.ts`의 머리 주석(위젯 준비를 선례로 든다), README의 트리, `docs/constitution/tech.md` 웹 행이다. 헌법을 고치면 판을 patch로 올린다. 기록(일지, 대기열, 명세, 닫힌 티켓)은 고치지 않는다

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 트레이스 주체를 보는 위젯 e2e 사례가 넘기는 길을 더하기 전에 빨갛다
- [ ] **위젯 e2e(`pnpm -C web/apps/widget exec playwright test`)와 `uv run --env-file .env pytest -m llm_widget`이 초록이다.** 위젯 e2e의 준비와 `tests/test_widget_llm.py`가 바뀌므로 둘 다 로컬에서 친다(`CLAUDE.md` 검증 명령)
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯과 위의 위젯 e2e·`-m llm_widget`이다
