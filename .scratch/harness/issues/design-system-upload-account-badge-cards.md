# design-system-upload-account-badge-cards: 디자인 시스템 올리기가 늘린 지난 산출 목록을 싣는다

**What to build:** admin-login 08(PR 646)이 디자인 시스템에 아이콘 일곱과 계정 상태 배지(`AccountStatusBadge`)를 더했고, 병합 뒤 `sync-design-system 올리기`로 아티팩트에 올렸다(2026-11-25 18:34 UTC, 아티팩트 판 45). 그 올리기의 산출 목록(`output-paths.json`)에는 지난 산출 목록(`web/tools/sync-design-system/previous-output.json`)에 없던 경로 둘이 있다: `project/components/AccountStatusBadge/README.md`와 `project/components/AccountStatusBadge/preview.html`. 목록을 그 산출로 바꾸지 않으면 다음에 이 카드가 코드에서 빠질 때 올리기가 아티팩트의 그 파일을 지우지 못한다(`upload.md` 6의 6 "목록 갱신과 돌아가기"). 그 목록은 커밋 검사의 면제 모양이 아니라서 티켓을 가리키는 브랜치에만 실리므로, 이 일을 하나뿐인 harness 티켓으로 쓴다.

함께 admin-login 08 티켓의 올리기 칸을 닫는다(기능 디렉터리의 티켓은 커밋 검사의 면제 모양이다).

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `web/tools/sync-design-system/previous-output.json`이 올리기가 낸 `output-paths.json`과 같다(새 경로 둘 말고 빠진 경로는 없다)
- [x] `.scratch/admin-login/issues/08-design-system-icons-and-account-badge.md`의 올리기 칸이 닫혀 있고, 올린 판과 확인 결과가 적혀 있다
- [x] 일지 `docs/journal/2026-11-26-0144-admin-login-ticket-08.md`에 올리기 결과와 못 본 것(카드 확인)이 적혀 있다
