# 2026-10-30 (12) 첫 정식 올리기로 Components 절에 카드 아홉이 뜨고 배너가 사라진다 (design-card-build 05)

next-session 지시문으로 연 새 세션이다. 주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌고, 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`(이름 `05-first-canonical-upload`)로 들어가 브랜치를 `feature/05-first-canonical-upload`로 바꿨다. 기준은 `origin/main` `fc54912a`(PR #435 병합)이다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/design-card-build/issues/05-first-canonical-upload.md / 다음 작업: .scratch/design-card-build/issues/05-first-canonical-upload.md. 첫 정식 올리기로 디자인 시스템 아티팩트의 Components 절에 카드 아홉을 띄우고, 옛 카드 파일과 배너를 걷는다 / 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /implement .scratch/design-card-build/issues/05-first-canonical-upload.md / 브랜치: feature/05-first-canonical-upload / 모델: Opus 5.5 / medium. 레벨 스윕의 갈래 / 읽을 것: 일지 docs/journal/2026-10-30-10-upload-always-assembles.md의 "다음" / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다 / 이번 요청 범위: PR과 병합까지"

## 체크아웃 정리

루트는 main이고 깨끗해 `fcf808fa`에서 `fc54912a`로 당겼다(당기기 명령의 출력을 손으로 봤다).

- 끝낸 것과 지운 것: 쉬는 세션의 프로세스만 쥐었던 `02-assemble-tokens-readme-foundations`를 `end-holders`로 끝낸 뒤 그 워크트리와 브랜치를 지웠다.
- 남긴 것: `03-upload-plan-first-canonical`·`06-admin-run-list`·`08-admin-decision-column`(쉬는 세션 밖의 프로세스가 쥐었다), `04-upload-always-assembles`(그 브랜치의 세션이 돌았다), `06-round-drive-record`(바뀐 파일이 있다), PR이 없는 것 여럿, 앱 표지가 있는 둘. 줄마다의 이유는 judge 출력 그대로다.
- 휴지통: 일부를 비웠고, `design-card-build-tickets` 등은 다른 체크아웃의 node.exe(pid 11212)가 쥐어 남았다. 다음 정리가 다시 본다.

## 올리기

`upload.md` 1~6대로 `origin/main`의 분리 HEAD에서 했다. 수와 판정은 도구(`check judge`, `decide`, `assemble`, `record plan`)가 찍은 출력과 Artifact 도구의 결과를 손으로 옮긴 것이다. 줄마다의 사실은 티켓의 "결과" 1~7이 원천이라 여기서는 흐름만 적는다.

- 확인 `clean`, 결정 `upload`. 기록의 `files`에 정식 카드 0개, 옛 별칭 48개라 첫 정식 올리기가 아직이었다.
- 계획: `firstCanonical` true, 보낼 파일 26개(`tokens.json` 포함), 지울 경로 48개, 한 호출.
- 첫 publish가 "haven't viewed the latest version"으로 거부됐다. 확인을 처음부터 다시 돌려 `clean`을 보고(판만 `1793331444-ea25`로 바뀌고 기록 해시와 산출이 같았다), 페이지 단위 read로 원인이 Design System 형식의 새 릴리스(`1793316667-952a`)라는 것을 본 뒤 같은 계획으로 다시 보내 받아들여졌다(Version 34).
- 보낸 뒤 확인 `clean`, Files 목록 880 → 852, 옛 별칭 0.

## 페이지 확인

앱 안 브라우저에서 사용자가 로그인한 뒤 스크린샷으로 봤다. 본 것은 티켓의 "결과" 8이다. 카드 아홉이 모두 그려졌고(몇 카드는 몇 초 늦게), TextField의 아래 문구는 잘리지 않았으며, 테마 여덟이 '(Light)'·'(Dark)'로 갈리고 라이트·다크 모두 맞게 그려졌다. 배너와 "Finish setting up" 단추는 없었다. 한글 글꼴의 계산된 이름은 교차 출처 iframe이라 읽지 못했다.

## 커밋

`682f8e52` 지난 산출 목록과 티켓 결과. pre-commit의 검사가 모두 Passed였다(pytest 431.5초, web-verify 486.7초). `.py`가 없어 ruff 둘이 `Skipped`라 손으로 쳤고 `All checks passed!`, `1181 files already formatted`였다.

## 셀프 리뷰

기준 `fc54912a`, 파일 2개, 커밋 1개, 미추적 1개(이 일지).

### 표준 축

수를 센 주장(지울 48, 더한 20, 802줄, 보낸 26, 880 → 852, 기록 commit의 조상)은 모두 맞다고 냈다. 하드 둘: 마무리의 plan.md 체크박스가 그 일을 하기 전에 [x]였다, 결과 4가 옮기기 절을 아티팩트에서 받은 README가 아니라 지은 README로 근거했다. 판단 다섯: 조건부 박스 셋을 [x]로 둔 것, 검증 박스가 기록 없이 [x]인 것, Status는 PR 전에 done으로, 결과 6의 원인이 읽은 것인지 판단인지, smell 없음.

### 명세 축

범위 밖 동작 없음. 지적 셋: Noto Sans KR 요구를 눈으로만 봤는데 [x]다, 결과 4의 README 대상(표준 축과 같다), 검증 박스가 일 전에 [x]다. 결과 3·9·1·2의 주장은 맞다고 냈다.

### 반영

- 고친 것: plan.md·검증 박스를 [ ]로 되돌렸다(병합 직전 커밋과 검증 뒤에 닫는다). 조건부 박스 셋을 [ ]로 두고 "(해당 없음, 결과 N)"을 붙였다. 결과 4를 "확인이 아티팩트에서 받은 README(보내기 전에 돈 두 번의 확인 사본)에 "## Migrated from the standalone version" 절이 없어 물을 것이 없었다. 두 사본에서 그 머리 문장을 `grep -c`로 세어 모두 0이었다."로 고쳤다(check-1·check-3 사본을 `grep -c`로 봤다). 결과 6을 "경로 없이 `url`만 준 Artifact read의 결과에 Design System 형식의 새 릴리스(`1793316667-952a`)가 보여, 그 릴리스가 아티팩트의 판을 올린 것이 거부의 원인이라고 판단했다. read 결과를 손으로 보고 낸 판단이고, 판이 오른 시각과 릴리스 시각을 대 보지는 않았다."로 고쳤다(처음 고친 글에 `page: true`라 적었다가 트랜스크립트의 호출 입력을 대 보고 바로잡았다). 결과 8의 글꼴 줄을 "확인하지 못했다"로 고치고, 코드로 본 것(묶음 CSS가 `font-family:Noto Sans KR`을 선언한다, `grep -o`)을 따로 적었다. 카드 iframe 주소를 따로 열어 계산된 글꼴을 읽으려 했으나 껍데기 페이지로 넘어가 닿지 못했다.
- 남긴 것: Status는 PR 직전에 done으로 바꾼다(규약대로). Noto Sans KR의 렌더 확인은 이 세션의 도구로 닿지 않아 남긴다.
- 다시 돌린 명령: 다음 커밋의 pre-commit으로 갈음한다. 결과는 커밋 뒤 이 일지에 적는다.
- PR 직전 리뷰에 밀 주장: 위 결과 4·6·8의 고친 문장.

## 커밋(셀프 리뷰 반영)

`3b594c63` 티켓 결과의 근거와 이 일지. pre-commit의 검사가 모두 Passed였다(pytest 598.7초, web-verify 602.7초. 커밋이 600초를 넘겨 백그라운드로 넘어갔고 끝 알림의 출력을 손으로 봤다). ruff 둘은 `.py`가 없어 `Skipped`였고, 첫 커밋 뒤 손으로 친 결과가 그대로다(그 뒤 `.py`를 바꾸지 않았다).

## PR 직전 리뷰

origin/main은 `fc54912a` 그대로라 합칠 것이 없었다. CodeRabbit CLI는 좌석이 없어 대체 둘을 나란히 돌렸다.

### bug-perf-review

지적 0건(유효 0, 오탐 4). 지난 산출 목록은 비글꼴 32와 글꼴 770의 802줄이고 기록·색인이 들지 않았으며, 다음 올리기에서 잘못된 지울 경로가 나오는 길은 찾지 못했다고 냈다(`upload.ts`·`upload.test.ts` grep과 `assemble.ts` 대조로 판정했고 `planUpload`를 이 목록으로 부르지는 않았다고 밝혔다). 밀 주장 넷: 결과 4의 머리 문장이 `upload.md` 47행과 글자 그대로 같다, 결과 6이 판단으로 적혔다, 결과 8의 묶음 CSS는 `assemble.ts`가 fontsource의 `@font-face`를 붙여 짓는 길이 맞다(패키지가 설치되어 있지 않아 글자는 대 보지 못했다), 체크박스 모양이 맞다.

### /security-review

식별 서브태스크가 확신도 8 이상의 취약점 0건을 냈고, 거르기에 넘길 후보가 없었다. 지난 산출 목록 802줄에 `..`·절대 경로·`project/` 밖 항목이 0건이고 읽는 길(`io.ts`의 `readPathList`·`isArtifactPath`)이 그런 항목을 막는다고 냈다(서브태스크가 코드를 읽은 판정이다). 티켓과 일지에 비밀 형태의 문자열은 없었다.

### 반영 (PR 직전)

고친 것 없음. 두 리뷰 모두 지적 0건이었다.
