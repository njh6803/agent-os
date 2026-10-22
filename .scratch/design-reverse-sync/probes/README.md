# design-reverse-sync 프로브

명세(`.scratch/design-reverse-sync/spec.md`)가 근거로 드는 측정이다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"이고 짓는 규칙은 `.claude/rules/probes.md`다.

저장소 루트에서 돈다. `pnpm -C web install`을 한 번 한 기계여야 한다(사본에 오프라인으로 설치한다).

```sh
node .scratch/design-reverse-sync/probes/tools_import.mjs [--commit <커밋>] [--keep]
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `contrast_module_mutations.toml` | 티켓 01의 변이 표 아홉. `web/tools/contrast-module.test.ts`의 vitest 사례 둘은 패키지가 옛 짝 표 파일을 그대로 내보내던 때에도 초록이었다(손으로 봤다. 같은 때 루트 타입 검사는 시험의 import에서 빨갰다. Node 실행의 빨강은 아래 2026-10-22 결과의 프로브다). 그래서 시험의 단언 둘(짝 하나를 뺀 짝 표, 기준을 넘는 짝도 거는 판정), Node를 띄우는 사례 하나와 그 대조군 둘(새 모듈에 `.js`를 붙인 상대 import. 루트 타입 검사와 vitest 안의 사례 둘은 지난다), 루트 타입 검사 셋(새 모듈에 확장자 없는 상대 import, DOM 타입을 쓰는 함수, 패키지 `exports`에서 새 경로를 뺀 것), 진입점 스토리의 여섯째 진입점(새 경로가 다른 파일을 가리킨다)을 겨눈다. 표지는 변이를 손으로 넣어 본 실패 출력에서 골랐다. `tools/mutate.py`로 돈다 | 티켓 01의 수용 기준(새 모듈이 상대 import 없는 한 파일이고 DOM 함수를 넣지 않는다, `web/tools`의 시험과 그 타입 검사·실행) | 없음 | Node 24.19.0, pnpm 11.24.0, TypeScript 5.9.3, Vitest 5.0.2(node 프로젝트와 Storybook 10.6 스토리 테스트, Chromium). 결과는 일지 2026-10-22-17 |
| `tools_import.mjs` | `web/tools`의 Node 스크립트(루트 tsconfig: `nodenext`, `lib` es2024)가 디자인 시스템 패키지의 명암비 계산과 짝 표를 부를 수 있는지. 커밋의 `web/`을 임시 폴더에 두 번 꺼내, 두 갈래 모두 루트 `web/package.json`에 `"@agent-os/ui": "workspace:*"`를 더하고 패키지 `exports`에 경로 하나를 더한 뒤 오프라인으로 설치하고, 루트 타입 검사(`tsc --noEmit`)와 `node tools/probe-import.ts` 실행까지 본다. `as-is`는 지금의 `contrast.ts`를 그대로 내보내고, `self-contained`는 `testing/index.ts`의 DOM 없는 앞부분과 `contrast.ts`의 본문을 이어 붙인 상대 import 없는 한 파일을 내보낸다 | 명세 Implementation Decisions의 "명암비 계산과 짝 표를 부르는 길"(ADR 0025 이력 2026-10-21 "명세가 정할 것" (6)) | 기본은 지금 `HEAD`의 `web/`이다. 아래 결과를 그대로 다시 보려면 `--commit 14efe41d`. 사본을 남기려면 `--keep`. 측정 아닌 갈래나 기대와 다른 갈래가 있으면 1로 끝난다 | 커밋 `14efe41d`, Node 24.19.0, pnpm 11.24.0, TypeScript 5.9.3 |

## 2026-10-21 결과

- `as-is`: 설치 0, 링크가 섰다. 타입 검사가 2로 끝났고, 출력 줄의 `tsc.codes`(타입 검사 출력에서 모은 오류 번호)가 TS2834·TS2835 둘뿐이었다. 표지로 단언한 것은 `contrast.ts`의 줄에 그 둘 가운데 하나가 있다는 것이고, 다른 번호가 없다는 것은 출력으로 봤다. `node`는 1로 끝났고 첫 import `"../testing"`을 폴더 import로 읽어 `ERR_UNSUPPORTED_DIR_IMPORT`를 냈다.
- `self-contained`: 설치 0, 링크가 섰다. 타입 검사 0, 오류 번호 없음. `node`가 0으로 끝나며 `{"pairs":43,"failures":43}`을 찍었다. 모든 쓰임새 토큰을 검정으로 준 실행이라 짝 43개가 모두 실패하는 것이 기대값이고, 계산이 실제로 돌았다는 표지다.
- 요약: 측정 2, 측정 아님 0, 기대와 다름 0. 종료 0.

두 갈래는 같은 설치(작업 공간 의존, `exports`가 `.ts` 파일을 바로 가리키는 경로, Node의 타입 지우기 실행)를 나누고, 다른 것은 내보낸 파일 안의 상대 import 유무뿐이다. 그래서 `as-is`의 실패를 `exports`가 `.ts`를 가리키는 탓이나 작업 공간 링크 탓으로 읽는 해석은 `self-contained`가 같은 설치로 초록인 것이 배제한다(양성 대조). 반대로 `self-contained`의 초록이 그 상대 import를 없앤 덕이라는 해석은, 같은 설치에서 상대 import만 남긴 `as-is`가 그 import의 자리에서 빨간 것이 받친다.

첫 실행은 `as-is`의 `node` 표지를 `ERR_MODULE_NOT_FOUND`로 잘못 골라 그 갈래가 측정 아님이었다. 원본 출력을 본 뒤 표지를 실제 오류(`ERR_UNSUPPORTED_DIR_IMPORT`와 `testing` 폴더 경로)로 고쳐 다시 돌린 것이 위 결과다.

## 2026-10-22 결과 (티켓 01, 옮기기 전 판)

티켓 01이 짝 표 파일을 한 파일 모듈로 옮기기 전 판에서 두 빨강을 보려고 `--commit 96fbe241`(그 브랜치의 base)로 다시 돌렸다. 위 결과와 같다. `as-is`는 타입 검사 2(`TS2834`·`TS2835`), `node` 1(`ERR_UNSUPPORTED_DIR_IMPORT`)이고, `self-contained`는 타입 검사 0, `node` 0(`{"pairs":43,"failures":43}`)이다. 측정 2, 측정 아님 0, 기대와 다름 0, 종료 0. 판은 위와 같다.

## 재지 못한 것

- 상대 import에 `.ts` 확장자를 붙여 지금 파일들을 그대로 내보내는 길. 루트 tsconfig는 `allowImportingTsExtensions`를 켜지만 패키지 쪽 설정과 Storybook 빌드에서 그 꼴이 지나는지는 보지 않았다. 명세는 잰 길을 고른다.
- 패키지 안의 `testing`과 `contrast.ts`가 새 한 파일 모듈을 불러 쓰게 바꾼 뒤에도 패키지의 스토리 테스트가 그대로 초록인지. 패키지는 `bundler` 해석이라 확장자 없는 import가 지금처럼 지난다고 본다(어림). 구현 티켓이 `pnpm -C web verify`로 본다. (2026-10-22 티켓 01: 옮긴 뒤 `pnpm -C web exec vitest run --project storybook`의 스토리 테스트 102개가 초록이었다. 손으로 봤다. 사진 비교(`nodenext`)도 `themes.ts`를 들여, 그 파일은 새 모듈을 `.js` 확장자로 들인다)
