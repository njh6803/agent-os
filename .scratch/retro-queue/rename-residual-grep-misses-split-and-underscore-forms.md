# rename-residual-grep-misses-split-and-underscore-forms: 용어를 바꾸는 chore의 잔존 확인이 줄바꿈으로 갈라진 꼴과 밑줄 꼴을 놓쳤다(`git grep -E "질문 ?페이지"`와 `-Pzc`가 `질문\n// 페이지`와 `test_질문_페이지에서`를 못 잡아 티켓의 "잔존 0" 닫힌 주장이 거짓으로 지났다)

**상태:** 열림
**어디로:** `docs/agents/issue-tracker.md`의 이름 바꾸기 chore 티켓 서식에 잔존 확인 한 줄(공백·줄바꿈·주석 머리표·밑줄을 허용하는 정규식으로 추적 파일 전부를 훑는다). 검사가 아니라 지침인 까닭은 바꾸는 말이 chore마다 달라 도구에 고정할 꼴이 없어서다. 같은 실수의 다섯 번째 반복에서 더한다
**승인:** 자체 승인 2026-11-13, 자체 승인 2026-11-18, 3회차, 일지 2026-11-13-1625-rename-portal-to-widget-preview.md·2026-11-17-2031-plain-words-in-written-artifacts.md(2회차, 2026-11-17)·2026-11-18-1559-rename-workflow-terms.md(3회차), ADR 불필요. 같은 서식 자리에서 더 바꾼 쪽(기록 줄을 고친 것)은 `rename-chore-edits-record-lines`

사건: 앞 세션이 90여 개 파일의 치환 뒤 잔존을 `git grep -IlE "질문 ?페이지"`와 `git grep -Pzc`로 세고 0이라 닫았다. 셀프 리뷰 두 축이 갈라진 꼴 둘(`web/apps/portal/browser/portal.ts` 21-22행, `web/apps/widget/tools/start.ts` 22-23행)과 밑줄 꼴(`tests/test_portal_llm.py`의 시험 함수 이름)을 짚었고, 이 세션이 공백·줄바꿈·주석 머리표·밑줄을 허용하는 파이썬 정규식으로 추적 파일 전부를 훑어 기록 파일 밖에 더 없음을 확인했다. 셀프 리뷰가 제 몫을 한 사건이라 지침의 추가 기준 횟수(다섯 번째)에는 닿지 않았다.

(2회차: 용어집의 이름 열여섯을 바꾼 chore다. 갈라진 꼴과 밑줄 꼴은 이 항목의 정규식으로 훑어 찾았다. 놓친 것은 정규식이 잡지 못하는 꼴이다. 옛 이름의 낱말 사이에 조사가 끼거나 줄여 부른 꼴이 `retro` 스킬 네 곳("더하는 것의 문턱", "문턱대로")과 `src/agent_os/sdk/events.py`의 주석("덮는 범위의 끝")에 남았고, 티켓의 "잔존 0"이 그 채로 셀프 리뷰까지 갔다. 명세 축이 잡았다. 반영할 때 옛 이름의 핵심 낱말 하나(문턱, 덮는)로도 한 번 훑어 눈으로 가리는 줄을 함께 본다)

(3회차: 용어집의 작업 규약 쪽 이름 셋을 바꾼 chore다. 줄바꿈으로 갈린 "되돌려⏎합치기"(`tools/check_ticket.py` 105~106행, 카나리아 명세 `dev_base_next_session_backmerge_row.toml` 1~2행 머리 설명)와, 노트 조각을 줄여 부른 "조각"(`tools/check_notes.py`의 독스트링과 오류 문구, 워크플로 주석 셋, 시험의 커밋 제목과 주석)이 남은 채 셀프 리뷰까지 갔다. 표준 축과 명세 축이 잡았다)
