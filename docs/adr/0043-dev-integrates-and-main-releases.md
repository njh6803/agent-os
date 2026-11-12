---
status: accepted
date: 2026-11-04
---

# 티켓 PR은 dev로 가고 기능이 끝나면 dev를 main에 merge 커밋으로 올리며 hotfix는 main에서 따 되돌려 합친다

지금 브랜치는 main 하나다. 티켓마다 브랜치를 따 main으로 PR하고 squash로 합치며 main 이력은 PR 단위다(ADR 0005, ADR 0037, `docs/constitution/operations.md`의 "브랜치와 병합"). ADR 0042의 묶음 ②가 트레이스 저장소를 PostgreSQL로 옮기고 Redis를 들이면 테스트가 컨테이너를 띄우고(testcontainers), 실제 이미지로 띄워 보는 e2e와 LLM 테스트처럼 느리고 비싼 검사가 는다. 그 검사를 PR마다 돌리면 티켓 PR이 느려지고, 돌리지 않으면 main이 운영에 내보낼 수 있는 머리라는 뜻을 잃는다. 묶음 ② 라운드에서 사용자가 브랜치 전략을 바꾸자고 냈다. main은 운영에 배포하는 용도로, dev는 개발용으로 쓰고, dev에 병합할 때는 CI를 빠르게, main은 실제 컨테이너를 띄워 테스트하며, 운영에서 발견된 버그는 hotfix 브랜치로 따서 바로 main에 합친다는 것이다(일지 2026-11-04-01 라운드 3 7호출의 채팅 답. 원문은 그 일지의 `> 사용자:` 인용). 라운드 3 8~10호출이 모양을 정해 합의 요약을 확인받았다. **main은 운영에 내보낼 수 있는 머리(릴리스)이고 dev는 개발 브랜치다. 티켓 PR(feature·chore·docs)은 dev로 가고 지금처럼 squash에 티켓 하나다. dev→main은 기능(`.scratch/plan.md`의 행) 하나가 done이고 main CI가 초록일 때, 그 기능을 끝낸 세션이 PR을 열고 merge 커밋으로 병합한다(사용자 승인 없음, squash 아님). (바뀜: 이력 2026-11-12 "출시 PR 뒤에도 main을 dev에 되돌려 합친다") hotfix는 main에서 `hotfix/NN-<slug>`로 따 main으로 PR하고, 티켓 PR이라 feature와 같은 티켓 규칙과 봇이 들며 squash다. 병합 뒤 그 세션이 main을 dev에 되돌려 합친다(merge 커밋). Git Flow에서 release 브랜치를 뺀 판이다.** 배포 자체(어디에 어떻게)는 이 결정 밖이다.

## Considered Options

- **지금처럼 main 하나에 느린 검사까지 PR마다 돈다.** 티켓 PR 하나가 컨테이너 pytest에 LLM 테스트와 실제 이미지 e2e까지 기다린다. 거부했다. 인터뷰에 올린 선택지가 아니라 이 ADR이 견준 안이다.
- **느린 검사를 PR에서 빼고 main 푸시에서만 돈다.** main이 빨갛게 될 수 있어 "운영에 내보낼 수 있는 머리"가 아니다. 거부했다. 이것도 인터뷰에 올린 선택지가 아니라 이 ADR이 견준 안이다.
- **dev→main을 정해진 주기(예: 매주)나 티켓(PR)마다 자동으로 올린다.** 주기는 기능이 반쯤 든 머리를 내보내고, 티켓마다는 dev의 뜻이 없다. 둘 다 거부했다(라운드 3 8호출). 기준은 기능 하나가 done인 때다.
- **hotfix PR도 merge 커밋으로.** 티켓 PR의 모양(squash에 티켓 하나)이 둘로 갈린다. 거부했다(라운드 3 10호출). merge 커밋은 dev→main과 main→dev 되돌려 합치기 둘뿐이다.
- **dev PR에서 pytest를 아예 빼고 린트·타입·경계·web verify·커밋 검사만 돈다.** 컨테이너 pytest가 main PR까지 미뤄져 티켓이 깨진 것을 기능 끝에서야 안다. 거부했다(라운드 3 9호출).
- **테스트가 DB를 docker compose로 먼저 띄운 것에 붙고 연결 문자열이 없으면 실패한다, 또는 있으면 그것을 없으면 testcontainers.** pytest가 testcontainers로 스스로 띄우고 없으면 실패하는 쪽을 골랐다(ADR 0042 묶음 ② 18). 거부했다(라운드 3 9호출).
- **전환 때 열린 PR도 base를 dev로 바꾼다.** 전환이 서기 전에 열린 PR(이 PR 포함)은 main으로 끝낸다. 거부했다(라운드 3 9호출).
- **도구의 기준을 브랜치 접두가 아니라 설정 파일 한 줄(기본 base)로 두고 hotfix 세션이 그 값을 바꿔 쓴다.** 세션마다 값을 바꾸면 같은 체크아웃의 다른 세션이 엉뚱한 base로 간다. 접두로 가른다. 거부했다(라운드 3 9호출).
- **이 PR에서 훅·스킬·CI까지 고친다, 또는 방향 PR 뒤에 별도 설계 인터뷰로 미룬다.** 전략은 이 인터뷰에서 정하고 ADR 초안을 이 PR에 싣되 하네스 고침은 harness 티켓이다. 둘 다 거부했다(라운드 3 8호출).
- **CI 분담의 추천안: dev PR은 린트·타입·경계·web verify·커밋 검사와 PostgreSQL·Redis 컨테이너를 띄운 pytest만 돌고, main PR은 그 전부에 두 e2e·사진 비교·LLM 테스트·실제 이미지 compose e2e를 더한다.** 사용자가 dev PR에 지금 잡 전부를 두는 쪽을 골라 거부됐다(라운드 3 9호출). 그래서 dev PR은 지금보다 빨라지지 않는다.
- **티켓 검사와 봇: dev→main PR도 커밋 검사를 지나되 PR 본문이 done 기능(`plan.md` 행)을 가리키는지 본다, 또는 면제 없이 지금 판정 그대로 두고 어긋나는 것은 harness 티켓이 정한다.** 둘 다 거부했다(라운드 3 9호출). dev→main PR의 면제가 가장 작다.

## Consequences

- **CI 분담.** dev PR은 지금의 잡(`.github/workflows/ci.yml`의 python, web, e2e, e2e-widget, visual, ticket와 모음 잡 verify)에 PostgreSQL·Redis 컨테이너를 띄운 pytest를 더한 것이다. main PR(dev→main, hotfix→main)과 main 푸시는 거기에 LLM 테스트(`-m llm`, `-m llm_widget`. API 키 시크릿이 CI에 든다)와 실제 이미지의 compose e2e(Dockerfile과 compose를 새로 짓는다)를 더한다. 잡 이름과 모양은 harness 티켓이 정한다. (바뀜: ADR 0056)
- **티켓 검사와 봇.** 커밋 검사(`tools/check_ticket.py`, ADR 0037)는 dev→main PR에서 면제한다. 머리가 dev라 티켓 하나를 가리키지 않기 때문이다. hotfix→main은 티켓 PR이라 그대로 지난다. 리뷰 봇은 dev→main에서 끄고 hotfix에서는 돈다. ADR 0037의 "main에 들어가는 PR은 모두 티켓 파일 하나를 가리킨다"는 dev에 들어가는 티켓 PR과 hotfix PR을 가리키는 것으로 읽히고 그 문장에 이 ADR의 포인터를 단다. ADR 0005의 "squash 병합, main 이력은 PR 단위"도 같다(main 이력은 기능 단위의 merge 커밋이 된다).
- **직접 커밋 금지는 main과 dev 둘 다다.** 지금 `hook_git_main_commit`은 main 위의 커밋만 막는다(ADR 0005). dev도 막는다.
- **도구의 기준.** 워크트리의 기준(`origin/main`)과 PR의 base를 브랜치 접두로 가른다. `hotfix/*`는 main, 그 밖(`feature/*`, `chore/*`, `docs/*`)은 dev다. `tools/sibling_overlap.py`, `next-session`의 merge.md, `tidy-checkouts`, `git-pr`·`git-pr-merge` 같은 main을 전제한 tools와 스킬(인터뷰 때의 셈으로 tools 12개, 스킬 8개)과 `CLAUDE.md`의 환경 함정, `docs/constitution/operations.md`의 "브랜치와 병합"이 바뀐다.
- **전환.** harness 티켓이 dev를 main에서 딴다. 그 뒤에 연 PR부터 dev로 가고, 그때 열린 PR(이 ADR을 싣는 PR 포함)은 main으로 끝낸다. 하네스 고침(훅·스킬·CI·규약 문서)은 그 harness 티켓의 일이고 워크트리에서 하며 새 세션에서 불러 본다(작업 규약 3). 그때까지 지금 규약(main으로 PR)이 그대로다.
- **되돌려 합치기.** hotfix를 main에 합친 세션이 바로 main을 dev에 merge 커밋으로 합친다. (바뀜: 이력 2026-11-12 "출시 PR 뒤에도 main을 dev에 되돌려 합친다") 잊으면 다음 dev→main에서 hotfix가 사라진다. 그 순서를 `next-session`의 merge.md에 적는 것도 harness 티켓이다. 되돌려 합치기를 PR로 하는지 로컬 병합 뒤 푸시로 하는지와, dev 직접 커밋을 막는 훅이 그 병합 커밋을 어떻게 지나게 할지도 그 티켓이 정한다.
- **원격 설정.** 저장소는 merge 커밋·squash·rebase 세 방식을 모두 허용한다(`gh repo view`로 봤다, 라운드 3 10호출). dev를 main처럼 보호 브랜치로 둘지는 인터뷰에서 묻지 않았고 harness 티켓이 정하며, 그 설정은 사람이 GitHub에서 한다.
- **치르는 값.** main에 오르는 간격이 기능 길이를 따르고, 되돌려 합치기를 잊으면 다음 배포에서 hotfix가 사라지며, dev PR은 지금보다 빨라지지 않는다(컨테이너 pytest가 더해진다). 이 PR이 ADR 둘(ADR 0042와 이것)을 들어 승인도 둘이었다(둘 다 2026-11-04에 승인됐다).
- **용어.** `CONTEXT.md`에 티켓 PR, 운영 브랜치, 개발 브랜치, 기준 브랜치, 출시 PR, 핫픽스, 되돌려 합치기가 든다. 개발 브랜치가 서기 전에는 기준 브랜치가 모두 운영 브랜치(main)다.

## 이력

### 2026-11-12 출시 PR 뒤에도 main을 dev에 되돌려 합친다

dev 전환(`dev-branch-create`)이 main의 보호를 strict(필수 검사 `verify`를 낸 PR의 머리가 main의 끝 커밋을 품어야 병합된다)로 두었다. 출시 PR을 merge 커밋으로 병합하면 main에 그 merge 커밋이 생기는데 dev에는 없으므로, 되돌려 합치지 않으면 둘째 출시 PR부터 `BEHIND`로 막힐 것으로 본다(커밋 관계로 따진 어림이다). 그래서 되돌려 합치기를 핫픽스 뒤에만이 아니라 출시 PR 뒤에도 한다. 출시 PR을 병합한 세션이 바로 main을 dev에 PR과 merge 커밋으로 합치고, 계기는 `main`의 끝 커밋이 dev의 조상이 아닌 상태다(`git merge-base --is-ancestor origin/main origin/dev`가 1). 내용 diff로 가르지 않는다. 출시 직후의 diff는 0이어도 그 merge 커밋을 dev가 품지 않기 때문이다.

2026-11-12에 사용자가 세 길 가운데 이것을 골랐다. 나머지 둘은 출시 PR만 `gh pr merge --admin`으로 병합하기(보호를 건너뛰는 일이 출시마다 정례가 된다)와 main의 strict 끄기(핫픽스 PR이 옛 main 기준으로 통과한 채 병합될 수 있다)였다. 치르는 값은 출시마다 PR 하나와 CI 한 바퀴, dev 이력에 merge 커밋 하나다. 순서는 `next-session`의 `merge.md` "출시 PR"과 "되돌려 합치기"에 있다. 출시 PR을 여는 계기(기능 계획의 끝 줄을 적은 커밋이 dev에만 있다)와 전제 확인(main CI 초록, dev가 main을 품었다)도 같은 파일이 정한다. 기능을 끝낸 세션이 출시 PR을 열지 못했거나 보류했으면 다음 병합 뒤의 세션이 같은 상태를 읽고 대신 연다(본문의 "기능을 끝낸 세션이 PR을 열고"는 이 경우를 뺀 첫 길이다). 위 Consequences의 "잊으면 다음 dev→main에서 hotfix가 사라진다"는 임시 저장소에서 핫픽스가 다른 줄이면 출시 뒤에도 main에 남는 것을 본 결과와 어긋나지만(`docs/journal/2026-11-12-0407-dev-base-skills-docs.md`), 그 문장의 개정은 이 이력이 다루지 않는다.
