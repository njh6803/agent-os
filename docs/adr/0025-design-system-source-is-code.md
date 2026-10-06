---
status: accepted
date: 2026-10-03
---

# 디자인 시스템은 코드가 원천이고 Claude Design은 탐색과 화면을 맡는다

위젯 설계 인터뷰 끝에 사용자가 화면 작업 전에 디자인 시스템과 화면 디자인을 먼저 만들자고 했다. 위젯과 관리 화면은 **디자인 시스템 하나를 나눈다.** 그 원천을 어디에 두는지가 물음이었다. **토큰과 핵심 컴포넌트는 코드에서 만들고 테스트한다. 그것이 원천이다. Claude Design에는 사용자가 시작하는 `/design-sync`로 올린다. Claude Design은 방향 탐색(색과 글꼴 짝, 대략의 화면)과, 올린 디자인 시스템으로 그리는 Wireframe과 UI mockups를 맡는다. 확정한 화면은 기능의 `.scratch/<slug>/design/`에 내보내 커밋하고, 화면마다 근거 문서의 전체 경로와 기준 커밋을 적는다.** 그다음 구현이 그 화면을 근거로 짓는다. 근거 문서는 화면을 그릴 때 있는 것이다. 명세 전에 그리는 화면은 ADR과 `plan.md`의 그 기능 행이고, 명세가 생긴 뒤에는 명세가 화면을 가리킨다.

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
- **코드가 바뀌면 `/design-sync`로 다시 맞춘다.** (바뀜: ADR 0026) 자동으로 맞춰지지 않는다.
