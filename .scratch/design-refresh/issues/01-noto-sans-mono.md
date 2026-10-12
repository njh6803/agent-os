# 01: 글꼴 — 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다

**What to build:** 위젯과 관리 화면이 `@agent-os/ui`의 글꼴 CSS를 들이면, 어느 테마를 골라도 한글은 Noto Sans KR(400·500·600)로, 고정폭은 Noto Sans Mono(400·500)로 그려진다. 테마가 더는 고정폭 글꼴을 고르지 않는다. JetBrains Mono와 IBM Plex Mono, 그리고 IBM의 설치 스크립트를 끄던 설정이 저장소에서 빠진다. 판정 스토리 Fonts가 다섯 벌의 적재와 굵기를 본다. 사진의 정답은 바뀌지 않는다.

02와 나란히 돈다. 둘은 서로를 막지 않는다. 03이 둘을 기다린다. 헌법(`docs/constitution/tech.md`)에 닿지만, 헌법을 바꾸는 티켓이 그 기능의 첫 티켓이며 다른 티켓을 막는다는 규약(`docs/agents/issue-tracker.md` 전체 계획)의 예외다. 이 티켓이 고치는 것은 결정이 아니라 웹 행의 사실 문장(patch)이고, 02는 그 문장에 기대지 않는다. 03이 이 티켓을 기다리므로 헌법을 바꾸는 티켓이 그 뒤의 티켓보다 먼저 선다는 규약의 뜻은 지킨다(design-system 티켓 02의 선례).

근거는 `.scratch/design-refresh/spec.md`의 "글꼴" 절, "테마" 절의 "테마가 바꾸지 않는 것", "문서와 설정" 절과 그 2026-10-12 명세 검토·to-tickets 주석이다. 결정은 ADR 0026의 2026-10-12 이력 "테마는 넷이고 색만 바꾸며, 글꼴은 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다"다. 측정은 `.scratch/design-refresh/probes/font.mjs`다.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] **패키지.** `@fontsource/noto-sans-mono`를 `packages/ui`의 `dependencies`에 더하고 `@fontsource/jetbrains-mono`와 `@ibm/plex-mono`를 뺀다. 판은 잰 5.3.0에서 시작한다. 공급망 유예(`minimumReleaseAge`)를 푸는 예외는 들이지 않는다. 설치한 판이 잰 판과 다르면 `font.mjs --version <판>`으로 그 판을 다시 재고(라이선스, 설치 스크립트, `@font-face`의 모양) 일지에 적는다
- [x] **설치 조건.** `web/pnpm-workspace.yaml`의 `allowBuilds`에서 `@ibm/plex-mono` 줄을 빼고 머리 주석을 고친다. 새 글꼴 패키지에는 설치 때 도는 스크립트가 없어 더할 것이 없다(`font.mjs`). `pnpm -C web install`이 멈추지 않고 지나는지 본다
- [x] **글꼴 CSS.** Noto Sans KR처럼 Noto Sans Mono의 굵기 CSS 둘(`400.css`, `500.css`)을 `@import`한다. JetBrains Mono의 `@import`와, IBM의 split 파일을 다시 선언하던 `@font-face` 열 개를 지운다. 판정 스토리 RemFree는 그대로 지난다
- [x] **글꼴 변수는 뿌리에 한 번 둔다**(명세가 정했다). `--sans`와 `--mono`를 테마 블록에서 빼고 뿌리(`:root, :host`)에 한 번 둔다. 고정폭 스택은 `"Noto Sans Mono", ui-monospace, monospace`이고 한글은 덮지 않는다. 테마 블록의 `--weight-mid`는 건드리지 않는다. 테마 블록을 색만으로 다시 쓰는 03이 뺀다. 페이지 안 위젯이 감싼 요소에서 `--sans`·`--mono`를 다시 정하는 길은 그대로다
- [x] **Fonts.** 판정 스토리 Fonts가 다섯 벌(Noto Sans KR 400·500·600, Noto Sans Mono 400·500)이 `document.fonts.load`로 `loaded`인지 본다. 모든 테마에서 `--sans`·`--mono`가 같은지는 03의 Matrix가 여덟 벌에서 본다(명세 Matrix의 to-tickets 주석)
- [x] **사진은 그대로다.** 사진 비교에 찍히는 스토리 가운데 고정폭을 쓰는 것이 없다(명세 검토가 `src`를 grep했다). `pnpm -C web visual`이 정답을 하나도 바꾸지 않고 초록인지 본다. 바뀌면 멈추고 어느 스토리가 고정폭이나 바뀐 변수를 쓰는지 본다
- [x] **헌법.** `docs/constitution/tech.md` 웹 행의 글꼴 줄과 글꼴 패키지, `allowBuilds`의 문장을 새 글꼴로 고친다. 같은 행의 테마 문장("색과 글꼴의 한 벌로 다섯")은 이 티켓에서 "글꼴"이 거짓이 되므로 "색의 한 벌로 다섯"으로 고치고, 수와 이름은 03이 고친다. `docs/constitution/README.md`의 버전을 patch로 올린다
- [x] **함께 고칠 문장.** 옛 글꼴의 말(`JetBrains Mono`, `IBM Plex`, `plex-mono`, `jetbrains-mono`)이 살아 있는 문서와 코드에서 0인지 본다. 기록(일지, 지난 명세와 티켓, ADR의 지난 이력, 헌법 README의 지난 판 기록, 디자인 파일 v3와 첫 탐색 프롬프트)은 제외한다(명세의 잔존 grep 절). `.design-sync/`(NOTES 등)는 동기화와 함께 05가 고친다. 코드 주석에서 테마마다 고정폭이 다르다는 문장(글꼴 CSS의 머리 주석, 테마 목록의 머리 주석이 든 "고정폭 글꼴")도 고친다
- [x] **원칙 III.** 판정 스토리를 고칠 때 `as`·`any`·`!` 없이 쓴다
- [ ] **이 기능의 첫 병합인지는 병합 직전에 판정한다.** `git fetch` 뒤 `origin/main`의 `.scratch/plan.md`에서 design-refresh 행이 아직 `todo`이면(02가 먼저 병합되지 않았으면) 이 PR이 `in-progress`로 바꾼다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이고 사진 비교 명령도 로컬에서 초록이다. web 파일만 바꾸므로 LLM 테스트는 돌리지 않는다
