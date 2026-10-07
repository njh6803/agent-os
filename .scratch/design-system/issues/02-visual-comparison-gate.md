# 02: 사진 비교 게이트 — 스토리를 고정 이미지의 컨테이너에서 먹의 라이트·다크로 찍고 CI가 바이트까지 비교한다

**What to build:** 개발자가 `packages/ui`를 건드리면 명령 하나로 Storybook 정적 빌드를 호스트에서 짓고, 판을 고정한 Playwright Linux 이미지의 `--network none` 컨테이너에서 패키지의 스토리 전부를 먹의 라이트와 다크로 찍어 커밋한 정답 사진과 `maxDiffPixels: 0`으로 비교한다. 버튼과 아이콘 버튼은 실제 마우스와 키보드의 올림, 누름, 키보드 포커스도 찍는다. 같은 Playwright가 움직임 줄이기에서 도는 표시가 멈추는지, 시스템 다크와 속성 없는 문서·호스트가 먹의 값인지 본다. CI는 같은 이미지를 컨테이너로 쓰는 새 잡에서 설치하고 짓고 비교하며, 필수 검사 `verify`가 그 잡을 `needs`로 모은다. 게이트가 열둘이 된다.

03·04를 막는다. 두 티켓은 자기 스토리의 정답 사진을 이 게이트로 만든다. 헌법(`operations.md`의 게이트)을 바꾸는 티켓이 그 기능의 첫 티켓이 아닌 예외다. ADR 0026 Consequences가 게이트 문서의 갱신을 "그 게이트를 들이는 티켓"에 배정했고, 이 티켓이 뒤의 컴포넌트 티켓을 막으므로 헌법을 바꾸는 티켓이 그 뒤의 티켓보다 먼저 선다는 규약의 뜻은 지킨다(2026-10-06 명세 검토와 to-tickets 주석).

**GitHub 러너에서 사진이 일치하는지는 이 PR의 CI가 처음 본다.** 로컬에서 잴 수 없다. 러너의 사진이 로컬 컨테이너가 만든 정답과 다르면 정답을 러너에 맞춰 다시 만들지 않는다. 멈추고 그 차이(바이트, 다른 픽셀의 수와 자리)를 보고하며 ADR 0026의 이력을 제안한다.

근거는 `.scratch/design-system/spec.md`의 "사진 비교 게이트", "문서와 설정", Testing Decisions의 "사진 비교" 절, 스토리 13·37·42와 그 2026-10-06 명세 검토·to-tickets 주석이다. ADR 0026의 "시각 회귀" 절과 둘째·넷째 2026-10-06 이력이 앞선 결정이다. 선례는 `.scratch/design-system/probes/tokens/visual.mjs`·`visual.spec.mjs`·`visual.config.mjs`와 `probes/visual_docker/`, 상태 색과 움직임과 전환의 측정은 `probes/tokens/measure.mjs`(states, motion, switch)다.

**Blocked by:** 01

**Status:** ready-for-agent

### 이미지와 도구

- [ ] **Playwright Test의 `toHaveScreenshot`, `maxDiffPixels: 0`이다.** 입력은 Storybook 정적 빌드이고 스토리의 `iframe.html`을 route로 파일에서 낸다. 밖으로 나가는 요청은 막고 센다(측정에서 0이었다)
- [ ] **이미지는 `mcr.microsoft.com/playwright:v1.63.0-noble`이고 태그에 digest를 붙여 쓴다**(`<이미지>:<태그>@sha256:<digest>`). digest는 잰 이미지의 것이다(프로브 README의 이미지 ID `sha256:2c1f4e0fd645…`, linux/amd64 매니페스트 `sha256:bc6ab0d6d44f…`). 로컬에 받은 이미지의 ID가 다르면 멈추고 다시 잰다. 이미지의 판은 저장소 락의 Playwright 판과 같고 함께 올린다
- [ ] **정답 사진은 한 벌이고 컨테이너 안에서만 만든다.** 자리는 패키지 안이고 커밋한다. 갱신 명령도 컨테이너에서만 돈다. 호스트에서 정답을 쓰는 길을 두지 않는다

### 찍는 것

- [ ] **패키지의 스토리 전부를 먹의 라이트와 다크로 찍는다.** 01이 태그로 표시한 판정 스토리(Matrix, 음성 사례 등)는 뺀다. 새 스토리를 더하면 저절로 찍힌다. 정답 사진이 없는 스토리는 CI에서 빨갛다(정답이 없으면 실패하는지 이 티켓이 확인한다)
- [ ] **상호작용 컴포넌트는 실제 입력의 올림, 누름, 키보드 포커스를 더 찍는다.** 이 티켓에서는 버튼과 아이콘 버튼이다. 누른 뒤에는 빈 자리를 눌러 순차 탐색의 출발점을 돌린 다음 Tab을 누른다(측정에서 그러지 않자 포커스가 버튼에 오지 않았다). 03·04가 자기 상호작용 컴포넌트를 같은 모양으로 더할 수 있게 둔다
- [ ] **움직임 줄이기.** `reducedMotion: "reduce"`에서 불러오는 중의 도는 표시의 animation-name이 `none`이고, 줄이기가 없으면 `spin`이다. 사진은 Playwright가 움직임을 멈춰 찍으므로 사진으로는 가르지 못한다. 값 모름 진행 막대는 03이 같은 자리에 더한다
- [ ] **시스템 모드와 속성 없음**(스토리 13, 명세 검토 should-fix). 정적 빌드에서 `mode=system`과 `colorScheme` 라이트·다크의 `--bg`가 먹의 그 모드 값이다. 문서 뿌리와 shadow 호스트에서 데코레이터가 단 두 속성을 지우면 두 시스템 모드 모두 먹의 값이다(측정 `measure.mjs`의 switch가 선례다). 쓰임새 토큰의 기대값은 디자인 파일이 아니라 Matrix처럼 형식과 차이로 보거나 같은 빌드의 `data-theme="muk"` 요소에서 읽는다

### 명령과 CI

- [ ] **로컬 명령.** 정적 빌드를 호스트에서 01의 스크립트로 짓고 비교만 `--network none` 컨테이너에서 한다. 컨테이너에 Playwright 패키지를 넣는 방법은 이 티켓이 정한다(프로브는 호스트 설치본을 복사해 bind 마운트했다. 세 패키지에 네이티브 파일이 0개였다). 명령의 이름과 자리(`web/package.json`의 스크립트인지)도 이 티켓이 정한다
- [ ] **CI.** `.github/workflows/ci.yml`에 그 이미지를 컨테이너로 쓰는 잡을 더한다. 잡 안에서 설치하고(네트워크는 설치에만 쓴다) 정적 빌드를 지은 뒤 비교한다. 같은 이미지 안에서 지은 Linux 정적 빌드가 Windows 빌드의 정답을 바이트까지 같게 지났다(측정). `verify`의 `needs`에 넣는다. 빠뜨리면 `verify`가 빨갛다
- [ ] **pre-commit에는 넣지 않는다**(ADR 0026). 로컬에서는 `packages/ui`를 건드렸을 때 직접 친다. e2e와 같은 자리다
- [ ] **실패하면 차이를 볼 수 있다.** CI가 실패 사진과 차이 그림을 아티팩트로 남긴다. 사진을 다시 만들 때는 바뀐 사진을 사람이 보고 PR 본문에 적는다(스토리 37)

### 지침과 문서 (ADR 0026 Consequences의 목록)

- [ ] **`CLAUDE.md`.** 검증 명령 절의 web 괄호에 사진 비교 명령과 언제 치는지를 적고, 게이트 줄을 "열하나"에서 "열둘"로, CI만 도는 것을 e2e와 사진 비교 둘로 고친다. 손으로 치는 명령의 수와 pre-commit이 돌리는 수가 여전히 맞는지 다시 센다
- [ ] **헌법.** `docs/constitution/operations.md`의 두 자동 검사의 차이(CI에만 있는 것)와 CI 잡 문장(잡 셋 → 넷, `verify`가 모으는 잡)을 고치고 `docs/constitution/README.md`의 버전을 올린다. `docs/constitution/tech.md`의 원격·CI 행(잡 셋)과 웹 행의 시각 회귀 문장("그 잡을 CI에 하나 더한다")을 지난 사실로 고친다(명세 검토 nit). `ci.yml`의 머리 주석(잡 셋, CI에만 있는 것)도 고친다
- [ ] **게이트 훅.** `tools/hook_bash_gate_pipe.py`의 게이트 목록에 사진 비교 명령을 더한다. 파이프 뒤 `$?`가 판정을 속이는 것은 이 명령도 같다. `tests/tools/`의 그 훅 테스트와 `tools/hook_payloads.toml`에 발동할 입력과 발동하지 말아야 할 입력을 하나씩 더하고 `tools/run_hooks.py`로 실제 실행을 확인한다(`.claude/rules/tools.md`)
- [ ] **보호 설정(`tools/protection.json`)은 바뀌지 않는다.** 필수 검사는 `verify` 하나 그대로다
- [ ] **잔존 grep.** `게이트는 열하나`, `열하나(린트는`, `잡 셋`, `세 잡`, `CI만 돈다`, `CI에만 있다`, `남은 하나인 e2e`를 저장소 전체에서 찾는다. 기록(일지, ADR의 지난 이력, done인 기능의 `.scratch/`, 대기열의 닫힌 행)과 이 기능의 `.scratch/design-system/`, `.claude/worktrees/`는 제외한다. 글자 grep은 같은 뜻의 다른 말을 놓치므로 걸린 것 둘레도 읽는다
- [ ] **01이 정한 앱 스토리의 자리대로 둔다.** 앱의 Storybook이 따로 서는 결정이면 이 명령이 그 정적 빌드도 찍을 수 있는 모양인지 보고, 앱의 스토리가 아직 없으므로 지금 찍는다고 적지 않는다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이고 사진 비교 명령도 로컬에서 초록이다. `ci.yml`만 바꾼 PR도 claude-review는 돈다(`operations.md` 리뷰 파이프라인). 판정은 코멘트가 실제로 있는가다

### 이 티켓이 정할 것

PR에서 사용자가 이름을 본다. 결정과 근거는 일지에 적고, 여기 "이 티켓이 정한 것" 절을 더한다.

1. 이미지의 digest 값(잰 이미지의 것)
2. 사진 비교 명령의 이름과 자리, 정답 사진의 자리와 이름
3. 판정 스토리를 사진에서 빼는 방법(01의 태그를 읽는 모양)
4. 로컬 비교가 컨테이너에 Playwright 패키지를 넣는 방법
5. CI 잡의 이름과 실패 아티팩트의 모양

### 01이 넘긴 것 (2026-10-07)

- 정적 빌드의 스크립트는 `pnpm -C web/packages/ui run build-storybook`이고 산출물은 `web/packages/ui/storybook-static/`이다(뿌리 `.gitignore`에 앵커를 붙여 든다).
- 판정 스토리의 태그는 `judgment`, 그 가운데 심은 것을 그리는 음성 사례는 `planted`도 단다. 정적 빌드의 `index.json` 항목마다 `tags`에 그대로 실린다(01이 지어 본 빌드에서 봤다).
- 앱 스토리의 자리는 앱마다의 Storybook이다(ADR 0026의 2026-10-07 이력). 사진 비교 명령이 정적 빌드의 자리를 받게 두면 앱의 정적 빌드도 같은 명령으로 찍는다.
- 다크 스토리는 globals `mode: "dark"`로 둔다(`Button`의 `PrimaryDark` 등). 포커스 링의 스토리 둘은 globals `theme: "gongmun"`이다(먹은 `focus`와 `accent`가 같은 색이다).
