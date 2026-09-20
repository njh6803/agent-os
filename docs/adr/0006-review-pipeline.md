---
status: accepted
date: 2026-09-20
---

# 리뷰는 두 단계 세 축이고 PR 봇은 하나다

리뷰 파이프라인은 세 축이다. 표준·명세(커밋 전 `/code-review`), 보안·버그·성능(PR 직전 CodeRabbit CLI, `coderabbit-review` 서브에이전트), 유지보수성·경계(PR에서 Claude Code Review). 판단 기준과 심각도의 원천은 `CODING_STANDARDS.md`, 누가 언제 보는지는 `docs/constitution/operations.md`의 "리뷰 파이프라인"이다. 선행 저장소 `ai-agent-platform`의 2단계 파이프라인을 옮기되 이 계정과 플랜에서 실측한 대로 고쳤다.

## 개정 이력

- 2.2.0 (2026-09-20 오전): 선행 저장소대로 PR 봇 둘. CodeRabbit이 보안·성능, Claude가 유지보수성·경계.
- 2.2.1 (같은 날 오후): CodeRabbit PR 리뷰를 끄고 CLI만 남겼다. 사용자 결정. 근거는 PR #2 실측. 비공개 저장소의 Free 플랜은 시트가 없어 Walkthrough 요약만 남기고 체크는 `pass`였고, 둘째 푸시는 "Review rate limited"로도 `pass`였다. 초록만 늘고 리뷰는 없는 봇은 "코멘트 0개인 초록은 리뷰 없음" 규약을 흐린다. 무료 CLI는 주기당 3회라 커밋마다가 아니라 PR마다 한 번이다.
- 같은 날 저녁: Claude Code Review를 공식 플러그인 대신 직접 프롬프트로 바꾸고 "코멘트 0개면 실패" 스텝을 두는 PR #10을 열었다(회고 후보 1. 병합은 Actions 결제 문제가 풀린 뒤). 플러그인은 서브에이전트를 백그라운드로 띄우고 턴을 끝내 짧은 실행 다섯에서 코멘트 없이 초록이 됐다. 단일 에이전트가 요약 코멘트 하나를 `gh pr comment`로 남기는 것이 완료 조건이다.

## 버린 대안

CodeRabbit 유료나 공개 전환(PR 봇 둘을 되살린다. 플랜 결정은 사용자 몫으로 남겨 두었다). Claude 플러그인 유지 + 검사 스텝만(문서 PR마다 빨강 소음). 검사 없이 플러그인만(초록 착시 그대로).

## Consequences

- 봇의 초록은 리뷰가 아니다. 병합 전에 코멘트 수를 보고, 코멘트 없는 초록은 `tools/gh_run_summary.py`로 실행 내용을 본다. 워크플로 파일을 바꾼 PR은 액션이 건너뛰므로 별도 PR로 먼저 병합한다.
- 셀프 리뷰는 문서만 바뀐 diff에서도 돈다. 첫날 여덟 번에 Major 다섯을 잡았다. 비용은 소스 파일이 없는 diff의 Standards 축을 sonnet으로 돌려 줄인다(code-review 스킬 사본 4단계).
- 스킬 사본 둘(retro, code-review)이 원본과 다르다. `npx skills update -p`가 덮어쓰면 사본 머리 주석으로 알아챈다.
- 다시 열 조건: 공개 전환이나 유료 플랜이면 CodeRabbit PR 리뷰를 켜고 역할 분담을 operations.md에 다시 적는다. 2026-09-21 공개 전환으로 조건이 충족됐다. 켤지는 사용자 결정 대기.
