# rename-residual-grep-misses-split-and-underscore-forms: 용어를 바꾸는 chore의 잔존 확인이 줄바꿈으로 갈라진 꼴과 밑줄 꼴을 놓쳤다(`git grep -E "질문 ?페이지"`와 `-Pzc`가 `질문\n// 페이지`와 `test_질문_페이지에서`를 못 잡아 티켓의 "잔존 0" 닫힌 주장이 거짓으로 지났다)

**상태:** 열림
**어디로:** `docs/agents/issue-tracker.md`의 이름 바꾸기 chore 티켓 서식에 잔존 확인 한 줄(공백·줄바꿈·주석 머리표·밑줄을 허용하는 정규식으로 추적 파일 전부를 훑는다). 검사가 아니라 지침인 까닭은 바꾸는 말이 chore마다 달라 도구에 고정할 꼴이 없어서다. 같은 실수의 다섯 번째 반복에서 더한다
**승인:** 자체 승인 2026-11-13, 1회차, 일지 2026-11-13-1625-rename-portal-to-widget-preview.md, ADR 불필요

사건: 앞 세션이 90여 개 파일의 치환 뒤 잔존을 `git grep -IlE "질문 ?페이지"`와 `git grep -Pzc`로 세고 0이라 닫았다. 셀프 리뷰 두 축이 갈라진 꼴 둘(`web/apps/portal/browser/portal.ts` 21-22행, `web/apps/widget/tools/start.ts` 22-23행)과 밑줄 꼴(`tests/test_portal_llm.py`의 시험 함수 이름)을 짚었고, 이 세션이 공백·줄바꿈·주석 머리표·밑줄을 허용하는 파이썬 정규식으로 추적 파일 전부를 훑어 기록 파일 밖에 더 없음을 확인했다. 셀프 리뷰가 제 몫을 한 사건이라 지침을 더하는 문턱(다섯 번째)에는 닿지 않았다.
