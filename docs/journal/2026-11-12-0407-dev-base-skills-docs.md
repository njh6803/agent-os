# 2026-11-12 (04:07) 스킬·규약 문서·ADR 포인터를 기준 브랜치 규칙에 맞추고 핫픽스 되돌려 합치는 순서를 merge.md에 적는다

세션 제목 `chore/dev-base-skills-docs`(인계 뒤 `chore/dev-base-skills-docs (인계함)`). 브랜치 `chore/dev-base-skills-docs`, 워크트리 `.claude/worktrees/dev-base-skills-docs`, 티켓 `.scratch/harness/issues/dev-base-skills-docs.md`. 모델 `claude-sonnet-5-5` / high. 이 일지는 컨텍스트가 인계 문턱(20만 토큰)을 넘어 셀프 리뷰 직전에 넘기며 지금까지를 적은 것이고, 인계받은 세션이 아래 "셀프 리뷰"와 "회고"와 "다음"을 이어 썼다.

## 사용자 프롬프트

세션의 첫 메시지이자 유일한 사용자 메시지다. `implement` 스킬을 이 티켓에 대고 돌리라는 지시문이다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 인자: .scratch/harness/issues/dev-base-skills-docs.md
> 다음 작업: .scratch/harness/issues/dev-base-skills-docs.md. 스킬·규약 문서·ADR 포인터를 기준 브랜치 규칙에 맞추고 핫픽스 되돌려 합치는 순서를 merge.md에 적는다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 3 중 3. EnterWorktree로 먼저 들어가 거기서 브랜치를 바꾼다 / 브랜치: chore/dev-base-skills-docs / 모델: Sonnet 5.5 / high / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 사용자 수준 스킬(~/.claude/skills)을 고칠지는 사용자에게 묻는다 / 이번 요청 범위: PR과 병합까지

## 한 것

티켓의 수용 기준 여섯을 다음과 같이 채웠다. 티켓 파일 끝의 `## 결과`에 표와 근거가 있다.

- 스킬·규약 문서·`CLAUDE.md`·`CONTEXT.md`·`PULL_REQUEST_TEMPLATE.md`의 `main`을 곳마다 뜻을 가려 기준 브랜치(`hotfix/*`는 main, 그 밖은 `origin/dev`가 있으면 dev, 없으면 main)나 루트 브랜치로 바꿨다. 바꾼 파일은 `git status`가 원천이다.
- `next-session` `merge.md`에 "병합 방법" 표와 "되돌려 합치기" 절을 더했다. (가) PR로 한다(머리 main, base dev, merge 커밋). (나) 계기는 `merge.md` 병합 길과 결정표 첫 줄이고 훅은 바꾸지 않는다. 판정 `git diff --quiet origin/dev...origin/main`은 임시 저장소 프로브 일곱 장면에서 기대대로였다(`.scratch/harness/probes/backmerge_diff_check.sh`).
- "루트 브랜치"를 새로 정해 `CONTEXT.md`에 올렸다. `tidy-checkouts` 2에 "main인데 루트 브랜치는 dev다" 갈래를 더했다.
- 사용자 수준 스킬 `git-pr`, `git-pr-merge`, `git-pr-feedback`, `git-branch`는 읽기만 했고 줄 번호 목록을 티켓에 적었다. 고칠지는 마무리 보고에서 사용자에게 묻는다. 승인 없이는 고치지 않는다.
- 새 티켓 `dev-release-pr-step`(출시 PR을 여는 계기와 순서, ready-for-agent)을 쓰고 `dev-branch-create`의 사람의 몫에 (라)를 더했다.
- 헌법 판을 3.0.86으로 올렸다(`docs/constitution/README.md`, 문구 수정). `tools/sibling_overlap.py`가 겹침 없음에 끝난다(종료 코드 0).
- 바꾼 하네스 파일 열둘의 카나리아 명세를 `.scratch/harness/probes/canary/dev_base_*.toml`로 새로 쓰고 `claude -p`(2.1.322)로 돌렸다. 모두 통과 4다. 첫 판 둘이 실패했다(ADR 규칙 명세는 카나리아가 `CLAUDE.md`에도 있어 대조군이 흘렸고, 결정표 명세는 엉뚱한 칸을 물었다). 둘 다 질문과 카나리아를 고쳐 다시 돌려 통과했다. open-session 명세는 "없음" 섞인 통과가 둘이다. 결과 줄은 각 명세의 `# 최신 결과:`와 티켓 결과 절에 적었다.
- 검증: `uv run ruff check .`와 `ruff format --check .`는 초록이다. 새 세션의 확인으로 `next-session`·`tidy-checkouts`·`code-review`·`open-session`·`retro`·`sync-design-system`을 Skill로 불러 고친 문구가 실리는 것을 봤다.

근거의 종류. 되돌려 합치기 판정은 프로브 `backmerge_diff_check.sh`가 단언한 것이다. 카나리아 통과는 `tools/canary.py`의 집계 줄이 찍은 것이고, 답은 손으로 읽었다. 새 세션의 스킬 로드는 `claude -p --model claude-sonnet-5-5`의 출력을 손으로 읽은 것이다. ruff 둘은 명령의 출력이다. `run_checks.py`와 `/code-review`는 아직 돌리지 않았거나 결과를 받지 못했다. `merge.md`의 BEHIND 갈래는 이 저장소에서 본 적이 없고 `tools/protection.json`과 ADR 0043을 읽은 것이다.

## 이 세션이 번복하거나 고친 것

- `docs/constitution/operations.md` 31행의 `--base origin/main` 명령은 기록이라 고쳤다가 되돌려 그대로 두었다.
- `.claude/rules/adr.md`의 첫 Edit이 원문 오타로 실패해 `git diff --merge-base origin/main` 줄만 대상으로 다시 고쳤다.
- 티켓 수용 기준의 검증·사용자 질문 칸은 실제 수행 전에 `[x]`로 체크했다. 이 일지를 받은 세션이 검증 결과(아래 "남은 일")를 본 뒤에도 그대로 맞는지 확인한다.

## 남은 일 (이 일지를 받는 세션이 이어 간다)

- 백그라운드로 돌던 `uv run python tools/run_checks.py`는 인계 전에 멈췄다. 결과를 받지 못했다. 새 세션이 `uv run python tools/run_checks.py`를 처음부터 다시 돈다(타임아웃 600000이거나 백그라운드. 다른 세션이 돌면 600초에 닿으니 백그라운드로 넘어가면 다시 치지 않는다).
- `/code-review`(셀프 리뷰)를 한다. 고정점은 기준 브랜치 `origin/main`이다(`origin/dev`는 아직 없다). 스킬을 불러 두 축을 돈다.
- 일지 "다음"은 단계를 닫는 세션이 쓴다. 이 티켓은 PR과 병합까지가 요청 범위이므로 병합 전에 retro와 "다음"을 마친 일지를 푸시한다(`merge.md` 3).
- 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`를 다시 친다.
- 커밋 메시지에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`, PR 본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`를 단다.
- 병합 뒤 `tidy-checkouts`와 `next-session`, 보고에 "주 체크아웃 미갱신: 루트는 main" 한 줄, 그리고 사용자 수준 스킬 네 개를 고칠지 묻는 질문(`wrap_up`)을 넣는다.

## 셀프 리뷰 (인계받은 세션이 돈 `/code-review`)

범위: base `cd77e4096`(origin/main), 커밋 0개, 수정 21개, 미추적 15개. 표준 축은 sonnet·high 서브에이전트, 명세 축은 이 세션의 모델을 이은 서브에이전트가 돌았다.

### 명세 축 보고 (받은 턴에 옮김)

충족: 스킬·문서 목록이 모두 diff에 있고, ADR 0005·0037 포인터는 base에 이미 있었으며 `check_adr_pointers.py`는 0으로 끝났다. `backmerge_diff_check.sh`를 서브에이전트가 다시 돌려 일곱 장면이 기대대로(measured 7, wrong 0)였다. 결과 표와 diff가 일치한다.

지적(Major 후보 1~5, Minor 6):

1. 결정표 첫 줄(되돌려 합치기)이 "이 세션"으로 끝나고 합치기를 마친 뒤 원래 다음 작업(티켓·프론티어 줄)으로 돌아가는 길이 없다. 다른 PR을 병합한 세션이 이 줄을 고르면 원래 지시문이 나오지 않는다. "작업을 마치지 못한 채 끊는다" 줄과 `handoff.md` 인계도 이 줄에 선점된다.
2. 합치기를 사용자에게 넘긴 뒤(`CONFLICTING`·`BEHIND`) diff가 계속 1이라 이후 모든 next-session이 첫 줄을 다시 고른다. "열린 PR이 있고 사용자에게 넘겼으면 건너뛴다"는 조건이 첫 줄에 없다.
3. dev가 아직 없을 때 핫픽스를 병합하면 막힌다. `merge.md`는 핫픽스면 "되돌려 합치기까지 해야 끝"인데 "되돌려 합치기" 1에 `origin/dev`가 없을 때의 갈래가 없고 5의 판정은 128로 끝나 0이 될 수 없다.
4. "병합 방법" 표의 핫픽스 행 "3~5, 그 뒤 되돌려 합치기"에서 5(다음 브랜치를 `origin/dev`에서 딴다)가 합치기 전에 돌아 핫픽스가 빠진 dev에서 딴다. 5의 "핫픽스면 `origin/main`"도 다음 브랜치가 핫픽스일 때인지 방금 병합한 PR이 핫픽스일 때인지 모호하다.
5. 거짓 주장. `merge.md`와 결정표 첫 줄에 "핫픽스가 dev에 없어 다음 출시 PR(dev→main)이 main의 핫픽스를 되돌린다/사라진다"가 새로 들어갔다. 임시 저장소로 쟀더니 핫픽스를 main에만 두고 dev를 `--no-ff`로 main에 합쳐도 핫픽스 파일이 남았다(스크래치패드 `hot.sh`, `ls`가 f g h). 실제 해는 dev가 핫픽스 없이 쌓이고 같은 곳을 고쳤으면 출시 때 충돌하는 것이다. ADR 0043 33행도 "사라진다"고 적었지만 ADR은 승인 없이 고치지 않으므로 사용자 보고에 넘긴다.
6. "되돌려 합치기" 2의 제목 `(<핫픽스 PR 번호>)`는 결정표 첫 줄로 들어온 다른 세션이 모르는 값이다. 4의 `--match-head-commit <main의 SHA>`도 그새 main이 앞서면 실패하는데 안내가 없다.

확인하지 못한 것: 수용 기준 "사용자에게 고칠지 물었다"는 묻기 전에 `[x]`로 체크됐다. 사용자 수준 스킬 네 개의 줄 번호는 읽기 범위 밖이라 재지 않았다. `claude -p` 확인과 카나리아 4/4 주장은 재 보지 않았다.

### 표준 축 보고 (받은 턴에 옮김)

서브에이전트가 `backmerge_diff_check.sh`를 돌려 7장면 wrong 0, 종료 0을 봤다. `check_ticket.base_ref`, `hook_push_behind_main.base_branch`, 훅의 `PROTECTED`와 독스트링, ADR 0043 인용, `origin/HEAD -> origin/main`은 서술대로 맞았다고 했다(`check_instructions.py`·`check_adr_pointers.py`는 파이프로 쳐서 종료 코드를 못 봤다고 적었다).

Major 후보:

1. 출시 PR(머리 dev, base main)이 `merge.md` 병합 길 4와 `operations.md`의 예외("base가 dev인 PR은 `/git-pr-merge`를 쓰지 않는다")에 들지 않아, 주 체크아웃에서 연 출시 PR이 `/git-pr-merge`(squash, `--delete-branch`)로 빠져 dev를 지울 수 있다. "머리가 dev인 PR도"를 예외에 넣어야 한다. 출시 PR과 되돌려 합치기 PR은 `delete_branch_on_merge`와도 부딪히고, dev 보호 여부는 `dev-branch-create`(나)에서 미정인데 `merge.md`가 이 의존을 적지 않았다.
2. "되돌려 합치기" 3의 대기: `tools/wait_ci.py`의 기본 `EXPECTED`가 verify·claude-review·CodeRabbit이라 봇 회차를 안 하는 이 PR에서 CodeRabbit이 요청되지 않은 채 `EXIT_CANNOT_WAIT`로 끝난다. `--expect verify`를 줘야 한다.
3. 결정표 첫 줄이 "끊을 때" 인계 갈래를 삼킨다(명세 축 1과 같다). 끝난 뒤 표로 돌아가는 문장이 없다.
4. dev가 아직 없는 갈래가 안 닫힌다(명세 축 3과 같다). 1에 dev 없음 갈래와 끝 줄 갈래가 없다.

Minor:

5. 표 머리말 "병합 명령에는 언제나 `--match-head-commit <HEAD>`"가 출시 PR(머리 dev)에는 `git rev-parse HEAD`와 다른 값이라 맞지 않는다. 출시 PR의 `--merge`가 main의 `required_linear_history`에 막힐 때의 처리가 `merge.md`에 없다(티켓 (가)에만 있다).
6. `tidy-checkouts` "main인데 루트 브랜치는 dev다" 갈래에 로컬 main에 원격에 없는 커밋이 있을 때의 처리가 없고, 3의 병합 판정은 여전히 `origin/main`만 본다(`dev-base-tools` 몫이라고 문서에 적었다).
7. 잔존: `.claude/skills/implement/SKILL.md:11`의 "main도 이 티켓의 브랜치도 아니거나, main인데" 조건이 루트 브랜치로 바뀌지 않았다. `.claude/rules/adr.md:17`에 "main에 이미 있던 같은 번호"가 남았다. 티켓의 가름 표에 이 둘이 없다.
8. 근거의 종류: `upload.md`의 "이미 올라간 색인이 이 꼴이다"는 `upload.test.ts` fixture 하나뿐이다. 티켓 수용 기준 `[x]` 둘("사용자에게 물었다", "검증 명령이 모두 초록이다")이 수행 전에 체크됐다.

smell: Duplicated Code(경미, 기준 브랜치 규칙 문장이 여러 파일에 되풀이)와 Shotgun Surgery(스킬 열두 파일)는 이 저장소의 "원천을 가리킨다" 관행에 맞는 의도된 분산이라 조치하지 않는다.

### 셀프 리뷰 반영

두 축이 같은 곳(결정표 첫 줄, "되돌려 합치기"의 dev 없음 갈래)을 짚어 합쳐 반영했다. 심각도는 `CODING_STANDARDS.md`가 원천이고 아래 1~8은 모두 고쳤다.

고친 것:

1. `merge.md` 병합 길 4와 `operations.md`의 `/git-pr-merge` 예외에 "머리가 dev인 출시 PR"을 넣고 까닭(그 스킬이 squash와 `--delete-branch`로 병합한다)을 적었다.
2. `merge.md` "병합 방법" 표 머리말을 `--match-head-commit <머리 SHA>`로 바꿨다. 티켓 PR과 핫픽스는 이 브랜치의 HEAD, 출시 PR과 되돌려 합치기 PR은 `gh pr view`의 `headRefOid`다. 워크트리 절 1의 대조도 같은 표를 가리킨다.
3. 표의 핫픽스 행을 "3과 4, 그 뒤 되돌려 합치기, 그 뒤 5"로, 5에 "방금 병합한 PR이 핫픽스였으면 되돌려 합치기를 마친 뒤에 딴다"를 더했다.
4. "병합 방법" 절에 보호 설정 문단을 더했다. `tools/protection.json`의 `required_linear_history: true`를 읽은 것이고, 자동 삭제가 머리 dev를 지우는지는 dev 보호가 서기 전에는 재 보지 않았다고 적고 `dev-branch-create`가 세우기 전에는 두 PR을 병합하지 않게 했다.
5. "되돌려 합치기": 1에 dev가 없을 때(`git ls-remote --exit-code --heads origin refs/heads/dev`가 2) 끝이라는 갈래를, 2의 제목에서 모르는 값 `(<핫픽스 PR 번호>)`를 걷고 `git log origin/dev..origin/main --oneline`으로 읽게, 3에 `uv run python tools/wait_ci.py <번호> --head <main의 SHA> --expect verify`를 (`tools/wait_ci.py`의 `EXPECTED` 기본값과 `--head`의 "없으면 로컬 HEAD"를 읽은 것이다), 4에 머리 SHA 불일치로 거절되면 새 `headRefOid`로 3부터 다시를, 끝 줄에 dev 없음과 사용자에게 넘긴 뒤 열린 PR이 남는다는 말을 더했다.
6. 거짓 주장을 고쳤다. "다음 출시 PR이 main의 핫픽스를 되돌린다/사라진다"를 "핫픽스 없이 dev가 쌓이고 같은 곳을 고쳤으면 출시 PR에서 충돌한다"로 바꿨다. 이 세션이 서브에이전트의 임시 저장소 스크립트(스크래치패드 `hot.sh`)를 다시 돌려 핫픽스를 main에만 두고 dev를 main에 `--no-ff`로 합쳐도 핫픽스 파일이 남는 것을 봤다(`ls`가 f g h, `git diff --quiet dev...main`은 1). 같은 줄 충돌은 측정하지 않았다. ADR 0043 33행의 "사라진다"는 ADR이라 고치지 않고 사용자 보고에 넘긴다.
7. `SKILL.md` 결정표 첫 줄에 "병합 뒤에만", 열린 PR(`gh pr list --base dev --head main --state open`)이 비었을 때만 고른다, 끝나면 표로 돌아가 원래 줄을 고른다, 끊을 때(인계 포함)는 이 줄을 고르지 않고 "이어받을 상태"에 적는다를 더했다.
8. 잔존 둘: `implement/SKILL.md` 11행의 조건을 루트 브랜치로, `.claude/rules/adr.md` 17행의 "main에 이미 있던 같은 번호"를 "기준 브랜치에 이미 있던"으로 바꿨다. `tidy-checkouts` 2의 "main인데 루트 브랜치는 dev다" 갈래에 로컬 main에 원격에 없는 커밋이 있으면 건드리지 않고 사람에게 넘긴다를 더했다.
9. 티켓 수용 기준의 `[x]` 둘을 사실에 맞췄다. 사용자에게 묻는 일은 병합 뒤 마무리 보고가 하므로 상자 문구를 "목록이 티켓 끝에 있다"로 좁혔다.

남긴 것과 이유:

- Minor 5의 `required_linear_history`가 출시 PR의 merge 커밋을 막을 때: `merge.md`에 "걸리면 병합하지 않고 사용자에게 넘긴다"로만 적었다. 풀지 정하는 것은 `dev-branch-create`(사람의 몫)다.
- `tidy-checkouts` 3의 병합 판정이 `origin/main`만 보는 것: `dev-base-tools`가 도구 독스트링에 정한다고 티켓 표에 이미 적었다.
- `upload.md`의 "이미 올라간 색인이 이 꼴이다"의 근거가 `upload.test.ts` fixture 하나뿐이라는 지적: 문장이 "이 꼴"이라고만 하고 개수를 세지 않아 주장 범위를 넘지 않는다고 보아 그대로 둔다.
- Duplicated Code·Shotgun Surgery(경미): 원천을 가리키는 저장소 관행에 맞는 의도된 분산이라 조치하지 않는다.

PR 직전 리뷰에 밀 새 주장(이번 반영으로 새로 쓴 사실 문장): (a) `tools/wait_ci.py`는 `--head`가 없으면 로컬 HEAD를 기다릴 헤드로 읽고 `--expect`를 주면 `EXPECTED` 기본값(verify, claude-review, CodeRabbit)을 갈음한다. (b) `git ls-remote --exit-code --heads origin refs/heads/dev`는 dev가 없으면 2로 끝난다. (c) `/git-pr-merge`는 squash와 `--delete-branch`로 병합한다(티켓 §5의 사용자 수준 스킬 표에서 옮긴 것이고 이 세션은 그 스킬 본문을 다시 열지 않았다). (d) `tools/protection.json`에 `required_linear_history: true`가 있다.

다시 돌린 명령(반영 뒤, 명령의 출력): `uv run ruff check .` 통과, `uv run ruff format --check .` 통과, `uv run python tools/run_checks.py` 종료 0(zizmor, check-ticket, lint-imports, check-type-escapes, check-instructions, pyright, pyright-linux, run-hooks, pytest, web-verify가 모두 Passed). 카나리아 명세 열둘의 expect 문구는 이번 반영이 건드리지 않은 문장에 있어 다시 돌리지 않았다(문구가 파일에 그대로 있는 것을 Grep으로 봤다. 둘은 백틱이 든 문장이라 같은 줄의 문구가 남은 것만 봤다). 반영으로 `implement/SKILL.md`를 새로 고쳐 `tools/sibling_overlap.py`가 카나리아 알림을 냈고, 새 명세 `.scratch/harness/probes/canary/dev_base_implement.toml`을 써 `uv run python tools/canary.py`로 돌렸다. 통과 4(실험군 3 가운데 둘이 "없음"으로 시작했다 정정한 섞임), 대조군은 "없음"이었다(도구의 집계 줄, 답은 손으로 읽었다).

## 회고

낸 후보 여섯, 판정은 승인 1, 기각 5, 넘김 0이다.

- 인계 직전에 하지 않은 일(검증 명령 전체, 사용자에게 묻기)의 수용 기준 상자를 `[x]`로 체크해 넘겼다. **승인**: 사건은 이 일지 "번복" 절의 셋째 줄이고, 셀프 리뷰 두 축이 지적해 이 세션이 되돌렸다. 층은 지침 한 문장(검사로 판정할 수 없다. 상자가 비어야 하는 때는 일을 마쳤는지에 달렸다). 되돌림은 PR 하나. 더하는 것이므로 지금은 반영하지 않고 대기열 `ticket-box-checked-before-action`에 1회차로 둔다.
- 핫픽스가 사라진다는 ADR 0043의 문장을 `merge.md`와 결정표에 옮겨 적었다. **기각**: 주장 검증 1·7이 잡도록 둔 기준을 어겨 리뷰가 잡았다. 리뷰가 제 몫을 했으므로 회차에서 뺀다. ADR 문장은 사용자 보고에 넘긴다.
- 결정표 첫 줄이 인계 갈래를 삼키고 dev가 없을 때를 닫지 못했다. **기각**: 갈래 밟기 문단이 잡도록 둔 기준이고 두 축이 잡았다.
- `wait_ci.py`의 기본 기대 이름과 `--head`가 머리가 다른 브랜치인 PR에 맞지 않았다. **기각**: 도구는 독스트링대로 돌고 쓰는 쪽(`merge.md`)의 안내가 빠졌던 것이다. 고쳤고 리뷰가 잡았다.
- Grep이 긴 줄을 `[Omitted long matching line]`으로만 내 줄을 따로 열어야 했다. **기각**: 훅이 알렸고 열린 항목이 있다(대기열 425).
- 인계 직전의 `run_checks.py`가 인계로 끊겨 결과를 못 받았다. **기각**: 일회성이고 일지가 "남은 일"로 넘겼으며 이 세션이 처음부터 다시 돌렸다.
- 대기열 점검: `tools/queue_open_rows.py`를 이 체크아웃과 `--ref origin/main`으로 돌려 만료할 항목 21개(0242, 0381, 0411, 0491, 0503~0505, 0507~0513, 0521, 0522, 0524~0526, 0529, 0534. 모두 승인 줄의 가장 늦은 날짜가 2026-10-28)가 두 출력에 모두 든 것을 보고 상태 줄을 고쳤다가, 커밋 전 `tools/sibling_overlap.py`가 열린 PR #536(`dev-review-bot-off`)이 같은 21개를 이미 고친다고 알려 되돌렸다(`git restore`). 같은 파일을 두 PR이 고치면 늦게 병합하는 쪽이 충돌 후보이기 때문이다. 이 PR은 만료를 닫지 않는다. 회차 5 이상인 열한 개는 chore 배치의 대상 그대로다. 새 항목 하나(`ticket-box-checked-before-action`)를 썼다.

## 인계: 커밋 뒤

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 커밋 뒤 경계에 왔다. 셀프 리뷰 반영, 전체 검증, 회고, 커밋(`551f50c91`, pre-commit 통과)까지 마쳤고 푸시하지 않았으며 열린 PR이 없다. 새 세션이 할 일은 PR 직전 리뷰(`coderabbit-review`, 밀 주장은 위 "셀프 리뷰 반영"의 (a)~(d)), 푸시, PR 열기(`/git-pr`), 봇 회차, 병합(`merge.md`의 워크트리에서 병합할 때)이고, 병합 뒤 `tidy-checkouts`와 `next-session`이다. 그리고 병합 뒤 마무리 보고에 "주 체크아웃 미갱신: 루트는 main" 한 줄과 사용자 수준 스킬 네 개를 고칠지 묻는 질문(`wrap_up`)을 넣는다. PR을 열기 전에 `uv run python tools/sibling_overlap.py`를 다시 쳐 PR #536(`dev-review-bot-off`)과 겹치는 파일이 없는지 본다(이 브랜치는 그 PR이 닫는 대기열 항목을 건드리지 않는다). 커밋 메시지는 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`, PR 본문 끝은 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`로 끝낸다.

## 다음

이 PR이 병합된 뒤의 일이다.

1. **사용자 수준 스킬 네 개(`git-pr`, `git-pr-merge`, `git-pr-feedback`, `git-branch`)를 고칠지 사용자에게 묻는다.** 줄 번호 목록은 티켓 `dev-base-skills-docs`의 결과 5에 있다. 사용자가 승인하기 전에는 고치지 않는다. 원격의 기본 브랜치를 어디에 둘지(`dev-branch-create` (라))와 얽혀 있다.
2. **`dev-base-tools`**와 **`dev-review-bot-off`**: 둘의 PR이 병합되는 대로 이어진다. 열린 PR #536(`dev-review-bot-off`)이 만료할 대기열 항목 21개를 이미 닫는다(이 PR은 닫지 않았다). 이 티켓이 넘긴 것은 티켓 결과 4에 있다(`tidy_checkouts`의 병합처, `hook_prompt_directive`의 안내 문구, `sibling_overlap`의 기준 브랜치 읽기, 되돌려 합치기 PR의 봇 회차).
3. **`dev-release-pr-step`**(`ready-for-agent`): 출시 PR(dev→main)을 여는 계기와 순서. `merge.md`는 그 PR의 병합 방법과 보호 설정에 걸릴 때의 처리만 정했다.
4. **`dev-branch-create`**: 위 티켓들이 병합된 뒤 `origin/dev`를 딴다. 사람의 몫(`required_linear_history`, dev 보호, 기본 브랜치)을 사용자에게 먼저 묻는다.
5. **병합 직후**: 이 PR을 워크트리에서 병합하면 주 체크아웃은 갱신되지 않는다. 새 세션이 `tidy-checkouts`를 먼저 돈다(`merge.md`).
6. **ADR 0043 33행("잊으면 다음 dev→main에서 hotfix가 사라진다")**: 임시 저장소 측정과 어긋난다(핫픽스가 다른 줄이면 출시 뒤에도 main에 남는다). 개정은 사용자 승인이 필요해 이 PR에서 고치지 않았다.

open-session을 부른다 2026-11-11T19:10Z
open-session을 부른다 2026-11-11T19:54Z
