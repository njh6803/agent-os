# llm-local-record-uncommitted-tree: 커밋하지 않은 작업 트리로 돈 `llm_local` 기록은 시험한 커밋이 기준 브랜치의 끝으로 찍혀, 유효 판정이 글자대로는 늘 무효가 된다

**상태:** 열림
**어디로:** `tools/llm_local.py`(기록 묶음에 범위 경로의 변경 해시를 더하거나 커밋하지 않은 범위 변경이 있으면 기록에 표시한다), `.claude/skills/next-session/merge.md`("병합 전" 3의 유효 판정). `docs/constitution/operations.md` LLM 테스트의 "기록과 유효함"까지 닿으면 ADR과 사용자 승인이 따로 필요하다
**승인:** 자체 승인 2026-11-21, 1회차, 일지 2026-11-20-1918-serve-requires-database.md. ADR은 operations.md를 고칠 때만 필요

03-serve-requires-database가 구현 끝에 커밋 전 작업 트리로 `llm_local`을 돌렸고 기록의 `commit`이 `7b52bbd61`(기준 dev의 끝)로 찍혔다. 규약의 유효 판정은 시험한 커밋과 브랜치 끝 사이에서 범위 경로가 바뀌었는지로 가르는데, 이 기록은 글자대로는 `src/agent_os/` 네 파일을 건너 늘 무효다. 세션 둘이 시험한 내용과 커밋한 내용이 같은지 해시로 대 보려 했고(`git diff HEAD -- src …`의 sha256 앞 16자), 추적 파일 셋은 ruff 서식 한 줄 때문에 같은 바이트로 맞추지 못해 한 번 더 대 봐야 했다. 세 번째 세션이 시험 때 작업 트리를 임시 색인으로 다시 만들어 맞췄다. CodeRabbit도 첫 리뷰에서 이 기록을 Major로 짚었다.

처방의 후보는 둘이다. 도구가 범위 경로의 `git diff <기준 커밋> --` 해시를 기록 묶음에 남기고 유효 판정이 그 해시를 현재 머리와 견주게 하는 것, 또는 절차에서 `llm_local`을 커밋 뒤에 돌리게 하는 것이다. 앞의 것이 사람의 해시 손재주를 없앤다.
