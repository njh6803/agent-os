# 01: 사이트 파일 읽기와 디자인 시스템 서브패스를 패키지로 뽑는다 — 위젯 빌드가 `@agent-os/site-file`로 사이트 파일을 읽는다

**What to build:** 위젯을 빌드하는 운영자에게는 바뀌는 것이 없다. 같은 사이트 파일에서 같은 허용 출처와 요청 글자 수 상한이 위젯 빌드에 박히고, 사이트 파일이 틀리면 같은 진단으로 빌드가 멈춘다. 달라지는 것은 그 읽기가 새 워크스페이스 패키지 `@agent-os/site-file`(`web/packages/site-file`)에 있고, 사이트마다 발급자, `audience`, 열 에이전트, 허용 출처, 공개 키(`kid`, `pem`), 요청 글자 수 상한을 든 모델을 낸다는 것이다. 위젯 빌드는 그 가운데 합친 허용 출처와 가장 작은 요청 글자 수만 쓰고, 나머지 칸은 질문 페이지의 시작 검사(04)가 쓴다. 디자인 시스템 패키지에는 서브패스 둘이 열린다. `@agent-os/ui/themes`는 `THEMES`·`DEFAULT_THEME`·`MODES`·`DENSITIES`를, `@agent-os/ui/fonts`는 위젯의 글꼴 도우미(글꼴 CSS가 가리키는 woff2 목록, `@font-face` 목록, 복사)와 `FontFaceSource` 타입을 낸다. 위젯의 시작 래퍼와 페이지 안 번들이 그것을 쓴다. 셋(`@agent-os/site-file`, `@agent-os/ui/themes`, `@agent-os/ui/fonts`) 모두 node가 빌드 없이 읽는 꼴(확장자를 붙인 상대 import, `.tsx` 없음)이라 질문 페이지 서버가 패키지 이름으로 import할 수 있다(스토리 14).

01은 이 기능의 첫 티켓이고 02와 04를 막는다. 명세의 묶음 A 가운데 e2e 준비는 02가 뽑는다. 명세의 이야기 16("패키지를 뽑는 변경이 첫 티켓 하나에")은 to-tickets에서 사용자가 아홉 장 분할을 골라 01과 02 둘로 바뀌었다. 위젯 빌드는 이 티켓의 한 커밋에서 바뀐다.

근거는 `.scratch/pilot-portal/spec.md`의 "앱과 패키지"와 그 2026-11-10 명세 검토 주석, "띄우기와 타입 검사"의 주석 첫째, "고칠 자리의 묶음"의 A 줄과 그 주석, Further Notes의 "재지 않은 것(어림)"이다. 측정은 `.scratch/pilot-portal/probes/node_ts_workspace.py`와 그 `README.md`이고 다시 돌리지 않는다. 앞선 결정은 ADR 0050의 결정 "띄우기"·"함께 쓰는 코드"와 그 2026-11-09 이력 "띄우기의 어림을 잰 값으로 바꾸고 토큰 CSS와 페이지 스크립트는 시작 때 짓는다"이고, 사이트 파일의 형식은 ADR 0024다.

**Blocked by:** None (can start immediately)

**Status:** done

### 어림 둘을 먼저 대 본다

- [x] **명세 Further Notes의 어림 둘을 그 자리에서 먼저 대 본다.** `@agent-os/ui/themes`가 node로 패키지 이름에서 읽히는가, `site-file` 패키지 안에서 `smol-toml`이 그 패키지 폴더의 `node_modules` 링크로 풀리는가다. 둘 다 아래 node 풀이 시험의 사례가 되어 늘 돈다. 틀리면 명세가 적은 고칠 길(서브패스를 열고 의존성을 적는다)대로 고치고 일지에 적는다

### `@agent-os/site-file`

- [x] **위젯의 `tools/site-file.ts`와 그 시험을 패키지로 옮긴다.** 허용 출처의 표기 규칙과 모양 판정(서버의 pydantic 모델과 같은 규칙, 문제를 모두 모아 알린다)은 그대로다. smol-toml을 제 의존성으로 든다
- [x] **읽은 사이트 파일을 사이트마다 발급자, `audience`, 열 에이전트, 허용 출처, 공개 키(`kid`, `pem`), 요청 글자 수 상한을 든 모델로 낸다**(명세 "앱과 패키지"). 지금 위젯의 읽기는 칸의 모양을 모두 판정하되 값은 합친 허용 출처와 가장 작은 요청 글자 수만 낸다. 넓힌 칸마다 공유 픽스처(`tests/fixtures/site_file/`)를 읽는 시험 사례를 더한다
- [x] **위젯의 `next.config.ts`, 시작 래퍼, 페이지 안 번들의 빌드가 패키지 이름으로 그것을 쓴다.** `next.config.ts`의 상대 import가 시작 래퍼의 `process.chdir`에 기대던 가정이 사라진다(명세 "앱과 패키지", 프로브 `next_config_legacy_other_cwd_decoy`)
- [x] **패키지의 진입점과 그 안의 상대 import는 모두 확장자를 붙인다.** 패키지의 tsconfig는 `web/tsconfig.base.json`을 extends 하고 `module`·`moduleResolution`을 `nodenext`로 둔다(명세 "띄우기와 타입 검사"의 주석 첫째). 확장자 없는 상대 import 하나를 일부러 넣어 `pnpm -C web verify`의 타입 검사가 `TS2835`로 빨개지는 것을 본 뒤 되돌린다. 위젯과 다른 패키지의 `bundler`로는 그 import가 지나 이 티켓에서 아무 게이트도 확장자를 보지 않기 때문이다

### `@agent-os/ui`의 서브패스 둘

- [x] **`./themes`는 `themes.ts`를, `./fonts`는 위젯의 `tools/fonts.ts`를 옮긴 node 쪽 도우미와 `FontFaceSource` 타입을 낸다.** 그 타입은 지금 위젯의 `element/fonts.ts`에 있고 브라우저 쪽 코드가 쓴다(명세 "앱과 패키지"의 주석 셋째). 브라우저 쪽은 `import type`으로 읽는다. 두 파일 모두 `.tsx`를 거치지 않고 상대 import에 확장자가 있다
- [x] **진입점 판정 스토리(`web/packages/ui/src/Entrypoints.stories.tsx`)와 node 풀이 시험(선례 `web/tools/contrast-module.test.ts`)에 두 서브패스를 더한다.** 스토리의 머리 주석이 든 진입점 수도 고친다. `./fonts`는 `node:fs`를 들이므로 브라우저에서 도는 그 스토리가 불러올 수 있는지 먼저 본다. 불러올 수 없으면 `./visual`처럼 그 까닭을 머리 주석에 적고 node 풀이 시험만 둔다
- [x] **위젯의 시작 래퍼(글꼴 복사)와 페이지 안 번들(`@font-face` 등록)이 `@agent-os/ui/fonts`를 쓴다**

### 참조와 문서

- [x] **옛 경로(`web/apps/widget/tools/site-file.ts`, `tools/fonts.ts`)의 grep 잔존이 살아 있는 문서와 코드에서 0이다.** 명세 "앱과 패키지"의 주석 둘째가 든 자리(`src/agent_os/main.py`, `tests/test_main.py`, `tests/fixtures/site_file/README.md`, 위젯의 `lib/build.ts`·`lib/build.test.ts`·`next.config.test.ts`·`element/fonts.ts`·`tools/start.ts`·`tools/element.test.ts`), README의 트리, `docs/constitution/tech.md` 웹 행을 포함한다. 헌법을 고치면 판을 patch로 올린다(`docs/constitution/README.md`). 기록(일지, 대기열, 명세, 닫힌 티켓)은 고치지 않는다

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 넓힌 모델의 칸(발급자, `audience`, 열 에이전트, 공개 키)을 읽는 시험이 옮기기 전에 빨갛다
- [x] **위젯의 Vitest와 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`)가 그대로 초록이다.** 위젯 빌드가 바뀌었으므로 위젯 e2e를 로컬에서 치고, `uv run --env-file .env pytest -m llm_widget`도 친다(`CLAUDE.md` 검증 명령). `packages/ui`를 건드리므로 사진 비교 셋(`pnpm -C web visual`, `visual:widget`, `visual:admin`)도 친다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯과 위의 e2e·`-m llm_widget`·사진 비교다
