# frontend-design과 저장소 규칙이 부딪친 자리

`/ui-design`이 화면을 그리며 부른 `frontend-design` 스킬이 권한 것과 저장소 규칙(`.claude/rules/web-design.md`, 디자인 시스템의 토큰, `CONTEXT.md`의 용어)이 부딪치면, 그 화면은 저장소 규칙을 따르고 여기에 한 줄을 적는다(ADR 0033 이력 2026-10-20 "하네스가 스킬을 부르는 자리를 감사하고, 설명에만 기대던 계기를 하네스로 옮긴다"). 줄은 그 화면을 그린 세션이 `/ui-design` 4단계에서 적는다.

디자인 시스템을 다시 탐색하는 세션은 이 표를 먼저 읽고, 같은 축에서 되풀이해 부딪친 규칙을 그때 고칠지 사람에게 묻는다(`refresh-prompt.md` 머리). 디자인 규칙이 낡았다는 신호를 다시 볼 자리라서 일지가 아니라 이 폴더에 둔다.

| 날짜 | 기능과 화면 | frontend-design이 권한 것 | 따른 저장소 규칙(파일과 줄) |
|---|---|---|---|
| 2026-10-22 | admin-style 모든 화면 | 브리프에 맞춰 기본 팔레트를 이름 붙인 hex 4~6개로 새로 짓는다 | 색은 쓰임새 토큰만 쓰고 값은 디자인 토큰 CSS 한 자리에 있다(`.claude/rules/web-design.md` 9·23행) |
| 2026-10-22 | admin-style 모든 화면 | 늘 쓰는 기본 글꼴 대신 이 브리프에 맞춰 고른 서체를 쓴다 | 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다(ADR 0026 이력 2026-10-12 "테마는 넷이고 색만 바꾸며, 글꼴은 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다") |
| 2026-10-22 | admin-style 실행 목록, 실행 하나 | 작은 데이터 라벨에 고정폭을 쓰는 것은 생성물의 흔한 표지이니 고른 뒤에만 쓴다 | 실행 ID와 시각은 고정폭 칸이고 도구 이름과 인자는 글자 그대로 고정폭이다(`.claude/rules/web-design.md` 50행, `.scratch/admin-style/design/screens-prompt.md` 28행) |
| 2026-10-22 | admin-style 모든 화면 | 그리면서 화면을 찍어 보고 고친다 | 찍어 보거나 렌더해 확인하는 일은 사람이 청할 때만 한다(`.claude/skills/ui-design/SKILL.md` 23행, Design 형식 지침) |
| 2026-10-23 | web-widget 모든 화면 | 브리프에 맞춰 기본 팔레트를 이름 붙인 hex 4~6개로 새로 짓는다 | 색은 쓰임새 토큰만 쓰고 값은 디자인 토큰 CSS 한 자리에 있다(`.claude/rules/web-design.md` 9행과 23행) |
| 2026-10-23 | web-widget 모든 화면 | 늘 쓰는 기본 글꼴 대신 이 브리프에 맞춰 고른 서체를 쓴다 | 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다(ADR 0026 이력 2026-10-12 "테마는 넷이고 색만 바꾸며, 글꼴은 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다") |
| 2026-10-23 | web-widget 대화, 승인 묻기, 실패 | 작은 데이터 라벨에 고정폭을 쓰는 것은 생성물의 흔한 표지이니 고른 뒤에만 쓴다 | 도구 이름과 인자는 글자 그대로 고정폭이다(`.claude/rules/web-design.md` 50행). 실패 알림의 실행 식별자도 고정폭이다(`.scratch/web-widget/design/screens-prompt.md` "2. UI mockups") |
| 2026-10-23 | web-widget 모든 화면 | 그리면서 화면을 찍어 보고 고친다 | 찍어 보거나 렌더해 확인하는 일은 사람이 청할 때만 한다(`.claude/skills/ui-design/SKILL.md` 23행, Design 형식 지침) |
