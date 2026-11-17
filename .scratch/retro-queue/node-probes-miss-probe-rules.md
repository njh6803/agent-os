# node-probes-miss-probe-rules: Node로 지은 새 프로브의 첫 판이 `.claude/rules/probes.md`의 두 항목을 어겼고 PR 직전 리뷰가 잡았다(다섯째 항목: `fetch_idle_timer.mjs`가 자식 프로세스의 첫 줄을 제한 시간 없이 기다렸다. 첫 항목: `preview_shield.mjs`가 화면의 자리를 읽지 못하면 그 회차를 측정이 아니라고 세지 못하고 예외로 끝났다)

**상태:** 열림
**어디로:** 하네스 chore: 0339가 파이썬 프로브에 둔 길(`tools/probe_kit.py`의 `Rounds`와 `LineReader`, 그것을 쓰지 않은 파이썬 프로브를 짚는 알림 훅)이 `.mjs` 프로브에는 없다. Node용 도우미를 두거나 알림 훅이 `.mjs` 프로브도 짚게 한다. 어느 쪽인지는 chore가 정한다
**승인:** 자체 승인 2026-11-16, 0339의 8회차, 일지 2026-11-16-1705-portal-admin-spec.md(7회차와 8회차가 같은 일지다. 8회차는 PR 봇이 같은 프로브들에서 끝없이 기다릴 수 있는 자리 셋과 던진 예외가 판정을 흐리는 자리 하나를 더 잡았다). ADR 불필요

두 스크립트는 portal-admin 명세 세션이 지은 프로브이고(서브에이전트에 맡긴 것을 포함한다) 셀프 리뷰 두 축을 지났다. 고친 판은 `.scratch/portal-admin/probes/`에 있다. 8회차의 자리는 넷이다. `login_relay`의 `probe.mjs`와 `tester_stub.mjs`가 도중에 끊긴 응답을 끝없이 기다렸고(둘), `fetch_idle_timer.mjs`의 재는 요청에 한도가 없었으며, `preview_shield.mjs`는 그려지기를 기다리다 던진 예외를 잡지 않아 종료 코드 1이 "측정했는데 기대와 다르다"와 섞였다(이 넷째는 끝없이 기다리는 자리가 아니다. 제한을 주지 않은 `waitForFunction`은 30초쯤에 던졌다). 셀프 리뷰 두 축과 PR 직전 리뷰를 모두 지났다.
