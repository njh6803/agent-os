# rename-review-bot-note-section: 리뷰 봇 워크플로의 절 이름 "릴리스 노트 조각"을 "릴리스 노트 원고"로 바꾼다

**What to build:** 앞 티켓 `.scratch/harness/issues/rename-workflow-terms.md`가 용어집 이름 "노트 조각"을 "릴리스 노트 원고"로 바꾸며 `docs/constitution/operations.md`의 절 제목도 `## 릴리스 노트 원고`로 바꿨다. 리뷰 봇 워크플로 `.github/workflows/claude-code-review.yml` 67행은 그 절을 아직 옛 이름 "릴리스 노트 조각"으로 가리킨다. 그 한 곳을 새 이름으로 바꾼다.

앞 티켓이 이 줄을 함께 바꾸지 않은 까닭은 그 티켓의 "바꾸지 않는 것" 마지막 항목에 있다. 이 파일을 바꾼 PR은 리뷰 봇이 리뷰하지 않고 건너뛴다(`docs/constitution/operations.md` 100행). 그리고 같은 워크플로의 가드 스텝(리뷰 봇이 코멘트를 남겼는지 세는 마지막 단계, `Fail when Claude left no comment`)은 그 PR이 일지·대기열·티켓·하네스 탐침(`.scratch/harness/probes/`) 밖의 파일을 함께 실으면 실패한다(그 스텝의 103~113행, PR 서식의 `.github/` 줄). 그래서 이 파일은 다른 파일과 함께 싣지 않는다(`operations.md` 48행). 이 PR에는 그 워크플로 파일과 이 티켓, 일지, 대기열 항목만 싣는다.

리뷰 봇은 그 절을 절 이름이 아니라 "느낌표의 기준"이라는 글자로 찾는다(같은 줄의 Grep 안내). 그래서 이름을 바꿔도 봇이 읽는 문단은 같다. 다만 그 글자로 찾으면 `operations.md`의 두 줄이 걸린다. 46행은 그 문단이고, 94행은 그 문단을 가리키는 리뷰 파이프라인 3이다. 프롬프트는 걸리는 줄을 하나로 여기고 "그 줄이 길어 Grep은 내용을 생략하고 번호만 준다"고 적었지만, 이 PC의 Grep 도구는 46행을 내용까지 보이고 94행만 생략했다(2026-11-18에 손으로 봤다. CI의 Claude Code 판으로는 보지 않았다). 이 둘은 이름을 바꾸기 전에도 같았고, 이 티켓은 그 안내를 고치지 않는다. 고칠지는 이 단계 일지의 "다음"에 넘긴다.

같은 67행의 "판을 올릴 때"는 판 계열 이름을 바꿀 때 다시 이 파일을 따로 고친다. 대기열 항목 `glossary-plain-names-left`의 "`rename-workflow-terms` 티켓의 셀프 리뷰가 잡아 더 적는 하나다" 단락이 이미 그렇게 적고 있어, 이 티켓은 그 낱말을 그대로 둔다.

**병합 뒤의 빈 기간.** 이 PR을 dev에 병합하면 dev와 main의 이 워크플로가 달라지고, 다음 출시 PR이 main에 올릴 때까지 그 상태가 이어진다. 그동안 main에서 딴 핫픽스 PR도 리뷰 봇이 건너뛸 것으로 본다(`operations.md` 100행의 어림이고 재 보지 않았다). 그 핫픽스 PR은 이 워크플로를 바꾸지 않았으니 가드 스텝이 코멘트를 세고, 0개라 claude-review가 빨개질 것이다(가드 스텝의 코드를 읽은 어림이다). 이 PR은 그 빈 기간을 없애지 않는다. 기준 커밋 `b74a8adf2`에서 origin/main과 dev의 이 파일은 같고, dev에만 있는 커밋 가운데 이 파일을 바꾼 것은 없다(`git diff --stat origin/main b74a8adf2`와 `git log origin/main..b74a8adf2`로 손으로 봤다). 그래서 지금은 빈 기간이 없고, 이 PR의 병합이 그것을 연다.

**대기열:** glossary-plain-names-left

**Status:** done

## 수용 기준

- [x] `.github/workflows/claude-code-review.yml` 67행이 `docs/constitution/operations.md`의 절을 "릴리스 노트 원고"로 가리킨다. 그 밖의 글자는 그대로다
- [x] 기록 밖의 살아 있는 문서와 코드에 "노트 조각"이 용어집의 뜻으로 남지 않았다. 남은 것은 이름을 바꿨다는 기록과 바꾸기 전의 글을 따온 자리뿐이다(앞 티켓의 "바꾸지 않는 것"과 그 티켓 수용 기준 둘째 줄이 든 자리)
- [x] 이 PR에 실린 파일이 워크플로 파일, 이 티켓, 일지, 대기열 항목뿐이다
- [x] 대기열 항목 `glossary-plain-names-left`의 "반영한 것"에 이 한 줄이 있고 남은 목록에서 빠졌다. 상태는 열림이다
- [x] 검증 명령이 모두 초록이다
