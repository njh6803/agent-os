# 2026-11-18 용어집의 작업 규약 쪽 이름 셋을 쉬운 이름으로 바꾼다

앞 일지(`2026-11-18-1422-rename-small-run-terms.md`)의 "다음"을 잇는다. 용어집의 낯선 이름을 쉬운 이름으로 바꾸는 일의 셋째 PR이다. 바꿀 이름과 묶는 법은 일지 2026-11-18-1036의 선택 화면들에서 사용자가 정했다(그 일지의 "정해진 이름 바꾸기"). 이 단계에서 사용자에게 새로 물은 것은 아래 "사용자에게 물은 것" 하나다.

## 앞 PR의 병합 (PR 605)

둘째 푸시(`a95c599e7`)의 결과는 PR 605의 마지막 코멘트에 적었다(`next-session` `merge.md` 2의 "뒤로 넘긴 일"). `tools/wait_ci.py 605`가 "끝: 모두 통과. CodeRabbit: Review rate limited"로 끝났고, claude-review는 둘째 회차에도 "지적 없음"이었다. `gh pr merge 605 --squash --match-head-commit`으로 병합했고 dev의 병합 커밋은 `f13190072`다. 원격 브랜치는 병합과 함께 지워졌다(`git ls-remote --exit-code`가 2). 주 체크아웃 미갱신: 루트는 dev.

다음 작업 결정표(`next-session` `SKILL.md`)는 위에서부터 봤다. main의 커밋은 모두 dev에 들어 있고, dev에만 있는 커밋 가운데 기능을 끝낸 것이 없어 첫 두 줄(운영에서 개발로 합치기, 출시 PR)은 해당하지 않았다. 고른 줄은 "하네스·문서만 고친 PR이었고 같은 주제가 남았다"이고 이 세션에서 잇는다. 낸 지시문은 이렇다.

```
다음 작업: 받는 세션이 쓸 .scratch/harness/issues/rename-workflow-and-screen-terms.md. 용어집의 작업 규약과 화면 쪽 이름 다섯(노트 조각, 되돌려 합치기, 루트 브랜치, 거꾸로 동기화, 원색 토큰)을 사용자가 고른 쉬운 이름으로 바꾼다
다음 단계: 구현
어디서: 이 세션. 같은 주제가 남았고 컨텍스트가 자산이다
시작 프롬프트: 대기열 glossary-plain-names-left의 작업 규약과 화면 이름 다섯을 티켓 .scratch/harness/issues/rename-workflow-and-screen-terms.md로 쓰고 한다
브랜치: chore/rename-workflow-and-screen-terms
모델: 없음
읽을 것: docs/journal/2026-11-18-1422-rename-small-run-terms.md의 "다음", docs/agents/issue-tracker.md
이어받을 상태: PR 605 둘째 회차의 결과와, 다음 회고가 셀 두 사건(문서만 바꾼 둘째 커밋의 pre-commit 929초, 둘째 커밋 직후의 인계 계기 240,904 토큰)은 PR 605의 마지막 코멘트에 있다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 나란히 도는 docs/postgres-foundation-spec 세션이 용어집(CONTEXT.md)을 고칠 수 있다
이번 요청 범위: PR과 병합까지
```

## 다섯을 둘로 나눈 까닭

지시문은 다섯을 한 PR에 묶었다. 쓰인 곳을 세어 보니 앞의 PR들과 달리 하네스에 깊이 얽혀 있었다. 스킬의 절 제목(`merge.md`의 "되돌려 합치기"), 결정표의 칸 값, 리뷰 봇의 프롬프트(`.github/workflows/claude-code-review.yml`이 "릴리스 노트 조각" 절을 이름으로 가리킨다), 노트 검사의 오류 문구, 카나리아 명세의 물음과 기대 문구, 스킬의 자리 표시 `<루트 브랜치>`가 그 예다. 다섯이 고치는 스킬과 규칙을 원천으로 든 카나리아 명세는 76개였다(스크래치의 `canary_by_name.py`로 셌다. 작업 규약 셋이 60개, 화면 둘이 16개).

그래서 둘로 나눴다. 이 PR은 작업 규약의 셋(노트 조각, 되돌려 합치기, 루트 브랜치)이고, 화면 쪽 둘(거꾸로 동기화, 원색 토큰)은 다음 PR이다. 원색 토큰의 풀이는 디자인 시스템 아티팩트에 올라가는 원본(`web/tools/sync-design-system/artifact-source/README.md`, `foundations/colors/index.html`)에도 있어, 그 PR은 병합 뒤 `sync-design-system` 올리기까지 해야 끝난다. 묶는 법("작은 이름은 주제가 가까운 것끼리 PR 하나")을 따르면서 올리기가 따르는 묶음을 따로 둔 것이다. 이것은 이 세션의 판단이고 사용자가 고른 것은 아니다. 로컬 브랜치 이름을 `chore/rename-workflow-terms`로, 티켓 이름을 `rename-workflow-terms`로 바꿨다(아직 푸시하지 않은 브랜치다).

## 사용자에게 물은 것

카나리아를 얼마나 다시 돌릴지 물었다. 이 PR이 고친 스킬 파일 아홉을 원천으로 든 명세는 60개다. 사전 확인(`uv run python tools/canary.py --preflight <명세 60개>`)에서 실험군 쪽 카나리아가 원천에 없다고 나온 명세는 셋(`next_session_fable_cut_row`, `next_session_model_line`, `tidy_skill_cwd_owner`)이었고, 셋 다 `origin/dev`의 원천에도 그 문구가 없었다(`git show origin/dev:<원천>`을 grep해 0). 대조군 쪽은 대부분 막혔다. 대조군이 주 체크아웃이거나 지금은 없는 임시 체크아웃이라, 다시 돌리려면 명세마다 바뀌기 전 커밋을 `--control-commit`으로 주어야 한다.

> 질문: 이번 PR에서 고친 스킬 파일 9개를 원천으로 든 카나리아 명세는 60개입니다. 9개는 이름이 바뀐 문장을 직접 묻고, 48개는 사전 확인(세션을 띄우지 않고 묻는 문구가 원천에 남았는지만 보는 검사)에서 문구가 그대로였으며, 남은 3개는 이번 변경과 상관없이 dev에서 이미 원천과 어긋나 있었습니다. 카나리아를 얼마나 다시 돌릴까요?
>
> 사용자: 10개만 돌린다 (Recommended). "이름이 바뀐 문장을 묻는 명세 9개와, 그 9개가 닿지 않는 upload.md를 확인할 명세 1개만 새 세션으로 돌립니다(Sonnet 세션 40번, 걸리는 시간은 20분 안팎으로 어림). 고친 스킬 파일 9개가 모두 새 세션에서 한 번 이상 확인됩니다. 나머지 50개는 결과 줄을 고치지 않습니다. 앞 PR(603)이 원천 명세를 모두 돌린 것과 다르게 가는 것이라, 그 차이를 일지와 PR에 적습니다. 어긋난 3개는 따로 나중 할 일로 남깁니다."

고르지 않은 선택지는 "60개를 모두 돌린다"였다. 설명은 "PR 603처럼 원천 명세를 모두 새 세션으로 돌립니다(Sonnet 세션 240번, 걸리는 시간은 1시간 반에서 2시간으로 어림). 명세마다 바뀌기 전 커밋을 찾아 대조군으로 주어야 합니다. dev에서 이미 어긋난 3개(next_session_fable_cut_row, next_session_model_line, tidy_skill_cwd_owner)도 이 PR에서 먼저 고쳐야 통과합니다."였다.

## 카나리아

고른 열을 스크래치의 `run_canaries_workflow.py`로 돌렸다(일꾼 셋, claude 2.1.325). 명세마다 `uv run python tools/canary.py --control-commit <바뀌기 전 커밋> <명세> <출력 폴더>`를 부르고 러너의 집계 줄만 측정으로 센다. 먼저 `--preflight`로 열 모두 통과한 것을 본 뒤 띄웠다.

열 모두 "통과 4 · 실패 0"이고 종료 코드 0이었다. `dev_base_open_session`의 "없음" 섞임 1은 실험군 2/3이 "없음"으로 시작했다가 그 답이 틀렸다고 스스로 고치고 카나리아 구절을 옮긴 회차다(로그를 읽었다). 대조군은 열 모두 카나리아를 옮기지 않았다(러너의 판정이고, 답을 읽은 것은 `dev_base_open_session` 하나다). 결과 줄은 스크래치의 `stamp_results_workflow.py`로 열 명세의 머리에 더했다. 새 `# 최신 결과:` 줄을 넣고 옛 줄의 머리를 `# 그 전 결과:`로 바꾸는 PR 603의 꼴이다. `pr_merge_skill_kinds`는 옛 줄의 머리가 `# 결과:`여서 그것을 `# 그 전 결과:`로 바꿨다. 나머지 50개의 결과 줄은 고치지 않았다.

## 셀프 리뷰

`/code-review`의 두 축을 기준 커밋 `f13190072`(origin/dev의 merge-base) 위의 작업 트리 변경에 돌렸다. 범위는 고친 추적 파일 41개, 미추적 둘(티켓, 일지), 커밋 0개다. 표준 축은 Sonnet·high, 명세 축은 이 세션의 모델이다.

### 표준 축의 보고

- Major 1: 노트 조각을 줄여 쓴 "조각"이 `tools/check_notes.py`에 절반만 바뀌었다. 독스트링 49~51행, 함수 독스트링 231·237·282·403행, 사람에게 보이는 오류 문구 둘(288행 "조각은 비어 있지 않다.", 291행 "조각에는 없다.")이 남았다. 티켓이 "독스트링·주석 셋과 오류 문구"로 세어 닫은 주장의 반례다.
- Minor 2: 워크플로 주석 셋에 "조각"이 남았다(`pr-title.yml` 2행, `ci.yml` 405행, `release.yml` 211행).
- Minor 3: 티켓이 아직 in-progress이고 수용 기준이 모두 비었다.
- Minor 4: 일지에 "다음" 절이 없다. 티켓은 어긋난 카나리아 셋을 거기 남긴다고 했다.
- Nit 5: `tests/tools/test_release.py` 571·581행의 커밋 메시지와 `test_check_notes.py` 537행 주석에 "조각"이 남았다.
- Nit 6: `directive.md` 30행의 "주 체크아웃이 그 체크아웃이 따르는 브랜치"가 겹쳐 읽기 거칠다.
- Nit 7: ADR 0066 본문 30행이 이제 없는 절 이름을 가리킨다. 이력이 풀어 주고 본문은 고치지 않는 규칙이라 허용 범위다.
- 문제 없다고 확인한 것: 세 옛 이름의 잔존은 모두 허용 목록 안이고, 조사 오류는 grep 0건, ADR 이력의 모양과 인용 셋, 절 제목을 가리키는 글, "되돌려"를 뗀 문장, `tidy-checkouts` 정의 문단.
- 검증 못 한 것: 카나리아 명세의 수(76·60·16)는 세션 스크래치 스크립트가 센 값이라 저장소에서 다시 세지 못했다.

### 명세 축의 보고

- Major 1: `dev_base_implement.toml` 8행은 지난 결과 줄에 이어 적은 줄인데, 2026-11-12에 모델이 옮긴 구절의 옛 이름을 바꿨다. 기록을 고친 것이다.
- Major 2: 옛 이름이 남았다. `tools/check_ticket.py` 105~106행의 "되돌려"와 "합치기"가 줄바꿈으로 갈려 grep에 걸리지 않았다. `check_notes.py`의 "조각"(표준 축 Major 1과 같다). 앞 티켓의 수용 기준에 있던 "줄바꿈으로 갈라진 꼴로도 훑었다"가 이 티켓에서 빠졌다.
- Major 3: 리뷰 봇 워크플로를 같은 PR에서 고친다. 그 파일의 변경은 별도 PR로 먼저 병합한다는 규약을 티켓이 언급하지 않는다.
- Minor 4: "main을 dev에"가 없는 자리에서도 "되돌려"를 떼어 방향이 사라졌다(`next-session` `SKILL.md` 49행, `merge.md` 37·118행, 프로브 README와 `backmerge_diff_check.sh` 68행의 장면 이름 "합친 뒤").
- Minor 5: 새 이름을 끼운 문장에서 말이 겹친다(`tidy-checkouts` 8행 "주 체크아웃(…)이 주 체크아웃이 따르는 브랜치의", `tidy-checkouts` 28행과 `open-session` 18행 "루트가 주 체크아웃이 따르는 브랜치(…)").
- Minor 6: 티켓이 센 "아홉"의 반례. `dev_base_next_session_backmerge_row.toml` 1~2행 머리 설명에 줄바꿈으로 갈린 "되돌려 합친다"가, `implement_ticket_status.toml` 10행 머리 설명에 "upgrade 조각"이 남았다.
- Minor 7: ADR 0066 이력이 본문에서 줄여 쓴 "조각"(18·30행)을 적지 않았다.
- Minor 8: "조각"이 워크플로 주석 셋과 `test_check_notes.py` 537행 주석에 남았다(표준 축 Minor 2·Nit 5와 같다).
- Nit 9: 돌린 열 가운데 여섯은 기대 문구가 `f13190072` 판에도 있어, 통과가 이 PR의 바뀐 문장이 실렸다는 것을 가르지 못한다. "9개가 모두 새 세션에서 확인"은 파일이 실린 데까지만 맞다.
- Nit 10: `check_ticket.py` 192행의 "main→dev 운영에서 개발로 합치기"는 방향을 두 번 말한다.
- 갈래 밟기: 4·5를 고치면 카나리아가 묻는 문장에 닿아(`backmerge_row`, `tidy_root_branch`, `open_session`) 사전 확인과 실행을 다시 한다.
- 맞다고 확인한 것: 용어집 세 풀이의 사실, 피할 말 줄의 꼴, 원천을 센 60개, ADR 0043·0056의 포인터 둘씩과 인용, 대기열 항목, 결과 줄과 일지, 사용자 답의 인용.

한 줄로 줄이면 표준 축은 지적 일곱(가장 무거운 것은 `check_notes.py`에 "조각"이 절반만 바뀐 Major), 명세 축은 지적 열(가장 무거운 것은 리뷰 봇 워크플로를 같은 PR에서 고친 Major)이다.

### 고친 것

지적마다 근거를 열어 본 뒤 고쳤다. 고치며 새로 쓴 사실 문장은 이 절 끝에 원문으로 옮긴다.

- 표준 Major 1, 명세 Major 2의 둘째. `tools/check_notes.py`의 모듈 독스트링(49~51행), 함수 독스트링(231·237·282·403행), 오류 문구 둘(288·291행)의 "조각"을 "원고"로 바꿨다. 티켓의 "조각" 항목은 고칠 곳을 세어 닫지 않고, 그 뜻으로 쓰인 곳은 모두 바꾼다는 조항 뒤에 예시를 두는 꼴로 고쳤다(원문 2). 세어 닫은 목록에는 새 반례가 이어 나온다(`code-review` 6의 1).
- 명세 Major 2의 첫째와 Minor 6의 첫째. 줄바꿈으로 갈린 옛 이름 둘(`tools/check_ticket.py` 105~106행, `dev_base_next_session_backmerge_row.toml` 1~2행 머리 설명)을 바꿨다(원문 9). 옛 이름 셋을 줄 끝과 다음 줄 머리의 공백과 주석 기호를 걷고 이어 붙인 글에서 찾는 스크래치 스크립트(`find_old_names_wrapped.py`)로 추적 파일을 다시 훑어, 줄바꿈에 걸친 일치가 0인 것을 봤다. 티켓의 수용 기준 2에 "줄바꿈으로 갈린 꼴로도 훑었다"를 되살렸다.
- 명세 Major 1. `dev_base_implement.toml`의 지난 결과 줄에 이어 적은 줄(모델이 옮긴 구절 `루트 브랜치(main이나 dev. 정하는 법은 tidy-checkouts)`)을 기준 커밋의 글자로 되돌렸다. 그 줄은 그날 모델이 옮긴 글을 적은 기록이다.
- 명세 Major 3. `.github/workflows/claude-code-review.yml`을 기준 커밋과 같게 되돌렸다(`git diff --stat`이 빈다). 그 파일을 바꾼 PR은 리뷰 봇이 건너뛰고, 가드 스텝이 다른 파일과 함께 실은 PR을 실패로 만든다(`docs/constitution/operations.md` 48행, 리뷰 파이프라인 3). 그 한 줄은 받는 쪽인 대기열 항목의 남은 목록에 적고(원문 5, 6), 티켓의 "바꾸지 않는 것"에 여섯째로 적었다(원문 1). 절 제목을 가리키는 글의 목록에서도 리뷰 봇 프롬프트를 뺐다.
- 표준 Minor 2, 명세 Minor 8. 워크플로 주석 셋(`ci.yml` 405행, `pr-title.yml` 2행, `release.yml` 211행)의 "조각"을 "원고"로 바꿨다.
- 표준 Nit 5. `tests/tools/test_release.py` 571·581행의 커밋 제목 둘과 `tests/tools/test_check_notes.py` 537행 주석의 "조각"을 "원고"로 바꿨다. 커밋 제목 둘은 단언에 쓰이지 않는다(그 시험의 단언을 읽었다).
- 표준 Nit 6. `directive.md` 30행의 "주 체크아웃이 그 체크아웃이 따르는 브랜치(…)가 아니거나"를 "주 체크아웃이 자기가 따르는 브랜치(…)에 있지 않거나"로 고쳤다(원문 7). 티켓의 "함께 고치는 것"도 같이 고쳤다.
- 명세 Minor 4. "main을 dev에"가 앞에 없는 자리에서 "되돌려"를 뗀 문장에 방향을 덧붙였다. `next-session` `SKILL.md` 49행 두 곳(원문 8), `merge.md` 37·118행(원문 10, 11), 프로브 README 194행과 `backmerge_diff_check.sh` 2·68행(원문 12, 13)이다. `merge.md` 118행의 ADR 0043 항목 이름 인용 "되돌려 합치기"는 그대로 두었다. 고친 뒤 `sh .scratch/harness/probes/backmerge_diff_check.sh`가 `{"measured":7,"not_measured":0,"wrong":0,…}`로 끝났고, 장면 이름 "main을 dev에 합친 뒤"가 찍혔다.
- 명세 Minor 5의 첫째. `tidy-checkouts` 8행의 "주 체크아웃(…)이 주 체크아웃이 따르는 브랜치의"를 "주 체크아웃(…)이 자기가 따르는 브랜치의"로 고쳤다(원문 14).
- 명세 Minor 7. ADR 0066 이력에 본문이 줄여 쓴 "조각"도 원고로 읽는다는 문장을 더했다(원문 4). 인용한 세 구절은 모두 결정 절(12~35행)의 18·30행에 글자 그대로 있다.
- 명세 Nit 10. `check_ticket.py` 192행 주석이 방향을 두 번 말하지 않게 "(dev→main 출시 PR, 운영에서 개발로 합치기)"로 고쳤다(원문 9).
- 일지. 처음에 적은 "대조군은 열 모두 '없음'이거나 옛 문장을 옮겼다"는 답을 읽지 않고 쓴 주장이라, "러너의 판정이고, 답을 읽은 것은 `dev_base_open_session` 하나다"로 고쳤다(원문 15).
- 위 반영을 다시 훑다 잡은 수용 기준 2의 반례. `dev_base_tidy_root_branch` 머리 설명이 옛 굵은 머리 "루트 브랜치"를 밝힌 한 곳이 그 닫힌 목록에 없었다. 옛 결과 줄을 읽는 데 필요한 말이라 두고, 수용 기준을 "이름을 바꿨다는 기록과 바꾸기 전의 글을 따온 자리"라는 조항과 예시로 고쳤다(원문 3).

고치며 새로 쓴 사실 문장의 원문이다. PR 직전 리뷰와 PR 봇이 겨냥해 볼 문장들이다.

```
1. (티켓, 바꾸지 않는 것) 리뷰 봇 워크플로 `.github/workflows/claude-code-review.yml` 67행의 절 이름 "릴리스 노트 조각". 그 파일을 바꾼 PR은 리뷰 봇이 건너뛰고, 그 워크플로의 가드 스텝(`Fail when Claude left no comment`)이 일지·대기열·티켓·하네스 탐침 밖의 파일을 함께 실은 PR을 실패로 만든다(`docs/constitution/operations.md` 48행과 리뷰 파이프라인 3). 그래서 이 PR에서는 그대로 두고 이 PR을 병합한 뒤 그 한 줄만 따로 PR로 낸다. 받는 쪽은 대기열 항목 `glossary-plain-names-left`의 남은 목록이다. 리뷰 봇은 그 절을 절 이름이 아니라 "느낌표의 기준"이라는 글자로 찾으므로(그 프롬프트의 같은 줄), 두 PR 사이에 절 이름이 어긋나도 찾는 문단은 같다.
2. (티켓, 함께 고치는 것) 노트 조각을 줄여 쓴 "조각"도 그 뜻으로 쓰인 곳은 모두 "원고"로 바꾼다. 다른 뜻의 "조각"(코드 조각, 경로 조각, 인용 조각, 세션마다 주는 기록 조각)은 그대로 둔다.
3. (티켓, 수용 기준 2) 남은 것은 이름을 바꿨다는 기록과 바꾸기 전의 글을 따온 자리뿐이다(용어집의 피할 말 줄 셋, 새로 단 ADR 이력 셋, 대기열 항목이 옛 이름으로 적은 반영 기록과 남은 일, `dev_base_tidy_root_branch` 머리 설명이 옛 굵은 머리를 밝힌 한 곳, 위 "바꾸지 않는 것"). 줄바꿈으로 갈린 꼴로도 훑었다
4. (ADR 0066 이력) 본문이 노트 조각을 줄여 쓴 "조각"(결정의 "그 조각", "새로 싣는 조각", "`upgrade/` 조각")도 릴리스 노트 원고로 읽는다.
5. (대기열 항목, 남은 것) 작업 규약(`rename-workflow-terms`에서 넘어온 한 줄): 리뷰 봇 워크플로 `.github/workflows/claude-code-review.yml` 67행의 절 이름 "릴리스 노트 조각" → "릴리스 노트 원고". 그 PR에서 빼고 따로 낸다
6. (대기열 항목, 바꾸는 길) 리뷰 봇 워크플로 `.github/workflows/claude-code-review.yml`에 옛 이름이 있으면 그 파일의 줄은 다른 파일과 함께 싣지 않고 따로 PR로 낸다. 그 파일을 바꾼 PR은 리뷰 봇이 건너뛰고, 그 워크플로의 가드 스텝이 일지·대기열·티켓·하네스 탐침 밖의 파일을 함께 실은 PR을 실패로 만든다(`docs/constitution/operations.md` 48행과 리뷰 파이프라인 3, PR 서식의 `.github/` 줄). 그 파일 67행에는 "판을 올릴 때"도 있어 판 계열을 바꿀 때도 같다.
7. (directive.md 30행) 주 체크아웃이 자기가 따르는 브랜치(`origin/dev`가 있으면 dev, 없으면 main. `tidy-checkouts` 2의 기준과 같다)에 있지 않거나 깨끗하지 않다
8. (next-session SKILL.md 49행) 핫픽스를 병합하고 main을 dev에 합치지 않았거나, 출시 PR의 merge 커밋이 dev에 없다. 후자는 내용 diff가 0이어도 해당하고, main이 strict라 그 merge 커밋을 dev에 합치지 않으면 다음 출시 PR이 막힌다. / "이어받을 상태"에 main을 dev에 합칠 것이 남았다고 적는다
9. (check_ticket.py) 머리 브랜치가 main 이나 dev 인 PR 은 판정 1 로 지난다. dev→main 출시 PR 과 운영에서 개발로 합치기는 티켓 하나를 가리키지 않는다 / 이것이면 티켓 하나를 가리키지 않는 PR(dev→main 출시 PR, 운영에서 개발로 합치기)이라 지난다. (그리고 backmerge_row 머리 설명) main 을 dev 에 합친다
10. (merge.md 37행) 앞 출시 PR의 merge 커밋은 dev에 없으므로 그 커밋을 dev에 합치지 않으면 둘째 출시 PR부터 `BEHIND`가 날 것으로 본다
11. (merge.md 118행) 핫픽스는 main을 dev에 합치지 않으면 dev에 없다. / 출시 PR은 내용이 같아도 그 merge 커밋이 dev에 없어, main을 dev에 합치지 않으면 main의 strict 때문에 다음 출시 PR이 막힌다.
12. (프로브 README 194행) `git diff --quiet dev...main`이 main에서 dev로 합칠 변경이 있을 때만 1을 내는지. 임시 저장소에서 장면 일곱(…, 핫픽스가 main에만 있다, main을 dev에 합친 뒤, 다음 출시 직후)
13. (backmerge_diff_check.sh) main에서 dev로 합칠 것이 남았는지 보는 판정 / 장면 "main을 dev에 합친 뒤"
14. (tidy-checkouts 8행) 주 체크아웃(저장소 루트, `git worktree list`의 첫 줄)이 자기가 따르는 브랜치의 원격보다 뒤에 있는 것과
15. (일지, 카나리아) 대조군은 열 모두 카나리아를 옮기지 않았다(러너의 판정이고, 답을 읽은 것은 `dev_base_open_session` 하나다).
16. (dev_base_next_session_root_branch.toml 물음) "어디서" 줄에 워크트리 문장을 넣어야 하는 조건 가운데 "주 체크아웃이 ... 에 있지 않거나 깨끗하지 않다"는 조건이 있다.
```

### 남긴 것

- 명세 Minor 5의 둘째와 셋째. `tidy-checkouts` 28행과 `open-session` 18행의 "루트가 주 체크아웃이 따르는 브랜치(…)"는 그대로 둔다. 여기의 "루트"는 저장소 루트라는 폴더이고 겹친 낱말이 없어 뜻이 맞는다. `dev_base_open_session`의 물음도 "루트가 무엇이 아니라고"를 그대로 묻는다.
- 명세 Minor 6의 둘째. `implement_ticket_status.toml` 10행 머리 설명의 "upgrade 조각"은 그 명세가 들어온 때를 적은 내력 줄이라 기록이다. 이 PR이 고른 열에도 들지 않는다.
- 표준 Nit 7. ADR 0066 본문 30행이 옛 절 이름을 가리키는 것은 그대로 둔다. ADR 본문은 고치지 않는 규칙(`.claude/rules/adr.md`)이고 새 이력이 그 절 이름을 풀어 준다.
- 명세 Nit 9. 돌린 열 가운데 여섯은 기대 문구가 기준 커밋 `f13190072`의 원천에도 있어, 통과가 이 PR의 바뀐 문장이 실렸다는 것까지는 가르지 못한다. 그 여섯은 고친 파일이 새 세션에 실렸다는 것까지만 보인다. 한계로 PR 본문과 "다음"에 적는다.
- 표준 Minor 3(티켓 상태)은 커밋 전에 done으로 바꿨고, Minor 4("다음" 절)는 단계를 닫을 때 쓴다.

### 다시 돌린 명령

- `uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `2429 files already formatted`였다.
- 카나리아. 통과한 뒤 고친 원천은 넷(`next-session`의 `SKILL.md`·`directive.md`·`merge.md`, `tidy-checkouts/SKILL.md`)이고, 고친 시각을 이 세션 기록의 편집 시각과 파일의 수정 시각으로 가렸다. 카나리아 기록 파일은 19:14에 끝났고, 그 뒤의 편집은 19:30~19:38의 본문 편집 일곱이며 머리말에 닿은 것은 없다. 이 PR이 머리말을 고친 두 스킬은 그 전에 고쳤다(`tidy-checkouts`는 설명 줄 편집이 16:15, `pr-merge`는 마지막 수정 시각이 16:15). 그 넷을 원천으로 든 명세는 다섯이다.
  - `dev_base_next_session_root_branch`는 다시 돌렸다. 물음이 자리를 가리키려고 든 "…가 아니거나"라는 글이 원천에서 사라져, 카나리아가 물음이 묻는 자리에 남았는지를 사전 확인으로 가를 수 없었다. 물음을 "…에 있지 않거나"로 고치고 `uv run python tools/canary.py --control-commit cd77e4096 <명세> <출력>`으로 돌려 통과 4·실패 0이었다(claude 2.1.325). 실험군 셋은 고친 조건의 괄호를 옮겼고, 대조군은 옛 판의 조건 "주 체크아웃이 main이 아니거나 깨끗하지 않다"에 붙은 다른 괄호를 옮겼다(답을 읽었다).
  - 나머지 넷(`backmerge_row`, `merge_methods`, `dev_branch_create_merge_protection`, `tidy_root_branch`)은 사전 확인으로 갈음했다. 같은 PR에서 같은 claude 판(2.1.325)으로 통과했고, 그 뒤 고친 곳은 원천 본문뿐이며(머리말은 고치지 않았다), 명세에서 고친 칸은 없고(머리 주석만 고쳤다), 카나리아는 물음이 묻는 자리(칸, 문단)에 그대로 남았다. 고친 문장이 그 자리에 함께 든 것은 `backmerge_row`(같은 칸의 괄호)와 `dev_branch_create_merge_protection`(같은 문단)이다. 스크래치의 `run_canaries_workflow.py --preflight`로 열 모두 `--control-commit`을 주어 사전 확인 통과 10·실패 0이었다. 그 넷의 `# 최신 결과:` 줄은 실제 돌린 결과를 두고 갈음한 날짜와 일지를 뒤에 덧붙였다.
  - 고친 스킬 아홉을 원천으로 든 60개 전체의 사전 확인(`--preflight`, 대조군 커밋 없이)에서 실험군 쪽 실패는 처음의 셋(`next_session_fable_cut_row`, `next_session_model_line`, `tidy_skill_cwd_owner`)뿐이었다. 대조군 쪽 실패는 커밋을 주지 않아 주 체크아웃이나 지금은 없는 체크아웃을 읽은 것이다.
- 고친 명세 다섯의 `uv run python tools/canary.py --shape`는 통과 5·실패 0이었다.
- 손으로 치는 나머지 검사(pytest 전체, pyright, lint-imports, web verify)는 커밋의 pre-commit 결과로 갈음한다. 결과는 커밋 뒤 이 절과 PR 본문에 적는다.
- 첫 커밋 시도는 pre-commit의 pytest 하나로 막혔다(`1 failed, 7817 passed`, 1026초). 빨간 것은 `tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`이고 문구는 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"였다. 나머지 검사는 모두 `Passed`였다(web-verify 1253초). 이 PR은 `src/`와 `tests/channel/`을 건드리지 않았고(`git diff --cached --stat -- src tests/channel`이 빈다), 그 시험만 홀로 돌리자 통과했다(`uv run pytest -q <그 시험>`, 160초). 부하가 큰 때만 나는 실패로 보고 시험과 코드는 그대로 둔 채, 이 줄만 더해 다시 커밋했다. 이 시험의 앞선 대기열 항목 `0531`(닫힘)은 다른 시험의 시계 비교였다. 원인은 가르지 못했다.
- 둘째 시도도 pytest 하나로 막혔는데 다른 시험이었다(`1 failed, 7817 passed`, 699초). `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`가 `assert lines`에서 빨갰다. 자식 파이썬이 0.5초 안에 첫 줄을 내지 못한 것이다. 그때 이 PC는 CPU 사용률이 88%였고 다른 세션의 pytest 둘이 함께 돌고 있었다(`Get-Process`, `Win32_Processor`). 그 시험도 홀로 돌리자 0.8초에 통과했다. 두 시도에서 서로 다른 시간 시험이 하나씩 빨개져 같은 시험의 연속 실패는 아니다. 셋째 시도를 띄웠다.

셋째 시도(커밋 `91e4eb4f4`)의 pre-commit은 check-ticket, check-notes, lint-imports, zizmor, check-type-escapes, check-instructions, pyright, pyright-linux, run-hooks, pytest(727.3초), web-verify(760.1초)가 모두 `Passed`였다. 마크다운 표, 줄 구분 문자, 변이 표, 카나리아 명세 모양, 헌법 판, 인용 대조, 커밋 메시지 검사도 `Passed`였다. `Skipped`는 없었다. 인용 대조의 경고 여섯은 사용자에게 보인 선택지의 설명, 이 세션이 고치기 전의 글, 바꾸기 전의 원천 글을 따온 것이라 그대로 두었다. 그 가운데 옛 판의 조건 "주 체크아웃이 main이 아니거나 깨끗하지 않다"는 대조군 커밋 `cd77e4096`의 `directive.md`에 글자 그대로 있는 것을 `git grep -c`로 봤다.

## PR 직전 리뷰

`coderabbit-review` 서브에이전트를 커밋 `91e4eb4f4`에 돌렸다(기준 `f13190072`). 셀프 리뷰를 반영하며 새로 쓴 문장 여섯 묶음을 밀 주장으로 넘겼다.

- **CLI.** CodeRabbit CLI 0.7.5가 끝까지 돌았다(`review_completed`, 종료 코드 0). 로그인 상태는 `Plan: Free`, `Seat: not assigned`였고 그래도 리뷰가 돌았다. 지적은 4건이고 보안·버그·성능에 드는 것은 없었다. 트리아지는 유효 0, 보류 1, 오탐 3이다.
  - 보류(Minor). 일지에 "다음" 절이 아직 없다. 단계를 닫을 때 쓰는 절이라 의도된 상태다. 그 절에 넣을 두 가지(돌린 열 가운데 여섯이 가르지 못하는 한계, dev에서 이미 어긋난 카나리아 셋)는 PR 본문의 "남긴 위험"에도 적었다.
  - 오탐. `backmerge_diff_check.sh` 2행이 옛 판정을 지금의 판정처럼 설명한다는 지적. 이 PR은 "되돌려"를 방향어로 바꿨을 뿐 뜻을 바꾸지 않았다.
  - 오탐. `operations.md` 27행의 `verify` 누락 잡 검출 범위, 94행의 봇 느낌표 검사. 둘 다 이 PR이 바꾸지 않은 사실이다.
- **넘긴 문장 여섯.** 모두 맞다고 판정했다. 리뷰 봇 가드의 허용 경로와 "느낌표의 기준" 찾기(워크플로 67·82~116행), ADR 0066 이력이 든 세 구절, "되돌려"를 뗀 문장들의 사실(낱말 단위로 옛 문장과 견줬다), 갈음 조건 넷의 대응(`operations.md` 149행), 헌법 판의 patch(`operations.md`의 word-diff가 절 제목 1곳과 문장 7곳), 남은 옛 이름의 자리(줄바꿈 꼴까지 `git grep`). 갈음의 시각 근거(카나리아 뒤의 편집이 본문뿐이다)는 세션 기록과 파일 시각에서 나온 것이라 git으로 다시 재지 못했다고 했다.
- **그 밖(Nit).** `dev_base_next_session_backmerge_row.toml`의 `# 그 전 결과:` 줄과 `dev_base_implement.toml`의 이어 적은 줄에 옛 이름이 남았는데, 티켓의 "바꾸지 않는 것"은 `# 최신 결과:` 줄만 이름으로 든다. 비밀 값은 더한 줄에서 찾지 못했다고 했다.

고친 것. 티켓의 "바꾸지 않는 것" 넷째 항목을 "카나리아 명세 머리의 결과 줄(`# 최신 결과:` 줄과 그 뒤에 이어 적은 줄, `# 그 전 결과:` 줄)"로 넓혔다. 헌법 문서 위치 절(`operations.md` 122행)이 기록으로 드는 "카나리아 명세 머리 주석의 `# 최신 결과:` 줄과 그 뒤에 이어 적은 줄"과 같은 범위에, 이 PR이 옛 줄의 머리를 바꿔 단 `# 그 전 결과:` 줄을 더한 것이다. 두 줄의 글자는 고치지 않았다. 이 고침은 둘째 푸시에 싣는다.

## 헌법 판

커밋 직전의 `uv run python tools/sibling_overlap.py`가 "헌법 파일을 고치고 판을 올리지 않았다: docs/constitution/operations.md"로 1을 냈다. 이 PR은 `operations.md`에서 절 제목 하나(`## 릴리스 노트 조각` → `## 릴리스 노트 원고`)와 일곱 군데의 문장에 든 옛 이름 셋을 새 이름으로 바꿨을 뿐 규약은 바꾸지 않아 문구 수정이다(`git diff --word-diff`로 바뀐 낱말을 봤다). 형제가 쓴 가장 높은 판이 3.1.1(origin/dev)이라 patch를 올려 3.1.2로 했다(`docs/constitution/README.md`의 판 줄, Last Amended 2026-11-18).

## PR 봇 리뷰 (PR 607)

첫 푸시(`91e4eb4f4`)의 결과다. `uv run python tools/wait_ci.py 607`이 "끝: 모두 통과. CodeRabbit: Review rate limited"로 끝났다(종료 코드 0). claude-review, e2e, e2e-portal, e2e-standalone, e2e-widget, python, ticket, verify, visual, web이 `SUCCESS`였고 llm은 `SKIPPED`였다.

- claude-review(이 봇의 첫 회차). "지적 없음"이었다. 경계, 유지보수성, 제목의 느낌표를 보고 걸리는 것이 없다고 적었다. 유지보수성 줄에는 `tools/check_notes.py`의 오류 문구가 그 시험의 단언과 같이 바뀌었고, `tools/`에 옛 이름이 남지 않았으며, 리뷰 봇 워크플로 한 줄은 PR 설명대로 따로 낸다고 적었다.
- CodeRabbit. 무료 리뷰 몫을 다 써서 이 푸시를 리뷰하지 않았고, 남긴 `@coderabbitai review`에도 `Review rate limited`로 답했다. 한도에 걸린 푸시라 이 봇의 회차로 세지 않는다(`next-session` `merge.md` 2의 회차 세기). 이 PR의 보안·버그 축은 PR 직전에 돈 CodeRabbit CLI의 결과(위 "PR 직전 리뷰")를 PR 체크리스트에 적은 것이 대신한다(`docs/constitution/operations.md` 108행).
- 인라인 코멘트는 두 봇 모두 없었다.

고친 것도 남긴 것도 없다. 로컬 모델 시험은 이 PR이 고친 파일이 병합 조건의 범위에 들지 않아 돌리지 않는다.

둘째 푸시는 이 절과 아래 회고와 "다음"을 실은 커밋이다(이 일지, 티켓의 한 줄, 대기열 항목 여섯만 바뀐다). 이 푸시로 도는 claude-review는 둘째 회차라 Critical·Major만 고친다. CodeRabbit이 이 푸시를 리뷰하면 그 봇의 첫 회차라 Minor·Nit도 지적마다 고칠지 판단한다. 한도로 리뷰하지 않으면 풀리기를 기다리지 않고 병합하며, 그 사실을 PR 코멘트에 적는다. 둘째 푸시의 결과와 보류하는 지적은 이 일지에 다시 적지 않고 PR 코멘트와 다음 일지에 적는다(`merge.md` 2의 "뒤로 넘긴 일").

## 회고

원천은 이 일지와 이 세션, 그리고 앞 단계의 지시문이 "이어받을 상태"로 넘긴 사건 둘(PR 605의 마지막 코멘트)이다. 낸 후보는 열둘이다. 승인이 여섯(열린 항목에 회차를 더한 것 넷, 새 항목 둘), 기각이 넷, 일지에만 남기는 것이 둘, 넘김은 없다. 이 세션에서 회고로 반영한 것은 없고 사용자에게 물은 것도 없다. 만료한 항목은 없다.

**승인(열린 항목에 회차를 더한 것).**

- 인계 계기가 백그라운드로 띄운 커밋이 끝나기 전에 왔다. 사건: 이 단계의 커밋 호출 직후 세 번(295,702·325,429·331,408 토큰)과, 앞 단계 PR 605의 둘째 커밋 직후 한 번(240,904 토큰)이다. 넷 모두 곁 세션이라 넘기지 않고 이었다. 열린 항목 `handoff-trigger-before-background-commit-ends`가 이미 처방한 사건이라 회차를 더했고, 더한 뒤 7회차다. 처방은 있는 훅의 판정을 고치는 것이라 새 훅의 발동 확인(`tools/hook_report.py`)은 돌리지 않았다. PR을 연 뒤에 온 계기(350,797 토큰)는 실제 단계 경계에 온 것이라 이 사건이 아니다.
- 문서만 바꾼 커밋의 pre-commit이 길었다. 사건: PR 605의 둘째 커밋 `a95c599e7`(일지·대기열 항목·티켓만 바꿨다)이 929초였다(pytest 711.4초, web-verify 928.7초). 앞 단계가 다음 회고에 세라고 넘긴 사건이다. 열린 항목 `docs-only-commit-precommit-slow-again`에 회차를 더했고, 더한 뒤 13회차다.
- 이름을 바꾸는 chore의 잔존 확인이 줄바꿈으로 갈린 꼴과 줄여 부른 꼴을 놓쳤다. 사건: 위 셀프 리뷰의 표준 Major 1·Minor 2·Nit 5와 명세 Major 2·Minor 6의 첫째·Minor 8이다(`tools/check_ticket.py` 105~106행과 카나리아 명세 머리 설명의 "되돌려⏎합치기", `tools/check_notes.py`와 워크플로 주석의 "조각"). 열린 항목 `rename-residual-grep-misses-split-and-underscore-forms`가 이미 처방한 사건이라 회차를 더했고, 더한 뒤 3회차다.
- 원천과 어긋난 카나리아 명세가 사전 확인에 다시 걸렸다. 사건: 고친 스킬 아홉을 원천으로 든 60개의 사전 확인에서 `next_session_fable_cut_row`, `next_session_model_line`, `tidy_skill_cwd_owner`의 실험군 카나리아가 원천에 없었다(`origin/dev`의 원천에도 없다). 같은 종류를 다루는 열린 항목 `stale-web-design-canaries`(0539를 잇는다)에 회차를 더했고, 더한 뒤 3회차다. `tidy_skill_cwd_owner`는 0539가 든 넷 가운데 하나다.

**승인(새 항목).** 둘 다 새 검사가 처방이라 같은 실수의 다섯 번째이거나 손상이 한 번 났을 때 더한다.

- `canary-question-quote-left-source`(1회차). 사건: `dev_base_next_session_root_branch`가 통과한 뒤 셀프 리뷰가 원천의 조건을 고쳐, 물음이 자리를 가리키려고 따온 "…가 아니거나"가 원천에서 사라졌다. 사전 확인은 기대 문구만 원천에서 찾아(`tools/canary.py`의 `source_problems`를 읽었다) 이를 알리지 않았고, 갈음 조건 넷을 손으로 대 보다 찾았다. 그 명세 하나를 다시 돌린 값이 들었다. 층은 사전 확인의 검사다. `--search 물음.*인용`, `--search 인용.*물음`, `--search 물음이.가리키`, `--search tools/canary.py`, `--search preflight`로 찾았고 같은 처방의 항목이 없었다. 가까운 것은 카나리아가 원천에 있는지 보는 닫힌 0133과, 기대 문구가 앞 판에도 있는지를 다룬 만료한 0538이다.
- `rename-chore-edits-record-lines`(1회차). 사건: 명세 Major 1이다. 티켓의 "바꾸지 않는 것"이 `# 최신 결과:` 줄만 들어, 그 뒤에 이어 적은 기록 줄(`dev_base_implement.toml` 8행)의 옛 이름을 바꿨다. 구현 때 실리는 지침(`docs/constitution/operations.md` 문서 위치 절이 그 줄을 기록으로 든다)을 어겨 리뷰가 잡은 사건이라 회차로 센다. 그 지침을 낸 항목을 `--search 최신.결과`, `--search 결과.줄`, `--search 기록을.고`, `--search 이어.적은.줄`, `--search 기록까지`, `--search 지난.결과`로 찾지 못해 새 항목을 썼다. 처방은 기준 판과 견주어 결과 줄이 덧붙이기만 했는지 보는 검사이고, 검사로 가를 수 없으면 이름 바꾸기 티켓 서식의 지침이다. 같은 서식 자리를 다루는 `rename-residual-grep-misses-split-and-underscore-forms`와 서로 가리키게 했다.

**기각.**

- 헌법 판을 올리지 않은 채 커밋하려 했다. 커밋 직전의 `tools/sibling_overlap.py`가 그 자리에서 알렸다(이미 있는 검사).
- 리뷰 봇 워크플로를 다른 파일과 함께 실었다(명세 Major 3). 셀프 리뷰가 잡았고, 그대로 푸시했어도 그 워크플로의 가드 스텝(닫힌 0158의 고침)이 그 자리에서 막는다.
- 리뷰가 잡도록 둔 기준이 제 몫을 한 것들. 수용 기준 2의 닫힌 목록의 반례, "되돌려"를 떼어 방향이 사라지거나 새 이름을 끼워 말이 겹친 문장(명세 Minor 4·5·Nit 10, 표준 Nit 6), ADR 0066 이력이 줄여 쓴 "조각"을 빠뜨린 것(명세 Minor 7)이다. 검사로 옮길 수 없고 표준에 더할 새 판단 기준도 아니라 회차로 세지 않는다.
- 일지 문장 몇을 근거보다 강하게 썼다가 고쳤다(답을 읽지 않고 쓴 대조군 문장, 카나리아 뒤 편집의 시각과 자리를 말한 문장, 헌법 판의 까닭). PR 직전 리뷰 전에 이 세션이 근거를 다시 대 보고 고쳤고, 근거를 끝까지 열었는지는 검사로 가를 수 없다. 돌린 카나리아 열 가운데 여섯이 바뀌기 전 원천으로도 통과하는 한계(명세 Nit 9)는 사용자가 고른 범위에서 나온 것이고, 결과 줄과 일지와 PR 본문이 그 한계를 적어 넘치는 주장이 없다. 0538이 다룬 실수(판정했다고 적은 것)가 이번에는 없어 사건으로 세지 않는다.

**만료.** `uv run python tools/queue_open_rows.py`의 작업 트리 출력에 만료할 항목이 없어, `--ref origin/dev`로 다시 돌릴 대상이 없었다(두 출력에 모두 든 항목만 닫는다).

**일지에만 남기는 것.**

- 커밋 시도 둘을 막은 시간 시험 둘(`tests/channel/cli/test_interrupt.py`의 Ctrl+C 30초, `tests/tools/test_probe_kit.py`의 배출 0.5초, 위 "다시 돌린 명령"). 0306이 받아들여 닫은 종류(부하에서만 빨간 시간 시험)의 새 사례라 회차를 더하지 않는다(retro 5단계의 항목의 종류).
- 이 PR의 첫 커밋은 `.py`가 들어 문서만 바꾼 커밋이 아니라 `docs-only-commit-precommit-slow-again`에 세지 않는다. 둘째 커밋(이 일지, 티켓, 대기열 항목만 바뀐다)의 시간은 그 커밋이 끝나야 알 수 있어 PR 코멘트에 적고, 다음 단계의 회고가 센다.

## 다음

이 PR이 병합되면 작업 규약 쪽 이름 셋은 리뷰 봇 워크플로의 한 줄만 남는다. 남은 것은 아래와 같다.

- **리뷰 봇 워크플로 한 줄**(다음 작업). `.github/workflows/claude-code-review.yml` 67행의 절 이름 "릴리스 노트 조각"을 "릴리스 노트 원고"로 바꾼다. 그 파일을 바꾼 PR은 리뷰 봇이 건너뛰고, 가드 스텝이 일지·대기열·티켓·하네스 탐침 밖의 파일을 함께 실은 PR을 실패로 만든다(`docs/constitution/operations.md` 48행과 리뷰 파이프라인 3). 그래서 그 파일과 harness 티켓과 일지만 싣는다. 받는 쪽은 대기열 `glossary-plain-names-left`의 남은 목록이다. 그 줄에는 "판을 올릴 때"도 있어 판 계열을 바꿀 때 같은 길을 한 번 더 간다.
- **화면 쪽 이름 둘.** 거꾸로 동기화 → 웹 편집 반영, 원색 토큰 → 색 단계 토큰. 원색 토큰의 풀이는 디자인 시스템 아티팩트에 올라가는 원본(`web/tools/sync-design-system/artifact-source/README.md`, `foundations/colors/index.html`)에도 있어, 그 PR은 병합 뒤 `sync-design-system` 올리기까지 해야 끝난다(위 "다섯을 둘로 나눈 까닭". 그 둘이 고치는 스킬과 규칙을 원천으로 든 카나리아 명세는 16개였다).
- **남은 이름 바꾸기**(대기열 `glossary-plain-names-left`). 앞 일지(`2026-11-18-1422-rename-small-run-terms.md`)의 "다음"에 적힌 목록에서 이 PR의 셋과 위 화면 쪽 둘을 뺀 것이다. 계약 파일에 닿지 않는 작은 이름(서버 파일, 전송, 관리자, 넘김), 큰 이름(고지, 운영자 파일, 규칙 파일, 사이트 파일), 계약 파일에 닿는 이름(저자, 교환, 주체, 컨텍스트, 상한, 표지. 병합 전에 사용자에게 알리고 로컬 모델 시험의 범위에 드는지 본다), 그리고 맨 뒤의 제품 판과 판 계열이다. 쓰인 곳의 수는 그 일지에 있고 시작할 때 다시 센다. 로컬 모델 시험의 비용에 대한 사용자의 답은 처음의 여덟을 바꾸는 PR에 닿는다고 읽었으므로, 2026-11-18에 더 고른 이름의 PR이 시험 범위에 닿으면 예상 비용을 보이고 다시 묻는다.
- **이 PR의 카나리아가 남긴 한계.** 돌린 열 가운데 여섯은 바뀌기 전 원천으로도 통과해, 고친 파일이 새 세션에 실렸다는 것까지만 보인다(위 "남긴 것"의 명세 Nit 9). 나머지 50개는 사전 확인만 했다.
- **원천과 어긋난 카나리아 셋.** `next_session_fable_cut_row`, `next_session_model_line`, `tidy_skill_cwd_owner`는 이 PR이 고치지 않았다. 대기열 `stale-web-design-canaries`(3회차)가 같은 종류를 센다. 그 명세들의 원천을 다시 고치는 PR이 사전 확인에서 다시 만난다.
- **rag-engine.** 같은 결정을 rag-engine에 맞추는 지시문은 앞의 일지에 있고 사용자에게 냈다. 이 단계에서 사용자가 새로 한 말은 없다.
- **열여섯 이름의 영어 표기.** 일지 `2026-11-17-2031-plain-words-in-written-artifacts.md`의 "다음"이 남긴 물음이고 사용자가 아직 답하지 않았다.
- **회차 5 이상인 대기열 항목.** 이 회고로 `handoff-trigger-before-background-commit-ends`가 7회차, `docs-only-commit-precommit-slow-again`이 13회차가 됐다. 하네스 chore를 고를 때의 계기다.
- **앞 일지의 "다음"에서 그대로 남은 것.** 끝난 기능의 변이 표에 남은 `-k` 여섯(`mutation-table-test-filter-stale-after-rename`), `CLAUDE.md` 밖에 남은 "위젯 미리보기 페이지"(`widget-test-page-term-leftovers`), e2e가 `serve`를 시스템 임시 폴더에서 띄우는 것(`e2e-serve-cwd-is-system-temp-dir`), 회차를 한꺼번에 띄우는 프로브의 띄우기 예외(`probe-parallel-launch-outside-round`). 앞 일지가 적은 `.scratch/plan.md`의 함께 고친 파일은 이 브랜치의 `uv run python tools/sibling_overlap.py`에 "함께 고친 파일 없음"으로 나왔다.
