# 08: 디자인 시스템의 아이콘 일곱과 계정 상태 배지

**What to build:** 디자인 시스템(`web/packages/ui`)의 스토리북에서 새 아이콘 일곱(대화, 계정, 계정 메뉴 열기, 로그아웃, 링크 복사, 잠김, 상태 점)과 계정 상태 배지 하나를 본다. 배지는 값 넷(활성, 비활성, 비밀번호 미설정, 잠김)을 받아 글자를 스스로 쓰고, 앞의 셋은 상태 점, 잠김은 자물쇠 아이콘을 붙인다. 상태를 색만으로 가르지 않는다. 디자인 시스템 아티팩트(claude.ai에 올려 둔 디자인 시스템 페이지. 화면을 그릴 때 이것을 본다)에도 같은 것이 오른다. 관리 화면은 아직 이것을 쓰지 않는다. 09와 12가 쓴다.

근거는 명세 `.scratch/admin-login/spec.md`의 "디자인 시스템에 더하는 것", "계정 화면과 내 비밀번호"의 "배지의 이름", Testing Decisions의 "사진 비교"다. 그린 화면은 `.scratch/admin-login/design/mk-accounts.dc.html`과 `ch-a.dc.html`이다. 결정은 ADR 0026(디자인 시스템과 앱의 경계), ADR 0053(마크다운 부품)이다. 이 티켓의 "명세 검토"는 일지 `docs/journal/2026-11-25-1007-admin-login-tickets.md`의 "명세 검토(spec-reviewer)" 절을 가리킨다.

**Blocked by:** 01

**Status:** ready-for-agent

### 시작 전

- [ ] Skill 도구로 `sync-design-system`을 인자 `확인`으로 부른다. 웹에서 고친 것이 있으면 먼저 들인다

### 아이콘

- [ ] `message-square`, `users`, `chevrons-up-down`, `log-out`, `copy`, `lock`, `circle`을 디자인 시스템의 아이콘 이름 목록에 더한다(열일곱에서 스물넷). 모양은 Lucide이고 선은 1.5px이다(`.claude/rules/web-design.md`)

### 계정 상태 배지

- [ ] 새 배지 컴포넌트 하나를 더한다. 실행의 상태 배지는 실행 상태 넷에만 쓰므로 고치지 않는다. 바탕을 칠하지 않고 옅은 테두리 안에 글자와 아이콘을 두는 것은 실행의 상태 배지와 같다
- [ ] 색의 쓰임새 토큰(색 값이 아니라 `text-text-muted`처럼 쓰임새로 이름 붙인 디자인 값. 테마와 모드가 값을 바꾼다)은 기존 토큰에서 고른다. 새 토큰을 더하지 않는다
- [ ] 스토리(스토리북에서 컴포넌트 하나를 한 상태로 보여 주는 쪽), 쓰는 법 문서(`<Name>.md`), 보여 주기용 스토리(`쓰임: 운영자 계정 목록의 상태`)를 함께 둔다

### 올리기

- [ ] Skill 도구로 `sync-design-system`을 인자 `올리기`로 불러 디자인 시스템 아티팩트에 올린다

### 검증

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [ ] `packages/ui`를 고치므로 사진 비교(화면을 찍어 정답 사진과 화소 단위로 견주는 시험) 셋(`pnpm -C web visual`, `pnpm -C web visual:widget`, `pnpm -C web visual:admin`)을 Docker로 로컬에서 치고, 새 아이콘과 배지의 정답을 디자인 시스템의 사진 정답에 더한다
