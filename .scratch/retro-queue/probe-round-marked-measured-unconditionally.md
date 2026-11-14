# probe-round-marked-measured-unconditionally: **0430의 10회차. release-image의 netns 프로브가 호스트에서 본 양성 대조 회차를 조건 없이 `measured=True`로 세어, `up`이 실패해 배치가 서지 않은 회차도 측정으로 세어졌다**

**상태:** 열림
**어디로:** `tools/hook_scratch_probe_rule.py`: 저장소 프로브(`.scratch/**/probes/*.py`)를 Write·Edit할 때, 회차 블록 안에서 조건도 단언도 거치지 않고 `mark(measured=True`를 부르는 자리가 있으면 probes.md 첫 항목(표지를 `measured`에 건다)을 짚는다. 판정의 꼴과 그 시험, 페이로드 표는 반영하는 티켓이 정한다
**승인:** 자체 승인 2026-11-11, 10회차(0430의 10회차. 0430은 9회차로 `.scratch/harness/issues/scratch-probe-hook-rounds-and-reread.md`에 닫혔다), 일지 2026-11-11-1532-release-image-design-round3.md. 11회차 2026-11-12, 일지 2026-11-12-0248-local-model-spec.md. 12회차 2026-11-14, 일지 2026-11-13-1843-release-image-spec.md. ADR 불필요

(셀프 리뷰 두 축은 놓쳤고 PR 직전 CodeRabbit CLI가 Minor로 잡았다. 그 프로브는 `Rounds`를 쓰고 있어 0430이 더한 계기에는 걸리지 않는다. 글자만 보는 검사는 맞지 않는다. 저장소 프로브의 `measured=True`는 파일 20개에 71곳이고(Grep으로 셌다), 표지를 본 갈래 안에서 부른 것이 섞여 있다)

(11회차: local-model 명세의 프로브에서 PR의 CodeRabbit이 Minor로 표지 셋을 짚었다. 표지는 있었으나 재려는 상황을 다 보지 못했다. 키를 지운 뒤의 호출이 키 없음 거부로 끝났는지, 둘째 호출이 응답을 읽는 데까지 갔는지, 401·500·JSON 아님 갈래의 예외가 그 갈래의 원인인지를 보지 않았다. 앞선 셀프 리뷰 두 축과 PR 직전 리뷰도 같은 꼴을 여럿 잡았다(그 일지 "리뷰 반영"). 조건 없는 `measured=True`가 아니라 조건이 있어도 느슨한 꼴이라 위 `어디로:`의 훅은 이것을 잡지 못한다)

(12회차: release-image 명세의 프로브에서 PR의 CodeRabbit 첫 회차가 Major 하나와 Minor 여덟을 표지 쪽으로 짚었다. 실패한 도구가 "회복 안 됨"으로 세어졌고(`bridge_recover`, 요청 실행 표지 없음), 실패 원인과 관계없이 종료 코드만으로 측정을 셌고(`registry_tags.py`), `test failed` 한 문구가 DNS 실패와 설정 오류를 함께 받았다(`proxy_config`). 이 세션은 Major인 `bridge_recover`를 고치고 Minor 여덟은 기준을 바꾸면 기록한 결과를 다시 재야 해서 보류했다. 일지 "봇 첫 회차")
