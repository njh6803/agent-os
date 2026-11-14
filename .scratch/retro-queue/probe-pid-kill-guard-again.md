# probe-pid-kill-guard-again: **0307의 2회차. release-image의 프로브 셸 둘(`entry-widget.sh`의 sampler, `supervise.sh`의 dockerd)이 저장한 pid만 보고 `kill`을 쳤다**(PR의 CodeRabbit 첫 회차가 Minor로 잡았다)

**상태:** 열림
**어디로:** `.claude/rules/probes.md`: 프로세스를 끄는 탐침은 pid만 보고 끄지 않는다는 항목이 이미 있다. 이 사건은 저장소의 `.sh` 프로브에서 어겨졌다. 회차 5에서 `kill`이 든 프로브 셸을 쓰는 자리에 그 항목을 짚는 계기 훅을 고른다
**승인:** 자체 승인 2026-11-14, 2회차(0307의 2회차. 0307은 1회차로 닫혔다), 일지 2026-11-13-1843-release-image-spec.md. ADR 불필요

두 곳 모두 띄운 프로세스가 먼저 끝나면 그 pid를 상관없는 프로세스가 받을 수 있다. 이 세션은 sampler를 `sh -c`로 띄우며 회차 전용 표지를 인자로 싣고, supervise는 dockerd의 환경 변수 표지로 끄기 직전에 확인하게 고쳤다(supervise의 표지가 컨테이너 안 dockerd에 실제로 실리는지는 돌려 보지 못했다).
