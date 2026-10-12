# kickoff-auto-flow 프로브

명세 `.scratch/kickoff-auto-flow/spec.md`가 근거로 드는 측정이다. 규약은 `docs/agents/issue-tracker.md`의 프로브와 근거 절이다.

| 프로브 | 무엇을 재나 | 근거로 드는 곳 | 다시 돌 때 |
|---|---|---|---|
| `skill_live/run.py`, `skill_live/show.py` | 세션 도중에 만든 `disable-model-invocation` 스킬을 그 세션에서 사람이 `/이름`으로 부를 수 있는지. 폴더가 세션 전부터 있으면(D) 바로, 없던 폴더면(C·E) `/reload-skills` 뒤에만 불렸다. 부르기 턴마다 CLI의 표지 둘(다시 낸 사용자 메시지의 `<command-name>` 태그, 그 턴 `system/init`의 `skills`)로 가르고, 표지가 갈리지 않는 턴이 있으면 1로 끝난다. 사용자 레벨은 재지 않았다(독스트링) | 명세 "첫 시작", ADR 0028의 2026-10-12 이력 | `claude` CLI와 로그인. haiku 세션 셋. claude 2.1.296에서 네 번 돌렸고 셋째부터 표지를 보는 판이다 |
| `billing_usage/run.py` | 사용자 billing usage 두 길(항목, 요약)을 `year`·`month`로 이번 달만 받는지, 항목의 열쇠와 값, 저장소 이름의 모양(주인 없이 이름만), 저장소와 `sku`마다의 Actions 분, 공개 여부(`gh repo list` 한 번), 요구 범위 헤더(`user`). 이번 달 밖의 날짜가 섞이거나 항목이나 저장소 목록이 비면 1로 끝난다. 금액과 사용량 없는 저장소의 이름은 찍지 않는다 | 명세 "준비"의 Actions 분량 | `gh` 로그인(`user` 범위). gh 2.98.0, 계정 플랜 `free`, 이번 달 항목은 공개 저장소 하나뿐이었다 |

## 결과 (2026-10-12)

- `skill_live`: C는 만든 뒤 두 번 불러도 실리지 않았고(다시 낸 메시지가 `/이름` 그대로, `skills`에 없음) `/reload-skills` 뒤에 실렸다. D는 바로 실렸다. E는 `/reload-skills` 뒤 첫 부르기에 실렸다. `/reload-skills`의 답은 세 회차 모두 "Reloaded skills: 17 skills available (no changes)"였는데도 그 뒤 실렸다. 측정이 아닌 부르기 턴은 0이었다.
- `billing_usage`: 항목 10개, 열쇠는 `date`·`discountAmount`·`grossAmount`·`netAmount`·`pricePerUnit`·`product`·`quantity`·`repositoryName`·`sku`·`unitType`이다. `product`는 `actions`, `sku`는 `Actions Linux`·`Actions Windows`, `unitType`은 `Minutes`였다. 날짜는 모두 이번 달이었다. `repositoryName`은 `agent-os`처럼 주인 없이 왔고, `gh repo list`가 낸 저장소 스물둘의 목록과 이름으로 맞춰 `PUBLIC`을 얻었다. 요약 길은 `product=actions`로 거르고 `timePeriod`가 `{"year": 2026, "month": 10}`이었으며 `grossQuantity`·`netQuantity`를 냈다(공개 저장소라 `netQuantity`는 0). 항목 길의 응답 헤더 `X-Accepted-OAuth-Scopes`는 `user`였다. 비공개 저장소의 항목은 이번 달에 없어 그 모양은 보지 못했다.
