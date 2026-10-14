# 2026-10-15 (03) CI 잡에 시간 제한을 두고 인터프리터 충돌의 단서를 남긴다(대기열 36·204)

## 계기

대기열 36·204. 대상 파일이 `.github/workflows/ci.yml`인 열린 행 가운데 ADR이 필요 없는 둘이다. 같은 파일을 든
31(행이 ADR을 요구한다)과 34(`tech.md`를 고쳐 ADR 뒤의 일이다)는 지시문의 결정대로 이 묶음에서 뺐다.

> 사용자: (지시문의 시작 프롬프트) "대기열 36·204(대상 파일이 `.github/workflows/ci.yml`인 열린 행 가운데 ADR이
> 필요 없는 둘)를 chore 한 PR로 반영한다"

## 시작 전 정리

`tidy-checkouts`: 루트 main을 `7eebfd79`에서 `804373a2`로 당겼다. 판정에서 지울 후보는 없었다. 넘긴 것은 분리
HEAD 일곱(`agent-canary-55ba299`, `elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`, 스크래치패드의
`m231`·`mrun2`·`mrun3`·`mrun4`), 등록이 `prunable`인 둘(`05-admin-hides-decision-for-end-user`,
`spec-pipeline-and-pytest-ids`)과 그 옆 이름 `spec-pipeline-and-pytest-ids.tidy-probe`, 병합된 PR의 머리와 끝이
다른 `skill-check-and-retro-section`이다. 나머지 워크트리는 모듈을 올린 프로세스(python 일곱, node 123348,
esbuild 16256·6844)나 실행 중인 세션, 다시 만들 수 없는 무시된 항목, 병합되지 않은 PR 때문에 남았다.

## 한 일

- `ci.yml`의 잡 다섯에 `timeout-minutes`를 두었다(python·web·e2e 15, visual 20, verify 5).
- python 잡의 `env`에 `PYTHONFAULTHANDLER: "1"`, pytest 앞 스텝에 `kernel.core_pattern`, pytest와 같은 `run`
  스텝에 `ulimit -c unlimited`, 실패 시 남은 코어를 gdb로 열어 `bt`와 `info sharedlibrary`만 찍는 스텝을 더했다.
- 시간 제한 값의 근거로 프로브 `.scratch/harness/probes/ci_job_durations.py`와 README 행을 더했다.
- CI에서 일부러 충돌시켜 코어 덤프와 gdb 스텝을 확인했고(아래 "잰 것"), 대기열 36·204를 닫았다.

## 잰 것

### 잡별 소요 시간(프로브)

`ci_job_durations.py`, 2026-10-15. 최근 성공 실행 40개가 모두 측정이었고 최대는 python 2.8분, web 2.3분, e2e
2.2분, visual 4.5분, verify 0.1분이었다. 제한은 그 네 배 이상이다. 캐시를 놓친 설치의 시간과 컨테이너 초기화가
잡의 제한에 드는지는 재지 않은 어림이다.

### 코어 덤프와 gdb 스텝(손으로 봤다)

PR #241에 임시 테스트 `tests/test_zz_crash_probe.py`를 커밋해 CI에서만 `ctypes.string_at(0)`으로 인터프리터를
충돌시키고, python 잡 로그를 `gh api .../actions/jobs/<id>/logs`로 받아 읽었다. 확인한 뒤 그 테스트를 지웠다.

- 테스트 도중의 충돌(커밋 `a9d17a65`, 실행 38595052814): pytest 스텝이 종료 코드 139로 끝났고 코어
  `/tmp/core.pytest.2554`가 남았다. 러너에 gdb가 없어 apt로 깔렸고(gdb 15.1, 약 10초), gdb가 `string_at`과
  `faulthandler_fatal_error`를 든 C 스택 38프레임과 공유 라이브러리 표를 찍었다. `Fatal Python error`와 파이썬
  스택은 로그에 없었다. pytest가 테스트 동안 stderr를 붙잡아 그 안에 갇혔다고 보지만 재지 않은 어림이다.
- 종료 중 충돌(커밋 `e4fe3677`, 실행 38652152183, `atexit`에 등록): PR #78과 같은 모양으로 `2714 passed` 뒤
  종료 코드 139였다. 이번에는 `Fatal Python error: Segmentation fault`와 `string_at`을 든 파이썬 스택이 로그에
  남았고, gdb도 코어 `/tmp/core.pytest.2560`에서 C 스택을 찍었다. 대기열 36이 겨냥한 상황에서 두 스택이 모두
  남는다.
- 코어 이름의 `%e`는 두 번 모두 `pytest`였다. 셀프 리뷰에서 코어를 이름으로 거르지 않기로 한 판단이 맞았다.
  이 사실과 테스트 도중 충돌의 한계를 `ci.yml` 주석에 적었다.

## 셀프 리뷰

base `804373a2`, 바뀐 파일 둘(`ci.yml`, 프로브 README), 미추적 하나(프로브), 커밋 0개. 표준 축은 소스 파일이
없어 sonnet이다.

표준 축:
- 하드: 프로브 82행 E501. → 고쳤다(출력 문자열을 둘로 나눴다).
- 하드: 프로브가 잡의 `conclusion`을 보지 않아 건너뛴 잡도 0분 안팎으로 측정에 섞인다(`.claude/rules/probes.md`
  첫 항목). → 고쳤다. 결론 `success`까지 표지로 본다. 다시 돌려 40개 모두 측정이었다.
- 하드: 첫 초안의 `ci.yml` 주석이 잡의 제한이 러너를 잡은 뒤부터 세어 컨테이너 초기화도 든다고 근거 없이
  단정했다. → `ci.yml` 주석과 프로브 독스트링에서 어림이라고 밝혔다.
- 근거 없음: "캐시를 놓친 설치의 여유를 더했다". → 어림이라고 밝혔다. 프로브 독스트링과 README에 모집단이 성공한
  실행뿐이라는 한계를 적었다.
- 판단: `/tmp/core.*`가 파이썬 아닌 프로세스의 코어도 잡아 gdb에 엉뚱한 실행 파일을 줄 수 있다. → 남긴다.
  `%e`는 셔뱅 스크립트를 띄우면 스크립트 이름(`pytest`)이 될 수 있어 이름으로 거르면 정작 파이썬 코어를 놓친다.
  CI에서 일부러 충돌을 일으켜 실제로 볼 몫이다.
- 판단: `timeout-minutes: 15` 반복, 프로브의 `JOBS`가 잡 이름을 복제, `gh`·`ts`·`got` 이름. → 남긴다. 반복은
  머리 주석이 근거를 한 곳에서 대고, `JOBS`가 어긋나면 프로브가 1로 끝나는 것이 의도한 표지다.

명세 축:
- Minor: 첫 초안의 주석이 2026-10-15를 실행 날짜처럼 적었는데 그것은 잰 날짜이고 실행은 2026-10-13~14다. →
  "2026-10-15 에 잰 최근 성공 실행 40개(2026-10-13~14)"로 고쳤다.
- 관찰: visual 20분 제한은 PR #195의 18분 정지를 그 안에 둔다. → 남긴다. 평소 4.5분 이하라 18분은 이미 이상
  징후지만, 이미지 캐시 없이 컨테이너를 당기는 시간을 재지 않아 더 줄이지 않았다.
- 누락과 범위 넘침은 없었다.

다시 돌린 명령: 프로브 재실행(40/40 측정), `uv run ruff check` 프로브(통과), zizmor(`No findings`). 나머지 검증
명령은 커밋의 pre-commit으로 갈음한다.
