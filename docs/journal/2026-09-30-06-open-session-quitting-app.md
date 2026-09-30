# 2026-09-30 (06) open-session이 새 세션을 열지 못하던 원인

티켓 08 세션(일지 2026-09-30-05)이 병합 뒤 다음 세션을 열다 `fired=` 뒤 `page=` 없이 30초 시간 초과로 멈췄다. 사용자가
원인을 찾아 해결하라고 했다. 브랜치는 `chore/open-session-quitting-app`, 워크트리다.

> 사용자: "새 세션 여는 거 계속 실패하는 이유가 뭔지 찾아서 해결해줘."

## 원인

**데스크톱 앱이 업데이트를 위한 끝내기를 시작하고 끝내지 못한 채 떠 있었고, 그 상태의 앱은 딥링크를 로그 없이 버린다.**

- 앱(2.9939.2)의 `second-instance` 처리기는 첫 줄이 `if(ej())return;`이고 `ej`는 끝내기 깃발 셋(`JA||YA||XA`)이다. `JA`는
  업데이트를 위한 끝내기, `YA`는 끝내기 처리기가 도는 중, `XA`는 끝낼 준비가 됨이다. 셋 다 `false`로 시작하고 다시 꺼지는 것은
  `YA`뿐이다(정리의 `finally`). 설치본의 `app.asar`를 풀지 않고 읽었다(`probes/asar_grep.mjs`).
- 앱의 `main.log`에 09-29 12:19:27·28의 `CLI exit before update`, `Session stop before update took`,
  `beforeQuitForUpdate handler fired, going down for update`가 있다. 앞의 둘은 업데이트를 위한 끝내기 함수(`Hln`, 업데이트 배너와
  스텔스 업데이트가 함께 부른다)가 첫 줄에서 `JA`를 켠 뒤에 찍는다. 도는 주 프로세스는 09-29 10:28:14부터 그대로다. 끝내기가
  시작됐는데 앱이 끝나지 않았다. 그 뒤의 딥링크는 모두 두 번째 인스턴스의 기동 줄(`Starting app`에서 `Not main instance`까지)만
  남겼다.
- **앱 안의 재시작은 이 상태를 풀지 못한다.** 업데이트 배너(`restartToUpdate` → `quitClaudeAppAndInstallUpdate` = `QA`)와 메뉴의
  끝내기(`$A`)가 모두 `ej()||`로 막혀 있다. 09-29 10:28의 재시작 앞에도 끝내기 처리기의 줄이 없어, 밖에서 프로세스를 끝낸
  모양이다(셀프 리뷰 두 축이 짚었다. 처음에는 배너의 재시작을 처방했다).
- 딥링크마다 새 세션 화면이 서기까지의 초를 로그로 쟀다(`probes/deeplink_timeline.ps1`). 09-28 22:53까지는 대체로 `page+0s`였고
  (+0이 아닌 것도 있다. 09-23 17:07~17:17과 09-26 01:51, 원인은 재지 않았다) 09-29 07:50부터는 한 번도 +0s가 아니다. 07:50~10:27은
  03:24의 같은 끝내기(`beforeQuitForUpdate`)가 남긴 앞 프로세스이고, 10:28에 밖에서 끝내고 다시 켜 풀렸다가 12:19에 다시 걸렸다.
- **"계속 실패"가 맞다.** 07→08의 세션도 스크립트는 실패했고 사람이 손으로 열었다. 이 세션의 첫 메시지가 스크립트가 옮긴
  문장(`.claude/skills/implement/SKILL.md 를 읽어…`)이 아니라 `/implement` 원문을 붙여 넣은 것이었다. 09-29 12:28부터 09-30 17:04
  까지 두 번째 인스턴스의 기록 열한 번이 모두 새 세션 화면이 +24초~+1741초 뒤에야 섰다(사람이 연 때다). 오늘 20:16의 것은 사람이
  열지 않아 끝내 서지 않았다. 두 번째 인스턴스의 기록은 딥링크만이 아니라 앱을 다시 켜려 한 클릭 같은 것도 센다.

## 잰 것과 버린 가설

- **피드백 루프.** 딥링크를 쏘고 프롬프트가 든 입력창(Edit)이 서는지만 보는 프로브(`probes/probe_deeplink.ps1`, 보내지
  않는다). ASCII 한 줄도 `none after 20s`였다. 지시문의 내용이 아니라 앱의 상태다.
- **버린 것.** URL 길이(1928자, 상한 8000), 모니터 절전(`idle=84s`, PR #62의 원인), 판의 어긋남(설치된 패키지와 도는 프로세스가
  모두 2.9939.2), 딥링크 경로(`code/new`뿐 아니라 기존 세션의 링크도 화면을 바꾸지 못했다), 스텔스 업데이트의 시작 줄
  (`Triggering stealth update`) 자체. 이 줄은 `tryTrigger`가 끝내기(`performStealthUpdate`)를 부르기 전에 찍어 끝내기가 시작됐는지
  말하지 않는다. 처음에는 17:04를 성공으로 읽어 이 줄들을 원인에서 뺐는데, 17:04도 실패였다(위).
- **첫 관찰.** 실패 직후 앱의 접근성 트리에 지시문이 든 입력창이 없었다. 화면을 열고 못 알아본 것이 아니라 열리지 않았다.
- **pwsh의 출력 인코딩.** pwsh는 파이프로 가는 출력을 콘솔 코드 페이지(cp949)로 써서 파이썬이 UTF-8로 풀지 못하고 stderr가
  `None`이 됐다. 처음에는 그 `AssertionError: None`을 `shutil.which`가 pwsh를 못 찾은 것으로 잘못 읽었다(표준 축이 반례를 냈다.
  which는 경로를 준다). 테스트는 pwsh 쪽에서 UTF-8로 고정하고 파이썬 쪽은 `errors="replace"`로 받는다.

## 한 것

- **`tools/open_session.ps1`.** 쏘기 전에 앱의 로그에서 주 프로세스가 선 뒤의 끝내기 표지를 찾는다. 있으면 쏘지 않고
  `quitting=<시각 메시지>`와 처방(작업 관리자에서 앱을 끝내고 다시 켠다)을 내고 멈춘다. 판정은 순수 함수
  `Find-QuitMarker`(로그 줄, 주 프로세스가 선 시각)이고 표지는 `JA`·`XA`를 켠 뒤의 다섯 문구다. `YA`의 표지는 보지 않는다(풀린다).
  주 프로세스(`app\Claude.exe` 가운데 `--type=`이 없는 가장 오래된 것)와 로그(MSIX와 일반 설치 가운데 최근에 쓰인 곳, 주 프로세스
  뒤에 쓰인 `main1.log`까지)를 찾는 것은 `Get-AppQuitMarker`다. 판정하지 못하면 막지 않고, 판정 중의 예외는 `quitcheck=`로 남기고
  지나간다. 고친 스크립트를 지금의 앱에 돌려 `quitting=2026-09-29 12:19:27 [CCD] CLI exit before update…`로 곧바로 멈추는 것을
  봤다(2.49초, pwsh 기동 포함).
- **`open-session` 스킬.** 3단계에 `quitting=`의 처리(사람에게 작업 관리자에서 앱을 끝내고 다시 켜 달라고 부탁하고 턴을 끝낸다,
  쏘지 않았으니 다시 돌려도 된다)와 `quitcheck=`, "막히면"에 `quitting=`의 예외와 표지 없이 `page=`에서 끝났을 때 볼 자리
  (`deeplink_timeline.ps1`, `asar_grep.mjs`)를 적었다.
- **런북.** `kickoff/facts.md`(부록 C)에 사실 한 행, `KICKOFF.md`의 open-session 항목에 한 문장.
- **테스트.** `tests/tools/test_open_session.py` 9. 파워셸 AST에서 함수 하나를 떼어 pwsh로 부른다. 대기열 17(open_session.ps1에
  회귀 시험이 없다)이 적은 그 모양의 이음매가 처음 저장소에 섰다. 17의 대상(`Normalize-Slash`·`Test-Needle`)은 아직이다.
- **변이.** `probes/open_session_quit_mutations.toml`의 다섯이 모두 기대대로 빨강이다(`tools/mutate.py`).
- **프로브.** 진단에 쓴 셋(`probe_deeplink.ps1`, `deeplink_timeline.ps1`, `asar_grep.mjs`)을 `.scratch/harness/probes/`에 남겼다.
- **web 테스트 하나(커밋 때 드러났다).** 첫 커밋의 pre-commit에서 `web/eslint.config.test.ts`의 판정 범위 테스트가
  `expected [ …(102) ] to include 'eslint.config.test.ts'`로 빨갰다. 워크트리에서 git이 훅 자식에 내보낸 `GIT_DIR`이
  `GIT_WORK_TREE` 없이 남아, `web/`에서 부른 `git ls-files`가 cwd를 작업 트리의 뿌리로 삼았다. 2026-09-28에 파이썬 쪽이 겪고
  `tests/conftest.py`로 막은 함정이 TS 테스트에는 닿지 않았다. `GIT_DIR`을 워크트리 자신의 `.git`으로 세워 같은 빨강을 재현하고,
  그 호출의 `env`에서 `GIT_*`를 벗겨 초록을 봤다. 런북 부록 A의 그 행을 넓혔다.

## 셀프 리뷰

`/code-review`, base `447c068`, 추적 파일 4, 미추적 6, 커밋 0.

- **두 축이 같은 Major 하나를 짚었다.** 처음의 처방(업데이트 배너로 다시 시작)이 이 상태에서 아무 일도 하지 않는다. 앱 코드로
  확인하고 처방을 작업 관리자로 바꿨다. 재시작 뒤 딥링크가 다시 먹는지는 이 세션이 재지 못한다(앱을 끝내면 이 세션도 멈춘다).
- **고친 Minor.** `YA` 표지(풀리는 깃발)를 뺐다(변이 하나를 더했다), `Session stop before update took`과
  `Update check still in flight`를 더했다(`CLI exit before update`는 로컬 CLI 세션이 있을 때만 찍힌다), 판정 중의 예외가 쏘기를
  막지 않게 했다, 주 프로세스 전의 돌림 파일을 건너뛴다, 런북 두 곳, 스킬의 "막히면"이 볼 자리, "21:54까지 +0s"의 틀린 문장
  셋, 대기열 72의 수.
- **고친 Nit.** `shutil.which` 주장, 30시간 → 32시간 넘게, "`Not main instance`만", 스텔스 업데이트만 부르는 것처럼 쓴 문장,
  배너를 원인에 이은 문장(배너는 새 판이 준비됐다는 뜻이다), 변수 이름(`$quitMarker`, `$logs`).
- **남긴 것.** `uv run pytest -q`가 이제 pwsh를 전제한다. CI의 ubuntu 러너와 이 기계에는 있다. `tech.md`의 테스트 행에 적는 것은
  ADR 뒤의 일이라 남겼다(PR #107 claude-review가 추적을 권해 대기열 17의 행에 더했다). 함수 이름의 `Find-` 동사가 이 파일의 다른 `Find-`(접근성 트리 탐색)와 어휘가 갈린다는 Nit은 두었다.

## 검사

- `uv run pytest -q` 1024 passed(이 PR의 9 포함). `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`,
  `uv run lint-imports` 초록. web은 테스트 파일 하나를 고쳤고 `pnpm -C web verify`는 pre-commit이 돌린다. 인용 대조가
  KICKOFF.md 234행의 옛 인용(이번에 고친 줄에 원래 있던 것) 하나를 경고했고 두었다.

## 남긴 것

- **앱의 결함은 이 저장소 밖이다.** 끝내기를 시작하고 끝내지 못한 앱이 32시간 넘게 딥링크를 버렸고, 앱 안의 재시작도 막혔다.
  스크립트는 알아보고 멈출 뿐 풀지 못한다. 앱 쪽에 알리는 것은 사용자의 일이다(앱의 피드백).
- **표지는 앱 코드의 로그 문구다.** 판이 바뀌어 문구가 달라지거나 `JA`를 켜고 표지를 찍기 전에 멈춘 끝내기면 이 판정은 못 보고
  전처럼 `page=`에서 끝난다. 스킬의 "막히면"이 그때 볼 자리를 적었다.

## 회고

후보 하나를 냈고 승인됐다.

> 사용자(질문에 답): "올린다 (추천)"

- **72(새로).** 이 실패가 되풀이되는 동안 어느 일지에도 적히지 않았다. open-session은 일지가 병합된 뒤에 돌아 그 결과를 적을
  자리가 없다. 손으로 연 세션은 첫 메시지로 알아볼 수 있다(첫 줄이 ASCII `/`의 원문). 그 세션의 훅이 앞 세션의 실패를 일지에
  적으라는 계기를 넣는다. `held=` 뒤 사람이 `／`를 고쳐 보낸 것과 가르는 법은 반영 때 정한다(셀프 리뷰의 반례).
- 대기열 17(open_session.ps1의 회귀 시험)은 이번에 이음매(AST에서 함수를 떼어 pytest로 부른다)가 섰고, 대상 함수 둘은
  남았다. PR #107의 claude-review가 `Get-AppQuitMarker`의 선택 부분(주 프로세스, 로그 파일)에 시험이 없다는 Minor 둘을
  냈고, 같은 이음매로 잴 대상이라 17의 행에 근거로 더했다. 표지 문구가 정규식과 테스트에 겹친다는 Minor 하나는 두었다.
  parametrize는 정규식 조각이 아니라 로그 한 줄 전체(앱의 오타 `Successully`까지)를 담는다.
- PR #107의 CodeRabbit 지적으로 `probes/probe_deeplink.ps1`이 첫 줄의 글자 대신 길이만 찍는다. 대화에 찍힌 첫 줄은
  open-session의 다음 전송이 `stale=`로 걸러야 하는 흔적이다.

## 다음

- 사용자가 작업 관리자에서 앱을 끝내고 다시 켠 뒤, `probes/probe_deeplink.ps1`이 `page=`를 내는지 본다. 그다음 일지
  2026-09-30-05의 "다음"(대기열 51·55·66·67과 69의 chore 배치)을 연다. 그 지시문은 2026-09-30-05 세션이 냈다.
