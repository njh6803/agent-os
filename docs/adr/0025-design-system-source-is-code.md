---
status: accepted
date: 2026-10-03
---

# 디자인 시스템은 코드가 원천이고 Claude Design은 탐색과 화면을 맡는다

위젯 설계 인터뷰 끝에 사용자가 화면 작업 전에 디자인 시스템과 화면 디자인을 먼저 만들자고 했다. 위젯과 관리 화면은 **디자인 시스템 하나를 나눈다.** 그 원천을 어디에 두는지가 물음이었다. **토큰과 핵심 컴포넌트는 코드에서 만들고 테스트한다. 그것이 원천이다. Claude Design에는 사용자가 시작하는 `/design-sync`로 올린다. Claude Design은 방향 탐색(색과 글꼴 짝, 대략의 화면)과, 올린 디자인 시스템으로 그리는 Wireframe과 UI mockups를 맡는다.** (바뀜: 이력 2026-10-16 "디자인 시스템과 화면은 Claude 아티팩트에 두고, Claude Code가 편집자로 저장소에서 올린다") **확정한 화면은 기능의 `.scratch/<slug>/design/`에 내보내 커밋하고, 화면마다 근거 문서의 전체 경로와 기준 커밋을 적는다.** 그다음 구현이 그 화면을 근거로 짓는다. 근거 문서는 화면을 그릴 때 있는 것이다. 명세 전에 그리는 화면은 ADR과 `plan.md`의 그 기능 행이고, 명세가 생긴 뒤에는 명세가 화면을 가리킨다.

연동의 방향이 이것을 정했다. `DesignSync` 도구는 로컬 컴포넌트 라이브러리를 Claude Design의 디자인 시스템 프로젝트에 컴포넌트 하나씩 맞추는 도구이고, `/design-sync` 안에서만 쓴다(도구 설명을 읽었다). 토큰의 제약도 코드에서만 보인다. Tailwind의 `@property` 등록이 shadow root 안에서 되지 않아 손대지 않은 CSS는 비교한 58곳 중 31곳이 다르게 그려졌다. 사이트의 `html { font-size }`가 바뀌면 rem 기반 위젯이 따라 줄었다(`.scratch/web-widget/probes/widget_tailwind/`). 단위 같은 토큰 결정은 이것을 잴 수 있는 자리에서 내린다. 명세와 화면의 연결을 저장소에 두는 이유는, 디자인 도구 안에 두면 저장소를 보는 세션이 그것을 보지 못하기 때문이다. 명세를 고치는 세션이 같은 자리에서 어느 화면을 고칠지 본다.

## Considered Options

- **Claude Design에서 디자인 시스템을 먼저 만들고 코드가 따라 옮긴다.** 디자인 작업이 가장 자유롭다. 그러나 원천이 둘이 되어 어긋나고, shadow root와 rem 같은 코드의 제약을 나중에 맞춰야 한다. 거부했다.
- **Claude Code가 Artifact(Design, Design System 형식)로 만든다.** 링크로 바로 읽힌다. 그러나 사람이 직접 보며 고치는 작업은 Claude Design이 낫다. 거부했다.
- **명세와 화면의 연결을 디자인 도구 안의 파일에 둔다.** 동기화를 요청하면 그 파일을 따라 화면을 고칠 수 있다. 그러나 저장소를 보는 세션이 그 기록을 보지 못한다. 거부했다.
- **위젯만의 디자인 시스템.** 최종 사용자용 모양에만 맞춘다. 그러나 관리 화면에도 아직 스타일이 없어서(ADR 0021 이력 2026-10-03) 같은 일을 두 번 한다. 거부했다.

## Consequences

- **design-system 기능이 `plan.md`에 는다.** web-widget과 admin-style이 그것을 기다리고, 파이썬 기능(conversation, end-user-channel)과는 나란히 간다.
- **Tailwind는 design-system이 토큰과 함께 처음 들인다.** 토큰은 Tailwind의 테마로 코드에 선다. 위젯과 관리 화면이 그것을 쓴다(ADR 0021 이력 2026-10-03, ADR 0024). shadow root와 rem의 측정은 위젯의 모양으로 했고, 그 결과를 토큰의 단위와 shadow root용 CSS에 반영하는 것이 이 기능의 일이다.
- **세부는 design-system 기능의 인터뷰가 정한다.** 두 앱이 토큰과 컴포넌트를 나누는 패키지의 모양(`packages/ui`를 둘지), rem과 px, 다크 모드, 접근성, 한글 글꼴과 남의 페이지에 싣는 법, Storybook을 둘지(Claude Design의 디자인 시스템이 미리보기를 대신할 수 있다), 디자인 문서의 이름과 자리와 실리는 방식(공유 하나와 앱별, `.claude/rules`의 `paths`)이다. (바뀜: ADR 0026)
- **`.scratch/<slug>/design/`은 새 자리다.** 그 규약을 `docs/agents/issue-tracker.md`에 더하는 일은 design-system 기능이 맡는다.
- **화면은 기능마다 그린다.** 위젯의 화면은 web-widget의 명세 직전에, 관리 화면의 화면은 admin-style에서 그린다.
- **코드가 바뀌면 `/design-sync`로 다시 맞춘다.** (바뀜: ADR 0026) (바뀜: 이력 2026-10-16 "디자인 시스템과 화면은 Claude 아티팩트에 두고, Claude Code가 편집자로 저장소에서 올린다") 자동으로 맞춰지지 않는다.

## 이력

### 2026-10-16 디자인 시스템과 화면은 Claude 아티팩트에 두고, Claude Code가 편집자로 저장소에서 올린다

admin-style의 화면을 그리려다 계정이 엇갈렸다. 저장소의 디자인 시스템 프로젝트(`.design-sync/config.json`의
`projectId`)와 재탐색 프로젝트는 njh4803 계정의 단독 Claude Design(claude.ai/design)에 있고, Claude Code는 njh6803
계정으로 로그인되어 있다(`claude auth status`로 봤다). 사용자가 두 계정이 같은 디자인을 나누고, 저장소에 판을 적어 같은
판인지 맞대 볼 수 있기를 바랐다. 공식 안내의 원문을 내려받아 대 봤다(`.scratch/design-artifacts/probes/`의
`find_sentences.mjs`, `pricing_rows.mjs`). 단독 Claude Design은 2026-12-14에 닫힌다. 프로젝트는 단독 쪽에 남아 닫힐
때까지 돌고(내려받기는 하나씩이다), 디자인 시스템은 "팀 디자인 시스템 마이그레이션"으로 Claude 아티팩트에 옮긴다.
개인 요금제는 프로젝트 공유와 협업이 없고(요금제 비교표의 "Project sharing and collaboration"이 Free·Pro·Max 모두 no),
njh4803의 설정에도 조직이나 멤버를 다루는 탭이 없었다(손으로 봤다). Team은 업무용 이메일로만 만든다. 아티팩트는 Pro·Max에서도 이메일로 특정 사람을 초대해 편집 권한을
줄 수 있다(베타). 개인 계정 사이에 데이터를 옮기는 것은 지원하지 않는다고 적혀 있고, 아티팩트 하나의 주인을 옮기는
방법은 공유 안내에서 찾지 못했다(손으로 읽었다). 위 결정이 거부한 "Claude Code가 Artifact(Design, Design System 형식)로
만든다"의 근거(사람이 직접 보며 고치는 작업은 Claude Design이 낫다)는 Claude Design이 아티팩트로 옮겨 가며 사라졌다.

**디자인 시스템과 화면은 Claude 아티팩트에 둔다. 주인은 njh4803 계정이고, Claude Code가 로그인한 njh6803 계정을 편집자로
초대한다. 원천은 그대로 코드다. 디자인 시스템은 지금의 `/design-sync` 빌드로 파일을 만들고, Claude Code가 편집자로서
Design System 아티팩트의 `project/` 아래 같은 경로에 바뀐 파일만 올리며 빌드에서 빠진 경로는 지운다. 올린 커밋은
아티팩트 색인의 `lastChange`에 적고, 같은 판인지는 파일의 sha256으로 맞댄다. 화면은 njh4803이 Design 아티팩트를 만들기만 하고 njh6803을 편집자로
초대하며, 그리기는 njh6803이 한다. 확정한 화면은 지금처럼 `.scratch/<slug>/design/`에 커밋한다.**

- 디자인 시스템 아티팩트는 https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH 다. njh4803의 단독 디자인 시스템을
  "팀 디자인 시스템 마이그레이션"으로 옮겼다. 빌드가 `ds-bundle/`로 그대로 옮기는 저장소 원본 다섯(`df705c17`의
  `.claude/rules/web-design.md`와 `.design-sync/foundations/`의 네 파일)이 아티팩트의 `project/guidelines/web-design.md`,
  `project/foundations/<이름>/index.html`과 바이트까지 같다(쟀다, `hash_match.mjs`). 그래서 빌드의 `ds-bundle/<경로>`가
  아티팩트에서는 `project/<같은 경로>`다. 빌드 산출 전체가 같은지는 커밋된 원본이 없어 맞대지 못했고, 다음 동기화가 본다.
- njh6803의 Claude Code는 초대를 수락한 뒤 그 아티팩트를 편집 권한으로 읽고, 색인에 `lastChange`를 더해 썼다(손으로
  봤다. 판 `1792115455-aa71`이고 다시 받은 파일의 sha256이 올린 것과 같다, `hash_match.mjs`). 수락하기 전에는 도구가
  "artifact not found"를 낸다.
- 올리기는 그 입력을 바꾼 PR이 main에 병합된 뒤 main에서 빌드해 하고, `lastChange`의 `via`에 빌드한 main의 커밋을
  적는다. 병합 전에 올리면 squash로 사라질 브랜치 커밋이 남고, 미리 지은 빌드를 올리면 그사이 병합된 변경이 빠진 채
  `via`만 앞선다. 파일 몇 개만 올리면 `via`를 부분이라 적어 다음 동기화가 전체를 맞대게 한다(모양은
  `docs/agents/issue-tracker.md` 화면 디자인 절).
- 옮긴 배치(색인의 `editing: "off"`와 `source`)를 지키고, 화면의 "Finish the migration" 정리는 하지 않는다. 정리는
  파일을 아티팩트 형식의 배치로 다시 짜서 빌드와 경로가 맞지 않게 되고, 화면 편집을 켜 원천을 둘로 만든다.
- 공식 안내대로라면 첫 쓰기로 단독 쪽과 갈라졌다. 다시 옮기기는 옮긴 뒤 Claude에서 바뀐 디자인 시스템을 그대로 두고
  건너뛴다(원문을 대 봤다. 실제로 건너뛰는지는 재지 않았다). 그래서 `/design-sync`의 업로드 도구(`DesignSync`)로 단독
  프로젝트에 올리는 일은 그만둔다. 빌드는 그대로 쓴다. 단독 쪽의 원본(디자인 시스템 프로젝트와 재탐색 프로젝트)은 따로
  지우지 않고 2026-12-14에 사이트와 함께 닫히게 둔다. 재탐색 프로젝트의 디자인 파일은 이미 `.scratch/design-system/design/`에
  있다.
- Claude Code의 디자인 시스템 목록에는 다른 계정이 공유한 이 디자인 시스템이 나오지 않는다(손으로 봤다). Claude Code가
  화면을 그릴 때는 그 주소를 이름으로 댄다.
- 재지 못한 것: njh4803이 Design 아티팩트를 비워서 만들 수 있는지, 그것에 이 디자인 시스템을 붙일 수 있는지, njh6803이
  편집자로 그리는 흐름(admin-style이 처음 그릴 때 잰다). 빌드 산출 전체가 지금 아티팩트와 같은지와 빌드에서 빠진 경로의
  지우기(다음 동기화가 잰다). 다시 옮기기가 실제로 건너뛰는지(재지 않고 둔다. 단독 쪽에 올리지 않으므로 다시 옮길 일이 없다).

거부한 안은 다섯이다.

- **2026-12-14까지는 `/design-sync`로 단독 프로젝트에 올리고 njh4803이 다시 옮긴다.** 지금 흐름을 지키지만, 바뀔
  때마다 브라우저 조작이 들고 닫힌 뒤에는 결국 직접 올려야 한다.
- **Claude Code가 화면 아티팩트를 직접 만든다.** 브라우저 조작이 없지만 주인이 njh6803이 되고, 주인을 옮기는 방법이 안내에 없다.
- **njh4803의 워크스페이스에 njh6803을 멤버로 둔다.** 개인 요금제에는 프로젝트 공유와 협업이 없고, Team은 업무용
  이메일로만 만들며 두 명 이상이다.
- **단독 Claude Design에서 njh4803 하나로 계속 그린다.** 계정을 나누지 않아 단순하지만 2026-12-14에 닫힌다.
- **정리를 하고 아티팩트 형식(`tokens.json`, `components/bundle.js`)으로 올리는 빌드를 새로 짓는다.** 아티팩트의 화면
  기능을 다 쓰지만 빌드를 새로 지어야 하고 화면 편집이 켜져 원천이 둘이 된다.

함께 고치는 것: `docs/agents/issue-tracker.md`의 화면 디자인 절, `.design-sync/NOTES.md`, `kickoff/prompting.md`,
`.scratch/admin-style/design/screens-prompt.md`의 하는 법과 고른 뒤, `.scratch/plan.md`(design-artifacts 행, admin-style·
web-widget 행), `.claude/rules/web-design.md`의 머리 문장, `README.md`의 `.design-sync/` 줄, 헌법 `tech.md`의 웹 행,
ADR 0026 본문의 포인터.
