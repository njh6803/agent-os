# 2026-10-12 (23) 변이 도구가 변이마다 시간 제한을 두고 번호와 커밋으로 고른다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 139·152·193을 한 PR로 닫는다. 셋 다
`tools/mutate.py` 한 파일이다. 세션은 주 체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈 뒤
`EnterWorktree(name=mutate-timeout-and-select)`로 들어가 `origin/main`(`f5052ed`)에서
`chore/mutate-timeout-and-select`를 땄다.

> 사용자: "대기열 139·152·193을 한 PR로 반영한다(tools/mutate.py: 변이마다 시간 제한, 원문 끝 줄바꿈 규칙, 따옴표 없는 변이 선택)"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `0661d72`에서 `f5052ed`로 당겼다. 스킬 파일은 바뀌지 않았다.
- **지운 것.** 로컬 브랜치 `docs/admin-design-direction`.
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, 분리 HEAD 셋(`confident-wright-2d3ebf`,
  `elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`), PR 머리가 다른 `skill-check-and-retro-section`, 제목 모를
  세션(`docs/admin-style-spec`)이 돌아 넘긴 `spec-pipeline-and-pytest-ids`, 등록 없는 폴더 여섯(대기열 148).
  지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **시간 제한은 변이마다, 기본 600초(139).** 변이 표의 `timeout`이고 명령 한 번에 걸린다(`repeat`면 번마다).
  기준선은 러너와 인자의 짝마다 한 번이라 그 짝을 쓰는 변이 가운데 가장 긴 제한을 받는다. 기본값은 지금 표들이
  한 번에 쓰는 시간(mutate.py 출력의 pytest 시간으로 번마다 28~87초, 일지 2026-10-12-16)과 pre-commit의 web
  verify(251초, 같은 일지)보다 넉넉하고, 사건에서 10분 넘게 돈 변이는 이 값에서 끊긴다. 넘긴 결과는 끊기 전의
  출력이 무엇이든 오류로 판정하고, 남은 반복(`repeat`)을 건너뛰어 되돌린 뒤 다음 변이로 간다. 끝나지 않는 변이
  하나가 표 전체를 멈추지 않는다. 반복을 건너뛰는 것은 셀프 리뷰가 짚었다(아래).
- **넘기면 띄운 프로세스까지 끝낸다.** 러너의 시그니처에 시간 제한을 넣고 실제 러너를 `subprocess.run`에서
  `Popen`과 `communicate(timeout=…)`으로 바꿨다. `subprocess.run`은 시간을 넘기면 `process.kill()`로 직접 띄운
  자식만 끝내고, 윈도우에서는 그 뒤 남은 출력을 `communicate()`로 다시 기다린다(CPython 3.12.10의 `subprocess.run`을
  `inspect.getsource`로 읽었다).
  손자가 출력 파이프를 쥐면 거기서도 멈춘다. 이 PC의 uv 가상 환경에서 `python.exe`는 진짜 인터프리터를 자식으로
  띄우는 실행기라, 직접 띄운 자식만 끝내면 진짜 프로세스가 남는다(`.venv/Scripts/python.exe`로 띄운 인터프리터의
  부모가 메모리 3.4MB의 `python.exe`였고 `sys._base_executable`이 설치된 인터프리터였다. `tasklist`로 손으로
  봤다). 윈도우는 `taskkill /F /T`가 부모를 따라 찾고, POSIX는 자식을 `start_new_session`으로 띄워 그 프로세스
  그룹을 `killpg`로 끝낸다. `taskkill`을 띄우지 못하거나 그룹을 끝내지 못해도 자식은 끝낸다. 기다리는 동안
  Ctrl+C가 나도 같이 끝낸 뒤 다시 던져 `finally`의 되돌림이 돈다.
- **그만 읽은 파이프는 닫지 않는다.** 처음 판은 `with Popen`으로 열었다. 남은 손자가 출력 파이프를 쥔 경우를 재는
  시험이 출력을 그만 읽었다는 문구는 냈는데 20초(손자가 스스로 끝나는 시간) 뒤에야 돌아왔다. `with`가 빠져나오며
  파이프를 닫는데, 윈도우에서는 그 파이프를 읽던 스레드가 닫기를 손자가 끝날 때까지 막았다. 그래서 `with`를 걷고
  다 읽은 파이프만 `communicate`가 닫게 했다. 그 시험은 고치기 전에 빨갰고 고친 뒤 5초에 지난다.
- **번호와 `--since`(193).** 번호는 표에 적힌 차례(1부터)이고 출력의 줄 머리(`== 3. 이름:`)와 어긋났을 때의 마지막
  줄(`다시 돌릴 번호: 1 3`)에 찍혀, 어긋난 것만 그 줄을 그대로 붙여 다시 돌린다. 고른 뒤에도 번호는 표의 차례다.
  번호와 가를 수 없어 숫자뿐인 이름은 변이 파일 오류다. `--since <커밋>`은 표가 든 저장소에서
  `git show <커밋>:./<표>`로 그때의 표를 읽어, 새로 더했거나 무엇이든 달라진 변이를 고른다. 달라짐은 변이 모델
  전체와 그 변이가 쓰는 러너의 비교다. 원문만 보면 기대나 시험을 바꾼 변이를 놓친다. 그 커밋에 표가 없으면 모두
  새것이고, 고를 것이 없으면 2로 끝난다. 잘못 준 커밋이 0으로 끝나면 잰 것처럼 보이기 때문이다. `--check`도
  `--since`로 고른 것만 본다.
- **전체와 고른 것의 기준.** 승인된 기준(시험을 고치거나 지웠으면 전체, 더하기만 했거나 코드만 바꿨으면 고른
  것)을 독스트링의 고르기 문단에 적고, 그 기준이 못 보는 것(코드만 바꾼 판에서 원문이 그대로인 변이도 둘레가
  바뀌어 결과가 달라질 수 있다)을 함께 적었다. 이 PR은 시험을 고쳤으므로(가짜 러너 열여덟의 시그니처) 그 기준대로
  `mutate.py`를 재는 기존 변이를 전부 다시 돌렸다. 표 셋(`mutate_runners`, `mutate_restore`, `mutation_check`)과
  `retro_hook` 표의 두 변이다(검사 절). 첫 판에서 `retro_hook`의 둘을 빠뜨린 것은 셀프 리뷰가 잡았다.
- **바깥의 `timeout` 명령을 걷었다.** 변이 표 머리 둘과 프로브 README 행 둘이 `PYTHONUTF8=1 timeout 3600 uv run …`
  처럼 도구를 바깥에서 감쌌다. 그것이 죽이면 독스트링의 못 보는 것(강제 종료)이라 되돌림이 돌지 않을 수 있다.
  시간은 변이마다의 `timeout`으로 걸고 바깥의 상한은 표 전체보다 넉넉히 준다고 독스트링에 적었다.
- **152는 독스트링 한 문장과 시험 하나.** 닫는 `'''`를 다음 줄에 두면 그 앞의 줄바꿈이 원문에 들어, 줄의 일부만
  적은 원문은 맞지 않는다. 다음 줄에 닫은 줄의 일부, 같은 줄에 닫은 줄의 일부, 다음 줄에 닫은 온전한 줄의 세
  경우를 `check`의 종료 코드와 "원문이 0번 있다" 표지로 잰다.

## 바꾼 것

- `tools/mutate.py`: 변이의 `timeout`과 `DEFAULT_TIMEOUT`, `CommandResult.timed_out_after`, 러너의 시간 제한 인자,
  `judge`의 끊긴 결과, 기준선의 가장 긴 제한, 끊기면 반복 건너뛰기, `run_command`의 `Popen`과 `_kill_tree`·`_drain`,
  번호 고르기와 숫자뿐인 이름 거부, `changed_names`·`changed_since`, 출력의 번호와 `다시 돌릴 번호` 줄, 인자를
  가르는 `_parse`·`_Args`·`_UsageError`, `--since`가 고른 것을 내는 `_since_picks`. 독스트링의 사용법·고르기·변이
  파일·하는 일 3·4·제자리가 아닌 실행·못 보는 것.
- `tests/tools/test_mutate.py`: 가짜 러너 열여덟과 타입 별칭의 시그니처, 새 시험 함수 스물(시간 제한 넷, 실제
  러너 다섯, 152 하나, 고르기 열), 기존 시험 하나에 `--since`를 섞는 경우.
- `.scratch/harness/probes/`: 새 표 `mutate_timeout_select_mutations.toml`, 원문이 옮겨 간 `mutate_runners`
  다섯·`mutation_check` 셋, `mutate_restore` 7번의 고르기와 주석, 바깥 `timeout`을 걷은 표 머리 둘, README 행
  넷(새 행 하나와 다시 돌린 셋)과 바깥 `timeout`을 걷은 행 둘.
- `.scratch/retro-queue.md`: 139·152·193 닫힘. `KICKOFF.md`의 도구 설명 한 문장.

## 잔존 grep

바깥 `timeout` 명령으로 도구를 감싼 안내(`timeout [0-9]+ uv run`)는 `.scratch`와 마크다운에서 찾아 표 머리 둘과
README 행 둘을 고쳤고, 남은 것은 일지(기록)뿐이다. 옛 사용 안내 "아는 것은 --check 하나다"와 옛 고르기는 셀프
리뷰의 명세 축이 살아 있는 문서(스킬, rules, operations.md, KICKOFF.md, PR 템플릿, 다른 도구의 독스트링)에서 찾아
고친 프로브 원문 밖에 없다고 했다.

## 검사

- 시험은 빨강부터 봤다. 첫 판의 새 시험은 없는 이름(`changed`)의 import에서 수집 오류로 빨갰다. 남은 손자 시험은
  `with Popen`을 걷기 전에 20초 걸려 빨갰다(어떻게 했나). Ctrl+C 시험은 처음에 시험 자체의 잘못으로 빨갰다.
  `Popen.communicate`를 통째로 바꿔 두어 `_kill_tree`가 띄운 `taskkill`의 기다림도 끊겼고, 처음 한 번만 끊게
  고쳤다.
- 변이는 두 판을 돌렸다. 시험을 고쳤으므로 고르기 기준대로 `mutate.py`를 재는 변이 전부다. 판마다 표를 차례로
  도는 스크래치 스크립트로 돌렸고, 표 전체의 시간은 그 스크립트가 앞뒤로 찍은 `date`로 손으로 봤다.
  - 첫 판(구현 뒤): 새 표 스물넷 모두 빨강(481초), `mutate_runners` 서른(원문 넷을 고친 뒤, 635초),
    `mutation_check` 여덟(원문 셋을 고친 뒤, 186초)이 모두 기대대로였다. `mutate_restore`는 일곱 가운데 7번(초록
    기대)이 빨갰다. 같은 PR #115의 리뷰 반영이 더한 시험이 그 변이도 잡기 때문이고, 이 PR 전부터 낡아 있었다(그
    시험이 붙잡는 "처음부터 모든 파일을 쥐기"는 이 PR이 건드리지 않았다).
  - 둘째 판(셀프 리뷰 반영 뒤): 새 표 스물여섯(555초), `mutate_runners` 서른(536초), `mutate_restore`
    일곱(129초, 7번은 리뷰 전의 시험 하나만 `-k`로 골라 초록), `mutation_check` 여덟(181초),
    `retro_hook`의 26·27(13초)이 모두 기대대로였다. pytest 한 번은 mutate.py 출력으로 14~34초였다(`-k`로 고른 것은
    1초 안). 실제 프로세스를 띄우는 시험 셋이 13.07초 가운데 10.1초였다(셀프 리뷰의
    표준 축이 `--durations`로 손으로 봤다). 그래서 2026-10-01에 표 전체가 67초였던 `mutate_runners`(프로브 README)가
    536초가 됐다.
  - 새 고르기를 그 자리에서 썼다. 첫 판 뒤 `mutate_restore` 7번의 기대를 고치고
    `tools/mutate.py .scratch/harness/probes/mutate_restore_mutations.toml 7`로 그 하나만 다시 돌렸고, 둘째 판의
    `retro_hook`도 번호(`26 27`)로 골랐다. 둘째 판이 잰 `tools/mutate.py`와 시험은 이 일지가 처음 든 커밋의 것과
    같다(다음에 `--since`로 견줄 커밋).
- 검증 명령: `ruff check`·`ruff format --check`, `pyright` 0 errors, `lint-imports` 5 kept, 지침 검사와 타입 우회
  검사가 초록이었다. `uv run pytest -q`는 셀프 리뷰 전에 2095 passed(7 deselected)였고, 반영 뒤에는
  `test_mutate.py` 123 passed와 커밋의 pre-commit으로 갈음한다. web 파일은 바꾸지 않았다.
- 실제 러너 시험은 이 윈도우에서 돌았고, POSIX의 프로세스 그룹 길은 CI의 리눅스 pytest가 돈다.
- 워크트리라 `uv sync`와 `pnpm -C web install --frozen-lockfile --offline`을 먼저 쳤다.

## 셀프 리뷰

`/code-review`(기준 `f5052ed`, 수정 10·미추적 2, 커밋 0). 두 축 모두 Critical·Major가 없었다. 표준 축은 Minor
여덟·Nit 여섯, 명세 축은 Minor 넷·Nit 셋이었고 둘이 겹친 것이 셋이다(`repeat`, README의 `mutate_restore` 행,
`retro_hook`).

- **고친 것.**
  - 둘 다: 시간 제한을 넘긴 뒤에도 남은 `repeat`를 돌아, 변이가 든 채 제한의 `repeat`배를 썼다. 첫 끊김에서
    반복을 멈추고 시험과 변이를 더했다.
  - 둘 다: 프로브 README의 `mutate_restore` 행이 7번을 여전히 초록 기대로 적었다. 명세 축은 7번을 빨강 기대로 바꾸면
    6번과 같은 변이가 되어 대조군의 뜻이 사라진다고 짚었다. 기대를 초록으로 되돌리고, 리뷰 전의 그 시험 하나를
    `-k`로 골라 원래 뜻(그 시험만으로는 지나간다)을 되살렸다.
  - 둘 다: 일지가 다시 돌린 것을 "기존 표 셋"이라 닫아, `retro_hook` 표에서 `mutate.py`와 그 시험을 고치는 두
    변이(26·27)를 빠뜨렸다. 둘째 판에 넣었다.
  - 표준: `main`의 try 블록에 `--since` 처리·출력·이른 반환이 쌓였다(`CODING_STANDARDS.md`의 에러 처리와 정상 흐름
    분리). 인자 가르기를 `_parse`로, 사용법 오류를 `_UsageError`로, `--since`가 고른 것을 `_since_picks`로 뺐다.
    번호 표를 두 번 짓던 것도 `_numbers` 하나로 모았다.
  - 표준: 실패를 기대하는 새 시험 넷이 까닭을 단언하지 않았다(대기열 144). 원문 0번, 숫자뿐인 이름, 커밋을 풀지
    못함, 표 밖의 번호의 표지를 보게 했다.
  - 표준: "모두 끝낸다"는 닫힌 주장이 못 보는 것과 어긋났다. 판정 요약은 "끊었다"로, 독스트링은 "띄운 프로세스까지
    끝낸다(못 보는 것은 아래)"로 고쳤다. `_kill_tree`의 "자식만은 끝낸다"를 재는 시험(`taskkill`을 띄우지 못하고
    그룹을 끝내지 못할 때)과 변이를 더했다.
  - 둘 다(Nit 포함): POSIX에서 남는 손자에 프로세스 그룹만 따로 연 것을 더했다.
  - 표준: 고르기 기준에 이 PR 안의 반례가 있었다. 시험을 더해도 초록을 기대한 대조군은 빨개질 수 있다(`mutate_restore`
    7번). 못 보는 것에 적고, 견주는 쪽이 그 표를 마지막으로 돌린 판이라는 것도 적었다.
  - 명세: `--since`에 어떤 커밋을 줄지 안내가 없었다. 그 표를 마지막으로 돌린 커밋, 이 브랜치의 것만이면
    `origin/main`, 다른 워크트리의 `HEAD`는 고를 것이 없다는 것을 적었다.
  - 표준: README의 시간이 무엇으로 섰는지 불분명했다. mutate.py 출력의 pytest 시간과 손으로 본 벽시계 시간을
    갈라 적고, 판(윈도우 10 19045의 `taskkill`, CPython 3.12.10)을 적었다.
  - 표준 Nit: `CommandResult`의 "끊기 전까지의 출력"을 그만 읽은 경우까지 맞게 고쳤다. `changed`를
    `changed_names`로, 지역 변수와 겹치는 시험 도우미 `_변이`를 `_글자_변이`로 바꿨다.
  - 명세 Nit: 일지의 "사건의 10분보다 짧게"(600초는 10분과 같다)를 고쳤다.
- **남긴 것.** 러너의 위치 인자 `int`(Primitive Obsession)는 명령, 자리, 시간 제한의 셋이라 타입을 따로 둘 값이
  작다. 가짜 러너 열여덟을 고친 것(Shotgun Surgery)은 러너의 계약이 바뀐 몫이다. 이름이 겹치면 안 되는 까닭을
  "이름으로 골라 다시 돌린다"로 대는 오류 문구(명세 Nit)는 이름 고르기가 여전히 있어 참이다.
