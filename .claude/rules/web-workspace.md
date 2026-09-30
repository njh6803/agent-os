---
paths:
  - "web/**"
---

# web 워크스페이스 규칙

원칙 III의 금지 목록, 층 경계, 금지 구문, 전역 `fetch`, 아이콘 import는 판정자 `web/eslint.config.mjs`가 판정하고, tsconfig의 strict 계열은 `web/tools/check-tsconfig.ts`가 본다. 여기 다시 적지 않는다. 아래는 그것들이 판정하지 못하는 판단 기준이다(ADR 0020·0021). 관리 화면 앱에만 걸리는 것은 앱의 규칙에 둔다.

- templates는 슬롯만 받는다. 데이터를 가져와 채우는 것은 pages다.
- 서버 데이터를 스토어(Zustand)에 복사하지 않는다. 서버 데이터는 SWR이 들고, 스토어는 클라이언트 상태만 든다.
- `isLoading`(처음 가져오는 중, 스켈레톤)과 `isValidating`(이미 보인 값을 다시 확인하는 중, 작은 표시)을 가른다. 다시 확인하는 동안 보인 것을 지우지 않는다.
- TS 테스트의 이름은 행동을 말하는 한국어 문장이다.
- ESLint 규칙을 더하거나 넓히면 경로와 무관하게 쓴다. 앱이 `app/`을 쓰든 `src/app/`을 쓰든 걸려야 한다. 그리고 `web/eslint.config.test.ts`에 위반을 만들어 넣는 사례와 지나보내야 할 사례를 붙인다. 사례는 "빨갛다"가 아니라 기대한 규칙 ID를 본다. 어느 tsconfig에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다.
- 판정자의 범위에서 빼는 목록(`ignores`, 글롭의 제외)을 두지 않는다. 커밋하는 생성물도 판정한다. 빠지는 것은 저장소 `.gitignore`가 무시하는 빌드 산출물뿐이고, 판정자와 Prettier가 그 파일을 그대로 읽는다(ADR 0020의 2026-09-30 이력). 경로마다 규칙을 다르게 둘 정당한 예외는 설정 파일에 경로와 이유를 함께 적어 리뷰에 diff로 보이게 한다.
- 새 tsconfig는 `web/tsconfig.base.json`을 extends 한다. 앱의 tsconfig에 extends도 strict도 없으면 Next가 `"strict": false`를 써 넣는다.
