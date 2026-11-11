# probe-round-marked-measured-unconditionally: **0430의 10회차. release-image의 netns 프로브가 호스트에서 본 양성 대조 회차를 조건 없이 `measured=True`로 세어, `up`이 실패해 배치가 서지 않은 회차도 측정으로 세어졌다**

**상태:** 열림
**어디로:** `tools/hook_scratch_probe_rule.py`: 저장소 프로브(`.scratch/**/probes/*.py`)를 Write·Edit할 때, 회차 블록 안에서 조건도 단언도 거치지 않고 `mark(measured=True`를 부르는 자리가 있으면 probes.md 첫 항목(표지를 `measured`에 건다)을 짚는다. 판정의 꼴과 그 시험, 페이로드 표는 반영하는 티켓이 정한다
**승인:** 자체 승인 2026-11-11, 10회차(0430의 10회차. 0430은 9회차로 `.scratch/harness/issues/scratch-probe-hook-rounds-and-reread.md`에 닫혔다), 일지 2026-11-11-1532-release-image-design-round3.md. ADR 불필요

(셀프 리뷰 두 축은 놓쳤고 PR 직전 CodeRabbit CLI가 Minor로 잡았다. 그 프로브는 `Rounds`를 쓰고 있어 0430이 더한 계기에는 걸리지 않는다. 글자만 보는 검사는 맞지 않는다. 저장소 프로브의 `measured=True`는 파일 20개에 71곳이고(Grep으로 셌다), 표지를 본 갈래 안에서 부른 것이 섞여 있다)
