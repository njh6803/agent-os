# 2026-11-16 (12:42) 위젯이 그리는 로그인 상태·고지·다크 모드 스위치의 명세를 쓴다 (widget-login-state)

세션 제목 `docs/widget-login-state-spec-2`. 브랜치 `docs/widget-login-state-spec-2`, 워크트리 `.claude/worktrees/widget-login-state-spec-2`. 모델 Fable 5.2. 일지 2026-11-16-0013의 "다음"이 낸 지시문으로 연 새 세션이다. 파일 이름의 시각은 일지 파일을 만든 때이고, 세션은 그보다 앞서 열렸다.

## 사용자 프롬프트

지시문을 그대로 옮긴다. 첫 줄은 `open-session`이 스킬 명령을 스킬 파일을 읽으라는 한 줄로 옮긴 꼴이다.

```
.claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: widget-login-state

다음 작업: 기능 widget-login-state. 화면이 모두 design/에 있고(PR #583으로 위젯 설정이 더한 화면 셋까지 병합) 기능 계획에 설계 줄만 있으므로 명세(spec.md)를 쓴다
다음 단계: 명세
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 widget-login-state-spec-2)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /to-spec widget-login-state
브랜치: docs/widget-login-state-spec-2
모델: Fable 5.2 / xhigh
읽을 것: 일지 docs/journal/2026-11-16-0013-widget-login-state-screens-2.md의 "다음" 절. 이어 .scratch/widget-login-state/design/README.md의 "명세가 정할 것"과 "위젯 설정이 더한 화면" 절, 앞 일지 docs/journal/2026-11-15-2058-widget-login-state-spec.md의 "다음"
이어받을 상태: PR #583 병합 완료(병합 커밋 f4a899194, 원격 브랜치는 저장소가 지웠다). 명세 세션이 알아야 할 후속 둘. (1) 앞 화면 작업의 아티팩트 94Gw...가 이 계정에서 열리지 않아 design/README.md 표의 앞 화면 열네 줄은 웹 편집 확인이 닿지 못한다. 사용자가 크롬에서 그 아티팩트의 Share로 이 계정에 편집 권한을 주면 확인할 수 있고, 공유 설정은 사람이 직접 누른다. 명세가 그 열네 줄을 근거로 읽을 때 이 점을 알린다. (2) 예시 질문의 모양(갈래 5의 세 모양)은 위젯 설정의 고르는 값 셋째다. ADR 0064 Consequences "화면"이 든 둘과 함께 portal-admin의 명세 전에 사용자에게 묻는다. 이 명세 세션이 묻는 일이 아니고 portal-admin 명세 세션 몫이니 명세에 넘길 것으로만 적는다. ADR 0059 결정 "화면"의 문장을 바꾸는 이력과 ADR 0061의 만료 알림 기본 모양 이력은 초안을 보이고 사용자 승인을 받는다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다. docs/portal-admin-screens 세션이 아직 돌면 .scratch/portal-admin/의 파일을 고치지 않는다. 그 워크트리가 .scratch/design-system/design/frontend-design-conflicts.md의 표 끝에 커밋하지 않은 변경이 있어 나중에 병합하는 쪽이 글자 충돌을 푼다
이번 요청 범위: PR과 병합까지
```

## 시작

작업 폴더가 `C:\project\agent`인 것을 보고 제목을 브랜치 이름으로 바꿨다.

`tidy-checkouts`를 주 체크아웃에서 돌았다.

- 루트: dev가 깨끗했고 원격에 없는 커밋이 0이라 `6cc678448`에서 `59536371f`로 당겼다.
- 지운 로컬 브랜치 둘: `worktree-portal-admin-screens`, `worktree-widget-login-state-screens-2`.
- 끝낸 것: 한 시간 넘게 쉰 세션 둘(`local_b61ee8bd-…`, `local_0e85fbd6-…`)의 `claude.exe`(pid 58784, 11268)를 `end-holders`로 끝냈다. 그 뒤 다시 판정해 워크트리 둘을 지웠다. `05-openai-compatible-adapter-and-local-model-test`(브랜치 `feature/05-openai-compatible-adapter-and-local-model-test`)와 `admin-login-screens`(브랜치 `docs/admin-login-screens`)다.
- 남긴 것: 나머지 워크트리는 도구가 든 이유(바뀐 파일, 병합된 PR 없음, 쥔 프로세스, 다시 만들 수 없는 무시된 항목, 앱의 표지)대로 남겼다. `넘긴다` 줄은 없었다.
- 휴지통: `empty-trash`가 종료 코드 1로 끝났다. `.claude/worktrees/.tidy-trash/` 아래 `web/node_modules` 아홉이 `esbuild.exe`를 올린 프로세스(`node.exe` pid 55668·22788, `esbuild.exe` pid 576·54260·59596·41384) 때문에 지워지지 않았다. 그 프로세스가 끝난 뒤의 정리가 다시 비운다.

`EnterWorktree`(name `widget-login-state-spec-2`)로 들어가 브랜치를 `docs/widget-login-state-spec-2`로 바꿨다. 기준은 `origin/dev`의 `59536371f`다. `uv run python tools/sibling_overlap.py`는 새 워크트리에 `.venv`를 짓느라(87 패키지, 3분 48초) 백그라운드로 넘어갔다가 0으로 끝났고, 번호 겹침과 함께 고친 파일이 없었다.

나란히 도는 세션은 `ListAgents`와 `list_sessions`로 봤다. `docs/portal-admin-screens`가 돌고 있어 `.scratch/portal-admin/`의 파일을 고치지 않는다. widget-login-state의 명세를 맡은 다른 세션은 없었다.

## 조사

읽은 것: `to-spec` 스킬, 일지 2026-11-16-0013의 "다음", 일지 2026-11-15-2058의 "사용자에게 물은 것"·"조사"·"다음", `.scratch/widget-login-state/design/README.md` 전체, `.scratch/widget-login-state/plan.md` 전체, `.scratch/widget-admin-server/plan.md` 전체, ADR 0061 전체, ADR 0064의 결정과 Consequences 가운데 이 행에 닿는 항목, ADR 0059 결정 "화면"과 이력 절, `.scratch/answer-markdown/spec.md`의 서두와 절 구조(명세의 꼴 선례), `docs/agents/issue-tracker.md`, `.claude/rules/probes.md`, `.scratch/admin-login/probes/`의 색인과 `cookie_relay/probe.mjs`(프로브의 꼴 선례), `CONTEXT.md`의 용어.

코드는 Explore 서브에이전트 둘에 맡겼다. 아래는 그 보고의 요지이고, 서브에이전트가 파일을 읽어 적은 것이다(본 세션이 다시 연 것은 `src/agent_os/http/sites.py`의 `MAX_LIFETIME_SECONDS = 600`과 `LEEWAY_SECONDS = 30`, `web/packages/e2e-stack/src`와 앱의 `e2e/`에 Docker·PostgreSQL 낱말이 0건이라는 것뿐이다).

- 위젯(`web/apps/widget`). 공개 표면 `EMBED.md`는 임베드 방식 둘(페이지 안, iframe), 속성 다섯(`agent`, `heading`, `intro`, `theme`, `mode`), 토큰 통로 둘(`tokenProvider`, 메시지 `agent-os/token-request`와 `agent-os/token`)을 적는다. 위젯이 사이트에 보내는 메시지는 토큰 요청 하나뿐이다. 위젯은 요청마다 토큰을 묻고(`drivers.ts`의 `authorize`), 토큰에서 `iss`와 `sub`만 읽으며 `exp`를 읽는 코드가 없다. 토큰을 받지 못했을 때와 서버가 401로 답했을 때는 버튼 없는 알림 "로그인 정보를 받지 못했습니다."가 서고, 보낸 글은 422와 429에서만 입력창으로 돌아온다. 브라우저 저장소는 탭 저장소 하나(열쇠 `agent-os-widget:<agent>`)이고 `localStorage`, `window.open`, `visibilitychange`, `BroadcastChannel`을 쓰는 곳이 없다. 화면 틀(`WidgetFrame`)은 슬롯 셋(위쪽 띠, 대화, 입력 자리)이고 덮개 자리가 없다. 디자인 시스템에는 메뉴, 덮개, 링크 부품이 없고 `Switch`는 있다. 시험은 네 높이다. jsdom 하네스(`testing/`의 `widget.tsx`, `network.ts`, `site.ts`. 가짜는 HTTP와 부모 창 둘뿐이다), 스토리 테스트, e2e(`e2e/`. 진짜 `serve`, 진짜 위젯 빌드, 중계, 사이트 서버), 사진 비교(`visual/`)이고, 실제 모델 수락은 `tests/test_widget_llm.py`가 e2e의 `llm` 프로젝트를 감싼다. Playwright의 브라우저는 Chromium 하나다.
- 위젯 미리보기 페이지(`web/apps/portal`). 설정은 TOML이고 `schema_version`은 글자 `"1"`이며 모르는 칸을 거부한다. 사이트 칸은 열(`name`, `issuer`, `agent`, `heading`, `intro`, `theme`, `mode`, `assurance`, `notice`, `report_url`)이다. 페이지가 지금 그리는 것은 띠의 사이트 고르기와 다크 모드 스위치, 고지 확인 덮개, 짧은 고지 줄과 "고지 전문" 펼침, 둘 다 사이트의 쓸 수 없는 로그인 단추 줄, 로그인 사이트의 안내 상자, 보고서 링크다. 토큰 끝점은 `POST /portal/sites/<이름>/token`이고 답은 JWT 글자 하나(평문)이며 수명은 120초다. 고지 확인은 `GET`·`POST /portal/sites/<이름>/acknowledgement`와 쿠키 `portal_anon`으로 기록한다. 위젯은 페이지 안 방식으로 넣고 속성 다섯과 `tokenProvider`를 넘긴다. 고지 전문에는 쿠키 문장을 늘 덧붙인다(`server/notice.ts`). 시험은 서버 단위 시험과 e2e 셋(`portal.e2e.ts`, `acknowledge.e2e.ts`, `sites.e2e.ts`)이고 실제 모델 수락은 `tests/test_portal_llm.py`다.

위젯 관리 서버의 명세(`.scratch/widget-admin-server/spec.md`)는 아직 없다. 위젯 설정을 받아 가는 경로와 답의 모양과 판 표시, 등록되지 않은 사이트의 답, 사이트의 이름의 꼴은 그 명세가 정하고 이 기능이 따른다(ADR 0064 결정 "위젯 설정을 받아 가는 주소").

## 프로브: 창 없이 부르는 로그아웃이 통하는 조건

ADR 0061 Consequences "재지 않은 것"이 이 명세에 맡긴 측정이다. `.scratch/widget-login-state/probes/logout_fetch/probe.mjs`를 지어 돌렸다. 짓는 법과 표지는 그 독스트링이, 결과와 재지 못한 것은 같은 폴더의 `README.md`가 원천이다.

- 첫 실행(Chromium 하나)에서 덤 갈래의 한 칸이 측정 아님으로 걸렸다. 다른 출처로 가는 `mode: "no-cors"`와 `redirect: "manual"`의 조합이고, 브라우저가 요청을 보내지 않았다(끝점에 닿은 POST가 0이고 `fetch`가 `TypeError`로 거절됐다). 프로브의 결함이 아니라 재야 할 사실이라, 같은 자리와 부르는 법의 `follow` 칸이 끝점에 닿았을 때만 "보내지 않았다"를 측정으로 세게 고치고 `cors` 모드의 칸을 더했다.
- 둘째 실행(`--engine all --update`)은 Chromium의 표지가 모두 섰고 `expected.json`에 그 결과를 적었다. Firefox와 WebKit은 뜨지 않았다. Playwright 1.63.0이 찾는 빌드(`firefox-1543`, `webkit-2359`)가 이 PC에 없고 있는 것은 옛 판(`firefox-1509`, `webkit-2248`)이다. 내려받기는 사용자의 승인이 필요한 일이라 하지 않았고, 두 엔진은 재지 못했다고 적는다.

## 사용자에게 물은 것

명세를 쓰기 전에 시험 이음매와 모양의 범위를 한 화면에서 물었다. 묻기 전에 "시험 이음매"가 무엇인지(어디까지를 진짜로 돌리고 어디부터를 가짜로 대신할지를 가르는 자리), 높이마다 무엇을 잡는지, 치르는 값이 무엇인지를 풀고 다섯 높이(규칙만 보는 시험, 위젯 화면 동작 시험, 화면 모양 시험, 실제 브라우저 시험, 실제 모델 수락 시험)를 장면과 함께 적었다. 훅이 첫 화면을 한 번 막아 선택지의 사실을 대 봤다. "시험이 위젯 설정을 데이터베이스에 직접 넣는다"는 기능 계획 12행에, 만료 알림의 모양이 0.1 판의 고르는 값이라는 것은 ADR 0061 결정 "0.1 판에서 등록하는 것"에, 나머지 세 갈래의 모양이 그 목록에 없다는 것은 ADR 0064 Consequences "화면"과 화면 문서에 있었고, 지금의 e2e 준비 코드에 Docker와 PostgreSQL 낱말이 0건이었다.

질문 1: "widget-login-state의 시험을 다섯 높이(규칙만 보는 시험, 가짜 사이트를 붙인 위젯 화면 동작 시험, 화면 사진 비교, 실제 브라우저 시험, 실제 모델 수락 시험)로 나누려고 합니다. 이 가운데 실제 브라우저 시험에서 위젯 설정을 어디서 받아 오게 할까요?"

- 선택지 "진짜 서버와 DB를 띄운다 (추천)": 실제 브라우저 시험이 위젯 관리 서버와 그 데이터베이스(PostgreSQL)까지 진짜로 띄우고, 시험이 위젯 설정을 데이터베이스에 직접 넣습니다. 기능 계획에 적힌 방법입니다. 얻는 것은 위젯이 진짜 서버의 답을 읽는 길 전체를 매번 본다는 점입니다. 치르는 값은 지금 Docker 없이 도는 실제 브라우저 시험에 데이터베이스를 띄우는 준비물이 생긴다는 점입니다.
- 선택지 "위젯 설정만 가짜 서버로": 실제 브라우저 시험에서는 시험용 작은 서버가 위젯 설정을 내주고, 진짜 위젯 관리 서버와 맞물리는지는 실제 모델 수락 시험에서만 봅니다. 얻는 것은 실제 브라우저 시험이 지금처럼 데이터베이스 없이 돈다는 점입니다. 치르는 값은 가짜 서버의 답이 진짜와 달라져도 수락 시험을 돌리기 전에는 알 수 없다는 점입니다.

> 사용자: 진짜 서버와 DB를 띄운다 (추천)

질문 2: "앞선 화면 작업에서 로그인 전 화면, 고지 전문을 보이는 법, 예시 질문, 만료 알림을 각각 세 모양으로 그렸습니다(모두 열두 모양). 이번 기능에서 위젯이 어디까지 그릴 줄 알게 지을까요? 나머지 모양을 운영자가 고르는 값으로 등록할지는 위젯 관리 화면의 명세 전에 따로 여쭙니다."

- 선택지 "기본 모양과 만료 알림 셋 (추천)": 위젯이 이번에 그리는 것은 여섯 모양입니다. 로그인 전은 대화 안의 카드, 고지 전문은 고지 줄 안에서 펼침, 예시 질문은 세로 목록이고, 만료 알림은 세 모양(대화 안의 카드, 위젯을 덮는 상자, 입력창 위 띠)을 모두 짓습니다. 만료 알림의 모양만 이미 0.1 판에서 등록하는 값으로 정해져 있기 때문입니다. 나머지 여섯 모양은 운영자가 고르는 칸을 지을 때 함께 짓도록 넘깁니다.
- 선택지 "열두 모양을 모두 이번에": 위젯이 열두 모양을 모두 그릴 줄 알게 지금 짓습니다. 운영자가 고르는 칸이 생기기 전까지 기본이 아닌 여섯 모양은 시험에서만 보입니다. 얻는 것은 나중에 고르는 칸만 더하면 된다는 점입니다. 치르는 값은 모양마다 화면 동작 시험과 사진이 늘어 이 기능의 티켓과 리뷰가 커진다는 점입니다.

> 사용자: 열두 모양을 모두 이번에

둘째 답은 추천과 다르다. 이 질문은 지시문이 이 세션에 금한 물음(세 갈래의 모양을 위젯 설정의 고르는 값으로 등록할지)이 아니라 이번 기능의 범위(위젯 코드가 그 모양을 지금 그릴 줄 알게 할지)를 물은 것이고, 등록할지는 질문 문장에 적은 대로 portal-admin의 명세 전에 따로 묻는다.

## 웹 편집 확인

화면 파일을 명세의 근거로 읽기 전에 `.claude/skills/ui-design/SKILL.md`의 "웹 편집 확인"을 했다. 아래는 손으로 본 것이다.

- "위젯 설정이 더한 화면" 절(아티팩트 `https://claude.ai/artifact/U366e3kPcujSdbjkYdmvZN`, 판 `1794762646-5d0f`). Artifact 도구의 `read`로 받은 파일 열넷과, 저장소의 `HEAD`(`59536371f`)에서 꺼낸 사본의 sha256을 견줬고 열넷이 모두 같았다. 저장소 쪽은 작업 트리가 아니라 커밋에서 꺼냈다(`git archive --format=tar -o <스크래치패드>/design-head.tar HEAD .scratch/widget-login-state/design`, `tar --force-local -xf`, `sha256sum`). 열넷은 `canvas-settings-additions.json`(아티팩트의 `project/canvas.json`), `ch-contact-1`, `ch-examples-1`·`2`·`3`, `sa-01`부터 `sa-09`다. `ch-contact-2`와 `ch-contact-3`은 디자인 `README.md`가 적은 대로 아티팩트에만 있다.
- 앞 절(아티팩트 `https://claude.ai/artifact/94Gw81HB8TQGoR21N8LuhM`). `list`가 "artifact not found — it may have been deleted, or it has not been shared with you"로 끝났다(같은 호출을 두 번 했다). 앞 절의 화면 스물넷과 `canvas.json`은 확인하지 못했고, 명세는 커밋된 판을 읽었다. 사용자가 크롬에서 그 아티팩트의 Share로 이 계정에 편집 권한을 주면 확인할 수 있다. 공유 설정은 사람이 직접 누른다.

`tar`가 `C:`로 시작하는 경로를 원격 호스트로 읽어 종료 코드 128로 끝났고, `--force-local`과 `/c/…` 경로로 풀었다.

## 명세

`.scratch/widget-login-state/spec.md`를 썼다. 꼴은 `to-spec`의 틀과 `.scratch/answer-markdown/spec.md`의 서두를 따랐다. 설계 인터뷰를 다시 열지 않았고 ADR 0061과 ADR 0064, 디자인 `README.md`, 기능 계획에서 합성했다.

명세가 스스로 정한 것 가운데 뒤의 단계에 영향이 큰 것이다.

- 토큰 답의 꼴은 여섯 갈래의 합이고(글자, `{token, signedIn?, name?}`, 상태 넷) 메시지 방식은 같은 칸을 메시지에 편다. 위젯이 통로에 싣는 까닭은 `reason` 하나에 값 둘이다.
- 토큰의 끝은 받은 때에 수명을 더한 시각과 `exp`를 PC의 시계로 읽은 시각 가운데 이른 쪽이고 10초 앞서 끝난 것으로 친다. 다시 쓴 토큰이 401이면 한 번 새로 물어 다시 보낸다.
- 위젯 설정의 답을 모형으로 옮기는 모듈 하나가 이음매다. 명세는 모형을 정하고, 경로와 답의 모양은 아직 없는 widget-admin-server의 명세를 따른다. 그래서 이 기능은 그 명세가 선 뒤에 티켓으로 쪼갠다.
- 열두 모양은 모두 짓되 위젯 설정의 답으로 닿는 것은 만료 알림의 모양뿐이다. 나머지 세 갈래의 기본 아닌 여섯 모양은 화면 부품에 값을 직접 주는 높이에서만 시험한다.
- 로그아웃은 본문 없는 POST에 `credentials: "include"`, `mode: "cors"`, `redirect: "manual"`이고 응답과 거절을 보지 않고 토큰을 다시 물어 판정한다. 근거는 프로브다.
- 실행이 서기 전에 막힌 질문은 까닭이 무엇이든 입력창에 되돌려 놓고, 주체가 바뀌면 대화와 함께 입력창도 비운다.
- 위젯 미리보기 페이지 설정의 `schema_version`은 `"2"`로 올리고, 그 페이지의 바탕은 기기의 설정을 따른다. 로그인 모드 사이트는 이 기능에서 바꾸지 않는다.
- ADR 0061이 e2e에 넘긴 넷은 어긋났을 때의 동작을 명세에 적어 두었다. 새 결정을 낳을 수 있는 것은 URL 방식의 창이 연 페이지와 메시지를 주고받지 못하는 경우 하나이고, 재려면 위젯 페이지가 있어야 해 URL 방식을 짓는 티켓의 첫 일로 두었다.

명세를 쓴 뒤 인용한 자리를 코드와 ADR에 대 보고 고친 것이다(코드를 읽었다).

- 위젯이 지금 토큰을 처음 묻는 때는 첫 질문만이 아니다. 탭 저장소에 저장한 대화가 있으면 뜰 때 묻는다(`useConversation.ts`).
- 401이 실행 전의 거절이라는 근거는 ADR 0023이 아니라 인증 미들웨어다(`src/agent_os/http/auth.py`. 자격이 맞지 않는 요청은 라우팅에 닿지 않는다).
- 그림의 가장 긴 예시 질문은 49자가 아니라 55자다(PowerShell의 `.Length`로 셌다). 49는 그 질문에 든 금액 "49,800원"을 잘못 옮긴 것이었다.
- 프로브를 든 문장 둘을 잰 범위로 좁혔다. `redirect`의 두 값은 덤 갈래의 두 자리와 `SameSite=Lax` 하나에서만 쟀고, "쿠키가 지워졌다"는 쿠키가 실린 칸의 결과다. 페이지 안 방식에서 로그아웃 주소가 페이지와 등록 도메인이 다른 자리는 재지 않았다고 더했다.
- 위젯 미리보기 페이지가 로그인 모드 사이트에 지금 보이는 것(위젯 자리의 알림과 끝점의 403)을 읽고(`web/apps/portal/server/handler.ts`, `page.ts`), 그 사이트는 이 기능에서 바꾸지 않고 portal-login에 넘기는 것으로 적었다. 첫 판은 그 사이트의 끝점이 `signed-out`을 답한다고 적었는데, 로그인이 아직 없는 페이지가 로그인하라고 안내하게 되는 문제가 있었다.
- 토큰의 주인을 가리키던 낱말 "묶음"을 용어집의 "주체"로 바꿨다. 같은 명세가 "묶음"을 단추의 무리와 고칠 자리의 무리에도 써서 뜻이 셋이었다.

받는 쪽 기능 계획에 적은 것은 `.scratch/portal-login/plan.md` 하나다. 토큰 답의 꼴을 따르는 것, 까닭 `continue-anonymous`를 받아 익명 주체로 바꾸는 것, 토큰 수명 120초를 다시 보는 것 셋을 넘겼다. `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다. `.scratch/portal-admin/plan.md`는 고치지 않았다. `list_sessions`에서 `docs/portal-admin-screens` 세션이 그 순간 돌고 있지는 않았지만 마지막 활동이 몇 분 전이었고 병합된 PR이 없어, 그 폴더의 일이 끝나지 않았다고 봤다.

## ADR 이력

명세가 본문의 문장을 바꾸는 ADR 둘에 2026-11-16 이력을 더하고 포인터를 달았다. 쓰기 전에 Skill 도구로 `domain-modeling`을 불렀다. `uv run python tools/check_adr_pointers.py`는 출력 없이 끝났다.

- ADR 0059: 이력 "로그인 만료로 막힌 질문은 다시 적지 않고 위젯이 입력창에 되돌려 놓는다". 포인터는 결정 "화면"의 "질문한 사람이 다시 적는다." 뒤 하나다. 거부한 안의 줄에는 달지 않았다(같은 ADR에서 ADR 0061이 다시 연 "팝업 창으로 로그인한다"에도 포인터가 없다).
- ADR 0061: 이력 "만료 알림의 기본 모양은 대화 안의 카드이고, 창 없이 부르는 로그아웃이 통하는 조건을 재서 고치며, 위젯 미리보기 페이지의 바탕은 기기의 설정을 따른다". 그 ADR의 첫 이력이라 `## 이력` 절을 새로 세웠다. 포인터는 셋이다. 결정 "다크 모드 스위치"의 바탕 문장, 결정 "로그아웃"의 통하는 조건 두 문장(이어진 묶음에 하나), Consequences "화면"의 만료 알림 문장이다. 결정 "로그아웃"의 "재 보지 않았다(어림)" 문장에는 달지 않았다. 그 문장은 결정이 아니라 그때의 근거를 적은 것이다(`.claude/rules/adr.md` "달지 않는 것").

ADR 0064에는 이력을 더하지 않았다. 명세가 문의 링크를 주소 하나로 정하고 주소의 검사를 그 주소까지 넓혔지만, ADR 0064의 문장(문의 링크는 글의 하나다, 로그인 주소와 로그아웃 주소는 형식만 검사한다)은 글자 그대로 여전히 참이다. 저장할 때의 검사를 문의 링크까지 넓힐지는 portal-admin의 명세가 정하고, 그때 그 ADR의 문장이 바뀌면 그 세션이 이력을 쌓는다.

## 인계

셀프 리뷰를 부른 자리에서 인계 계기(`hook_handoff`, 경계 `셀프 리뷰 직전`, 세션 컨텍스트 327,658 토큰)가 왔다. `next-session`의 `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않았다(계기를 낸 명령은 실패하지 않았고, 요청 범위는 병합까지이며, 이 세션의 지시문은 인계 줄이 아니고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다). 방금 불린 `code-review`의 단계는 밟지 않았다. 셀프 리뷰는 새 세션이 한다.

이 세션의 제목은 `docs/widget-login-state-spec-2`였다.

넘기는 때의 상태다.

- 커밋이 없다. 바뀐 파일은 `.scratch/widget-login-state/spec.md`(새 파일), `.scratch/widget-login-state/probes/`(새 폴더), 이 일지, ADR 0059와 ADR 0061(이력과 포인터), `.scratch/portal-login/plan.md`(넘긴 것 한 문단)다.
- 사용자에게 받은 답은 "사용자에게 물은 것"의 둘뿐이다. ADR 0059와 ADR 0061의 이력은 초안이고 승인받지 않았다. 셀프 리뷰를 반영한 뒤에 보이고 승인받는다(`CLAUDE.md` 작업 규약 5).
- 명세 서두의 수 셋(넘겨받은 것 스물, 사용자가 고른 것 열둘, 명세가 정한 것 스물넷)은 본문을 세어 맞춘 값이 아니다. 셀프 리뷰를 반영한 뒤에 센다(`to-spec`의 명세를 쓴 뒤의 차례).
- 셀프 리뷰의 명세 축에 넘길 요구는 지시문(위 "사용자 프롬프트"), `to-spec` 스킬의 틀, ADR 0061과 ADR 0064의 "명세가 짓는 것", 디자인 `README.md`의 "명세가 정할 것" 두 목록, 그리고 "사용자에게 물은 것"의 답 둘(선택지의 설명까지 글자 그대로)이다.
- 두 축에 밀 주장으로 나열할 것은 명세가 프로브를 든 문장("로그아웃" 절의 "이 부르는 법을 고른 근거", "통하는 조건", "재지 못한 것")과 ADR 0061 이력의 둘째 문단, 그리고 "코드를 읽었다"로 적은 자리(`useConversation.ts`의 토큰을 처음 묻는 때와 422·429의 되돌리기, `src/agent_os/http/auth.py`의 401, `src/agent_os/http/sites.py`의 30초 여유, `web/apps/portal/server/handler.ts`의 로그인 사이트 403)다.
- 끝 보고에서 사용자에게 알릴 것이다. 앞 화면 작업의 아티팩트가 이 계정에서 열리지 않아 앞 절의 화면 스물넷은 웹 편집 확인을 하지 못했다는 것, Firefox와 WebKit은 재지 못했고 재려면 내려받기 승인이 필요하다는 것, `tidy-checkouts`가 쉬는 세션 둘의 프로세스를 끝냈고 휴지통에 `web/node_modules` 아홉이 남았다는 것이다.

낸 지시문이다.

```
다음 작업: 기능 widget-login-state. 명세(spec.md)와 ADR 0059·0061의 이력 초안을 써 두었고 커밋 전이다. 셀프 리뷰부터 이어 PR과 병합까지 마친다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec widget-login-state
브랜치: docs/widget-login-state-spec-2
모델: Fable 5.2 / xhigh. 2의 잇는 지시문(명세). 모델 메뉴의 이름은 이 세션을 연 지시문의 값과 이 세션이 도는 모델(claude-fable-5-2)을 따랐다
읽을 것: 일지 docs/journal/2026-11-16-1242-widget-login-state-spec-2.md 전체(끝의 "인계" 절이 남은 차례다). 이어 .claude/skills/to-spec/SKILL.md의 명세를 쓴 뒤의 차례
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/dev)부터 한다. 일지는 docs/journal/2026-11-16-1242-widget-login-state-spec-2.md다. 명세를 새로 쓰지 않는다. 남은 차례는 셀프 리뷰 반영, 명세 서두의 수 세기(넘겨받은 것 스물, 사용자가 고른 것 열둘, 명세가 정한 것 스물넷은 세지 않고 적은 값이다), ADR 0059·0061 이력 초안을 사용자에게 보이고 승인받기(아직 받지 않았다), 커밋, PR, 병합, 회고다. 앞 화면 작업의 아티팩트 94Gw...는 이 계정에서 열리지 않아 앞 절의 화면 스물넷은 웹 편집 확인을 하지 못했고, Firefox와 WebKit은 Playwright 빌드가 없어 프로브가 재지 못했다(내려받기는 사용자 승인이 필요하다). 둘 다 끝 보고에서 알린다
확인할 선행 조건: docs/portal-admin-screens 세션이 끝났는지 보지 못했다. 그 세션의 일이 병합되기 전에는 .scratch/portal-admin/의 파일을 고치지 않고, 명세의 Out of Scope가 portal-admin에 넘긴 넷과 세 갈래 모양의 등록 여부를 묻는 일을 일지 "다음"에 그 명세 세션 몫으로 적는다. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `docs/widget-login-state-spec-2 (인계함)`으로 바꿨고, 띄운 백그라운드 작업은 없었으며, `git worktree unlock`으로 이 워크트리의 잠금을 풀었다.

open-session을 부른다 2026-11-16T04:31Z

## 이어받은 세션

위 "인계"가 낸 지시문으로 연 새 세션이 같은 일지를 잇는다. 세션 제목 `docs/widget-login-state-spec-2`, 모델 Fable 5.2. 지시문은 위 "낸 지시문이다"의 블록과 글자 그대로 같고, 그 앞에 `open-session`이 스킬 명령을 스킬 파일을 읽으라는 한 줄로 옮겨 붙였다(이 일지 "사용자 프롬프트"의 첫 줄과 같은 꼴이다).

- 작업 폴더가 `C:\project\agent`인 것을 보고 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 이 브랜치의 자리를 찾아 `EnterWorktree`(path)로 들어왔다. 커밋하지 않은 변경은 "인계"가 적은 여섯 자리 그대로였다.
- `ListAgents`에서 앞 세션(`docs/widget-login-state-spec-2 (인계함)`)과 `docs/portal-admin-screens`가 busy였다. 앞 세션은 인계를 마치는 중이라고 봤고(어림, 그 세션의 화면은 보지 않았다) 목록에 widget-login-state의 명세를 맡은 다른 세션은 없었다.
- `git fetch origin dev` 뒤 `origin/dev`는 `aa215fa3b`였다(이 브랜치의 기준 `59536371f`에서 세 커밋 앞). `git diff --name-only HEAD...origin/dev`의 열 파일은 release-image의 티켓과 프로브, `deploy/images/serve.Dockerfile`, 루트 `README.md`, 대기열 항목 하나, 일지 하나이고, 이 브랜치가 이름으로 든 파일이 없었다.
- `uv run python tools/sibling_overlap.py`는 번호 겹침 없이 끝났다. 함께 고친 파일로 `portal-admin-screens` 워크트리의 커밋하지 않은 변경 둘(`.scratch/portal-login/plan.md`, ADR 0059)을 냈다. 나중에 병합하는 쪽이 글자 충돌을 푼다.
- 프로브를 이 워크트리에서 다시 돌렸다(`node .scratch/widget-login-state/probes/logout_fetch/probe.mjs --engine chromium`). 표지 다섯이 모두 섰고(브라우저를 띄웠다, 표지가 빠진 칸이 없다, 대조, 양성 대조, `SameSite`가 걸리는 환경) "expected.json 과 모두 같다"로 끝났다.

## 셀프 리뷰

`code-review`는 이 워크트리 사본의 `SKILL.md`를 Read로 열어 따랐다(세션을 연 주 체크아웃의 사본이 아니다). 고정점은 `origin/dev`이고 base는 `59536371fe7c03e5bb65b6f6180cab8ebebb2d72`다. 범위는 추적 파일 셋의 diff, 미추적 여섯(명세, 프로브 넷, 이 일지), 커밋 0이다. 표준 축은 sonnet·high로, 명세 축은 모델을 주지 않고 띄웠다. 명세 축의 요구는 "인계"가 적은 다섯(지시문, `to-spec`의 틀, ADR 0061과 ADR 0064, 디자인 `README.md`의 "명세가 정할 것" 둘, 사용자의 답 둘을 선택지의 설명까지 글자 그대로)과 기능 계획이다.

### 표준 축의 보고

서브에이전트의 보고를 줄여 옮긴다. Critical과 Major는 없었고 아래는 모두 Minor나 Nit이다. 그 축은 `tools/check_adr_pointers.py`가 0으로 끝난 것과 프로브를 `--engine chromium`으로 다시 돌려 "expected.json 과 모두 같다"로 끝난 것을 함께 보고했다.

1. Minor, 명세 "사람이 그사이 적은 글". 입력창의 값을 되돌릴 글로 바꾸는 곳은 `useConversation.ts`가 아니라 `setDraft`를 넘기는 `ConnectedWidget.tsx`다. 동작은 맞고 든 파일이 틀렸다.
2. Minor, 명세 "로그인 모드 사이트". 따옴표 안의 한 문장은 `handler.ts`의 403 본문이고, 페이지의 알림은 `page.ts`의 제목과 본문 두 줄이다.
3. Minor, 명세 서두. "바뀌는 ADR 문장은 셋"인데 포인터는 넷이다(ADR 0059에 하나, ADR 0061에 셋).
4. Minor, 수로 닫은 주장의 반례 넷. "표면에 더하거나 바꾸는 것은 여섯"은 `agent`가 필수가 아니게 된 것과 스위치가 모든 위젯에 보이는 것을 뺐다. "새로 묻는 때 넷"에는 401 뒤의 물음이 들지 않는다. "막히는 길은 넷"은 방금 받은 토큰의 401과 5xx·네트워크 실패를 뺐고 "어느 까닭으로 막혔든"과 맞지 않는다. "e2e가 재는 넷" 밖에도 "e2e가 잰다"고 적은 자리가 있다.
5. Minor, ADR 0061의 남은 문장. Consequences "재지 않은 것"의 "통하는 조건은 명세가 재고"가 미래형 그대로이고 포인터가 없다. 결정 "로그아웃"의 "재 보지 않았다(어림)" 문장은 "그때의 근거" 예외로 설명할 수 있어 판단 사항이라고 했다.
6. Nit, 명세 "통하는 조건". "위젯이 도는 문서와 로그아웃 주소가 같은 등록 도메인이면 통했다"는 프로브가 잰 것보다 넓다. 프로브는 감싼 페이지를 늘 로그아웃 주소와 같은 등록 도메인에 두었다.
7. Minor, `to-spec`. Implementation Decisions에 구현 파일 경로 다섯과 프로토타입에서 오지 않은 `TokenAnswer` 조각이 있다. 근거 문장을 위한 인용이라는 점이 완화한다고 했다.
8. Minor, `to-spec` Out of Scope. 받는 쪽의 `Blocked by`가 이 기능을 포함하는지가 명세에 없다.
9. Nit, 명세 서두. "ADR 0061의 결정 열둘"이라 적었지만 그 ADR의 결정 항목은 열일곱이다.

냄새 기준선(모두 판단 항목, `probe.mjs`): `runCell`의 인자 일곱과 불리언 기본값 `siblingArrived`, 함께 다니는 인자 묶음 둘, `runEngine`의 `unmeasured` 기록 블록이 두 번 나오는 것, `redirect === null`이 "덤 갈래 없음"을 뜻하는 것.

주장 검증에서 맞다고 본 것: 프로브 README의 표 둘과 "읽는 법", 명세 "로그아웃"의 세 항목, ADR 0061 이력의 둘째 문단을 `expected.json`의 칸마다 댄 것(6번만 예외), ADR 0059·0061·0064의 절 이름과 포인터 넷의 글, 선택지 라벨 셋, `EMBED.md`의 인용과 절 이름, 수와 이름(속성 다섯, `schema_version` `"1"`, 120초, 30초, 55자, 완성 화면 스물셋, 앞 절 스물넷, 열셋과 색인, 시험 파일 이름), `useConversation`의 뜰 때 묻는 흐름, `auth.py`의 401, `ComposerBand`의 띠 셋. 확인하지 못했다고 한 것: 아티팩트의 sha256, 열리지 않는 아티팩트, 프로브의 28초, 일지의 "87 패키지", `restoreSaved`의 안쪽, 명세가 ADR 0023을 "까닭을 말하지 않는다"로 줄인 것, portal-admin과 portal-login 기능 계획의 `Blocked by`.

### 명세 축의 보고

서브에이전트의 보고를 줄여 옮긴다. Critical은 없고 Major 아홉, Minor 아홉, Nit 둘이다. 그 축은 코드를 읽기만 했고 프로브와 함수는 돌리지 않았다고 했다.

빠졌거나 부분인 것이다.

- A1 Major, "수락 문장의 자리". URL 방식의 수락 질문을 `-m llm_portal`이 본다고 적었는데 위젯 미리보기 페이지는 페이지 안 방식뿐이고 `-m llm_widget`은 `site` 없는 위젯으로 둔다. URL 방식의 창을 열고 토큰과 고지 확인에 답할 사이트가 어느 시험에도 없다.
- A2 Major, "주소의 검사". 호스트 이름이 정확히 `localhost`인 주소만 받는데 e2e의 브라우저 주소는 `*.localhost`와 `127.0.0.1`이다. 시험용 사이트의 로그인·로그아웃 주소가 검사에 걸려 단추가 서지 않는다.
- A3 Major, Out of Scope. widget-admin-server에 바라는 것 둘을 그 기능 계획에 적지 않았는데 그 명세가 먼저 쓰인다. "꼴에 맞지 않는 이름은 그 서버가 등록되지 않은 사이트로 답한다"는 ADR 0064가 그 명세에 맡긴 것을 사실로 적었다.
- A4 Major, "재지 않은 것이 어긋났을 때". 돌아온 신호가 오지 않을 때 "다음 요청의 새 물음이 대신한다"고 했는데 `signed-out` 화면은 입력창이 막혀 다음 요청이 없다. URL 방식의 창이 연 페이지와 메시지를 주고받는지는 프로브가 이미 창을 `window.open`으로 띄우므로 지금 잴 수 있다.

요구 밖이다.

- B1 Major, "주소의 검사". 사용자 정보(`user:pw@`)가 든 주소를 받지 않는다는 것은 ADR 0064 Consequences "명세가 짓는 것"이 portal-admin의 명세에 맡긴 물음이다.
- B2 Minor. 창의 크기를 주지 않는 것과 바탕이 기기의 설정을 따르는 것은 이력 승인 화면에서 대안과 함께 보여야 한다.

틀려 보이는 것이다.

- C1 Major. "로그인 전의 세 모양에서 본문은 같다"인데 `ch-gate-2`에는 제목이 없고 `ch-gate-3`은 글이 다르다.
- C2 Major. "카드와 띠 모양에서는 입력창을 막지 않는다 … 보내기를 누르면 위젯이 다시 물어"인데 `mk-08`은 보내기가 막혀 있다. "예시 질문" 절은 만료를 "입력이 막힌 화면"에 넣어 명세 안에서도 어긋난다.
- C3 Major. URL 방식에서 물을 곳이 없을 때의 로그인 상태 줄을 "로그인하지 않음"과 쓸 수 없는 로그인 단추로 적었는데, `mk-11a`의 연 페이지가 닫힌 화면은 이름과 쓸 수 없는 "로그아웃"이다.
- C4 Minor. "로그인 없이 계속"을 고른 사람이 글을 다시 적어야 한다는 대가는 같은 카드의 "적어 둔 질문은 입력창에 남아 있습니다."와 어긋나고, 사용자가 고른 "입력창에 남기기"를 좁힌다.
- C5 Minor. "로그아웃하지 못했습니다"와 "이 창을 연 페이지에서 다시 열어 주세요"는 그림과 마침표가 다르다.
- C6 Minor, 빈 자리 넷. 짧은 줄만 있고 전문이 없을 때가 표와 "고지" 절에서 다르게 읽힌다. "새로 묻는 때 넷"에 상태 답을 든 채 보내기를 누를 때가 없다. "남는 것"에 로그인 모드 사이트의 알림이 빠졌다. Out of Scope의 끝 문단이 portal-login을 "더하지 않았다"와 "적었다" 양쪽에 든다.

주장 검증에서 어긋났다고 한 것이다.

- V1 Major. 명세가 고른 부르는 법(`cors`에 `redirect: "manual"`)은 대부분 잰 칸이 아니다. 본 갈래의 쉰네 칸은 `redirect`를 주지 않아 `follow`로 돌았고, `cors`와 `manual`의 조합은 덤 갈래의 자리 둘에 `SameSite=Lax` 하나뿐이다.
- V2 Minor. "통하는 조건"의 축이 프로브와 다르다. 프로브가 견준 것은 위젯의 출처와 사이트이고 로그아웃 주소는 한 자리만 빼고 사이트의 것이다(표준 축 6과 같은 자리).
- V3 Minor. ADR 0061 이력 둘째 문단이 프로브 README "재지 못한 것"의 것으로 든 "페이지 안 방식에서 로그아웃 주소가 페이지와 등록 도메인이 다른 자리"가 그 절에 없다.
- V4 Minor. ADR 0061 Consequences "신뢰와 노출"의 "사이트가 자기 로그아웃 끝점을 위젯의 출처에 열어야 하고"는 이력이 범위를 바꾸는데 포인터가 없다.
- V10 Minor. 서두의 "바뀌는 ADR 문장은 셋"(표준 축 3과 같다)과 Solution의 "달라지는 것은 둘이다". 뒤의 것은 명세가 정한 것만으로 넷이 더 있다(`site` 없는 위젯도 뜰 때 묻는다, 401에 다시 보낸다, 되돌린 글이 덮지 않는다, 최상위 창이면 URL 방식으로 돈다).
- V11 Nit(표준 축 1과 같다), V12 Nit("모양 값 넷이 닿는 길"이 셋을 ADR 0064 Consequences "화면"의 것으로 들었는데 그 절은 둘만 들고 셋째는 디자인 `README.md`가 든다).

문제를 찾지 못했다고 한 묶음: ADR 절 이름 열여섯 곳, ADR 0059 이력이 옮긴 문장과 포인터 넷의 제목, 코드를 읽었다는 자리(`sites.py`의 30초, `auth.py`의 401, `useConversation.ts`의 뜰 때 묻는 조건, `handler.ts`의 403), 프로브 문장(V1~V3 제외), 화면 문구(만료 제목과 본문 두 꼴, 로그인 전 제목과 본문, 55자), 디자인 `README.md`의 "명세가 정할 것" 두 목록, ADR 0061 "명세가 짓는 것"의 항목 전부, 사용자의 답 둘, 지시문, 틀의 일곱 절. 받는 쪽의 `Blocked by`는 portal-login, portal-admin, widget-appearance가 이 기능을 들고 step-up-login은 portal-login을 거쳐 기다리며, widget-admin-server는 이 기능보다 먼저다. 확인하지 못했다고 한 것: 앞 절 화면의 웹 편집 여부, `expected.json`의 칸별 값, `auth.py`와 `sites.py`를 불러 보는 일, `mk-02`·`mk-09`·`mk-10`·`sa-*`의 나머지 문구, pilot-portal 명세의 절 이름과 ADR 0050·0060, 위젯이 `iss`와 `sub`로 주체를 견준다는 코드, 위젯 미리보기 페이지의 토큰 끝점이 쿠키 없을 때 지금 내는 답.

### 반영: 다시 잰 것

Major 가운데 둘(V1, A4)은 글을 고쳐서는 닫히지 않아 프로브를 넓히고 새로 지었다. 측정을 다음 단계에 넘길 때 결과가 새 결정을 낳을 수 있으면 그 자리에서 잰다는 `to-spec`의 규칙을 따랐다.

- V1과 V3. `logout_fetch/probe.mjs`를 넓혔다. 위젯이 도는 자리 여섯을 일곱으로(페이지 안 방식에서 로그아웃 주소가 등록 도메인이 다른 자리를 더했다), 부르는 법 셋을 다섯으로(명세가 고른 `mode: "cors"`, `redirect: "manual"` 둘을 더했다), 끝점이 303으로 답하는 덤 갈래를 자리 둘과 `SameSite=Lax`에서 자리 일곱과 `SameSite` 셋으로 넓혔다. 본 갈래 105칸, 덤 갈래 126칸이다. 결과는 명세가 고른 부르는 법이 견준 다른 부르는 법과 같은 자리에서 통했다는 것이고, 새 자리는 iframe 방식과 URL 방식의 등록 도메인이 다른 자리와 같았다(`Lax`와 `Strict`는 통하지 않았고 `None`은 통했다). 첫 판이 잰 62칸은 넓힌 판에서 모두 같은 값이었다(손으로 봤다. 넓히기 전의 `expected.json` 사본과 칸마다 `JSON.stringify`로 견주는 한 줄을 `node -e`로 돌렸다).
- A4. `opener_message/`를 새로 지었다. 위젯의 창의 출처 셋과 여는 법·그 뒤의 일 열하나의 33칸이다. `window.open`으로 연 창은 출처 셋 모두에서 물음과 답을 주고받았으므로 ADR 0061 결정 "URL 방식"은 그대로다. 본문에 없던 것이 둘 나왔다. `rel`을 적지 않은 `target="_blank"` 링크로 연 창과, 사이트의 페이지가 `Cross-Origin-Opener-Policy: same-origin`을 낸 창은 `window.opener`가 `null`이었다.
- 두 프로브가 함께 쓰는 것(자체 서명 인증서, 이름 몇 개의 `CONNECT`만 로컬 서버로 잇는 프록시, `expected.json`과의 견줌)은 `probes/kit.mjs`로 뽑았다.

다시 돌린 명령이다.

- `node .scratch/widget-login-state/probes/logout_fetch/probe.mjs --engine chromium --update` 한 번, 그 뒤 `--update` 없이 두 번. 세 번 모두 표지가 섰고 뒤의 두 번은 "expected.json 과 모두 같다"로 끝났다. `time`으로 잰 두 번은 3분 59초와 3분 55초다.
- `node .scratch/widget-login-state/probes/opener_message/probe.mjs --engine chromium --update` 한 번, 그 뒤 `--update` 없이 한 번. 20초이고 "expected.json 과 모두 같다"로 끝났다.
- `uv run python tools/check_adr_pointers.py`는 이력과 포인터를 고친 뒤 출력 없이 끝났다. `uv run python tools/plan_table.py`도 출력 없이 끝났다.

### 반영: 고친 것

새로 쓴 사실 문장은 원문으로 옮기고 근거를 붙인다.

- V1, V2, 표준 6(명세 "로그아웃"). "이 부르는 법을 고른 근거", "통하는 조건", "재지 못한 것"을 넓힌 측정에 맞춰 다시 썼다. 원문: "그 문서의 출처와 로그아웃 주소의 출처가 같거나 같은 등록 도메인 아래인 네 자리에서는 쿠키의 `SameSite`가 `Lax`, `Strict`, `None` 가운데 무엇이든 통했다." 근거는 `probes/logout_fetch/expected.json`과 그 README의 표 둘이다. 문장은 "이 부르는 법으로 부른 칸"으로 좁혔다. 덤 갈래의 `mode: "no-cors"`에 `redirect: "manual"`을 준 칸이 다른 출처에서 끝점에 닿지 않아, 잰 칸마다 같았다고 적으면 반례가 생기기 때문이다.
- A4(명세 "새 창 로그인과 돌아온 신호", "URL 방식", "재지 않은 것이 어긋났을 때"). 새 글머리 "신호가 오지 않아도 닿는 길"을 더했다. 원문: "지난 답이 `signed-out`이나 `expired`여서 질문을 보낼 수 없는 화면에서는 사람이 위젯 안을 누를 때 토큰을 다시 묻는다." 이것은 측정이 아니라 명세가 정한 동작이다. "URL 방식"에는 "연결이 서는 조건"을 더했다. 원문: "`window.open`으로 연 창은 위젯의 출처가 사이트의 페이지와 같은 출처이든, 등록 도메인이 같은 다른 출처이든, 등록 도메인이 다른 출처이든 물음과 답을 주고받았다." 근거는 `probes/opener_message/expected.json`과 그 README의 표다. 절 제목의 "어림"을 프로브를 가리키는 말로 바꿨다.
- A2(명세 "주소의 검사", ADR 0064 이력 초안). 원문: "이 저장소의 e2e가 사이트와 위젯을 `http://site.localhost:<포트>`와 `http://widget.localhost:<포트>`에 세우므로(`web/apps/widget/e2e/stack.ts`, 코드를 읽었다) `localhost` 하나만 받으면 시험용 사이트의 로그인 주소와 로그아웃 주소가 이 검사에 걸린다." 근거는 그 파일의 76~78행과 `web/apps/portal/e2e/stack.ts`의 79~81행이다(Grep으로 `.localhost`를 찾아 읽었다). 예외를 `.localhost`로 끝나는 이름까지 넓히는 것은 ADR 0064 결정 "주소의 검사"의 문장을 바꾸므로 그 ADR에 이력 초안을 쓰고 사용자에게 묻는다.
- B1(명세 "주소의 검사"). 사용자 정보 자리와 쿼리를 받을지는 portal-admin의 명세가 정하고 위젯의 검사는 그 답을 따른다고 고쳤다.
- A1(명세 "수락 문장의 자리", "고칠 시험"). URL 방식 창에서의 수락 질문은 `-m llm_widget`에 사례를 하나 더해 본다고 고쳤다. 위젯 미리보기 페이지는 페이지 안 방식 하나라 그 창을 열어 줄 페이지가 없기 때문이다.
- A3(명세 Out of Scope, `.scratch/widget-admin-server/plan.md`). widget-admin-server의 명세에 바라는 것 넷을 그 기능 계획에 한 문단으로 적었다. 꼴에 맞지 않는 이름의 답은 사실이 아니라 바라는 것으로 고쳤다.
- C1(명세 "로그인 상태의 화면"). 로그인 전 세 모양의 글을 그림마다 적었다. 근거는 디자인 폴더의 `ch-gate-1`, `ch-gate-2`, `ch-gate-3`이다(세 파일을 읽었다).
- C2(명세 "만료 알림과 되돌려 놓는 질문", "예시 질문"). 알림이 선 동안 보내기가 막힌다고 고쳤고(`mk-08`), "입력이 막힌 화면"을 "질문을 보낼 수 없는 화면"으로 고쳤다.
- C3(명세 "URL 방식"의 "물을 곳이 없을 때"). 로그인 상태 줄이 앞서 받은 답대로 남는다고 고쳤다(`mk-11a`의 두 화면).
- C4(명세 "만료 알림과 되돌려 놓는 질문", ADR 0059 이력). 새 글머리 "'로그인 없이 계속'은 글을 남긴다"를 더하고 ADR 0059 이력의 문장에 그 예외를 더했다. 사용자가 고른 "입력창에 남기기"를 좁히지 않기 위해서다.
- C5(명세 "문구"). 두 문구에 그림대로 마침표를 붙였다.
- C6(명세 "고지", "토큰을 다시 쓰는 규칙", "위젯 미리보기 페이지", Out of Scope). 짧은 줄과 전문의 네 조합을 적었고, 새로 묻는 때의 둘째를 "쓸 토큰이 없는 채 요청을 보내려 할 때"로 넓혔으며, 남는 것에 로그인 모드 사이트의 알림을 더했고, Out of Scope의 끝 문단을 받는 쪽마다 한 줄로 다시 썼다.
- 표준 1과 V11. 든 파일을 `ConnectedWidget.tsx`로 고쳤다. 표준 2. 알림의 제목과 본문(`page.ts`)과 403의 글(`handler.ts`)을 갈랐다.
- 표준 4와 V10(수로 닫은 주장). "공개 표면에서 바뀌는 것"과 Solution의 "달라지는 것"을 일반 조항과 예시로 고쳤다. "새로 묻는 때"는 ADR 0061이 적은 넷과 명세가 더한 401 하나로 갈랐다. "되돌려 놓는 규칙"은 실행이 서지 않은 채 막힌 것을 위젯이 아는 때로 일반화했다(401, 422, 429. 5xx와 네트워크 실패는 지금처럼 결말을 준다). 원문: "422와 429는 지금도 되돌린다(`web/apps/widget/lib/rejection.ts`, 코드를 읽었다)." "e2e가 재는 것"은 넘긴 넷과 명세가 더한 CSP `connect-src` 하나로 적었다.
- 표준 3과 서두의 수. 포인터를 단 자리는 여덟(ADR 0059 하나, ADR 0061 다섯, ADR 0064 둘), 이력은 넷, 프로브는 둘로 고쳤다. `(바뀜: 이력 2026-11-16`을 Grep으로 세어 아홉 포인터가 여덟 자리에 있는 것을 봤다(ADR 0061 Consequences "재지 않은 것"에 둘이 이어 달렸다).
- 표준 5, V3, V4(ADR 0061). 이력 둘째 문단을 넓힌 측정에 맞춰 다시 썼고(재지 못한 것에서 페이지 안 방식의 자리를 뺐다), 포인터를 Consequences "신뢰와 노출"의 끝 문장과 "재지 않은 것"에 더했다. URL 방식의 측정은 같은 날의 둘째 이력으로 따로 썼다. 이 세션에서 이력을 더 쓰기 전에 Skill 도구로 `domain-modeling`을 불렀다.
- 표준 8(명세 Out of Scope). 받는 쪽의 `**Blocked by:**`를 읽어 기다리는 차례를 적었다.
- 표준 9(명세 서두). "ADR 0061의 결정 가운데 이 기능이 짓는 열둘"로 고쳤다.
- V12. "모양 값 넷이 닿는 길"과 Out of Scope의 인용을 둘로 갈랐다. 디자인 `README.md` 81행이 셋째(예시 질문의 모양)를 든다.

### 반영: 남긴 것과 이유

- 표준 7(구현 파일 경로와 `TokenAnswer` 조각). 남긴다. 경로는 "코드를 읽었다"는 근거 문장의 인용이고, `TokenAnswer`는 공개 표면의 꼴이라 이 명세가 정하는 것 자체다.
- 냄새 기준선(`probe.mjs`의 인자 수와 되풀이 블록). 남긴다. 프로브는 `.scratch`의 측정 스크립트이고 두 프로브가 함께 쓰는 부분은 `kit.mjs`로 뽑았다.
- B2(창의 크기, 바탕의 밝기). 고치지 않고 승인 화면에서 대안과 함께 묻는다(아래 "ADR 이력 승인").

## ADR 이력 승인

셀프 리뷰를 반영한 뒤 `AskUserQuestion` 한 화면에 넷을 올렸다. 화면을 올리기 전에 초안이 든 ADR 세 파일의 경로와 ADR 0064의 초안이 둘째 물음의 추천안을 가정하고 쓴 것임을 글로 알렸다. 첫 호출은 선택 화면의 사실을 대 보라는 훅이 한 번 막았다. 대 본 것은 이력 초안의 수(ADR 0059에 하나, ADR 0061에 둘), ADR 0064 결정 "주소의 검사"의 문장(20행), e2e의 주소 이름(`web/apps/widget/e2e/stack.ts` 76~78행, `web/apps/portal/e2e/stack.ts` 79~81행), 위젯 미리보기 페이지가 지금 바탕을 설정 파일의 `mode`에 맞추는 것(`web/apps/portal/browser/portal.ts`의 `effectiveMode`와 `data-mode`를 Grep으로 읽었다)이다. 재 보지 않은 것(새 탭으로 열리는지, 쿠키와 포트, 작은 창의 크기)은 설명에 어림이라고 적고 다시 올렸다. 질문과 답은 글자 그대로다.

> 질문 1: ADR 0059와 0061에 쌓을 기록(이력) 초안 셋을 승인할까요? ① 로그인 시간이 끝나 보내지 못한 질문은 입력창에 남기고, '로그인 없이 계속'을 골라도 그 글은 남긴다. ② 만료 알림의 기본 모양은 대화 안의 카드이고, 위젯의 로그아웃 단추가 통하는 조건을 실제 브라우저(Chromium)로 재서 고쳤다. ③ 주소 하나로 여는 위젯 창(URL 방식)이 자기를 연 페이지와 토큰을 주고받는 조건을 쟀다(결정은 그대로다).
>
> 사용자: 셋 다 승인 (Recommended)
>
> 그 선택지의 설명: 초안 그대로 커밋합니다. 초안은 ADR 0059에 하나, ADR 0061에 둘입니다. 결정이 새로 더해지는 것은 ①의 '로그인 없이 계속을 골라도 적어 둔 글은 남긴다' 하나이고, ②와 ③은 이미 고르신 것과 프로브로 재 본 사실을 적는 것입니다.

고르지 않은 선택지는 "①의 예외만 빼기"('로그인 없이 계속'을 고르면 대화와 함께 입력창의 글도 지운다)와 "고칠 곳이 있다"였다.

> 질문 2: 위젯은 운영자가 등록한 로그인 주소와 로그아웃 주소가 https:// 로 시작할 때만 열고, 예외로 자기 PC에서 시험할 때 쓰는 http://localhost 만 받기로 했습니다(ADR 0064). 그런데 이 저장소의 자동 브라우저 시험은 http://site.localhost:포트 같은 이름을 씁니다. 시험용 예외를 어디까지 받을까요?
>
> 사용자: site.localhost 같은 이름도 받기 (Recommended)
>
> 그 선택지의 설명: 호스트 이름이 localhost 이거나 .localhost 로 끝나는 http 주소를 받습니다. 그런 이름은 그 PC 자신만 가리키는 것으로 알고 있어 바깥 주소가 새로 열리지는 않는다고 봅니다(어림이고 재 보지 않았습니다). 자동 시험의 주소 이름(코드에서 site.localhost, widget.localhost, portal.localhost 를 확인했습니다)을 바꾸지 않아도 되고, ADR 0064에 이력을 쌓습니다.

고르지 않은 선택지는 "localhost 하나만 받기"(ADR 0064의 문장을 그대로 두고 로그인과 로그아웃을 보는 자동 브라우저 시험의 사이트 주소를 `http://localhost:포트`로 다시 짠다)였다. 이 답이 ADR 0064의 2026-11-16 이력 "시험할 때 받는 http 주소를 호스트 이름이 .localhost로 끝나는 것까지 넓힌다"의 승인이다.

> 질문 3: 위젯의 '로그인하고 질문하기' 단추를 누르면 로그인 페이지가 새 창으로 열립니다. 어떤 모양으로 열까요?
>
> 사용자: 새 탭으로 열기 (Recommended)
>
> 그 선택지의 설명: 창의 크기를 주지 않고 엽니다. PC 브라우저 대부분에서 옆에 새 탭이 생기고 휴대폰과 같은 모양이라고 봅니다(어림이고 재 보지 않았습니다). 로그인한 뒤 원래 탭으로 돌아오는 일은 사람이 합니다.

고르지 않은 선택지는 "작은 창으로 열기"(크기를 정해 준 작은 창이 위젯이 든 페이지 위에 뜬다)였다.

> 질문 4: 위젯 미리보기 페이지(운영자가 위젯을 띄워 보는 페이지)에서 위젯 둘레 바탕의 밝기를 무엇에 맞출까요? 전에는 설정 파일의 밝기 값에 맞췄는데, 그 값이 위젯 설정(데이터베이스)으로 옮겨 가 이 페이지가 알 수 없게 됐습니다.
>
> 사용자: 보는 사람 기기의 설정 따르기 (Recommended)
>
> 그 선택지의 설명: PC가 다크 모드이면 어두운 바탕, 아니면 밝은 바탕입니다. 운영자가 위젯의 처음 밝기를 '어둡게'로 등록한 사이트는 밝은 바탕 위에 어두운 위젯이 설 수 있습니다. 페이지가 위젯 설정을 따로 받아 오지 않아 코드가 단순합니다.

고르지 않은 선택지는 "위젯 설정의 처음 밝기에 맞추기"(페이지가 위젯 설정을 한 번 더 받아 와 바탕을 처음 밝기에 맞춘다)였다.

답을 받은 뒤 고친 것이다. 명세 서두의 "사용자가 고른 것"을 열둘에서 열여섯으로 고치고 네 절(주소의 검사, 새 창 로그인과 돌아온 신호, 만료 알림과 되돌려 놓는 질문, 위젯 미리보기 페이지)에 사용자가 고른 것과 고르지 않은 안을 적었다. ADR 0061 이력의 셋째 문단에는 바탕을 사용자가 골랐다는 한 문장을 더했다. 승인받은 초안의 다른 글자는 고치지 않았다.

## 커밋

커밋 전에 `git branch --show-current`(이 브랜치), `git fetch origin dev`, `uv run python tools/sibling_overlap.py`를 쳤다. 번호 겹침은 없었고, 함께 고친 파일로 열린 PR #590(`portal-admin-screens`)의 셋(`.scratch/portal-login/plan.md`, ADR 0059, ADR 0064)이 나왔다. 나중에 병합하는 쪽이 글자 충돌을 푼다. `origin/dev`는 `aa215fa`이고 `git diff --name-only HEAD...origin/dev`의 열 파일에 이 브랜치가 이름으로 든 파일이 없었다. pre-commit에서 `Skipped`로 나올 ruff 둘은 손으로 쳤다(`uv run ruff check .`는 "All checks passed!", `uv run ruff format --check .`는 "2368 files already formatted").

커밋 `db82ac3b5`(`docs: 위젯의 로그인 상태와 고지와 URL 방식의 명세를 쓴다 (widget-login-state)`)다. pre-commit의 검사는 모두 통과했고 `parallel-checks`가 1229초 걸렸다(pytest 928초, web-verify 1229초. 다른 워크트리의 세션들이 함께 돌았다). `Skipped`는 ruff 둘(위에서 손으로 쳤다), canary specs, constitution version(둘 다 해당 파일이 없다)이다. 인용 대조는 경고 열하나를 냈고 막지 않았다. 그 가운데 둘은 인용이 아니라 내 문장에 따옴표를 친 것이라 커밋 뒤에 따옴표를 뗐다(명세 "공개 표면에서 바뀌는 것"의 `agent` 문장, `logout_fetch/README.md`의 첫 판 표지). 나머지 아홉은 이 일지가 리뷰 보고와 선택지를 줄여 옮긴 글이라 그대로 둔다. 따옴표를 뗀 두 파일과 이 절부터의 일지는 커밋하지 않았고 다음 커밋에 싣는다.

## 둘째 인계

커밋이 끝난 자리에서 인계 계기(`hook_handoff`, 경계 `커밋 뒤`, 세션 컨텍스트 324,560 토큰)가 왔다. `next-session`의 `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않았다(커밋은 성공했고, 요청 범위는 병합까지이며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 경계가 다르고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다).

이 세션의 제목은 `docs/widget-login-state-spec-2`였다.

넘기는 때의 상태다.

- 커밋 하나(`db82ac3b5`)가 있고 푸시하지 않았다. 열린 PR이 없다.
- 커밋하지 않은 변경은 셋이다. 이 일지(위 "커밋" 절부터), 명세의 따옴표 한 곳, `logout_fetch/README.md`의 따옴표 한 곳이다.
- 사용자에게 받은 답은 "사용자에게 물은 것"의 둘과 "ADR 이력 승인"의 넷이다. ADR 0059·0061·0064의 이력 넷은 승인받았다.
- 남은 차례는 PR 직전 리뷰와 그 반영, 푸시, PR 열기, PR 봇 회차, 병합, 회고, 일지 "다음"이다. 반영으로 명세 본문을 고치면 서두의 수를 다시 세고, 승인받은 이력의 글을 고치게 되면 사용자에게 다시 보인다.
- 일지 "다음"에 적을 것이다. portal-admin의 명세 세션 몫으로, 이 명세의 Out of Scope가 portal-admin에 넘긴 다섯을 그 기능 계획에 적는 일과 모양 값 셋(로그인 전의 모양, 고지 전문을 보이는 법, 예시 질문의 모양)을 위젯 설정에 등록할지 사용자에게 묻는 일이다. PR #590이 병합되기 전에는 `.scratch/portal-admin/`의 파일을 고치지 않는다.
- 끝 보고에서 사용자에게 알릴 것은 셋이다. 앞 화면 작업의 아티팩트가 이 계정에서 열리지 않아 앞 절의 화면 스물넷은 웹 편집 확인을 하지 못했다는 것, Firefox와 WebKit은 두 프로브가 재지 못했고 재려면 내려받기 승인이 필요하다는 것, 앞 세션의 `tidy-checkouts`가 쉬는 세션 둘의 프로세스를 끝냈고 휴지통에 `web/node_modules` 아홉이 남았다는 것이다.

낸 지시문이다.

```
다음 작업: 기능 widget-login-state. 명세와 프로브 둘과 ADR 이력 넷을 커밋했고 푸시 전이다. PR 직전 리뷰부터 이어 PR과 병합까지 마친다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec widget-login-state
브랜치: docs/widget-login-state-spec-2
모델: Fable 5.2 / xhigh. 2의 잇는 지시문(명세). 모델 메뉴의 이름은 이 세션을 연 지시문의 값과 이 세션이 도는 모델(claude-fable-5-2)을 따랐다
읽을 것: 일지 docs/journal/2026-11-16-1242-widget-login-state-spec-2.md 전체(끝의 "둘째 인계" 절이 남은 차례다). 이어 .claude/skills/to-spec/SKILL.md의 명세를 쓴 뒤의 차례
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영, 명세 서두의 수 세기, ADR 0059·0061·0064 이력 넷의 사용자 승인, 커밋 하나까지 했고 푸시하지 않았다. 일지는 docs/journal/2026-11-16-1242-widget-login-state-spec-2.md다. 명세를 새로 쓰지 않고 셀프 리뷰도 다시 돌지 않는다. 남은 차례는 PR 직전 리뷰와 그 반영(반영으로 명세 본문을 고치면 서두의 수를 다시 센다. ADR 이력의 승인받은 글을 고치게 되면 사용자에게 다시 보인다), 푸시, PR 열기, PR 봇 회차, 병합, 회고, 일지 "다음"이다. 워크트리에 커밋하지 않은 변경 셋(일지의 "커밋" 절부터, 명세의 따옴표 한 곳, logout_fetch/README.md의 따옴표 한 곳)이 있어 다음 커밋에 싣는다. 열린 PR #590(portal-admin-screens)이 .scratch/portal-login/plan.md와 ADR 0059와 ADR 0064를 함께 고쳐, 나중에 병합하는 쪽이 글자 충돌을 푼다. 끝 보고에서 사용자에게 알릴 것 셋(아티팩트 미확인, Firefox·WebKit 미측정과 내려받기 승인 필요, tidy-checkouts가 끝낸 프로세스와 휴지통)은 일지 "둘째 인계" 절의 목록 마지막 항목에 적혀 있다
확인할 선행 조건: PR #590(docs/portal-admin-screens)이 병합됐는지 보지 못했다. 그 일이 병합되기 전에는 .scratch/portal-admin/의 파일을 고치지 않고, 명세의 Out of Scope가 portal-admin에 넘긴 다섯과 모양 값 셋의 등록 여부를 묻는 일을 일지 "다음"에 그 명세 세션 몫으로 적는다. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `docs/widget-login-state-spec-2 (인계함)`으로 바꿨고, 띄운 백그라운드 작업은 모두 끝나 있었으며, `git worktree unlock`은 이미 풀려 있다는 오류(`is not locked`)로 끝나 넘어갔다.

open-session을 부른다 2026-11-16T06:19Z

그 줄을 적은 직후 자동 압축이 와서 스킬은 압축 뒤에 불렀다. 첫 호출은 딥링크의 URL이 8140자(상한 8000)라 `tools/open_session.ps1`이 쏘기 전에 거부했고 세션은 생기지 않았다. 위 지시문의 "이어받을 상태"에서 끝 보고의 세 문장을 이 절의 목록 마지막 항목을 가리키는 한 문장으로 줄였고(위 블록은 줄인 뒤의 글이다), 같은 프롬프트 파일로 다시 돌린다.

open-session을 부른다 2026-11-16T06:24Z

## 둘째로 이어받은 세션

위 "둘째 인계"가 낸 지시문으로 연 새 세션이 같은 일지를 잇는다. 세션 제목 `docs/widget-login-state-spec-2`, 모델 Fable 5.2. 지시문은 위 "둘째 인계"의 "낸 지시문이다" 블록과 글자 그대로 같고, 그 앞에 `open-session`이 스킬 명령을 스킬 파일을 읽으라는 한 줄로 옮겨 붙였다(이 일지 "사용자 프롬프트"의 첫 줄과 같은 꼴이다).

- 작업 폴더가 `C:\project\agent`인 것을 보고 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 이 브랜치의 자리를 찾아 `EnterWorktree`(path)로 들어왔다. 커밋은 `db82ac3b5` 하나였고 커밋하지 않은 변경은 "둘째 인계"가 적은 셋 그대로였다.
- `ListAgents`에서 앞 세션(`docs/widget-login-state-spec-2 (인계함)`)이 처음에는 busy였고 몇 분 뒤 idle이 됐다. widget-login-state의 명세를 맡은 다른 세션은 없었다. `gh pr view 590`은 `OPEN`이었고 `docs/portal-admin-screens` 세션이 돌고 있어, `.scratch/portal-admin/`의 파일은 고치지 않는다.
- `git fetch origin dev` 뒤 `origin/dev`는 `716e51d25`였다(앞 세션이 본 `aa215fa3b`에서 한 커밋 앞, PR #589). `git diff --name-only HEAD...origin/dev`의 열세 파일은 `.github/workflows/claude-code-review.yml`, release-image의 티켓 둘과 프로브, `deploy/images/`의 둘, 루트 `README.md`, 대기열 항목 하나, 일지 둘이고, 이 브랜치가 고친 파일이 없었다.
- `uv run python tools/sibling_overlap.py`는 번호 겹침 없이 끝났고, 함께 고친 파일로 PR #590의 셋(`.scratch/portal-login/plan.md`, ADR 0059, ADR 0064)을 냈다. 나중에 병합하는 쪽이 글자 충돌을 푼다.
- `git merge origin/dev --no-edit`로 기준 브랜치를 합쳤다(병합 커밋 `1747032ef`, 충돌 없음). 합친 까닭은 둘이다. PR #589가 `claude-code-review.yml`을 고쳤고, claude-review는 그 파일이 기본 브랜치의 것과 다르면 리뷰를 건너뛰면서 초록이 된다(`docs/constitution/operations.md` 리뷰 파이프라인). 그리고 PR 직전 리뷰가 보는 범위를 `origin/dev`와의 차이인 이 브랜치의 열다섯 파일로 맞추기 위해서다.

## PR 직전 리뷰

기준 브랜치를 합친 뒤 서브에이전트 둘을 나란히 띄웠다. `coderabbit-review`가 CLI 축(보안·버그·성능)을 보고, `bug-perf-review`는 셀프 리뷰를 반영하며 새로 쓴 사실 문장(밀 주장)만 근거와 대 보게 했다. CLI가 도는 PR에는 밀 주장을 넘기는 인자가 없어 따로 띄운 것이다(대기열 `cli-review-claims-path`). 두 브리프 모두 프로브를 돌리지 말라고 적었다. 아래 두 절은 서브에이전트의 보고를 줄여 옮긴 것이고, 본 세션이 다시 본 것은 "반영" 절에 따로 적는다.

### CLI 축의 보고 (`coderabbit-review`)

`coderabbit review --agent --base origin/dev --include-untracked`가 종료 코드 0과 `review_completed`로 끝났다(파일 15개, CLI 0.7.5, `Seat: not assigned`, `Plan: Free`). 끝까지 돌았으므로 CLI 축이 돌았고 대체 둘(`/security-review`, `bug-perf-review`의 버그·성능 몫)은 돌리지 않았다. CLI의 지적은 다섯이고 서브에이전트가 모두 유효로 갈랐다. 서브에이전트가 명세와 프로브를 직접 읽어 더한 것이 일곱이다. 오탐은 0건이라고 했다.

CLI의 지적이다.

1. Major, 명세 "로그아웃"의 "판정". 새 답이 로그인한 사람의 토큰이 아니면 모두 로그아웃된 것으로 본다. 그 밖의 답에는 `expired`, `denied`, `notice-required`와 토큰을 받지 못한 때가 든다. 로그아웃되지 않았는데 토큰 물음만 실패해도 로그아웃된 것처럼 그리고 글을 지운다.
2. Major, 명세 "묻는 때가 겹칠 때와 401". 401 뒤에 새로 받은 토큰의 주체가 앞의 것과 달라도 같은 요청을 그대로 다시 보낸다. 주체를 견주어 비우는 규칙이 다시 보내는 길에 이어져 있지 않다.
3. Major, 명세 "주체가 바뀌면 입력창도 비운다"와 "열린 응답 스트림은 토큰이 끝나도 끊지 않는다". 주체가 바뀌거나 `signed-out`을 받아 대화를 비울 때 열린 스트림을 끊는다는 말이 없어, 앞 사람의 실행이 낸 늦은 이벤트가 비운 화면을 다시 채울 수 있다.
4. Minor, 두 프로브의 `--update`. 표지가 빠졌거나 측정 아님 칸이 있는 회차에도 `expected.json`을 덮어쓴다(`opener_message/probe.mjs` 420~423행, `logout_fetch/probe.mjs` 609~611행).
5. Minor, `logout_fetch/probe.mjs` 333~335행. 요청이 끝점에 닿지 않은 칸을 `fetch`의 거절과 앞 칸이 닿았다는 것만으로 측정으로 센다. 거절의 까닭이 그 조합(`no-cors`와 `manual`)인지 일시적인 연결 오류인지를 가르는 표지가 없다.

서브에이전트가 직접 읽어 더한 것이다.

6. Major, 명세 "위젯 설정을 받아 오기"와 Out of Scope의 widget-admin-server에 바라는 것. 페이지 안 방식의 위젯은 사이트의 페이지에서 돌므로 위젯 설정을 받는 요청이 다른 출처로 나간다. 응답의 CORS 머리와 사이트 CSP의 `connect-src`가 명세에 없다.
7. Minor, 명세 "토큰 답의 꼴"과 "로그인 상태의 화면". 거절 알림은 다음 답이 `denied`가 아니면 사라지는데, 사이트는 거절을 한 번만 답하고 위젯은 돌아온 신호와 위젯 안을 누른 때에 다시 묻는다. 사람이 읽기 전에 알림이 사라질 수 있다.
8. Minor, 명세 "돌아온 신호". 신호마다 토큰을 새로 묻는데 간격의 제한이 없고, 위젯이 사라질 때 1초마다 보는 일과 이벤트 리스너를 치운다는 말이 없다.
9. Minor, 명세 "URL 방식". 위젯이 자기를 연 창에 물음을 보낼 때의 대상 출처가 정해져 있지 않다.
10. Minor, 명세 "임베드 속성 `site`". 값을 URL 인코딩만 해서 경로에 넣으면 `.`과 `..`이 경로 이동으로 풀린다.
11. Minor, 명세 "토큰을 다시 쓰는 규칙"의 "읽지 못하는 토큰". `iss`와 `sub`를 읽지 못하는 토큰의 주체를 앞의 것과 같다고 볼지 다르다고 볼지가 비어 있다.
12. Minor, 명세 "열지 못했을 때"의 두 링크. `rel`이 정해져 있지 않다(문의 링크에는 `rel="noopener"`를 적었다).

프로브를 직접 읽은 결과로는 끝나지 않는 프로세스나 서버가 없고 포트는 `listen(0)`으로 받아 겹치지 않는다고 했다. `openssl`이 PATH에 있어야 하고 `import.meta.dirname` 때문에 Node 20.11 이상이어야 한다는 전제를 README에 적는 편이 좋다고 했다(Minor, 보류).

### 밀 주장 검증의 보고 (`bug-perf-review`)

기준 `716e51d`, 범위 15파일이다. 보고는 마지막 호출 수를 33으로 적었는데 작업 알림의 도구 사용 수는 59였다. 지적은 Minor 하나다.

- Minor, 명세 "만료 알림과 되돌려 놓는 질문". "그림은 둘째 문장을 늘 그렸다"가 그림과 다르다. 둘째 문장 "적어 둔 질문은 입력창에 남아 있습니다."는 카드와 덮는 상자 그림에만 있고 띠 그림(`ch-expiry-3`, `mk-08`의 띠)에는 없다. 같은 띠 그림의 제목은 "로그인 시간이 끝났습니다."로 마침표가 있는데 명세는 마침표 없이 적었다.

맞다고 본 것은 아홉 묶음이다. 로그아웃 프로브의 수와 칸(본 갈래 105칸, 덤 갈래 126칸, `Sec-Fetch-Site`가 `cross-site`인 세 자리의 `Lax`·`Strict`만 통하지 않은 것, 고른 부르는 법의 칸 어디에서도 다음 주소를 부르지 않은 것), URL 방식 프로브의 33칸, e2e의 주소 이름, "코드를 읽었다"는 문장 다섯 자리, 화면 문구(위 지적만 예외), 서두의 수(넘겨받은 것 스물, 사용자가 고른 것 열여섯, "명세가 정했다" 괄호를 단 절 제목 스물셋과 그 가운데 한 절이 항목 둘이어서 스물넷, 포인터 아홉이 여덟 자리, 이력 넷), 받는 쪽 기능 계획의 `Blocked by`와 넘긴 문단, ADR 이력 넷의 사실 문장, 모양 값의 갈래다. 확인하지 못했다고 한 것은 `useConversation.ts`의 `restoreSaved` 안에서 토큰을 묻는지와, 범위 밖이라 보지 않은 그림의 나머지 문구다.

### 반영

본 세션이 지적 열셋을 근거와 대 보고 열둘을 고쳤고 하나를 남겼다. 고친 것은 모두 명세가 스스로 정한 절 안의 세부이고, 승인받은 ADR 이력 넷의 글은 고치지 않았다. 번호는 위 두 보고의 것이다.

명세(`.scratch/widget-login-state/spec.md`)에서 고친 것이다.

1. 로그아웃의 "판정"을 셋으로 갈랐다. 답이 로그인한 사람의 것이면(로그인한 사람의 토큰, 또는 `signedIn`이나 `name`을 실은 `notice-required`) "로그아웃하지 못했습니다."다. 로그인한 사람의 것이 아니면(`signed-out`, 로그인한 사람의 것이 아닌 토큰, `expired`, `denied`, `signedIn`과 `name`이 없는 `notice-required`) 로그아웃된 것이고 대화와 입력창의 글을 비운 뒤 답대로 그린다. 답을 받지 못했으면 판정하지 않고 다음 물음이 답을 받은 때에 같은 판정을 한다. 처음에는 이때의 `expired`를 `signed-out`과 같은 화면으로 그린다고 적었다가 고쳤다. `anonymous: true`인 `expired`에서 "로그인 없이 계속"이 사라지고, 뒤의 물음이 같은 답을 다시 받으면 화면이 만료 알림으로 바뀌기 때문이다. 지금 문장은 "대화가 없는 채 뜬 위젯이 그 답을 받은 때와 같다"다. 절 제목의 괄호를 "부르는 법과 판정은 명세가 정했다"로, 서두의 목록을 "로그아웃을 부르는 법과 판정"으로 맞췄다. 근거는 같은 명세의 "토큰 답의 꼴"(여섯 꼴)과 사용자 이야기 12·13이고, 새로 쓴 사실 문장은 없다.
2. "묻는 때가 겹칠 때와 401"에 줄을 더했다. 401 뒤에 새로 받은 토큰의 주체가 버린 토큰의 주체와 다르면 같은 요청을 그대로 다시 보내지 않고, 질문이면 앞 대화를 비운 새 대화의 첫 질문으로 보내며, 승인 결정이나 실행에 다시 붙는 요청이면 보내지 않고 대화를 비운다. 새 사실 문장은 "지금 위젯이 요청을 보내기 전에 받은 토큰의 주체가 바뀐 것을 안 때와 같게 한다"이고 근거는 코드 읽기다. `web/apps/widget/components/pages/drivers.ts`의 `run()`이 받은 토큰의 묶음이 바뀌면 `switched`를 내보내고 이어 갈 대화의 자리를 비운 뒤 그 질문을 시작으로 보내고, 승인 결정(`sendDecision`)과 다시 붙기(`subscribeRun`)는 바뀌었으면 `session.forget()` 뒤 보내지 않는다.
3. 같은 절의 "열린 응답 스트림은 토큰이 끝나도 끊지 않는다" 뒤에 끊는 때를 더했다. 주체가 바뀌었거나 `signed-out`을 받았거나 로그아웃된 것으로 판정해 대화를 비울 때 열린 응답 스트림과 답을 기다리던 요청을 먼저 끊고, 끊긴 뒤에 온 이벤트는 그리지 않는다. 새 사실 문장은 끊는 길이 지금 위젯이 새 대화와 주체가 바뀐 때에 쓰는 길이라는 문장이고 근거는 코드 읽기다(`useConversation.ts`의 `reset`이 `open.current?.abort()`로 열린 일을 끊고 대화를 비우며, 주체가 바뀐 때에 `drivers.ts`가 부르는 `Session.forget`이 그 `reset`이다. 같은 파일의 `begin`이 지은 길은 끊긴 뒤에 온 것을 화면에 넣지 않는다).
6. "위젯 설정을 받아 오기"에 문장을 더했다. 페이지 안 방식에서는 이 요청이 다른 출처 요청이고, 답을 읽게 여는 응답 머리는 widget-admin-server의 명세가 짓는다. 지적의 절반은 이미 맡긴 일이었다. ADR 0064 Consequences "명세가 짓는 것"과 그 기능 계획 13행("다른 출처의 페이지에서도 읽을 수 있게 연다")이 그 머리를 그 명세의 몫으로 적어 두었으므로 "바라는 것 넷"은 늘리지 않았다. `connect-src`는 `EMBED.md` "사이트의 CSP"가 최종 사용자 경로 때문에 이미 위젯 출처를 적는 자리다(162행을 읽었다). e2e가 재는 것에 "`site`를 적은 위젯이 CSP를 건 사이트의 페이지에서 위젯 설정을 받아 온다"를 더해 "더한 하나"가 "더한 둘"이 됐고, "고칠 문서"의 `EMBED.md` 항목에도 그 자리를 적었다.
7. 거절 알림의 수명을 바꿨다. 사람이 로그인 단추를 누르거나 질문을 보내거나 "새 대화"를 누른 때와 로그인한 사람의 토큰을 받은 때에 사라지고, 돌아온 신호와 위젯 안을 누른 것으로 한 물음의 답으로는 지우지 않는다. 사이트가 거절을 한 번만 답한다는 같은 명세의 문장("토큰 답의 꼴")이 근거다.
8. "돌아온 신호"에 간격 제한을 두지 않는다는 것과 까닭(로그인 창에서 곧바로 돌아온 사람의 물음을 늦추지 않는다), 대가(창을 오갈 때마다 서명이 한 번 는다), 1초마다 보는 일과 신호를 듣는 일을 그치는 때를 적었다.
9. "URL 방식"에 "묻는 메시지의 대상 출처"를 더했다. iframe 방식처럼 `"*"`로 보낸다. 새 사실 문장은 "지금 iframe 방식이 같은 까닭으로 그렇게 보낸다"이고 근거는 코드 읽기다(`web/apps/widget/lib/token.ts`의 머리 주석. 물음에는 `type`과 `id`와 까닭뿐이고 답은 허용 출처의 것만 받는다).
10. "임베드 속성 `site`"에 예외 하나를 더했다. 값이 `.`이나 `..`이면 요청을 보내지 않고 등록되지 않은 사이트의 답을 받은 것과 같게 다룬다. 근거는 손으로 본 것이다. `node -e "console.log(JSON.stringify([encodeURIComponent('..'), encodeURIComponent('.'), new URL('https://widget.example/settings/../x').pathname, new URL('https://widget.example/settings/.').pathname]))"`가 `["..",".","/x","/settings/"]`를 냈다(Node v24.19.0). 브라우저의 `URL`로는 재지 않았다. 받는 쪽 기능 계획(`.scratch/widget-admin-server/plan.md` 18행)의 "위젯은 이름의 꼴을 스스로 검사하지 않고" 문장에도 이 예외를 괄호로 적었다. `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다.
11. "읽지 못하는 토큰"에 `iss`나 `sub`를 읽지 못하는 토큰은 지금처럼 토큰을 받지 못한 것으로 친다고 적었다. 근거는 코드 읽기다(`drivers.ts`의 `authorize`가 `bundleOf(token)`이 `null`이면 `no-token`으로 돌려준다).
12. "로그인 페이지 열기"와 "로그아웃 페이지 열기" 링크를 연 창과의 연결을 끊어 연다고 적었다(`rel="noopener"`).
- 밀 주장의 Minor. "그림은 둘째 문장을 늘 그렸다"를 "카드와 덮는 상자의 그림은 둘째 문장을 늘 그렸다"로 고치고, 띠 모양은 그림대로 제목에 마침표를 붙이며 둘째 문장을 보이지 않는다고 적었다. 근거는 그림 파일을 읽은 것이다(`design/ch-expiry-3.dc.html` 50·52행과 `design/mk-08-expiry.dc.html` 197·199행의 띠에 제목 "로그인 시간이 끝났습니다."와 "이어 갑니다" 문장만 있고, `design/screens-prompt.md` 88행이 띠의 본문을 그 한 문장으로 줄인다고 적는다).

"높이마다 보는 것"의 위젯 전체(jsdom) 칸에 위 1, 2, 3, 7의 사례를 더했다.

프로브에서 고친 것이다.

4. `kit.mjs`에 `writeExpected`를 더하고 두 프로브의 `--update`가 그것을 부르게 했다. 표지가 하나라도 빠진 엔진의 결과는 `expected.json`에 쓰지 않는다. 확인은 `opener_message`로 했다. 그냥 돌린 회차는 "expected.json 과 모두 같다"로 끝났다. `--update`로 돌린 회차는 `expected.json 에 표지가 모두 선 엔진의 결과를 썼다: chromium`을 찍었고 `git status`에 `expected.json`이 나오지 않았다(쓴 내용이 커밋된 것과 같다). 양성 대조 표지의 조건 앞에 `false &&`를 넣은 변이를 `--update`로 돌린 회차는 `expected.json 에 쓴 것이 없다`와 `표지가 빠져 expected.json 에 쓰지 않은 엔진: chromium`을 찍고 1로 끝났으며, `stat -c "%Y %s"`가 돌리기 전과 같은 값(`1794812231 11420`)을 냈다. 고치기 전 판이라면 그 회차에도 파일을 썼다. 변이는 되돌렸다(손으로 봤다. 변이는 커밋하지 않았다).
5. `logout_fetch/probe.mjs`가 "요청이 끝점에 닿지 않았다"를 측정으로 세는 조건을 좁혔다. 덤 갈래의 `manual` 칸이고, 다른 출처로 가는 `mode: "no-cors"`이며, `fetch`가 `TypeError`로 거절됐고, 같은 자리의 `follow` 칸이 끝점에 닿았을 때만 센다. 머리 주석과 README "결과를 본 뒤 바꾼 판정 기준"에 적었다.

남긴 것은 하나다. 프로브 README에 Node의 최소 판(`import.meta.dirname`)을 적으라는 Minor는 반영하지 않았다. README "잰 판"이 돌린 판(Node v24.19.0)을, "다시 돌리기"가 `openssl`을 이미 적고, 최소 판은 재지 않아 적으면 어림이 된다.

서두의 수를 다시 셌다. "명세가 정했다" 괄호를 단 절 제목은 그대로 스물셋이고(`^### ` 줄을 Grep으로 뽑아 셌다) 한 절이 항목 둘이어서 스물넷이다. 넘겨받은 것 스물, 사용자가 고른 것 열여섯, 이력 넷, 프로브 둘, 포인터 여덟 자리는 이번 반영이 건드리지 않았다.

`logout_fetch`를 두 번 다시 돌려 5의 조건을 확인했다(각각 약 4분, 손으로 봤다. 변이는 커밋하지 않았다).

- 변이 판. 조건의 `variant.mode === "no-cors"`를 `variant.mode === "cors"`로 바꿔 `node .scratch/widget-login-state/probes/logout_fetch/probe.mjs --engine chromium`을 돌렸다. `측정 아님` 줄이 열여덟이었고 모두 다른 출처로 가는 `noCorsMode manual` 칸이었다(`POST /logout 이 0번 닿았다(fetch {"settled":"rejected","name":"TypeError"})`). "표지가 빠진 칸이 없다" 표지가 서지 않았고(`측정 아님 18칸`) 1로 끝났다. 고치기 전 판은 부르는 법을 보지 않아 그 열여덟을 측정으로 셌으므로, 이 열여덟 줄은 좁힌 조건이 조합이 맞지 않는 닿지 않은 칸을 측정에서 빼는 때에만 난다. 이 회차에서 `mode: "cors"`인 `manual` 칸은 모두 끝점에 닿아, 바꾼 조건으로 "닿지 않았다"고 센 칸은 없었다.
- 원래 판. 변이를 되돌리고 같은 명령을 돌렸다. `표지 있음` 여섯, `표지 없음`과 `측정 아님` 0, "expected.json 과 모두 같다", 종료 코드 0이었다. 출력에서 `끝점에 닿았다=아니오`인 줄은 열여덟이고 모두 `noCorsMode manual`이었다(`grep -c`로 셌다). `expected.json`의 `"sent": false`도 열여덟이다.

프로브 색인(`probes/README.md`)의 `kit.mjs` 설명에 `--update`가 기대값 파일을 쓰는 법을 더했다. `uv run ruff check .`와 `uv run ruff format --check .`는 손으로 쳤고 둘 다 통과했다(`All checks passed!`, `2370 files already formatted`).

### 반영 커밋

- 첫 `git commit`은 pre-commit의 pytest에서 막혔다. `tests/channel/cli/test_interrupt.py`의 `test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`가 `Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다`로 빨갰다(1 failed, 7731 passed). 이 브랜치는 그 시험과 CLI를 건드리지 않았다. 그 회차의 pytest는 1554초, web-verify는 1604초가 걸렸다(다른 워크트리의 세션들이 함께 돌고 있었다). 부하에서 흔들리는 시간 단언의 새 사례로 보고(대기열 306과 332, ADR 0036) 회차를 더하지 않고 여기에만 적으며, 커밋을 다시 친다. 나머지 검사(check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify, 마크다운 표, 줄 구분 문자, 변이 표)는 그 회차에 통과했다. 그 시험 파일만 홀로 돌린 `uv run pytest -q tests/channel/cli/test_interrupt.py`는 6 passed였고 385초가 걸렸다. 그때 CPU 사용률은 100%였고(`Get-CimInstance Win32_Processor`), 프로세스의 명령줄에서 다른 워크트리 셋(`review-pipeline-docs-name-bang-check`, `15-full-gate-ci`, `09-standalone-compose-runs-real-images`)의 `tools/run_checks.py`가 16:35, 16:37, 16:43에 시작해 돌고 있었다. 이 워크트리의 프로세스는 남아 있지 않았다. 넷이 함께 돌면 같은 단언에서 다시 막힐 수 있어, 그 러너들이 끝난 뒤에 커밋을 다시 친다.
- 그 커밋 명령 뒤에 인계 계기(`커밋 뒤`, 세션 컨텍스트 278,181 토큰)가 왔다. 이 세션의 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작하므로 `next-session/handoff.md`의 "인계하지 않는 때" 셋째에 들어 넘기지 않고 잇는다. 계기를 낸 커밋도 실패했으므로 첫째에도 든다.
- 인용 대조의 경고 넷 가운데 이 세션이 쓴 셋(명세 문장을 작은따옴표로 바꿔 옮긴 하나, 프로브 출력 둘)은 따옴표를 떼거나 코드 표기로 바꿨다. 남은 하나(`2368 files already formatted`)는 앞 세션이 옮긴 도구 출력이다.
