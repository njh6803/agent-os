# stale-warning: 검색 결과의 근거 문서가 오래됐다고 표시돼 있으면 답에 경고를 붙여, 낡은 근거로 답했음을 알린다.
**슬라이스:** 10
**Blocked by:** pilot-release, rag-engine:doc-freshness

오래된 근거의 경고. `cite-sources` 스킬이 검색 결과 조각의 "오래됨" 칸을 보고 답에 경고를 붙인다. 기한과 판정은 문서 검색 서버의 doc-freshness가 하고, agent-os 쪽은 그 칸을 읽기만 한다. 가짜 검색 서버에도 같은 칸을 더한다. 수락: 오래됨 칸이 켜진 조각을 근거로 한 답에 경고가 붙고, 꺼진 조각으로 한 답에는 붙지 않는다
