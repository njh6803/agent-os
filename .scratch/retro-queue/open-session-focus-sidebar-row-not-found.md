# open-session-focus-sidebar-row-not-found: 병합 뒤 새 세션을 연 다음 `tools/open_session.ps1 -Action focus`가 두 번 모두 사이드바의 행을 찾지 못하고 종료 1로 끝났다

**상태:** 열림
**어디로:** `tools/open_session.ps1`의 화면 옮기기 단계: 실패한 출력의 원인을 먼저 가른다. 사이드바에 분할 패널이 여섯이던 것(`get_window_layout`)이 행을 못 찾는 까닭인지 본다. 같은 파일의 `open-session-page-timeout-late-screen`(새 세션 화면을 늦게 찾는 멈춤)과 뿌리가 같은지 함께 본다(고침, 원인 미상)
**승인:** 자체 승인 2026-11-21, 만료된 0524의 3회차(0524가 같은 사건의 2회차였고 2026-11-12에 만료했다), 일지 2026-11-21-0502-connection-check-spec.md. ADR 불필요

PR 614를 병합한 뒤 새 세션(`docs/connection-check-spec`)을 연 다음 `tools/open_session.ps1 -Action focus -Title docs/connection-check-spec`이 `-TimeoutSec 90`과 `60`으로 두 번 모두 사이드바의 행을 찾지 못하고 종료 1로 끝났다. 둘째 시도 전에 `list_sessions`는 그 세션의 제목이 이미 `docs/connection-check-spec`이라고 답했다. 그때 창에는 분할 패널이 여섯이었다. 원인은 보지 않았다.
