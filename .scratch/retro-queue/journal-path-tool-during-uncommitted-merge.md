# journal-path-tool-during-uncommitted-merge: 기준 브랜치를 합치고 아직 커밋하지 않은 워크트리에서 `tools/sibling_overlap.py --journal`이 합쳐 들어온 다른 브랜치의 일지를 이 브랜치의 일지로 찍는다

**상태:** 열림
**어디로:** `tools/sibling_overlap.py`의 `branch_journals`와 그 시험. 합치기를 커밋하기 전이면 합칠 머리가 들여온 일지를 뺀다(같은 파일의 번호 대조는 `MERGE_HEAD`를 이미 본다)
**승인:** 자체 승인 2026-11-15, 1회차(고침), 일지 2026-11-14-2152-admin-login-design.md. ADR 불필요

retro 2단계와 5단계가 이 출력을 일지의 경로로 쓴다. 이 세션은 출력이 다른 기능의 일지인 것을 알아보고 자기 일지에 적었다.
