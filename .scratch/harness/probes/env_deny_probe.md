# `.env` deny 탐침 (2026-09-29, Claude Code 데스크톱, Windows)

진짜 `.env` 가 아니라 스크래치패드의 가짜 `.env`(`FAKE=1`)와 `.env.example` 로 쟀다. deny 가 새면 값이 도구
출력에 실리기 때문이다. `.claude/settings.json` 을 고치면 같은 세션에서 곧바로 반영됐다. 규칙을 세 번 바꿔 가며
쟀다. (가) 바꾸기 전 `Read(./.env)`, (나) `Read(//**/.env)` 만, (다) (나)에 `PowerShell(Get-Content *.env*)` 와
`PowerShell(Select-String *.env*)` 를 더한 지금의 설정이다.

| 호출 | (가) | (나) | (다) |
|---|---|---|---|
| Read 도구로 cwd 밖의 가짜 `.env` | 읽혔다 | 막혔다 | 막혔다 |
| Read 도구로 `.env.example` | 읽혔다 | 읽혔다 | 읽혔다 |
| Bash `uv run --env-file <가짜 .env> python -c …` | 돌았다 | 돌았다 | 재지 않았다(Bash 쪽 규칙은 그대로다) |
| Bash `cat <가짜 .env>` | `hook_env_read` 훅이 막았다 | 같다 | 같다 |
| PowerShell `Get-Content <가짜 .env>` | 읽혔다 | 읽혔다(Read 규칙은 PowerShell 을 덮지 않는다) | 막혔다 |
| PowerShell `gc`·`cat`·`type`, `Get-Content -Raw` | 재지 않았다 | 재지 않았다 | 막혔다(별칭이 정규화된다) |
| PowerShell `sls FAKE <가짜 .env>`, `Select-String -Path <가짜 .env> …` | 재지 않았다 | 재지 않았다 | 막혔다 |
| PowerShell `Get-Content <.env.example>` | 재지 않았다 | 재지 않았다 | 막혔다(패턴이 `*.env*` 라서. Read 도구로는 읽힌다) |
| PowerShell `Select-String -Pattern '\.env' -Path <.py 파일>` | 재지 않았다 | 재지 않았다 | 막혔다(명령에 `.env` 가 들어서. 코드 검색은 Grep 도구로 한다) |
| PowerShell `[IO.File]::ReadAllText(<가짜 .env>)` | 재지 않았다 | 재지 않았다 | 읽혔다(규칙이 이름을 대지 않는 읽기) |
| PowerShell `Get-ChildItem <디렉터리>` | 재지 않았다 | 재지 않았다 | 됐다(나열은 막지 않는다) |

패턴 끝의 `*` 는 인용 부호로 끝나는 경로(`"…\.env"`)까지 맞추려고 두었다. 그 값으로 `.env.example` 읽기와 `.env`
를 언급하는 코드 검색도 PowerShell 에서는 막힌다. 둘 다 Read·Grep 도구로는 된다. 권한 규칙은 Claude 가 쓴 호출의
모양만 맞추므로(공식 permissions 문서) `.NET` 읽기와 스크립트 안의 읽기는 이 층이 보지 못한다. 그 층이 키
자체다(사용 한도를 건 개발용 키, 실린 키는 회전).
