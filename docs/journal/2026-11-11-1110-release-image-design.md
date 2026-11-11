# 2026-11-11 (11:10) release-image 설계 인터뷰

세션 제목: `docs/release-image-design`. 브랜치 `docs/release-image-design`, 워크트리 `.claude/worktrees/release-image-design`. 모델 Fable 5.2. 지시문 없이 주 체크아웃에서 연 세션이고, 사용자가 후보 다섯 가운데 이 기능을 고른 뒤 `EnterWorktree`로 들어와 브랜치 이름을 바꿨다. 이 기능에는 명세도 기능 계획의 `**설계:**` 줄도 없었다.

## 사용자 프롬프트

> 사용자: 설계 인터뷰 먼저 진행할 수 있는거 있어?

프론티어 일곱 가운데 명세도 설계 줄도 없는 다섯(`local-model`, `release-image`, `portal-login`, `portal-admin`, `widget-appearance`)을 보이고 `release-image`를 추천했다. 근거는 기다리는 기능이 넷으로 가장 많고(`public-demo`, `deploy-package`, `diag-bundle`, `ops-backup-upgrade`), 기능 계획이 "고르지 못하면 deploy-package가 막힌다"고 적은 것이다.

> 사용자: 이미지 배포 설계

## 인터뷰 전에 대 본 사실

근거의 종류를 괄호에 적는다. 서브에이전트의 보고는 그 보고가 적은 종류를 그대로 옮겼고, 이 세션이 직접 다시 본 것은 따로 적었다.

- 루프백 목록은 네 곳이 따로 들고 값은 모두 `("127.0.0.1", "::1")`이다. `src/agent_os/main.py` 74줄, `web/apps/admin/tools/loopback.ts` 25줄, `web/apps/widget/tools/start.ts` 39줄, `web/apps/portal/server/config.ts` 24줄(코드를 읽었다. 앞의 둘은 이 세션이 직접 읽었고 뒤의 둘은 서브에이전트가 읽었다). 네 곳 모두 시작할 때 묶을 주소의 문자열만 보고, 요청의 `Host`, 상대 주소, `X-Forwarded-*`를 보는 코드는 없다(서브에이전트가 `src`와 `web`을 grep했다).
- 관리 화면은 나가는 쪽도 묶는다. 상류 `AGENT_OS_UPSTREAM`의 호스트는 `127.0.0.1` 하나만 받고(`loopback.ts` 60~83줄, 이 세션이 읽었다), rewrites는 빌드 산출물에 박힌다(`web/apps/admin/next.config.ts` 머리 주석, 서브에이전트가 읽었다).
- 위젯 빌드의 입력은 사이트 파일이다. `frame-ancestors`와 env 둘(합친 허용 출처, 가장 작은 요청 글자 수 상한)이 빌드에 박힌다(`web/apps/widget/next.config.ts` 5~13줄과 25~41줄, 이 세션이 읽었다). 기능 계획에는 이 사실이 없다.
- 운영용 `Dockerfile`, compose 파일, `.dockerignore`, 운영 nginx 설정은 저장소에 없다. nginx 설정은 측정용 틀 `.scratch/web-widget/probes/nginx_relay/nginx.conf` 하나다(서브에이전트가 `git ls-files`로 손으로 봤다).
- git 태그는 0개이고 원격에 `dev` 브랜치가 없다(서브에이전트가 `git tag --list`, `git branch -r`, `git ls-remote --heads --tags origin`으로 손으로 봤다). ADR 0043의 compose e2e를 맡을 harness 티켓도 없다(같은 서브에이전트가 `.scratch/harness/issues/`를 grep했다).
- 제품 판은 `pyproject.toml` 3줄의 `version = "0.1.0"`이고(이 세션이 grep으로 봤다) `web/**/package.json`에는 `version` 칸이 없다(서브에이전트가 grep했다).
- calc 예시의 MCP 서버는 `command = "npx"`, `args = ["-y", "@modelcontextprotocol/server-everything"]`이다. 패키지의 판을 적지 않았다(`plugins/mcp/everything/plugin.toml` 8~9줄, 이 세션이 읽었다).
- 저장소의 마크다운 전체를 `[Pp]odman|RHEL|UBI`로 grep하면 `.scratch/release-image/plan.md` 한 곳만 맞는다(이 세션이 Grep으로 봤다). 배포 환경의 운영체제와 컨테이너 런타임은 어느 문서에도 사실로 적혀 있지 않다.
- GitHub 저장소 `njh6803/agent-os`는 공개다(이 세션이 `gh repo view --json visibility`로 손으로 봤다).
- GitHub 쪽 사실 셋은 웹 요약이다(WebFetch가 준 요약이고 본문을 내려받아 대 보지 않았다). 컨테이너 레지스트리에 처음 올린 패키지는 비공개이고, 공개로 바꾼 뒤에는 인증 없이 받을 수 있으나 비공개로 되돌릴 수 없다(`https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility`). 릴리스의 첨부 파일은 하나가 2GiB보다 작아야 한다(`https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases`). 워크플로는 `GITHUB_TOKEN`으로 그 저장소에 묶인 패키지를 올린다(`https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry`).
- 이미 정해져 있어 묻지 않은 것: 이미지는 넷, 밖으로 여는 포트는 TLS를 끝내는 프록시 하나, 관리 화면은 SSH 포트 포워딩, 빈도 제한은 프록시, init과 root가 아닌 사용자(ADR 0011, ADR 0024, ADR 0046, ADR 0048, ADR 0050과 기능 계획. 서브에이전트가 문서를 읽었다).

## 설계 인터뷰 라운드 1

첫 화면은 `hook_choice_facts`가 한 번 막았다. 설명의 사실 넷(Podman·RHEL 검색, `pyproject.toml`의 판, ops-backup-upgrade와 deploy-package 기능 계획의 인용)을 다시 대 보고 수락 문장의 인용을 원문 글자로 고친 뒤 같은 질문과 라벨로 다시 올렸다.

> 사용자: (0.1 판의 이미지와 compose 파일을 어떤 서버 환경까지 띄워 보고 보증할까요?) "Docker와 리눅스 x86-64만 (Recommended)" — 설명: 이미지와 단독 compose를 Docker Engine과 Docker Compose, 리눅스 x86-64 서버에서만 띄워 보고, 배포 안내에 그 환경만 보증한다고 적습니다. Podman, RHEL 계열 전용 베이스 이미지, ARM 서버는 0.1 판의 범위 밖이라고 적습니다. 배포 환경이 Docker를 허용하지 않는 곳으로 정해지면 그때 이 설계를 다시 열어야 합니다. 지금 저장소의 문서에는 배포 환경의 운영체제와 실행 도구가 사실로 적혀 있지 않습니다(마크다운 전체를 Podman, RHEL로 검색하면 이 기능의 계획 한 곳에만 "제한될 수 있다"는 가정으로 나옵니다).

> 사용자: (판마다 지은 이미지를 어디에 올려 둘까요?) "Docker Hub" — 설명: 가장 널리 쓰이는 공개 이미지 저장소에 올립니다. Docker Hub 계정과 접근 토큰을 새로 만들어서 CI의 비밀 값으로 넣어야 합니다. 무료 계정에는 이미지를 받는 횟수의 제한이 있는 것으로 알고 있지만 이 세션에서 확인하지 않았습니다(어림).

추천(GitHub 컨테이너 저장소)과 다른 답이다. 이 답이 여는 가지는 Docker Hub의 어느 이름 아래에 올리는지, 계정과 접근 토큰을 만들어 저장소의 비밀 값으로 넣는 사람 몫, 받는 횟수 제한의 실제 값이고 다음 라운드로 넘긴다.

> 사용자: (판의 이름표(태그)를 어떤 꼴로 달고, 0.1.0 판보다 먼저 필요한 이미지는 어떻게 낼까요?) "v0.1.0 꼴, 그 전에는 출시 후보 (Recommended)" — 설명: main의 커밋에 git 태그 v0.1.0을 달면 CI가 네 이미지를 0.1.0 태그와 그 커밋의 해시 태그로 올립니다. 공개 데모처럼 0.1.0보다 먼저 필요한 이미지는 v0.1.0-rc.1 같은 출시 후보 태그로 냅니다. 태그의 판 번호가 pyproject.toml에 적힌 판(지금 0.1.0)과 다르면 CI가 실패합니다. 늘 최신을 가리키는 latest 태그는 두지 않습니다. 판 올림이 "이미지 태그를 바꾸는 것"(ops-backup-upgrade 기능 계획)이라서, 움직이는 태그가 있으면 어느 판이 돌고 있는지 알 수 없기 때문입니다. 태그를 누가 언제 다는지는 다음 라운드에서 묻습니다.

> 사용자: (판마다 이미지 말고 무엇을 함께 내서, 운영자가 서버에 띄울 수 있게 할까요?) "작은 배포 파일 묶음만 첨부 (Recommended)" — 설명: 판마다 compose 파일, 프록시 설정, 환경 변수 틀, 배포 안내를 묶은 작은 압축 파일 하나를 GitHub 릴리스에 첨부합니다. 이미지는 이미지 저장소에서 받습니다. 인터넷이 막힌 곳을 위해서는 배포 안내에 "인터넷이 되는 PC에서 이미지를 받아 파일로 저장하고, 옮겨서 불러온 뒤, 해시를 대조하는" 명령을 적고, 그 명령을 실제로 돌려 본 기록을 남깁니다. 모델 파일까지 포함한 반입 절차는 deploy-package 기능이 이 명령 위에 짓습니다(그 기능 계획이 "이미지와 모델 파일을 파일로 옮기는 절차와 해시 확인"을 자기 몫으로 적고 있습니다).

같은 라운드의 둘째 화면(frontier가 넷을 넘어 호출을 둘로 나눴다). 첫 화면의 답이 연 가지 하나(태그를 누가 언제 다는지)를 함께 올렸다. 이 화면도 `hook_choice_facts`가 한 번 막았고, 올리기 전에 대 본 사실은 셋이다. calc 예시의 매니페스트가 `mcp = ["everything"]`이다(`plugins/agents/calc/plugin.toml` 6줄, Grep). 명령을 찾지 못하면 `FileNotFoundError`가 나고 여는 단계 안이라 연결 오류의 원인이 된다(`src/agent_os/adapters/mcp.py` 555~564줄, Grep). `tests/` 아래 아홉 파일이 `everything`이라는 이름을 가리킨다(Grep의 count. 그 서버를 실제로 띄우는 시험이 몇인지는 세지 않았다).

> 사용자: (서버 이미지에 Node를 넣을까요, 그리고 calc 예시가 쓰는 MCP 서버는 어떻게 준비할까요?) "Node를 넣고 예시 MCP 서버도 미리 설치 (Recommended)" — 설명: 서버 이미지에 파이썬과 Node를 함께 넣고, calc 예시가 쓰는 MCP 서버 패키지를 판을 고정해서 이미지에 미리 설치합니다. 인터넷이 없는 서버에서도 예시가 돌고, 운영자가 Node로 띄우는 MCP 서버를 플러그인으로 더할 수 있습니다. 이미지가 커지고 취약점 점검 대상이 늘어납니다(크기는 아직 재지 않았습니다). 예시 플러그인의 실행 명령(지금은 npx -y, 판 고정 없음)을 미리 설치한 것을 실행하도록 고쳐야 합니다. 미리 설치되어 있어도 npx -y가 인터넷 접속을 시도하는지는 아직 재지 않았습니다(어림. 명세에서 잽니다).

둘째 질문은 선택지를 고르지 않고 글로 답했다. 조사를 청한 답이라 이 질문은 아직 열려 있다.

> 사용자: (판 태그는 누가 언제 달까요?) 보통 어떻게 해? 버전을 0.0.0 이라고 하면 맨 앞에가 호환이 불가능할 정도의 큰 변경일 때 올리고, 가운데는 새로운 기능이 추가될 때, 마지막은 버그를 수정했을 때? 였던거 같은데.
> 조사 한번 해보고 릴리즈 노트나 이런 것들을 관리하는지 등
> 개발하면서 이런것들을 어떻게 정하는지 조사해줘

## 라운드 1 뒤의 조사

사용자가 청한 조사를 서브에이전트 둘(판 번호와 릴리스 관행, Docker Hub와 도구)에게 맡겼고, 인터뷰 전에 띄운 측정 서브에이전트(컨테이너 네트워크 배치)가 같은 때 끝났다. 아래는 그 보고에서 옮긴 것이고 근거의 종류는 보고가 적은 것이다. 이 세션이 원문 파일이나 프로브의 README를 다시 열어 본 것은 "이 세션이 다시 봤다"고 적었다. 내려받은 원문은 세션 스크래치패드에만 있다. ADR의 근거로 쓸 사실은 그때 주소에서 다시 받아 대 본다. 영어 원문은 옮겨 적지 않고 뜻만 적었다.

### 판 번호와 릴리스 관행

- 유의적 버전 2.0.0(`https://semver.org/spec/v2.0.0.html`. 서브에이전트가 원문을 받아 대 봤고, 3·4항과 6~8항은 이 세션이 다시 봤다). 맨 앞자리는 호환이 깨지는 변경, 가운데는 호환되는 기능 추가, 끝자리는 호환되는 버그 수정이다. 기준은 변경의 크기가 아니라 공개 API가 호환되느냐다. 6~8항의 조문에는 맨 앞자리가 0보다 클 때라는 조건이 붙어 있고, 4항은 0.y.z가 초기 개발용이라 무엇이든 언제든 바뀔 수 있다고 적는다. 3항은 낸 판의 내용을 고치지 못하게 하고 고친 것은 새 판으로 내게 한다. FAQ는 0.1.0에서 시작해 릴리스마다 가운데 자리를 올리는 것이 가장 단순하다고 적고, `v1.2.3`은 판 번호가 아니라 태그 이름이라고 적는다(FAQ는 서브에이전트가 대 봤다).
- 날짜로 매기는 판 번호(`https://calver.org/`, 서브에이전트가 원문을 받아 대 봤다). 호환이 깨지는지를 번호가 알리지 않는다고 그 사이트가 스스로 적는다.
- 파이썬의 판 표기(`https://packaging.python.org/en/latest/specifications/version-specifiers/`, 서브에이전트가 원문을 받아 대 봤다). 출시 후보는 `X.YrcN` 꼴이다. `packaging` 26.3은 `v0.1.0-rc.1`을 `0.1.0rc1`로 읽고, uv 0.10.8은 `0.1.0`에서 `uv version --bump rc`만으로는 올리지 못하며 값을 직접 주면 `0.1.0 => 0.1.0rc1`이다(서브에이전트가 스크래치 스크립트와 임시 프로젝트의 `--dry-run`으로 손으로 봤다. 저장소의 프로브가 아니다).
- GitHub가 자동으로 만드는 릴리스 노트는 병합된 PR의 목록이고, 분류는 커밋 접두가 아니라 PR 라벨로 한다(`https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes`, 서브에이전트가 원문을 받아 대 봤다). 이전 태그를 자동으로 고르는 규칙은 그 문서에 없어 확인하지 못했다. 이 저장소의 최근 병합 PR 40개에는 라벨이 붙은 것이 없다(이 세션이 `gh pr list --state merged --limit 40 --json number,labels`의 결과를 `--jq`로 세어 손으로 봤다).
- 워크플로의 기본 토큰으로 만든 태그와 릴리스는 다른 워크플로를 일으키지 않는다(release-please-action의 README 106~113줄이 GitHub 문서를 인용한다. 이 세션이 다시 봤다).
- semantic-release는 0으로 시작하는 판을 지원하지 않는다고 FAQ가 적는다(`https://semantic-release.org/support/faq/`, 이 세션이 내려받은 파일의 486줄을 다시 봤다).
- release-please는 커밋 접두를 읽어 다음 판의 PR을 계속 갱신하고, 병합하면 변경 기록과 판 번호 파일을 고치고 태그와 릴리스를 만든다. 릴리스 PR이 생기는 접두는 `feat`·`fix`·`deps`이고 파이썬 유형에서는 `docs`도 든다(서브에이전트가 README를 받아 대 봤다). 출시 후보의 판을 `pyproject.toml`에 `0.1.0-rc.1` 꼴로 쓴다는 것은 서브에이전트가 main의 소스를 읽은 것이고 돌려 보지 않았다.
- 이미지를 내는 서버 제품 다섯의 워크플로와 설정 파일을 서브에이전트가 받아 읽었다. Paperless-ngx와 Immich와 Synapse는 사람이 때를 정하고(태그나 수동 실행) CI가 나머지를 한다. Flagsmith는 release-please, Zitadel은 semantic-release다. Synapse는 PR마다 조각 파일을 모으는 towncrier를 쓴다.
- GitHub의 배포 환경에는 승인자를 둘 수 있고 Free 요금제에서는 공개 저장소에서만 된다. 환경에 넣은 비밀 값은 승인 뒤에야 그 잡이 읽는다. 일으킨 사람이 스스로 승인하지 못하게 하는 것은 따로 켜는 설정이다(`https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments`. 이 세션이 그 문서의 본문을 받아 16~23줄과 76~81줄을 봤다).

### Docker Hub

- 무료 개인 계정은 공개 저장소를 수 제한 없이, 비공개 저장소를 하나 둔다. 조직을 만드는 절차는 요금제 선택과 결제로 끝난다. 개인 접근 토큰의 저장소 권한은 계정이 닿는 모든 저장소에 걸리고 저장소 하나로 좁힐 수 없다(`https://docs.docker.com/docker-hub/usage.md`, `https://docs.docker.com/accounts/organization/setup/orgs.md`, `https://docs.docker.com/security/access-tokens/reference.md`. 서브에이전트가 원문을 받아 대 봤고 이 세션이 세 파일의 그 줄을 다시 봤다). 저장소별로 좁히는 조직 토큰과, 토큰을 저장하지 않는 GitHub Actions 연결(OIDC)은 Team·Business 요금제의 것이다(서브에이전트가 대 봤다).
- 받는 횟수 제한은 공식 출처끼리 수가 다르다. 문서는 로그인하지 않으면 주소마다 6시간에 100번, 무료 계정으로 로그인하면 6시간에 200번이고(`https://docs.docker.com/docker-hub/usage/pulls.md`, 이 세션이 다시 봤다), 가격 페이지와 FAQ는 시간당 10번과 100번이다(서브에이전트가 대 봤다). 서브에이전트가 이 PC에서 익명으로 받은 응답 헤더는 3600초에 100번이었다(손으로 봤다, 한 번).
- 오래 받지 않은 이미지를 지우는 정책은 지금 문서에 없고 6개월 넘게 받지 않은 이미지에 표시만 붙는다. 약관에는 6개월 넘게 쓰지 않은 계정을 닫을 수 있다는 조항이 있다(서브에이전트가 대 봤다). 2020년에 발표된 삭제 정책을 거둔다는 공식 문장은 찾지 못했다.
- 태그를 덮어쓰지 못하게 하는 설정이 있고 Beta다. 켜면 지우기도 막힌다. 어느 요금제에서 되는지는 문서에 없다(서브에이전트가 대 봤다).
- SBOM과 출처 증명은 이미지 인덱스 안의 매니페스트로 붙어 Docker Hub에 함께 저장된다(서브에이전트가 문서를 대 보고, 공개 이미지 하나의 인덱스를 레지스트리 API로 손으로 봤다).

### 빌드와 점검 도구

- docker 액션 넷의 최신 릴리스와 커밋(서브에이전트가 `gh api`로 손으로 봤다, 2026-11-11). `docker/login-action` v4.8.0 `8aa5831fb8d48d8f76594c7ddde61ae58019f550`, `docker/setup-buildx-action` v4.4.1 `f87e5991a6d7451dcb8d9637bfbc97413f497069`, `docker/build-push-action` v7.4.0 `c3c9e263c25d99ce0380d002d59b67737d91b0dc`, `docker/metadata-action` v6.2.0 `dc802804100637a589fabce1cb79ff13a1411302`.
- `docker/build-push-action`은 공개 저장소에서 출처 증명을 가장 자세한 모드로 스스로 붙이고(빌드 인자의 값이 실린다), SBOM은 입력을 켜야 붙는다. BuildKit의 SBOM은 기본으로 마지막 스테이지만 훑는다(`https://docs.docker.com/build/ci/github-actions/attestations.md`, `https://docs.docker.com/build/metadata/attestations/sbom.md`. 이 세션이 두 파일의 그 줄을 다시 봤다). `docker/metadata-action`의 `type=semver`는 출시 전 태그에 `latest`를 붙이지 않는다(서브에이전트가 소스를 읽었다).
- Trivy, Grype, Syft는 모두 Apache-2.0이다. Trivy와 Grype는 취약점 자료를 인터넷에서 받고, Grype는 자료가 닷새보다 오래되면 점검이 실패한다(서브에이전트가 대 봤다). `aquasecurity/trivy-action`은 2026년 3월에 판 태그 거의 전부가 악성 커밋으로 옮겨진 권고가 있고(GHSA-69fq-xp46-6x23), 커밋으로 고정한 사용자는 영향이 없었다고 권고가 적는다. `anchore/scan-action`과 `anchore/sbom-action`은 게시된 권고를 찾지 못했다(서브에이전트가 `gh api`로 손으로 봤다. 없다는 뜻이 아니다).
- npx는 패키지가 npx 캐시에만 있으면 실행마다 레지스트리에 묻고, 프로젝트의 `node_modules/.bin`이나 전역에 설치돼 있으면 묻지 않는다. `--offline`은 캐시에 없으면 오류로 끝난다. `--no-install`은 네트워크를 끊는 옵션이 아니다(서브에이전트가 npm 12.2.2의 소스와 문서를 읽었다. 네트워크를 끊고 돌려 보지 않아 어림이다).
- compose의 `network_mode: "service:<이름>"`은 `networks`와 함께 쓰지 못한다고 compose 참조가 적고, 포트 발행을 못 한다는 것은 Engine 문서의 `container:` 모드 절에 있다(서브에이전트가 대 봤다).

### 컨테이너 네트워크 배치(netns 프로브)

`.scratch/release-image/probes/netns/run.py`로 쟀다(서브에이전트가 지었다. 다시 돌리는 명령과 환경은 그 폴더의 `README.md`. 이 세션은 README를 다시 읽었고 스크립트를 다시 돌리지 않았다). Windows의 Docker Desktop 4.97.0, 엔진 29.9.2, Compose v5.6.1, nginx 1.31.6에서만 돌았다.

- 프록시의 네트워크 이름공간을 빌린 컨테이너가 `127.0.0.1`에만 묶여도 nginx가 닿는다. `::1`도 닿는다. 이름공간을 함께 쓰지 않으면 포트를 발행해도, 서비스 이름으로 걸어도 닿지 않는다.
- 프록시 컨테이너가 compose를 거치지 않고 다시 뜨면(`docker restart`, 재시작 정책) app은 죽지 않은 채 옛 이름공간에 남아 502가 이어지고, `docker compose restart app`으로 돌아온다. `docker compose up -d --force-recreate proxy` 뒤에도 502이고 그때는 `restart app`이 실패하며 `docker compose up -d`로 돌아온다. `docker compose restart proxy`는 `depends_on`을 적지 않으면 app까지 다시 시작해 닿고(compose가 `restart: true`가 든 의존을 스스로 넣는다), `depends_on`을 짧은 꼴로 적으면 그 의존이 빠져 502다.
- 이름공간을 빌린 서비스에 `ports`를 주면 Docker가 거부한다. 공개하지 않는 프로세스에는 nginx의 둘째 `listen` 포트를 호스트 `127.0.0.1`에만 발행해서 닿는다.
- `limit_req`의 거부는 기본이 503이고 `limit_req_status 429`를 주면 429다. 이 PC에서는 호스트에서 온 요청의 상대 주소가 compose 네트워크의 게이트웨이 하나로 보였다. 리눅스 서버에서 실제 접속 주소가 보이는지는 재지 못했다.
- 재지 못한 것: 리눅스의 Docker Engine, Docker 데몬과 호스트를 다시 켠 뒤의 차례, 다른 기기에서 오는 요청, `nginx -s reload`. 이름공간의 주인을 프록시가 아닌 전용 컨테이너로 두는 배치는 같은 서브에이전트에게 후속 측정으로 맡겼다.

## 설계 인터뷰 라운드 2

조사 결과를 정리해 보이고 질문 넷을 한 화면에 올렸다. 판 번호의 세 자리를 0.x 동안 어떤 규칙으로 올릴지(추천: 운영자가 할 일로 가름), 릴리스 노트를 어떻게 만들고 보관할지(추천: 판마다 노트 파일을 씀), 판을 내는 때를 누가 정하고 공개 전에 어떤 확인을 둘지(추천: 에이전트가 준비하고 사용자가 GitHub의 배포 환경에서 승인), Docker Hub의 어느 이름 아래에 올릴지(추천: 이 제품만의 새 계정)다. 화면은 `hook_choice_facts`가 한 번 막았고, 올리기 전과 막힌 뒤에 대 본 사실은 위 "라운드 1 뒤의 조사"에 "이 세션이 다시 봤다"로 적은 것과 다음 셋이다. 유의적 버전 FAQ의 0.y.z 문단(내려받은 `semver.md` 249~252줄), 날짜 방식의 안내 사이트가 호환이 깨지는 변경을 일부러 알리지 않는다고 적은 문단(내려받은 `calver.html` 310~311줄), 가장 최근에 병합된 PR이 522번인 것(`gh pr list --state merged --limit 1 --json number`). 훅 파일(`tools/hook_*.py`)을 `refs/tags|--tags|push.*\btag\b|git tag`로 grep하면 태그 올리기를 막는 훅은 없고 두 훅의 독스트링이 `--tags`를 못 보는 것으로 든다.

사용자는 네 질문 가운데 어느 것도 고르지 않고 글로 답했다. 네 질문은 모두 열려 있다.

> 사용자: 전부 자동으로 안될까?
> 버그 수정한 패치도 릴리즈 노트에 적어야하는거 아니야?

둘째 말은 추천 선택지의 설명이 부른 오해다. "끝자리만 오른 판은 운영자가 이미지 태그만 바꾸면 된다"는 올릴 때 할 일이 없다는 뜻이었고 노트를 쓰지 않는다는 뜻이 아니었다. 모든 판에 노트가 붙는다고 답했다.

첫째 말을 받아, 전부 자동이 이 저장소에서 무엇을 뜻하는지 대 본 사실이다.

- 커밋 검사가 받는 제목 꼴은 접두 뒤의 느낌표를 이미 받는다(`tools/check_commit_msg.py` 29줄의 `!?`, 이 세션이 읽었다).
- 판 번호는 `importlib.metadata`로 읽혀 FastAPI 앱의 판과 CLI의 `--version`에 쓰이고(`src/agent_os/server.py` 110줄, `src/agent_os/channel/cli/main.py` 125줄), 계약 파일 `openapi.json` 1761줄에 `"version": "0.1.0"`으로 들어 있다(둘 다 이 세션이 Grep으로 봤다). 판 번호를 저장소 파일에서 올리는 길은 판마다 계약 파일을 함께 고친다. 빌드 백엔드는 hatchling이다(`pyproject.toml` 60줄).
- main의 보호 규칙은 필수 검사가 `verify` 하나이고 관리자에게는 강제하지 않는다(`gh api repos/njh6803/agent-os/branches/main/protection`, 손으로 봤다). 워크플로가 판 번호를 고친 커밋을 main에 바로 올리지 못할 것으로 읽었다(어림. 올려 보지 않았고 규칙 묶음은 보지 않았다).
- 2026-11-11에 `origin/main`의 지난 14일 커밋은 110개이고, 제목이 feat으로 시작하는 것이 47개, fix가 2개다. 그 가운데 `src`·`web`·`plugins`를 고친 것은 feat 38개, fix 1개다(`git rev-list --count origin/main --since=14.days`에 `--grep=^feat`, `--grep=^fix`, `-- src web plugins`를 붙여 손으로 봤다). `src`·`web`·`plugins`를 고치지 않은 feat 9개는 제목으로 보면 하네스의 것이라(PR 498, 497, 494 등) 접두만으로는 제품의 변경을 가르지 못한다.
- GitHub의 배포 환경은 공개 저장소에서 브랜치와 태그로 좁힐 수 있다(내려받은 배포 환경 문서의 51줄, 이 세션이 봤다).

자동화를 전제로 질문 넷을 다시 짜서 한 화면에 올렸다. 이 화면도 `hook_choice_facts`가 한 번 막았고, 설명의 사실은 위 다섯 항목과 앞 화면에서 대 본 것이다. 막힌 직후 컨텍스트가 압축되어, 압축 뒤의 세션이 같은 질문 문장과 라벨로 다시 올렸다.

첫 질문은 선택지를 고르지 않고 글로 답했다. 이 질문은 아직 열려 있다.

> 사용자: (판을 내는 계기를 무엇으로 할까요? (번호 계산, 릴리스 노트, 태그, 이미지 올리기는 어느 쪽이든 CI가 자동으로 하고, 판 번호의 원천은 태그가 됩니다.)) 판을 내는 것도 에이전트가 알아서 판단해서 미리 플랜으로 할 수 없나? 전부 자동으로 하고 싶어.

> 사용자: (판 번호를 자동으로 계산하는 규칙을 어떻게 할까요?) "고친 것만이면 끝자리, 기능이면 가운데 (Recommended)" — 설명: 지난 판 뒤의 PR 제목에 fix만 있으면 끝자리를 올리고(0.1.0 → 0.1.1), feat이 하나라도 있으면 가운데 자리를 올립니다(0.1.x → 0.2.0). 올릴 때 운영자가 손댈 것(설정, 환경 변수, 데이터, 플러그인 코드)이 있는 PR은 제목의 접두 뒤에 느낌표를 붙여 표시하고(feat!: 꼴. 커밋 검사가 이미 받는 꼴인 것을 코드에서 확인했습니다), 그런 PR이 있으면 가운데 자리를 올리며 노트의 '올릴 때 할 일'에 싣습니다. 그래서 끝자리만 오른 판은 이미지 태그만 바꾸면 된다는 약속이 됩니다. 맨 앞자리(1.0.0)는 자동으로 올리지 않고 따로 결정합니다. 기억하신 규칙(유의적 버전)이 0으로 시작하는 판에 허용하는 읽기입니다(원문 4항을 다시 확인했습니다).

> 사용자: (자동으로 만드는 릴리스 노트의 글을 무엇으로 채울까요? (어느 쪽이든 모든 판에 노트가 붙고, 고친 것도 빠짐없이 실립니다.)) "PR 제목 그대로 (Recommended)" — 설명: 제품 폴더를 고친 PR의 제목을 '새 기능', '고친 것', '올릴 때 할 일'로 묶어 싣습니다. 사람이 쓰는 글이 없습니다. 제목이 개발자의 말이라 운영자에게 필요 없는 항목이 섞일 수 있습니다. 다만 첫 판 0.1.0은 그동안 병합된 PR이 500개가 넘어 목록만으로는 읽을 수 없으므로(가장 최근 PR이 522번입니다), 저장소에 그 판의 소개 글 파일이 있으면 그 글을 노트 맨 위에 싣는 자리를 둡니다. 다른 판에서는 그 자리를 비워 둡니다.

> 사용자: (Docker Hub의 어느 이름 아래에 이미지를 올릴까요? (이미지 주소는 '이름/이미지:태그' 꼴이고, 이름은 계정이나 조직의 이름입니다.)) "이 제품만의 새 계정 (Recommended)" — 설명: Docker Hub에 이 제품의 이름으로 무료 개인 계정을 새로 만들고 그 아래에 네 이미지를 올립니다. 무료 계정은 공개 이미지를 수 제한 없이 둡니다. 무료 계정의 접근 토큰은 이미지 하나로 좁힐 수 없고 그 계정의 모든 이미지에 닿는데(문서를 다시 확인했습니다), 계정에 이 제품의 이미지만 있으면 토큰이 새도 닿는 범위가 이 제품에서 끝납니다. 이미지 주소에 개인 이름이 들어가지 않습니다. 계정 만들기, 2단계 인증, 토큰 발급, GitHub에 비밀 값 넣기는 사람 몫입니다. 한 사람이 계정을 둘 가져도 되는지는 약관에서 그런 문장을 찾지 못했고(검색어 몇 개로 본 것입니다), 약관에는 6개월 넘게 쓰지 않은 계정을 닫을 수 있다는 조항이 있습니다(조사 보고에서 옮긴 것입니다). 원하는 이름이 비어 있는지는 확인하지 않았습니다.

정해진 것: 판 번호는 커밋 접두로 자동 계산하고(fix만이면 끝자리, feat이나 `feat!:`이면 가운데, 1.0.0은 따로 결정), 노트는 제품 폴더를 고친 PR 제목을 묶어 만들며(첫 판만 소개 글 자리), 이미지는 이 제품만의 새 Docker Hub 계정 아래에 올린다. 앞 화면의 추천이었던 "판마다 노트 파일을 씀"과 "에이전트가 준비하고 사용자가 승인"은 이 답으로 버려졌다.

첫 질문의 답은 판을 내는 때까지 에이전트가 정하되, 그 판단을 그때그때가 아니라 계획에 미리 적어 두자는 뜻으로 읽었다(이 세션의 해석이고 사용자에게 확인하지 않았다). 이 읽기와 맞는 선례가 이미 하나 있다. pilot-release 기능 계획 5줄이 "public-demo를 뺀 기준선의 다른 행이 모두 닫히면 agent-os의 판 0.1.0을 main에서 내고(ADR 0043)"라고 적는다(이 세션이 Read로 봤다). 다음 라운드에서 이 뜻을 선택지로 풀어 다시 묻는다.

## 라운드 2 뒤에 도착한 보고

인터뷰 전과 라운드 1 뒤에 띄운 서브에이전트 셋의 보고다. 근거의 종류는 보고가 적은 것을 옮겼다. 이 세션은 프로브를 다시 돌리지 않았고, 두 프로브의 `README.md`만 읽었다.

### 실행 경로와 환경 변수

서브에이전트가 코드를 읽었다(파일은 고치지 않았고 `.env`는 열지 않았다).

- `serve`가 쓰는 자리는 둘뿐이다. 하나는 트레이스 폴더다(`--traces`, 기본은 작업 디렉터리 기준 `traces/`. `src/agent_os/adapters/jsonl.py` 101~110줄이 폴더를 만들고 `<run_id>.jsonl`에 덧붙인다). 다른 하나는 플러그인 루트의 `disabled.toml`이고, 관리 API로 플러그인을 켜고 끌 때만 쓴다. 같은 폴더에 임시 파일을 만든 뒤 `os.replace`로 바꿔 끼우므로 파일 하나가 아니라 플러그인 루트 폴더가 쓰기 가능해야 한다(`src/agent_os/adapters/filesystem.py` 191~201줄, 375~384줄). 루트를 읽기 전용으로 붙이면 켜고 끄는 요청만 500이고 나머지는 돈다(같은 파일 372줄).
- 트레이스를 지우는 코드는 `src/agent_os`에 없다(Grep). 보존은 배포의 몫이다. public-demo 기능 계획은 기한이 지난 트레이스 파일을 지우는 배포의 예약 작업을 전제로 하고, ops-backup-upgrade 기능 계획은 플러그인 폴더와 트레이스 폴더가 이미지 밖에 있어 태그를 바꿔도 남는 것을 전제로 한다.
- 플러그인 루트와 트레이스 폴더는 인자로만 받고 환경 변수가 없다. 기본값은 둘 다 작업 디렉터리 기준 상대 경로다(`src/agent_os/channel/cli/main.py` 68~69줄, 271~281줄).
- `serve`는 사이트 파일을 `--site-file`로만 받고 시작할 때 한 번 읽는다(`src/agent_os/main.py` 165~166줄, 411줄). ADR 0023의 2026-11-04 이력은 변경 시각으로 다시 읽기를 정했지만 아직 구현되지 않았다.
- 비밀이 드는 환경 변수는 `AGENT_OS_ADMIN_TOKEN`, `AGENT_OS_CHANNEL_TOKEN`, `ANTHROPIC_API_KEY`, 그리고 http MCP 매니페스트의 `[server.headers]`가 적은 변수다. 질문 페이지의 서명 개인 키는 환경 변수가 아니라 설정 파일이 가리키는 파일이다.
- 운영자 채널 실행의 주체 이름은 `getpass.getuser()`로 읽는다(`src/agent_os/main.py` 121줄, 174줄). root가 아닌 컨테이너 사용자에게 passwd 항목이 없고 `LOGNAME`·`USER`·`LNAME`·`USERNAME`도 없으면 실패할 수 있다(어림, 재지 않았다).
- stdio MCP 서버는 `env`와 `cwd`를 넘기지 않고 띄운다(`src/agent_os/adapters/mcp.py` 551~568줄). `npx -y`는 HOME의 npm 캐시에 쓸 것이다(어림).
- 관리 화면과 위젯의 기본 포트는 둘 다 3000이라 한 이름공간에 두면 하나를 바꿔야 한다. 관리 화면의 `AGENT_OS_UPSTREAM`은 빌드 때 산출물에 박힌다. 위젯의 `start`도 `next.config.ts`를 다시 읽으므로 `AGENT_OS_SITE_FILE`이 가리키는 파일이 시작할 때도 있어야 한다(`web/apps/widget/next.config.ts` 5~11줄).
- 질문 페이지는 환경 변수를 읽지 않고 `--config`와 `--site-file`을 받는다. 시작할 때 Tailwind CLI를 돌려 토큰 CSS를 메모리에 지으므로 이미지의 `node_modules`에 `@tailwindcss/cli`와 `@agent-os/ui`가 있어야 한다(`web/apps/portal/server/assets.ts` 101~114줄).
- 상태 확인 끝점은 `serve`의 `GET /health`(인증 없음, 앱이 섰는지만 본다)와 질문 페이지의 `GET /portal/health`뿐이다. 관리 화면과 위젯에는 없다(`web/apps`를 Grep).
- 플러그인 코드는 `serve`와 같은 인터프리터에 실리고(`importlib`의 `spec_from_file_location`), 플러그인마다 의존성을 따로 설치하는 길은 없다(`src/agent_os/adapters/filesystem.py` 457~470줄).
- 확인하지 못한 것: 플러그인 루트를 읽기 전용으로 붙였을 때 `__pycache__` 쓰기 실패가 조용히 넘어가는지, `next start`가 `.next/cache`에 쓰는지(둘 다 어림).

### 위젯 빌드(widget_build 프로브)

`.scratch/release-image/probes/widget_build/measure.mjs`로 쟀다. 환경은 Windows 10, node v24.19.0, pnpm 11.24.0, Next 16.3.6, Vite 8.3.1이고, 다른 세션이 함께 돌던 때라 시간은 범위로만 읽는다.

- 위젯 빌드는 PC가 덜 바쁠 때 처음 빌드 17.0~20.0초, 두 번째 빌드 13.3~18.0초였고, CPU가 가득 찼을 때는 처음 빌드가 76.0초까지 갔다. 두 번째 빌드가 줄이는 것은 컴파일 구간뿐이고 타입 검사와 페이지 구간은 줄지 않았다.
- 사이트 파일을 바꾸면 산출물 열 개가 바뀐다. 허용 출처는 `routes-manifest.json`의 `frame-ancestors`, `required-server-files`, 서버 쪽 번들, 브라우저 쪽 번들에 들고, 브라우저 쪽 번들은 내용 해시 이름까지 바뀐다. `public/element.js`에는 글자 수 상한만 든다(사이트 파일 둘로 빌드한 산출물 1,320개를 맞댔다).
- 텔레메트리를 끈 빌드에서 node 쪽의 루프백 밖 연결 시도는 0건이었다. 양성 대조(닿지 않는 주소로의 `fetch`가 훅에 적힘)는 마지막 실행에서만 섰다. Turbopack(Rust)이 직접 여는 소켓은 이 훅이 보지 못한다.
- 크기는 `.next/` 66.9MB(그 가운데 실행에 쓰지 않는 `cache/`가 48.8MB)이고, 빌드와 시작에 필요한 의존성은 394.9MB에서 636.8MB 사이다.
- 지금의 위젯 `start`도 `vite`와 `@tailwindcss/vite`를 적재한다(`web/apps/widget/tools/start.ts` 35줄, 코드를 읽었다). `next build`의 타입 검사는 시험·스토리·e2e 파일까지 포함한 tsconfig 전체를 보므로 빌드에 개발 의존성이 필요할 수 있다(어림, 빼고 돌려 보지 않았다).
- 관리 화면 빌드는 26.7~40.6초였다.
- 재지 못한 것: 리눅스 컨테이너에서의 모든 값, 네트워크가 실제로 없는 빌드, `start`의 동작(사이트 파일만 바꾸고 다시 빌드하지 않은 채 띄울 때 무엇이 옛 값으로 남는지), `output: "standalone"`.

### 컨테이너 배치 후속(netns 프로브 항목 7)

`.scratch/release-image/probes/netns/run.py` 항목 7로 쟀다. 이름공간의 주인을 아무 일도 하지 않는 전용 컨테이너(`holder`)로 두고 proxy·app·admin이 그 이름공간을 빌리는 배치다. 마지막 판으로 항목 1~7 전체를 한 번 돌려 71회차 모두 측정이었고 종료 코드 0이었다. 항목 7은 두 번씩만 돌렸다.

- 배치는 동작한다. proxy를 다시 띄우는 여섯 조작(compose 밖의 `docker restart`와 재시작 정책 포함)에서 모두 app과 admin에 닿았고 app은 다시 시작되지 않았다. 주인이 proxy인 배치에서는 같은 여섯 가운데 셋이 502였다.
- 대신 약한 고리가 holder로 옮겨 간다. holder가 compose 밖에서 다시 뜨면 빌린 셋이 옛 이름공간에 남아 호스트의 요청이 nginx에 닿지 못한다. 회복은 경우마다 다르다. holder가 같은 컨테이너로 다시 시작되면 `docker compose up -d`는 아무것도 바꾸지 않고 `docker compose restart proxy app admin`이 회복하며, holder가 다시 만들어지면 `up -d`가 회복한다. `docker compose restart holder`는 compose가 셋도 함께 다시 시작해 닿는다.
- `docker kill`로 죽인 holder는 `restart: always`가 있어도 다시 뜨지 않았고, holder의 프로세스가 스스로 끝난 갈래에서는 Docker가 다시 띄웠다. 사람이 멈춘 컨테이너는 정책이 다시 띄우지 않는다는 문서의 설명에 해당하는 것으로 보지만 문서를 대 보지 않았다(어림).
- app 하나만 다시 만들어도 닿고, `nginx -s reload`는 컨테이너를 다시 시작하지 않고 새 설정을 읽는다(컨테이너 안에 써 넣은 설정 파일로 봤다. 호스트에서 얹은 파일은 보지 않았다).
- 재지 못한 것: Docker 데몬이나 호스트를 다시 켠 뒤(holder가 다시 뜨는 가장 흔한 길), holder 배치에 `depends_on`을 짧은 꼴로 적은 판, 리눅스의 Docker Engine.
- `run.py`의 타입 검사는 저장소 루트에서 파일 경로만 주면 분석하지 않고 "0 errors"를 낸다(`summary.filesAnalyzed` 0, 서브에이전트가 손으로 봤다). 폴더에 strict `pyrightconfig.json`을 두고 `-p`로 돌려 0건이 되게 타입 우회 없이 고쳤다. `tools/check_type_escapes.py`의 범위에도 들지 않아, 서브에이전트가 그 판정 함수에 `run.py`를 손으로 넣어 0건인 것을 봤다.

## 회고

인터뷰를 끊고 다른 계정의 세션에 넘기며 "다음" 절을 쓴 계기로 돌렸다. 후보 다섯, 승인 셋(모두 회차로 세어 대기열에 둔다), 기각 둘, 넘김 0이다. 만료할 항목은 없었다(`tools/queue_open_rows.py`를 작업 트리와 `--ref origin/main`으로 돌렸다).

1. **승인(회차).** 압축 뒤의 이 세션이 후속 측정을 맡긴 서브에이전트에게 `uv run pyright .scratch/release-image/probes/netns/run.py`로 타입 검사를 보라고 알려 줬고, 그 명령은 `filesAnalyzed` 0으로 "0 errors"를 냈다. 서브에이전트가 스스로 잡아 폴더에 `pyrightconfig.json`을 두고 `-p`로 돌렸다. 열린 항목이 이미 처방한 사건이라 `대기열 431`에 회차를 더했다(9회차. 회차 5 이상이라 chore 배치의 대상이다).
2. **승인(회차).** Glob 도구에 `path` `.scratch`와 패턴 `*/probes/README.md`를 줘 "No files found"를 받고, `**/`로 다시 쳤다. `CLAUDE.md` 환경 함정의 Glob 줄을 어긴 것이고 그 줄을 낸 `대기열 211`이 닫혀 있어, 새 항목 `glob-slash-pattern-narrowed-path`를 `0211의 2회차`로 썼다. 처방은 지침보다 한 층 높은 계기 훅이고, Grep 쪽을 세는 열린 `grep-glob-slash-pattern`과 서로 가리키게 했다.
3. **승인(회차).** 라운드 2 첫 화면의 설명("끝자리만 오른 판은 운영자가 이미지 태그만 바꾸면 된다")을 사용자가 버그 수정 판에 노트가 없다는 뜻으로 읽었다. 같은 일을 다룬 항목이 없어(`오해`, `고르지 못`, `잘못 읽`, `선택지 설명`, `쉬운 말`로 찾았다. `대기열 101`·`308`은 대 보지 않은 사실을 다뤄 다른 일이다) 새 항목 `option-description-implied-omission`을 1회차로 썼다. 자동 검사가 잡을 수 없는 판단이라 지침 층이다.
4. **기각.** 워크트리 가드가 괄호가 든 `git rev-list … --grep=^(feat|fix)`를 거부했다. 이미 있는 앱 가드가 그 자리에서 막았고 `CLAUDE.md` 환경 함정이 적은 일이라, 명령을 둘로 나눠 쳤다.
5. **기각.** 서브에이전트 둘의 완료 알림이 왔는데 보고 내용이 이 세션에 보이지 않아, 프로브의 `README.md`를 읽고 한 서브에이전트에게는 다시 보내 달라고 했다. 보고는 나중에 메시지로 모두 도착했다. 앱의 전달 동작이라 저장소의 층에서 고칠 자리가 없다.

## 다음

다른 계정의 세션이 이 설계 인터뷰를 잇는다. 커밋한 것이 없다. 이 일지와 `.scratch/release-image/probes/`는 산출물 단계(ADR, `CONTEXT.md`, 기능 계획의 설계 줄)와 함께 한 커밋으로 싣는다. 세션 스크래치패드에 내려받은 원문과 서브에이전트의 원본 출력은 이 세션과 함께 사라지므로, ADR의 근거로 쓸 사실은 위에 적은 주소에서 다시 받아 대 보고, 측정은 프로브를 다시 돌린다.

1. **라운드 2 첫 질문을 다시 묻는다.** 위 "첫 질문의 답은…" 문단의 읽기를 선택지로 풀어 확인받는다. 올리기 전에 대 볼 것: 에이전트가 판 내기 단추를 누르는 길(`gh workflow run`)이 사용자의 gh 인증으로 되는지, 배포 환경의 보호 규칙과 함께 되는지(어림, 확인하지 않았다), 판을 내는 때를 어느 파일에 미리 적는지(기능 계획, `.scratch/plan.md` 등). 이 결정은 에이전트가 따르는 절차(`next-session`의 결정표와 `merge.md`)를 바꿀 수 있으므로, 합의 요약 전에 grilling의 갈래 밟기를 한다(인계받은 세션, 끊은 세션, 나란히 도는 티켓 세션이 병합할 때 누가 누르는지, 판 내기가 실패했을 때).
2. **다음 라운드의 frontier.** 컨테이너 배치(이름공간 공유와 그 holder 변형, 호스트 네트워크, 루프백 규칙 완화, 단일 컨테이너)와 관리 화면에 닿는 길(nginx 둘째 `listen` 포트와 SSH 포워딩), 위 회복 절차를 배포 안내에 어떻게 적을지. 위젯의 사이트 파일이 빌드 입력인 문제(시작 때 빌드, 런타임 설정으로 바꿈, 배포자가 다시 빌드). 플러그인 루트와 트레이스 폴더의 볼륨(쓰기 자리 둘, 이미지에 든 기본 플러그인과 볼륨의 관계, public-demo의 규칙 파일). 이미지 사용자와 passwd, 상태 확인(관리 화면과 위젯에 끝점이 없음). SBOM·CVE 점검의 범위와 도구. 프록시 세부(TLS 인증서, 빈도 제한 기본값, 리눅스에서 `$remote_addr`가 실제 접속 주소인지). compose e2e를 CI의 어디에서 돌릴지, 베이스 이미지.
3. **합의 요약에서 바로잡아 확인받을 것.** 라운드 1의 "태그의 판 번호가 pyproject.toml에 적힌 판(지금 0.1.0)과 다르면 CI가 실패합니다"는 판 번호의 원천이 태그가 되면서 맞지 않게 됐다. 저장소의 `pyproject.toml`과 계약 파일 `openapi.json`에 적힌 0.1.0을 어떻게 둘지, 이미지에 번호를 넣는 방법을 함께 정한다.
4. 합의 요약을 확인받은 뒤의 산출물 단계는 `grill-with-docs`의 것이다.
