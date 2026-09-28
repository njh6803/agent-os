# web-admin 프로브

ADR 0010·0011의 2026-09-28 이력과 ADR 0019~0021이 근거로 든 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`.
모두 설계 인터뷰(일지 2026-09-28-06) 중에 쟀다. 결과를 다시 볼 때는 버전을 함께 본다. Next 16.3.6,
openapi-typescript 7.13.0, typescript-eslint 8.70.1, TypeScript 5.9.3과 7.0.2다. 판이 바뀌면 값도 바뀔 수 있다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `gen_run.mjs` + `gen_rt_probe.ts` | 계약 파일 사본 셋(`openapi.json` 원본의 3.1.0, 3.2.0, admin/channel 태그)에 생성기 넷을 돌린다. openapi-typescript(+openapi-fetch), @hey-api/openapi-ts, orval(fetch·swr·react-query·tags-split), openapi-generator typescript-fetch다. 재는 것은 받는지, SSE 응답 타입, 유니온·열거·readonly, 파일·줄·외부 import, 태그 전후 차이, TS 7에서의 생성과 검사다. 루프백 스텁에 붙여 실제 SSE와 409 처리(hey의 POST 재전송 포함)도 본다 | ADR 0010의 2026-09-28 이력, ADR 0020(TS 7에서 생성이 죽음, 재귀 `Json`), ADR 0021(생성기와 Considered Options) | `node .scratch/web-admin/probes/gen_run.mjs <작업 디렉터리> [--versions] [--java-home <JDK>]`. Node 22.18 이상이다. npm 레지스트리와 Maven Central(jar 약 31MB)에 닿고 루프백 포트 하나를 연다. openapi-generator는 Java 11 이상이 필요하고, 없으면 건너뛴다. 약 3분 걸린다. 결과는 `<작업 디렉터리>/summary.json`에 쓴다 |
| `next_measure.mjs` + `next_sse_upstream.mjs`, `next_sse_client.mjs`, `next_app/` | Next 16.3.6에서 여덟 가지를 잰다. 바인딩, dev의 교차 출처 차단, SSE 중계(rewrites와 route handler × compress × Accept-Encoding), 압축 대상, 끊김 전파, 헤더와 `OPTIONS` 전달, Server Actions의 CSRF, 침묵 시 끊김(30초·300초)이다 | ADR 0019(중계, 바인딩, BFF를 거부한 이유), ADR 0011의 2026-09-28 이력 | `next_app/`을 저장소 밖에 복사해 `pnpm install --frozen-lockfile`을 한다. 그다음 저장소 루트에서 `node .scratch/web-admin/probes/next_measure.mjs <그 폴더> [섹션…]`을 돌린다. 포트 3000·8765가 비어 있어야 한다. 기본 섹션 전부 약 15분, `gaplong`은 따로 약 6분이다. Windows 전용(taskkill, netstat, powershell). 에이전트 환경의 `next dev`는 앱 폴더에 `AGENTS.md`·`CLAUDE.md`를 만든다(ADR 0021). 복사본에서 돌리는 이유 중 하나다 |
| `ts7_lint.sh` | typescript-eslint의 타입 기반 규칙(`strictTypeChecked` + 단언 금지)이 TS 5.9.3과 7.0.2에서 도는지 잰다 | ADR 0020(TypeScript 5.9 고정) | `bash .scratch/web-admin/probes/ts7_lint.sh <작업 디렉터리>`. npm 레지스트리에 닿는다. 5.9.3은 5건을 잡고 종료 1, 7.0.2는 시작에서 거부하고 종료 2다 |
