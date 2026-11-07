# 2026-11-07 (03) 리뷰 봇 워크플로가 대기열 폴더와 티켓 파일을 기록으로 받는다 (retro-queue-per-item 03)

세션 제목: `feature/03-review-bot-path-filter`. 브랜치 `feature/03-review-bot-path-filter`, 워크트리 `.claude/worktrees/03-review-bot-path-filter`. 모델 Sonnet 5.5 / high. 서브에이전트를 셋 띄웠다(셀프 리뷰 표준 축, 명세 축, PR 직전 `coderabbit-review`). 아래에서 "서브에이전트 보고"라고 적은 것은 그 보고를 이 세션이 읽은 것이다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/03-review-bot-path-filter.md

> 사용자: 다음 작업: .scratch/retro-queue-per-item/issues/03-review-bot-path-filter.md. 리뷰 봇 워크플로가 대기열 폴더와 티켓 파일을 기록으로 받게 거르는 경로를 고친다 … 이번 요청 범위: PR과 병합까지

## 한 일

- **시작 전.** 제목을 지시문의 브랜치로 바꾸고 `tidy-checkouts`를 돌았다. 루트를 `288686a5`에서 `9a1d8542`로 당겼고 로컬 브랜치 `worktree-02-retro-queue-one-file-per-item`을 지웠다. 병합된 워크트리 `05-default-model-required-and-checked`는 `agent-os.exe`와 `python.exe` 둘이 모듈을 올려 두어 이름 바꾸기가 막혀(`WinError 5`) 남겼다. 이 줄들은 `judge`와 `remove`의 출력을 손으로 읽은 것이다. 그 뒤 `EnterWorktree`로 들어가 브랜치 이름을 `git branch -m`으로 맞췄다.
- **워크플로.** `.github/workflows/claude-code-review.yml`의 마지막 스텝이 거르는 정규식을 `^(docs/journal/|\.scratch/retro-queue/|\.scratch/[^/]+/issues/[^/]+\.md$|\.scratch/harness/probes/)`로 바꿨다. 옛 파일 갈래(`\.scratch/retro-queue\.md$`)는 지웠고, 티켓 갈래(`.scratch/<폴더>/issues/` 바로 아래의 `.md`)를 더했다. `::error::` 문구는 "일지·대기열·티켓·하네스 탐침 밖의 파일"이 됐고 곁 주석도 같이 고쳤다.
- **탐침.** `.scratch/harness/probes/review_workflow.py`의 대기열 사례를 폴더로 바꾸고 사례를 19개에서 31개로 늘렸다. 티켓만 싣는 사례, 대기열 폴더의 새 항목과 그 아래 더 깊은 경로, 옛 대기열 파일, 기능 폴더의 `spec.md`, `issues/` 아래 더 깊은 경로, `issues/`가 아닌 폴더, 기능 폴더 없는 `issues/`, `.md`가 아닌 파일, 티켓 이름의 앞뒤에 글자가 붙은 경로가 새 사례다. `RECORD_WORDS` 검사를 더해 함께 실음의 오류 문구가 일지·대기열·티켓·하네스 탐침을 모두 드는지 본다.
- **README.** `.scratch/harness/probes/README.md`의 `review_workflow.py` 행에서 사례 수와 기대 서술, 결과를 고쳤다. 바로 위 `journal_cite_scan.py` 행(04의 몫)은 건드리지 않았다.
- **티켓.** `Status:`를 `in-progress`로 바꾼 것이 첫 편집이었고, PR을 열기 전에 `done`으로 바꿨다. 한 커밋으로 끝나므로 `in-progress`는 커밋에 실리지 않는다.

## 결정·번복·확인

- **빨강을 먼저 봤다(원칙 II).** 탐침만 새 기대로 바꾼 채 옛 워크플로에 돌려 `어긋남 20/32`가 나온 것을 보고 나서 워크플로를 고쳤다. 고친 뒤 `어긋남 0/32`였다(탐침이 센 값. `PYTHONUTF8=1 uv run python .scratch/harness/probes/review_workflow.py`). 셀프 리뷰 반영으로 사례를 하나 더한 뒤에는 작업 트리 0/33, `origin/main`(`9a1d854`) 21/33이다(같은 명령, `origin/main`은 인자로 줬다). 21 가운데 다섯은 판정 자체가 어긋났고 열여섯은 오류 문구에 티켓이 없어서였다. 이 분류는 어긋남 줄을 손으로 읽어 가른 것이다.
- **PR 템플릿 43행은 고치지 않았다.** 일지 2026-11-07-02의 "다음"이 03의 몫으로 `.github/PULL_REQUEST_TEMPLATE.md:43`의 경로 문구를 꼽았다. 그 줄은 "일지·대기열 등. 원천은 그 스텝의 패턴"이라고 적고(코드를 읽었다), 그 템플릿은 그 줄이 말하는 허용 경로 밖의 파일이며 티켓의 범위 문장(워크플로, 탐침, 티켓, 일지, 대기열 항목 밖의 파일을 싣지 않는다)도 같다. 문구가 아직 맞아서 고칠 이유도 없다. 02의 "다음"이 꼽은 `claude-code-review.yml:77·99`는 고쳤다.
- **폴더는 앞부분만 본다.** 일지(`docs/journal/`)와 대기열(`.scratch/retro-queue/`)은 접두 규칙이라 그 아래 더 깊은 경로도 기록으로 지난다. 표준 축이 이 동작을 고정한 사례가 없다고 짚어(Minor) 사례 하나와 주석 한 줄을 더했다.
- **`issues/README.md`도 티켓 모양이다.** 명세 축의 사소한 관찰이다. 정규식은 티켓의 정의("바로 아래의 `.md`")를 글자 그대로 구현한 것이라 `.scratch/<폴더>/issues/README.md`도 받는다. 요구에 없어 그대로 두었다.
- **패턴 변이 측정(손으로 본 것).** 스크래치 스크립트 `mutate_pattern.py`(커밋하지 않았다)가 정규식을 아홉 가지로 약하게 바꾼 사본에 탐침을 돌렸다. 대기열 폴더의 끝 슬래시 빼기, 티켓의 끝 앵커 빼기, `[^/]+`를 `.+`로 바꾸기 둘, 맨 앞 앵커 빼기, 옛 대기열 갈래 되살리기, 티켓 갈래 지우기는 어긋남 1~4개로 잡혔다. `[^/]+`를 `[^/]*`로 바꾼 둘(폴더 이름, 파일 이름)은 잡히지 않았다. 코드를 읽어 보면 빈 폴더 이름(`.scratch//issues/…`)과 이름이 `.md`뿐인 파일에서만 달라져 실제 경로에서는 같은 동작이다. 이 측정은 사례를 31개로 늘리기 전의 30사례 판으로 했다.

## 셀프 리뷰 (`/code-review`)

범위: base `9a1d8542`, 파일 넷과 미추적 일지 하나, 커밋 0.

- **표준 축(sonnet·high).** Critical·Major 없음. Minor 둘, Nit 둘이다. 서브에이전트 보고를 이 세션이 읽었고, 탐침 `0/32`와 `origin/main` `20/32`는 서브에이전트가 직접 돌려 같은 값을 얻었다고 적었다.
  - Minor 1(하위 경로를 고정한 사례가 없다): 고쳤다. 사례 `이 워크플로와 대기열 폴더 아래 더 깊은 경로`와 워크플로·독스트링 주석 한 줄을 더했다.
  - Minor 2(일지가 머리 한 줄뿐): 이 일지로 채웠다.
  - Nit 3(독스트링이 반영 전 판의 어긋남을 하나로만 적었다): 고쳤다.
  - Nit 4(`in-progress`는 한 커밋에서 실리지 않는다): 남겼다. 체크박스는 첫 편집으로 한 일을 가리키고, 티켓의 요구를 바꿀 이유가 없다.
- **명세 축(세션의 모델).** 지적 없음. 요구 항목을 모두 충족하고, 이 PR이 싣는 파일이 허용 경로 안에 든다고 정규식을 직접 대 보고 확인했다고 보고했다.
- **밀 주장(반영으로 새로 쓴 사실 문장, 원문).** PR 직전 리뷰가 겨냥하도록 옮긴다.
  - 탐침 독스트링: "대기열 폴더는 일지 폴더처럼 앞부분만 보므로 그 아래 더 깊은 경로도 기록으로 지난다."
  - 워크플로 주석: "일지와 대기열은 폴더라 앞부분만 보고, 그 아래 더 깊은 경로도 기록으로 받는다"
  - 탐침 독스트링: "옛 대기열 파일 사례가 건너뜀으로, 오류 문구에 티켓이 없는 함께 실음 사례들이 문구 검사로 어긋난다."
  - README: "작업 트리는 0/33, 반영 전의 `origin/main`(`9a1d854`)은 21/33 — 다섯은 판정 자체가 어긋났고 … 열여섯은 함께 실음의 오류 문구에 티켓이 없었다"
- **다시 돌린 명령.** 반영 전 전체 `uv run python tools/run_checks.py`는 종료 0이었고 열 검사가 모두 `Passed`였다(`pytest` 397.8초, `web-verify` 553.1초. 러너 출력을 손으로 읽었다). 반영 뒤에는 `uv run ruff check .`와 `uv run ruff format --check .`, 탐침 0/33을 다시 돌렸고, 나머지는 커밋의 pre-commit 결과로 갈음한다.
