# ds-upload-replacement-char-rejected: 디자인 시스템 올리기가 묶음 파일에 이스케이프 없이 든 U+FFFD 두 자리 때문에 Artifact 도구에 거부되어, 웹의 디자인 시스템에 마크다운 부품이 빠진 채다

**상태:** 열림
**어디로:** `web/tools/sync-design-system/assemble.ts`의 `libConfig`: 짓기 산출이 U+FFFD를 `�` 이스케이프로 쓰게 하고, `assemble.test.ts`에 그 글자가 산출에 그대로 들지 않는다는 시험을 더한 뒤 `/sync-design-system 올리기`를 다시 한다. 원인은 압축된 산출을 읽은 어림이라(원본 패키지를 대 보지 않았다) 고치기 전에 재현부터 한다
**승인:** 자체 승인 2026-11-13, 1회차, 일지 2026-11-13-0426-portal-login-ui-design.md. ADR 불필요

사건: `/sync-design-system 올리기`의 보내기를 Artifact 도구가 `_ds_bundle.js`의 U+FFFD를 들어 거부했다. 그 글자는 `_ds_bundle.js`와 `components/bundle.js`의 같은 두 자리에 있었고, 마크다운 해석 코드가 잘못된 문자 참조를 바꿔 쓰는 정상 코드로 읽었다. 아무것도 보내지 않았고 웹의 디자인 시스템은 2026-11-10에 올린 상태다. 도구의 버그라 사건 하나로 고친다. 사건이 난 PR은 기록만 실어 거기서 고치지 않았다.
