# canary-question-quote-left-source: 카나리아가 통과한 뒤 셀프 리뷰가 원천을 고쳐 물음이 자리를 가리키려고 따온 원천의 글이 원천에서 사라졌는데, 사전 확인(`tools/canary.py --preflight`)은 기대 문구(`expect`)만 원천에서 찾아 그 어긋남을 알리지 않았다

**상태:** 열림
**어디로:** `tools/canary.py`의 사전 확인(`source_problems`): 물음(`question`)의 따옴표 구절이 실험군 원천에 글자 그대로 있는지도 보고, 없으면 알린다. 물음이 원천 밖의 글을 일부러 따오는 명세가 있으면 그 꼴을 가르는 법은 chore가 정한다. 새 검사라 같은 실수의 다섯 번째이거나 손상이 한 번 났을 때 더한다
**승인:** 자체 승인 2026-11-18, 1회차, 일지 2026-11-18-1559-rename-workflow-terms.md. ADR 불필요

(사건: `.scratch/harness/probes/canary/dev_base_next_session_root_branch.toml`이 통과한 뒤 셀프 리뷰가 `next-session` `directive.md` 30행의 조건을 "…가 아니거나"에서 "…에 있지 않거나"로 고쳤다. 물음은 옛 글을 따온 채였고 사전 확인은 통과였다. `docs/constitution/operations.md` 카나리아 항목의 갈음 조건 넷을 손으로 대 보다 찾아, 물음을 고치고 그 명세를 다시 돌렸다(통과 4))
