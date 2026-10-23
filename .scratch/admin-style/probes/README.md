# admin-style 프로브

admin-style 화면을 그리기 직전의 디자인 시스템 맞추기가 근거로 드는 측정이다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"이고 짓는 규칙은 `.claude/rules/probes.md`다.

아티팩트를 읽는 일은 Claude Code의 Artifact 도구로만 되어, 도구가 낸 값(판 id, 바이트 수, sha256)을 기록 파일에 옮겨 적고 대조는 design-artifacts의 스크립트가 한다.

저장소 루트에서 돈다.

```sh
node .scratch/design-artifacts/probes/hash_match.mjs --record .scratch/admin-style/probes/artifact_reads.json [--saved <받은 파일 폴더>]
```

받은 폴더는 그 세션의 스크래치패드에 있어 커밋되지 않는다. `--saved` 없이 돌리면 받은 바이트의 sha256 대조 다섯이 빠져 측정 6(양성 다섯, 음성 하나)이다(2026-10-23 셀프 리뷰가 이 워크트리에서 돌린 탐침의 집계 줄 "측정 6, 측정 아님 0, 기대와 다름 0", 종료 0).

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `artifact_reads.json` | 빌드가 저장소 원본을 그대로 옮기는 다섯(`.claude/rules/web-design.md`, `.design-sync/foundations/` 아래 기초 카드 넷)이 디자인 시스템 아티팩트의 `project/guidelines/web-design.md`, `project/foundations/<이름>/index.html`과 바이트까지 같은지(양성 다섯). 음성 대조 하나는 `c41adad`가 머리 문장을 고치기 전(`df705c17`)의 `web-design.md`가 다르다고 나오는지다. 빌드 산출 전체(카드, 번들, 글꼴)는 맞대지 않는다 | `.scratch/admin-style/design/README.md` 표의 동기화한 커밋 칸(`agent-os 부분 main@c41adad`)과 일지 2026-10-23-27의 맞추기 판단 | 아티팩트를 다시 읽어(`read`의 `paths`) 줄의 판 id와 sha256을 새로 적고, 받은 폴더를 `--saved`로 준다 | 아티팩트 판 `1792677911-3a99`, 저장소 `b104f8fa`, Node 24 |

## 2026-10-22 결과

- `hash_match.mjs --record .scratch/admin-style/probes/artifact_reads.json --saved <받은 폴더>`: 측정 11, 측정 아님 0, 기대와 다름 0. 양성 다섯이 같고, 음성 대조 하나가 다르며, 받은 바이트 다섯의 sha256이 도구가 낸 값과 같다.
- 빌드 입력(`web/packages/ui`, NOTES를 뺀 `.design-sync`, `.claude/rules/web-design.md`)은 `c41adad`에서 `b104f8fa`까지 바뀌지 않았다(`git diff --stat`이 비었다). 마지막 전체 올리기 PR #239(`983bf491`)에서 `c41adad`까지는 `web-design.md`와 `web/packages/ui/visual/` 아래 사진 비교 시험 둘만 바뀌었다. 사진 비교 시험이 빌드 산출에 들지 않는다는 것은 설정을 읽은 어림이다. 패키지 `build`의 `tsconfig.build.json`은 `include`가 `src/**/*`이고, 참조 Storybook의 `.storybook/main.ts`는 `stories`가 `../src/**/*.stories.tsx`라 둘 다 `visual/`을 들이지 않는다. 번들 스킬의 변환기는 읽지도 돌리지도 않았다.
