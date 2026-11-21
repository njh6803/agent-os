# e2e-standalone-proxy-serve-resolve: 프록시가 serve 를 못 찾고 시작해도 serve 가 뜨면 곧 길을 연다

**What to build:** 출시 PR #616(dev→main)의 `e2e-standalone` 잡이 네 번째로 빨갰다(머리 `8013ab530`, 실행 44915085235). 앞선 티켓(`e2e-standalone-token-rate-limit`, PR #620)이 올린 `compose-at-failure.log`가 처음으로 실패한 시험 바로 뒤의 로그를 남겼다. 실패한 시험은 둘이고 둘 다 최종 사용자 길(`POST /end-user/runs`)을 지난다. 하나는 "고지를 확인한 최종 사용자의 질문에 모델 없는 에이전트가 프록시, 위젯, serve 를 지나 답한다", 다른 하나는 "네트워크 없는 MCP 실행: 계산 에이전트의 실행이 도구 연결이 아니라 모델 호출에서 끝난다"다. 둘 다 프록시가 502를 냈다.

산출물의 `compose-at-failure.log`에서 손으로 읽은 시간표는 다음과 같다(같은 컨테이너 묶음의 로그이고 시각은 14:42~14:43 UTC다).

- 14:42:44.89 프록시가 떴고, 0.01초 뒤 `serve could not be resolved (2: Server failure)`를 한 번 남겼다. 이 줄은 그 뒤로 다시 나오지 않았다.
- 14:42:56 `serve`의 시작이 끝났고(`Application startup complete.`), 14:42:57에 `/health`가 200이었다. `serve`는 `postgres`와 `migrate`를 기다려서 프록시보다 12초쯤 늦게 떴다.
- 14:43:01.586 첫 시험의 `POST /end-user/runs`가 502였다. 프록시 오류 줄은 `no live upstreams while connecting to upstream ... upstream: "http://up_serve/end-user/runs"`다. 14:43:11.309 둘째 시험도 같은 줄과 같은 502였다. 같은 때 포털과 위젯의 화면 요청(`/portal/`, `/widget/`)은 200이었고(경로 우회를 시험하는 요청의 404는 설계된 응답이다), `serve`의 로그에는 두 요청이 없다. 요청이 `serve`까지 가지 못했다.

곧 프록시는 시작할 때 `serve` 이름을 못 풀었고, `serve`가 이미 건강해진 뒤 4초와 14초(`/health` 200 기준. 프록시가 뜬 지 16초와 26초)가 지나도 다시 풀지 못했다. `deploy/standalone/proxy/site.conf`는 `resolver 127.0.0.11 valid=5s`와 `server serve:8000 resolve`로 5초마다 다시 풀기를 기대하는데도 그렇다.

**원인(손으로 가른 것).** 아래 실험에서 프록시는 이름 풀기에 실패한 뒤 다시 시도하기까지 `resolver_timeout`(기본값 30초)만큼 기다렸다. `valid=5s`는 풀기에 성공한 답의 유효 시간에만 걸리는 것으로 보인다. CI의 두 실패는 프록시가 뜬 뒤 16초와 26초 지점이라 30초 안이다. 그래서 둘 다 502였다. `compose.yaml`의 프록시에는 `depends_on`이 없어 `serve`보다 먼저 뜨는 것이 설계된 순서이고, `serve`는 `postgres`와 `migrate`를 기다리느라 늦게 뜬다. 앞선 두 번의 실패(일지 `2026-11-21-1346-e2e-standalone-failure-artifact`)에서 하나가 프록시의 502였던 것도 같은 길일 수 있다. 앞 일지(`2026-11-21-1935-e2e-standalone-token-rate-limit`)는 그 산출물에서 `serve could not be resolved (2: Server failure)`를 봤으나, 그 순간의 로그가 남지 않아 502와 잇지 못했다.

이 티켓은 시작 순서가 어긋나도 프록시가 `serve`를 곧 따라가게 고친다. 순서는 시험 먼저(회귀 시험이 지금 빨갛다), 고치기, 확인이다.

1. **회귀 시험.** `web/packages/e2e-standalone/e2e/deployment.e2e.ts`에 사례를 더한다. `serve`를 지우고 프록시를 다시 만들되, 프록시의 바깥 DNS를 끊는 시험 전용 덧씌움(`compose.dead-dns.yaml`)을 얹어 CI의 `Server failure`를 만든다. 프록시 로그에 그 오류가 찍힌 것을 확인한 뒤 `serve`를 올리고, `serve`가 건강해진 때부터 15초(`RECOVER_MS`) 안에 `POST /end-user/runs`가 502가 아니기를 기대한다. 끝나면 프록시를 덧씌움 없이 다시 만든다.
2. **고치기.** `site.conf`에 `resolver_timeout 2s;`를 더한다. 이름 풀기에 실패한 프록시가 2초마다 다시 시도한다.
3. **확인.** 이 PC에서 단독 배포 e2e가 모두 통과한다.

범위 밖이다. 출시 PR #616의 병합은 이 티켓이 아니라 출시 절차(`next-session`의 `merge.md` "출시 PR")가 맡는다. `compose.yaml`에 `depends_on`을 더해 프록시가 `serve`를 기다리게 하는 길은 고르지 않았다. 프록시가 먼저 떠 있어야 `serve`의 시작이 늦거나 다시 시작할 때도 같은 일이 되풀이되지 않고, 이 모양은 운영자가 고치지 않는 파일이라 바꾸는 값이 크다. 이 판단이 틀렸다고 드러나면 새 티켓을 쓴다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 회귀 시험을 쓰고, 고치기 전에 이 PC에서 빨갛다는 것을 본다(고치기 전에 그 사례만 돌려 29.9초 만에 "serve 가 건강해진 뒤 15000ms 안에 프록시가 길을 열지 않았다"로 실패했다. 프록시 로그에 `Server failure`가 있어야 한다는 선행 단언은 통과했고 마지막 상태가 502였다)
- [x] `site.conf`에 `resolver_timeout 2s;`를 더하고 회귀 시험이 초록이다(전체를 돌린 가운데 이 사례가 13.6초에 통과했다)
- [x] 이 PC에서 `pnpm -C web/packages/e2e-standalone exec playwright test`가 모두 통과한다(15개, 2.5분)
- [x] 검증 명령이 모두 초록이다(`CLAUDE.md`의 손으로 치는 명령 전부와 위에서 건드린 길의 e2e. `pnpm -C web verify`는 테스트 2777개 통과, 나머지 넷은 커밋의 pre-commit이 갈음한다. 셀프 리뷰 뒤 새 사례를 다시 돌려 22.2초에 통과했다)
- [ ] 이 티켓을 병합한 뒤 출시 PR #616의 `e2e-standalone`과 `verify`가 초록이 되는지 본다(초록이 아니면 새 산출물의 `compose-at-failure.log`를 읽고 이 티켓을 잇는 새 티켓을 쓴다. 병합 뒤의 일이라 일지의 "다음"이 맡는다)

## 근거

로그와 실험 모두 이 세션이 손으로 읽고 돌린 것이다. 커밋한 프로브가 아니므로 "쟀다"가 아니라 "손으로 봤다"로 적는다. 실험을 한 번씩만 돌렸고, 재시도 간격이 `resolver_timeout`이라는 설명은 그 한 쌍의 결과에서 세운 것이지 nginx 소스를 읽어 확인한 것이 아니다.

**CI의 로그.** 위 시간표는 실행 44915085235의 산출물 `e2e-standalone-test-results`에 든 두 시험의 `compose-at-failure.log`다. 산출물은 저장소에 없다. 비밀값은 로그에 없었다.

**손으로 돌린 실험(이 PC, Docker 29.9.2, 프록시 이미지는 `compose.yaml`이 고정한 nginx 1.30.6).** 프록시만 `serve`가 없는 네트워크에 띄우고 `--dns 127.0.0.2`로 바깥 DNS를 끊었다. Docker의 내장 DNS는 자기가 모르는 이름을 바깥 DNS에 넘기는데, 바깥이 막혀 있으면 `Server failure`를 돌려준다. 프록시 설정은 `site.conf`의 `resolver`와 `upstream`(`zone`, `resolve`) 부분만 옮긴 것이다. 1초마다 요청을 보내는 감시 컨테이너(같은 이미지의 `wget`)를 옆에 두고, 프록시를 띄운 지 13초(첫째 실행)와 11초(둘째 실행) 뒤에 이름이 `serve`인 컨테이너를 띄웠다.

| 설정 | 프록시의 이름 풀기 오류 | `serve` 시작 | 첫 200 |
|---|---|---|---|
| 지금(`resolver_timeout` 없음) | 16:54:34 | 16:54:47 | 16:55:04(오류 뒤 30초) |
| `resolver_timeout 2s` | 16:55:59, 16:56:01, 16:56:03 … 2초마다 | 16:56:10 | 16:56:12(감시 기록이 초 단위라 시작 뒤 1초에서 3초 사이) |

시작 직후의 오류 줄(`serve could not be resolved (2: Server failure)`)과 이어진 `no live upstreams` 502는 CI 로그와 글자 그대로 같았다. 실험 컨테이너와 네트워크는 지웠다.

**앞선 프로브가 어림으로 적어 둔 것.** `.scratch/release-image/probes/bridge_recover/README.md`의 마지막 쪽(바깥 DNS에 닿지 않는 서버)이 "바깥 DNS가 없는 서버에서는 (나)·(다)의 그 502가 더 늦거나 nginx `resolver_timeout`(기본 30초, 어림)까지 매달릴 수 있다"고 적었다. 이번 실험이 그 어림을 손으로 확인한 셈이다(어림이었고 그때는 재지 않았다).

**아직 모르는 것.** CI 러너에서 왜 `Server failure`가 났는지(바깥 DNS가 막혔는지, 러너의 DNS 설정이 다른지)는 보지 못했다. 이 PC의 평소 Docker에서는 같은 실패가 나지 않아 14개 시험이 모두 통과했다. 실험의 `--dns 127.0.0.2`는 그 실패를 흉내 낸 것이다.

**회귀 시험의 한계(코드를 읽은 것).** 시험이 고치기 전에 빨갛려면 프록시가 뜬 뒤 `serve`가 건강해지기까지의 시간이 15초보다 짧아야 한다(고치기 전 프록시는 30초 뒤에야 다시 푼다). 시험은 `--no-deps`로 `serve`만 올려 CI의 약 12초보다 짧을 것이라고 보았지만 그 시간을 재서 적지는 않았다. 고치기 전에 한 번 돌려 빨간 것(29.9초)이 그 한 번의 증거다. 또 시험의 선행 단언은 `Server failure`가 찍혀야 하므로, 다른 Docker에서 이름 풀기가 `Server failure`가 아닌 답(없는 이름, 시간 초과)으로 나오면 시험이 선행 단언에서 크게 실패한다(조용히 틀리지는 않는다). 바깥 DNS가 닿지만 답이 느린 경우(앞선 프로브가 내장 DNS가 "없다"고 답하기까지 3.3초 걸렸다고 적었다)는 덧씌움이 즉시 거절이라 재현하지 못하고, 그 경우를 `resolver_timeout 2s`가 어떻게 받는지는 보지 않았다.
