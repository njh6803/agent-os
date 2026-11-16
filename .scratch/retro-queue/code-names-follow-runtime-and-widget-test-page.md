# code-names-follow-runtime-and-widget-test-page: 코드의 빌드 대상과 폴더 이름 `serve`와 `portal`을 Docker Hub 저장소 이름이 따른 "런타임", "위젯 테스트 페이지"에 맞출지 첫 릴리스 뒤에 정한다.

**상태:** 열림
**어디로:** 제안만 한다. 하기로 하면 `deploy/images/docker-bake.hcl`의 대상 이름, `deploy/images/serve.Dockerfile`과 `portal.Dockerfile`, `deploy/standalone/compose.yaml`의 서비스 이름과 `./portal` 폴더, `web/apps/portal/`, `tools/release_ci.py`의 `IMAGES`와 점검 결과 파일 이름(`grype-<이름>.json`), 단독 배포 e2e가 닿는다. 서비스 이름과 폴더 이름은 운영자가 쥔 것(compose 파일, 마운트 경로)이라 올릴 때 할 일이 생기므로 느낌표 PR이고 ADR이 따로 필요하다
**승인:** 사용자 승인 2026-11-17(제안으로만 남긴다. 하기로 정한 것은 아니다), 1회차, 일지 2026-11-16-2249-ci-publishes-release-from-main.md. ADR 필요

판 내기 PR(release-image 티켓 11)은 Docker Hub에 올라가는 이름만 `agent-os-runtime`, `agent-os-admin`, `agent-os-widget`, `agent-os-widget-test-page`로 정했다. 둘의 대응은 `deploy/images/docker-bake.hcl`의 `tags` 한 곳이 정하고, 대응표는 `deploy/standalone/README.md`에 있다. 코드의 이름(빌드 대상 `serve`, `portal`)은 그대로 둬서 두 이름이 달라졌다. 처음 보는 운영자는 서비스 `serve`가 이미지 `agent-os-runtime`임을 표로 찾아야 한다.

첫 릴리스 뒤에 정할 것: 코드 이름도 `runtime`과 `widget-test-page`로 맞출지, 맞추면 운영자가 이미 쥔 compose 서비스 이름과 `portal/` 마운트 폴더를 어떻게 옮기게 할지. 첫 릴리스 전에는 운영자가 없어 비용이 가장 낮지만, 이 PR의 범위를 넘고 `web/apps/portal`과 패키지 이름 `@agent-os/portal`, 마커 `llm_portal`, 잡 `e2e-portal`까지 닿는다.
