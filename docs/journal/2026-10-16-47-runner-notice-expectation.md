# 2026-10-16 (47) 훅 러너가 사람에게만 보이는 알림을 기대 값으로 받는다

`next-session` 지시문(기능 token-usage, 티켓 01, 나란히 여는 넷 가운데 하나)으로 연 새 세션이다. 주 체크아웃(main
`8a2163eb`)에서 열려 제목을 `feature/01-runner-notice-expectation`으로 바꿨다.

> 사용자: (지시문의 시작 프롬프트) "/implement .scratch/token-usage/issues/01-runner-notice-expectation.md"

## 정리

지시문대로 `tidy-checkouts`를 먼저 돌았다. 루트를 `8a2163eb`에서 `30b9f37b`로 당겼고(티켓 아홉과 일지 2026-10-16-38이
들어왔다) 지운 워크트리와 브랜치는 없다. 사람에게 넘긴 것은 `skill-check-and-retro-section`(병합된 PR의 머리와 브랜치 끝이
다르다) 하나다.

판정(`judge`)은 `feature/07-review-axis-and-plugins`를 "커밋이 모두 origin/main 에 있다"며 지우라고 냈다. 그 브랜치는
나란히 열린 07 세션이 막 만든 것이었고, 판정 직후 `git worktree list --porcelain`에서는 이미 그 세션의 워크트리
(`07-review-axis-and-plugins`, 잠금 pid 42152)에 체크아웃되어 있어 지우지 않았다. 그 세션의 제목은 아직
"토큰 사용량 축 및 플러그인 검토"라 판정 3의 `--running` 제목으로는 그 브랜치의 주인을 알아보지 못했다. 나란히 연 세션이
제목을 바꾸고 워크트리에 들어가는 사이에 첫 세션의 정리가 돌면 생기는 경합이다(회고 후보).

그 뒤 `EnterWorktree`(이름 `01-runner-notice-expectation`)로 들어가 브랜치를 `feature/01-runner-notice-expectation`으로
바꿨다.

## 구현

- `Expectation`에 `notice`를 더했다. 빈자리 셈(`coverage_gaps`)은 이미 `silent` 밖을 발동으로 세고 있어 코드는 그대로이고,
  표를 읽는 단계의 `Literal`만 `notice`를 막고 있었다. `contains`의 원천(`message_of`)도 이미 `systemMessage`를 읽었다.
- 시험은 티켓대로 표를 읽고(`load_cases`) 래퍼로 띄워 대조하는(`run_case`) 길로 돌린다. 래퍼(`tools/launch_hook.py`)는
  훅을 자기 파일 옆에서만 찾으므로, 가짜 훅을 저장소 `tools/`에 두지 않으려고 `load_cases`와 `run_case`(와 `_launch`)가
  루트(`root`, 기본은 저장소 루트)를 받게 했다. 시험은 래퍼 사본과 가짜 훅을 든 임시 루트를 준다. 그 루트에는
  `pyproject.toml`이 없어 `uv run --project <루트> --no-sync`가 "`--no-sync` has no effect when used outside of a project"
  경고를 stderr에 내고 프로젝트 없이 돈다(이 워크트리를 작업 폴더로 두고 손으로 봤다). 가짜 훅은 표준 라이브러리만 쓴다.
  자식의 작업 폴더는 그대로 저장소 루트다.
- 고치기 전에 이음매만 더한 판에서 새 시험 넷(표 시험의 세 갈래, 빈자리 셈)이 모두 `literal_error`(`input_value='notice'`)로
  빨간 것을 봤다. 첫 갈래(`systemMessage_하나`)도 그 까닭이었다.
- 독스트링: 러너 머리의 "기대는 넷"을 다섯으로 고치고 notice를 풀었다. `outcome_of`의 "표의 훅은 내지 않는다",
  `notice_outcome`의 "표의 훅은 `systemMessage` 를 내지 않으므로"를 고쳤다. 러너와 시험을 "notice"·"systemMessage"·"넷"으로
  grep해 시험 둘의 독스트링(`test_사용자에게만_가는_systemMessage_는_notice_다`, 래퍼 알림의 사용자 몫 시험)과 이름 둘
  (`기대_넷`·`넷_중_하나` → 다섯)을 더 고쳤다. 바꾼 시험 이름을 가리키는 변이 명세는 없었다.

## 정한 것

티켓의 "이 티켓이 정할 것" 1(`systemMessage`와 `additionalContext`를 함께 낸 출력)은 지금처럼 `context`로 둔다. 그 출력은
모델에게도 가고, Stop에서는 `additionalContext`가 대화를 잇게 한다(`.claude/rules/tools.md`). 사람에게만 알리려던 훅이
모델 몫까지 내면 `notice` 사례가 어긋남으로 잡아야 한다. `notice`로 보면 그 사례가 대화를 잇는 훅을 지나보낸다. 표 시험의
둘째 갈래(`additionalContext_도`)가 이 결정을 고정한다.

## 변이

`.scratch/harness/probes/run_hooks_notice_mutations.toml`의 일곱이 모두 기대대로 빨갰다. 시험이 새로 고정한 판정 다섯(기대
값, 빈자리 셈, `contains`의 원천, notice 사례의 `contains`를 받는 검사, 함께 낸 출력의 판정. 기대 값 밖의 넷은 그 전부터
있던 코드다)과 루트 이음매 둘이다. 변이마다 그 까닭의 표지
(`literal_error`, 빈자리 줄, 판정과 빠진 조각의 쌍, 거절 문구, 없는 가짜 훅)를 `expect_output`으로 봤다. 표지를 보려고 표
시험의 단언을 `(판정, 빠진 조각)` 쌍의 비교로 바꿨다.

## 검증

셀프 리뷰 전의 판에서 손으로 치는 검증 명령 다섯이 모두 초록이었다. 린트 둘, `pyright`(0 errors), `lint-imports`(계약
다섯 유지), `pytest -q`(3112 통과, LLM 시험 7개는 선택 밖, 18분 8초), `pnpm -C web verify`(Vitest 380 통과)다. 셀프 리뷰를
반영한 뒤의 다섯은 커밋의 pre-commit으로 갈음한다.

## 셀프 리뷰

`/code-review`(기점 `30b9f37b`, 바뀐 파일 셋, 미추적 둘, 커밋 0)의 두 축이 같은 Major 하나와 Minor 넷으로 모였다.

- [Major, 두 축] 고친 `notice_outcome` 독스트링의 "표의 context 훅은 모델에게만 알려 `systemMessage` 를 내지 않으므로"가
  여전히 거짓이다. 표의 `hook_session_web_deps` context 사례가 `failure_output`에서 `additionalContext`와 `systemMessage`를
  함께 낸다. 시험 하나의 독스트링도 같다. 반례를 열어 맞다고 봤고, `tools/hook_*.py`를 grep하니 `systemMessage`를 내는
  훅은 그 하나였다(래퍼 `tools/launch_hook.py`는 표의 훅이 아니다). "표의 context 사례는 사용자 몫을 요구하지 않으므로(대부분의 훅은 모델에게만 알린다)"로 고쳤다.
- [Minor, 두 축] `outcome_of`와 빈자리 셈 시험의 독스트링이 아직 없는 04·05의 훅("Stop 의 알림, 세션 시작의 요약")을 적었다.
  `implement`의 "그 티켓 파일의 메모로 넘긴다"를 어긴다. 괄호를 지웠다.
- [Minor, 두 축] 프로브 README에 새 변이 명세의 행이 없다. 더했다.
- [Minor, 두 축] 명세 94행의 "지금 러너는 … 받지 않는다(… 넷이다)"가 이 변경으로 거짓이 된다. 진행 중인 기능의 명세라
  살아 있는 문서다. 명세를 쓸 때의 사실로 고치고 티켓 01이 고쳤다고 더했다. 같은 말을 쓴 티켓 3행(Nit)도 고쳤다.
- [Minor, 두 축] 티켓의 "검증 명령이 모두 초록이다"가 체크됐는데 일지에 pytest와 web 검증의 결과가 없다. 위 검증 절에 적었다.
- [Nit, 표준] 시험 둘에 같은 단언이 있다. 이름에서 수를 빼고(`기대로_읽는다`) 더했던 단언을 지웠다.
- [Nit, 표준] `_launch`의 `cwd=root`는 어느 시험도 고정하지 않는다. 바꿀 까닭이 없어 `cwd=ROOT`로 되돌렸다.
- [Nit, 표준] "새 판정 다섯" 가운데 넷은 전부터 있던 코드다. 변이 명세 머리, README 행, 이 일지를 "시험이 새로 고정한 판정"으로
  고쳤다.
- [Nit, 표준] 독스트링의 짧은 줄. 고치며 넘친 줄을 `tools/rewrap_comments.py`로 감았다.
- 남긴 것: 표준 축이 짚은 Data Clumps(`root`가 세 함수를 함께 돈다)는 `launch_argv(hook, root)`와 검사 도구들이 루트를 인자로
  받는 선례가 있어 그 축도 내지 않았다. 변이 3과 7의 표지가 같은 것은 변이를 하나씩 넣어 섞이지 않는다고 그 축이 봤다.

고치며 `launch_argv(hook),`를 원문으로 쓰던 `.scratch/harness/probes/launch_hook_mutations.toml`의 6번이 원문을 잃었다(`--check`).
같은 파일의 24번은 들여쓰기가 8칸이라 기점의 코드(4칸)에서도 원문이 없던 옛 썩음이다. 이 파일을 커밋하면 pre-commit이 파일 전체를
보므로 둘 다 지금 코드에 맞췄다. 둘만 골라 돌리니(`tools/mutate.py … 6 24`) 기준선(고친 판의 러너 시험 48개)이 초록이고 둘
다 빨갰다.

다시 돌린 것: 고친 판에서 러너 시험 파일 전체(위 기준선), 바뀐 파일의 린트·포맷, 마크다운 표 검사, 러너를 겨누는 변이 명세
셋의 `--check`가 초록이었다. 손으로 치는 다섯은 커밋 `4537a3a5`의 pre-commit이 모두 Passed로 갈음했다(pytest 875초,
web-verify 289초, run-hooks 82초, 변이 표 `--check` 포함). 인용 대조 경고 여섯 가운데 다섯은 지운 옛 문구와 줄바꿈으로 갈린
문구를 옮긴 것이라 두었고, `implement`의 문구를 글자가 다르게 옮긴 하나를 고쳤다.

밀 주장. 반영으로 새로 쓴 사실 문장이다. PR 직전 `bug-perf-review`의 브리프에 그대로 넘긴다(`code-review` 6단계 1, 이 커밋 뒤
main에서 들어왔다).

1. `tools/run_hooks.py` `notice_outcome`: "표의 context 사례는 사용자 몫을 요구하지 않으므로(대부분의 훅은 모델에게만
   알린다) `outcome_of` 에 넣지 않는다". 시험 `test_래퍼의_알림은_사용자에게_가는_systemMessage_가_없으면_context_여도_어긋남이다`의
   독스트링도 같은 말이다.
2. `tools/run_hooks.py` `outcome_of`: "`notice` 는 사용자에게만 가는 `systemMessage` 하나다 — 표의 훅이 사람에게만 알릴 때와
   래퍼가 Stop 에서 없는 훅을 지나갈 때(대기열 93)의 출력이다."
3. `tools/run_hooks.py` `_launch`: "래퍼는 `root` 의 것을 띄운다."
4. 시험 `test_종료_코드와_출력을_기대로_읽는다`: "notice 는 `test_사용자에게만_가는_systemMessage_는_notice_다` 가 본다."
5. 시험 `test_빈자리_셈은_notice_를_발동으로_센다`: "사용자에게만 알리는 훅도 notice 사례를 발동으로 둔다."
6. 명세 94행: "명세를 쓸 때의 러너는 사람에게만 보이는 `systemMessage` 하나(`notice`)를 표의 기대 값으로 받지
   않았다(`Expectation`이 deny·block·context·silent 넷이었다)." 와 "티켓 01이 고쳤다(일지 2026-10-16-47)."
7. 티켓 3행: "이 티켓 전의 러너의 기대는 deny·block·context·silent 넷이었고, `notice`는 래퍼가 없는 훅을 지나갈 때의 판정으로만
   쓰였다."
8. 변이 명세 머리: "기대 값 밖의 넷은 그 전부터 있던 코드다".
9. 이 일지: "`tools/hook_*.py`를 grep하니 `systemMessage`를 내는 훅은 그 하나였다"와 "24번은 들여쓰기가 8칸이라 기점의
   코드(4칸)에서도 원문이 없던 옛 썩음이다."
10. 프로브 README의 새 행과 `launch_hook_mutations.toml` 행 끝에 더한 2026-10-16 결과.
