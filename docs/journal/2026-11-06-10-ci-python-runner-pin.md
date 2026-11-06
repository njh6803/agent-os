# 2026-11-06 (10) CI의 python 잡을 ubuntu-24.04로 못 박는다(harness 045)

## 사용자 프롬프트

PR #479(docs/rag-engine-name)의 CI가 문서와 무관한 `python` 잡 실패로 막혔을 때, 그 세션이 원인을 알리고 해법을 물었다(경위는 일지 2026-11-06-11 "이어받은 세션(PR 반영·병합부터)". 이 일지가 쓰일 때는 2026-11-06-08이었고 이름순으로 뒤처지지 않게 11로 옮겼다).

> 사용자: (PR #479가 문서와 무관한 CI 실패로 병합되지 않습니다. CI 서버의 운영체제 이미지가 최근에 새 판(ubuntu-26.04)으로 바뀌어 검색 도구 ripgrep이 14.1.0에서 15.1.0으로 올라갔고, 14 판의 동작을 가정한 훅 테스트 한 건이 깨졌습니다. 어떻게 풀까요?) "러너를 24.04로 고정" — 설명: 이 워크트리에서 새 브랜치를 따서 ci.yml의 python 잡(ripgrep을 까는 유일한 잡)만 ubuntu-24.04로 고정합니다. main의 마지막 초록 실행(06:05 UTC)이 그 이미지였고, 이 PR의 실패 실행(07:46 UTC)이 26.04였습니다. 그 PR을 먼저 병합하고 #479에 main을 합쳐 다시 돌립니다. CI 한 바퀴가 이번 실행 기준 9분 32초라 그만큼 걸립니다. ripgrep 15에서 훅이 어떻게 다른지는 재 보지 않은 채 일지 '다음'에 별도 일로 적습니다.

## 한 일

티켓 `.scratch/harness/issues/045-ci-python-runner-pin.md`를 쓰고 `.github/workflows/ci.yml`의 `python` 잡 `runs-on`을 `ubuntu-latest`에서 `ubuntu-24.04`로 바꿨다. 까닭을 그 줄 위에 두 줄로 적었다. 다른 잡은 바꾸지 않았다. 원인과 근거(두 실행의 이미지와 ripgrep 판)는 티켓의 What to build와 일지 2026-11-06-11(옛 번호 08)에 있다.

근거의 종류. 두 실행의 `Image:`와 `Setting up ripgrep` 줄은 `gh run view <실행> --log --job <잡>`의 출력을 손으로 본 것이다. 26.04의 ripgrep 15.1.0에서 `{{.env}}`는 실패 로그의 단언 설명(`where True = _rg_reads_secret((['/usr/bin/rg'], None), …, ['--hidden', '--glob', '{{.env}}'])`)을 읽은 대로 겹친 묶음을 풀어 `.env`를 읽었다. 시험이 기대한 "훅이 더 넓게 막는다"가 아니라 둘이 같아져 실패한 것이다. 그 밖의 항목이 15에서 달라졌는지는 재지 않았다(통과한 6441개가 달라지지 않았다는 간접 근거뿐이다).

## 셀프 리뷰(기준 d0f5a195)

범위: base `d0f5a1951852ab878fffc3e23d62514c4f977ed5`(origin/main), 바뀐 파일 1개(`ci.yml`), 커밋 0, 미추적 2(티켓과 이 일지). 표준 축은 sonnet·high, 명세 축은 본 세션 모델(ADR 0033). 명세의 원천은 티켓 045와 사용자의 답이다.

### Standards

하드 위반 1건, 판단 항목 5건, smell 해당 없음. (1) ADR 0038 12줄의 "`ci.yml`의 `python` 잡은 `ubuntu-latest`이고, 그것이 가리키는 ubuntu-24.04 러너 이미지 …" 문장이 이 변경 뒤 현재형으로 거짓이 된다(`CLAUDE.md` 작업 규약 4). (2) 일지·티켓의 "일지 2026-11-06-08 '다음'"은 그 일지에 아직 없는 절이고, 그 파일은 PR #479에 있어 이 브랜치 단독으로는 가리킬 곳이 없다. (3) 티켓의 "(59줄, ADR 0038)"은 이 변경 뒤 61줄이라 줄 번호가 낡는다. (4) 티켓의 따옴표 인용이 시험 파일 117줄의 원문과 띄어쓰기·어미가 다르다. (5) 일지의 "어림"보다 센 근거(실패 로그의 `_rg_reads_secret … True`)가 있다. (6) 주석과 시험은 14.1.1이고 24.04 이미지는 14.1.0이다(24.04 실행이 `6442 passed`라 문제는 없다). 주장 검증: 두 실행의 이미지·ripgrep 판·통과 수(`gh run view --log`로 맞음), `rg`를 까는 잡은 `python` 하나뿐(맞음), 117줄 주석의 위치(맞음).

### Spec

막을 결함 없음. `python` 잡의 `runs-on`이 정확히 `ubuntu-24.04`이고 다른 `runs-on`(`ci.yml` 6곳과 `claude-code-review.yml` 1곳)은 `ubuntu-latest` 그대로이며 `tests/`는 바뀌지 않았다. 경미한 지적 둘은 표준 (2)·(3)과 같다. 수용 기준 2는 이 PR의 CI가 돌아야 확인되므로 대 보지 못했다.

### 반영

고친 것: (3) 티켓에서 줄 번호를 "`ripgrep` 설치 단계"로 바꿨다. (2) 티켓의 가리킴을 "경위는 일지 2026-11-06-08 '이어받은 세션(PR 반영·병합부터)', 남긴 일은 일지 2026-11-06-10 '다음'"으로 바꿨다(앞의 절은 #479의 일지에 있다). (4) 티켓의 인용을 시험 파일 117줄의 원문 "rg 14.1.1 은 겹친 묶음을 풀지 못해 오류로 끝나고 훅은 둘 다 푼다"로 바꿨다. (5) 위 "한 일"의 근거 문단을 실패 로그를 읽은 것으로 올려 적었다. 판단으로 둔 것: (6)은 24.04 실행이 초록이어서 그대로 둔다.

남긴 것: (1) ADR 0038은 이 PR에서 고치지 않는다. 그 문장은 이미지 `20261012.334.1`의 README를 받아 본 그때의 근거를 적은 것이라 `.claude/rules/adr.md` 16줄(결정 시점의 수나 근거를 적은 문장)에 가깝다. 다만 현재형인 "`python` 잡은 `ubuntu-latest`"가 거짓이 되고, 이 ADR의 판 정책("rg의 판은 저장소가 고정하지 않는다", 판이 갈리면 CI가 먼저 본다)과 러너 고정이 긴장한다. 이력과 포인터는 사용자 승인이 드는 ADR 개정이고, 무엇을 정할지는 후속 티켓(시험이 두 판을 아는 쪽으로 고치고 고정을 풀지)이 정하므로 그 티켓이 쓴다. 받는 쪽은 이 일지의 "다음" 첫 항목이다. PR 본문 "남긴 위험"에도 적는다.

다시 돌린 명령: 일지·티켓만 고쳐 다시 돌릴 검사가 없고, 커밋의 pre-commit으로 갈음한다. 반영으로 새로 쓴 문장은 이 절의 "고친 것" 줄과 위 "한 일"의 근거 문단이며 PR 직전 리뷰에 밀 주장으로 넘긴다.

## 검증

커밋 `f5607a77`(`chore: python 잡의 러너를 ubuntu-24.04로 고정한다 (harness 045)`)의 pre-commit이 모두 지났다(백그라운드 출력 파일을 `tail -40`으로 읽었다). 열 단계(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest 306.6s, web-verify 502.6s)와 마크다운 표·줄 구분 문자·변이 표·커밋 메시지 검사가 Passed이고, ruff 둘과 카나리아 명세·헌법 판 검사는 `(no files to check)`로 Skipped다(`.py`와 명세·헌법 파일이 커밋에 없다). zizmor는 커밋 전에 손으로도 쳐서 지적 없음이었다. 린트 둘(`uv run ruff check .`, `uv run ruff format --check .`)은 `.py`를 바꾸지 않아 손으로 치지 않았다. 인용 대조 경고 5건은 막지 않았고 하나씩 봤다. 대기열 500의 제안 문장 인용(이미 있던 행의 글), 이 일지가 옛 문구를 따옴표로 되짚은 둘(21줄 "일지 2026-11-06-08 '다음'"과 대기열 500의 머리를 줄여 옮긴 43줄), 티켓의 가리킴을 따옴표 모양만 바꿔 옮긴 29줄, 훅 안내문 인용(45줄)이다. 모두 글을 읽는 데 지장이 없어 두었다. `-m llm`·`-m llm_widget`·e2e·사진 비교는 돌리지 않았다. `ci.yml`의 러너 한 줄이 이 PR의 CI에서 그 이미지로 도는지가 수용 기준 2이고, 그 결과는 PR의 검사로 확인한다(아직 푸시하지 않았다).

## PR 직전 리뷰(이어받은 세션, 기준 d0f5a195)

`coderabbit auth status`가 `Seat: not assigned`(Plan Free)라 CLI는 돌지 못했다. 대체 둘을 돌렸다. origin/main은 이 브랜치의 기준에서 움직이지 않았다(`git log HEAD..origin/main`이 비었다).

`/security-review`: 보고할 취약점 없음. 바뀐 것은 `runs-on` 라벨과 주석뿐이라 권한·트리거·`${{ }}` 식·외부 액션 참조가 그대로다.

`bug-perf-review` 서브에이전트: Minor 3건, 코드·CI 단계의 버그·성능 문제는 없음. 잡 안의 다른 단계(`uv` 설치, pyright, 캐시, `rg` 설치 단계)와 어긋남이 없고 다른 `runs-on` 여섯 곳은 그대로다. (1) ADR 0038 12줄의 현재형 문장이 새 `ci.yml`과 어긋난다. (2) 티켓 본문은 "한 줄", 수용 기준은 "주석 두 줄"이다. (3) 티켓 `Status: done`인데 수용 기준 2가 열려 있다.

반영: (2) 티켓 본문을 "두 줄"로 고쳤다. (1)은 셀프 리뷰 "남긴 것"대로 이 PR에서 고치지 않고 PR 본문 "남긴 위험"과 아래 "다음"에 둔다. (3)은 PR의 CI가 돈 뒤 `gh run view --log`로 확인해 기준 2를 닫는다(CI 확인은 PR을 연 뒤라 지금은 닫을 수 없다). 서브에이전트가 접은 오탐 하나(24.04에서 26.04로 넘어갈 때 `setup-uv` 캐시를 되살려 깨질 가능성)는 근거가 없어 그대로 둔다.

### PR #480의 CI(수용 기준 2)

헤드 `102ceb01`의 실행 `42188182473`에서 `python`·`verify`·`web`·`e2e`·`e2e-widget`·`visual`·`ticket`·`claude-review`가 초록이다(`uv run python tools/wait_ci.py 480`의 끝 줄 `끝: 모두 통과`와 `gh pr checks 480`을 읽었다). `python` 잡 로그(`gh run view 42188182473 --log --job 127793435135`를 받아 `grep`으로 손으로 봤다)에 `Image: ubuntu-24.04`(`Version: 20261101.360.1`), `Setting up ripgrep (14.1.0-1)`, `6442 passed, 8 deselected`가 있다. 수용 기준 2를 닫았다. CodeRabbit은 무료 한도에 걸려 리뷰가 없다(PR 코멘트 `Review limit reached`, 체크 `skipping`). claude-review는 지적 없음 코멘트를 남겼다.

## 인계(커밋 뒤)

세션 컨텍스트가 인계 문턱을 넘어(계기 문장은 256,758 토큰) `커밋 뒤` 경계에서 넘긴다. 이 세션을 연 지시문의 "이어받을 상태"는 `인계: PR 연 뒤`로 시작해 지금 경계와 다르고, 곁 세션도 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 계기를 낸 커밋은 성공했다. 작업 트리는 이 일지의 "검증"·"인계"를 쓴 뒤라 이 일지만 커밋하지 않았다. 푸시하지 않았고 이 브랜치에 PR은 없다.

이 세션은 PR #479(`docs/rag-engine-name`)를 이어받아 봇 회차를 시작했다가 `python`·`verify` 실패를 만났고, 사용자가 "러너를 24.04로 고정"을 골라 이 브랜치로 옮겨 왔다. 그래서 새 세션이 이을 일이 둘이다. 이 브랜치의 PR을 병합하는 것(먼저), 그다음에 #479를 잇는 것이다.

제목을 `chore/045-ci-python-runner-pin (인계함)`으로 바꿨다(바꾸기 전 제목은 `docs/rag-engine-name`). 이 세션이 띄운 백그라운드 작업은 없다(CI 대기와 커밋은 끝났고 서브에이전트 둘은 보고를 냈다). 워크트리 잠금을 푸는 명령은 `045-ci-python-runner-pin`과 `rag-engine-name` 둘 다 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-11-06T08:17:51Z #479의 상태는 `C:/project/agent/.claude/worktrees/rag-engine-name/docs/journal/2026-11-06-08-rag-engine-name.md`의 "이어받은 세션(PR 반영·병합부터)" 절에 있고 그 절은 커밋하지 않았다(그 워크트리에 있다).

### 남은 단계

(가) 이 브랜치(`chore/045-ci-python-runner-pin`). 1. PR 직전 리뷰. `coderabbit auth status`가 `Seat: not assigned`이면 CLI는 돌지 못한다. 그때는 대체 둘인 `/security-review`와 `bug-perf-review` 서브에이전트를 돌려 두 보고를 이 일지에 옮기고 Critical·Major를 고친다. 2. 이 일지를 커밋해 푸시한다. 3. PR을 연다. 면제 PR이 아닌 chore 티켓 PR이므로 템플릿 체크리스트를 채우고, 본문 "남긴 위험"에 ADR 0038 12줄의 현재형 문장과 후속 티켓 둘을 적는다. 4. `@coderabbitai review` 코멘트를 남기고 `uv run python tools/wait_ci.py <번호>`를 백그라운드로 띄운다. 5. 수용 기준 2(`python` 잡 로그에 `Image: ubuntu-24.04`와 `Setting up ripgrep (14.1.0-1)`이 보이고 `python`·`verify`가 초록)를 `gh run view --log`로 확인해 이 일지와 티켓에 적는다. 6. `merge.md` "워크트리에서 병합할 때" 1~4로 병합한다.

(나) 병합 뒤 PR #479(`docs/rag-engine-name`). 1. `C:/project/agent/.claude/worktrees/rag-engine-name`에 `EnterWorktree(path)`로 들어간다. 그 워크트리의 일지 `docs/journal/2026-11-06-08-rag-engine-name.md`에 커밋하지 않은 변경(이어받은 세션 절)이 있으니 먼저 커밋하고 `git merge origin/main`을 한다. 2. 그 일지의 "다음"과 retro를 마친다. "다음"에 적을 것: answer-eval(`.scratch/plan.md` 32줄)의 Blocked by가 `rag-engine:core`만인데 수락은 실제 문서 검색 서버 이미지를 요구하고 그 이미지는 `release-image`가 만든다(제안서를 그대로 옮겼고 answer-eval의 설계 인터뷰가 먼저 본다). 이 CI 실패가 낳은 후속 둘은 새 harness 티켓으로 쓴다: 훅 시험이 ripgrep 14와 15 모두에서 맞게 고치고 러너 고정을 풀지 정하는 일, ADR 0038 이력과 12줄 포인터(사용자 승인). 3. 푸시한 뒤 첫 `@coderabbitai review` 코멘트를 다시 남긴다(이 세션이 07:58 UTC쯤 남긴 것은 옛 헤드 `ccfbd2c`에 대한 것이다). `wait_ci`를 띄우고 봇 지적을 반영한다(첫 회차의 Minor·Nit은 지적마다 판단, 둘째부터 Critical·Major만). 4. 병합 직전 `tools/sibling_overlap.py`를 다시 치고, 형제 워크트리 `04-runtime-enforces-rules-per-tool-call`의 일지 2026-11-06-09가 먼저 병합되면 일지 번호를 옮긴다. 병합은 `merge.md` "워크트리에서 병합할 때"대로 한다.

대기열 500에는 이 세션이 2회차를 더했다(이 브랜치의 커밋에 들어 있다). 열린 PR #478(approval-rules 04)도 같은 `python` 잡이 실패했을 것이라, 이 브랜치가 병합된 뒤 그쪽 세션이 main을 합쳐 다시 돌려야 한다.

### 인계 지시문

```
다음 작업: .scratch/harness/issues/045-ci-python-runner-pin.md. CI의 python 잡을 ubuntu-24.04로 고정하는 PR을 열어 병합하고, 그 뒤 막혀 있던 PR #479(docs/rag-engine-name)를 이어 병합한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: docs/journal/2026-11-06-10-ci-python-runner-pin.md의 "인계(커밋 뒤)" 절의 "남은 단계" (가)부터 잇는다
브랜치: chore/045-ci-python-runner-pin
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-06-10-ci-python-runner-pin.md 전체. #479는 C:/project/agent/.claude/worktrees/rag-engine-name/docs/journal/2026-11-06-08-rag-engine-name.md의 "이어받은 세션(PR 반영·병합부터)" 절과 gh pr view 479 --json body
이어받을 상태: 인계: 커밋 뒤. docs/journal/2026-11-06-10-ci-python-runner-pin.md. 커밋 f5607a77까지 했고 푸시하지 않았으며 이 브랜치에 PR이 없다. 남은 단계는 그 일지 "인계(커밋 뒤)" 절의 "남은 단계"에 있다. 그 절은 커밋하지 않았다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지(#479의 ADR 0048 이력은 사용자 승인을 받았다. 러너 고정은 사용자가 "러너를 24.04로 고정"을 골라 승인했다)
```


## 회고

후보 5, 승인 1(회차로 세는 것), 기각 4, 넘김 0. 넘긴 것이 없어 사용자에게 묻지 않았다. 일지는 PR #479 세션이 이어 쓴 이 일지 하나와 이 일지를 읽었다.

1. **승인(회차로 센다).** `ubuntu-latest`가 26.04로 넘어가 ripgrep이 14.1.0에서 15.1.0으로 오르자, 판의 동작을 단언한 훅 시험 한 건이 코드 변경 없이 빨개져 모든 PR의 `verify`가 막혔다. 열린 대기열 500("시험이 외부 도구의 판마다 바뀔 수 있는 세부를 단언해 GitHub 러너 이미지가 오르자 코드 변경 없이 필수 검사가 빨개졌다", 1회차)과 같은 종류다. 이번에는 `git push -h`의 종료 코드가 아니라 `rg`의 겹친 묶음 처리라는 점이 다르고, 러너 이미지 이동이 외부 도구 판을 바꿔 시험이 깨졌다는 모양은 같다. 500에 2회차를 더했다(`자체 승인 2026-11-06, 2회차`). 500은 3회차에 `CODING_STANDARDS.md`의 한 줄을 고르는 행이라 지금은 더하는 것이 없다. 이 세션이 한 러너 고정(티켓 045)은 사건 하나를 고친 것이다. 문턱: 사건은 위 실행 둘, 층은 지금 고르지 않고(3회차에 판단), 되돌림은 PR 하나다. 티켓의 `**대기열:**` 칸에 500을 적었다.
2. **기각.** 세션 카드(`start_session` `own_initiative`)를 훅이 막았다. 훅이 후속 일을 일지 "다음"이나 대기열에 적으라고 알려 그대로 했다. 이미 있는 훅이 그 자리에서 알린 것이다.
3. **기각.** `AskUserQuestion`의 사실 대조 훅이 세 번 막았다. 첫 번째는 "지난주까지"처럼 대 보지 않은 시점을 적은 것을 잡았고(훅이 제 몫을 했다), 두 번째는 질문 문장과 라벨을 고치자 새 화면으로 세어 다시 막았다. 훅 안내문에 "질문 문장과 라벨이 같으면 다시 막지 않는다"가 이미 있다. 이미 있는 훅이 그 자리에서 알린 것이다.
4. **기각.** `tools/wait_ci.py`의 끝 줄(`끝: 실패 python, verify`)에 실패한 시험 이름이 없어 `gh run view --log-failed`를 한 번 더 쳤다. 그 한 호출로 원인 줄이 나왔고 비용은 호출 하나다. 사건 없이 떠올린 개선에 가깝다.
5. **기각.** `sibling_overlap.py … | head`로 파이프를 썼다가 훅이 종료 코드가 가려진다고 알렸다. 이미 있는 훅이 그 자리에서 알린 것이다.

## 다음

- ripgrep 15에서 훅과 `rg`의 동작 차이를 재서 `tests/tools/test_hook_env_read_rg.py`가 두 판을 모두 아는 쪽으로 고치고, 그 뒤 러너 고정을 풀지 정한다. 새 harness 티켓으로 다룬다.
- 그 티켓이 ADR 0038에 이력을 쓴다(사용자 승인). 12줄 "`ci.yml`의 `python` 잡은 `ubuntu-latest`이고 …"가 이 PR 뒤 현재형으로 거짓이고, 같은 절의 "rg의 판은 저장소가 고정하지 않는다"와 러너 고정이 긴장한다. 이력에 러너 고정의 임시성과 시험이 판에 맞추는 방식을 적고 12줄에 포인터를 단다(`.claude/rules/adr.md`). 이 PR은 ADR을 고치지 않았다(위 셀프 리뷰 "남긴 것").
- `ubuntu-24.04`는 GitHub이 이미지를 내리면 쓸 수 없게 된다. 그 전에 위 일을 끝낸다.
