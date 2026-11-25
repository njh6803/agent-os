# 2026-11-26 (01:44) admin-login 티켓 08: 디자인 시스템의 아이콘 일곱과 계정 상태 배지

브랜치 `feature/08-design-system-icons-and-account-badge`, 워크트리 `.claude/worktrees/08-design-system-icons-and-account-badge`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev` `11343375b`(admin-login 01, PR 645의 병합)다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/admin-login/issues/08-design-system-icons-and-account-badge.md
> 다음 작업: .scratch/admin-login/issues/08-design-system-icons-and-account-badge.md. 디자인 시스템의 아이콘 일곱과 계정 상태 배지를 더하는 티켓(09와 12가 쓴다)
> 다음 단계: 구현
> 이번 요청 범위: PR과 병합까지

## 한 일

- 디자인 시스템 아티팩트의 웹 편집을 먼저 확인했다(`sync-design-system 확인`, 작업 폴더에 아티팩트의 색인·기록·토큰과 마크다운 열다섯을 받아 `check judge`와 `decide`를 돌렸다). 보고는 `result: clean`, 결정은 `act: continue`였다(탐침이 낸 값이다). 웹에서 고친 것이 없어 그대로 화면 작업을 했다.
- 아이콘 이름 목록(`Icon.tsx`의 `GLYPHS`)에 일곱을 더해 열일곱에서 스물넷이 됐다. 일곱 모두 설치한 lucide-react에 `dist/esm/icons/<이름>.mjs`로 있는 것을 `ls`로 봤다.
- 새 컴포넌트 `AccountStatusBadge`(값 넷: 활성, 비활성, 비밀번호 미설정, 잠김)를 더하고 `index.ts`에서 내보냈다. 모양과 치수는 `StatusBadge`와 같은 클래스 문자열이다. 색은 기존 토큰만 쓴다: 활성 `text-text`, 비활성·비밀번호 미설정 `text-text-muted`, 잠김 `text-warning`. 앞의 셋은 `circle`, 잠김은 `lock` 아이콘이다. 활성의 기본 글자색, 미설정의 흐린 색, 잠김의 warning은 그린 화면 `mk-accounts.dc.html`을 읽고 맞췄다(코드를 읽은 것). 비활성의 색은 그린 화면에 없어 구현자가 골랐다.
- 스토리 `AccountStatusBadge.stories.tsx`(상태별 넷, 색만으로 가르지 않음, 누르는 곳 아님, 다크, 보여 주기용 `쓰임: 운영자 계정 목록의 상태`), 쓰는 법 `AccountStatusBadge.md`, 아이콘 스토리의 스물넷 단언과 보여 주기용 `쓰임: 계정 메뉴와 탐색의 아이콘`, `Icon.md`의 목록을 더하거나 고쳤다.
- 올리기(`sync-design-system 올리기`)는 하지 않았다. `upload.md` 1이 올리기를 그 입력을 바꾼 PR이 기준 브랜치에 병합된 뒤 `origin/dev`에서 하라고 정한다. 티켓의 올리기 칸은 비워 두었다.

## 검증

- 스토리를 구현보다 먼저 썼다. 그 뒤 컴포넌트를 쓰고 `vitest run --project storybook packages/ui/src/components/atoms`로 7개 파일 63개가 통과했다. 빨강을 본 적이 없어 `AccountStatusBadge.tsx`에 변이를 넣었다(손으로 편집해 `vitest`를 돌렸다. `tools/mutate.py`를 쓰지 않았다): 잠김의 아이콘을 `lock`에서 `circle`로, 색을 `text-warning`에서 `text-text`로 바꾸자 잠김 스토리와 다크 스토리 둘이 빨개졌다(8개 가운데 2개 실패). 되돌린 뒤 8개가 통과했다.
- `pnpm -C web verify` 통과(136개 파일 2873개 통과 1 건너뜀, 종료 코드 0. 993.7초).
- 사진 비교 셋을 Docker로 쳤다. `pnpm -C web visual:update`는 두 이야기(`molecules-switch--on`, `molecules-textfield--disabled`)가 30초 시간 초과로 실패해 종료 코드 1이었다(이 변경이 건드리지 않은 이야기이고 그 사진 파일은 바뀌지 않았다. 부하로 본 것은 어림이다). 이어 `pnpm -C web visual`(검증 모드)이 143개 통과, `visual:widget` 44개 통과, `visual:admin` 98개 통과였다(모두 종료 코드 0). 새 정답은 `atoms-accountstatusbadge--*` 28장과 `atoms-icon--showcase-account-menu-*` 4장, 바뀐 정답은 `atoms-icon--all-names-*` 6장이다. 사람이 `atoms-accountstatusbadge--not-only-color-light-regular.png`와 `atoms-icon--all-names-light-regular.png` 두 장을 열어 봤다: 배지 넷이 한 줄에 서고(활성·비활성·비밀번호 미설정은 윤곽선 점, 잠김은 자물쇠와 갈색 글자), 아이콘 목록 끝에 `message-square`, `users`, `chevrons-up-down`, `log-out`, `copy`, `lock`, `circle`이 그려졌다.
- `uv run ruff check .`와 `uv run ruff format --check .` 통과. 나머지 손으로 치는 다섯(`pytest`, `pyright`, `lint-imports`, 지침·타입 우회 등)은 커밋의 pre-commit이 갈음한다.
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음, 함께 고친 파일 없음.
- 잔존 grep(옛 "열일곱"): 살아 있는 문서와 코드에는 이력을 말하는 문장 둘(`Icon.tsx`의 "열여섯", `Icon.stories.tsx`의 "열일곱") 말고 남지 않았다. 나머지 일치는 일지·지난 티켓·ADR 같은 기록이거나 이 티켓과 무관한 "열일곱"이다(Grep으로 봤다).

## 셀프 리뷰(`/code-review`)

범위: 기준 `11343375b`, 수정 파일 5개(사진 정답 제외), 미추적 3개(컴포넌트 셋. 일지는 머리뿐), 커밋 0개. 표준 축은 `sonnet`·high, 명세 축은 이 세션의 모델로 돌렸다. 둘 다 읽기만 하는 서브에이전트라 저장소는 바뀌지 않았다.

- 명세 축(Major 하나, 낮음): 컴포넌트 주석·쓰는 법 문서·스토리 주석 셋이 "용어집의 말"이라고 적었는데, `CONTEXT.md`에는 "비활성"의 풀이만 있고 "활성", "비밀번호 미설정", "잠김"은 없다. `Grep`으로 `CONTEXT.md`에서 세 낱말을 찾아 없는 것을 직접 확인했다. 고쳤다: 세 곳을 명세 `.scratch/admin-login/spec.md`의 "배지의 이름"으로 바꾸고, 용어집은 "비활성" 풀이로만 든다.
- 표준 축(확정 위반 없음): 같은 지적을 Minor로 냈고(위와 같이 고쳤다), Nit 하나 "같은 흐린 글자지만 글자가 다르다"의 두 뜻을 "같은 흐린 색이지만 문구가 다르다"로 고쳤다.
- 남겼다: 티켓이 `done`인데 올리기 칸이 열려 있다는 지적(근거는 `upload.md` 1이 병합 뒤에 올리라고 정한 것이고, `Status:`의 값은 첫 낱말로 읽는 규칙이라 도구는 막지 않는다. 병합 뒤 올리기 세션이 칸을 닫는다), `BASE`가 `StatusBadge`와 같은 긴 클래스 문자열이라는 중복 냄새(두 컴포넌트를 나누는 것이 명세와 티켓의 결정이고 `StatusBadge`를 고치지 않는다는 요구가 있다), `TEXT`·`ICON`·`STATUS_CLASS`가 같은 키 넷을 되풀이하는 약한 반복(`StatusBadge`와 같은 모양의 관례), 아이콘 스토리가 일곱 이름을 `toContain`으로 되풀이하는 것(일곱이 정말 들어갔는지 이름으로 고정한다), 아이콘 보여 주기용 스토리의 `kim.admin` 앞 점 줄이 그린 화면에 없는 모양이라는 지적(규칙이 컴포넌트마다 보여 주기용 하나를 요구하고, 그린 화면 계정 메뉴의 줄은 이름·단계·`chevrons-up-down`이라 점은 보탠 것이다).
- 다시 돌린 것: `prettier --check`(통과)와 배지 스토리 8개(통과). 나머지는 커밋의 pre-commit이 갈음한다.
