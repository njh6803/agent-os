# pilot-portal 프로브

명세·ADR이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/pilot-portal/spec.md`와 ADR 0050의 2026-11-09 이력이다.

## 돌리는 법

저장소 루트에서 돈다(Windows, Git Bash). `web/node_modules`가 있어야 한다(`pnpm -C web install --frozen-lockfile`). 위젯 폴더(`web/apps/widget/`) 안에 임시 폴더 `.probe-node-ts-*`를 만들어 거기서 node를 띄우고 끝나면 지운다. `--group`으로 묶음 하나만 돌 수 있고(`strip`, `tsc`, `css`, `fonts`, `next`, `pagescript`. 여러 번 줄 수 있다), `--raw <경로>`를 주면 회차마다의 명령·종료 코드·stdout·stderr를 JSON으로 남긴다(세션 스크래치패드에 두고 커밋하지 않는다).

```sh
uv run python .scratch/pilot-portal/probes/node_ts_workspace.py
uv run python .scratch/pilot-portal/probes/node_ts_workspace.py --group next --raw <스크래치패드>/node_ts_raw.json
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `node_ts_workspace.py` | node가 `.ts`를 빌드 없이 돌릴 때 워크스페이스 패키지와 디자인 시스템을 그대로 읽을 수 있는지를 소비 지점까지. 타입 벗기기 여덟 회차(패키지 이름의 서브패스 export, `--preserve-symlinks` 갈래, `node_modules` 안의 `.ts` 대조, `@agent-os/ui`의 루트 진입점과 `.tsx` 파일과 `@agent-os/api-client`의 거부 대조, `themes.ts`와 `clients.ts`의 상대 경로 읽기), tsc `--noEmit` 여섯 회차(`nodenext`·`bundler` 각 깨끗한 판과 `TS2322` 변이와 확장자 없는 상대 import), 토큰 CSS 짓기 두 회차(CLI를 바로 돌린 것과 node가 자식으로 띄워 메모리에 읽고 파일을 지운 것. 지시문 잔존, 화면 그림이 쓰는 변수의 선언, 레이어와 클래스 선택자 수, 크기와 시간), 글꼴 두 회차(woff2 수와 크기, `@font-face` 수, 패키지 안에서 `@agent-os/ui/fonts.css` 자기 참조), Next 설정 읽기 네 회차(기본 길을 설정 파일 폴더에서, 다른 작업 디렉터리에서 빠진 `local.ts`와 미끼 `local.ts`, node 네이티브 길), 페이지 스크립트 타입 벗기기 두 회차(`node:module`의 `stripTypeScriptTypes`로 벗긴 스크립트가 돌고 타입 주석이 남지 않는지, `enum`이 거부되는지). 표지는 독스트링 | `spec.md`의 "앱과 패키지", "띄우기와 타입 검사", "모양", "페이지" 결정과 Testing Decisions. ADR 0050의 2026-11-09 이력 | 위 명령(`--group`은 `strip`, `tsc`, `css`, `fonts`, `next`, `pagescript`). 회차마다 node 한 번이고 tsc 여섯 번이 각 1초 안팎이다. 전체 시간은 재지 않았다 | node 24.19.0(`process.features.typescript`가 `strip`), pnpm 11.24.0, typescript 5.9.3, next 16.3.6, smol-toml 1.9.1, @tailwindcss/cli 4.3.3, tailwindcss 4.3.3. Windows 10(이 PC)만. 2026-11-09와 2026-11-10 |
| `e2e_stack_mutations.toml` | 티켓 02의 `@agent-os/e2e-stack` 단위 시험(트레이스 읽기, 환경 변수 넘기기, 실행 주체의 이름) 가운데 코드와 함께 써서 빨강을 본 적 없는 것을 겨누는 변이 표 여섯. 이 표가 재는 것이 아니고 손으로 본 것: 위젯 e2e의 트레이스 주체 사례는 넘기는 길을 더하기 전에 `playwright test` 출력에서 빨강을 봤다(준비가 `AGENT_OS_E2E_TRACES`를 넘기지 않았다는 오류) | 티켓 02 | `uv run python tools/mutate.py .scratch/pilot-portal/probes/e2e_stack_mutations.toml`. 패키지의 `traces.ts`, `env.ts`, `token.ts`를 고칠 때 | 2026-11-10, 변이 여섯 모두 기대대로 빨강 |

## 결과

2026-11-09에 네 번, 2026-11-10에 한 번 돌렸다. 첫 실행은 16회차 가운데 15회차가 측정이었고 `next_config_legacy`가 측정 아님(종료 코드 1)이었다. 그 회차는 작업 디렉터리를 임시 폴더로 둔 채 Next의 기본 길을 돌렸고 `Cannot find module './local.ts'`로 끝났다. 원인을 가르는 회차 둘을 더하고 양성 회차의 작업 디렉터리를 설정 파일의 폴더로 옮긴 둘째 실행은 18회차 모두 측정, 측정 아님 0, 종료 코드 0이었다. 명세를 쓰며 페이지 스크립트 묶음(아래 "페이지 스크립트") 두 회차를 더해 그 묶음만 돌렸고(셋째 실행), 이어 여섯 묶음 스무 회차 전체를 한 번 더 돌렸다(넷째 실행. 스무 회차 모두 측정, 측정 아님 0, 종료 코드 0). 2026-11-10에는 셀프 리뷰를 받아 회차 넷(`tsc_nodenext_extensionless`, `tsc_bundler_extensionless`, `theme_css_build_child`, `fonts_css_self_reference`)을 더하고 스물네 회차 전체를 돌렸다(다섯째 실행. 스물네 회차 모두 측정, 측정 아님 0, 종료 코드 0). 같은 날 PR #504의 CodeRabbit을 받아 표지 둘을 좁혔다. `strip_api_client_root`는 오류 코드에 더해 찾지 못한 지정자에 `packages/api-client/src/clients`가 있어야 표지이고(패키지 자체가 없어도 같은 코드가 나므로), `theme_css_build_child`는 바이트 수 대신 sha256이 바로 돌린 회차와 같아야 표지다(바이트 수가 같아도 내용이 다를 수 있으므로). 스물네 회차 전체를 다시 돌렸다(여섯째 실행. 스물네 회차 모두 측정, 측정 아님 0, 종료 코드 0. 좁힌 표지 둘 다 섰다). 실행마다 겹치는 회차의 판정은 같았다. 아래 값은 그 회차를 처음 측정으로 돌린 실행의 것이고, 시간은 프로브가 잰 초이며 실행마다 다른 값은 괄호에 적는다.

### 타입 벗기기 — `strip_*`

| 회차 | 입력 | 결과 |
|---|---|---|
| `strip_subpath` | `@agent-os/ui/contrast`를 패키지 이름으로 | 읽힘. `MODES`가 `light`·`dark`. `import.meta.resolve`와 `require.resolve` 모두 `web/packages/ui/src/styles/contrast.ts`(실제 경로, `node_modules` 밖) |
| `strip_preserve_symlinks` | 같은 입구를 `--preserve-symlinks`로 | 거부 `ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING`. 문구의 경로가 `web/apps/widget/node_modules/@agent-os/ui/src/styles/contrast.ts` |
| `strip_inside_node_modules` | 임시 `node_modules/probe-ts-pkg/index.ts` | 거부. 같은 코드 |
| `strip_root_index` | `@agent-os/ui`(`.` 진입점 `src/index.ts`) | 거부 `ERR_MODULE_NOT_FOUND`. 찾지 못한 지정자는 `web/packages/ui/src/components/atoms/Button`(확장자 없는 재내보냄) |
| `strip_tsx_file` | `components/atoms/Button.tsx`를 확장자까지 적어 | 거부 `ERR_UNKNOWN_FILE_EXTENSION`(`.tsx`) |
| `strip_themes_file` | `web/packages/ui/src/themes.ts`를 상대 경로로 | 읽힘. `THEMES` 넷(`guncheong`, `nokcheong`, `jacho`, `jjokbit`), `DEFAULT_THEME` `nokcheong`, `MODES` 둘, `DENSITIES` 둘 |
| `strip_package_dep` | `web/packages/api-client/src/clients.ts`를 상대 경로로 | 읽힘. `openapi-fetch`는 `web/node_modules/.pnpm/openapi-fetch@0.17.0/node_modules/openapi-fetch/dist/index.cjs`에서 풀림 |
| `strip_api_client_root` | `@agent-os/api-client`를 패키지 이름으로 | 거부 `ERR_MODULE_NOT_FOUND`. 지정자 `web/packages/api-client/src/clients`(확장자 없음) |

- **pnpm 링크를 실제 경로로 풀어 워크스페이스 패키지의 `.ts`를 벗긴다.** 양성 대조는 `strip_inside_node_modules`(`node_modules` 아래 실제 파일은 거부된다)이고, 갈래는 `strip_preserve_symlinks`(링크를 풀지 않으면 같은 파일이 `node_modules` 경로로 보여 거부된다)다. 그래서 읽히는 까닭은 node가 링크를 따라간 실제 경로가 `node_modules` 밖이기 때문이지, 워크스페이스 패키지를 따로 봐주기 때문이 아니다. 질문 페이지를 띄우는 명령에 `--preserve-symlinks`를 넣으면 안 된다.
- **ADR 0050의 걸림돌 하나(`@agent-os/ui`의 루트 진입점)는 `.tsx` 앞에서 막힌다.** `src/index.ts`의 재내보냄 지정자에 확장자가 없어 `ERR_MODULE_NOT_FOUND`가 먼저 난다. 확장자를 적어도 `.tsx`는 `ERR_UNKNOWN_FILE_EXTENSION`이다(`strip_tsx_file`). 그러므로 node가 읽을 수 있는 것은 `.tsx`를 거치지 않는 파일을 서브패스 export로 연 것뿐이고, `./contrast`가 그 모양이다. `themes.ts`는 상대 경로로는 읽혔고(`strip_themes_file`) 서브패스 export로 열었을 때의 길은 `strip_subpath`가 지나는 길과 같다(export 지도를 지나 실제 경로로 푼다). 서브패스 export 자체의 측정은 `./contrast`로 했고 `./themes`는 아직 없어 재지 않았다.
- **패키지 안의 상대 import에는 확장자가 있어야 한다.** `strip_api_client_root`가 그 지정자에서 막혔다. `themes.ts`가 `./styles/contrast.ts`를 확장자까지 적어 읽히는 것과 대비된다.
- **패키지의 의존성은 그 패키지 폴더의 `node_modules` 링크를 거쳐 풀린다.** `clients.ts`에서 `openapi-fetch`를 풀면 `web/node_modules/.pnpm/openapi-fetch@0.17.0/…/dist/index.cjs`가 나온다(프로브가 찍었다). 그 파일에서 가장 가까운 `node_modules`인 `web/packages/api-client/node_modules/`에 `openapi-fetch`가 그 스토어 경로를 가리키는 심볼릭 링크로 있다(`ls -la`로 봤다). 사이트 파일 읽기를 패키지로 옮기고 `smol-toml`을 그 패키지의 의존성으로 들면 같은 길로 풀릴 것으로 미루어 본다(어림. 그 패키지가 아직 없어 재지 않았다. 위젯의 `node_modules`에서 `smol-toml`이 풀리는 것은 아래 Next 설정 회차가 잰 것이다).

### 타입 검사 — `tsc_*`

| 회차 | 결과 | 시간 |
|---|---|---|
| `tsc_nodenext_clean` | tsc 종료 0, `error TS` 없음 | 1.4(첫 실행 0.8, 다섯째 0.8) |
| `tsc_nodenext_mutated` | `mutated.ts(2,7): error TS2322: Type 'string' is not assignable to type 'number'` | 1.5(0.8, 0.8) |
| `tsc_nodenext_extensionless` | `extensionless.ts(1,23): error TS2835: Relative import paths need explicit file extensions in ECMAScript imports when '--moduleResolution' is 'node16' or 'nodenext'. Did you mean '../../../packages/ui/src/themes.js'?` | 0.8 |
| `tsc_bundler_clean` | tsc 종료 0, `error TS` 없음 | 1.5(0.8, 0.8) |
| `tsc_bundler_mutated` | 같은 `TS2322` | 1.4(0.8, 1.0) |
| `tsc_bundler_extensionless` | tsc 종료 0, `error TS` 없음, `--listFiles` 목록에 `extensionless.ts` | 0.9 |

- `@agent-os/ui/contrast`를 패키지 이름으로, `themes.ts`를 확장자 있는 상대 경로로 읽는 코드가 `nodenext`와 `bundler` 두 해석에서 모두 타입 검사를 지난다. 변이가 두 해석 모두에서 `TS2322`로 빨개져 검사가 그 파일을 봤다는 양성 대조가 된다. 임시 tsconfig는 `web/tsconfig.base.json`을 extends 하고(`strict`, `erasableSyntaxOnly`, `verbatimModuleSyntax`), `allowImportingTsExtensions`와 `types: ["node"]`를 둔다. 질문 페이지 앱의 tsconfig는 이 둘 가운데 고를 수 있고 둘 다 선다.
- **확장자 없는 상대 import는 `nodenext`만 막는다.** 다섯째 실행에서 더한 두 회차다. `nodenext`에서는 `TS2835`가 그 파일 이름과 함께 나고(양성 대조), `bundler`에서는 `--listFiles` 목록에 그 파일이 있는데도 오류가 없다(갈래. 파일이 프로그램에 들었는데도 지난 것이라, 검사가 그 파일을 보지 않아 지난 것과 가른다). 그래서 `nodenext`를 고르면 node가 실제로 푸는 규칙(확장자 필수, `strip_api_client_root`)을 타입 검사가 같이 강제하고, `bundler`를 고르면 tsc는 지나지만 node가 `ERR_MODULE_NOT_FOUND`로 막는 코드를 쓸 수 있다. 명세가 `nodenext`를 고른 까닭이다.
- 두 묶음이 함께 쓰는 양성 입구 둘은 다섯째 판부터 `entry_subpath_file`·`entry_themes_file`이 쓰므로 `--group tsc`만 돌려도 선다. 넷째 판까지는 strip 묶음이 쓴 파일에 기대 `--group tsc`만으로는 tsc가 파일을 찾지 못했을 것이다(코드를 읽었다. 그 모양으로 돌린 적은 없다).

### 토큰 CSS — `theme_css_build`·`theme_css_build_child`

패키지 `build`의 둘째 명령(`tailwindcss -i src/styles/theme.css -o <출력>`)을 `web/packages/ui`에서 돌렸다. `theme_css_build`는 프로브가 CLI를 바로 띄운 것이고, `theme_css_build_child`는 node 프로세스가 같은 명령을 `child_process.spawnSync`로 자식으로 띄워 산출 파일을 메모리에 읽고 지운 것이다(질문 페이지 서버가 시작 때 하는 모양).

| 항목 | 값 |
|---|---|
| 원본의 Tailwind 지시문(`@theme`·`@import`·`@source`·`@apply` 줄) | 4(양성 대조) |
| 산출에 남은 지시문 | 0 |
| 크기 | 29,569바이트 |
| 걸린 시간 | 0.67(첫 실행 0.31, 다섯째 0.36) |
| 자식으로 띄운 회차(`theme_css_build_child`) | 자식 종료 0, 산출 29,569바이트(sha256 `51ace4d2…`가 바로 돌린 것과 같음. 여섯째 실행에서 sha256으로 견줬고 다섯째까지는 바이트 수였다)를 메모리에 읽고 파일을 지움(지운 뒤 없음), 지시문 0, 그림의 변수 27개 모두 선언, `--body-size` 선언. 자식 0.31초, node 전체 0.38초 |
| 선언된 CSS 변수 수 | 167 |
| 화면 그림 `pp-page.dc.html`이 `var()`로 읽는 변수 | 27개 모두 선언됨(`--accent`, `--bg`, `--bg-active`, `--bg-raised`, `--bg-selected`, `--border`, `--border-control`, `--control-h`, `--focus-ring`, `--font-weight-medium`, `--on-primary`, `--primary`, `--radius-l`, `--radius-m`, `--radius-s`, `--sans`, `--spacing-1`, `--spacing-2`, `--spacing-3`, `--spacing-4`, `--spacing-6`, `--spacing-8`, `--text`, `--text-muted`, `--text-title`, `--text-title--font-weight`, `--text-title--line-height`) |
| 밀도 변수 `--body-size` | 선언됨 |
| `@layer` 블록(차례대로) | `theme`, `base`, `utilities`, `theme`, `base`, `properties` |
| 클래스 선택자 수 | 122(`flex`, `shadow-float`, `text-body`, `gap-3`, `text-small` 모두 있음) |

- **이 명령의 산출은 토큰만 든 CSS가 아니다.** 변수 선언과 함께 `base` 레이어의 기본 초기화와 유틸리티 클래스 122개가 든다(프로브가 셌다). 같은 명령을 스크래치패드로 한 번 더 돌려 손으로 봤다(`node web/packages/ui/node_modules/@tailwindcss/cli/dist/index.mjs -i web/packages/ui/src/styles/theme.css -o <스크래치패드>/theme-built.css --cwd web/packages/ui` 뒤 `head -40`과 `grep -n "^@layer"`). 산출은 `@layer theme { :root, :host { --text-title: 24px; …`로 시작하고 51행의 `@layer base` 바로 아래가 `*, ::after, ::before, ::backdrop, ::file-selector-button {`이며 199행부터 `@layer utilities`다. 유틸리티가 드는 까닭은 Tailwind v4가 작업 디렉터리 아래 소스에서 클래스 이름을 스스로 긁기 때문으로 본다(어림. 작업 디렉터리를 바꿔 가르지 않았다). 질문 페이지가 이 파일을 그대로 실으면 페이지의 보통 HTML에도 그 초기화가 걸린다. 토큰만 뽑는 입력(`@import "tailwindcss/theme"`만 두는 등)은 재지 않았다.
- 화면 그림이 쓰는 변수 27개는 모두 선언된다. 그 가운데 `--text-title--font-weight`·`--text-title--line-height`는 원본 `@theme static`이 `--text-title` 곁에 함께 선언한 것이다(`theme.css` 39~41행을 읽었다).
- **node 프로세스가 CLI를 자식으로 띄워 메모리에 읽는 길이 선다.** 다섯째 실행에서 더한 회차다. 양성 대조는 바로 돌린 회차와 sha256이 같은 산출이 나와 같은 변수 판정을 지난 것이고, 갈래는 지운 뒤 파일이 없는데도 메모리의 글이 그대로인 것(디스크의 산출에 기대지 않는다)이다. 명세의 "토큰 CSS는 시작 때 짓는다"가 ADR 0050이 거부한 `dist/theme.css`로 되돌아갈 길은 이 측정 안에서는 없다. 두 회차 모두 작업 디렉터리가 `web/packages/ui`이고, 질문 페이지 앱 폴더를 작업 디렉터리로 두는 길은 재지 않았다(Tailwind v4가 작업 디렉터리 아래 소스를 긁으므로 유틸리티의 수는 달라질 수 있다. 어림. 명세는 작업 디렉터리를 디자인 시스템 패키지 폴더로 정했다).

### 글꼴 — `fonts_files`·`fonts_css_self_reference`

`fonts_files`는 위젯의 `tools/fonts.ts`를 그대로 import 해 돌렸다. `fonts_css_self_reference`는 `web/packages/ui/` 안 임시 폴더의 `.ts`가 그 도우미와 같은 호출(`createRequire(import.meta.url).resolve("@agent-os/ui/fonts.css")`)로 패키지 자신의 서브패스를 푸는지 봤다.

| 항목 | 값 |
|---|---|
| `fonts.css` 원본의 `@import "@fontsource/…"` 줄 | 5(양성 대조) |
| `fontFiles()`가 가리키는 woff2 파일 | 386개, 5,853,912바이트 |
| `fontFaces()`의 `@font-face` | 386개, 글꼴 가족 둘(`Noto Sans KR`, `Noto Sans Mono`) |
| `fonts_css_self_reference` | 패키지 안에서 `@agent-os/ui/fonts.css`가 `web/packages/ui/src/styles/fonts.css`로 풀림. export 지도에 없는 `@agent-os/ui/__probe_missing__.css`는 `ERR_PACKAGE_PATH_NOT_EXPORTED` |

- 글꼴 CSS를 같은 출처에서 내려면 위젯이 `copyFonts`로 하듯 woff2 386개(약 5.6MiB)를 정적 폴더로 복사하거나 그 경로에서 바로 읽어야 한다. 위젯의 `tools/fonts.ts`는 node가 그 자리에서 그대로 돌렸다(`fonts_files`가 `fontFiles()`·`fontFaces()`를 불렀다).
- **그 도우미가 `@agent-os/ui/fonts.css`를 푸는 호출은 패키지 안으로 옮겨도 선다.** 다섯째 실행에서 더한 `fonts_css_self_reference`가 그 패키지 안의 임시 폴더에서 같은 호출로 `src/styles/fonts.css`를 풀었다(node의 패키지 자기 참조. `package.json`에 `exports`가 있어야 한다). 양성 대조는 푼 경로가 그 파일인 것이고, 갈래는 export 지도에 없는 서브패스가 `ERR_PACKAGE_PATH_NOT_EXPORTED`로 거부된 것이다(푼 길이 어느 `node_modules`의 사본이 아니라 자기 `package.json`의 export 지도라는 것을 가른다). 옮긴 도우미 파일 자체가 그 자리에서 도는지는 재지 않았다(어림. 푸는 호출의 모양이 같다).

### Next 설정 — `next_config_*`

임시 `nextapp/next.config.ts`가 `@agent-os/ui/contrast`, `smol-toml`, 이웃 `./local.ts`를 import 하고, `next/dist/server/config.js`의 `loadConfig`가 그것을 읽어 `env` 세 값을 내는지 봤다. 옮겨 갈 사이트 파일 패키지가 아직 없어 `@agent-os/ui/contrast`가 그 자리의 대리다.

| 회차 | 작업 디렉터리 | 결과 | 시간 |
|---|---|---|---|
| `next_config_legacy`(기본 길) | 설정 파일의 폴더 | `env` 세 값 그대로(`PROBE_LOCAL=local-ok`) | 0.5 |
| `next_config_legacy_other_cwd_missing` | 임시 폴더(`local.ts` 없음) | `Cannot find module './local.ts'`로 종료 1 | |
| `next_config_legacy_other_cwd_decoy` | 임시 폴더(`local-from-cwd`를 내는 `local.ts` 있음) | `env` 세 값 그대로, `PROBE_LOCAL=local-from-cwd` | 0.4 |
| `next_config_native_other_cwd`(`__NEXT_NODE_NATIVE_TS_LOADER_ENABLED=true`) | 임시 폴더 | `env` 세 값 그대로(`PROBE_LOCAL=local-ok`). 끝난 뒤에도 그 변수가 `true`(대체 길로 떨어지지 않았다) | 0.5 |

- **두 길 모두 워크스페이스 패키지의 `.ts` 진입점과 `smol-toml`을 읽는다.** ADR 0050이 "위젯 빌드의 `next.config.ts`가 옮겨 간 패키지의 `.ts` 진입점을 읽는지"를 묻던 자리다. 기본 길은 SWC로 CJS로 옮긴 뒤 `require.extensions`에 `.ts` 훅을 걸어 패키지의 `.ts`도 변환한다(`next/dist/build/next-config-ts/require-hook.js`를 읽었다).
- **기본 길의 상대 import는 설정 파일의 폴더가 아니라 작업 디렉터리를 기준으로 풀린다.** 미끼 회차가 가른다. 상대 import 자체가 안 되는 것이면 미끼를 두어도 실패했을 텐데 미끼의 값이 실렸다. 까닭은 `requireFromString`이 `new Module(filename)`에 `_compile`만 불러 `filename`이 `null`로 남고, node의 CJS 로더가 `filename`이 없는 부모의 상대 요청에 기준 폴더 `['.']`를 돌려주기 때문이다(node 24.19.0의 `Module._resolveLookupPaths`를 `node -p "require('module')._resolveLookupPaths.toString()"`으로 읽었다. 그 코드는 `!parent.filename`이면 `['.']`를 돌려준다. 같은 모양의 `Module`을 만들어 `node -p "const M=require('module'); const m=new M('C:/x/y/fake.js', module); m.paths=M._nodeModulePaths('C:/x/y'); JSON.stringify({filename:m.filename, lookup:M._resolveLookupPaths('./local.ts', m)})"`를 치니 `{"filename":null,"lookup":["."]}`였다. 손으로 봤다). 위젯의 `tools/start.ts`는 next를 부르기 전에 `process.chdir(APP)`을 하므로 지금 위젯의 `./tools/site-file.ts` import는 그 덕에 맞는다. 사이트 파일 읽기를 패키지로 옮기면 `next.config.ts`에서 그 가정이 사라진다.
- node 네이티브 길은 ESM `import()`라 작업 디렉터리와 무관하다. 이 프로브는 그 변수를 켠 길이 서는 것만 봤고, 위젯 빌드가 그 길을 쓰게 바꾸자는 뜻은 아니다.

### 페이지 스크립트 — `page_script_*`

명세를 쓰며 더한 묶음이다(같은 날 셋째 실행, `--group pagescript`로 두 회차만 돌렸다). 브라우저는 `.ts`를 읽지 못하므로, 페이지 스크립트를 `.ts`로 두고 서버가 시작 때 `node:module`의 `stripTypeScriptTypes`(node 24.19.0)로 타입만 벗겨 내주는 길이 서는지 봤다.

| 회차 | 입력 | 결과 | 시간 |
|---|---|---|---|
| `page_script_strip` | 타입 별칭 하나와 주석 넷이 든 스크립트를 `strip` 모드로 벗긴 뒤 `vm.runInThisContext`로 돌림 | 돌았음(전역에 둔 라벨 글이 기대와 같음). 산출에 타입 주석과 `type` 선언 잔존 없음. 줄 수가 원본과 같음 | 0.1 |
| `page_script_strip_enum` | `enum Mode { Light }`를 같은 모드로 벗김 | 거부 `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` | 0.1 |

- **페이지 스크립트는 `.ts`로 두고 시작 때 벗겨 내줄 수 있다.** 양성 대조는 벗긴 산출이 실제로 돌아 기대한 값을 낸 것이고(`page_script_strip`), 갈래는 지울 수 없는 문법이 거부된 것이다(`page_script_strip_enum`). 잰 것은 그 둘뿐이다. 벗기지 못하는 문법의 목록(`enum`, 런타임 코드가 있는 `namespace`, 매개변수 프로퍼티)과 TypeScript 5.8 이상에서 `erasableSyntaxOnly: true`를 두라는 권고는 Node 문서(`nodejs.org/api/typescript.html`, 2026-11-10에 읽었다)가 적는 것이라, 기준 tsconfig의 `erasableSyntaxOnly`를 지난 스크립트가 벗기기에서 막히지 않는 것은 문서로 아는 것이고 이 프로브가 잰 것이 아니다(PR #504의 CodeRabbit이 일반화를 짚었다). 줄 수가 같으므로 브라우저의 오류 줄 번호가 원본 `.ts`의 줄과 맞는다.
- 결과를 본 뒤 바꾼 기준 하나. 갈래의 표지를 첫 판은 `ERR_INVALID_TYPESCRIPT_SYNTAX`로 적었고, 첫 실행의 원본(stdout의 `{"code":"ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX"}`)이 다른 코드라 그 코드로 고쳤다(틀린 문법이 아니라 지원하지 않는 문법의 코드다). 첫 실행은 그 회차가 측정 아님으로 끝나 종료 코드 1이었고, 고친 뒤의 실행이 두 회차 모두 측정이었다.
- node가 그 API를 처음 부를 때 stderr에 두 줄을 찍는다. 첫 줄은 `(node:<pid>) ExperimentalWarning: stripTypeScriptTypes is an experimental feature and might change at any time`이고 둘째 줄은 `--trace-warnings`로 경고가 난 자리를 보라는 안내 `(Use \`node.EXE --trace-warnings ...\` to show where the warning was created)`다(`node.EXE`는 이 PC의 실행 파일 이름이다). 저장소 루트에서 `node -e "const {stripTypeScriptTypes}=require('node:module'); stripTypeScriptTypes('const a: number = 1;', {mode:'strip'});"`를 쳐 손으로 봤고, 두 회차의 원본 stderr에도 같은 두 줄이 있다. 서버의 stderr에도 남을 것이다(어림. 끄는 플래그는 재지 않았다).
