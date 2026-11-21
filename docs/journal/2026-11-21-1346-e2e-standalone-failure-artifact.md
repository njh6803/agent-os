# 단독 배포 e2e 실패 기록을 CI 산출물로 남긴다 (harness e2e-standalone-failure-artifact)

2026-11-21. 티켓: `.scratch/harness/issues/e2e-standalone-failure-artifact.md`. 브랜치 `chore/e2e-standalone-failure-artifact`.

## 왜

출시 PR #616(dev→main, 머리 `17fe2b169201a51d4d1a677dc7ffd24a66bf860f`)에서 `e2e-standalone`이 두 번 연속 빨갰다. 이 잡은 base가 main인 PR과 main 푸시에서만 시험하므로, dev로 간 티켓 PR(#615)의 초록은 이 시험을 돌린 결과가 아니었다.

> 사용자: 원인 찾기

> 사용자: 티켓 열기

## 손으로 본 것

- 이 PC에서 `pnpm -C web/packages/e2e-standalone exec playwright test`를 한 번 돌리니 14개가 모두 통과했다(4.8분). CI에서 빨갰던 시험 둘도 통과했다.
- CI에서 빨간 시험은 둘 다 최종 사용자가 `serve`에 질문하는 길을 지난다. 하나는 답이 5초 안에 화면에 뜨지 않았고, 다시 돌린 실행에서는 다른 하나가 프록시의 502를 받았다.
- `ci.yml`의 `e2e-standalone` 잡에는 실패 때 올리는 산출물이 없어서 `serve`·프록시·데이터베이스 로그를 볼 수 없다. 시험 틀은 끝날 때(teardown)와 준비 실패 때 `test-results/compose.log`를 쓰므로 올리기만 하면 된다(코드를 읽었다: `web/packages/e2e-standalone/e2e/stack.ts`). 잡이 20분 제한으로 끊기면 teardown이 안 돌아 그 파일이 없을 수 있다.

## 한 일

`ci.yml`의 `e2e-standalone` 잡 끝에 `if: failure() && steps.gate.outputs.run == 'true'`인 `actions/upload-artifact@v4` 스텝을 더했다(`visual` 잡과 같은 모양).

## 셀프 리뷰 (표준 축과 명세 축)

- 명세 축: 누락과 범위 넘침이 없었다. 새 스텝의 경로가 시험 틀이 로그를 쓰는 폴더와 같고, teardown이 `playwright test` 명령 안에서 끝나 스텝이 돌 때 `compose.log`가 이미 있음을 코드를 읽어 확인했다.
- 고친 것: 코드 주석에서 일회성 사건 이력("출시 PR 의 이 잡이 두 번 빨갰을 때")을 뺐다(사건은 티켓과 이 일지에 있다). "끝날 때마다 쓰고 Playwright도 실패 자료를 둔다"는 근거가 약해 teardown과 준비 실패 때 `compose.log`를 쓴다는 것으로 좁혔다(`playwright.config.ts`는 `trace: "off"`이고 화면 갈무리·영상 설정이 없다).
- 남긴 것: 수용 기준 셋째(pre-commit 초록)를 커밋 전에 닫은 것은 선례(`ci-compose-e2e-comment`)와 같은 방식이라 그대로 둔다. pre-commit이 실패하면 커밋이 만들어지지 않는다. `failure()`는 시험 앞 스텝의 실패에도 참이지만 그때는 폴더가 없어 올리기가 경고만 하고 넘어가며 `visual` 잡도 같은 조건이다.
- 비밀 노출: 저장소가 공개라 산출물이 내려받기 가능하다(`gh repo view`로 손으로 봤다). 시험이 만드는 관리·채널 토큰과 데이터베이스 비밀번호는 실행마다 새로 만든 무작위 값이고(`stack.ts`를 읽었다) 스택과 함께 버려지며, `src`에서 데이터베이스 주소를 로그로 찍는 곳은 찾지 못했다(Grep). 토큰을 로그에 싣지 않는다는 원칙 V를 지킨다고 보지만 서버 로그 전체를 읽어 확인하지는 않았다. 첫 산출물이 올라오면 한 번 열어 본다.
- 5초: "답이 5초 안에 뜨지 않았다"는 CI 로그의 5000ms 시간 초과를 본 것(손으로 본 것)이고 e2e 코드에서 그 값의 자리는 찾아 확인하지 않았다.

## 회고

후보 셋: 승인 1, 기각 2, 넘김 0. 사용자에게 넘긴 것은 없다. 만료할 대기열 항목도 없다(`tools/queue_open_rows.py`의 "만료할 항목"이 없음).

- **단독 배포 e2e가 실패 때 기록을 남기지 않는다(정보 접근): 승인, 이 PR에서 반영.** 사건: 출시 PR #616의 `e2e-standalone`이 두 번 빨갰는데 CI에 `serve`·프록시 로그가 없어 원인을 가르지 못했다. 층: CI 설정이다(`visual` 잡이 쓰는 `if: failure()` 산출물 올리기와 같은 모양). 되돌림: PR 하나. 고침에 해당해 사건 하나로 반영했고 이 PR의 티켓 자체가 그 반영이라 대기열 항목은 쓰지 않는다.
- **같은 커밋이 dev에서 초록이었으니 CI 변덕일 것이라 어림한 것: 기각.** 사건은 있었다(어림을 사용자에게 먼저 말했다). 그러나 `ci.yml`의 이 잡 주석이 base가 main일 때만 시험한다고 이미 적었고(ADR 0043), 그 주석을 읽자 바로 정정했다. 손상이 없고 자동 검사로 잡을 모양도 아니다.
- **관리 화면·위젯·위젯 테스트 페이지 e2e 잡도 실패 기록을 올리지 않는다: 기각.** 사건 없이 떠올린 것이다. 그 잡들이 실제로 원인 불명으로 빨간 일이 생기면 그때 이 PR과 같은 고침으로 센다.

## 다음

- 이 PR이 dev에 병합되면 #616의 머리가 바뀌어 `e2e-standalone`이 다시 돈다. 다시 빨가면 산출물 `e2e-standalone-test-results`의 `compose.log`를 읽어 원인(느린 첫 응답인지, `serve` 종료인지, 프록시 문제인지)을 가른다. 그 전까지 원인은 어림도 못 정했다(실행기가 느려서일 수 있다는 가설은 확인하지 못했다).
- 원인을 고치는 일은 산출물을 읽은 뒤 따로 티켓을 연다.
- #616은 병합하지 않았다. `e2e-standalone`과 `verify`가 초록이어야 한다.
