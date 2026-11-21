# e2e-standalone-failure-artifact: 단독 배포 e2e가 실패하면 컨테이너 기록을 CI 산출물로 남긴다

**What to build:** CI의 `e2e-standalone` 잡은 실패해도 기록을 하나도 남기지 않는다. 시험 틀(`web/packages/e2e-standalone/e2e/stack.ts`)은 끝날 때(teardown)와 준비가 실패했을 때 `docker compose logs`를 `web/packages/e2e-standalone/test-results/compose.log`에 쓰지만, 잡이 그 폴더를 올리지 않아 실행기가 사라지면 함께 사라진다. 출시 PR(dev→main)에서 이 잡이 두 번 연속 빨갰다(최종 사용자 질문 길의 시험 두 개: 답이 5초 안에 뜨지 않았고, 한 번은 프록시가 502를 돌려줬다). 같은 시험은 이 PC에서 14개 모두 통과했고, CI에는 `serve`·프록시·PostgreSQL의 로그가 없어서 원인을 가르지 못했다(손으로 본 것: `gh run view` 로그와 `ci.yml`, 이 PC에서 `pnpm -C web/packages/e2e-standalone exec playwright test` 한 번). 그래서 `visual` 잡이 이미 쓰는 방식(`if: failure()`의 `actions/upload-artifact@v4`)으로 `test-results/`를 실패 때만 올리는 스텝을 `e2e-standalone` 잡에 더한다. 시험 스텝이 실패했을 때만 올리고 게이트가 건너뛴 실행(`run=false`)에서는 올리지 않는다. 잡의 시험 동작과 트리거는 바꾸지 않는다. 원인을 고치는 일은 이 티켓이 아니라 산출물을 읽은 뒤 따로 연다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `ci.yml`의 `e2e-standalone` 잡 마지막에 `if: failure() && steps.gate.outputs.run == 'true'`인 `actions/upload-artifact@v4` 스텝이 있고, `web/packages/e2e-standalone/test-results/`를 이름 `e2e-standalone-test-results`, 보존 14일로 올린다(`visual` 잡의 스텝과 같은 모양)
- [x] 새 스텝 앞의 주석이 실패 때 기록을 올린다는 것과 `compose.log`가 든다는 것을 적는다
- [x] 워크플로 감사(zizmor)와 커밋의 pre-commit이 초록이다 (커밋의 pre-commit 결과)

병합 뒤에는 출시 PR #616의 e2e-standalone 실행에서 실패 산출물이 올라오는지 본다. 올라오면 그 산출물에서 원인을 읽고 고침 티켓을 따로 연다(이 티켓의 범위 밖이다).
