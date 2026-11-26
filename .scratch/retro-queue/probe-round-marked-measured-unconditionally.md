# probe-round-marked-measured-unconditionally: **0430의 10회차. release-image의 netns 프로브가 호스트에서 본 양성 대조 회차를 조건 없이 `measured=True`로 세어, `up`이 실패해 배치가 서지 않은 회차도 측정으로 세어졌다**

**상태:** 열림
**어디로:** `tools/hook_scratch_probe_rule.py`: 저장소 프로브(`.scratch/**/probes/*.py`)를 Write·Edit할 때, 회차 블록 안에서 조건도 단언도 거치지 않고 `mark(measured=True`를 부르는 자리가 있으면 probes.md 첫 항목(표지를 `measured`에 건다)을 짚는다. 판정의 꼴과 그 시험, 페이로드 표는 반영하는 티켓이 정한다
**승인:** 자체 승인 2026-11-11, 10회차(0430의 10회차. 0430은 9회차로 `.scratch/harness/issues/scratch-probe-hook-rounds-and-reread.md`에 닫혔다), 일지 2026-11-11-1532-release-image-design-round3.md. 11회차 2026-11-12, 일지 2026-11-12-0248-local-model-spec.md. 12회차 2026-11-14, 일지 2026-11-13-1843-release-image-spec.md. 13회차 2026-11-17, 일지 2026-11-17-2031-plain-words-in-written-artifacts.md. 14회차 2026-11-24, 일지 2026-11-24-1637-widget-admin-server-spec.md. 15회차 2026-11-27, 일지 2026-11-27-0407-widget-runtime-values-spec.md. ADR 불필요

(셀프 리뷰 두 축은 놓쳤고 PR 직전 CodeRabbit CLI가 Minor로 잡았다. 그 프로브는 `Rounds`를 쓰고 있어 0430이 더한 계기에는 걸리지 않는다. 글자만 보는 검사는 맞지 않는다. 저장소 프로브의 `measured=True`는 파일 20개에 71곳이고(Grep으로 셌다), 표지를 본 갈래 안에서 부른 것이 섞여 있다)

(11회차: local-model 명세의 프로브에서 PR의 CodeRabbit이 Minor로 표지 셋을 짚었다. 표지는 있었으나 재려는 상황을 다 보지 못했다. 키를 지운 뒤의 호출이 키 없음 거부로 끝났는지, 둘째 호출이 응답을 읽는 데까지 갔는지, 401·500·JSON 아님 갈래의 예외가 그 갈래의 원인인지를 보지 않았다. 앞선 셀프 리뷰 두 축과 PR 직전 리뷰도 같은 꼴을 여럿 잡았다(그 일지 "리뷰 반영"). 조건 없는 `measured=True`가 아니라 조건이 있어도 느슨한 꼴이라 위 `어디로:`의 훅은 이것을 잡지 못한다)

(12회차: release-image 명세의 프로브에서 PR의 CodeRabbit 첫 회차가 Major 하나와 Minor 여덟을 표지 쪽으로 짚었다. 실패한 도구가 "회복 안 됨"으로 세어졌고(`bridge_recover`, 요청 실행 표지 없음), 실패 원인과 관계없이 종료 코드만으로 측정을 셌고(`registry_tags.py`), `test failed` 한 문구가 DNS 실패와 설정 오류를 함께 받았다(`proxy_config`). 이 세션은 Major인 `bridge_recover`를 고치고 Minor 여덟은 기준을 바꾸면 기록한 결과를 다시 재야 해서 보류했다. 일지 "봇 첫 회차")

(13회차: `.scratch/harness/probes/plain_words_reach/loading.py`. 표지(답하는 쪽이 도구를 부르지 않았다)는 있었으나, 양성 대조를 갈래끼리 맡기고 코드가 보지 않아 모든 갈래가 "없음"이라 답한 실행도 측정으로 세어 0으로 끝난다. 셀프 리뷰 표준 축이 Nit으로 잡았다. 기록한 결과에는 문장을 옮긴 갈래가 있어 결론은 그대로이고, 독스트링에 읽는 쪽의 몫이라고 적는 것으로 반영했다. 그 뒤 PR 직전 리뷰(CodeRabbit CLI)가 같은 자리와, 서브에이전트 갈래가 부른 서브에이전트의 종류를 보지 않는 것을 함께 짚어 코드로 옮겼다. 문장을 옮긴 측정 회차가 없으면 1로 끝나고, 부른 종류가 갈래와 다르면 측정이 아니다. 11회차와 같은, 조건이 있어도 느슨한 꼴이다)

(14회차: widget-admin-server 명세의 프로브 `.scratch/widget-admin-server/probes/uv_workspace/run.py`. PR의 CodeRabbit 첫 회차가 표지 넷을 Minor로 짚었다. 양성 대조가 심은 파일의 이름만 보고 규칙 `reportAssignmentType`은 보지 않았고, `-n 2` 회차가 마지막 줄의 `passed`만 보아 두 경로가 다 시험을 냈는지 몰랐고, 대조 이미지 회차가 `widget-admin`이 든 줄만 보아 `not a workspace member`라는 기대한 까닭을 보지 않았고, 타입 우회 검사는 종료 0과 빈 출력만 보았다. 앞의 셋은 11회차와 같은 느슨한 꼴이라 좁혔고(잰 실행의 로그가 좁힌 조건을 만족하는 것을 손으로 봤다), 넷째는 그 검사기가 정상이면 아무것도 찍지 않고 같은 사본 나무의 양성 대조 회차가 따로 있어 두었다. 같은 리뷰가 접속 주소의 비밀번호가 로그에 남는 것도 짚어 그 명령의 표준 출력을 로그에 싣지 않게 했다. 셀프 리뷰 두 축과 PR 직전 리뷰는 이 프로브의 표지를 짚지 않았다)

(15회차: widget-runtime-values 명세의 프로브 `.scratch/widget-runtime-values/probes/prebuilt_start/run.py`. `Rounds`를 쓰고 표지도 있었으나 느슨했다. PR 직전 CodeRabbit CLI가 열셋(Major 여섯)을, PR의 CodeRabbit 첫 회차가 열하나(Major 넷)를 표지와 대조 쪽으로 짚었다. 실패를 기대하는 대조가 상태와 종료 코드만 보고 실패의 까닭을 보지 않았고, 이미지 ID나 컨테이너 기록을 읽지 못한 회차와 빌드가 실패한 뒤 앞서 지어 둔 이미지로 돈 검사가 측정으로 세어질 수 있었다. PR 직전 리뷰의 지적을 고치며 넣은 표지(따로 건 요청의 연결 거절)도 가르려던 다른 해석 아래에서 나는 관찰이라 봇이 다시 Major로 짚었다. 리뷰 층마다 고친 뒤 일곱 섹션 전체를 다시 쟀고(셀프 리뷰 뒤, PR 직전 리뷰 뒤, 봇 첫 회차 뒤의 세 번), 그때마다 네 문서의 수를 손으로 맞췄다(`probe-ranges-hand-merged-across-docs`). 11회차와 같은, 조건이 있어도 느슨한 꼴이다)
