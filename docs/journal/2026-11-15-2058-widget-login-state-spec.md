# 2026-11-15 (20:58) 위젯이 그리는 로그인 상태·고지·다크 모드 스위치의 명세 (widget-login-state)

세션 제목 `docs/widget-login-state-spec`. 브랜치 `docs/widget-login-state-spec`, 워크트리 `.claude/worktrees/widget-login-state-spec`. 모델 Fable 5.2. 일지 2026-11-15-1319의 "다음"이 낸 지시문으로 연 새 세션이다.

이 세션은 `open-session`이 보낸 꼴이 아니다. 첫 줄이 반각 `/to-spec`이라 사람이 손으로 새 세션을 열어 지시문을 붙여 넣은 것이다. 앞 세션의 일지 "다음"은 인계 열기가 그 세션에서 자동 모드 분류기에 거부됐다고 적고 "열기가 또 막히면 사람이 새 세션에 붙여 넣는다"고 했다. 병합 뒤의 열기가 또 막혔는지, 부르지 않았는지는 이 세션이 모른다(대기열 72).

## 사용자 프롬프트

지시문을 그대로 옮긴다. 일지 2026-11-15-1319의 "다음"에 실린 지시문과는 첫 줄 머리의 `/to-spec `과 모델 줄이 다르다(그쪽은 첫 줄이 `다음 작업:`으로 시작하고 모델이 `Fable 5.1 / xhigh`다).

```
/to-spec 다음 작업: 기능 widget-login-state. 위젯이 그리는 로그인 상태·고지·다크 모드 스위치·로그아웃 화면을 PR #579로 병합했고, 명세를 쓴다
다음 단계: 명세
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 widget-login-state-spec)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /to-spec
브랜치: docs/widget-login-state-spec
모델: Fable 5.2 / xhigh
읽을 것: 일지 docs/journal/2026-11-15-1319-widget-login-state-screens.md의 "다음"과 .scratch/widget-login-state/design/README.md의 "명세가 정할 것"
이어받을 상태: 없음
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 나란히 돌던 portal-admin 설계 인터뷰(docs/portal-admin-design)가 끝났는지는 확인하지 않았다. 아직 돌면 .scratch/portal-admin/의 파일을 고치지 않는다
이번 요청 범위: PR과 병합까지
```

## 시작

제목을 브랜치 이름으로 바꿨다(앱이 지은 제목 "widget-login-state 명세"라 묻지 않고 바뀌었다).

`tidy-checkouts`를 주 체크아웃에서 돌았다.

- 루트: dev가 깨끗했고 원격에 없는 커밋이 0이라 `0c25ea79c`에서 `be22f3ff5`(PR #579 병합)로 당겼다. 당긴 커밋은 그 스킬 파일을 바꾸지 않았다.
- 지운 로컬 브랜치: `worktree-admin-login-screens`(커밋이 모두 `origin/dev`에 있었다).
- 끝낸 프로세스: 병합된 워크트리 셋을 쥔 쉬는 세션 여섯의 `claude.exe`. `04-tools-compute-release-number-and-notes`의 `local_f20cc7a8`, `admin-login-design`의 `local_9cab0557`·`local_b4f4f6f9`·`local_b792131c`·`local_cef8ea13`, `widget-login-state-design`의 `local_f3b92808`이다. 치기 직전마다 `list_sessions`를 다시 읽어 여섯 모두 `isRunning`이 아니고 마지막 활동이 한 시간 넘게 지났음을 봤다.
- 지운 워크트리와 브랜치: 위 셋(`feature/04-tools-compute-release-number-and-notes`, `docs/admin-login-design`, `docs/widget-login-state-design`).
- 휴지통에 남은 것: `web/node_modules` 다섯(이번 셋과 이전 정리의 둘). `esbuild.exe`를 올린 `node.exe`(pid 23688)와 `esbuild.exe`(pid 32976, 23724)가 쥐어 `empty-trash`가 1로 끝났다. 그 프로세스가 끝난 뒤의 정리가 다시 비운다.
- 남긴 워크트리 스물넷: 바뀐 파일이 있다(여섯), 병합된 PR이 없다(여덟), 작업 디렉터리로 쥔 프로세스가 쉬는 세션의 것만이 아니다(넷), 다시 만들 수 없는 무시된 항목이 있다(셋), 앱의 표지가 있다(셋). 사람에게 넘긴 것(`넘긴다` 줄)은 없었다.

`EnterWorktree`(name `widget-login-state-spec`)로 들어와 머리가 `origin/dev`의 `be22f3ff5`임을 본 뒤 `git switch -c docs/widget-login-state-spec`으로 브랜치를 바꿨다.

## 나란히 도는 세션

`ListAgents`에서 `docs/portal-admin-design`이 `busy`였다. 지시문의 선행 조건대로 `.scratch/portal-admin/`의 파일은 고치지 않았다. `uv run python tools/sibling_overlap.py`는 "이 브랜치의 새 번호 없음", "번호 겹침 없음", "함께 고친 파일 없음"을 냈다. widget-login-state의 명세를 맡은 다른 세션은 `ListAgents`에 없었다.

그 브랜치를 읽기만 했다. `git log --oneline origin/dev..docs/portal-admin-design`이 커밋 둘(`503af04c3` "위젯 설정 관리의 설계를 ADR 0064로 남긴다", `e02fda6a9` "PR 직전 리뷰가 낸 빈 자리를 ADR 0064의 명세 목록에 더한다")을 냈고, `gh pr list --head docs/portal-admin-design --state all`이 `[]`를 내 PR은 아직 없었다. `git show`로 그 브랜치의 ADR 0064와 기능 계획 셋(widget-login-state, widget-admin-server, portal-admin)을 스크래치패드에 꺼내 읽었다. 아래는 그 브랜치의 글을 읽은 것이고, `origin/dev`에는 아직 없다.

- ADR 0064의 머리는 `status: accepted`, `date: 2026-11-15`다.
- 그 ADR의 결정 "0.1 판에서 등록하는 것"이 위젯 설정에 다섯을 더한다. 로그인 단추의 문구, URL 방식 창의 탭 제목, 문의 링크, 첫 화면의 예시 질문(누르면 그 질문이 보내지는 단추들), 밝기 스위치 숨기기다. 결정 "밝기 스위치 숨기기"는 ADR 0061의 "늘 사람이 고르기"를 "사이트가 숨기지 않는 한 사람이 고르기"로 바꾼다.
- Consequences "화면"이 이 기능의 화면 그리기에 셋을 더한다. 첫 화면의 예시 질문, 문의 링크, 밝기 스위치를 숨긴 위젯이다. `.scratch/widget-login-state/design/`에는 그 셋이 없다(`예시 질문|문의 링크|스위치를 숨`으로 찾아 나온 세 줄은 그림에 넣은 지어낸 질문을 가리키는 글이었다).
- 그 브랜치의 `.scratch/widget-login-state/plan.md`는 `**Blocked by:**`를 widget-admin-server로, `**설계:**`를 "ADR 0061, ADR 0064"로 바꾸고, ADR 0064가 이 행에 더한 일 넷을 적었다. 위젯 설정 항목 다섯을 그리는 일, 로그인 주소와 로그아웃 주소를 열거나 부르기 전에 형식을 한 번 더 보는 일, 위젯 미리보기 페이지 설정 파일에서 칸 여섯(`agent`, `heading`, `intro`, `theme`, `mode`, `notice`)을 빼는 일(`schema_version`은 명세가 정한다), 위젯 미리보기 페이지가 고지 전문에 문장을 더하지 않게 하는 일이다. 명세 전에 그리는 화면의 목록에도 위 셋이 들었다.
- 위젯이 위젯 설정을 받아 오는 경로의 이름, 답의 모양과 판 표시, 등록되지 않은 사이트의 답은 widget-admin-server의 명세가 정하고 이 기능이 따른다(ADR 0064 결정 "위젯 설정을 받아 가는 주소"). 그 행은 postgres-foundation을 기다린다.
- 그 브랜치는 ADR 0064를 더하면서 기존 ADR 아홉(0023, 0024, 0046, 0047, 0050, 0056, 0059, 0061, 0062)도 고친다(`git diff --stat=200 origin/dev...docs/portal-admin-design -- docs/adr`). 그 가운데 ADR 0061(바뀐 줄 12)과 ADR 0059(바뀐 줄 6)는 이 기능의 명세가 이력을 쌓기로 한 ADR이고, 그 브랜치가 두 파일에 더한 낱말은 `(바뀜: ADR 0064)` 포인터 열뿐이다(낱말 단위 diff에서 더하고 뺀 낱말만 뽑아 봤다).
- 앞 세션의 일지 "다음"이 넘긴 새 위젯 설정 값 둘(로그인 전 화면의 모양, 고지 전문을 보이는 모양)은 그 브랜치의 ADR 0064와 기능 계획 둘(portal-admin, widget-admin-server)에 없다(꺼낸 세 파일을 `알림의 모양|세 모양|모양을 고르|로그인 전`으로 찾아 0건). widget-admin-server의 계획은 표가 담는 항목을 "ADR 0061 결정 "0.1 판에서 등록하는 것"의 목록에 ADR 0064가 다섯을 더한 것"으로 적는다.

그래서 지시문대로 지금 명세를 쓰면 병합 전의 결정 위에 쓰게 되고, 그 결정이 병합되면 기능 계획이 명세 전에 그리라고 한 화면 셋이 비어 있게 된다. 멈추고 물었다.

## 사용자에게 물은 것

두 질문을 한 화면으로 올렸다. 훅(`hook_choice_facts`)이 첫 등장이라 한 번 막았고, 설명의 사실을 대 본 뒤 질문과 라벨이 같은 화면을 다시 올렸다. 다시 올리며 설명 둘을 고쳤다. 둘째 질문의 첫 선택지에는 "(코드를 읽었습니다)"를 더했고, 둘째 선택지의 "완성 화면 8과 다크 화면"은 "화면 넷(완성 화면 8, 다크 화면, 만료 갈래의 그림 둘)"으로 고쳤다. 그 본문이 `mk-08-expiry`, `mk-12-dark`, `ch-expiry-1`, `ch-expiry-2`에 있기 때문이다(`적어 둔 질문은 입력창에 남아 있습니다`로 `design/`을 찾았다). 대 본 사실은 위 "나란히 도는 세션"의 것과 아래 셋이다.

- ADR 0059 결정 "화면"은 만료를 알게 된 질문이 "다시 로그인하고 돌아온 화면에 없고, 질문한 사람이 다시 적는다"고 적고, Considered Options는 사용자가 "다시 적게 두기"를 골랐다고 적는다(그 ADR의 18행과 44행을 `다시 적`으로 찾아 읽었다).
- 지금 위젯은 보내기를 누르는 순간 입력창의 글을 비운다(`web/apps/widget/components/pages/ConnectedWidget.tsx`의 `onSend`가 `setDraft("")`를 부른다. 코드를 읽었다).
- 앞선 탐색의 본문은 "보내려던 질문은 남지 않으니 다시 적어 주세요."였다(일지 2026-11-15-1319 "시작 프롬프트").

> 질문: 오늘 승인하신 위젯 관리 설계(ADR 0064)가 아직 병합 전인데, 이 기능에 아직 그리지 않은 화면 셋(첫 화면의 예시 질문, 문의 링크, 밝기 스위치를 숨긴 위젯)을 더했습니다. 위젯 로그인 상태 기능의 명세를 어떻게 진행할까요?
>
> 사용자: "화면 셋을 먼저 그리기 (추천)" — 설명: 이 세션은 명세를 쓰지 않고 여기서 끝냅니다. ADR 0064가 dev에 병합된 뒤 새 세션이 화면 셋을 더 그려 확정받고, 그다음 세션이 명세를 한 번에 씁니다. 기능 계획이 정한 '명세 전에 화면을 그린다'는 순서 그대로입니다. 대가는 명세가 그 두 단계만큼 늦어진다는 것입니다.

고르지 않은 선택지는 둘이다. "그림 없이 명세의 글로 정하기"(이 세션이 ADR 0064의 병합을 기다렸다가 이어서 명세를 쓰고, 예시 질문과 문의 링크의 자리를 그림 없이 글로 정한다)와 "지금 앞선 결정만으로 쓰기"(ADR 0061까지의 결정만으로 지금 쓰고, ADR 0064가 더한 것은 병합 뒤에 명세를 고치는 PR로 낸다)다.

> 질문: 로그인 시간이 끝나 질문을 보내지 못했을 때, 보내려던 질문을 입력창에 남길까요? 예전 결정(ADR 0059)에서는 '다시 적게 두기'를 고르셨는데, 그때는 로그인하러 같은 탭이 이동해 위젯이 다시 뜨던 때였고, 지금은 로그인이 새 창이라 위젯이 그대로 남습니다.
>
> 사용자: "입력창에 남기기 (추천)" — 설명: 알림 본문이 '적어 둔 질문은 입력창에 남아 있습니다.'가 됩니다(확정하신 완성 화면 8의 글 그대로입니다). 보내려다 막힌 질문이 입력창에 그대로 남아, 다시 로그인한 뒤 보내기만 누르면 됩니다. 지금 위젯은 보내기를 누르는 순간 입력창을 비우므로(코드를 읽었습니다), 막힌 질문을 되돌려 놓는 동작을 새로 짓습니다. 예전 결정 '질문한 사람이 다시 적는다'가 바뀌므로 ADR에 바뀐 기록을 남기고, 초안을 보여 드린 뒤 승인받습니다.

고르지 않은 선택지는 "예전대로 다시 적게 두기"다(본문이 앞선 탐색의 글이 되고 막힌 질문을 되돌려 놓지 않으며 ADR 0059를 고치지 않는다).

둘째 답은 `.scratch/widget-login-state/design/README.md`의 "명세가 정할 것"에 옮겼다. 그 항목은 명세 전에 사람에게 묻는다고 적혀 있었다. ADR 0059의 그 문장을 바꾸는 이력은 이 세션이 쓰지 않았다. 명세를 쓰는 세션이 초안을 보이고 승인받는다. ADR 0059는 병합 전인 portal-admin 설계 브랜치도 고치고 있어, 지금 이 브랜치에서 이력을 쌓으면 같은 파일을 두 브랜치가 고치게 된다.

물은 뒤에 고친 사실이 하나 있다(셀프 리뷰의 표준 축이 짚었다). 둘째 질문의 첫 선택지 설명은 "막힌 질문을 되돌려 놓는 동작을 새로 짓습니다"라고 했는데, 되돌려 놓는 길은 이미 있다. 요청이 422나 429로 거절되면 위젯이 그 요청을 입력창에 다시 넣는다. `web/apps/widget/lib/rejection.ts`의 `runStep`이 그 두 상태에만 `return`을 내고, `drivers.ts`의 `run`이 그 갈래에서만 `refuse`를 부르며, `useConversation.ts`의 `send`가 거기서 `onReturn(request)`를 부르고, `ConnectedWidget.tsx`가 그 자리에 `setDraft`를 넘긴다(코드를 읽었다). 토큰을 받지 못한 때(`no-token`)와 401에는 그 길이 닿지 않는다. 그래서 새로 지을 것은 되돌려 놓는 장치 전체가 아니라 로그인 만료로 막힌 질문에도 그 길이 닿게 하는 것이다. 위 "대 본 사실"의 둘째 항목(보내는 순간 비운다)은 맞지만 반쪽이었다. 짓는 일이 설명보다 작아지는 쪽이라 고른 답은 그대로 둔다고 보았고(이 세션의 판단이다), 끝 보고에서 사람에게 알린다. 위 인용은 사람이 본 글 그대로 두고, README의 그 항목은 고쳐 적었다.

## 조사

명세를 쓸 생각으로 띄운 탐색 서브에이전트 둘(위젯 앱, 위젯 미리보기 페이지와 최종 사용자 경로)이 보고를 냈다. 명세를 쓰지 않게 되어 쓰지 않았고, 명세 세션이 다시 탐색할 때의 출발점으로 요지만 남긴다. 아래는 서브에이전트의 보고이고, 이 세션은 `ConnectedWidget.tsx`의 `onSend` 말고는 원문과 대 보지 않았다.

- 위젯의 임베드 방식은 지금 둘(페이지 안 방식, iframe 방식)이고 임베드 속성은 다섯이다. 토큰 통로는 페이지 안 방식이 요소의 속성 `tokenProvider`, iframe 방식이 부모 창과 주고받는 메시지이고, 위젯은 요청마다 토큰을 묻는다(`web/apps/widget/EMBED.md`, `web/apps/widget/lib/token.ts`, `web/apps/widget/components/pages/drivers.ts`).
- 위젯의 위쪽 띠(`web/apps/widget/components/organisms/TopBar.tsx`)에는 이름과 "새 대화"뿐이다. 브라우저 저장소는 탭 저장소 하나만 쓴다(`web/apps/widget/lib/storage.ts`). 밝기는 뿌리의 `data-mode`로 정하고 없으면 디자인 토큰 CSS의 `prefers-color-scheme` 규칙이 정한다.
- 위젯의 시험은 네 높이다. 위젯 전체를 jsdom에 띄우고 HTTP와 부모 창만 가짜로 두는 vitest(`web/apps/widget/testing/`의 `widget.tsx`, `network.ts`, `site.ts`), 스토리 테스트, 실제 `serve`와 위젯 빌드와 다른 출처의 시험용 사이트 서버를 띄우는 Playwright e2e(`web/apps/widget/e2e/`의 `stack.ts`, `site.ts`, `element-site.ts`), 사진 비교(`web/apps/widget/visual/`)다. 실제 모델 e2e는 `tests/test_widget_llm.py`다.
- 디자인 시스템 패키지에 `Button`, `IconButton`, `Icon`, `Switch`가 있고, 메뉴와 덮개 계열 부품은 없다.
- 위젯 미리보기 페이지(`web/apps/portal`)는 `node:http` 서버이고 위젯을 페이지 안 방식으로 넣는다. 지금 그 페이지가 그리는 띠의 스위치, 고지 확인 덮개, 짧은 고지 줄, 로그인 단추 줄은 `web/apps/portal/server/page.ts`와 `web/apps/portal/browser/portal.ts`에 있다. 고지 확인은 쿠키로만 기록하고, 토큰 끝점은 JWT 글자 하나를 평문으로 답하며 수명은 120초다(`web/apps/portal/server/handler.ts`, `web/apps/portal/server/token.ts`).
- 위젯 미리보기 페이지의 e2e는 `web/apps/portal/e2e/`의 셋(`portal.e2e.ts`, `acknowledge.e2e.ts`, `sites.e2e.ts`)이고, 띄우는 것은 `web/packages/e2e-stack`이 맡는다.
- 루트 `openapi.json`에 위젯 설정 경로는 없고, `src/`와 `web/`에 `window.open`을 쓰는 코드는 없다.

## 인계

셀프 리뷰(`/code-review origin/dev`)를 부르자 인계 계기(`hook_handoff`)가 왔다. 세션 컨텍스트 359,151 토큰이 문턱 200,000을 넘은 채 단계 경계 `셀프 리뷰 직전`에 왔다. `next-session/handoff.md` 1의 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 명령이 실패하지 않았고, 요청 범위(PR과 병합까지)가 이 경계에서 끝나지 않으며, 지시문의 "이어받을 상태"는 "없음"이고, 이 일지에 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 셀프 리뷰의 단계를 밟지 않고 넘긴다. 계기를 받은 직후 자동 압축이 왔고, 같은 문서의 5대로 끝나지 않은 단계(일지)부터 이었다. 바꾸기 전 제목은 `docs/widget-login-state-spec`이다. 넘길 때 커밋하지 않은 변경은 둘이다. 이 일지(미추적)와 `.scratch/widget-login-state/design/README.md`의 "명세가 정할 것" 가운데 만료 알림 본문 항목의 끝부분이다(한 문장의 "묻는다"를 "묻기로 했다"로 고치고 그 뒤에 문장을 더했다. 아래 지시문은 이것을 "끝 문장"이라 적었다). 이 브랜치에 커밋과 PR은 없다(`gh pr list --head docs/widget-login-state-spec --state all`이 `[]`를 냈다).

이 브랜치는 명세를 싣지 않는다. 사용자가 "화면 셋을 먼저 그리기"를 골랐기 때문이다(위 "사용자에게 물은 것"). 새 세션은 `/to-spec`의 단계를 밟지 않고, 위 두 변경의 셀프 리뷰부터 병합까지와 다음 작업 지시문을 맡는다.

새 세션이 "다음"과 다음 작업 지시문과 끝 보고에 넘길 것이다.

- 다음 단계는 명세가 아니라 화면 그리기다. ADR 0064(브랜치 `docs/portal-admin-design`)가 dev에 병합된 뒤 `/ui-design widget-login-state`로 화면 셋(첫 화면의 예시 질문, 문의 링크, 밝기 스위치를 숨긴 위젯)을 더 그려 확정받고, 그다음 세션이 명세를 쓴다. 인계 때 그 브랜치의 PR은 없었고(`gh pr list --head docs/portal-admin-design --state all`이 `[]`를 냈다) 그 세션은 `ListAgents`에서 `idle`이었다.
- 앞 세션이 portal-admin 행에 넘긴 새 위젯 설정 값 둘(로그인 전 화면의 모양, 고지 전문을 보이는 모양. `design/README.md` "명세가 정할 것"의 첫 항목)이 ADR 0064의 목록과 받는 쪽 계획 둘(widget-admin-server, portal-admin)에 없다(위 "나란히 도는 세션"의 끝 항목). ADR 0064가 병합된 뒤 그 목록에 둘을 더하는 이력(사용자 승인)과 두 계획의 반영이 남는다. 이 세션은 portal-admin 세션이 돌고 있어 그 파일을 고치지 않았다.
- ADR 0059 결정 "화면"의 "질문한 사람이 다시 적는다"를 바꾸는 이력과, ADR 0061의 이력(만료 알림의 기본 모양이 대화 안의 카드로 바뀐 것. 같은 README의 둘째 항목)은 명세 세션이 초안을 보이고 승인받는다.
- 위젯이 위젯 설정을 받아 오는 경로와 답의 모양은 widget-admin-server의 명세가 정하고, 그 행은 postgres-foundation을 기다린다(위 "나란히 도는 세션"). 이 기능의 명세가 그보다 먼저 돌면 그 자리를 "따른다"로만 적게 된다. 순서는 다음 지시문을 내는 세션이 본다.
- 끝 보고에 사람에게 알릴 것은 `tidy-checkouts`가 쉬는 세션 여섯의 프로세스를 끝냈고 휴지통에 `web/node_modules` 다섯이 남았다는 것이다(위 "시작").

회고가 볼 것이다(판정은 `retro`가 한다).

- 앞 세션의 지시문은 다음 단계를 "명세"로 냈는데, 나란히 돌던 설계 세션이 병합 전의 ADR로 이 기능의 범위와 명세 전에 그릴 화면을 바꿨다. 지시문의 "확인할 선행 조건"은 그 세션이 끝났는지 확인하지 않았다고만 적었고, 이 세션이 그 브랜치를 읽고서야 알았다.
- `next-session/directive.md` 2의 잇는 지시문은 명세의 값을 `Fable 5.1 / xhigh`로 적는데, 사람이 이 세션을 열 때 그 줄을 `Fable 5.2 / xhigh`로 고쳐 붙여 넣었다(위 "사용자 프롬프트").
- 계기가 온 때 남은 일은 문서 둘의 셀프 리뷰와 병합이었다.

지시문:

```
다음 작업: 기능 widget-login-state. 명세를 화면 셋을 더 그린 뒤로 미루기로 한 사용자의 답과 만료 알림 본문의 답을 일지와 design/README.md에 남겼고, 셀프 리뷰와 커밋과 PR과 병합이 남았다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/widget-login-state-spec
모델: Fable 5.2 / xhigh. 2의 잇는 지시문의 값은 Fable 5.1 / xhigh이고, 사용자가 이 세션을 열 때 그 줄을 Fable 5.2로 고쳐 붙여 넣어 그 값을 잇는다
읽을 것: 일지 docs/journal/2026-11-15-2058-widget-login-state-spec.md 전체(특히 "사용자에게 물은 것"과 "인계")
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지 docs/journal/2026-11-15-2058-widget-login-state-spec.md. 이 브랜치는 명세를 싣지 않는다. 사용자가 "화면 셋을 먼저 그리기"를 골라 명세를 미뤘으므로 /to-spec의 단계는 밟지 않는다. 커밋하지 않은 변경은 이 일지(미추적)와 .scratch/widget-login-state/design/README.md의 만료 알림 본문 항목 끝 문장 둘뿐이다. 셀프 리뷰의 고정점은 origin/dev이고, 티켓이 없어 명세 축은 이 세션을 연 지시문(일지 "사용자 프롬프트")과 일지 "사용자에게 물은 것"의 답 둘(설명까지 글자 그대로)을 요구로 쓴다. 그 뒤 커밋(직전에 git branch --show-current와 tools/sibling_overlap.py), PR, 병합, retro, next-session이다. 다음 지시문과 끝 보고에 넘길 것은 일지 "인계"의 목록에 있다
확인할 선행 조건: 나란히 도는 portal-admin 설계 세션(docs/portal-admin-design)이 끝났는지와 ADR 0064가 dev에 병합됐는지는 새 세션이 다시 본다. 아직 돌면 .scratch/portal-admin/의 파일을 고치지 않는다. 주 체크아웃이 루트 브랜치(dev)의 최신인지는 인계 때 확인하지 않았다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `docs/widget-login-state-spec (인계함)`으로 바꿨고(앱이 묻지 않고 바꿨다), 띄워 둔 백그라운드 작업은 없었으며, `git worktree unlock C:/project/agent/.claude/worktrees/widget-login-state-spec`이 오류 없이 끝났다.

open-session을 부른다 2026-11-15T12:16:53Z

인계 못함 셀프 리뷰 직전. `open_session.ps1 -Action send` 호출을 자동 모드 분류기가 거부했다(까닭은 내지 않았다). 앞 세션의 일지가 적은 거부와 같은 자리다. 돌아가는 길을 찾지 않았고, 제목을 `docs/widget-login-state-spec`으로 되돌린 뒤 이 세션에서 셀프 리뷰부터 잇는다. 워크트리 잠금은 `handoff.md` 4대로 다시 걸지 않았다. 위 지시문은 보내지 않았다.

## 셀프 리뷰

인계하지 못해 이 세션이 `/code-review origin/dev`를 이었다. 본 범위는 base `be22f3ff5`, 추적 파일 하나(`.scratch/widget-login-state/design/README.md`), 커밋 0, 미추적 하나(이 일지)다. 티켓이 없어 명세 축에는 이 세션을 연 지시문, 첫 턴 훅이 시킨 것, 사용자의 답 둘(설명까지 글자 그대로)을 요구로 주고, 이 브랜치가 명세를 싣지 않는다는 것과 ADR 이력을 쓰지 않았다는 것은 리뷰어 참고로 갈라 주었다. 표준 축은 sonnet·high로, 명세 축은 이 세션의 모델로 돌았다. 리뷰를 띄우기 전에 "시작"의 남긴 워크트리 갈래별 수를 판정 출력(스크래치패드에 받아 둔 둘째 `judge`의 출력)과 대 보고 "병합된 PR이 없다"를 아홉에서 여덟으로 고쳤다(합 스물넷은 맞았다).

### 표준 축

하드 위반은 없었고 Minor 둘, Nit 둘, 판단 하나가 나왔다.

- Minor 1. README와 이 일지가 위젯이 보내는 순간 입력창을 비우므로 되돌려 놓는 동작을 새로 짓는다고 적은 것이 과장이다. 422와 429의 거절은 이미 요청을 입력창에 되돌린다. 고쳤다. 코드를 읽어 맞음을 확인한 뒤 README의 그 항목을 고쳐 적고, "사용자에게 물은 것" 끝에 고친 사실을 적었다. 사람에게 보인 설명에 같은 말이 있어 끝 보고에서 알린다.
- Minor 2. 그 브랜치가 ADR 0061과 ADR 0059의 본문에 포인터를 단다고 적은 문장이 고친 ADR이 둘뿐인 것처럼 닫혔다. 그 브랜치는 기존 ADR 아홉을 고친다. 고쳤다. `git diff --stat=200`의 출력으로 아홉을 적고, 두 파일에 더한 낱말이 포인터 열뿐인 것을 낱말 단위 diff로 봤다.
- Nit 3. "모델 줄만 다르다"는 첫 줄 머리의 `/to-spec `도 다르다. 고쳤다.
- Nit 4. README의 변경을 "끝 문장"이라 불렀으나 한 문장을 고치고 문장을 더한 것이다. "인계"의 글을 고쳤다. 그 절의 지시문 블록은 보내려던 글의 기록이라 그대로 두고 그 사실을 옆에 적었다.
- 판단 5. "인계" 절의 지시문이 `다음 단계: 명세`와 `/to-spec`을 실어 지금도 유효한 지시로 읽힐 수 있다. 남겼다. 그 두 값은 `handoff.md` 인계 줄이 정한 것이고, 바로 아래 `인계 못함` 줄이 보내지 않았다고 적는다.

리뷰가 원문과 대 보아 맞다고 한 주장은 붙여 넣은 지시문의 사본, 그 브랜치의 ADR 0064에서 옮긴 사실(머리, 더한 다섯, 화면 셋, 받아 가는 경로의 결정), 그 브랜치의 기능 계획에서 옮긴 사실(`**Blocked by:**`, `**설계:**`, 더한 일 넷, 칸 여섯), 새 값 둘의 부재, ADR 0059의 두 인용, 본문이 든 화면 파일 넷, `handoff.md`와 `directive.md`의 인용이다. 대 보지 못했다고 한 것은 `tidy-checkouts`의 수치, `sibling_overlap.py`의 출력, 토큰 수, 열기 시각, "조사" 절이다.

### 명세 축

표준 축의 반영이 실린 뒤의 파일을 보았다. 빠지거나 덜 된 요구, 요구 밖의 동작, Critical·Major·Minor는 없었고 Nit 셋과 판단 하나가 나왔다.

- Nit 1. 위 표준 축 Minor 1의 줄이 옛 README 문장을 따옴표로 옮기며 가운데 괄호를 말없이 뺐다. 고쳤다. 따옴표를 떼고 풀어 적었다. Minor 2의 줄도 지금은 없는 옛 문장의 인용이라 같이 풀어 적었다.
- Nit 2. "나란히 도는 세션"이 그 브랜치의 기능 계획을 따옴표로 옮긴 말이 계획의 글자가 아니다. 고쳤다. 따옴표를 뗐다.
- Nit 3. 같은 절이 기존 ADR 아홉의 "본문"을 고친다고 적었는데, ADR 0046은 이력을 쌓은 것이라 본문이 아니다. 고쳤다. "본문"을 뺐다.
- 판단. README가 사용자가 고른 설명의 "새로 짓습니다"를 만료에도 닿게 하는 것으로 좁힌 것은 사실에 맞고(리뷰가 `runStep`을 node로 불러 `return`이 422와 429뿐이고 401은 `settle`임을 봤다. `refuse`에서 `setDraft`까지의 배선은 이 워크트리에 `web/node_modules`가 없어 실행하지 못하고 코드와 기존 시험의 단언으로 봤다), 답을 그대로 둔 판단에 동의하되 끝 보고에서 사람에게 알려야 닫힌다고 했다. 끝 보고에 넣는다.

리뷰가 대 보아 맞다고 한 것은 두 질문과 두 답(요구로 준 글과 글자 그대로), 지시문 사본, ADR 0064와 그 브랜치의 기능 계획에서 옮긴 사실, 새 값 둘의 부재, ADR 0059의 18행과 44행, 화면 파일 넷, 고친 ADR 아홉(numstat), 포인터 열, `handoff.md`와 `directive.md`의 인용, `sibling_overlap.py`를 다시 돌린 출력, 인계 목록의 순서다. 대 보지 못했다고 한 것은 `tidy-checkouts`의 갈래별 수(합만 봤다), `ListAgents`의 상태, 훅이 막은 일, 토큰 수, 열기 시각과 분류기 거부, 고르지 않은 선택지 셋의 원문, 답을 받은 턴에 옮겼는지, "조사" 절(여섯 항목만 표본으로 보았고 모두 맞았다)이다.

### 반영

- 고친 것: 표준 축의 Minor 둘과 Nit 둘, 명세 축의 Nit 셋. 리뷰 전에 고친 갈래별 수 하나(아홉을 여덟으로).
- 남긴 것: 표준 축의 판단 5("인계" 절의 지시문이 유효한 지시로 읽힐 수 있다). `handoff.md`가 정한 값이고 `인계 못함` 줄이 바로 아래에 있다. 인용 검사(`tools/check_quotes.py`)가 낸 경고 가운데 여섯도 남겼다. 셋은 이 체크아웃에 없는 그 브랜치의 글(ADR 0064에서 둘, widget-admin-server의 계획에서 하나)을 옮긴 인용이라 도구가 원문을 찾지 못하는 것이고 두 축이 `git show`로 대 보았다. 나머지 셋은 파일에 없는 글이다(그 브랜치의 커밋 제목 둘은 `git log`의 것이고, 하나는 선택 화면의 설명 한 토막이다).
- 다시 돌린 명령: 문서 둘뿐인 변경이고 다음이 커밋이라 손으로 치는 다섯은 그 커밋의 pre-commit으로 갈음한다. ruff 둘은 `.py`가 없어 pre-commit에서 Skipped일 것이라 손으로 친다. 결과는 아래 "커밋과 PR"에 적는다.

고치며 새로 쓴 사실 문장은 넷이고 PR 직전 리뷰에 밀 주장으로 넘긴다.

1. README: 지금 위젯은 보내기를 누르는 순간 입력창을 비우고, 요청이 422나 429로 거절됐을 때만 그 요청을 입력창에 다시 넣는다. 로그인 만료로 막힌 질문에는 그 길이 닿지 않는다.
2. 일지 "사용자에게 물은 것" 끝 문단: `runStep`이 422와 429에만 `return`을 내고, `run`이 그 갈래에서만 `refuse`를 부르며, `send`가 거기서 `onReturn(request)`를 부르고, `ConnectedWidget.tsx`가 그 자리에 `setDraft`를 넘긴다. 토큰을 받지 못한 때와 401에는 그 길이 닿지 않는다.
3. 일지 "나란히 도는 세션": 그 브랜치는 ADR 0064를 더하면서 기존 ADR 아홉(0023, 0024, 0046, 0047, 0050, 0056, 0059, 0061, 0062)도 고치고, ADR 0061과 ADR 0059에 더한 낱말은 `(바뀜: ADR 0064)` 포인터 열뿐이다.
4. 일지 "사용자 프롬프트": 붙여 넣은 지시문은 앞 일지의 지시문과 첫 줄 머리의 `/to-spec `과 모델 줄이 다르다.
