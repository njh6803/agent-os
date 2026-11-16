# node-probes-miss-probe-rules: Node로 지은 새 프로브의 첫 판이 `.claude/rules/probes.md`의 두 항목을 어겼고 PR 직전 리뷰가 잡았다(다섯째 항목: `fetch_idle_timer.mjs`가 자식 프로세스의 첫 줄을 제한 시간 없이 기다렸다. 첫 항목: `preview_shield.mjs`가 화면의 자리를 읽지 못하면 그 회차를 측정이 아니라고 세지 못하고 예외로 끝났다)

**상태:** 열림
**어디로:** 하네스 chore: 0339가 파이썬 프로브에 둔 길(`tools/probe_kit.py`의 `Rounds`와 `LineReader`, 그것을 쓰지 않은 파이썬 프로브를 짚는 알림 훅)이 `.mjs` 프로브에는 없다. Node용 도우미를 두거나 알림 훅이 `.mjs` 프로브도 짚게 한다. 어느 쪽인지는 chore가 정한다
**승인:** 자체 승인 2026-11-16, 0339의 7회차, 일지 2026-11-16-1705-portal-admin-spec.md. ADR 불필요

두 스크립트는 portal-admin 명세 세션이 지은 프로브이고(서브에이전트에 맡긴 것을 포함한다) 셀프 리뷰 두 축을 지났다. 고친 판은 `.scratch/portal-admin/probes/`에 있다.
