# 부록 A. 세팅 중 실제로 걸린 함정

문서를 읽어서는 알 수 없고 겪어야 아는 것. ai-agent-platform과 agent 두 저장소의 실측이다. 원칙 하나로 요약하면 **조용히 통과하는 것을 시끄럽게 만든다.** 환경에 걸린 행은 머리에 표시했다 — [Win] Windows·Git Bash·PowerShell, [Py] 파이썬·uv·pre-commit. 표시 없는 행은 환경 무관이다.

| 함정 | 증상 | 대응 |
|---|---|---|
| [Win] PowerShell here-string | `@`가 커밋 메시지에 새어 들어감 | 여러 줄은 파일로. 지침만으로는 새 세션에서 2/3 위반이라 commit-msg 훅이 거부 |
| 큰 heredoc | Bash 도구의 파서가 깨져 아무것도 실행되지 않음 | 긴 스크립트는 파일로 쓰고 셸에는 경로만. `hook_bash_heredoc` |
| [Win][Py] `PYTHONUTF8=1` 누락 | 한글 출력이 cp949로 깨지고 일부 검사가 통째로 안 돎 | `.claude/settings.json`의 `env`에 넣는다(사용자 설정 env의 다른 값이 Bash 도구에 보이는 것으로 실측. 훅 프로세스 쪽은 재지 못했다). pytest는 conftest에서 stdout 재설정. 훅은 그 값을 가정하지 않고 stdin을 바이트로 읽는다 |
| [Py] 맨 `python` | 프로젝트 인터프리터가 아니다 — 스토어 스텁이면 아무것도 안 하고 pyenv shim이면 다른 버전이 돈다 | `uv run python`. `hook_bash_python_stub` |
| 파이프·체인 뒤의 `$?` | 마지막 명령의 종료 코드라 게이트의 빨강이 가려짐(agent-os 4회) | 판정 명령은 파이프 없이. `hook_bash_gate_pipe`가 경고 |
| [Win] CRLF가 훅 경로를 오염 | 포매터가 엉뚱한 경로를 받음 | 훅에서 `tr -d '\r'`, `.gitattributes`로 LF 고정 |
| [Win] Git Bash `echo`가 백슬래시를 먹음 | JSON 페이로드가 안 파싱돼 훅 시험이 조용히 헛돎 | 페이로드도 파일로 |
| [Py] 추적 파일 0개에서 `pre-commit run --all-files` | 훅 전부 "no files to check"로 exit 0 | 스테이징 뒤 다시 돌리고 `always_run` |
| CI 경로 필터 미매칭 | 필터 구멍이 조용히 job을 skip | 미매칭을 실패로 승격 |
| [Py] 워크트리에서 pre-commit이 돌린 테스트의 `git init` | git이 훅 자식에 `GIT_DIR`을 내보내 임시 디렉터리 대신 그 저장소를 재초기화. 공유 config의 `core.bare`가 true가 되어 체크아웃 전부가 "must be run in a work tree" | `tests/conftest.py`가 저장소를 가리키는 `GIT_*`를 벗긴다. 복구는 `git config core.bare false` |
| 환경 부재로 skip된 테스트 | 초록으로 보임. agent-os는 "CI에서는 에러로 만든다"고 적고 장치가 없었다(2026-09-28 감사) | conftest가 skip을 세션 실패로 만든다(`tests/conftest.py`). LLM 테스트는 키 없으면 실패 |
| 같은 체크아웃을 쓰는 세션 둘 | 커밋이 엉뚱한 브랜치에 들어감. 다른 세션의 커밋이 내 피처 브랜치에(agent-os PR #46, 2026-09-23), 다른 세션이 main으로 옮긴 32초 뒤 내 커밋이 main에(2026-09-27) | main 위 커밋을 막는 훅 `hook_git_main_commit`(뒤의 모양만). 커밋 직전 `git branch --show-current`. 하네스 작업은 워크트리에서 |
| 에이전트의 grep이 `.env`를 읽음 | 키 값이 도구 출력에 실림(agent-os 2026-09-28) | `permissions.deny`로 Read·Edit 거부, Bash·Grep으로 읽는 길(`.env`를 빼지 않은 전체 grep 포함)은 `hook_env_read`가 막는다 |
| 헌법이 "판정자가 있다"고 적었는데 없음 | 그 절이 영영 초록(agent-os 원칙 IV의 플러그인 절, 원칙 II의 skip 절, `@` 임포트 검사가 줄 머리만) | 판정자 주장은 실제 검사와 하나씩 대조. 없으면 테스트를 만들고 문장을 고친다(ADR 0013·0018) |
| 전역 스킬이 프로젝트 스킬을 이김 | `npx skills update` 뒤 낡은 전역이 조용히 이김 | 프로젝트가 관리하는 스킬의 전역 사본을 두지 않는다 |
| 스킬의 `disable-model-invocation` | 지침에 "자동으로 돌린다"고 써도 에이전트가 그 스킬을 못 부름 | 자동으로 돌아야 하는 스킬(retro)만 사본에서 플래그를 뺀다. 사람이 시작을 확인해야 하는 스킬(to-spec·to-tickets·implement·grill-with-docs)은 남기고, 시작 프롬프트는 next-session 결정표가 슬래시 명령으로 적는다 |
| `npx skills update -p`가 덧댄 사본을 되돌림 | 범위·절차가 조용히 사라지고 그 뒤로도 리뷰는 초록 | 사본 첫머리 주석을 센티널로 훅이 판정한다(7단계). 목록은 양방향으로 본다 — 주석이 있는데 목록에 없는 사본도 빨강 |
| [Win] ini 계열 파일의 한글 | 환경변수로도 인코딩을 못 바꿔 죽음 | ASCII만 |
| 셸 체인이 앞 명령의 실패를 무시 | 스크립트가 문법 오류로 안 돌았는데 뒤의 커밋이 그대로 실행돼 메시지가 내용을 앞지름 | 판정 명령 뒤에 `\|\| exit 1`. 커밋 전에 `git show --stat`으로 내용을 본다 |
| 봇 리뷰의 초록 착시 | 시트 미할당·무료 플랜이면 CodeRabbit이 Walkthrough만 남기고 `pass`, 시간당 한도를 넘어도 `pass`. Claude Code Review 플러그인은 지적이 없으면 코멘트 없이 `pass`가 되곤 했고, **자기 워크플로 파일**(`claude-code-review.yml`)을 바꾼 PR에서는 그 파일이 기본 브랜치와 다르다는 검증에 걸려 건너뛰며 `pass`다(다른 워크플로 파일은 무관. agent-os #3·#6 건너뜀, #43은 `ci.yml`만 바꿔 돌았다) | 비공개+무료면 CodeRabbit PR 리뷰를 끄고 CLI만. Claude는 플러그인 대신 직접 프롬프트로 요약 코멘트를 완료 조건에 걸고 "코멘트 0개면 실패" 스텝을 둔다. `show_full_output`으로 로그를 남긴다. 그 워크플로 파일의 변경은 별도 PR 먼저 |
| CodeRabbit CLI 한도와 좌석 | 개발자당 시간당 3회, 롤링 윈도(공식 요금제 문서, 2026-09-21 확인). `coderabbit --usage`는 청구 주기 누적만 보여주고 시간당 잔량은 안 보여준다. 연결 단계에서 즉시 끝나는 것은 한도가 아니라 좌석 미배정(`Seat: not assigned`, 2026-09-23 실측)이고 좌석은 유료 구독이 있어야 배정된다 | 그 출력으로 실행을 막지 않는다. 좌석은 PR마다 `auth status` 한 줄로 본다. 한도 문서는 공급자 페이지에서 확인하고 저장소에 날짜와 함께 적는다(부록 C) |
| `.coderabbit.yaml`의 제외 목록을 로컬 CLI도 읽음 | 테스트 경로를 빼면 로컬에서도 리뷰를 못 받음 | 제외는 생성물·락파일·남이 쓴 스킬 사본만 |
| [Win] 도구의 거부를 앱의 한계로 읽음 | `open_session_in`이 부모-자식 관계로 거부하고 `spawn_task`가 워크트리를 기본으로 하니 "무클릭과 네이티브 패널은 동시에 안 된다"고 두 번 단정했다. 사용자가 "다시 확인해봐"로 밀어서야 풀렸다(agent, 2026-09-21) | 도구가 거부하면 앱이 사람에게 허용한 길을 본다. 앱 번들(`app.asar`)의 딥링크 라우트와 접근성 트리(UI Automation)의 버튼·메뉴가 원천이고, 실측은 사람 손이 입력란 밖일 때 백그라운드 대기로 깨어나 한다 |
| 무료 플랜 비공개 저장소의 보호 브랜치 | `gh api .../branches/main/protection`이 403 "Upgrade to GitHub Pro". 룰셋도 같다(2026-09-20 실측) | 공개 전환이나 Pro. 아니면 `/git-pr-merge`의 `gh pr checks`가 유일한 게이트라 직접 `gh pr merge`를 치지 않는다 |
| 세션 중에 만든 `.claude/agents/*.md` | 바로 부르면 `Agent type '<이름>' not found`이고, 세션이 이어지는 동안 뒤늦게 목록에 올라온다(http-channel에서 `spec-reviewer`를 굳힐 때 검토 한 번이 끝난 뒤였다) | 첫 실패를 파일 오류로 읽지 않는다. 기다리는 동안은 같은 본문을 일회성 호출로 돌리고, 목록에 뜨면 짧은 연기 시험으로 도구와 본문이 실렸는지 본다 |
