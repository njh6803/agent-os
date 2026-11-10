# answer-markdown 프로브

명세·ADR·코드 주석이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거".

`markdown_render/`는 모델이 지은 답을 마크다운으로 그릴 라이브러리를 고르는 프로브다. 후보는 react-markdown + remark-gfm과 markdown-to-jsx이고, marked는 크기와 의존성을 견주는 데만 든다. 후보마다 제한을 건 컴포넌트(`apps/widget/components/molecules/MarkdownReact.tsx`, `MarkdownJsx.tsx`)와 주소 판정(`apps/widget/lib/safe-url.ts`)을 짓고, 그것이 저장소와 같은 타입 검사와 판정자 설정을 지나는지, 위험한 입력에서 무엇을 그리는지, 번들이 얼마나 느는지를 본다. 스크립트마다 측정이 아닌 회차를 세는 조건과 양성 대조는 그 파일의 머리 주석에 있다.

```sh
pnpm -C .scratch/answer-markdown/probes/markdown_render install --frozen-lockfile
node .scratch/answer-markdown/probes/markdown_render/probe/typecheck.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/lint.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/deps.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/registry.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/render.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/report.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/size.mjs
node .scratch/answer-markdown/probes/markdown_render/probe/stress.mjs
```

저장소 루트에서 돈다. Node 24와 pnpm 11.24.0이 있어야 하고, 설치는 `pnpm-workspace.yaml`의 정책대로 설치 스크립트를 돌리지 않는다. 산출물은 `markdown_render/out/`에 생기고 커밋하지 않는다(그 폴더의 `.gitignore`). 스크립트마다 표준 출력의 마지막 줄이 결과의 JSON 한 줄이다. `registry.mjs`만 바깥(`https://registry.npmjs.org/`)에 읽기 요청 넷을 보낸다.

결과의 근거. 아래 표의 결과는 2026-11-10에 손으로 돌려 본 것이다. 처음에는 설계 인터뷰의 조사 서브에이전트가 저장소 밖 임시 폴더에서 돌렸고, 같은 날 이 폴더로 옮긴 뒤 위 명령을 순서대로 다시 돌려 그 실행이 남긴 표준 출력과 견줬다. `render.mjs`와 `size.mjs`의 출력은 글자까지 같았다. `typecheck.mjs`와 `lint.mjs`는 경로 표기만 달랐고, `deps.mjs`는 설치 로그 칸만 달랐다(옮긴 자리에는 `out/install.log`가 없다). `registry.mjs`는 시각만 달랐고, `stress.mjs`는 걸린 시간만 달랐다. 옮기며 고친 것은 `lint.mjs`의 저장소 경로 기본값(지은 워크트리의 절대 경로를 이 폴더에서 네 단계 위로)과 그 머리 주석뿐이다. 브라우저에서 본 것은 없다. 렌더의 판정은 `react-dom/server`의 `renderToStaticMarkup`이 낸 HTML을 parse5로 읽은 나무에서 한 것이다.

결과를 본 뒤 바꾼 기준은 하나다. `typecheck.mjs`의 양성 대조는 처음에 허용 목록 `switch`에서 갈래 하나를 지우면 TS2366("끝에 return이 없다")이 난다고 기대했는데 걸리지 않았다. 반환 타입 `ReactNode`가 `undefined`를 품기 때문이다. 그래서 컴포넌트의 `default` 갈래에 `never` 대입을 넣고 기대를 TS2322로 바꿨다(그 파일의 머리 주석). 그리고 `MarkdownJsx.tsx`는 첫 판에서 할 일 목록의 `input`과 각주의 `footer`가 제한을 지나 그려졌고, 허용 목록과 `overrides`를 고친 뒤 다시 돌린 것이 아래의 결과다. 첫 판의 산출물은 커밋하지 않았으므로 이 문장은 조사 서브에이전트의 보고다.

answer-markdown의 명세 단계가 설치할 판으로 다시 돌리고 결과를 ADR 0053의 이력에 적는다(`.scratch/answer-markdown/plan.md`).

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `markdown_render/probe/typecheck.mjs` + `apps/widget/**` + `tsconfig.json` + `tsconfig.base.json` | 제한을 건 두 컴포넌트와 주소 판정이 저장소와 같은 strict 옵션(`tsconfig.base.json`은 `web/tsconfig.base.json`의 사본)에서 `tsc --noEmit`을 지나는지. 손으로 돌려 본 결과: 오류 0, tsc가 본 파일 287개, 양성 대조 둘(`noUncheckedIndexedAccess`와 빠진 갈래)이 TS2322로 걸렸다 | answer-markdown 설계 인터뷰의 라이브러리 결정(일지 2026-11-10-1345). ADR 0053은 이 결과를 글로 들지 않는다 | 인자 없음. `tsconfig.base.json`은 사본이라 `web/tsconfig.base.json`이 바뀌었으면 다시 옮긴다 | TypeScript 5.9.3, react-markdown 10.1.0, remark-gfm 4.0.1, markdown-to-jsx 9.10.6, React 19.3.0 |
| `markdown_render/probe/lint.mjs` | 같은 세 파일이 저장소의 판정자 설정(`web/eslint.config.mjs`를 글자 그대로 복사)을 지나는지. 손으로 돌려 본 결과: 세 파일 모두 오류 0·경고 0, 일부러 심은 위반(`Planted.tsx`)에서 기대한 규칙 넷이 걸렸다. 복사한 설정의 SHA-256은 `8ec742f8…6ada`다 | answer-markdown 설계 인터뷰의 라이브러리 결정(일지 2026-11-10-1345). ADR 0053은 이 결과를 글로 들지 않는다 | 인자는 저장소 경로이고 주지 않으면 이 폴더에서 네 단계 위다. 판정자 설정이 바뀌었으면 SHA-256이 달라진다 | ESLint 10.11.0, typescript-eslint 8.70.1, eslint-plugin-boundaries 7.2.0 |
| `markdown_render/probe/deps.mjs` | 설치된 `node_modules`를 따라가 센 후보마다의 판, 라이선스, 직접·전이 의존성 수. 손으로 돌려 본 결과: react-markdown + remark-gfm은 직접 14, 전이 98(타입만 든 것 8), 라이선스 MIT 99와 ISC 1, 설치 스크립트가 든 패키지 0. markdown-to-jsx와 marked는 의존성 0 | ADR 0053 Consequences "의존성" | 인자 없음. 설치 로그의 peer 경고를 보려면 설치 출력을 `out/install.log`에 남긴다 | react-markdown 10.1.0, remark-gfm 4.0.1, markdown-to-jsx 9.10.6, marked 18.1.3, pnpm 11.24.0 |
| `markdown_render/probe/registry.mjs` | 설치한 판이 언제 나왔고 지난 365일에 정식 판이 몇 번 나왔는지. 손으로 돌려 본 결과(2026-11-10): react-markdown 10.1.0은 612일 전에 나왔고 365일 동안 0판, remark-gfm 4.0.1은 637일 전이고 0판, markdown-to-jsx 9.10.6은 3일 전이고 52판, marked 18.1.3은 7일 전이고 26판 | ADR 0053 Considered Options "markdown-to-jsx", Consequences "의존성" | 인자 없음. 레지스트리에 닿아야 한다. 돌리는 날에 따라 수가 달라진다 | 위와 같다 |
| `markdown_render/probe/render.mjs` + `cases.mjs` + `entry.tsx` + `report.mjs` | 입력 52가지(원시 HTML, 스크립트, 이벤트 속성, 위험한 주소, 이미지, 표, 각주 등)를 후보 둘 × 방식 둘(제한, 기본)로 그린 208회차의 HTML. 손으로 돌려 본 결과: 208회차 모두 측정이고, 제한을 건 쪽은 두 후보 모두 규칙 위반 0·기대 어김 0. 제한을 걸지 않은 대조군은 react-markdown이 23가지, markdown-to-jsx가 28가지 입력에서 규칙을 어겼다 | ADR 0053 결정 "그리는 요소는 허용 목록", "링크", "받아들이는 부작용", "시험", Considered Options "markdown-to-jsx" | 인자 없음. `report.mjs`는 `out/render/summary.json`을 사람이 읽는 글로 편다 | react-markdown 10.1.0, remark-gfm 4.0.1, markdown-to-jsx 9.10.6, React 19.3.0, parse5 8.0.1, esbuild 0.28.2 |
| `markdown_render/probe/size.mjs` + `size-entries/**` | 제한을 건 컴포넌트를 묶었을 때 글자 문단만 그리는 기준선보다 느는 바이트. esbuild(React는 밖)와 Vite 라이브러리 빌드(IIFE, React를 품는다) 두 가지로 본다. 손으로 돌려 본 결과(gzip 증분, esbuild와 Vite 순): react-markdown + remark-gfm 50,964와 48,812, markdown-to-jsx 32,040과 31,172, remark-gfm을 뺀 react-markdown 36,982와 35,291. Vite 기준선은 gzip 67,445바이트다 | ADR 0053 Consequences "번들이 는다", Considered Options "markdown-to-jsx" | 인자 없음. 기준선은 프로브의 것이라 실제 element 번들의 크기와 다르다. 실제 번들의 증분은 의존성을 들이는 티켓이 잰다 | esbuild 0.28.2, Vite 8.3.1, 위 라이브러리의 판 |
| `markdown_render/probe/stress.mjs` + `stress-child.mjs` | 병적인 입력 14가지에서 제한을 건 컴포넌트가 멈추거나 던지는지와 걸린 시간. 회차마다 자식 프로세스를 띄워 15초에 끊는다. 손으로 돌려 본 결과: 28회차 모두 측정이고 끊긴 회차 0. react-markdown은 `>`를 3,000겹 겹친 인용에서 `RangeError`를 던졌고 markdown-to-jsx는 던지지 않았다. 보통의 답 1KB는 두 번의 실행에서 react-markdown이 약 3ms, markdown-to-jsx가 약 0.6ms였다 | ADR 0053 결정 "실패하면 원문", Considered Options "markdown-to-jsx", Consequences "병적인 입력" | 인자 없음. 시간은 Node 24의 서버 렌더로 본 것이라 브라우저의 값이 아니고 견줌에만 쓴다 | Node 24, React 19.3.0, 위 라이브러리의 판 |
