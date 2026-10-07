# 2026-10-07 (18) claude-review 워크플로가 보안·버그·성능 축의 대체를 안다

PR #167(대기열 136)이 띄운 작업 칩의 일이다. 그 PR의 잔존 grep이 `.github/workflows/claude-code-review.yml`의 두 자리를
찾았지만, 그 파일을 바꾼 PR은 claude-review가 건너뛰므로 별도 PR로 넘겼다(일지 16의 잔존 grep). 워크트리
`charming-bhaskara-4d6dc8`에서 #167이 병합되기를 기다린 뒤 `origin/main`(`eda296e`)으로 `chore/review-owner-fallback`을
땄다. 순번은 18이다. 17은 열린 PR #169(`17-zizmor-workflow-audit`)가 쓴다(`tools/sibling_overlap.py`).

## 계기

> 사용자: "PR(브랜치 chore/review-axis-and-failure-reason, 대기열 136을 닫는 PR) 병합 뒤 main을 동기화하고 시작한다. 저장소는 C:\project\agent이고 CLAUDE.md의 작업 규약을 따른다. 브랜치는 chore/<slug>.
>
> 할 일: `.github/workflows/claude-code-review.yml`의 두 자리가 보안·버그·성능 축의 소유자를 옛 판으로 적는다.
> - 2행 주석: "보안·버그·성능은 PR 직전 CodeRabbit CLI와 PR의 CodeRabbit이 본다."
> - 59행 봇 프롬프트: "보안과 성능은 PR 직전 CodeRabbit CLI가 맡는다."
> 대기열 136을 닫은 PR이 `docs/constitution/operations.md` 리뷰 파이프라인 2단계에 "CLI가 돌지 못하면(미설치, 로그인·좌석 없음, 한도 초과) PR 직전에 내장 `/security-review`(보안)와 `bug-perf-review` 서브에이전트(버그·성능)를 나란히 돌린다"를 세웠다(ADR 0006의 2026-10-07 이력). `CODING_STANDARDS.md` 리뷰 관점 끝 줄은 이미 "PR 직전 CodeRabbit CLI(돌지 못하면 `/security-review`와 `bug-perf-review`)"로 고쳤다. 워크플로의 두 자리도 같은 뜻으로 맞춘다. 봇이 보지 않는 축이라는 범위 제외의 뜻은 그대로 둔다.
>
> 주의: 이 워크플로 파일을 바꾼 PR은 claude-review가 건너뛰고 코멘트 0개 가드도 꺼진다(`docs/constitution/operations.md` 리뷰 파이프라인, PR 템플릿의 `.github/` 줄). 그래서 다른 변경과 섞지 않고 별도 PR로 내고, CodeRabbit 코멘트와 셀프 리뷰를 손으로 본다. 같은 파일을 겨누는 열린 대기열 146(`claude_args`로 모델이 `.git/`을 읽지 못하게 한다, 권한 규칙 탐침이 먼저)과 한 PR로 묶을 수 있는지 먼저 본다. 묶으면 146의 탐침과 행 닫기도 그 PR의 일이다."

## 어떻게 했나

- **병합을 기다렸다.** 세션을 시작했을 때 #167은 열리지도 않았고, 그 워크트리에는 커밋하지 않은 변경이 열셋 있었다.
  `gh pr list --head`를 1분마다 묻는 스크래치 스크립트를 백그라운드로 걸고, 그동안 146을 읽었다. 기다리는 사이에
  #168(액션을 커밋 해시로 고정)이 같은 파일 머리에 한 줄을 더해, 지시문의 59행은 60행이 되었다.
- **146은 묶지 않았다.** 행은 `.git/config`의 앱 토큰 하나를 겨누는데, 같은 토큰에 닿는 길이 더 있어 보인다.
  - Claude Code permissions 문서(code.claude.com/docs/en/permissions, 2026-10-07에 읽었다)의 Read and Edit 절은 `Read`
    deny가 내장 파일 도구, Claude Code가 알아보는 `cat`·`head`·`tail`·`sed`·`tee`, 리다이렉트 대상에 닿고, 파일을 스스로
    여는 하위 프로세스에는 닿지 않는다고 적는다. 문서가 드는 예는 그 명령들과 파이썬·노드 스크립트다. 허용 목록의
    `gh pr comment --body-file <경로>`와 `git diff --no-index`가 그 모양이라는 것은 이 세션이 허용 목록에 그 문장을 대 본
    어림이다.
  - 워크플로가 고정한 액션 커밋 `5898584`(v1.0.244. 지금 `v1` 태그도 이 커밋이다)의 `action.yml`을 `gh api`로 읽었다.
    `Run Claude Code Action` 단계의 환경에 `DEFAULT_WORKFLOW_TOKEN`(잡의 `github.token`. `pull-requests`·`issues` 쓰기,
    308행)과 `CLAUDE_CODE_OAUTH_TOKEN`(336행)이 있다. 일지 14는 액션이 앱 토큰을 `GH_TOKEN`·`GITHUB_TOKEN`에 넣는다고
    적는다(`run.ts`). 허용 목록의 `Read`는 경로 제한이 없어, `/proc/self/environ`을 읽으면 셋이 보일 수 있다. 마지막의
    `Revoke app token` 단계(448행)는 앱 토큰만 폐기하므로 `CLAUDE_CODE_OAUTH_TOKEN`은 실행이 끝나도 살아 있다.
  - 둘 다 문서와 소스에서 끌어낸 어림이고 재지 않았다. Claude Code 프로세스가 그 환경을 물려받는지, `Read`가
    `/proc/self/environ`을 읽는지도 보지 않았다. 맞다면 146의 탐침은 길 서넛을 보아야 하고, 처방은 deny 한 줄에서
    `Read`의 경로 제한이나 샌드박스까지 넓어질 수 있다. 그 범위는 사용자가 정할 일이라, 두 줄의 문구 수정을 그
    결정에 묶어 두지 않았다. 146 행에는 이 절을 가리키는 한 줄만 두었다. 범위를 넓히는 것은 아직 후보라 대기열이
    아니라 여기에 둔다.
- **60행은 소유자만 고쳤다.** 원문은 범위에서 "보안과 성능"을 빼고 버그는 빼지 않는다. 버그를 더하면 봇이 명백한
  버그(Major)를 보지 않게 되어 동작이 바뀌므로 그대로 두었다. 소유자는 2행·`CODING_STANDARDS.md`와 같게 "PR 직전 CodeRabbit
  CLI(돌지 못하면 `/security-review`와 `bug-perf-review`)와 PR의 CodeRabbit"으로 적었다. 원문에 없던 "PR의 CodeRabbit"이
  여기서 들어갔다.

## 바꾼 것

- `.github/workflows/claude-code-review.yml`: 2행 머리 주석과 60행 프롬프트(절차 4)의 소유자.
- `.scratch/retro-queue.md`: 146 행의 "어디로"에 이 일지를 가리키는 한 줄, 승인 칸에 이 일지.

## 잔존 grep

`PR 직전 CodeRabbit CLI(가|와|이)`, `CLI가 맡는다`, `보안과 성능은`, `CodeRabbit CLI`를 md·yml·yaml·py·json·ts·toml에서
찾았다. 소유자를 옛 판으로 적은 살아 있는 문서는 없다. 이 패턴에 걸려 남은 것은 기록(일지, ADR 0006·0009, interrupts
티켓 둘의 지난 지적)과 헌법 README의 버전 이력, CLI의 한도·좌석 사실만 적는 `kickoff/facts.md`·`kickoff/pitfalls.md`,
소유자를 이미 새 판으로 적는 `CODING_STANDARDS.md`·`operations.md`·두 서브에이전트다. 셀프 리뷰가 패턴 밖에서 옛
결정의 문구("좌석이 있으면 `coderabbit-review`를 돌리고, 없으면 돌리지 않고")를 `.scratch/plugin-toggle/spec.md`와
`.scratch/web-admin/spec.md`에서 찾았다. 두 기능 모두 `plan.md`에서 done이라 기록이다.

## 검사

- 워크플로를 PyYAML로 읽어 `Run Claude Code Review` 단계 프롬프트의 절차 4 줄을 찍었다(스크래치 스크립트). 고친 문장이
  그대로 들었다.
- 탐침 `.scratch/harness/probes/review_workflow.py`(Git Bash, 작업 트리): 어긋남 0/8. 체크아웃과 가드는 이 PR이 건드리지
  않았고, 파일을 다시 읽어도 그대로라는 것만 본다.
- 검증 명령: `uv run pytest -q` 1846 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(25파일 338개)가 모두 초록이다. 이 워크트리에는 web 의존성이 없어 `pnpm -C web install
  --frozen-lockfile`을 먼저 쳤다.

## 셀프 리뷰

`/code-review`(기준 `eda296e`, 수정 2·미추적 1, 커밋 0). 소스가 없어 표준 축은 sonnet이다. 명세는 사용자 지시문과 146
행이고 요구와 리뷰어 참고를 갈라 넘겼다. 표준 축은 Minor 2·Nit 4, 명세 축은 Minor 1·Nit 3이었고 Critical·Major는 없었다.
명세 축은 요구 다섯이 모두 충족되었다고 봤다. 60행에 버그를 더하지 않은 것과 소유자에 PR의 CodeRabbit을 더한 것도 요구
2에 든다고 봤다.

- **고친 것.**
  - 표준 Minor·명세 Nit(겹침): 146 행의 "어디로"에 근거 네 문장을 넣어 행이 두 배가 되었고, 탐침이 `.git/` 밖의 길도
    본다는 승인받지 않은 범위 확장을 대기열에 적었다. 대기열 머리는 행을 넷으로 짧게 두고 후보는 일지에 둔다.
    행에는 이 일지를 가리키는 한 줄만 남겼다.
  - 표준 Minor: `action.yml`을 판 없이 "액션 v1"로 적었다. 워크플로가 고정한 `5898584`의 파일을 다시 읽어 행 번호와 함께
    적었다. `v1` 태그도 지금 그 커밋이다(`gh api repos/anthropics/claude-code-action/commits/v1`).
  - 명세 Minor: 같은 단계의 환경에 `DEFAULT_WORKFLOW_TOKEN`(잡의 `github.token`)도 있다. 일지의 토큰 목록에 더했다.
  - 표준 Minor: "실행이 끝나도 폐기되지 않는다"에 출처가 없었다. `Revoke app token` 단계가 앱 토큰만 폐기한다는 것을 댔다.
  - 명세 Nit: 문서가 적은 것과 이 세션이 허용 목록에 대 본 어림이 한 괄호에 섞였다. 일지에서 둘을 갈랐다.
  - 표준 Nit: 2행 주석의 두 이름에 백틱을 달아 60행·`CODING_STANDARDS.md`와 맞췄다.
  - 명세 Nit: 잔존 절의 grep 낱말에 `tools/check_quotes.py`가 인용 경고를 냈다. 낱말을 백틱으로 바꿨다.
  - 표준 Nit: 잔존 절의 "남은 것"이 패턴 밖의 done 명세 둘을 빠뜨렸다. 더했다.
  - 표준 Nit: 프롬프트 변경의 실제 실행 확인 계획이 없었다. 아래 "다음"에 적었다.
- **남긴 것.**
  - 표준 Nit(Duplicated Code 판단 항목): 봇 프롬프트에 대체 도구의 이름까지 되풀이해, 대체가 바뀌면 리뷰가 건너뛰는 이
    파일을 또 고쳐야 한다. 지시문이 `CODING_STANDARDS.md` 끝 줄과 같은 뜻으로 맞추라고 했고, 일지 16이 같은 반복을
    실리는 때가 다른 자리마다 둔 포인터로 받아들였다.
## PR 직전 보안·버그·성능 축

## PR 리뷰 반영

## 회고

후보 셋을 냈고 셋 다 승인됐다. 셋 다 이 PR에서 반영하지 않고 대기열로 갔다. PR #166(열림)이 151·152를 쓰므로 155~157이다.

> 사용자: (고른 것) "1. 대기열 행 비대,2. 외부 근거 대조 불가,3. 다음 일지 번호"

1. **대기열의 열린 행에 근거 서술과 범위 확장을 적었다(대기열 155, 1회차).** 위 셀프 리뷰의 첫 항목이다. 대기열 머리를
   읽은 직후였다. 기계 판정은 닫힘 메모와 거짓 양성이 겹쳐 대상을 정하지 않고 회차를 본다.
2. **리뷰 서브에이전트가 외부 문서의 근거를 대조하지 못했다(대기열 156, 1회차).** 두 축이 permissions 문서의 Read and
   Edit 절을 대조 불가로 남겼다. 본 세션은 WebFetch 저장본을 세션 폴더에서 읽었고, 서브에이전트의 같은 읽기는 거부되었다.
3. **번호 대조 도구가 다음 빈 번호를 알려 주지 않는다(대기열 157, 1회차).** 일지를 쓰기 전에 돌린 첫 대조는 "새 번호
   없음"이었고, 17로 쓴 뒤의 대조가 #169와의 겹침을 냈다.

일지에만 남기는 것:

- 작업 칩 지시문의 "59행"이 #168 병합으로 60행이 되었다. 지시문이 문장도 함께 인용해 찾는 데 지장이 없었다.
- 선행 PR(#167)의 병합을 스크래치 스크립트(`gh pr list --head`를 1분마다)로 기다렸다. 칩을 띄운 세션은 그 PR을 열기
  전이었다.
- Grep의 부정 glob(`!docs/journal/**`)을 `hook_env_read`가 막았다. 일지 16에 이은 둘째이고, 훅이 설계대로 동작했다.
- 첫 커밋 시도에서 pre-commit의 `web-verify`가 빨갰다. 백그라운드로 돌린 `pnpm -C web verify`와 겹쳐, 그쪽 Vitest의
  `web/eslint.config.test.ts`가 만든 임시 폴더 `web/judge-*`를 이쪽 prettier가 봤다. 백그라운드 실행은 초록이었고 폴더는
  남지 않았다. 같은 체크아웃에서 `verify`를 둘 겹쳐 돌리지 않는다.
## 다음

- 병합 뒤 첫 PR의 claude-review 실행에서 액션이 바뀐 프롬프트로 돌고(`Skipping action due to workflow validation`이
  없다) 요약 코멘트를 남기는지 본다. 이 PR에서는 액션이 건너뛰어 바뀐 프롬프트가 한 번도 돌지 않는다.
- 대기열 146은 열린 채다. 그 행을 잡는 세션은 이 일지의 "어떻게 했나"에서 `.git/` 밖의 길 후보를 읽고, 탐침의 범위를
  넓힐지 사용자에게 먼저 묻는다.
