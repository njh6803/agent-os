# ci-compose-e2e-comment: ci.yml 머리 주석이 compose e2e 잡을 더할 티켓을 ADR 이력대로 가리킨다

**What to build:** `.github/workflows/ci.yml`의 머리 주석은 실제 이미지의 compose e2e 잡을 "release-image 의 첫 티켓이 Dockerfile·compose 와 함께 더한다(ADR 0056)"라고 적었다. release-image 명세(`.scratch/release-image/spec.md` "티켓을 나눌 때 함께 둘 것")는 이미지 넷을 짓는 티켓을 네 프로세스의 예외를 들이는 티켓 뒤에 두어, 그 잡을 Dockerfile과 compose 파일·프록시 설정이 모두 갖춰지는 티켓이 싣게 했다. 그 결정은 ADR 0056 이력 2026-11-14 "실제 이미지의 compose e2e 잡은 Dockerfile과 compose를 갖추는 티켓이 더한다"에 쌓였다. 그래서 그 주석 한 줄이 거짓이 되어 이력과 맞게 고친다. 주석만 고치고 잡과 트리거는 바꾸지 않는다. 이 PR은 release-image 명세를 쓰는 면제 PR(`docs/release-image-spec`)이고, 이 티켓은 그 가운데 면제 모양이 아닌 ci.yml의 주석 고침만 맡는다(`tools/check_ticket.py` 판정 6, 선례 harness 009).

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] ci.yml 머리 주석이 compose e2e 잡을 더하는 티켓을 "Dockerfile·compose 를 갖추는 release-image 의 티켓"으로 적고 ADR 0056 이력 2026-11-14를 가리킨다
- [x] 옛 표현("첫 티켓이 Dockerfile", "release-image의 첫 티켓")을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0이다. ADR 0056 본문의 두 문장은 그 이력을 가리키는 포인터를 달았고, 같은 말이 든 done인 harness 티켓 둘(`dev-branch-create`, `dev-branch-transition`)은 기록이다(`docs/constitution/operations.md` 문서 위치)
- [x] 검증 명령이 모두 초록이다 (커밋의 pre-commit, 일지 2026-11-13-1843)
