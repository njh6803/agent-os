# canary-notice-spec-paths: **`tools/sibling_overlap.py`의 카나리아 알림이 바뀐 규칙을 원천으로 든 명세의 이름만 주고 경로와 돌리는 명령을 주지 않아, 세션이 Glob으로 경로를 찾고 `tools/canary.py --help`의 독스트링 전체를 읽었다**(mcp-http 티켓 01이 `adapters.md`·`sdk.md`를 고쳐 명세 다섯을 돌렸다. 알림은 `adapters_rule_rules_file_read.toml` 같은 파일 이름만 적었다)

**상태:** 열림
**어디로:** 다섯 번째에 `tools/sibling_overlap.py`의 카나리아 알림: 명세마다 저장소 기준 경로와 돌리는 명령 한 줄(`uv run python tools/canary.py <명세 경로> <출력 디렉터리>`)을 낸다. 그 시험
**승인:** 자체 승인 2026-11-10, 자체 승인 2026-11-16, 2회차(2회차는 release-image 티켓 09 세션이 `.claude/rules/http.md`를 고쳐 그 규칙을 원천으로 든 카나리아 명세 셋을 돌릴 때다. 명세 위치를 `.scratch/harness/probes/canary/` 아래로 잘못 짚어 도구가 명세를 읽지 못했고(종료 2, 아무것도 돌지 않았다), 이어 명세의 "돌리는 법"에 없는 `--control-commit`을 주어 도구가 거절했다. 세 명세는 `.scratch/end-user-continuation/probes/canary/`와 `.scratch/web-widget/probes/canary/`에 있었고 Glob으로 찾았다), 일지 2026-11-10-0152-mcp-http-contract.md·2026-11-16-1447-standalone-compose-runs-real-images.md. ADR 불필요
