# main이 움직이면 CI가 판 번호를 계산해 이미지와 릴리스를 낸다 (release-image 티켓 11)

브랜치 `feature/11-ci-publishes-release-from-main`, 워크트리 `.claude/worktrees/11-ci-publishes-release-from-main`. 모델 Sonnet 5.5 / high. 기준은 `origin/dev` `11e41115a`다. release-image의 마지막 티켓이다. 이 일지는 커밋 전에 썼고 PR과 병합 절은 병합 세션(같은 세션)이 아래에 더한다.

## 사용자 프롬프트 원문

> 사용자: /implement .scratch/release-image/issues/11-ci-publishes-release-from-main.md
>
> 다음 작업: .scratch/release-image/issues/11-ci-publishes-release-from-main.md. main이 움직이면 CI가 판 번호를 계산해 이미지와 릴리스를 낸다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막인 11-ci-publishes-release-from-main)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 브랜치: feature/11-ci-publishes-release-from-main
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-16-2048-deploy-guide-walks-operator-through-standalone.md의 "이 PR이 끝난 뒤"
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

사용자의 다른 말은 없었다.

## 시작할 때 한 것

- `tidy-checkouts`로 주 체크아웃을 `11e41115a`로 당기고 병합된 `worktree-10-…` 브랜치 하나를 지웠다. 나머지 워크트리는 도구가 남긴 이유대로 두었다.
- `EnterWorktree`(name `11-ci-publishes-release-from-main`)로 들어와 브랜치를 `feature/11-ci-publishes-release-from-main`으로 바꿨다.

## 한 것

- `.github/workflows/release.yml`(새 파일): 판 내기 워크플로. 잡 둘(`build`, `publish`), 환경 `release`, 동시 실행 묶음 `release`(취소하지 않음), 기본 토큰은 `contents: read`. 단계마다 이름을 붙였다. 이 이름이 `operations.md`의 실패 단계 표가 대는 이름이다.
- `deploy/images/docker-bake.hcl`(새 파일): 이미지 넷을 한 번에 짓는 목록. 이미지마다 다른 gha 캐시 범위를 둔다. 시험용 짓기와 올리는 짓기가 같은 파일을 쓰고 변수 값(`NAMESPACE`, `TAG`)만 다르다.
- `tools/release_ci.py`(새 파일)와 `tests/tools/test_release_ci.py`(34개): 워크플로가 부르는 판정을 파이썬 순수 함수로 떼어 시험했다. `image-id`(저장 파일의 설정 해시), `platform-manifest`와 `manifest-config`(올린 색인의 linux/amd64 매니페스트와 그 `config.digest`), `judge`(번호 태그 판정), `precheck`(사전 확인), `verify-files`(받은 아티팩트 대조).
- `deploy/release.toml`(`candidate_for = "0.1.0"`), `docs/release-notes/features/release-image.md`(278자 한 단락), `docs/release-notes/intro/0.1.0.md`, 기능 계획의 `**끝:** 2026-11-16`.
- 규약 문서: `merge.md`에 "판 내기를 기다린다" 절(출시 PR과 핫픽스 표 줄, 출시 PR 병합 뒤 순서 포함), `operations.md`에 "판이 나는 차례와 실패한 판을 다시 돌리는 절차" 절, `tech.md`에 레지스트리·프록시·점검 행, 헌법 판 3.0.106 → 3.1.0(절 추가는 minor. `sibling_overlap`이 형제가 쓴 가장 높은 판을 3.0.106으로 보였다).
- `release_mechanics` 프로브 고침과 다시 돌리기는 서브에이전트가 했다(아래 "프로브").

## 결정

- 번호 도구(`tools/release.py`)는 쪼개지 않았다. 워크플로에서 쓸 판정은 `tools/release_ci.py`로 따로 두어 `release.py`를 키우지 않았다. `judge_number_tag`는 `release_ci.py`의 `judge` 하위 명령이 부르므로 지우지 않는다.
- 시험한 이미지와 올린 이미지의 대조는 이미지 설정 파일의 해시로 한다. 시험한 쪽은 `docker save` 파일의 `manifest.json`이 가리키는 `Config` 멤버의 sha256이고(옛 저장 방식의 `<해시>.json`과 containerd 저장 방식의 `blobs/sha256/<해시>`를 모두 읽는다), 올린 쪽은 올린 색인의 linux/amd64 매니페스트의 `config.digest`다. 설정과 레이어를 함께 가리키는 값이라 `ENV`만 다른 이미지도 가른다. 레이어 `diff_ids`만 견주는 안은 받지 않았다.
- 점검 도구는 digest로 고정한 Grype 0.121.3과 Syft 1.57.1의 공식 컨테이너다. Grype DB는 실행마다 새로 받는다. 묵은 DB는 새 취약점을 놓치고, 풀어 둔 크기가 3.2GiB라 캐시에 두면 저장소 캐시 한도(10GB)를 잡아먹는다.
- 환경 `release`, 비밀 값 `DOCKERHUB_TOKEN`·`RELEASE_GH_TOKEN`, 변수 `DOCKERHUB_NAMESPACE`가 이 티켓이 정한 이름이다.
- 액션 고정: 10개를 2026-11-16에 다시 골라 커밋 해시로 고정했다. `gh api`로 각 `v` 태그가 가리키는 커밋이 워크플로의 해시와 같은지 대 봤다(10개 모두 같다).
- 제한 시간은 어림이다(`build` 90분, `publish` 30분). 첫 판의 실제 시간으로 고친다.
- 워크플로의 감사: `uv run zizmor --offline --strict-collection --config .github/zizmor.yml .github`가 findings 0이었다. 설정 없이(`--no-config`) 돌려도 release.yml은 0이었다.

## 프로브

서브에이전트가 `release_mechanics` 프로브의 지적 셋과 `scan_tools.py` 586행의 갈래를 고치고 다시 돌렸다. 보고에서 옮긴다.

- `scan_tools.py`: 양성 대조가 거르지 않은 JSON에 해당 심각도의 고칠 수 있는 행이 1건 이상일 때만 측정으로 센다. `volumes_to_remove(trivy_cache, grype_cache)`가 지울 볼륨 목록을 정한다.
- `registry_tags.py`: 캐시 표지가 `RUN` 단계의 `CACHED`만 본다. 증명을 켠 `--load`의 실패 표지는 `docker exporter does not currently support`가 로그에 있을 때만, 성공 표지는 `generating sbom`이 있을 때만 측정으로 센다.
- 다시 돌린 결과: `registry_tags.py` 측정 21회차, 측정 아님 0회차, 종료 0. `scan_tools.py` 측정 35회차, 측정 아님 0회차, 종료 0. 명세 문장과 어긋난 결과는 없었다. DB가 사흘 뒤 것이라 건수가 몇 개 달랐다(README 3번에 적었다).
- 손으로 반박한 입력: `volumes_to_remove`에 다른 도구의 기본 이름과 `IN_VOLUME`을 인자로 준 입력(고치기 전에는 그 볼륨까지 지울 목록에 들었고 지금은 빠진다).
- 번호 태그 판정의 시험 입력(`tests/tools/test_release.py`의 `EXISTING`)은 로컬 `registry:3`에서 다시 잰 `docker buildx imagetools inspect` 출력과 맞췄다(증명 매니페스트 항목과 항목 사이 빈 줄을 더했다). 맨 앞 칸 `Digest:`가 첫 줄이라는 것은 실제와 같았다. Docker Hub의 인증된 조회 출력은 보지 못했다(로그인 금지).
- 이 PR이 끝난 뒤에도 남는 어림: `plain_inspect.py`는 커밋하지 않은 스크래치였고 출력 꼴은 README에 "손으로 봤다"로만 적혔다.
- GitHub 러너에서의 시험(2026-11-16, 실행 43879846300, 이 저장소의 임시 브랜치 `probe/release-image-ci`에서 스크래치 워크플로 `release-probe.yml`을 돌렸다. 스크래치 파일은 세션 스크래치패드에 있고 커밋하지 않았다). 러너의 저장 방식은 `Storage Driver: overlay2`다(이 PC도 `docker info`로 다시 보니 `overlay2`다. containerd 저장 방식의 `docker save`는 이 PC에서도 러너에서도 본 적이 없고, 그 꼴은 `tests/tools/test_release_ci.py`가 만들어 넣은 입력으로만 시험한다). 증명을 끄고 `--load`한 `portal` 이미지의 `docker save` 설정 해시와 `docker image inspect`의 Id가 `sha256:7028460d…8135`로 같았고, 증명(`provenance: mode=max`, `sbom: true`)을 켜고 로컬 레지스트리 `registry:3`에 올린 색인의 linux/amd64 매니페스트(`sha256:6f07162c…04b0`) `config.digest`가 같은 값이어서 `RESULT same`이었다. 올리는 짓기에서 앞 단계가 `CACHED`(#9~#25)로 찍혔다. 번호 태그 판정 단계는 `docker buildx imagetools inspect <없는 태그>`가 종료 1로 끝났다. Docker Hub가 아니라 로컬 레지스트리이므로 Docker Hub의 인증 조회 출력과 로그인 없는 받기는 첫 판의 몫으로 남는다. 시험 브랜치는 이 일지를 쓴 뒤 지웠다.

## 단독 e2e와 카나리아

- `deploy/`를 건드렸으므로 이 PC에서 단독 e2e를 쳤다(`pnpm -C web/packages/e2e-standalone exec playwright test`, 환경 변수 없이 이미지를 로컬에서 지었다). 12 passed, 1.5분. 이 PC의 Docker는 Engine 29.9.2이고 이미지 저장 방식은 `overlay2`다(`docker info`).
- `merge.md`를 바꿨으므로 카나리아 명세 `.scratch/release-image/probes/canary/next_session_release_wait.toml`을 새로 쓰고 돌렸다. 실험군 3/3 통과, 대조군(옛 판 `11e41115a`) 1/1 "없음". 통과 4, "없음" 섞임 0.

## 사람 몫 여섯(사용자에게 보인 화면)

명세 "사람 몫"의 여섯이다. 이것이 없으면 첫 판 내기가 실패한다. 이 PR을 병합한 세션이 출시 PR을 병합하기 전에 끝났는지 묻는다.

1. Docker Hub에 이 제품의 이름으로 무료 개인 계정을 만들고 2단계 인증을 켠다.
2. 그 계정의 접근 토큰을 읽기·쓰기 권한(지우기 없음)으로 발급한다.
3. GitHub 세분 토큰을 만든다. 아래 주소를 열면 이름과 권한(Contents 쓰기, Workflows 쓰기)이 채워진다. 저장소는 "Only select repositories"에서 `njh6803/agent-os` 하나만 고르고, 만료는 직접 고른다. `https://github.com/settings/personal-access-tokens/new?name=agent-os-release&description=agent-os+release+workflow&target_name=njh6803&contents=write&workflows=write`
4. 저장소 설정의 Environments에서 환경 `release`를 만들고 Deployment branches를 `main` 하나로 좁힌다. 그 환경에 비밀 값 `DOCKERHUB_TOKEN`(2의 접근 토큰)과 `RELEASE_GH_TOKEN`(3의 세분 토큰), 변수 `DOCKERHUB_NAMESPACE`(1의 계정 이름)를 넣는다.
5. 저장소 설정에서 squash 병합의 기본 커밋 제목을 PR 제목(`PR_TITLE`)으로 바꾼다. 세션이 하지 않는다.
6. Docker Hub 계정 아래에 공개 저장소 넷 `serve`, `admin`, `widget`, `portal`을 미리 만든다.

## 하지 못했거나 어림인 것

- 워크플로는 아직 한 번도 돌지 않았다. 판정 도구의 시험(34개)과 zizmor만 지났다. 첫 실행은 출시 PR의 병합이다.
- 러너 이미지 저장소(overlay2)에서 `docker save`의 설정 해시와 올린 매니페스트의 `config.digest`가 같은지, gha 캐시를 두 번째 짓기가 쓰는지는 임시 브랜치 `probe/release-image-ci`의 시험 워크플로(실행 43879846300, 1분 55초, 성공)를 돌려 `gh run view 43879846300 --log`의 줄을 손으로 봤다(커밋한 프로브가 아니다). 결과는 위 "프로브"의 마지막 항목이다. 이 시험에 든 것은 `portal` 이미지 하나이고 본 워크플로 전체는 아니다.
- 초안이 git 태그를 만들지 않는다는 것, 둘째 잡만 다시 돌렸을 때 첫 회차의 아티팩트를 받는다는 것은 명세의 어림 그대로다. 대조 셋(`초안 직후 태그 대조`, `아티팩트 대조`, 지난 판의 공개 릴리스 확인)이 틀렸을 때 실패로 드러나게 한다.

## 회고

후보 다섯: 승인 1(회차로 센 것), 기각 4, 넘김 0. 판정은 `retro` 4단계의 조건으로 에이전트가 했다.

- **옛 절차가 `pr-merge/SKILL.md`에 남았다 — 승인(회차로 센 것).** `merge.md`의 출시 PR·핫픽스 병합 뒤 절차를 바꾸면서 같은 절차를 되풀이한 `pr-merge/SKILL.md` 4단계를 맞추지 않았고, 표준 축 셀프 리뷰가 Major로 잡았다. `CLAUDE.md` 작업 규약 4(옛 표현을 저장소 전체에서 grep해 잔존 0)를 어긴 사건이라 `0420`(옛 표현 잔존)의 14회차로 센다. `0420`의 승인 줄에 회차와 이 일지를 더했다(13회차에서 14회차). 처방은 `0420`이 이미 5회차에 계기 훅이나 검사로 고르기로 했고 회차 5 이상이므로 chore 배치의 계기에 이미 서 있다.
- **일지에 "이 PC는 containerd 저장소"라고 확인 없이 썼다 — 기각.** 이미 있는 훅이 일지 편집마다 근거의 종류를 밝히라고 알린다(`hook_journal_evidence`). 이번에는 리뷰 서브에이전트가 `docker info`와 대 보고 잡았다. 알림이 있는데도 놓친 사건이라 같은 꼴이 반복되면 `hook_journal_evidence`의 문구를 고쳐야 한다. 지금은 사건 하나.
- **`release.yml` 머리 주석의 "ci.yml과 같다"가 거짓이었다 — 기각.** `code-review`의 주장 검증 목록(닫힌 주장, 인용)이 겨냥한 사건이고 리뷰가 제 몫을 해 잡았다(`retro` 4단계, 리뷰가 잡도록 둔 기준을 어긴 사건은 셈에서 뺀다).
- **Bash 훅이 `python3` 직접 호출과 62줄 heredoc을 막았다 — 기각.** 이미 있는 훅이 그 자리에서 막았다.
- **`PreToolUse` 한국어 점검 훅이 중간 문장 영어를 알렸다 — 기각.** 이미 있는 훅이 알렸고 다음 문장부터 고쳤다.

## 다음

- 이 PR을 병합한 세션은 출시 PR을 열기 전에 사용자에게 위 사람 몫 여섯이 끝났는지 묻는다(`merge.md` "출시 PR").
- 출시 PR을 병합한 세션은 `merge.md`의 "판 내기를 기다린다"대로 첫 판 `0.1.0-rc.1`을 끝까지 보고 아래를 일지에 적는다. 잡마다 걸린 시간, 초안 단계에서 git 태그가 없었는지, 로그인 없이 이미지가 받아지는지, 압축 크기, 러너에서 시험한 이미지와 올린 이미지의 설정 해시가 같았는지(`시험한 이미지와 올린 이미지 대조` 단계), gha 캐시가 두 번째 짓기에서 맞았는지. 이 PC에서 받은 이미지와 묶음으로 단독 e2e를 실제 모델 묶음까지 켜서 돌린다. `timeout-minutes`(`release.yml` 90·30, `ci.yml`의 `e2e-standalone` 45)를 잰 값으로 맞춘다.
- rag-engine에 줄 지시문은 첫 판이 실제로 돈 뒤 그 세션이 사용자에게 낸다(기능 계획 본문과 명세 "rag-engine에 줄 지시문"). 대기열 `rag-engine-port-by-hand`에 회차를 더한다.

## 셀프 리뷰 (이어받은 세션)

범위: base `11e41115a`, 수정 열한 개와 미추적 아홉 묶음, 커밋 0개. 표준 축(Sonnet·high)과 명세 축(본 세션 모델)을 따로 돌렸다. Critical 0. 아래는 두 보고를 코드와 대 본 판정이다.

**고친 것(Major)**
- `.claude/skills/pr-merge/SKILL.md` 4단계가 옛 절차(출시 PR은 되돌려 합치기까지, 보고에 판 없음)였다. 코드로 읽어 맞았다. 핫픽스와 출시 PR 줄에 판 내기를 기다리는 단계를 더했다.
- `merge.md` "판 내기를 기다린다"에 중간에서 들어오는 갈래가 비었다(두 축이 각자 냈다). 일지에 `판 내기: 병합 커밋 <해시>` 줄을 남기게 하고(기록), 끊긴 뒤 이어받는 길(이어받기)을 더했다. 되돌려 합치기를 끝낸 세션도 그 줄을 먼저 본다. 병합 커밋 해시는 일지에서 읽으므로 PR 번호를 몰라도 이어 간다. 결과 가르기에 `timed_out`과 "그 밖의 값"을 더하고, 실패 단계를 읽는 `jq`를 `success`·`skipped`가 아닌 것으로 넓혔다. 밀려 취소된 뒤에는 나중 실행의 `headSha`로 일지 줄을 고쳐 1~3을 다시 한다. 30초 간격은 포그라운드 `sleep`이 막혀 `Monitor`의 `until` 루프로 적었다.
- `operations.md` 단계 표에 `release.yml`의 단계 이름이 빠져 있었다(`체크아웃`, `Docker Hub 로그인`, `앞 실행의 초안 지우기`, 준비 단계, `노트와 배포 파일 묶음`, `정리`). 줄을 더하고 제한 시간 초과 줄을 더했다. 명세가 "어림. 돌려 보지 않았다"로 적은 아티팩트 대조 길이 표에서는 사실로 적혀 있어 어림 표시를 달았다. 제한 시간 초과 때 단계가 어떻게 읽히는지는 확인하지 못했으므로 `cancelled`나 `failure` 둘 다를 고르게 쓰고 어림이라 적었다.

**고친 것(Minor)**
- `release.yml`: 머리 주석의 "체크아웃의 판은 ci.yml과 같다"는 거짓이었다(`ci.yml`은 `checkout@v4`, `setup-node@v7`, `cache@v4` 태그). 사실대로 고쳤다(`grep`으로 `ci.yml`을 대 봤다). "세분 토큰은 릴리스 단계만 받는다" 목록에 `사전 확인`과 `초안 직후 태그 대조`가 빠져 있어 더했다. 출시 후보를 `prerelease=true`로 표시하던 것은 명세·ADR에 근거가 없어(`grep` 0건) 지웠다.
- `사전 확인`의 `done < <(gh api …)`는 `gh`가 실패해도 단계가 실패하지 않았다. 파일로 받은 뒤 읽게 바꿔 `gh`의 실패가 단계의 실패가 된다. `점검`의 `echo "$image=$(… image-id …)"`도 같은 모양이라 변수에 먼저 받게 했다.
- `정리`가 `tagcheck.outcome == 'failure'`를 봐서 `gh api`의 일시 오류에도 새로 만든 초안을 지웠다. `초안 직후 태그 대조`가 태그를 찾았을 때만 `found=true` 출력을 쓰고 `정리`는 그것을 보게 했다.
- `tools/release_ci.py`: `--sha ""`가 `precheck`를 `done`으로 통과시켰고, `verify-files`는 아티팩트와 인자의 해시가 모두 없으면 `None == None`으로 지났다(`uv run python`으로 두 입력을 직접 넣어 본 서브에이전트의 보고를 코드로 다시 읽어 확인했다). `--sha` 형식 검사와 "첫째 잡이 해시를 넘기지 않았다" 실패를 더했다. 시험 여섯을 더했다(하위 명령 `image-id`, `platform-manifest`, `manifest-config`의 `main` 길과 위 두 입력). 고친 뒤에 시험을 써서 빨강을 직접 보지는 못했다(손으로 변이를 넣어 보지 않았다).
- 일지의 "이 PC는 containerd 저장소" 두 문장이 틀렸다. `docker info --format '{{.Driver}}'`가 `overlay2`를 낸다(이 PC에서 쳤다). 일지와 `release_ci.py` 독스트링을 고쳤다. containerd 방식의 실제 `docker save`는 이 PC에서도 러너에서도 본 적이 없다.
- `tools/release.py` 독스트링의 "워크플로가 부를 명령줄은 … 티켓이 더한다"를 현재형으로 고쳤다(`release_ci.py judge`).
- 카나리아 명세의 "네 카나리아"를 셋으로, 취소 갈래의 기대 문장을 새 글에 맞게 고쳐 다시 돌렸다. 통과 4(실험군 3/3, 대조군 1/1 "없음"), 섞임 0(`tools/canary.py`가 단언한 결과). 그 뒤 `merge.md`에서 제한 시간 문장 하나만 더 고쳤고 기대 문장과는 겹치지 않아 다시 돌리지 않았다. 프로브 색인과 루트 `README.md`의 `deploy/` 줄에 새 파일을 올렸다.

**남긴 것**
- `release_ci.py`의 `_is_object`, `_is_list`, `_DIGEST`가 `release.py`와 같은 모양이다(Duplicated Code, Nit). 두 도구를 하나로 합치는 일은 이 티켓의 몫이 아니다.
- 워크플로 bash의 자동 시험은 없다(명세 Testing Decisions 넷째가 허용). 첫 실행을 지켜보는 세션이 맡는다(아래 "다음").
- `RELEASE_GH_TOKEN`이 조회 단계에도 넘어가는 것은 초안 조회에 필요해서다. 명세의 단계 목록을 넓혀 읽었으므로 위 주석에서 목록을 고쳤다.

## 앞 세션의 인계 (이 세션이 이어받았다)

이 세션은 컨텍스트가 문턱을 넘어 `셀프 리뷰 직전`에서 인계한다. 제목은 인계 전 `feature/11-ci-publishes-release-from-main`이었고 인계하며 `feature/11-ci-publishes-release-from-main (인계함)`으로 바꾼다. 커밋은 하지 않았다. 새 세션이 이 일지를 이어 쓰고 커밋한다.

- 남은 일: 티켓 `Status:`를 `done`으로 바꾸고 `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 만든다. `/code-review`(고정점 `origin/dev`)로 셀프 리뷰하고 Critical·Major를 고친다. 일지 끝 `## 다음`을 마무리하고 `retro`(단계를 닫는 훅이 요구했다)를 돈다. 전체 검증(`uv run ruff check . && uv run ruff format --check .`, `uv run python tools/run_checks.py`를 Bash `timeout` 600000으로)을 돌린 뒤 `tools/sibling_overlap.py`와 `git branch --show-current`를 보고 커밋한다. 티켓의 "검증 명령이 모두 초록이다"는 그때 체크한다.
- 사람 몫 여섯: 위 화면을 사용자에게 보인 다음에야 티켓의 "사람 몫" 체크박스를 체크한다. 이 PR의 마지막 메시지에 같은 화면을 한 번 더 보인다.
- 병합은 `merge.md`의 "워크트리에서 병합할 때"를 따른다. 이 PR을 병합한 세션이 출시 PR을 열기 전에 사용자에게 사람 몫 여섯이 끝났는지 묻는다.
- 시험용 임시 브랜치 `probe/release-image-ci`는 원격에서 지웠다.

open-session을 부른다 2026-11-16T13:55Z
