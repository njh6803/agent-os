# admin-style 화면

관리 화면의 완성 화면이다. `/ui-design admin-style`이 Design 아티팩트에 그리고 사람이 고른 것을 그 스킬의 7단계가 옮겼다(일지 2026-10-23-27). 규약은 `docs/agents/issue-tracker.md`의 화면 디자인 절이고, 그린 순서와 화면은 시작 프롬프트 `screens-prompt.md`다. 그리며 `frontend-design`과 저장소 규칙이 부딪친 자리는 `.scratch/design-system/design/frontend-design-conflicts.md`의 2026-10-22 행이다.

아티팩트에는 쪽이 둘이다. "와이어프레임"(아트보드 열다섯, 회색조)과 "완성 화면"(아트보드 열일곱)이고, 여기 옮긴 것은 완성 화면 열일곱과 캔버스 색인 `canvas.json`이다. 와이어프레임은 아티팩트에만 남겼다(사람이 확정하는 선택 화면에서 골랐다, 일지 2026-10-23-27). 그 확정은 캔버스 메모에 없고 일지에만 있다. 확정을 메모에 적게 한 스킬 6단계의 고침(harness 009)이 확정 뒤에 들어왔다. 그래서 `canvas.json`의 `boards`와 `order`는 여기 없는 와이어프레임 파일(`Main.dc.html`, `wf-*.dc.html`)도 가리킨다. 와이어프레임을 다시 보려면 아티팩트를 연다. 화면 파일은 디자인 시스템을 `ds/agent-os/` 아래에서 불러오고 그 폴더는 옮기지 않았다(스킬 7단계가 `project/ds/`를 뺀다). 저장소에서 브라우저로 그려지는지는 보지 않았다.

와이어프레임에서 A·B 두 안을 그린 화면은 셋이고, 사람이 고른 안(일지 2026-10-23-27의 6단계)으로 완성 화면을 그렸다.

- 플러그인 목록: A(종류마다 묶은 줄). 고르지 않은 B는 종류를 열로 둔 표 하나였다.
- 실행 하나: B(결정 자리가 오른쪽 옆 칸에 붙어 스크롤해도 보인다). 고르지 않은 A는 결정 자리가 이벤트 열 아래였다. 모바일은 두 안이 같다.
- 설정: A(테마 카드 넷이 한 줄). 고르지 않은 B는 2×2 격자였다.

그리며 둔 탐색용 가정이다. 결정이 아니고 명세가 결정으로 바꾸거나 다시 묻는다(시작 프롬프트 "고른 뒤" 2). 다섯째(빈 목록의 버튼과 결정 자리의 링크 둘)를 뺀 다섯은 캔버스의 메모(`notes`의 `wf-how`, `mk-how`)에도 적혀 있다.

- 플러그인 행의 스위치는 디자인 시스템 Switch라 보이는 이름을 스스로 그린다. 그래서 플러그인 이름을 스위치의 이름으로 두고, 플러그인 하나로 가는 링크를 같은 행의 "매니페스트"로 따로 달았다.
- 탐색의 "설정" 아이콘(Lucide `settings`)은 패키지의 아이콘 열여섯(`IconName`)에 없어 선 아이콘 SVG를 그 자리에 직접 넣었다. 시작 프롬프트 "고른 뒤" 2의 새 아이콘이라 명세 전에 사람에게 묻는다. 다른 아이콘은 모두 열여섯 안에 있다.
- 테마는 고르는 즉시 화면 전체에 적용되고 저장 버튼이 없다(시작 프롬프트의 가정).
- 승인 뒤 재개 스트림이 끊긴 화면은 트레이스를 다시 읽은 뒤의 모습이다. 결말 이벤트가 없어 머리의 상태 배지를 "결말 없음"으로 두었다. 결정할 것이 없어 오른쪽 옆 칸이 걷히고 이벤트 칸이 880px로 선다.
- 거르기 때문에 빈 실행 목록에 "전부 보기" 버튼을 두었다. 꺼진 플러그인으로 막힌 결정 자리에는 "플러그인 목록" 링크를, 채널 토큰이 없는 결정 자리에는 "설정 열기" 링크를 두었다.
- 실행 목록의 첫 행(`7f3a2c91…`)은 실행 하나 화면과 같은 실행이라 주체를 operator로 맞췄다. 아티팩트의 와이어프레임 쪽은 같은 행을 최종 사용자로 적어 어긋나 있다.

기준 커밋은 그릴 때 읽은 근거 문서의 커밋이다. 이 화면은 그 커밋에서 딴 워크트리에서 그려, 시작 프롬프트 "고른 뒤" 1의 날짜 어림(명령은 탐색 프롬프트 `.scratch/design-system/design/exploration-prompt.md`의 "고른 뒤" 3) 대신 그 커밋을 적었고, 어림이 아니라 "(어림)"을 붙이지 않았다. 그 어림은 `19bbfa06`을 내는데, 그 커밋은 이 워크트리를 딴 뒤에 main에 들어와 `plan.md` admin-style 행에 `next build`의 `.js` 풀기를 넘기는 괄호 하나를 더했다(`git diff b104f8fa 19bbfa06 -- <근거 문서 셋>`으로 손으로 봤다). 그 괄호는 화면에 닿지 않는다. 동기화한 커밋은 디자인 시스템 아티팩트 색인 `lastChange`의 `via`이고 부분 올리기라 그대로 적는다. 그 판에서 빌드가 저장소 원본을 그대로 옮기는 다섯이 코드와 바이트까지 같았다는 대조는 `.scratch/admin-style/probes/`의 `artifact_reads.json`이다.

| 파일 | 화면 | 근거 문서 | 기준 커밋 | 동기화한 커밋 | 아티팩트 |
|---|---|---|---|---|---|
| `mk-token.dc.html` | 관리 토큰 넣기, 데스크톱 1280px, 관리 토큰이 거부된 알림 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-token-m.dc.html` | 관리 토큰 넣기, 모바일 375px, 서버에 닿지 못한 알림 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-plugins.dc.html` | 플러그인 목록, 데스크톱 1280px, 고른 안 A(종류마다 묶은 줄). 켜고 끄기에 실패한 알림과 추적 식별자 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-plugins-m.dc.html` | 플러그인 목록, 모바일 375px | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-plugin.dc.html` | 플러그인 하나, 데스크톱 1280px, 다시 확인하는 중 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-plugin-m.dc.html` | 플러그인 하나, 모바일 375px | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-runs.dc.html` | 실행 목록, 데스크톱 1280px, 녹청 라이트 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-runs-dark.dc.html` | 실행 목록, 데스크톱 1280px, 녹청 다크 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-runs-m.dc.html` | 실행 목록, 모바일 375px(실행마다 카드) | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-runs-empty.dc.html` | 실행 목록, 거르기 때문에 빈 목록 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-runs-loading.dc.html` | 실행 목록, 처음 불러오는 중(행 자리의 뼈대) | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-run.dc.html` | 실행 하나, 데스크톱 1280px, 고른 안 B(결정 자리가 오른쪽 옆 칸) | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-run-resumed.dc.html` | 실행 하나, 승인 뒤 재개 스트림이 끊긴 정보 알림 | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-run-m.dc.html` | 실행 하나, 모바일 375px(결정 자리가 이벤트 아래) | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-decision.dc.html` | 결정 자리의 변형 다섯(기본, 꺼진 플러그인으로 막힘, 최종 사용자의 실행, 채널 토큰 없음, 형식 1 트레이스), 자리 폭 360px | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-settings.dc.html` | 설정, 데스크톱 1280px, 고른 안 A(테마 카드 넷이 한 줄, 카드마다 그 테마로 칠한 표본) | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
| `mk-settings-m.dc.html` | 설정, 모바일 375px(테마 카드 2열, 채널 토큰을 넣은 상태) | `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md`, `.scratch/plan.md`(admin-style 행), `.scratch/admin-style/design/screens-prompt.md` | `b104f8fa` | `agent-os 부분 main@c41adad` | https://claude.ai/artifact/KJgGKTc76zzyHwaGaydGk2 |
