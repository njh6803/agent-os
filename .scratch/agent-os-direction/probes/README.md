# agent-os-direction 프로브

명세·ADR·코드 주석이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거".

저장소 루트에서 돈다. `.env`의 `ANTHROPIC_API_KEY`가 있어야 한다(워크트리에서는 주 체크아웃의 `.env`를 `--env-file ../../../.env`로).

```sh
uv run --env-file .env python .scratch/agent-os-direction/probes/probe_models_price.py
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `probe_models_price.py` | Anthropic Models API(`GET /v1/models`, `GET /v1/models/{id}`)의 응답에 단가 칸이 있는지. 토큰을 쓰지 않는 GET 둘이고 회차는 둘(목록의 첫 항목, 그 id의 단건)이다. 문서가 적은 칸 `id`(비지 않은 문자열)와 `max_input_tokens`(정수)가 있고 단건이 요청한 id를 되돌려 줄 때만 측정으로 센다. 갈래는 응답 JSON의 모든 키(중첩 포함)에 price·pricing·cost·usd·dollar 가운데 하나라도 드는지다. 잰 것은 그 두 호출의 응답뿐이고, 다른 끝점이나 다른 항목은 재지 않았다 | ADR 0042 묶음 ② 9(단가는 모델 매니페스트의 선택 칸이고 자동 경로는 찾지 못했다) | 단가 칸을 없애거나 자동 단가를 다시 찾을 때, anthropic SDK의 주 버전이 오를 때 | anthropic 1.7.0, 2026-11-04. 이 자리의 파일을 워크트리 루트에서 `uv run --env-file ../../../.env python .scratch/agent-os-direction/probes/probe_models_price.py`로 돌려 탐침이 찍은 결과: 측정 2회차·측정 아님 0회차, 둘 다 price_absent, 최상위 키 열하나(capabilities, created_at, deprecated_at, display_name, id, lifecycle, line, max_input_tokens, max_tokens, retires_at, type). 이름 검색의 양성 대조는 없고 대신 최상위 키 전부를 `RESULT` 줄에 찍어 사람이 본다(단가 칸이 다른 이름일 가능성은 그 목록으로 가른다). 같은 결과를 세션 스크래치패드의 사본으로 먼저 봤다(일지 2026-11-04-01 라운드 3 1호출) |
