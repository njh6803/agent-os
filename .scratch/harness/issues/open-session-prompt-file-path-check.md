# open-session-prompt-file-path-check: 인계 열기 스크립트가 `-PromptFile`과 `-Folder`를 스스로 좁히고, 좁은 허용 규칙을 더한다

**What to build:** 인계 열기(`open-session` 스킬 3단계의 `pwsh -NoProfile -File tools/open_session.ps1 -Action send …`)를 자동 모드 분류기가 거부해, 인계를 못 하고 같은 세션이 압축으로 이은 일이 다섯 번 있었다. 허용 목록에 규칙을 넣으면 풀리지만, 08 세션이 넣었다가 리뷰 두 번의 지적으로 같은 PR에서 뺐다. 이유는 스크립트가 입력을 좁히지 않아서다. `-PromptFile`을 경로 검사 없이 읽어 새 세션의 입력창에 넣으므로 `.env`를 실어 보내는 호출이 `.env` 읽기 금지 규칙(`permissions.deny`)을 돌아간다. 신뢰 대화상자의 폴더는 호출자가 준 `-Folder`와만 견주어, 아무 폴더의 신뢰 수락이 판정기 없이 지난다. 허용 규칙의 끝 `*`는 그 뒤의 글자를 가리지 않으므로 자리를 좁히는 일은 스크립트가 해야 한다.

`tools/open_session.ps1`의 `send`를 고친다.

- `-PromptFile`: `Resolve-PromptFile`이 경로를 정규화해 세션 스크래치패드가 사는 `<임시 폴더>\claude` 아래인지 보고(`..`, 접두만 같은 형제 폴더, 슬래시 방향), 파일에서 그 폴더까지 올라가며 링크가 있으면 멈춘다. 읽기는 `-LiteralPath`로 한다.
- `-Folder`: `Test-RepoFolder`가 이 스크립트가 든 저장소의 뿌리(이 사본이 든 체크아웃과, 워크트리면 그 주 체크아웃)와 같을 때만 받는다. 신뢰 대화상자와 새 세션 화면의 폴더 견줌이 이 검사를 지난 값을 기준으로 한다.
- `tests/tools/test_open_session.py`에 두 검사의 시험을 더한다. 스크래치패드 아래는 지나고, `.env` 같은 바깥 파일·`..`로 빠져나가는 경로·접두만 같은 형제 폴더·폴더 밖을 가리키는 링크·없는 파일은 멈춘다. 저장소 뿌리가 아닌 폴더는 멈춘다.
- `.claude/settings.json`의 `permissions.allow`에 `PowerShell(pwsh -NoProfile -File C:\project\agent\tools\open_session.ps1 -Action send -Folder C:\project\agent -PromptFile *)`를 더하고, `open-session` 스킬의 3단계가 가리키는 호출 모양과 글자가 같음을 시험이 대조한다. 스크립트 경로를 절대 경로로 적는 것은 사용자 결정이다(2026-11-08, "절대 경로로 바꿈"). 상대 경로이면 작업 폴더를 옮기고 같은 상대 경로에 만든 가짜 스크립트가 규칙과 같은 글자로 확인 없이 돌아 두 검사가 빠지기 때문이다. 이 호출이 도는 사본은 주 체크아웃의 것이다.
- 다음 인계 열기가 분류기에 거부되지 않는지는 이 PR을 병합한 뒤 실제 인계에서 본다(병합 뒤 일지의 "다음"에 남긴다).

**대기열:** 498

**Status:** done

## 수용 기준

- [x] `Resolve-PromptFile`이 스크래치패드(`<임시 폴더>\claude`) 아래의 파일만 받고, 바깥 파일·`..` 경로·접두만 같은 형제 폴더·링크가 낀 경로·대체 데이터 스트림(`파일:스트림`)이 붙은 경로·없는 파일은 멈추며, 시험이 이를 고정한다
- [x] `Test-RepoFolder`가 스크립트가 든 저장소의 뿌리(워크트리면 주 체크아웃 포함)만 받고 다른 폴더는 멈추며, 시험이 이를 고정한다
- [x] `Send-Prompt`가 두 검사를 읽기와 쏘기 전에 부르고, `-LiteralPath`로 읽는다
- [x] `.claude/settings.json`에 좁은 허용 규칙이 들었고, 스킬이 가리키는 호출 모양과 같은지 시험이 대조한다
- [x] 검증 명령이 모두 초록이다(손으로 치는 명령 전부와 `uv run python tools/run_checks.py`. 커밋 직전의 pre-commit이 갈음하는 것은 그 결과로 갈음한다)
