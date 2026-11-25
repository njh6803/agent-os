# 접속 확인의 기능 단락이 보이는 탭에서만 도는 것을 말하게 고친다

PR #634(`feature/05-admin-e2e-scene-for-connection-check`)가 병합되면서 접속 확인 기능의 끝 줄과 기능 단락이 dev에 올랐다. 그 PR의 CodeRabbit 둘째 회차가 단락의 "화면이 열려 있는 동안 30초마다"가 명세와 어긋난다고 짚었고, 맞는 지적이었지만 푸시가 하나 더 필요해 그 PR에서는 보류했다(#issuecomment-7139012640). 단락은 출시 때 릴리스 노트에 글자 그대로 실리므로, 출시 PR을 열기 전에 이 문구를 먼저 고치기로 했다.

> 질문: 출시 PR 전에 기능 단락의 문구를 먼저 고칠까요?
>
> 사용자: 문구부터 고쳐요

## 한 일

- 새 브랜치 `docs/connection-check-feature-paragraph-visible-tab`을 `origin/dev`(`b4ee2ee`)에서 땄다. 병합된 `feature/05-…` 위에서 따지 않았다.
- `docs/release-notes/features/connection-check.md`의 "화면이 열려 있는 동안 30초마다 스스로 확인하고"를 "화면이 보이는 동안 30초마다 스스로 확인하고(다른 탭을 보거나 창을 내린 동안에는 멈췄다가 돌아오면 바로 한 번 확인한다)"로 고쳤다. 나머지 문장(stdio 서버의 손으로 하는 확인, 꺼 둔 플러그인, 배포 안내의 '문제 해결' 절)은 그대로다.
- 이 파일은 `tools/check_ticket.py`의 면제 모양에 없어 harness 티켓 `.scratch/harness/issues/connection-check-feature-paragraph-visible-tab.md`를 함께 썼다(`docs/` 브랜치는 harness 티켓 하나가 있으면 지난다).

## 근거

- 명세 `.scratch/connection-check/spec.md`의 "간격과 보이지 않는 탭" 둘째 항목은 다른 탭을 보거나 창을 내려 화면이 보이지 않는 동안 확인을 보내지 않고, 돌아오면 바로 한 번 확인한 뒤 다시 30초마다 확인한다고 적는다. 읽었다.
- 단락은 한 줄 297자이고 줄 바꿈이 없다(`uv run python tools/check_notes.py`가 출력 없이 끝났다. 글자 수는 파이썬 `len`으로 셌다).
- 구현이 명세대로 보이지 않는 탭에서 멈추는지는 이 세션이 보지 않았다. 셀프 리뷰의 명세 축 서브에이전트가 `web/apps/admin/hooks/queries/connection/index.ts`에서 `refreshWhenHidden: false`와 `visibilitychange`가 `visible`일 때 바로 `mutate`하는 줄을 읽었다고 보고했다(읽은 것이고 화면에서 돌려 본 것은 아니다).

## 셀프 리뷰(`/code-review`, base `b4ee2ee`, 파일 5개: 수정 2·미추적 3, 커밋 0)

- 명세 축: Critical·Major 0. Minor 둘. (1) 단락의 괄호가 명세의 "창을 내려"보다 좁았다. (2) 명세·계획·ADR 0067에 "열려 있는 동안"이 남았으나 명세가 보이지 않는 탭을 따로 정하므로 모순이 아니다.
- 표준 축: 확정 위반 1, 판단 2. 확정은 harness 티켓에 `**대기열:**` 줄이 없던 것(`docs/agents/issue-tracker.md` 13행에서 원문을 확인했다). 판단은 티켓의 셋째 체크박스가 커밋 전에 이미 체크된 것과, 대기열 새 항목의 "처음이다"가 닫힌 주장인 것이다.
- 고친 것: 티켓에 `**대기열:** 없음`을 더했다. 단락 괄호를 "다른 탭을 보거나 창을 내린 동안에는"으로 넓혔다. 티켓 셋째 칸에 "커밋 때 돈다, 결과는 PR 본문에 적는다"를 적었다. 대기열 항목의 "처음이다"에 열린 항목 기준임을 달았다.
- 남긴 것: 명세·계획·ADR의 "열려 있는 동안"은 모순이 아니고 이 티켓의 요구도 아니라 그대로 둔다.

## 인계(셀프 리뷰 직전)

이 세션의 제목은 `feature/05-admin-e2e-scene-for-connection-check`였고(PR #634를 병합한 세션이다), 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전`에 왔다. 이 세션이 한 것: 새 브랜치를 `origin/dev`(`b4ee2ee`)에서 딴 것, 기능 단락 한 문장 수정, harness 티켓 작성(`Status: done`), 이 일지, 회고(`## 회고`), 대기열 항목 하나 신설과 하나 회차 더하기. 커밋하지 않았고 푸시하지 않았다. 셀프 리뷰는 `code-review` 스킬을 불러 지시문만 읽었고 서브에이전트 둘은 띄우지 않았다. 새 세션이 `/code-review`의 4단계부터 하고 커밋·푸시·PR·봇 회차·병합을 잇는다. 병합 뒤 결정표의 출시 PR 줄이 맞으면 출시 PR을 연다(사용자가 출시 전에 문구를 고치기를 골랐다).

open-session을 부른다 2026-11-25T03:02Z

주 체크아웃 미갱신: 루트는 dev(`2f474ec`)다. 이 워크트리가 지난 PR #634를 병합했으므로 `tidy-checkouts`가 아직 돌지 않았다.

## 회고

후보 둘, 승인 둘(대기열에 둠), 기각 0, 넘김 0.

- 기능 단락을 기능 계획의 값(30초)과 배포 안내의 소절 이름에만 대고 명세의 "보이지 않는 탭에서 멈춘다"를 대지 않아 CodeRabbit이 짚은 사건. 판정은 승인이다. 사건은 위 PR #634이고, 층은 지침이다(글이 명세와 맞는지는 낱말로 가를 수 없어 검사로 옮기지 못한다). 되돌림은 PR 하나다. 같은 일을 다룬 항목을 `tools/queue_open_rows.py --search 기능.단락 --search release-notes/features`로 찾았으나 없어 새 항목 `feature-paragraph-checked-against-plan-not-spec`을 1회차로 썼다. 더하는 것이라 다섯 번째 전에는 반영하지 않는다.
- 일지 한 파일만 바꾼 커밋의 pre-commit이 둘째 시도에서 pytest 1171초가 걸리고 앞 두 시도가 시간 제한 시험에 막힌 사건(2026-11-24-2140 일지 178행). 판정은 승인이고 열린 `docs-only-commit-precommit-slow-again`에 22회차로 더했다. 막대별 시간과 나란히 돈 세션의 부하는 그 일지가 적지 않았다. 이번 문구 고침 커밋의 pre-commit 시간은 커밋 뒤 이 항목에 더할지 본다.

## 다음

- 이 PR이 병합되면 출시 PR(dev→main)을 연다. `next-session`의 결정표 둘째 줄의 조건(끝 줄 커밋이 dev에만 있고, 열린 출시 PR이 없고, dev가 main을 품었다)은 PR #634 병합 직후 이미 맞았다. main의 push CI가 초록인지는 열기 직전에 다시 본다.
