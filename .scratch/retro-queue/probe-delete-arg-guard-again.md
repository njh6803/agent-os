# probe-delete-arg-guard-again: **0269의 2회차. release-image의 이미지 프로브 `strip-tests.sh`가 인자로 받은 앱 폴더를 절대 경로 검사도 표지 파일 검사도 없이 `find -delete`와 `rm -rf`로 지웠다**(PR의 CodeRabbit 첫 회차가 Major로 잡았다)

**상태:** 열림
**어디로:** `.claude/rules/probes.md`: 인자로 받은 폴더를 지우는 프로브의 셋(절대 경로, 비었거나 표지가 있을 때만, 실패에서 멈춤)이 이미 있다. 이 사건은 그 항목이 실린 `paths`(`.scratch/**/probes/**`)의 `.sh` 파일을 새로 쓰는 자리에서 어겨졌다. 회차 5에서 셸 프로브를 쓸 때 그 항목을 짚는 계기 훅을 고른다(계기만 넣는 훅은 단계를 닫는 순간의 지침에 붙이는 길이 아니라 별도 판정이다)
**승인:** 자체 승인 2026-11-14, 2회차(0269의 2회차. 0269는 1회차로 닫혔다), 일지 2026-11-13-1843-release-image-spec.md. ADR 불필요

`strip-tests.sh`는 이미지 안의 사본에만 쓰려던 도우미였고 인자는 `Dockerfile`이 준 `/app/web/apps/widget`이었다. 그래도 `package.json` 확인 하나만 있어 저장소의 `web/apps/widget`을 주면 지워졌다. 이 세션은 절대 경로와 `.git` 조상 검사를 더하고, 임시 사본, 상대 경로, 저장소 폴더 세 갈래를 손으로 돌려 확인했다.
