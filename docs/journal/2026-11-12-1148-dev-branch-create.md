# 2026-11-12 (11:48) dev를 origin/main에서 따고 dev 전환을 닫는다

세션 제목 `chore/dev-branch-create`. 브랜치 `chore/dev-branch-create`, 워크트리 `.claude/worktrees/dev-branch-create`, 티켓 `.scratch/harness/issues/dev-branch-create.md`. 모델 `claude-opus-5-5`(지시문은 Sonnet 5.5 / high였고 세션 중에 바뀌었다).

## 사용자 프롬프트

세션의 첫 메시지는 `implement` 스킬을 이 티켓에 대고 돌리라는 지시문이다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/harness/issues/dev-branch-create.md
> 다음 작업: .scratch/harness/issues/dev-branch-create.md. dev를 origin/main에서 따고 dev 전환을 닫는다 / 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 그 뒤 EnterWorktree(name은 dev-branch-create)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 브랜치: chore/dev-branch-create / 이번 요청 범위: PR과 병합까지. 단 사람의 몫 (가)~(라)와 dev를 따는 푸시는 사용자의 답과 승인을 받은 뒤에 한다

## 사람의 몫 (가)~(라)

첫 선택 화면에서 사용자는 네 답을 고르면서 그 답에 다음 말을 덧붙였다.

> 사용자: 4개의 질문을 진행하기전에 다른 사람들은 보통 어떻게 해? 조사한번 하고 다시 질문해줘.

그래서 첫 답은 잠정으로 두고 웹을 조사했다(GitHub 보호 브랜치·자동 삭제 문서는 WebFetch 요약, 나머지는 검색 결과 요약). 조사 결과를 선택지 설명에 넣어 같은 네 질문을 다시 물었고, 사용자는 첫 화면과 같은 답을 골랐다. 받은 답(라벨과 설명 글자 그대로)은 아래와 같다.

- (가) main 보호: **보호를 끈다 (Recommended)**. "조사: Git Flow 팀은 보통 dev→main과 main→dev를 병합 커밋으로 합치고, 오래 사는 두 브랜치 사이를 squash로 합치면 출시마다 충돌이 되풀이된다는 경고가 많습니다. GitHub 문서상 이 보호는 squash·rebase만 받으므로, 병합 커밋을 쓰려면 끄는 것이 일반적입니다. 치르는 값: 티켓 PR을 squash로 합치는 규칙을 GitHub가 강제하지 않고 스킬 지침(merge.md)만 지킵니다."
- (나) dev 보호: **보호하되 엄격 모드는 끈다 (Recommended)**. "verify 통과를 필수로 두고, 엄격 모드와 선형 이력 강제는 끕니다(되돌려 합치기는 병합 커밋이기 때문입니다). 조사: GitHub 문서상 보호 규칙은 자동 삭제를 막을 수 있어, 출시 PR 병합 뒤 dev가 지워지는 일도 막을 것으로 봅니다(어림). 엄격 모드는 PR마다 갱신을 되풀이게 한다는 지적이 많고, 그 대안인 병합 대기열은 개인 계정 저장소에서 쓸 수 없다고 알려져 있습니다(어림). 치르는 값: 옛 기준으로 통과한 PR이 병합될 수 있고, dev 푸시에서 도는 CI가 뒤늦게 잡습니다."
- (다) LLM 테스트: **넣겠다, 잡은 후속 티켓으로**. "조사: 흔한 방식은 PR마다 모의 테스트만 돌리고, 실제 모델 테스트는 main이나 출시 직전에 돌리며, 키는 그 잡에만 주는 것입니다. 새 게이트는 처음에 막지 않는 참고 모드로 돌려 흔들림을 먼저 재 보라는 권고도 있습니다. 이 티켓은 후속 티켓 ci-llm-job을 쓰고 그 권고를 티켓에 적습니다. 시크릿은 그 티켓이 돌기 전에 넣으시면 됩니다."
- (라) 기본 브랜치: **dev로 옮긴다 (Recommended)**. "조사: GitHub 문서상 기본 브랜치는 새 PR의 기본 대상이고, Git Flow에서는 develop을 기본으로 두어 기능 PR이 저절로 develop으로 가게 하는 경우가 많습니다(출처에서 끌어낸 추론). 사용자 수준 스킬 git-pr·git-branch도 base를 dev로 알아볼 가능성이 큽니다(스킬 본문을 다시 재지 않은 어림). 치르는 값: 각 체크아웃에서 git remote set-head origin dev를 쳐야 /security-review가 dev와 견주고, 핫픽스 PR은 base를 main으로 직접 줘야 합니다."

실행 승인: dev 따기·dev 보호·main 선형 이력 끄기·기본 브랜치 dev·`git remote set-head origin dev` 일곱 명령을 이 세션이 실행해도 되는지 물었고, 사용자는 **실행한다 (Recommended)**를 골랐다. 그 설명은 "일곱 명령을 순서대로 하나씩 실행하고, 매 단계의 출력을 확인한 뒤 다음으로 넘어갑니다. 이 워크트리의 공통 git 폴더가 주 체크아웃의 .git이라(git rev-parse로 확인), 이 워크트리의 fetch와 set-head가 같은 클론의 다른 워크트리에도 반영될 것으로 봅니다(어림이며 실행 뒤 주 체크아웃에서 확인합니다)."였다. dev 보호를 `tools/protection.json`에 키로 더하지 않고 `tools/protection-dev.json`으로 따로 둔 것은 그 파일이 `gh api --input`이 읽는 브랜치 하나의 본문이기 때문이다(KICKOFF.md 8단계를 읽었다).

질문을 올리기 전에 대 본 것: `gh api`로 main 보호(`required_linear_history` 켜짐, `enforce_admins` 꺼짐, strict 켜짐, 필수 검사 `verify`), 저장소 설정(기본 브랜치 main, `delete_branch_on_merge` 켜짐, 세 병합 방식 모두 허용), 사용자 계정의 관리자 권한을 읽었다. 워크플로 트리거는 `.github/workflows/*.yml`을 grep해 push와 pull_request뿐인 것을 봤다.

## 체크아웃 정리

첫 턴에 주 체크아웃 세션에서 `tidy-checkouts`를 돌고 `EnterWorktree(name: dev-branch-create)`로 들어왔다. 그 보고를 그 턴에 옮기지 않아(대기열 0576의 2회차), 회고 때 대화 기록을 grep해 되찾은 것만 적는다. `judge`의 줄은 모두 `남긴다`였다. 까닭은 병합된 PR이 없다(`01-shared-markdown-component`, `admin-style-spec` 등), 바뀐 파일이 있다(`03-default-model-plugin-and-explicit-flag`, `06-round-drive-record` 등), 그 폴더를 쥔 프로세스가 있다(`answer-markdown-tickets`, `local-model-design` 등), 앱의 표지가 있다(`confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`), 그 브랜치의 세션이 돈다(`dev-base-skills-docs`)였다. 지운 것은 없다. 루트를 당긴 앞뒤 커밋은 되찾지 못했다.

## 실행한 것

일곱 명령을 하나씩 치고 출력을 본 뒤 다음으로 넘어갔다. 명령과 출력은 티켓의 결과 1·2에 있다. 요지는 `origin/dev`와 `origin/main`이 모두 `82297e614`(`git ls-remote`), main 보호의 선형 이력 꺼짐, dev 보호(`tools/protection-dev.json`) 적용, 기본 브랜치 dev, `origin/HEAD -> origin/dev`다. 주 체크아웃의 공유 ref 파일 `C:\project\agent\.git\refs\remotes\origin\HEAD`도 Read로 열어 `ref: refs/remotes/origin/dev`를 봤다(워크트리 가드가 `git -C <주 체크아웃>`을 거부해서다).

헌법 판을 3.0.86에서 3.0.87로 올렸다. `operations.md`의 가드레일(보호 브랜치 줄), 브랜치와 병합(거절 문장), 리뷰 파이프라인(`origin/HEAD` 문단)의 문구를 사용자의 네 답에 맞춰 고쳤고, 원칙이나 절을 더하지 않은 문구 수정이라 patch다.

## 셀프 리뷰

`/code-review`. base `82297e614`(`git merge-base origin/dev HEAD`), 수정 파일 13개, 커밋 0개, 미추적 3개(`ci-llm-job.md`, 이 일지, `tools/protection-dev.json`). 표준 축은 sonnet·high, 명세 축은 상속 모델이다. 두 브리프에 주장 검증 10항, 갈래 밟기, 외부 근거 발췌(GitHub 보호 브랜치·자동 삭제 문서의 웹 요약)를 실었다.

### 표준 축 보고

- Major 1. 기본 브랜치를 dev로 옮겼는데 핫픽스 PR의 base를 main으로 열라는 말이 살아 있는 문서에 없다. `gh pr create`와 사용자 수준 `git-pr`은 base를 원격 기본 브랜치에서 잡으므로 핫픽스 PR이 dev로 열린다. 사용자에게 보인 (라)의 설명에는 그 값이 있는데 규약에 옮기지 않았다.
- Minor 2. `operations.md` 리뷰 파이프라인의 "Claude Code Review는 자기 워크플로 파일이 기본 브랜치와 다르면 건너뛴다"가 기본 브랜치 dev에서 새로 걸린다. dev와 main의 그 파일이 갈라지면 핫픽스 PR과 되돌려 합치기 PR의 리뷰가 건너뛰어질 수 있다.
- Minor 3. `rag-engine-port-by-hand.md` 본문의 "지시문을 내는 자리는 plan-head의 dev 전환 문단과 release-image 기능 계획 본문"은 plan-head 문단을 이 변경이 걷어 반쯤 낡았다.
- Minor 4. 자동 삭제 문장의 근거 문서는 "can also prevent"라고만 하고 어느 설정이 막는지 말하지 않는다. 문장은 "보호 브랜치라서"로 적었다.
- Minor 5. 가드레일의 보호 브랜치 문장이 선형 이력을 끈 까닭과 strict를 끈 까닭을 한 문장에 섞었다.
- Minor 6. 일지에 "다음"과 판을 올린 까닭이 없다. 판 올림은 patch가 맞다.
- Minor 7. 티켓이 done인데 수용 기준 셋이 비었다.
- 맞은 것: `origin/HEAD`와 공통 git 폴더, `base_ref`의 두 반환값, `claude-code-review.yml`의 건너뛰는 조건, `hook_prompt_directive` 문구, 둘째 출시 PR부터의 `BEHIND` 어림(첫 출시는 안 난다), `/security-review`의 커밋 목록이 대칭차라 dev 커밋이 섞인다는 추정(diff는 merge-base부터라 영향이 없다, "범위"가 커밋 목록이라고 밝히면 낫다), rag-engine 지시문의 도구 이름·기본 브랜치·ADR 0015, `plan_table.py --check`, `git diff --check`.

### 표준 축 판정

- 1은 고친다. `gh pr create --help`가 "If not configured, the repository's default branch will be used"라 적고, 사용자 수준 `git-pr` 2단계가 base를 원격 HEAD로 감지한다(그 파일을 Grep으로 읽었다). 프로젝트 스킬에는 핫픽스 PR을 여는 절차가 없어서, PR을 여는 줄이 있는 `operations.md` 브랜치와 병합에 적는다.
- 2는 고친다. 이 변경이 기본 브랜치를 옮겨 생긴 갈래이고 문장 하나로 닫힌다.
- 3·5는 고친다. 4는 문장을 근거 문서가 말한 만큼으로 줄인다. `allow_deletions:false`가 막는다고 좁히면 근거 없는 새 주장이 되므로 그 설정은 "두 파일 모두 그렇다"는 사실로만 둔다.
- 6·7은 이 단계의 남은 일이다(일지 "다음"과 PR 뒤의 상자).
- 맞은 것의 "범위" 표현은 고친다(커밋 목록이라고 밝힌다).

고친 것(새로 쓴 사실 문장의 원문. PR 직전 리뷰에 밀 주장으로 넘긴다):

- `operations.md` 브랜치와 병합: "그 사용자 수준 스킬과 `gh pr create`는 base를 따로 주지 않으면 원격의 기본 브랜치로 잡고, 원격의 기본 브랜치는 2026-11-12부터 dev다(`gh pr create --help`와 `git-pr` 2단계를 읽었다). 그래서 핫픽스 PR은 base 감지에 맡기지 않고 `gh pr create --base main`으로 연다."
- `operations.md` 리뷰 파이프라인 초록 착시: "기본 브랜치가 dev가 된 2026-11-12부터는 dev의 그 파일과 비교하므로, dev에서 그 파일을 바꾼 뒤 출시 PR로 main에 올리기 전까지는 main에서 딴 핫픽스 PR과 머리가 main인 되돌려 합치기 PR도 건너뛸 것으로 본다(PR #3·#6에서 본 동작에서 끌어낸 어림이고, 기본 브랜치 dev로는 재 보지 않았다)."
- `operations.md` 가드레일: "dev가 strict가 아닌 것은, strict이면 dev에 main에 없는 커밋이 있는 동안 머리가 main인 되돌려 합치기 PR이 뒤처진 것으로 막히기 때문이다."
- `operations.md` 리뷰 파이프라인 2: "대칭차인 커밋 목록에 main에 없는 dev의 커밋이 들어갈 것이므로(diff는 merge-base부터라 dev의 커밋이 들지 않는다. …)"
- `merge.md` 병합 방법: "GitHub 자동 삭제 문서(웹 요약)는 보호 규칙이 자동 삭제를 막을 수 있다고만 하고 어느 설정이 막는지는 말하지 않으며, 두 파일은 모두 삭제를 막는다(`allow_deletions: false`)."
- 티켓 결과 5의 rag-engine 지시문 (3): "그 뒤로 base를 주지 않은 gh pr create는 dev로 열리므로 핫픽스 PR은 --base main으로 연다."
- `rag-engine-port-by-hand.md`: "앞의 것은 1회차로 냈고, 뒤의 것을 내는 자리는 `.scratch/release-image/plan.md`의 본문이 적는다."

### 명세 축 보고

Critical·Major 없음, Minor 여섯, Nit 일곱.

- Minor 1. `ci-llm-job.md`가 "`verify`의 `needs`에 잇는다", "dev로 가는 티켓 PR에서는 돌지 않는다", "막지 않는 참고 모드"를 함께 적는다. `verify`는 건너뛴 잡도 빨강으로 보므로(ci.yml 331~333행) 글자 그대로면 모든 dev PR이 빨갛고, 참고 모드도 needs에 이은 잡과 맞지 않는다. `ticket` 잡처럼 한 줄 찍고 지나는 꼴(305행)이나 `continue-on-error`를 적어야 한다.
- Minor 2. rag-engine 지시문의 "아래 파일은 agent-os의 origin/dev에 있으니"는 지금 사실이 아니다. origin/dev에 `tools/protection-dev.json`이 없고 `protection.json`은 선형 이력이 켜진 판이다.
- Minor 3. `tools/hook_push_behind_main.py`의 12행 독스트링과 280행 차단 문구 "strict 보호라 병합 전에 어차피 {base} 를 합쳐야"는 기준이 dev일 때 거짓이다(작업 규약 4).
- Minor 4. `KICKOFF.md` 371행의 "strict, 선형 이력"이 300행이 복사하라는 `protection.json`(이제 선형 이력 false)과 어긋난다.
- Minor 5. `rag-engine-port-by-hand`가 가리키는 plan-head 문단을 이 diff가 걷었다(표준 축 3과 같다).
- Minor 6. 자동 삭제의 웹 요약은 "can also prevent"이고 막는 값은 `allow_deletions:false`다. 출시 PR은 `merge.md` 3(`ls-remote`)을 건너뛰므로 dev가 지워져도 알아채지 못하고, `fetch --prune` 뒤 `base_ref`가 조용히 main으로 돌아간다. `dev-release-pr-step` 메모에 첫 출시 PR 뒤 `ls-remote` 확인을 넣기를 권한다.
- Nit. (c) "다른 클론은 … 쳐야 바뀐다"는 넓다. 기본 브랜치를 바꾼 뒤 새로 만든 클론은 이미 dev다 / `dev-release-pr-step`의 "빨리 감기로 된다"는 PR과 `--merge`로만 합치는 `merge.md`에서는 merge 커밋이 생긴다 / `ci-llm-job`의 인용 "LLM 호출 테스트는 돌리지 않는다"가 원문과 글자가 다르고 "일지의 조사 절"이 일지에 없다 / 지시문 (4)의 "임시 저장소 측정"은 스크래치패드 스크립트이고 커밋한 프로브(`backmerge_diff_check.sh`)는 그 장면을 재지 않는다 / "되돌려 합치기" 끝 줄이 보호 설정 거절을 빠뜨렸다 / 명세 (나)의 "`protection.json`에 더한다"를 별도 파일로 바꾼 것은 근거가 있어 받아들일 만하다 / What to build의 "이 시차를 PR 본문에 적는다"를 추적하는 줄이 결과 절에 없다.
- 확인됨: 원격 상태와 두 JSON, 기본 브랜치, `ls-remote` / (b) 추론(첫 출시 PR은 dev가 main을 품는다) / (c)의 공유 / (d) release-image의 판 내기 지시문 문장은 남고 plan-head 문단은 걷혔다 / (e) 셋 가운데 둘을 맞췄고 일지 "다음"은 아직이다 / (f) 얇은 ADR 요건과 rag-engine의 도구 여섯·워크플로 둘·`grill-with-docs` / `plan_table --check` 0, `base_ref` 경계 입력 다섯.

### 명세 축 판정

- Minor 1은 고쳤다. `ci.yml`을 다시 읽으니 `needs`에 없는 잡도 `verify`가 빨강으로 본다(334~338행 주석). 그래서 `ci-llm-job`의 첫 항목을 "늘 돌고 대상이 아니면 한 줄을 찍고 지나거나, 참고 모드 동안은 `needs`에 잇지 않고 차집합 예외에 더한다"로 고치고, dev PR의 `verify`가 빨개지지 않는다는 수용 기준을 더했다.
- Minor 2는 고쳤다. 결과 5에 "이 PR이 dev에 병합된 뒤에 주라고 사용자에게 알렸다"와 그 까닭(`git cat-file -e`가 128, `git show`가 옛 판)을 더했다. 사용자가 세션 중에 "rag-engine 저장소에 지금 지시해?"라고 물어 같은 까닭으로 병합 뒤에 주라고 답했다.
- Minor 3은 고쳤다. `tools/hook_push_behind_main.py`의 독스트링과 막는 문구를 main은 strict, dev는 규약으로 나눠 적었다. 판정은 바꾸지 않았고, dev에서도 막을지는 다시 정하지 않았다고 독스트링에 적었다. 변이 표(`push_behind_hook_mutations.toml`)의 대조군이 찾는 "지금 푸시하면 CI 가 한 번 더 돈다"는 한 줄에 남겼다. `uv run pytest -q tests/tools/test_hook_push_behind_main.py`가 80 passed.
- Minor 4는 고쳤다. `KICKOFF.md` 8단계에서 "선형 이력"을 빼고 껐다는 문장을 더했다.
- Minor 5는 표준 축 3과 같아 이미 고쳤다. Minor 6은 표준 축 4와 같이 고쳤고, 권고대로 `dev-release-pr-step`에 첫 출시 PR 뒤의 `ls-remote` 확인을 메모와 수용 기준으로 넘겼다(받는 쪽은 `dev-branch-create`가 병합된 뒤에 하는 티켓이다).
- Nit은 여섯을 고쳤다. (c)는 "기본 브랜치를 옮기기 전에 만든 다른 클론"으로 좁히고 `git ls-remote --symref origin HEAD`가 `ref: refs/heads/dev`인 것을 봤다. 빨리 감기 괄호를 merge 커밋이 생긴다는 말로 바꿨다. `ci-llm-job`의 인용을 행 번호 가리킴으로, "일지의 조사 절"을 실제 절 이름으로 바꿨다. 지시문 (4)를 "손으로 본 것과 어긋났다(커밋한 프로브는 없다)"로 바꿨다. "되돌려 합치기" 끝 줄에 보호 설정 거절을 더했다. 시차를 PR 본문에 적는다는 줄을 결과 4에 더했다. 별도 파일로 바꾼 것은 고치지 않는다.

고친 것 가운데 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장으로 넘긴다):

- `ci-llm-job.md`: "`needs`에 없는 잡도 `verify`가 빨강으로 본다(334~338행의 주석. 일부러 밖에 둘 잡은 그 차집합의 예외에 이름을 더한다)."
- `hook_push_behind_main.py` 독스트링: "dev 는 strict 가 아니지만(`tools/protection-dev.json`, 2026-11-12) 사용자 수준 `git-pr` 2단계가 base 가 앞섰으면 푸시 전에 rebase 하게 하고, 이 훅도 dev 에서 같은 판정으로 막는다."
- `operations.md` 리뷰 파이프라인 2: "그 뒤에 만든 클론(클라우드 세션의 클론 등)은 `git clone`이 원격의 HEAD(…)를 따라 dev일 것으로 본다(git의 동작에서 끌어낸 어림이고 새 클론으로 재 보지 않았다)."
- `dev-release-pr-step.md`: "출시 PR은 `merge.md` "워크트리에서 병합할 때" 3(원격 정리의 `ls-remote`)을 건너뛰므로 다른 자리에서는 dev가 지워져도 알아채지 못하고, 그 뒤 `fetch --prune`이 `origin/dev`를 걷으면 기준 브랜치 규칙(`tools/base_rule.py`)이 조용히 main으로 돌아간다."
- `KICKOFF.md`: "agent-os는 처음에 켰다가, dev 전환 뒤 출시 PR(dev→main)을 merge 커밋으로 받으려고 2026-11-12에 껐다."

다시 돌린 명령: 반영 전의 `uv run python tools/run_checks.py`(백그라운드)가 종료 0이었다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest 588초, web-verify 757초가 모두 Passed). 반영 뒤에는 `uv run pytest -q tests/tools/test_hook_push_behind_main.py`(80 passed), `uv run ruff check`·`ruff format --check`(고친 훅 파일), `uv run python tools/plan_table.py --check`(종료 0)를 쳤고, 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다. 결과는 커밋 뒤에 적는다.

## 카나리아

`uv run python tools/sibling_overlap.py`가 `merge.md`를 원천으로 드는 카나리아 명세 열 개를 알렸다. 그 열 개가 묻는 문장은 이 변경이 고치지 않은 자리라, 고친 보호 설정 문단을 묻는 명세 `.scratch/harness/probes/canary/dev_branch_create_merge_protection.toml`을 새로 썼다. 첫 판은 카나리아로 dev 보호 파일 이름을 골랐는데, 러너가 그 이름이 세션에 실리는 git 상태(이 브랜치의 새 파일)에 있다며 명세 오류로 돌리지 않았다. 문단에만 있는 구절 둘("어느 설정이 막는지는 말하지 않으며", `allow_deletions: false`)로 바꿔 돌리니 통과 4, "없음" 섞임 0이었다(claude 2.1.322, 실험군 3/3, 대조군 1/1은 두 물음 모두 "없음"). 나머지 열 개는 돌리지 않았다.

## 회고

후보 열하나. 승인 넷(회차로 세는 것 셋, 새 항목 하나), 기각 일곱, 넘김 없음. 만료할 항목은 작업 트리와 `origin/dev` 두 셈 모두 없었다.

1. **승인(회차, 0420의 13회차).** 기본 브랜치와 보호 설정을 바꾼 뒤 옛 표현이 살아 있는 문서에 남아 셀프 리뷰가 잡았다. `tools/hook_push_behind_main.py`의 "strict 보호라", `KICKOFF.md`의 "선형 이력", `rag-engine-port-by-hand`가 가리키던 plan-head 문단, 기본 브랜치 dev가 핫픽스 PR의 base와 claude-review의 비교 대상에 주는 영향이다. `CLAUDE.md` 작업 규약 4(구현 때 실리는 지침)를 어긴 것이라 회차로 센다. 그 항목은 이미 chore 계기(5회차 이상)다.
2. **승인(회차, 0580의 2회차).** 사람의 몫 넷(GitHub 보호, 기본 브랜치)을 물으며 다른 팀의 관행을 선택지에 싣지 않아, 사용자가 답 위에 조사를 요청했고 같은 넷을 다시 물었다. 0580은 같은 일을 하는 가장 가까운 선례를 선택지로 들라는 처방이라 같은 처방으로 보고, 구현 티켓의 질문 자리도 함께 보라고 어디로 줄에 더했다.
3. **승인(회차, 0576의 2회차).** 첫 턴의 `tidy-checkouts` 보고를 그 턴에 일지로 옮기지 않아, 압축 뒤 대화 기록을 grep해 되찾았고 루트의 앞뒤 커밋은 끝내 되찾지 못했다. 열린 항목이 이미 처방한 사건이다.
4. **승인(새 항목 `cross-repo-directive-before-merge`, 1회차).** rag-engine 지시문을 이 PR이 병합되기 전에 내면서 언제 주라는 말을 붙이지 않아 사용자가 "rag-engine 저장소에 지금 지시해?"라고 물었다. 지시문이 읽으라는 파일은 그때의 `origin/dev`에 없었다. 같은 처방의 열린 항목이 없었고(`queue_open_rows.py --search 지시문 --search rag-engine --search 병합.뒤에`), 방향이 반대인 `external-ref-moved-while-citing`과 서로 가리키게 적었다. 더하는 것이라 회차만 센다.
5. **기각.** `ci-llm-job`의 `needs`와 건너뛰기가 `verify` 판정과 어긋난 것은 새로 쓴 사실 문장이 근거를 열지 않은 것이고, 명세 축 브리프의 주장 검증이 잡도록 둔 기준이라 리뷰가 제 몫을 했다. 검사로 옮길 길이 없다.
6. **기각.** `hook_choice_facts`가 처음 보는 선택 화면을 세 번 막았다. 훅이 설계대로 막고 사실 확인 뒤 다시 불러 지났다.
7. **기각.** Grep의 glob이 `.env`에 닿아 `hook_env_read`가 막았다. 이미 있는 훅이 그 자리에서 막았다.
8. **기각.** 워크트리 가드가 `git -C <주 체크아웃>`을 거부했다. `CLAUDE.md` 환경 함정에 있는 앱 가드이고, 공유 ref 파일을 Read로 열어 대신 봤다.
9. **기각.** 파이프를 쓴 판정 명령과 영어 중간 문장에 훅 경고가 붙었다. 이미 있는 훅이 알렸다.
10. **기각.** `hook_measure_word`가 새 문장의 "실측"을 짚었다. 이미 있는 훅이 알려 그 자리에서 고쳤다.
11. **기각.** 반영 전 `run_checks`가 약 13분(web-verify 757초)이었다. 절차를 따른 비용이고 0334에서 이미 다뤘다.

## 다음

이 PR(base dev)을 병합한 뒤 `next-session`이 다음 지시문을 낸다. 이어받을 것:

- **풀린 일.** release-image 기능은 dev 전환을 기다리지 않는다(`.scratch/release-image/plan.md`). harness 티켓 `ci-llm-job`(ready-for-agent)은 시작할 때 사용자에게 시크릿을 넣었는지 먼저 묻는다. harness 티켓 `dev-release-pr-step`은 이 PR이 병합된 뒤에 하며, 그 메모에 main strict 때문에 둘째 출시 PR부터 `BEHIND`가 날 것이라는 어림과 첫 출시 PR 뒤의 `ls-remote` 확인이 있다.
- **다른 체크아웃.** 기본 브랜치를 옮기기 전에 만든 다른 클론은 `git fetch origin`과 `git remote set-head origin dev`를 친다. 이 PC의 주 체크아웃은 루트가 아직 main이고, 다음 `tidy-checkouts`의 "main인데 루트 브랜치는 dev다" 갈래가 dev로 옮긴다.
- **rag-engine 지시문.** 티켓 결과 5의 글을 이 PR이 dev에 병합된 뒤에 사용자가 그 저장소의 새 세션에 준다.
- **사용자에게 다시 묻는 것.** 사용자 수준 스킬 넷(`git-pr`, `git-pr-merge`, `git-pr-feedback`, `git-branch`)을 고칠지. 기본 브랜치가 dev가 되어 `/git-pr`은 base를 dev로 감지하지만, `/git-pr-merge`는 squash와 `--delete-branch`로 병합한다. 일반적인 문장으로 고치는 길과 프로젝트 사본으로 덮는 길을 함께 보인다.
- **사용자 승인이 필요한 것.** ADR 0043 33행("잊으면 다음 dev→main에서 hotfix가 사라진다")은 임시 저장소로 손으로 본 것과 어긋난다. 개정은 ADR 이력과 사용자 승인으로 한다.
- **정하지 않은 것.** `tools/hook_push_behind_main.py`가 dev에서도 뒤처진 푸시를 막을지는 dev가 strict가 아니게 된 뒤 다시 정하지 않았다(그 독스트링).
- **chore 계기.** 대기열 0420이 13회차다.
