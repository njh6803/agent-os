# probe-ranges-hand-merged-across-docs: 프로브를 다시 잴 때마다 여러 실행을 합친 범위와 회차 수를 손으로 다시 세어 네 문서에 옮겨 적었고, 첫 판의 수 셋은 원본 기록과 달랐다

**상태:** 열림
**어디로:** `docs/agents/issue-tracker.md`의 프로브와 근거 절이나 `.claude/skills/to-spec/SKILL.md`: 여러 실행을 합친 수를 드는 프로브는 실행마다의 요약을 프로브 폴더에 남기고 합친 범위를 스크립트가 내게 하거나, 명세와 기능 계획은 수를 옮겨 적지 않고 프로브 README의 결과 번호만 가리키게 한다. 어느 쪽인지는 반영하는 chore가 정한다. 더하는 것이라 문턱은 다섯 번째 반복이다
**승인:** 자체 승인 2026-11-27, 1회차, 일지 2026-11-27-0407-widget-runtime-values-spec.md. ADR 불필요

(widget-runtime-values 명세의 프로브 `prebuilt_start`다. 리뷰 층마다 프로브를 고치고 일곱 섹션 전체를 다시 재, 실행이 셋에서 여섯으로 늘었다. 그때마다 첫 응답 시간, 메모리, healthy, 끄기의 합친 범위와 회차 수를 손으로 다시 더해 명세, 프로브 README 둘, deploy-package 기능 계획에 옮겼다. 원본 기록(`results.jsonl`, `raw.log`)은 세션 스크래치 폴더에 있어, 인계받은 세션은 앞 실행의 원본을 열지 못하고 README에 적힌 수에 새 실행의 값을 더했다. 첫 세션은 README를 쓴 뒤 원본과 다시 대 보다 수 셋이 틀린 것을 스스로 찾았다. 리뷰가 틀린 수를 잡은 적은 없다.)
