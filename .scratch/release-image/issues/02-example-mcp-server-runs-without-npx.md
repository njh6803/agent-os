# 02: 예시 MCP 서버가 npx 없이 미리 설치한 실행 파일로 뜬다

**What to build:** 저장소의 예시 MCP 플러그인(`plugins/mcp/everything/plugin.toml`)이 `npx -y`가 아니라 미리 설치한 실행 파일 `mcp-server-everything`을 띄운다. 그래서 인터넷이 막힌 서버의 이미지에서도 calc 예시가 MCP 연결을 지난다(07이 이미지에 같은 판을 깐다). 개발 PC와 CI의 실제 모델 시험(`-m llm`, `-m llm_widget`, `-m llm_portal`)은 같은 판을 전역에 깔아 둔 채 지금처럼 calc 예시로 초록이다.

사용자가 세 안 가운데 매니페스트를 저장소에서 바꾸는 안을 골랐다(명세 "이미지의 구성"의 예시 MCP 서버, 일지 2026-11-13-1843 "사용자에게 물은 것 넷"). 매니페스트를 바꾸면 calc를 실제 모델로 돌리는 모든 곳에 같은 실행 파일이 있어야 하므로, 이 티켓이 같은 변경에서 그 자리를 모두 고친다.

근거는 명세 "이미지의 구성"의 예시 MCP 서버(둘째 문단에 고칠 자리 셋이 있다)와 ADR 0056 결정 "서버 이미지의 Node와 예시 MCP 서버"다. 측정은 `.scratch/release-image/probes/serve_image/README.md` 4번이고 이 티켓은 다시 돌리지 않는다(07이 serve_image를 고쳐 다시 돈다). 이 티켓의 "명세 검토"와 그 번호(S3, N4 같은 것)는 일지 `docs/journal/2026-11-14-1748-release-image-tickets.md`의 "명세 검토" 절을 가리킨다.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] 예시 매니페스트를 `command = "mcp-server-everything"`, `args = []`로 바꾼다. 실행 파일은 `@modelcontextprotocol/server-everything` 2.3.0이 전역 설치로 만드는 이름이다(07의 이미지도 같은 판을 쓴다)
- [ ] ci.yml의 `llm` 잡에 setup-node 다음으로 같은 판을 전역에 까는 단계를 더한다. 그 잡의 `-m llm`과 `-m llm_widget` 단계가 그 뒤에 돈다. 워크플로 감사(zizmor)를 지난다
- [ ] `docs/constitution/operations.md`의 LLM 테스트 절에 개발 PC에서 그 판을 전역에 까는 준비 한 줄을 더하고, 헌법 판을 올린다(`docs/constitution/README.md`의 판 줄. 올린 까닭은 일지에 적는다. 명세 검토 N4). 판을 매기기 전에 `tools/sibling_overlap.py`로 형제 브랜치가 먼저 가져간 판을 본다. 규약 문서를 고치는 일이라 이 티켓은 워크트리에서 한다(명세 "티켓을 나눌 때 함께 둘 것")
- [ ] 위젯과 위젯 미리보기 페이지의 Playwright 설정(`web/apps/widget/playwright.config.ts`, `web/apps/portal/playwright.config.ts`)에서 실제 모델 프로젝트의 제한 시간을 설명하며 그 MCP 서버를 "npx"로 적은 주석을 고친다
- [ ] 모델을 부르지 않는 시험은 저마다 적은 매니페스트를 쓰므로 바꾸지 않는다(명세가 든 `tests/test_server.py`의 `EVERYTHING` 픽스처, `tests/sdk/test_manifest.py`, `tests/adapters/test_filesystem.py`). 그 시험들이 그대로 초록인지 본다
- [ ] Windows 개발 PC에서 npm이 만든 `.cmd`로 서버가 뜨는지 `-m llm`으로 본다. 명세는 mcp SDK의 코드를 읽고 뜰 것으로 보았고 띄워 보지는 않았다. 뜨지 않으면 멈추고 보고한다
- [ ] `-m llm`, `-m llm_widget`, `-m llm_portal`을 이 PC에서 돌려 calc 예시가 초록인지 보고 결과를 일지에 적는다(워크트리의 `.env` 경로는 `docs/constitution/operations.md` LLM 테스트). 키를 쓰는 시험이라 PR 전에 한 번 돈다
- [ ] 검증 명령이 모두 초록이다
