# 부록 C. 플랜·요금·플랫폼 사실과 확인일

바뀌는 사실이다. 날짜가 없는 값은 추정으로 읽고, 다른 프로젝트에서 쓸 때 공급자 페이지에서 다시 확인해 날짜를 갱신한다.

| 사실 | 확인일 | 어디서 |
|---|---|---|
| GitHub Actions 무료 분량은 계정 단위 월 2,000분. 다른 비공개 저장소가 써 버리면 잡이 시작조차 안 된다 | 2026-09-20 | agent-os PR #10, ADR 0005 |
| 무료 플랜 비공개 저장소는 보호 브랜치·룰셋이 403 | 2026-09-20 | agent-os, ADR 0005 |
| CodeRabbit CLI 상한은 개발자당 시간당 3회 롤링 윈도. `--usage`는 시간당 잔량을 보여주지 않는다 | 2026-09-21 | 공식 요금제 문서 rate limits 표 |
| CodeRabbit OSS PR 리뷰는 별 수에 따라 시간당 1~10회. 별 10개 미만이면 자동 리뷰 없음, `@coderabbitai review`로 부른다 | 2026-09-21·22 | agent-os PR #12·#43 |
| CodeRabbit CLI 좌석 배정에는 활성 유료 구독이 필요하다. 무료면 `Seat: not assigned`로 연결 단계에서 끝난다 | 2026-09-23 | 공식 문서 management/seat-assignment, agent-os 실측 |
| Claude Code Review 액션은 자기 워크플로 파일이 기본 브랜치와 다르면 건너뛴다. 다른 워크플로 파일은 무관 | 2026-09-20, 정정 2026-09-28 | agent-os PR #3·#6(건너뜀)·#43(돌았다) |
| Claude Code 스킬 우선순위는 enterprise > personal > project | 2026-09-19 | 공식 문서 |
| Claude Code의 `@` 임포트는 CLAUDE.md 어디에서든 임포트다. 코드 스팬과 펜스는 제외 | 2026-09-28 | 공식 문서 memory 페이지 |
| 앱 딥링크가 첫 줄의 슬래시를 전각으로 바꾼다. 딥링크 URL은 8000자 안 | 2026-09-24 | agent-os PR #50·#65 |
