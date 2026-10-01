# 2026-10-01 (10) `verify`가 같은 실행의 잡 목록을 읽어 `needs` 밖의 잡을 빨강으로 본다 — 대기열 89

일지 09와 같은 세션이 이어서 했다. PR #117을 병합한 뒤 next-session 결정표의 "하네스·문서만 고친 PR이었고 같은
주제가 남았다" 줄로 이 세션에 남았다. 같은 워크트리(`ci-parallel-jobs`)에서 최신 main으로 `chore/verify-needs-check`를
땄다.

앞 PR의 끝을 여기 남긴다(일지 09의 "다음"). PR #117은 `ff7d21f`(CI 1분 31초, claude-review 3회차 "지적 없음") 뒤
`43a6905`로 병합됐다. 나란히 돈 세션의 PR은 #118로 열렸다.

## 자리를 정한 것

- **판정.** `verify`가 `gh api …/actions/runs/$GITHUB_RUN_ID/attempts/$GITHUB_RUN_ATTEMPT/jobs`로 같은 실행 시도의 잡
  이름을 읽고, 자기 밖의 잡이 `needs`에 없으면 빨강이다. 목록에 `verify` 자신이 없으면(빈 목록) 그것도 빨강이다.
  `actions: read`는 이 잡에만 준다. 셸은 Actions 기본(`bash -e`)이고 파이프를 쓰지 않는다. 명령 치환이 든 대입이
  실패하면 단계가 끝나는 것에 기댄다.
- **ADR 0021의 둘째 2026-10-01 이력.** 초안을 보여주고 받았다. 거부한 안은 pytest의 저장소 상태 테스트와, 체크아웃한
  뒤 러너 이미지의 `yq`로 읽는 것이다.

> 사용자: "승인"

- **문구.** `operations.md`의 가드레일 한 문장, `ci.yml` 머리 주석, 대기열 34(잡을 더할 계획)와 89(닫음), 헌법
  3.0.5. 같은 날짜의 이력이 둘이 되어 3.0.4와 `plan.md`의 참조에 "첫째"를 붙였다.

## 잰 것

- **API의 잡 이름(손으로 봤다).** 끝난 실행 둘에 `gh api repos/…/actions/runs/<id>/attempts/1/jobs`를 쳤다.
  `36877116756`은 네 잡이 잡 id 그대로 나왔고, `36871174692`(일지 09의 실험 A)에서는 건너뛴 `web`도 목록에 들었다.
  러너 이미지 README(ubuntu-24.04, 20260927.320)에는 `yq 4.53.6`과 `GitHub CLI 2.101.0`이 있었다(읽었다).
- **판정식(스크래치 스크립트로 손으로 봤다).** 표본 목록 셋(정상, `needs` 밖의 `lowest`, 빈 목록)이 초록, 빨강,
  빨강이었다.
- **실제 실행(PR #119, 손으로 봤다).** 바꾼 커밋 그대로(`01c74d6`, `36880955836`)는 초록이었고, 도는 중의 `verify`가
  `["e2e","web","python","verify"]`를 읽었다. 실행 중인 자신이 목록에 들고 `actions: read`로 읽힌다는 미측정 전제
  둘이 이것으로 섰다. 실험 커밋(`1db1ef1`, `36881731015`)에 `needs`에 없는 `extra`와 `needs: [verify]`인 `after`를
  더하자 `verify`가 `["extra"]`를 찍고 빨갰다. 목록에 `after`는 없었다. 그래서 ADR 초안의 "`verify` 뒤에 도는 잡은
  예외로 적는다"를 "이 검사가 보지 못한다"로 고쳤다. 실험 커밋은 `ci.yml`을 `01c74d6`의 것으로 되돌려 지웠다.
- **e2e 지연.** 실험 실행에서 `e2e` 잡이 5분 24초 걸렸다. `playwright install-deps chromium`(apt)이 4분 32초였고
  평소에는 14~18초다. 이번 변경과 무관한 러너 쪽 지연으로 보인다(어림, 한 번).

## 셀프 리뷰

`/code-review`(이번에는 워크트리 사본), base `43a6905`, 수정 파일 5, 커밋 0, 미추적 0. 소스 파이썬이 바뀌지 않아 표준
축은 sonnet이다. 명세는 ADR 0021의 둘째 2026-10-01 이력과 대기열 89 행이다.

- **표준 축.** Major 하나: 새 검사가 CI에서 한 번도 돌지 않았는데 89를 닫았다(작업 규약 3). 실행 중인 `verify`가 목록에
  드는지, `actions: read`로 읽히는지가 재지 않은 전제다. Minor 셋: "API로 손으로 봤다"에 명령이 없고 근거 실행 하나만
  건너뛴 잡을 받친다, `yq` 안을 거부한 "이미지에 기댄다"는 채택한 안(`gh`·`jq`)에도 걸린다, PyYAML은 `uv.lock`에 이미
  있다. Nit 둘: 일지 10이 아직 없다, 같은 날짜의 이력 둘이 모호하다.
- **명세 축.** Critical·Major 없음. Minor 둘: PyYAML 주장, `needs: [verify]`인 잡은 `needs`에 넣을 수 없어 "자기 밖의
  잡이 하나라도 없으면 빨강"에 반례가 된다(목록에 드는지에 따라 늘 빨강이거나 조용히 샌다). Nit 둘: 3.0.4의 참조가
  모호하다, "PR의 코드를 받지 않는 경계"가 넓다(실제 경계는 체크아웃하지 않고 `contents` 권한이 없다는 것).
- **고친 것.** 근거 표기(명령과 실행별 결과), 거부 근거(이미지 의존은 양쪽이 같고 갈리는 것은 체크아웃·`contents`
  경계), PyYAML 문장, 3.0.4와 `plan.md`의 "첫째", `verify` 뒤의 잡을 ADR과 주석에. Major와 `verify` 뒤의 잡은 위
  실험으로 채웠고, 결과에 따라 ADR의 그 항목을 다시 고쳤다.
- **남긴 것.** 89를 닫는 편집은 같은 PR에 두었다. 실험이 병합 전에 끝났기 때문이다.

## 검사

- 리뷰 반영 뒤: `uv run pytest -q` 통과, `uv run ruff check .`·`uv run ruff format --check .` 통과, `uv run pyright`
  0 errors, `uv run lint-imports` 통과, `pnpm -C web verify` 통과. `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.

## PR 리뷰

PR #119를 draft로 열었다. PR 직전 CodeRabbit CLI는 돌리지 않았다(`Plan: Free`, `Seat: not assigned`). draft 동안의
실험은 위 잰 것 절에 있다. 이번에는 `gh pr ready`와 `@coderabbitai review` 앞에서 PR head가 로컬 HEAD와 같은지 먼저
봤다(대기열 86의 사건).
