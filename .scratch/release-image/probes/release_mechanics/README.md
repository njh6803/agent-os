# release_mechanics

release-image 명세가 ADR 0056에서 넘겨받은 세부(판 내기의 차례, 번호 태그, 취약점 점검, Docker Hub 받는 횟수, Docker 액션, compose 최소 판, 릴리스 노트, 다시 돌리기)를 원문과 작은 로컬 측정으로 대 본 자리다. 고르지 않고 고를 재료를 적는다. 원문은 모두 2026-11-13에 받았고 측정과 손 확인도 그날 했다. 번호는 맡은 일의 번호이고, 8은 뒤에 더해진 일이다. 확인하지 못한 것은 항목마다 그렇다고 적는다.

## 근거의 종류

- 쟀다: 이 폴더(`.scratch/release-image/probes/release_mechanics/`)의 커밋한 프로브가 다시 낸다. 프로브 이름을 함께 적는다.
- 손으로 봤다: 명령을 손으로 쳐서 본 것이다. 명령을 함께 적는다. 다시 내는 프로브는 없다.
- 읽었다: 도구의 소스 원문을 판과 함께 받아 읽었다.
- 원문을 받아 대 봤다: 문서 원문(페이지 본문, 저장소의 마크다운, 문서 API의 JSON)을 내려받아 문장을 찾았다. 주소를 함께 적는다. docs.github.com은 `https://docs.github.com/api/article?pathname=<경로>`로 받았다.
- 어림: 위 어느 것도 아닌 풀이다.

웹 요약은 쓰지 않았다.

## 프로브

| 파일 | 재는 것 | 다시 돌 때 |
|---|---|---|
| `registry_tags.py` | 2번(번호 태그를 덮지 않는 길), 5번의 `load: true`, 8번의 다시 짓기 | `uv run python .scratch/release-image/probes/release_mechanics/registry_tags.py`. Docker와 buildx, 비어 있는 호스트 포트 39460~39462가 필요하다. 걸린 시간은 재지 않았다 |
| `scan_tools.py` | 3번(Trivy와 Grype의 건수, 문턱 플래그의 종료 코드, 두 도구의 겹침, SBOM 형식) | `uv run python .scratch/release-image/probes/release_mechanics/scan_tools.py`. Docker가 필요하다. DB 볼륨을 주지 않으면 두 DB를 받는다(풀어 둔 크기 약 5 GiB) |

## 도구의 판

- 이 PC: Windows 10, Docker Desktop 엔진 29.9.2(리눅스 컨테이너, 이미지 저장 방식 overlay2라 containerd 스냅샷 저장소가 아니다), buildx v0.38.1, Docker Compose v5.6.1, gh 2.98.0
- 로컬 레지스트리: `registry:3`(distribution 3.1.2), `registry@sha256:82f6ff4a7f982960c8aa51617fea3aabc485df6e55cce80d22deb1de36f1bc3c`
- 점검 도구 이미지(digest로 고정): Trivy 0.76.2 `ghcr.io/aquasecurity/trivy@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb`, Grype 0.121.3 `ghcr.io/anchore/grype@sha256:13113eeceab017260370cf540e1d25442c59665fd07d1b09b66d63bb0c282887`, Syft 1.57.1 `ghcr.io/anchore/syft@sha256:03215d0e98b661d0ecbc8575dbc14d65be1743b5de5df6410aecb7e80f95b060`

## 1. 릴리스와 태그의 차례

불변식 "실패한 판 내기가 그 판의 git 태그와 공개된 릴리스를 남기지 않는다"에 쓰는 사실이다. GitHub에 릴리스나 태그를 실제로 만들어 보지 않았다(맡은 일의 금지). 그래서 아래 차례는 원문과 gh 소스로 선 것이고 실행으로 확인하지 못했다.

- 초안이 태그를 만드는가. REST 문서에는 초안이면 태그를 만들지 않는다는 문장이 없다. Create a release의 `draft`는 "true to create a draft (unpublished) release, false to create a published one."뿐이다. 원문을 받아 대 봤다(https://docs.github.com/en/rest/releases/releases, 같은 내용의 github/docs `src/rest/data/fpt-2026-03-10/releases.json`에서도 찾지 못했다).
- 간접 근거. gh 2.98.0의 `pkg/cmd/release/shared/fetch.go`는 "FetchRelease finds a published repository release by its tagName, or a draft release by its pending tag name."이라 적고, 초안은 REST로 찾을 수 없어 GraphQL로 찾는다고 적는다. 읽었다(https://raw.githubusercontent.com/cli/cli/v2.98.0/pkg/cmd/release/shared/fetch.go). REST의 Get a release by tag name도 "Get a published release with the specified tag."다(원문을 받아 대 봤다, 위 주소). 초안의 태그 이름은 아직 태그가 아닌 "기다리는" 이름이라고 읽힌다(어림). 릴리스 화면 안내(https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)도 새 태그를 고르는 법과 "Save draft"만 적고 태그가 생기는 때는 적지 않는다(원문을 받아 대 봤다).
- gh 도움말: "If a matching git tag does not yet exist, one will automatically get created from the latest state of the default branch." `--target`은 그 자동 생성의 가지나 커밋을 바꾸고, `--verify-tag`는 태그가 없으면 멈춘다. 읽었다(cli/cli v2.98.0 `pkg/cmd/release/create/create.go`). 기본 브랜치가 `dev`인 이 저장소에서 `--target`을 빠뜨리면 태그가 dev 끝에서 생긴다(어림).
- 태그를 어디서 만드는가. Create a release의 `target_commitish`는 "Specifies the commitish value that determines where the Git tag is created from. Can be any branch or commit SHA. Unused if the Git tag already exists. Default: the repository's default branch." 원문을 받아 대 봤다(같은 주소). 만드는 때가 공개 때라는 문장은 없다. 태그가 이미 있으면 `target_commitish`를 쓰지 않으므로, 초안을 만들기 전에 그 번호의 태그가 없는지 봐야 한다(어림).
- 공개. Update a release의 `draft`는 "true makes the release a draft, and false publishes the release." 원문을 받아 대 봤다(같은 주소).
- gh `release create`. 도움말이 자산을 붙이면 "separate API calls are made to create the release as a draft, upload the assets, and then publish the release."라 적는다. 코드는 자산이 있고 `--draft`가 아니면 초안으로 만들고(`draftWhileUploading`), 올리기나 공개가 실패하면 `cleanupDraftRelease`로 초안을 지우며, 공개는 `{"draft": false}`를 보내는 PATCH다. 공개 전에 같은 태그의 공개 릴리스가 있으면 "a release with the same tag name already exists"로 멈춘다. 도움말은 "Immutability is enforced only after a release is published. Draft releases can be modified or deleted, and the associated git tags can be modified or deleted as well."이라고도 적는다. 읽었다(https://raw.githubusercontent.com/cli/cli/v2.98.0/pkg/cmd/release/create/create.go).
- 기본 브랜치 함정. 이 저장소의 기본 브랜치는 `dev`이고(손으로 봤다, `gh api repos/{owner}/{repo} --jq .default_branch`) 판은 `main`에서 낸다. Create a release와 Update a release의 주석: "If the commit identified by target_commitish (or, when target_commitish is omitted, the latest commit on the default branch) adds or modifies any file under .github/workflows/ relative to the repository's default branch, the authenticating token must be authorized to modify workflows. Otherwise, this endpoint returns 404 Not Found; some authentication paths surface 403 Resource not accessible by integration instead." 그리고 "The GITHUB_TOKEN available to GitHub Actions cannot be authorized for this". 원문을 받아 대 봤다(같은 주소). 그래서 main과 dev의 `.github/workflows/`가 다를 때(워크플로를 고친 핫픽스를 dev로 되돌려 합치기 전 등) `GITHUB_TOKEN`으로 릴리스를 만들거나 공개하면 404나 403으로 실패할 수 있다. 무엇과 무엇을 견주는지는 문서에 없어 이 풀이는 어림이고, 실제로 돌려 보지 못했다. 피하는 길(워크플로 쓰기 권한이 있는 GitHub App 토큰이나 세분 토큰을 그 단계에만 쓰기)은 그 토큰이 만든 태그와 릴리스가 다른 워크플로를 띄운다는 값을 치른다(아래 이벤트 줄과 함께 어림).
- 이벤트. "When you use the repository's `GITHUB_TOKEN` to perform tasks, events triggered by the `GITHUB_TOKEN` will not create a new workflow run"(예외는 `workflow_dispatch`, `repository_dispatch`, 승인이 필요한 상태의 `pull_request` 일부). 원문을 받아 대 봤다(https://docs.github.com/en/actions/concepts/security/github_token). "Workflows are not triggered for the `created`, `edited`, or `deleted` activity types for draft releases." 원문을 받아 대 봤다(https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows).
- 권한. 워크플로 문법의 `permissions` 표가 "`contents: write` allows the action to create a release"라 적는다(https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions). 릴리스 만들기·고치기와 `git/refs` 만들기는 Contents 쓰기 권한이다(https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps). 원문을 받아 대 봤다.
- 규칙셋. "Restrict creations — If selected, only users with bypass permissions can create branches or tags whose name matches the pattern you specify." Restrict updates와 Restrict deletions도 있고 Restrict deletions는 기본으로 골라진다. 원문을 받아 대 봤다(https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets). 옛 태그 보호 규칙 주소는 규칙셋 문서를 낸다. 이 저장소에는 규칙셋이 없다(손으로 봤다, `gh api repos/{owner}/{repo}/rulesets`가 `[]`). 사용자 소유 저장소에서 Actions를 우회 목록에 넣을 수 있는지는 확인하지 못했다.
- 변경 불가 릴리스. "Git tags cannot be moved: Once an immutable release is published, its associated Git tag is locked to a specific commit, cannot be changed, and cannot be deleted while the release exists. If you delete the immutable release, you can delete the tag, but you cannot reuse the same tag name." 권하는 차례는 초안으로 만들기, 초안에 자산 붙이기, 초안 공개의 셋이다. 원문을 받아 대 봤다(https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases). 이 저장소는 꺼져 있다(손으로 봤다, `gh api repos/{owner}/{repo}/immutable-releases`가 `{"enabled":false,"enforced_by_owner":false}`). 켜면 한 번 공개한 번호는 릴리스를 지워도 다시 쓰지 못하므로, 공개가 마지막 단계여야 한다는 요구가 더 세진다(어림).
- 동시 실행. 기본은 "any existing `pending` job or workflow in the same concurrency group will be canceled and the new queued job or workflow will take its place." `queue: max`는 "Up to 100 jobs or workflow runs can be `pending` in the concurrency group. When the queue is full, any additional jobs or workflow runs are canceled." `queue: max`와 `cancel-in-progress: true`를 함께 쓰면 검증 오류다. 기다리기 시작한 차례로 돌지만 "ordering is not guaranteed"라 적는다. 원문을 받아 대 봤다(https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs).

명세가 고를 차례의 재료(어림, 실행으로 확인하지 못했다).

1. 네 이미지를 짓고 실제로 띄워 시험하고 점검한다.
2. 커밋 해시 태그로만 올린다.
3. 그 번호의 git 태그와 공개 릴리스가 없는지 본다.
4. 초안 릴리스를 `target_commitish=<그 커밋의 전체 SHA>`로 만들고 자산을 올린다.
5. 레지스트리에 번호 태그를 2번의 지키는 차례로 붙인다.
6. 초안을 공개한다. 이때 git 태그가 생긴다고 본다. 4~6 가운데 실패하면 초안을 지운다.

5가 6보다 앞인 까닭. 6 뒤에 5가 실패하면 공개 릴리스와 git 태그가 이미지 없이 남는다. 5 뒤에 6이 실패하면 레지스트리의 번호 태그만 남고, 같은 커밋으로 다시 돌리면 2번의 "같은 digest면 그대로 둔다"를 지나 이어 간다.

## 2. 번호 태그를 덮지 않는 방법

쟀다(probes/release_mechanics/registry_tags.py, 로컬 `registry:3`). 첫 실행은 `tags`·`lookup`·`overwrite`·`guard`·`load` 19회차가 모두 측정이고 측정 아님 0이었다. 뒤에 더한 `rebuild` 갈래(8번)는 `--sections rebuild`로 따로 돌려 2회차가 모두 측정이었다. 그 뒤 JSON을 푸는 도움 함수의 타입 표기만 고치고(pyright strict에 맞추려고) 모든 갈래를 다시 돌려 21회차가 모두 측정이고 측정 아님 0이었으며, 회차마다 결과가 앞의 두 실행과 같았다. 같은 날 손으로 출력 모양을 본 뒤 프로브를 지었고, 돌린 뒤 판정 기준을 바꾸지 않았다.

- 가. 해시 태그로 올린 뒤 `docker buildx imagetools create -t <번호 태그> <해시 태그>`로 번호를 붙인다.
  - 원본이 한 플랫폼 매니페스트일 때(`docker push`로 올린 증명 없는 이미지) 기본값은 번호 태그에 새 매니페스트 목록을 만들어 digest가 달라진다. 목록 안의 digest는 원본과 같다. `--prefer-index=false`를 주면 digest가 같다.
  - 원본이 출처 증명과 SBOM이 붙은 이미지 색인일 때(build-push-action이 바로 올릴 때의 꼴) 기본값으로도 digest가 같다. 다른 저장소 이름으로 옮겨도 같다.
  - 원문: "If only one source is specified and that source is a manifest list or image index, create performs a carbon copy. If one source is specified and that source is *not* a list or index, the output will be a manifest list, however you can disable this behavior with `--prefer-index=false` which attempts to preserve the source manifest format in the output." 원문을 받아 대 봤다(https://raw.githubusercontent.com/docker/buildx/master/docs/reference/buildx_imagetools_create.md).
- 양성 대조. 이미 있는 번호 태그에 `docker push`도 `imagetools create`도 거부 없이 덮는다(종료 0, 태그의 digest가 바뀐다). 레지스트리는 막지 않는다.
- 나. 조회. `docker buildx imagetools inspect <참조>`의 종료 코드와 마지막 줄이다.

| 상황 | 종료 코드 | 마지막 줄 |
|---|---|---|
| 있는 태그 | 0 | 매니페스트를 찍는다 |
| 없는 태그, 없는 저장소 | 1 | `ERROR: <참조>: not found` |
| 아무것도 듣지 않는 포트 | 1 | `ERROR: failed to do request: Head "http://…": dial tcp …` |
| 401·429·500만 내는 가짜 서버 | 1 | `ERROR: unexpected status from HEAD request to …: 401 Unauthorized`(429 Too Many Requests, 500 Internal Server Error도 같은 꼴) |

  마지막 실행에서 `imagetools inspect` 한 번에 가짜 서버가 받은 요청은 401과 429에서 5건, 500에서 2건이었다. 프로브가 요청의 수만 적어 어떤 요청을 왜 되풀이했는지는 모른다. `docker manifest inspect --insecure`도 없음과 실패가 모두 종료 1이다(`no such manifest: <참조>`, `failed to configure transport: error pinging v2 registry: …`). 종료 코드만으로는 "없다"와 "모른다"를 가를 수 없다. 마지막 줄이 `: not found`로 끝날 때만 없다고 읽어야 한다. 레지스트리의 HTTP `HEAD /v2/<저장소>/manifests/<태그>`는 200과 404로 가른다.
- 지키는 차례(가와 나를 함께). 조회해 없으면 `--prefer-index=false`로 붙이고, 같은 digest면 그대로 두고, 다른 digest면 거부하고, 조회가 실패하면 붙이지 않는다. 네 갈래 모두 기대대로 났고 뒤의 태그는 처음 붙인 digest를 가리켰다.
- Docker Hub에서. 로그인하지 않고(이 PC에 저장된 자격을 보내지 않게 빈 `DOCKER_CONFIG`로) 물었다. 있는 태그 `docker.io/library/alpine:3.22`는 종료 0, 있는 저장소의 없는 태그 `docker.io/library/alpine:ri-rel-absent-tag`는 종료 1과 `ERROR: docker.io/library/alpine:ri-rel-absent-tag: not found`로 로컬 레지스트리와 같았다. 없는 저장소 둘(`library/` 아래와 없는 이름공간 아래)은 종료 1과 `ERROR: pull access denied, repository does not exist or may require authorization: server message: insufficient_scope: authorization failed`로, 로컬 레지스트리의 없는 저장소(`not found`)와 달랐다(손으로 봤다, `DOCKER_CONFIG=<빈 폴더> docker buildx imagetools inspect <참조>`, buildx v0.38.1). 그래서 번호 태그 조회는 해시 태그를 올려 저장소가 생긴 뒤에 해야 "없다"가 `not found`로 나온다. 로그인한 토큰으로 자기 저장소의 없는 태그를 물을 때의 문구는 로그인이 금지라 보지 못했다.
- 못 본 것. 두 실행이 동시에 조회하고 붙이는 경합(동시 실행 묶음으로 막을 자리), 여러 플랫폼 이미지.
- Docker Hub의 변경 불가 태그. 설정은 "All tags are mutable (Default)", "All tags are immutable", "Specific tags are immutable"의 셋이고 마지막은 정규식(RE2)으로 태그를 고른다. "Immutable tags are image tags that, once pushed to Docker Hub, cannot be overwritten or deleted." 켜면 "You cannot push a new image with the same tag name". 기능 표(`data/summary.yaml`)는 `Immutable tags`를 `availability: Beta` 한 줄로만 적는다. 같은 표가 구독을 가리는 기능에는 `subscription:` 줄을 단다(바로 아래 `Insights`는 `subscription: [Business]`). 그래서 문서로는 무료 개인 계정을 막는 적힘이 없다. 원문을 받아 대 봤다(https://raw.githubusercontent.com/docker/docs/main/content/manuals/docker-hub/repos/manage/hub-images/immutable-tags.md, https://raw.githubusercontent.com/docker/docs/main/data/summary.yaml). 무료 개인 계정에서 실제로 켤 수 있는지는 로그인이 금지라 확인하지 못했다.

## 3. 취약점 점검 도구

쟀다(probes/release_mechanics/scan_tools.py, 35회차가 모두 측정이고 측정 아님 0). 이번 실행은 DB를 다시 받지 않으려고 손 실행에서 채운 DB 볼륨을 `--trivy-cache`·`--grype-cache`로 줬다(Trivy DB 갱신 2026-11-13 07:00 UTC, Grype DB 지은 때 2026-11-13T06:20:21Z). 손 실행에서 출력 모양을 본 뒤 프로브를 지었고, 돌린 뒤 판정 기준을 바꾸지 않았다. 대상은 `docker save`로 받은 tar다. 그 실행 뒤 JSON을 푸는 도움 함수의 타입 표기만 고쳤다(pyright strict에 맞추려고). 고친 판의 해석 함수를 그 실행이 남긴 점검 JSON 열두 개에 다시 걸어 아래 표와 같은 건수를 봤다(손으로 봤다, 세션 스크래치의 `parse_check.py`). 고친 판으로 Docker 실행 전체를 다시 돌리지는 않았다(DB를 다시 받아야 해서).

| 대상 | 도구 | 고칠 수 있는 Critical | 고칠 수 있는 High | 전체 | 점검 시간(이 PC, 두 번) |
|---|---|---|---|---|---|
| `python:3.12-slim-trixie` `python@sha256:5e2bdb1b…` (Python 3.12.16, Debian 13.7) | Trivy | 0 | 2 | 214 | 2.9초, 2.5초 |
| 같은 것 | Grype | 0 | 2 | 217 | 12.6초, 12.5초 |
| `node:24-trixie-slim` `node@sha256:af02d57b…` (Node 24.22.3, Debian 13.7) | Trivy | 0 | 8 | 220 | 16.0초, 4.2초 |
| 같은 것 | Grype | 0 | 8 | 215 | 27.1초, 26.9초 |
| 양성 대조 `python:3.12.10-slim-bookworm` `python@sha256:fd95fa22…` (Debian 12.11) | Trivy | 7행(CVE 6) | 47행(CVE 29) | 532 | 4.4초, 4.6초 |
| 같은 것 | Grype | 20행(CVE 15) | 100행(CVE 67) | 577 | 15.4초, 11.3초 |

- 건수는 꾸러미와 취약점의 짝(행)이고, 두 후보에서는 행과 CVE 수가 같았다. 시간은 컨테이너를 띄우는 시간까지 든 이 PC의 값이고, Trivy의 둘째 회가 빠른 것은 같은 볼륨에 층 분석을 담아 두기 때문으로 풀이한다(어림).
- 두 후보에서 두 도구가 고칠 수 있는 Critical·High로 센 CVE는 같았다(겹침 2와 8, 한쪽만 0). 두 후보 모두 High는 `zlib1g` 1:1.3.dfsg+really1.3.1-1+b1의 CVE-2026-76844·CVE-2026-85091이고 Debian이 `+deb13u1`에서 고쳤다(Grype가 처음 본 날 2026-11-07). node는 그 밖에 npm 꾸러미 `brace-expansion` 5.0.9와 `undici` 6.28.0의 여섯이다(손으로 봤다, 프로브가 남긴 점검 JSON을 세션 스크래치의 `look_high.py`로 늘어놓았다). 바탕 이미지가 다시 지어지기 전에는 Critical·High 문턱이면 두 후보 모두 판 내기를 멈추고, Critical만이면 둘 다 지난다.
- 양성 대조(Debian 12)에서는 Grype가 Trivy를 다 품고 더 냈다. Critical·High의 CVE가 둘 다 35, Grype만 47, Trivy만 0이었다. Grype만인 47을 Trivy는 LOW 9, MEDIUM 19로 매겼거나 19는 내지 않았고, 그 행의 꾸러미 종류는 deb 47행과 binary 19행(`/usr/local`의 CPython을 NVD CPE로 맞춘 것)이다.
- 문턱의 종료 코드. 여섯 대상·도구 짝마다 문턱 둘(Critical만, Critical·High)을 걸어 열둘 모두 종료 코드와 출력 건수가 거르지 않은 JSON에서 따로 센 건수와 맞았다. 찾으면 Trivy는 `--exit-code`로 준 10, Grype는 2이고 없으면 0이다. 없는 입력은 두 도구 모두 1이라 문턱 코드와 갈린다. 쓴 플래그는 Trivy `--ignore-unfixed --severity CRITICAL[,HIGH] --exit-code 10`, Grype `--only-fixed --fail-on critical|high`다. Grype 도움말은 "set the return code to 2 if a vulnerability is found with a severity >= the given severity"다(손으로 봤다, `docker run --rm <grype 이미지> --help`).
- SBOM(`python:3.12-slim-trixie`). Syft SPDX 2.3 JSON 2,307,094 바이트(꾸러미 96, 파일 2,738, 7.8초), Syft CycloneDX 1.7 JSON 949,680 바이트(구성 요소 2,755), Trivy SPDX 2.3 JSON 193,876 바이트(꾸러미 90, 파일 0, 4.1초), Trivy CycloneDX 1.7 JSON 179,727 바이트(구성 요소 89). Syft는 파일 하나하나를 담아 열 배쯤 크다.
- DB. 볼륨 크기 Trivy 1.65 GiB, Grype 3.20 GiB. 새 판인지 보는 데 2.1초, 2.8초였다(받지는 않았다).
- Trivy는 기본으로 익명 사용 자료를 보낸다. 도움말에 `--disable-telemetry`가 "disable sending anonymous usage data to Aqua"로 있다(손으로 봤다, `docker run --rm <trivy 이미지> image --help`). 프로브는 이것과 `--skip-version-check`를 켜고 돈다.

아래는 프로브를 짓기 전에 손으로 본 것이다(손으로 봤다, 세션 스크래치의 `try_scan.sh`. 대상은 위 양성 대조와 `alpine:3.22.8` `alpine@sha256:49340b346798875b5592e5d420241f2f9cfba5f47e62ebb1446a1b34734e898f`를 `docker save`로 받은 tar). 걸린 시간은 Git Bash에 `bc`가 없어 재지 못했다.

- 문턱 플래그와 종료 코드. Trivy `image --input <tar> --ignore-unfixed --severity CRITICAL --exit-code 10 --format json`은 찾으면 10, 없으면 0(alpine), 입력이 없으면 1과 `FATAL` 줄. `--exit-code 1`로 두면 오류와 가를 수 없다. Grype `docker-archive:<tar> --only-fixed --fail-on critical -o json`은 찾으면 2와 `ERROR discovered vulnerabilities at or above the severity threshold`, 입력이 없으면 1과 `failed to catalog: no source providers were able to resolve the input`.
- `--ignore-unfixed`는 "a shorthand of `--ignore-status affected,will_not_fix,fix_deferred,end_of_life`". 원문을 받아 대 봤다(https://raw.githubusercontent.com/aquasecurity/trivy/v0.76.2/docs/guide/configuration/filtering.md).
- 같은 python bookworm 이미지에서 고칠 수 있는 Critical의 CVE가 Trivy 6, Grype 15였다. Grype만인 아홉 가운데 Debian 꾸러미의 여섯을 Trivy는 HIGH·MEDIUM·LOW로 매겼고, 셋은 `/usr/local`의 CPython 바이너리를 NVD CPE로 맞춘 것이라 Trivy가 내지 않았다(손으로 봤다, 두 JSON을 세션 스크래치의 `look_diff.py`로 맞댔다). alpine 3.22.8에서는 Grype만 `CVE-2026-4738`(zlib 1.3.2-r1, 1.4-r0에서 고침, 처음 본 날 2026-11-07)을 고칠 수 있는 Critical로 냈다.
- DB. Trivy는 `mirror.gcr.io/aquasec/trivy-db:2`에서 133.47 MiB를 받았고 풀어 둔 것은 1.7 GB(`trivy.db` 1,766,359,040 바이트)다. Grype는 `https://grype.anchore.io/databases/v6/…`(스키마 v6.1.10)에서 받았고 풀어 둔 것은 3.4 GB(`vulnerability.db` 3,434,344,448 바이트)다. Trivy의 기본 받는 자리는 `mirror.gcr.io/aquasec` 다음 `ghcr.io/aquasecurity`다. 원문을 받아 대 봤다(https://raw.githubusercontent.com/aquasecurity/trivy/v0.76.2/docs/guide/configuration/db.md).
- 출력 크기(python bookworm). Trivy JSON 2,410,422 바이트, SARIF 1,296,140, 표 50,763. Grype JSON 2,787,804, SARIF 2,287,106, 표 33,603. 둘 다 SARIF 2.1.0이다.
- SBOM(python bookworm). Syft SPDX 2.3 JSON 2,766,350 바이트(꾸러미 114, 파일 3,304), CycloneDX 1.7 JSON 1,138,613 바이트(구성 요소 3,338). Trivy SPDX 2.3 JSON 228,030 바이트(꾸러미 108), CycloneDX 1.7 JSON 208,477 바이트(구성 요소 107). buildx `--sbom=true` 증명은 작은 alpine 이미지에서 SPDX JSON 113,879 바이트였고 만든 것은 `docker/buildkit-syft-scanner:stable-1` 속 syft v1.51.0이다(손으로 봤다, `docker buildx imagetools inspect <참조> --format '{{json .SBOM.SPDX}}'`).
- 공식 액션. `aquasecurity/trivy-action` v0.36.0(`ed142fd0673e97e23eac54620cfb913e5ce36c25`)의 `action.yaml`은 `version` 입력의 기본값이 `v0.70.0`이라 입력을 주지 않으면 최신 Trivy가 아니다. `aquasecurity/setup-trivy`를 커밋 `3fb12ec12f41e471780db15c232d5dd185dcb514`(v0.2.6)로 고정하고, DB는 `actions/cache`로 날짜 키를 써 담는다. `anchore/scan-action` v7.4.2(`27805bf3b4e84b4a5c980df22ed233c00390a439`)는 node24 액션이고 기본값이 `severity-cutoff: medium`, `fail-build: true`, `only-fixed: false`, `output-format: sarif`다. 원문을 받아 대 봤다(두 저장소의 그 커밋의 `action.yaml`·`action.yml`).
- 공급망 사고(Trivy). GHSA-69fq-xp46-6x23, 2026-03-24 공개, critical. "On March 19, 2026, a threat actor used compromised credentials to publish a malicious Trivy v0.69.4 release, force-push 76 of 77 version tags in `aquasecurity/trivy-action` to credential-stealing malware, and replace all 7 tags in `aquasecurity/setup-trivy` with malicious commits." 3월 22일에는 악성 v0.69.5·v0.69.6 Docker Hub 이미지. 영향 없음에 "SHA pinning to a safe commit commit after 2025-04-09"와 "trivy images referenced by digest"가 들고, 2025-04-09 이전 커밋으로 고정한 trivy-action은 고정하지 않은 setup-trivy를 불러 영향을 받았다. 원문을 받아 대 봤다(`gh api advisories/GHSA-69fq-xp46-6x23`). ADR 0056의 "커밋으로 고정한 사용자는 영향이 없었다"는 이 날짜 단서가 붙어야 맞다.
- 그 밖의 권고(원문을 받아 대 봤다, `gh api -X GET advisories -f ecosystem=<actions|go> -f affects=<이름>`과 `gh api repos/<저장소>/security-advisories`). Trivy 쪽: trivy-action GHSA-9p44-j4g5-cfx5(2026-02-18, 입력이 셸로 해석되는 주입, `>= 0.31.0, < 0.34.0`, 0.34.0에서 고침), trivy GHSA-mcj4-mphf-j9ff(2026-08-25, high, 조작된 DB 등 내려받은 산출물로 경로 밖에 쓰기, `< 0.71.1`), GHSA-8rc5-4fr6-64pw(플러그인 관리자 경로 밖에 쓰기), GHSA-q3fv-x8vg-qqm4(Helm 차트 tar 폭탄), GHSA-xcq4-m2r3-cmrj(2024, 악성 레지스트리에서 자격 누출, `< 0.51.2`). Anchore 쪽: 공급망 침해 권고는 없고, grype GHSA-6gxw-85q2-q646(2025-11-25, high, 레지스트리 자격이 설정돼 있으면 JSON 출력 파일에 실림, `>= 0.68.0, < 0.104.1`), syft 둘(2026-03 임시 파일 정리, 2023 `SYFT_ATTEST_PASSWORD` 자격 누출)과 syft 저장소 권고 하나(2026-09 이진 입력의 메모리 소진). `anchore/scan-action`과 `anchore/sbom-action`에는 권고가 없었다.
- trivy-action v0.36.0의 기본 Trivy 판 `v0.70.0`은 GHSA-mcj4-mphf-j9ff의 범위(`< 0.71.1`)에 든다. 액션을 쓰면 `version`을 직접 줘야 한다(두 원문을 이은 풀이다).

## 4. Docker Hub 받는 횟수 제한

배포 안내에 옮길 원문 문장(원문을 받아 대 봤다, https://raw.githubusercontent.com/docker/docs/main/content/manuals/docker-hub/usage/pulls.md 와 https://raw.githubusercontent.com/docker/docs/main/content/manuals/docker-hub/usage/_index.md).

- "Unauthenticated and Docker Personal users are subject to a 6-hour pull rate limit on Docker Hub. In contrast, Docker Pro, Team, and Business users benefit from an unlimited pull rate."
- 표 "Pull rate limit per 6 hours": `Personal (authenticated)` 200, `Unauthenticated Users` "100 per IPv4 address or IPv6 /64 subnet", Pro·Team·Business "Unlimited". 두 문서의 표가 같다.
- "Using GET emulates a real pull and counts towards the limit. Using HEAD won't." 예시 머리는 `ratelimit-limit: 100;w=21600`.
- 제3자 플랫폼: "When pulling images via a third-party platform, the platform may use the same IPv4 address or IPv6 /64 subnet to pull images for multiple users. Even if you are authenticated, pulls attributed to a single IPv4 address or IPv6 /64 subnet may cause abuse rate limiting." 남용 제한은 "in the order of thousands of requests per minute"이고 맨 `429 Too Many Requests`로 답한다(받는 횟수 제한은 문서 주소가 든 긴 오류).
- GitHub Actions는 `docker/login-action`으로 로그인하라고 적는다.
- 가격 페이지: Personal 칸에 "100 Docker Hub pulls/hr*"와 각주 "*Access with reasonable use when logged in", 비교 표에 Personal "100 pulls/hr per user". 로그인하지 않은 수는 정적 HTML에서 찾지 못했다. 원문을 받아 대 봤다(https://www.docker.com/pricing/).
- 실제 응답: 로그인하지 않은 토큰으로 `ratelimitpreview/test` 매니페스트를 HEAD로 물으니 `ratelimit-limit: 100;w=3600`, `ratelimit-remaining: 54;w=3600`이었다(손으로 봤다, `auth.docker.io`에서 익명 토큰을 받아 `curl --head https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest`). 창이 3600초라 문서 표의 6시간과 다르다. 세 자리가 서로 맞지 않는다.

## 5. Docker 액션과 버전 고정

- 최신 판과 커밋(손으로 봤다, `gh api repos/<저장소>/releases/latest`와 `gh api repos/<저장소>/git/ref/tags/<태그>`, 모두 가벼운 태그가 커밋을 가리킨다): `docker/login-action` v4.8.0 `8aa5831fb8d48d8f76594c7ddde61ae58019f550`, `docker/setup-buildx-action` v4.4.1 `f87e5991a6d7451dcb8d9637bfbc97413f497069`, `docker/build-push-action` v7.4.0 `c3c9e263c25d99ce0380d002d59b67737d91b0dc`, `docker/metadata-action` v6.2.0 `dc802804100637a589fabce1cb79ff13a1411302`. 같은 때 `aquasecurity/trivy-action` v0.36.0 `ed142fd0673e97e23eac54620cfb913e5ce36c25`, `anchore/scan-action` v7.4.2 `27805bf3b4e84b4a5c980df22ed233c00390a439`, `anchore/sbom-action` v0.24.3 `66cbf4bc1f1c0d2edc94016e65bc221b6bb0ad6c`.
- `load: true`와 증명. "If you're using the `docker` exporter, or you're loading the build results to the runner with `load: true`, no attestations are added to the image. These output formats don't support attestations." 공개 저장소는 출처 증명이 `mode=max`가 기본이고 SBOM은 `sbom: true`를 줘야 붙는다. 원문을 받아 대 봤다(https://raw.githubusercontent.com/docker/docs/main/content/manuals/build/ci/github-actions/attestations.md). 시험 뒤 올리기는 `load: true`로 지어 시험하고 둘째 build-push-action이 `push: true`로 내부 캐시를 쓰는 꼴을 권한다(https://raw.githubusercontent.com/docker/docs/main/content/manuals/build/ci/github-actions/test-before-push.md).
- 쟀다(probes/release_mechanics/registry_tags.py의 `load` 갈래, 이 PC의 옛 저장 방식). 증명을 끈 `--load`로 실은 이미지의 Id는, 뒤이어 같은 빌더가 캐시로 다시 지어 증명과 함께 올린 이미지의 플랫폼 매니페스트 config digest와 같았다. 증명을 켠 채 `--load`하면 종료 1, `ERROR: failed to build: docker exporter does not currently support exporting manifest lists`. GitHub 러너의 이미지 저장 방식은 보지 못했다.
- `type=gha` 캐시. `scope`의 기본값은 `buildkit`이고 "If you build multiple images, each build will overwrite the cache of the previous, leaving only the final cache." 네 이미지는 저마다 `scope`를 줘야 한다. "Only the cache for the current branch, the base branch and the default branch is accessible by a workflow." 원문을 받아 대 봤다(https://raw.githubusercontent.com/docker/docs/main/content/manuals/build/cache/backends/gha.md, https://raw.githubusercontent.com/docker/docs/main/content/manuals/build/ci/github-actions/cache.md). main에서 도는 판 내기는 기본 브랜치 `dev`의 캐시도 읽을 수 있다고 읽힌다(어림).

## 6. compose 기능과 Engine·Compose 최소 판

compose 파일 참조(https://raw.githubusercontent.com/docker/docs/main/content/reference/compose-file/services.md)에서 "Introduced in Docker Compose version"이 붙은 줄을 모두 찾고, 단독 compose가 쓸 기능의 절을 읽었다(원문을 받아 대 봤다). 릴리스 본문은 `gh api repos/docker/compose/releases/tags/<태그>`와 `gh api repos/compose-spec/compose-go/releases/tags/<태그>`로 받았다.

| 기능 | 처음 들어간 판 | 근거 |
|---|---|---|
| `depends_on`의 `restart: true` | Compose 2.17.0 | 원문을 받아 대 봤다("Introduced in Docker Compose version 2.17.0", v2.17.0 릴리스 본문의 "introduce `restart` for depends_on") |
| `depends_on`의 `required` | 문서는 Compose 2.20.0, 릴리스 본문은 2.20.2 | 원문을 받아 대 봤다. 문서는 "Introduced in Docker Compose version 2.20.0"인데 v2.20.0 릴리스 본문에는 `required`가 없고, v2.20.2 릴리스 본문이 "Add support of `depends_on.required` attribute"라 적는다 |
| healthcheck `start_interval` | Compose 2.20.2, Engine 25.0 | 원문을 받아 대 봤다. 같은 문서의 "`interval`, `timeout`, `start_period`, and `start_interval` are specified as durations. Introduced in Docker Compose version 2.20.2", compose-go v1.17.0 릴리스 본문의 "add support of healthcheck.start_interval attribut"(Compose v2.20.2가 compose-go를 v1.17.0으로 올렸다), moby/buildkit Dockerfile 참조(https://raw.githubusercontent.com/moby/buildkit/master/frontend/dockerfile/docs/reference.md)의 "This option requires Docker Engine version 25.0 or later." 문서의 문장은 네 칸을 함께 든 문장 끝에 판을 붙여 `start_period`까지 2.20.2로 읽힐 수 있다. 릴리스 본문이 더한 것은 `start_interval`뿐이라 그 판으로 읽었다(어림) |
| `volumes` 긴 문법의 tmpfs `mode` | Compose 2.14.0 | 원문을 받아 대 봤다(같은 문서) |
| 최상위 `name` | Compose 2.3.0으로 풀이 | 릴리스 본문 두 줄을 이은 어림(compose-go v1.1.0 "Update spec and implement project name", Compose v2.3.0 "Bump compose-go 1.1.0") |
| `127.0.0.1`에만 발행 | Engine 28.0.0, firewalld를 쓰는 호스트는 28.3.3 | 원문을 받아 대 봤다(아래) |
| `init: true`, `read_only`, `tmpfs`(짧은 문법), `restart`(`unless-stopped` 포함), `depends_on`의 `condition: service_healthy`, healthcheck `start_period` | 판 적힘 없음 | 원문을 받아 대 봤다(같은 문서의 그 절에 판 적힘이 없다. 다만 `start_period`는 위 2.20.2 문장에 함께 든다. `docker run` 참조(https://raw.githubusercontent.com/docker/cli/master/docs/reference/commandline/container_run.md)의 옵션 표에서 `--init`·`--read-only`·`--tmpfs`·`--health-start-period`에도 판 적힘이 없다) |

- 포트 발행: "In releases older than 28.0.0, hosts within the same L2 segment (for example, hosts connected to the same network switch) can reach ports published to localhost." 원문을 받아 대 봤다(https://raw.githubusercontent.com/docker/docs/main/content/manuals/engine/network/port-publishing.md). Engine 28 릴리스 노트의 28.0.0에 "Fix a security issue that was allowing neighbor hosts to connect to ports mapped on a loopback address."(moby/moby#49325), 28.3.3에 "This release fixes an issue where, after a firewalld reload, published container ports could be accessed directly from the local network, even when they were intended to be accessible only via a loopback address."(CVE-2025-54388). 원문을 받아 대 봤다(https://raw.githubusercontent.com/docker/docs/main/content/manuals/engine/release-notes/28.md).
- IPv6를 켠 네트워크: Engine 27 릴리스 노트의 27.0.1 절, Networking 아래 IPv6 항목에 "With ip6tables enabled, if ip6tables is not functional on your host, Docker Engine will start but it will not be possible to create an IPv6-enabled network." 원문을 받아 대 봤다(https://docs.docker.com/engine/release-notes/27/의 페이지 본문). ip6tables가 돌지 않는 호스트에서 IPv6를 켠 compose 네트워크를 띄우면 실제로 무엇이 나는지는 재지 않았다.
- 최소 판의 재료(어림): Engine은 28.3.3(28.0.0의 고침과 firewalld 재적재 고침을 모두 지나고, `start_interval`의 25.0도 덮는다), Compose는 `start_interval`이나 `depends_on`의 `required`를 쓰면 2.20.2, 둘 다 쓰지 않고 `depends_on`의 `restart: true`만 쓰면 2.17.0이다. `required`는 문서의 2.20.0이 아니라 릴리스 본문의 2.20.2를 따랐다. 이 PC는 Engine 29.9.2, Compose v5.6.1이라 아래쪽 판에서 돌려 보지는 않았다.
- nginx: "Changes with nginx 1.27.3 26 Nov 2024"에 "the "server" directive in the "upstream" block supports the "resolve" parameter."와 upstream 블록의 `resolver`·`resolver_timeout`. 모듈 문서는 "Prior to version 1.27.3, this parameter was available only as part of our commercial subscription."이라 적고, 그 그룹이 공유 메모리(`zone`)에 있어야 한다. 원문을 받아 대 봤다(https://nginx.org/en/CHANGES, https://nginx.org/en/docs/http/ngx_http_upstream_module.html).

## 7. 릴리스 노트의 재료

손으로 봤다(세션 스크래치의 `notes_git.sh`·`notes_next.sh`, git 2.32, 읽기만 하는 `git rev-list`·`git log`). 커밋한 프로브는 없다.

- `origin/main`(`afe4b7f86`)은 565커밋이고 병합 커밋은 dev를 main으로 올린 #542 하나다. 그 앞의 main은 제목이 `(#NNN)`으로 끝나는 squash 커밋의 줄이다.
- `--first-parent`는 틀린다. #542의 첫 부모(`82297e614`, 옛 main)를 지난 판으로 두면 `git rev-list --first-parent 82297e614..afe4b7f86`은 병합 커밋 하나만 낸다. 티켓 PR의 squash 커밋은 출시 병합의 둘째 부모 쪽에 있어 첫 부모만 따라가면 빠진다. git 문서도 `--first-parent`를 "Follow only the first parent commit upon seeing a merge commit."이라 적는다(원문을 받아 대 봤다, 설치된 git 2.32의 `share/doc/git-doc/git-log.html`).
- 다음 출시 PR이 가져올 것(`origin/main..origin/dev`, dev는 `0e06c9cf7`): 17커밋, 병합 커밋 1. 제품 경로(`-- src web plugins`)를 건드린 병합 아닌 커밋은 7이고 7 모두 제목이 `(#NNN)`으로 끝난다. 접두는 feat 4, test 2, chore 1로 feat·fix가 아닌 것이 3이다. 제품 경로 밖은 chore·docs·test 9다.
- 임의의 옛 커밋(`06845c686`, 2026-10-29 전 main의 마지막 커밋)을 지난 판으로 두면 `06845c686..afe4b7f86`의 제품 경로 커밋은 42이고 42 모두 `(#NNN)`으로 끝난다. 접두는 feat 39, chore 2, fix 1로 feat·fix가 아닌 것이 2다.
- 경로 거르기와 병합 커밋. 두 범위 모두 기본 단순화와 `--full-history`의 수가 같았다(42와 42, 7과 7). git 문서의 기본 모드는 "prunes some side branches if the end result is the same"이고 "If the commit was a merge, and it was TREESAME to one parent, follow only that parent."다(원문을 받아 대 봤다, 같은 파일). 바꾸고 되돌린 쪽 가지처럼 끝 상태가 같은 가지를 기본 모드가 잘라 내는 모양은 이 이력에 없어 보지 못했다. 그래서 `git log --no-merges --full-history <지난 태그>..<이번 커밋> -- src web plugins`이 안전한 쪽이라는 것은 어림이다. 임시 저장소로 미래의 꼴(출시 병합, 되돌려 합치기, main의 핫픽스)을 짓는 시험은 하지 않았다.
- 저장소 설정은 squash 제목이 `COMMIT_OR_PR_TITLE`이다(손으로 봤다, `gh api repos/{owner}/{repo}`). 커밋이 하나인 PR은 squash 제목이 PR 제목이 아니라 그 커밋 제목일 수 있다(어림, 그 설정 이름에서 읽은 것이다). squash 제목과 PR 제목을 맞대 보지는 않았다.

## 8. 다시 돌리기 `gh run rerun`

- 원문(https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs, 원문을 받아 대 봤다):
  - "Re-runs use the privileges of the actor who initially triggered the workflow, not the privileges of the actor who initiated the re-run. The workflow will also use the same `GITHUB_SHA` (commit SHA) and `GITHUB_REF` (git ref) of the original event that triggered the workflow run."
  - "A workflow run can be re-run a maximum of 50 times." 처음 실행 뒤 30일 안에만 다시 돌릴 수 있다.
  - "When you re-run failed jobs or a specific job, GitHub also re-runs the jobs that depend on them. Jobs that aren't included keep their outputs from the previous attempt, which the newly run jobs can use."
  - 워크플로가 꺼져 있으면 다시 돌릴 수 없다.
- gh 2.98.0의 `gh run rerun`(`pkg/cmd/run/rerun/rerun.go`, 읽었다): 인자 없이 런 전체, `--failed`는 "Rerun only failed jobs, including dependencies", `--job`은 한 작업과 그 의존, `--debug`는 디버그 기록. 런 전체는 REST `POST …/actions/runs/{id}/rerun`, `--failed`는 `…/rerun-failed-jobs`, `--job`은 `…/actions/jobs/{id}/rerun`을 부른다.
- 쟀다(probes/release_mechanics/registry_tags.py의 `rebuild` 갈래). 같은 Dockerfile과 같은 빌드 인자를 증명(출처 증명 `mode=max`, SBOM)과 함께 다시 지어 올리면, 캐시를 다 써도(RUN 단계가 CACHED) 플랫폼 매니페스트 digest는 같았지만 색인 digest는 달랐다. `--no-cache`로 RUN을 다시 돌리면 플랫폼 매니페스트 digest도 달랐다. 두 갈래 모두 2번의 지키는 차례가 "다른 digest 라 거부했다"를 냈다. 색인이 다른 것은 증명 매니페스트가 달라진 것으로 풀이한다(어림. 색인에는 플랫폼 매니페스트와 증명 매니페스트만 든다).
- 둘째 작업만 다시 돌릴 때의 아티팩트(2026-11-14 셀프 리뷰를 반영하며 더했다, 원문을 받아 대 봤다).
  - 실행 번호. "A unique number for each workflow run within a repository. This number does not change if you re-run the workflow run."(`github.run_id`, https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)
  - 받기. `actions/download-artifact`의 README는 받을 실행을 적지 않았을 때를 "If unspecified, the action will download artifacts from the current repo and the current workflow run."로, `run-id`의 기본값을 "Default is ${{ github.run_id }}"로 적는다(https://raw.githubusercontent.com/actions/download-artifact/main/README.md).
  - 올리기. `actions/upload-artifact`의 README는 "Artifacts are retained for 90 days by default."라 적고 `retention-days`로 줄일 수 있게 하며, "Artifacts created by upload-artifact@v4 are immutable."이라 같은 이름을 다시 올리려면 `overwrite: true`를 준다(https://raw.githubusercontent.com/actions/upload-artifact/main/README.md).
  - 그래서 첫째 작업이 올린 아티팩트를 `--failed`로 다시 돈 둘째 작업이 같은 실행에서 받는다고 읽는다(어림. 다시 돌리기 문서는 다시 돌지 않는 작업의 출력만 적고 아티팩트는 적지 않으며, 돌려 보지 않았다).
- 판 내기에 주는 뜻(어림): 번호 태그를 붙인 뒤 공개가 실패한 런을 처음부터 다시 돌리면, 같은 커밋을 다시 지어 해시 태그가 새 digest로 바뀌고 지키는 차례가 번호 태그를 거부해 끝나지 못한다. 짓기·시험·점검·해시 태그 올리기를 한 작업(job)으로, 번호 태그 붙이기와 공개를 그 뒤의 작업으로 나누고 `gh run rerun --failed`(앞 작업의 출력인 digest를 그대로 쓴다)로 다시 돌리면 같은 digest를 보고 이어 간다. 아니면 지키는 차례가 digest 대신 이미지의 커밋 표시(`org.opencontainers.image.revision`)를 견주게 해야 하는데, 그러면 같은 커밋의 다른 digest로 번호 태그를 옮기게 된다.
