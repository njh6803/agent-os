# git-add-all-staged-leftover-judge-tree: 검증이 도중에 죽으며 남긴 임시 폴더 `web/judge-<여섯 글자>/`를 `git add -A`가 스테이지에 올려, 다음 커밋의 pre-commit이 12분 뒤 커밋 검사에서 막혔다

**상태:** 열림
**어디로:** 대상 미정, 회차 감시. 후보는 둘이다. 첫째는 `.gitignore`에 `web/judge-*/`를 더하는 것이다. 그 폴더는 린트 판정자 시험이 쓰는 임시 폴더라, 더하기 전에 `web/eslint.config.mjs`가 `.gitignore`를 무시 목록으로 읽는지를 먼저 본다(읽는다면 그 시험이 헛돌 수 있다. 이 회차의 세션은 확인하지 않았다). 둘째는 `git add -A`와 `git add .`를 칠 때 미추적 파일 목록을 알리는 Bash 훅이다. 닫힌 0379가 둔 청소(`web/package.json`의 `clean:judge-trees`)는 다음 검증의 첫 단계에야 돌아, 그 사이의 `git add -A`와 `git status`에는 폴더가 그대로 섞인다
**승인:** 자체 승인 2026-11-21, 1회차, 일지 2026-11-20-1928-diag-bundle-design.md. ADR 불필요

세션이 스테이지에 올리기 전에 `git status`를 보지 않고 `git add -A`를 쳤다. 폴더의 파일 110개가 함께 올라갔고, 다음 검증의 청소가 폴더를 지워 스테이지에는 있는데 파일은 없는 상태가 됐다. 커밋 검사가 "면제 모양 밖의 바뀐 파일 110개"로 막았다. 손상은 없고 한 바퀴(722.66초)를 다시 쳤다. 그 뒤로 세션은 경로를 지정해 스테이지에 올렸다.

폴더가 남은 까닭은 검증이 메모리 부족으로 죽은 것이다(`run-checks-out-of-memory-with-parallel-sessions`).
