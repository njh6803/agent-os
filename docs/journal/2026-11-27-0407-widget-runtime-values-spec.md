# 2026-11-27 (04:07) widget-runtime-values 명세

세션 제목 `docs/widget-runtime-values-spec`. 브랜치 `docs/widget-runtime-values-spec`, 워크트리 `.claude/worktrees/widget-runtime-values-spec`. 모델 Fable 5.2. 기준은 `origin/dev` `e7c53cba3`다. 파일 이름의 시각은 이 일지를 처음 만든 때(사용자에게 물은 것 하나의 답을 받은 직후)다.

## 사용자 프롬프트

세션의 첫 메시지는 next-session 지시문을 붙여 넣은 글 하나였다.

> 사용자: .claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: widget-runtime-values
>
> 다음 작업: 기능 widget-runtime-values. 위젯 이미지를 미리 지어 두고 컨테이너가 뜰 때 사이트 파일의 허용 출처와 요청 글자 수 상한만 받게 해, 뜰 때마다 하던 빌드를 없앤다.
> 다음 단계: 명세
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다.
> 시작 프롬프트: /to-spec widget-runtime-values
> 브랜치: docs/widget-runtime-values-spec
> 모델: Fable 5.2 / xhigh. 결정표의 칸은 Fable 5.1이지만 지금 모델 메뉴에 없어 열 때 고를 수 있는 이름으로 적었다(대기열 model-menu-name-fable-5-1-stale의 임시 규칙).
> 읽을 것: 없음
> 이어받을 상태: 이 명세 세션의 일은 아니지만 알린다. admin-login 05(PR #653)의 봇 보류 하나가 병합된 일지 "다음"에 없고 PR 코멘트(issuecomment-7199113820)에만 있다. 관리 라우터의 public에 /health 외의 라우트가 붙는 것을 막는 시험이 없다는 지적이다. admin-login을 잇는 다음 세션이 이어받는다.
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다.
> 이번 요청 범위: PR과 병합까지

## 사용자에게 물은 것 하나: 시험의 이음매

측정(아래 "명세 전의 확인")이 끝난 뒤 물었다. 질문은 글자 그대로 아래와 같다.

> 위젯이 '빌드 없이 뜨고, 뜰 때 사이트 파일의 두 값을 받는다'를 지키는 자동 시험을 어디에 둘까요? (측정에서는 미리 지은 위젯 이미지가 약 1초 만에 떴고 메모리는 약 90MiB였습니다)

첫 호출은 `hook_choice_facts`가 막았다(이 세션의 첫 선택 화면은 설명의 사실을 코드에 대 보라고 막는다). 설명의 사실 셋을 대 본 뒤 같은 질문과 라벨로 다시 올렸다. 대 본 것은 약 1초와 약 90MiB가 측정의 범위 안인지(아래 절의 표), 단독 배포 e2e 잡이 main으로 가는 PR과 main 푸시에서만 시험을 돌리는지, 위젯 e2e 잡에는 그런 문이 없는지다(뒤의 둘은 `.github/workflows/ci.yml`의 `e2e-standalone` 잡의 `gate` 단계와 `e2e-widget` 잡을 읽었다). 새 잡이 PR마다 더 쓰는 시간은 재지 않아 설명에 어림이라고 적었다.

사용자가 고른 것은 **"있는 시험 넷에 더하기 (Recommended)"**이고, 그 설명은 글자 그대로 아래와 같다.

> 새 시험 틀을 만들지 않습니다. ① 실제 이미지를 통째로 띄우는 시험에 '빌드 없이 뜬다, 허용한 사이트만 위젯을 품는다, 글자 수 상한을 바꾸고 다시 띄우면 따른다'를 더합니다. 이 시험은 CI에서 main으로 가는 PR(출시 PR과 핫픽스) 때만 돌고, 이미지를 고친 티켓은 이 PC에서 돌립니다(CI 설정을 읽어 확인했습니다). ② 모든 PR에서 도는 위젯 브라우저 시험도 '뜰 때 값 받기'를 거치게 바꿔서, Next 판을 올렸을 때 깨지는 것을 평소 PR에서 잡습니다. ③④ 시작 스크립트와 위젯 화면의 작은 시험에는 세부 사례를 둡니다.

고르지 않은 선택지는 둘이다.

- "평소 PR에도 이미지 시험": "첫째 안에 더해, 위젯 이미지를 실제로 지어 띄우는 시험을 모든 PR의 CI에서 돌리는 잡을 새로 만듭니다. 이미지가 깨진 것을 출시 전에 일찍 알 수 있지만, PR마다 이미지를 짓는 시간이 더 들고(몇 분으로 어림합니다. CI에서 재지는 않았습니다) CI 잡이 하나 늘어납니다."
- "이미지 시험 하나에만": "실제 이미지를 통째로 띄우는 시험 하나에만 사례를 둡니다. 가장 단순하지만, 그 시험은 CI에서 main으로 가는 PR 때만 돌기 때문에 Next 판을 올려서 깨진 것을 출시 직전에야 알게 됩니다."

이 화면으로 확인받은 요약: 명세의 Testing Decisions는 새 이음매 없이 있는 이음매 넷을 쓴다. 단독 배포 e2e(실제 이미지 넷과 프록시)에 기능 계획의 수락 셋을 사례로 더하고, 위젯 e2e가 빌드는 사이트 파일 없이 하고 띄울 때 사이트 파일을 주게 바꿔 Next의 판을 올리는 PR이 그 시험을 지나게 하며, 시작 래퍼의 시험과 위젯의 브라우저 쪽 단위 시험에 세부 사례를 둔다.

## 시작할 때 본 것

- 지시문대로 `tidy-checkouts`를 먼저 돌았고, 주 체크아웃(dev)이 `e0e697425`에서 `e7c53cba3`으로 당겨졌다(이 세션의 전사 기록에 남은 `Updating e0e697425..e7c53cba3`과 `Fast-forward`를 읽었다). 그 스킬이 지우거나 남긴 워크트리의 목록은 이 절을 쓰는 때의 컨텍스트에 남아 있지 않아 옮기지 않는다.
- 그 뒤 `EnterWorktree`로 워크트리 `.claude/worktrees/widget-runtime-values-spec`에 들어가 브랜치 `docs/widget-runtime-values-spec`으로 바꿨다. 기준은 `origin/dev` `e7c53cba3`이다.
- 설계는 ADR 0064 결정 "허용 출처와 요청 글자 수 상한"이 이미 정했다. 기능 계획의 `**설계:**` 줄이 그 ADR을 가리키므로 설계 인터뷰를 다시 열지 않았다.

## 명세 전의 확인

기능 계획이 이 행의 첫 일로 둔 확인이다. ADR 0064는 "미리 짓고 뜰 때 값만 바꿔 넣는" 조합을 리눅스 컨테이너에서 끝까지 돌려 본 적이 없다고 적었고, 서지 않으면 그 결정으로 돌아가 사용자에게 다시 묻기로 했다. 그래서 명세를 쓰기 전에 프로브 `.scratch/widget-runtime-values/probes/prebuilt_start/`를 지어 쟀다. 시제품 이미지(`Dockerfile`)와 시제품 진입 단계(`entry.mjs`)는 측정용이고 구현이 아니다.

조합은 섰고, 그 결정으로 돌아가 다시 물을 것이 없었다. 아래 표의 "쟀다"는 그 프로브(`.scratch/widget-runtime-values/probes/prebuilt_start/run.py`)가 그 회차의 표지를 단언한 것이고, 괄호의 "결과 N"은 그 폴더 `README.md`의 "결과" 절의 번호다. 세 실행의 53회차가 모두 표지를 본 회차였다(실행 1은 `health`를 뺀 여섯 섹션 32회차, 실행 2는 `readonly,sitefile` 10회차, 실행 3은 `readonly,health` 11회차). 환경은 이 PC(Windows 10)의 Docker Desktop이고 리눅스 호스트의 Docker Engine이 아니다.

| 본 것 | 결과 | 근거 |
|---|---|---|
| 빌드 없이 서는가 | 사이트 파일 A로 띄운 일곱 회차가 모두 A의 두 값을 냈다. 컨테이너 시작부터 첫 200까지 0.62~1.78초(시간을 찍은 스물네 회차) | 쟀다(`probes/prebuilt_start` 결과 2) |
| 메모리 | 뜬 직후의 최고치가 제한 없는 스물세 회차에서 88.9~94.3MiB, CPU 하나와 256MiB로 제한한 한 회차에서 78.3MiB | 쟀다(`probes/prebuilt_start` 결과 2). 오래 띄운 값이 아니다 |
| 사이트 파일을 바꾸고 다시 띄우기 | 일곱 회차 모두 응답 머리와 값 파일이 새 값이 됐다 | 쟀다(`probes/prebuilt_start` 결과 3) |
| 읽기 전용 루트 | 쓰는 폴더 하나를 tmpfs로 주면 섰다(아홉 회차와 읽기 전용만 건 한 회차). tmpfs를 빼거나 링크 없는 이미지를 쓰면 `EROFS`로 끝났다 | 쟀다(`probes/prebuilt_start` 결과 4) |
| 사이트 파일이 없거나 깨졌을 때 | 진단을 찍고 Next를 부르지 않은 채 종료 1 | 쟀다(`probes/prebuilt_start` 결과 5) |
| 진입 단계를 건너뛰었을 때 | 링크를 둔 이미지에서는 Next가 응답 머리 목록을 열지 못해(`ENOENT`) 종료 1 | 쟀다(`probes/prebuilt_start` 결과 5) |
| 상태 확인 | 시작 유예 30초 옵션으로 세 회차 모두 2.61~2.66초에 healthy. 아무도 듣지 않는 포트에 건 대조는 25초 동안 starting | 쟀다(`probes/prebuilt_start` 결과 6) |
| 브라우저 | Chromium에서 허용 출처의 페이지가 품은 틀에만 위젯 문서가 실렸고, 사이트 파일을 바꾸고 다시 띄우자 뒤바뀌었다. 다른 출처의 문서가 값 파일을 읽었다 | 쟀다(`probes/prebuilt_start` 결과 7) |
| 이미지 크기 | 시제품 이미지 690.6MiB. 지금의 위젯 이미지 874.3MiB는 release-image 명세의 "이미지의 구성"에서 읽은 값이다 | 쟀다(`probes/prebuilt_start` 결과 1) |
| 이미지를 지을 때의 빌드 | 캐시 없이 64.2초와 73.8초 | 앞의 것은 손으로 친 `docker build`의 기록에서 봤고, 뒤의 것은 프로브의 첫 실행에서 봤다(`probes/prebuilt_start` 결과 1) |

재지 못한 것은 프로브 README의 같은 이름의 절에 있다. 리눅스 호스트의 Docker Engine, 호스트 폴더를 붙이는 바인드 마운트, 프록시를 거친 요청, 위젯의 코드가 값 파일을 받아 쓰는 것, 시작 래퍼의 루프백 검사, Next의 다른 판, Chromium 밖의 브라우저, 오래 띄운 컨테이너의 메모리다.

결과를 본 뒤 바꾼 것은 셋이고 프로브 README의 "결과를 본 뒤 바꾼 것"에 적었다.

- 깔린 패키지를 보는 방법. 첫 판은 패키지의 `package.json`을 `require`로 풀었는데, `@tailwindcss/vite`가 그 파일을 내보내지 않아 깔려 있어도 실패했다. 그대로였다면 이미지에 그 패키지가 있었어도 "없다"가 나왔을 것이다. 파일이 있는지를 보게 바꾸고 전체 의존성 단계를 대조로 뒀다.
- 서지 않는 회차의 결과 이름과 표지. 다섯 회차에 이름 하나를 붙였던 것을 회차마다 가르고, 표지를 오류 번호와 파일 이름으로 좁혔다.
- 더한 회차. 읽기 전용 하나만 건 회차와 상태 확인 섹션은 첫 전체 실행 뒤에 더했다.

프로브 README를 쓴 뒤 숫자를 원본 기록(`results.jsonl`, `raw.log`)과 다시 대 보니 셋이 틀려 있었다. 시간을 찍은 회차를 스물여섯으로, 다시 띄운 회차를 여섯으로, 읽기 전용 회차의 메모리 범위를 91.3~94.3MiB로 적었던 것이다. 스크래치 스크립트와 Grep으로 다시 세어 스물넷, 일곱, 89.1~94.3MiB로 고쳤고 문장마다 어느 실행의 회차인지를 밝혔다. 걸린 시간의 "약 35초"는 잰 값이 아니어서 빼고 `raw.log`의 처음과 끝 시각으로 본 53초로 바꿨다.

## 명세가 정한 것

명세 `.scratch/widget-runtime-values/spec.md`는 ADR 0064가 명세에 넘긴 자리를 채웠고 결정을 바꾸지 않았다. 그래서 ADR 이력을 쌓지 않았다(까닭은 명세 서두의 "이력"). 절 머리에 "명세가 정했다"로 표시한 것은 열이다.

- 값 파일: 위젯이 내주는 공개 파일 `/widget/runtime.json`, 키 둘(`allowedOrigins`, `requestChars`)의 JSON, 판 표시 없음, 누구나 읽는 응답 머리, 캐시는 Next가 다는 그대로.
- 품어도 되는 사이트를 알리는 응답 머리: 빌드는 늘 `'none'`으로 짓고, 지어 둔 응답 머리 목록의 원본을 남겨 뜰 때마다 원본에서 새로 만든다. 바꿀 자리가 정확히 하나이고 값이 `'none'`일 때만 바꾸며 아니면 뜨지 않는다.
- 합친 허용 출처와 가장 작은 상한을 지금처럼 쓴다.
- 시작 래퍼의 세 명령이 사이트 파일을 읽는 때(빌드는 읽지 않고, 서비스 시작과 개발 서버가 읽는다).
- 사이트 파일이 없거나 깨졌을 때의 진단과 종료 1, 진단의 끝 문장을 "다시 띄운다"로.
- 브라우저 쪽이 값을 받는 길: 읽는 자리 하나, 받는 동안 입력 막기, 받지 못하면 지금의 설정 오류 알림.
- 위젯 이미지: 운영 의존성과 산출물만 담고, 뜰 때 쓰는 두 파일은 `/run/agent-os-widget`로 가는 링크.
- 단독 compose의 위젯: 읽기 전용 루트와 tmpfs 하나, 시작 유예 30초, 메모리 제한은 두지 않음.
- 배포 안내에서 고칠 문장 넷.
- 티켓을 나눌 때 함께 둘 것(코드가 먼저, 이미지와 compose는 한 티켓).

사용자에게 따로 묻지 않고 명세가 정한 판단 가운데 무게가 있는 것은 둘이다. 하나는 값 파일을 받지 못한 위젯이 기본 상한으로 열리지 않고 닫힌 채 설정 오류 알림을 보이는 것이다. ADR 0024가 위젯 설정이 틀렸을 때 닫는 쪽을 이미 정했고, iframe 방식은 허용 출처 없이는 토큰을 물을 수 없어 어차피 닫혀야 해서 새 결정이 아니라고 봤다. 새 화면 요소와 새 문구가 없어 화면 디자인 단계도 두지 않았다. 다른 하나는 compose의 위젯에 메모리 제한 값을 두지 않는 것이다. 제한을 걸고 잰 회차가 하나뿐이고 오래 띄운 메모리를 재지 않아 값을 고를 근거가 모자란다.

다른 기능에 넘긴 것은 받는 쪽 기능 계획 본문에 적었다. `.scratch/site-limits-admin/plan.md`에는 위젯이 값을 받는 자리와 모양, 그리고 그 설계가 정할 것 넷을 적었다. `.scratch/deploy-package/plan.md`에는 메모리 문장이 이 기능 뒤에 맞지 않는다는 것과 새 값, 통합 배포가 따를 것 셋, 그 설계가 볼 것 둘을 적었다. `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다(표는 계획의 머리 줄과 티켓에서 만들어지고 본문은 싣지 않는다).

## 명세를 쓴 뒤 원본과 대 본 것

명세의 첫 판을 쓴 직후, 프로브를 근거로 든 문장과 "읽었다"고 적은 코드의 자리를 원본과 하나씩 대 봤다(`hook_probe_citing_doc`의 알림을 따랐다). 고친 것은 아래다.

- 값 파일의 예시가 시제품이 낸 값이 아니었다. "시제품이 낸 모양"이라고 적고 지어낸 주소와 20000을 넣었던 것을 프로브가 실제로 낸 전문(`{"allowedOrigins":["https://probe-a.example"],"requestChars":771133}`)으로 바꿨다.
- 이미지 밖에서 값을 넣는 단계를 건너뛰면 "닫힌 채 뜬다"고 적은 문장이 틀렸다. 이미지 밖에서는 Next가 읽는 자리가 보통 파일이라, 앞서 래퍼로 띄운 적이 있으면 그때 넣은 값으로 뜬다. "어느 쪽이든 열린 위젯은 없다"는 문장을 빼고, 건너뛰는 길이 없다는 말을 프로브가 잰 이미지로 좁혔다.
- 깨진 사이트 파일의 설명. 프로브의 파일은 필수 칸이 빠지고 모르는 칸도 든 파일이다(`sites_broken.toml`을 읽었다).
- 페이지 안 방식이 값 파일을 받는 주소. "스크립트가 실려 온 주소 옆"이라고 적었는데, 지금의 코드는 기준 주소를 스크립트의 출처로만 잡는다(`web/apps/widget/element/base.ts`를 읽었다). 출처의 `/widget/runtime.json`으로 고치고, 페이지 안 방식은 상한만 쓴다는 것을 더했다(`web/apps/widget/tools/element.ts`의 머리 주석).
- 시험의 셋째 이음매에서 실제 `next build`를 돌리는 사례를 뺐다. `pnpm -C web verify`에는 빌드가 없어(`web/package.json`의 `verify`를 읽었다) 그 사례는 커밋마다 빌드 한 번의 시간을 더한다. 사용자가 고른 선택지의 설명도 셋째와 넷째를 "작은 시험"이라고 했다. 실제 빌드가 낸 산출물의 모양은 모든 PR에서 도는 위젯 e2e의 준비가 지나므로 Next의 판을 올리는 PR에서 잡힌다는 것은 그대로다.
- 위젯 e2e에서 바뀌는 사례를 이름으로 적었다. "입력창의 글자 수 상한은 서버의 기본값과 같다"는 입력창과 서버가 모두 기본값이라 받은 값과 기본값을 가르지 못한다(그 사례의 단언을 읽었다). 사례들이 차례로 돈다는 것은 `web/apps/widget/playwright.config.ts`의 `workers: 1`에서 읽었다.
- 배포 안내의 절 이름을 그 문서의 제목과 맞췄다("4. 띄우기와 확인").
- 이미지 크기와 다시 뜨는 시간의 문장을 잰 범위로 좁혔다. "690.6MiB가 된다"는 시제품의 값이고, 프록시를 거쳐 응답이 끊기는 시간은 재지 않았다.
- 이미지 밖에서는 뜰 때 쓰는 두 파일이 앱 폴더 안의 보통 파일이라 한 체크아웃에서 사이트 파일이 다른 위젯 둘을 함께 띄울 수 없다는 것을 "시작 래퍼의 세 명령"에 더했다.
- deploy-package의 기능 계획을 다시 읽다가, 그 계획의 "위젯처럼 정적 파일로 낼 수 있는 것은 프록시가 바로 내준다"가 이 설계와 부딪친다는 것을 봤다. 응답 머리는 Next가 붙이므로 프록시가 파일을 바로 내면 빠진다. 그 기능 계획과 명세의 Out of Scope에 적었다.

서두의 수는 고친 뒤에 다시 셌다. "명세가 정했다" 표시는 서두 밖에 열, "사용자가 골랐다"는 본문에 하나, "거부한 안:" 문단은 일곱이고 든 안은 열아홉이다.

## 인계

셀프 리뷰(`/code-review`)를 부른 직후 인계의 계기(`hook_handoff`)가 왔다. 세션 컨텍스트가 311,309 토큰으로 문턱 200,000을 넘은 채 단계 경계 `셀프 리뷰 직전`에 왔다는 알림이다. `.claude/skills/next-session/handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않았다. 계기를 낸 호출은 실패하지 않았고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문은 인계로 연 것이 아니고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 방금 불린 `code-review`의 단계는 밟지 않았다. 셀프 리뷰는 새 세션이 한다.

이 세션의 제목은 `docs/widget-runtime-values-spec`이다. 넘기기 전에 `docs/widget-runtime-values-spec (인계함)`으로 바꾼다.

새 세션이 이어받는 상태는 아래다.

- 커밋한 것이 없다. 명세, 프로브 폴더, 이 일지는 미추적이고 기능 계획 둘(`.scratch/site-limits-admin/plan.md`, `.scratch/deploy-package/plan.md`)은 고친 채다.
- to-spec의 차례 가운데 끝난 것: 코드 탐색, 명세 전의 확인(프로브), 사용자에게 시험의 이음매 묻기(답을 받았다. 다시 묻지 않는다), 명세 쓰기, 받는 쪽 기능 계획 둘에 넘긴 것 적기, 명세를 원본과 대 보기.
- 남은 차례: 셀프 리뷰(기준 `origin/dev`)와 반영, 서두의 수 다시 세기, 검증 명령, 커밋, PR, PR 직전 리뷰, 봇 반영과 병합, 회고, 다음 지시문. 다음 지시문의 다음 단계는 이 명세를 티켓으로 나누는 일(`/to-tickets widget-runtime-values`)로 본다.
- 이 세션이 명세를 쓴 뒤 돌리지 않은 것: `uv run python tools/run_checks.py`, ruff 둘, 프로브의 타입 검사(`uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`), `uv run python tools/sibling_overlap.py`.
- 이 세션의 스크래치 폴더(`wrv-run1`~`wrv-run3`의 원본 기록)는 저장소 밖이라 새 세션에서 보이지 않을 수 있다. 프로브 README의 숫자는 그 원본과 이미 대 봤고, 다시 내려면 프로브를 다시 돌린다.

셀프 리뷰의 명세 출처는 넷이다. to-spec 스킬(`.claude/skills/to-spec/SKILL.md`. 명세의 틀과 쓴 뒤의 차례), 기능 계획(`.scratch/widget-runtime-values/plan.md`. 수락과 구현 티켓이 고치는 문서 셋), ADR 0064(결정 "허용 출처와 요청 글자 수 상한", Consequences의 "재지 않은 것"·"다른 행"·"명세가 짓는 것"), 사용자의 답(위 "사용자에게 물은 것 하나"의 라벨과 설명과 확인받은 요약)이다.

셀프 리뷰에 밀 주장으로 넘길 것은 아래다. 앞의 여섯은 컨텍스트 압축 전에 읽은 것을 요약에 기대어 적었고, 압축 뒤에 원문을 다시 열지 않았다.

1. 시작 래퍼(`web/apps/widget/tools/start.ts`)에 대해 명세가 적은 것: 어느 명령으로 불려도 스크립트를 짓는 도구를 불러온다는 것, 상대 경로의 사이트 파일을 부른 자리에서 푼다는 것, 세 명령의 지금 동작.
2. 명세 서두 "이력"의 "ADR 0024, ADR 0047, ADR 0056의 그 문장들에 `(바뀜: ADR 0064)` 포인터가 이미 있다".
3. release-image 명세에서 옮긴 수치(874.3MiB, 13.6~40.7초, 1,452~1,567MiB, 1GiB 이하에서 메모리 부족, 시작 유예 300초)와 "Next의 단독 실행 출력은 시작 래퍼를 거치지 않아 거부했다".
4. CI의 두 잡이 도는 때(`e2e-standalone`은 main으로 가는 PR과 main 푸시, `e2e-widget`은 모든 PR).
5. 단독 compose에 대해 적은 것(위젯에 읽기 전용이 없고 다른 web 컨테이너 둘에는 있다, serve가 같은 꼴의 tmpfs를 이미 쓴다, 공통 시작 유예 30초).
6. 구현 티켓이 고치는 문서의 인용 셋(`docs/constitution/tech.md`의 웹 칸, `CONTEXT.md`의 사이트 파일 항목, `web/apps/widget/EMBED.md`의 "위젯도 같은 파일로 빌드된다")과 위젯 화면의 알림 문구.
7. 압축 뒤에 원문과 대 본 것: 프로브를 근거로 든 문장 전부(프로브 README와 대 봤다), 시험 사례의 이름 여섯, 배포 안내의 절 이름과 고칠 문장, `element.ts`·`base.ts`·`token.ts`를 읽고 적은 문장, deploy-package 계획에서 옮긴 인용 둘, `EMBED.md`의 무결성 검사 인용(괄호 "(요청 글자 수 상한)"이 빠져 있어 인계 직전에 고쳤다).
8. 명세가 어림이라고 적은 것 가운데 리뷰가 다시 볼 만한 것: 이미지 밖에서 값을 넣는 단계를 건너뛰면 앞서 넣은 값으로 뜬다는 것, 한 체크아웃에서 두 e2e를 함께 돌리면 산출물을 덮어쓴다는 것, Next가 응답 머리 목록을 더는 읽지 않게 바뀌면 `'none'`으로 뜬다는 것.

앞 지시문이 "이 명세 세션의 일은 아니지만 알린다"며 넘긴 것은 인계 지시문에 그대로 옮겼다(admin-login 05, PR #653의 봇 보류 하나).

낸 지시문은 아래다.

```
다음 작업: 기능 widget-runtime-values. 위젯 이미지를 미리 지어 두고 컨테이너가 뜰 때 사이트 파일의 허용 출처와 요청 글자 수 상한만 받게 해, 뜰 때마다 하던 빌드를 없앤다.
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다.
시작 프롬프트: /to-spec widget-runtime-values
브랜치: docs/widget-runtime-values-spec
모델: Fable 5.2 / xhigh. 2의 잇는 지시문. 그 값은 Fable 5.1이지만 지금 모델 메뉴에 없어 열 때 고를 수 있는 이름으로 적었다(대기열 model-menu-name-fable-5-1-stale의 임시 규칙).
읽을 것: docs/journal/2026-11-27-0407-widget-runtime-values-spec.md의 "인계" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다(일지 docs/journal/2026-11-27-0407-widget-runtime-values-spec.md). 명세(.scratch/widget-runtime-values/spec.md)는 다 썼고 to-spec의 앞 차례(코드 탐색, 명세 전의 확인, 사용자에게 시험의 이음매 묻기)는 끝났다. 사용자에게 다시 묻지 않고 명세를 처음부터 다시 쓰지 않는다. 남은 차례와 셀프 리뷰에 넘길 명세 출처와 밀 주장은 그 일지의 "인계" 절에 있다. 이 기능의 일은 아니지만 앞 지시문이 알린 것을 잇는다: admin-login 05(PR #653)의 봇 보류 하나가 병합된 일지 "다음"에 없고 PR 코멘트(issuecomment-7199113820)에만 있다. 관리 라우터의 public에 /health 외의 라우트가 붙는 것을 막는 시험이 없다는 지적이고, admin-login을 잇는 세션이 이어받는다.
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 주 체크아웃이 지금 origin/dev를 따라가 있는지는 이 세션이 보지 않았다.
이번 요청 범위: PR과 병합까지
```

넘기기 전의 차례를 밟았다. 제목을 `docs/widget-runtime-values-spec (인계함)`으로 바꿨고, 이 세션이 띄운 백그라운드 작업은 없었으며, `git worktree unlock C:/project/agent/.claude/worktrees/widget-runtime-values-spec`이 출력 없이 끝났다.

open-session을 부른다 2026-11-26T19:47:18Z

## 이어받은 세션

인계로 연 새 세션이 이 절부터 쓴다. 세션 제목 `docs/widget-runtime-values-spec`, 모델 Fable 5.2. 첫 메시지는 위 "인계" 절의 "낸 지시문"을 붙여 넣은 글이었고, 그 앞에 open-session이 붙이는 한 줄(`.claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다 … 인자: widget-runtime-values`)이 있었다. 사용자가 따로 더한 말은 없다.

- 제목을 브랜치 이름으로 바꾸고 `git worktree list`에서 이 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. 커밋하지 않은 변경은 인계 절이 적은 그대로였다(고친 기능 계획 둘, 미추적 명세·프로브 폴더·이 일지).
- 앞 세션이 돌리지 않은 검사 가운데 셋을 먼저 돌렸다. `uv run python tools/sibling_overlap.py`는 "번호 겹침 없음", "함께 고친 파일 없음"이었고 기준 브랜치 줄이 `origin/dev afba836`으로 움직여 있었다(`afba83679`, admin-login 04, PR #652 하나가 더 들어왔다). `git diff --name-only HEAD...origin/dev`의 스물일곱 파일 가운데 이 명세가 이름으로 든 파일은 없었다. `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`는 오류 0, `uv run ruff check .scratch/widget-runtime-values`와 `uv run ruff format --check .scratch/widget-runtime-values`는 통과였다.

### 셀프 리뷰(`/code-review origin/dev`)

본 범위: 기준 `e7c53cba3ab4fe58f093e1552226d685c1232d1e`(origin/dev와의 merge-base), 추적 파일 둘의 변경, 커밋 0, 미추적 파일 열일곱. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델로 띄웠다. 명세 출처와 밀 주장은 "인계" 절의 것을 두 브리프에 옮기고, 서두의 수와 회차의 수를 다시 세는 것을 밀 주장에 더했다. 프로브는 다시 돌리지 말고 코드를 읽어 대 보라고 했다.

#### 표준 축의 보고

Critical 0, Major 1, Minor 7, Nit 2. 보고를 줄여 옮긴다.

1. (Major) 명세의 "걸리는 범위"와 프로브 README 결과 2가 값 파일의 응답에도 같은 `frame-ancestors` 값이 붙었다고 "쟀다"로 적었는데, `run.py`의 `observe`는 값 파일의 그 머리를 기록하지도 않고 `serves`가 단언하는 것은 페이지와 페이지 안 번들의 것뿐이다. 404의 머리(`missing_csp`), 페이지의 `s-maxage`, 값 파일의 캐시 머리와 ETag 변화도 기록만 하고 단언하지 않는다. README가 "쟀다"를 "표지를 단언한 것"으로 정의했으므로 근거의 종류가 그 정의와 어긋난다.
2. (Minor) 명세 "명세 전의 확인"의 "시제품이 실제 구현과 다른 점은 둘이다"에 반례가 있다. `patch-config.mjs`가 이미지 안 `next.config.ts` 사본에 값 파일의 `Access-Control-Allow-Origin: *` 규칙을 더했다.
3. (Minor) "25초 동안 확인 다섯 번 모두 실패"의 다섯은 Docker가 남기는 최근 기록의 수와 같고, `run.py`는 남은 기록이 비지 않고 모두 1인 것만 단언한다.
4. (Minor) "종료 1"을 "쟀다"로 적었는데 `exits_round`는 0이 아닌 것만 단언한다.
5. (Minor) "시작 래퍼의 세 명령" 표의 `start` "지금" 칸이 "빌드 산출물을 그대로 낸다"인데, `start.ts`의 머리 주석은 `next start`도 설정 파일로 사이트 파일을 읽고 읽지 못하면 같은 진단으로 끝난다고 적는다.
6. (Minor) "티켓을 나눌 때 함께 둘 것"의 "느리지만 맞게 선다"는 재지 않은 것을 단정했다. "명세 전의 확인" 표의 "그 폴더가 없거나"는 대조 회차와 다르다(폴더는 이미지에 있었고 루트가 읽기 전용이라 쓰지 못했다).
7. (Minor) 쉬운 말 원칙. tmpfs, 심볼릭 링크, ETag, healthy, uid·gid, init(tini), 바인드 마운트를 처음 나올 때 풀지 않았고, "값 파일"이 `CONTEXT.md`에 없다.
8. (Minor) 옛 말이 남은 자리의 나열에 빠진 곳이 있다. `web/packages/e2e-standalone/e2e/deployment.e2e.ts`의 상한 주석과 루트 `README.md`의 트리 설명이다.
9. (Nit) Out of Scope 머리 문장이 받는 쪽 문단의 이름을 "Out of Scope"로만 적었는데 deploy-package 쪽은 "Out of Scope와 Further Notes"다.
10. (Nit) 일지에 "다음" 절이 없다.
- baseline smell(모두 판단 항목, `run.py`): `(origins, chars)` 짝이 함께 다니는 Data Clumps, 회차 함수 넷이 같은 뼈대를 되풀이하는 Duplicated Code, `up`·`until`·`put`·`head`의 Mysterious Name.
- 맞다고 확인했다고 적은 것: 서두의 수(열한 행, 표시 열, "사용자가 골랐다" 하나, "거부한 안:" 일곱 문단 열아홉 안), 회차의 수(53 = 32 + 10 + 11, 시간을 찍은 스물넷, 다시 띄운 일곱, 읽기 전용 열셋), 세 ADR의 `(바뀜: ADR 0064)` 포인터, release-image에서 옮긴 수치, CI 두 잡이 도는 때, 단독 compose의 사실 셋, 따옴표 인용 전부, `start.ts`가 Vite와 Tailwind를 정적으로 불러오는 것과 상대 경로 풀기, 기능 계획 둘의 인용과 `Blocked by`.

#### 표준 축의 지적을 근거와 대 본 것

- 1은 맞다(`run.py`의 `observe`와 `serves`를 읽었다). 글을 낮추지 않고 프로브가 단언하게 고친다. `observe`가 값 파일의 `frame-ancestors` 머리를 적게 하고, `serves`에 값 파일과 404의 그 머리, 값 파일의 캐시 머리와 내용의 종류와 비지 않은 ETag, 글꼴의 다른 출처에 여는 머리, 페이지의 공유 캐시 머리를 더했다. `reflect_round`에는 다시 띄운 뒤 ETag가 달라지는 것을 더했다. 그 뒤 일곱 섹션 전체를 다시 돌린다(실행 4. 결과는 아래 "실행 4").
- 3은 맞다(`health_round`가 Docker의 `Health.Log`를 읽고 비지 않고 모두 1인지만 본다). "다섯 번"을 글에서 뺀다.
- 4는 맞다(`exits_round`의 `code != 0`). `exits_round`에 `exit_code` 인자를 더하고 `sitefile`의 서지 않는 회차 셋에 1을 줬다. 1과 같은 실행 4가 본다.
- 5는 맞다(`web/apps/widget/tools/start.ts` 머리 주석의 "next 만 부르는 `start` 는 next 가 같은 진단으로 끝난다"를 읽었다). 표의 칸을 고친다.
- 2, 6, 8, 9는 맞다. 2와 8은 반례만 덧붙이지 않고 닫힌 나열을 일반 조항과 예시로 바꾼다. 8은 찾는 말에도 빠진 꼴이 있었다. "사이트 파일로 빌드", "같은 파일로 빌드"로 Grep하니 `docs/constitution/operations.md`의 가드레일 절, `.github/workflows/ci.yml`, 위젯과 위젯 테스트 페이지의 e2e 준비와 설정, `web/packages/e2e-standalone/e2e/env.ts`가 더 나왔다.
- 7은 풀이를 붙여 고친다. "값 파일"은 ADR 0064가 지은 이름이고 용어집에 없다(`CONTEXT.md`를 Grep했다). 용어집 항목은 `CONTEXT.md`를 고치는 구현 티켓이 함께 더하도록 명세의 "구현 티켓이 코드와 같은 티켓에서 고치는 문서"에 적는다.
- 10은 단계를 닫을 때 쓰는 절이라 지금은 고칠 것이 없다.
- baseline smell 셋은 남긴다. 프로브는 측정용 스크립트이고, 결과를 낸 판의 함수 이름을 README와 독스트링이 가리킨다. 이름과 뼈대를 고치면 그 인용을 함께 옮겨야 하는데 측정의 뜻은 달라지지 않는다.

#### 명세 축의 보고

Critical 0, Major 1, Minor 3, Nit 4. 보고를 줄여 옮긴다.

1. (Major) Testing Decisions 셋째의 "지금의 사례 가운데 뒤집히는 것은 셋이다"가 틀린 닫힌 셈이다. `web/apps/widget/next.config.test.ts`가 명세의 파일 목록에 없는데, 그 파일의 사례 여럿이 Next의 설정 파일이 사이트 파일을 읽어 두 값을 빌드에 싣는 것을 단언한다. `element.test.ts`의 "사이트 파일을 주지 않으면 서버의 기본 상한을 싣는다"와 `start.test.ts`의 명령 표도 바뀐다. "변수가 준 사이트 파일을 읽지 못하면 빌드가 실패한다"는 같은 이름의 묶음이 두 파일에 있어 명세의 문장으로는 어느 쪽인지 가를 수 없다.
2. (Minor) 프로브가 적기만 하고 단언하지 않는 것을 측정으로 적은 자리. 표준 축 1, 4와 같은 지적이고, 끌 때의 종료 코드 143도 든다.
3. (Minor) 값 파일을 받지 못하면 설정 오류 알림으로 닫고 스스로 다시 시도하지 않는다는 것을 사용자에게 묻지 않고 명세가 확정했다.
4. (Minor) site-limits-admin 기능 계획에 더한 문단이 명세 Further Notes의 "떠 있는 동안 사이트 파일만 고쳤을 때"를 가리키며, 그 노트에 없는 내용(떠 있는 동안 Next가 응답 머리 목록을 다시 읽는지 보지 않았다)을 든다.
- Nit 넷: "확인 다섯 번", 세 명령 표의 `start` "지금" 칸, Out of Scope 머리 문장의 인용, 서두 "이력"의 ADR 나열에 ADR 0023이 빠진 것.
- 지적으로 싣지 않은 것: 한 체크아웃의 두 e2e가 산출물을 덮어쓴다는 어림은 코드로 확인된다는 것, "느리지만 맞게 선다"와 시작 유예 문장이 표시 없는 어림이라는 것, 명세가 구현 파일의 경로를 든다는 것.

#### 명세 축의 지적을 근거와 대 본 것

- 1은 맞다(`web/apps/widget/next.config.test.ts`, `tools/element.test.ts`, `tools/start.test.ts`를 읽었다). 앞의 파일은 사이트 파일의 환경 변수를 바꿔 가며 설정 파일을 새로 읽어, 설정의 `env`에 실린 두 값과 `frame-ancestors` 머리와 읽지 못할 때 던지는 진단을 단언한다. 같은 이름의 묶음 "변수가 준 사이트 파일을 읽지 못하면 빌드가 실패한다"가 `next.config.test.ts`와 `element.test.ts`에 하나씩 있다. 수를 고쳐 다시 닫지 않는다. 바뀌는 사례의 성질(빌드가 사이트 파일을 읽는다는 것, 산출물이 두 값을 싣는다는 것을 단언한다)을 일반 조항으로 적고 파일마다 예를 든다.
- 2는 표준 축 1, 4와 같다. 실행 4가 본다. 끌 때의 종료 코드 143과 시간과 메모리는 표지가 아니라 프로브가 회차마다 적는 값이다. 프로브 README가 "쟀다"를 표지를 단언한 것으로만 풀어 둔 것을 `docs/agents/issue-tracker.md`의 뜻(커밋한 프로브가 다시 내는 것)에 맞춰, 단언한 표지와 회차마다 적는 값 둘로 갈라 적는다.
- 3은 남긴다. to-spec은 모자란 결정을 명세에 확정하지 않고 사용자에게 묻는다고 적지만, 이 세션의 지시문이 "사용자에게 다시 묻지 않고"라고 했고 그 절은 머리에 "명세가 정했다"로 표시돼 있다. iframe 방식은 허용 출처를 모르면 토큰의 답을 믿을 수 없어(`web/apps/widget/lib/token.ts`를 앞 세션이 읽었다) 닫히는 것이 새 선택이 아니다. 남는 선택은 페이지 안 방식이 기본 상한으로 열지이고, 명세는 두 방식을 같게 두는 쪽을 골랐다. 사용자가 티켓으로 나누기 전에 뒤집을 수 있게 PR 본문의 리뷰어 참고에 적는다.
- 4는 맞다. 명세의 그 노트에 보지 않은 것을 더해 기능 계획의 인용이 서게 한다.
- Nit 넷은 고친다. ADR 나열은 닫힌 목록을 일반 조항과 예시로 바꾼다. `docs/adr/`에서 "빌드"가 "사이트 파일"·"허용 출처"·"뜰 때"·"글자 수 상한"과 함께 든 줄을 찾아 `바뀜: ADR 0064`가 든 줄과 ADR 0064 자신을 뺀 뒤 남은 줄을 한 줄씩 열어 봤다(손으로 봤다. `grep -n "빌드" docs/adr/*.md`를 그 낱말들로 걸렀다). 남은 줄은 거부한 안의 근거(ADR 0024의 둘, ADR 0056의 하나), 지난 이력 항목(ADR 0024), 그때 명세에 넘긴 목록(ADR 0056), 그때 코드를 옮긴 일과 띄우는 꼴을 적은 문장(ADR 0050), 지금도 맞는 e2e 문장(ADR 0024)이었다. `.claude/rules/adr.md`가 포인터를 달지 않는다고 정한 종류이거나 결정이 그대로인 문장이다. ADR 0023의 "위젯의 빌드도 같은 파일에서 허용 출처를 읽는다"에는 포인터가 있었다.
- 싣지 않은 것 가운데 구현 파일의 경로는 그대로 둔다. `docs/agents/issue-tracker.md`가 코드를 읽은 것은 파일과 판과 함께 읽었다고 적으라고 한다.

#### 실행 4

표준 축 1, 4와 명세 축 2를 받아 `run.py`의 단언을 넓힌 판으로 일곱 섹션 전체를 한 번에 돌렸다(`uv run python .scratch/widget-runtime-values/probes/prebuilt_start/run.py --sections build,start,reflect,readonly,sitefile,health,browser --rounds 3 --work <스크래치 폴더>`). 종료 코드 0, 측정 37회차, 측정 아님 0회차였다. 원본 기록의 처음과 끝 시각은 05:06:16과 05:08:22로 126초였다(`raw.log`를 손으로 봤다. 층 캐시가 찬 채다).

- 새로 단언한 표지가 모두 섰다(`.scratch/widget-runtime-values/probes/prebuilt_start/run.py`의 `serves`, `reflect_round`, `exits_round`). 값 파일과 없는 경로의 응답에도 같은 `frame-ancestors` 값, 값 파일의 `cache-control: public, max-age=0`과 `content-type: application/json; charset=UTF-8`과 비지 않은 ETag, 글꼴의 `Access-Control-Allow-Origin: *`, 페이지의 `s-maxage=31536000`, 다시 띄운 뒤 달라진 ETag, 서지 않는 회차 셋의 종료 코드 1이다.
- 회차마다 적은 값이 앞 세 실행의 범위를 세 군데에서 벗어났다(같은 `probes/prebuilt_start/run.py`가 `results.jsonl`에 적은 값이다). 첫 200까지의 시간은 0.61~0.88초로 아래 끝이 0.62에서 0.61로, 메모리 최고치는 제한 없는 회차 91.9~95.6MiB와 제한한 회차 81.6MiB로 위 끝이 94.3에서 95.6으로, healthy까지는 2.59~2.66초로 아래 끝이 2.61에서 2.59로 움직였다. 끄기는 열한 회차 0.16~0.33초에 모두 종료 코드 143, 진입 단계는 0.009~0.015초, Next의 `Ready in`은 126~227ms였다. 이미지의 크기와 깔린 것과 응답 머리 목록의 자리는 앞 실행과 같았다.
- 네 실행을 합친 범위로 README와 명세와 deploy-package 기능 계획의 수를 고친다.

#### 반영

두 축 합쳐 Critical 0, Major 2, Minor 10, Nit 6이었다(두 축이 같은 것을 낸 지적은 따로 셌다). 축마다 가장 무거운 것은 표준 축이 낸, 프로브가 단언하지 않는 것을 측정으로 적었다는 지적과 명세 축이 낸, 뒤집히는 사례를 셋으로 닫아 셌다는 지적이다.

고친 것. 새로 쓴 사실 문장은 PR 직전 리뷰에 밀 주장으로 넘기려고 원문을 옮긴다.

1. 프로브(`.scratch/widget-runtime-values/probes/prebuilt_start/run.py`)의 단언을 넓히고 실행 4를 돌렸다(위 "실행 4"). 프로브 README의 "근거의 종류"를 둘로 갈랐다. 원문: "하나는 `run.py`가 그 회차의 표지로 단언한 것이다. 어긋나면 그 회차가 측정 아님이 되고 종료 코드가 1이다. 다른 하나는 측정인 회차마다 `run.py`가 값으로 적는 것이다. 시간, 메모리, 크기, 끌 때의 종료 코드 143이 그렇고, 단언이 아니라서 아래에 범위로 옮겨 적었다." README "결과를 본 뒤 바꾼 것"에 "넓힌 표지(실행 4)"를 더했고 끝 문장은 "실행 4가 보이는 것은 같은 이미지가 그 값을 다시 냈다는 것이고, 다른 Next 판에서도 같다는 뜻은 아니다"다.
2. 네 실행을 합친 수로 고쳤다(명세, 프로브 README 둘, deploy-package 기능 계획). 첫 응답까지 0.61~1.78초(시간을 찍은 마흔 회차), 메모리 최고치 78.3~95.6MiB(제한 없는 서른여덟 회차 88.9~95.6MiB, 256MiB로 제한한 두 회차 78.3MiB와 81.6MiB), healthy까지 2.59~2.66초(여섯 회차), 끄기 0.16~1.16초(스물여덟 회차), 사이트 파일 A로 선 회차 열넷, 다시 띄운 회차 열둘, 읽기 전용 회차 열여덟과 쓰기 가능한 회차 스물, 네 실행 90회차(32 + 10 + 11 + 37). 앞 세 실행의 값은 README에 적혀 있던 것이고 그 원본 기록은 이 세션에서 다시 열지 못했다(앞 세션의 스크래치 폴더다).
3. 명세 "명세 전의 확인"의 "다른 점은 둘이다"를 일반 조항과 예시로 바꿨다. 원문: "저장소의 파일을 고치지 않고 이미지 안에서만 필요한 것을 채웠으므로, 시제품이 채운 자리는 모두 구현이 새로 짓는 자리다. … 값 파일에 다는 `Access-Control-Allow-Origin: *` 규칙은 저장소의 Next 설정이 아니라 이미지 안의 사본에 더했다. 응답 머리 목록의 원본은 래퍼의 빌드가 아니라 이미지를 짓는 파일이 복사해 남겼다."
4. "확인 다섯 번"을 뺐다. 명세는 "25초 동안 돈 확인이 모두 실패한 채"로, README는 "남은 기록은 두 번 모두 다섯이었다. Docker가 최근 기록만 남기는 것으로 알고 있어(재지 않았다) 그 수를 돈 확인의 수로 읽지 않는다"로 적었다.
5. 세 명령 표의 `start` "지금" 칸. 원문: "빌드 산출물을 그대로 낸다. 응답 머리는 빌드 때 굳은 값이 나간다. 래퍼는 사이트 파일을 읽지 않지만 Next가 설정 파일을 읽으며 사이트 파일도 읽어, 읽지 못하면 Next가 같은 진단으로 끝난다(그 파일의 머리 주석이 손으로 봤다고 적는다)".
6. 어림 표시와 낱말. "느리지만 맞게 선다"를 "느리지만 맞게 설 것으로 본다(구조에서 미룬 어림이고 재지 않았다. 그 티켓이 단독 배포 e2e를 이 PC에서 돌려 확인한다)"로, "그 폴더가 없거나"를 "그 폴더를 tmpfs로 주지 않거나"로 고쳤다. 시작 유예 문장은 "위젯의 상태 확인에만 시작 유예 300초가 걸려 있고(`deploy/standalone/compose.yaml`을 읽었다), Docker는 유예 동안의 실패를 세지 않는다(Docker의 동작으로 아는 것이고 이 명세가 재지 않았다). 위젯에만 긴 값을 둔 까닭은 뜰 때의 빌드를 기다리려는 것으로 본다(어림. release-image 명세는 그 값을 어림이라고만 적었다)"로 고쳤다. release-image 명세의 그 문장("시작 유예는 위젯 300초와 나머지 30초다(어림)")을 읽었다.
7. 처음 나오는 말에 풀이를 붙였다(healthy, tmpfs, ETag, 앱 사용자, 심볼릭 링크, init, uid·gid, 바인드 마운트). "값 파일"은 `CONTEXT.md`를 고치는 구현 티켓이 용어집에 올리도록 "구현 티켓이 코드와 같은 티켓에서 고치는 문서"의 셋째 항목에 적었다.
8. 옛 말의 나열을 예시로 바꿨다. 찾는 말의 예에 "사이트 파일로 빌드"와 "같은 파일로 빌드"를 더하고, 나온 자리의 예로 배포 안내, 두 앱의 e2e 준비와 설정, 단독 배포 e2e의 주석, CI 워크플로의 주석, 루트 `README.md`의 트리 설명, `docs/constitution/operations.md`의 가드레일 절을 들었다. `.scratch/` 아래에서 나온 자리는 문서 위치 절로 가른 뒤 고친다고 적었다.
9. Out of Scope 머리 문장을 두 기능 계획의 실제 머리("widget-runtime-values 명세가 넘긴 것(2026-11-27,")에 맞췄다.
10. Testing Decisions 셋째의 "뒤집히는 것은 셋이다"를 일반 조항과 파일마다의 예로 바꾸고 파일 목록에 `next.config.test.ts`를 더했다. 원문의 뼈대: "지금의 사례 가운데 이 명세가 바꾸는 행동을 단언하는 것은 같은 티켓이 고친다. 빌드가 사이트 파일을 읽는다는 것, 빌드가 두 값을 산출물에 싣는다는 것, 서비스 시작이 준비 없이 Next만 부른다는 것을 단언하는 사례가 그렇다." `next.config.test.ts`의 사례는 "어느 사례가 이 파일에 남고 어느 사례가 서비스 시작의 시험으로 옮겨 가는지는 … 구현 티켓이 정한다"로 두었다. 넷째 이음매의 "지금의 사례 셋"도 닫힌 수를 뺐다.
11. Further Notes "떠 있는 동안 사이트 파일만 고쳤을 때"에 보지 않은 것을 더했다. 원문: "값 파일은 요청마다 디스크에서 나가는 공개 파일이라 바뀐 내용이 나갈 것으로 보지만(어림), 응답 머리 목록은 Next가 시작할 때만 읽는지 떠 있는 동안에도 다시 읽는지 모른다."
12. 서두 "이력"의 ADR 나열을 일반 조항으로 바꿨다(위 "명세 축의 지적을 근거와 대 본 것"의 Nit 항목). 원문: "ADR 0023, ADR 0024, ADR 0047, ADR 0056에서 포인터가 달린 그 문장들을 읽었다(네 ADR은 예이고, 그런 문장이 이 넷에만 있다는 뜻이 아니다). … 그 줄들은 거부한 안의 근거, 지난 이력 항목, 그때 명세에 넘긴 것의 목록, 그때 코드를 옮긴 일을 적은 문장, 지금도 맞는 문장이었다."
13. 명세 서두의 "코드를 읽었다"는 기준을 "명세를 쓸 때의 origin/dev인 커밋 `e7c53cba3`"으로 고쳤다. 이 브랜치가 origin/dev(`afba83679`)를 빨리 감기로 받아 기준 커밋이 움직였기 때문이다.

남긴 것과 이유.

- 명세 축 3(값을 받지 못했을 때 닫는다는 것을 묻지 않고 정했다). 지시문이 다시 묻지 말라고 했고 그 절이 "명세가 정했다"로 표시돼 있다. PR 본문의 리뷰어 참고에 적어 사용자가 티켓으로 나누기 전에 뒤집을 수 있게 한다.
- 표준 축의 baseline smell 셋(`run.py`). 측정용 스크립트이고 고쳐도 측정의 뜻이 달라지지 않는다.
- 표준 축 10(일지에 "다음" 절이 없다). 단계를 닫을 때 쓴다.
- 명세가 구현 파일의 경로를 든다는 것. 근거 규칙이 읽은 파일을 적으라고 한다.

다시 돌린 명령. `git merge --ff-only origin/dev`(e7c53cba3에서 afba83679로, 스물일곱 파일), `uv run python tools/plan_table.py`(출력 없음, `.scratch/plan.md` 그대로), `uv run ruff check .`(All checks passed), `uv run ruff format --check .`(2693 files already formatted), `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`(오류 0), `uv run python tools/sibling_overlap.py`(번호 겹침 없음, 함께 고친 파일 없음. 열린 PR #651이 단독 compose에 위젯 관리 서버를 더하는 중이다). 손으로 치는 나머지 검사는 커밋의 pre-commit으로 갈음하고 결과를 아래에 적는다.

#### 커밋과 pre-commit

`git commit -F <메시지 파일>`이 커밋 `8d074ba43`을 만들었다. 파일 열아홉이 들었다(고친 기능 계획 둘, 새 명세, 새 프로브 파일 열다섯, 이 일지). 명령은 Bash의 600초 제한을 넘겨 백그라운드로 넘어갔고, 다시 치지 않고 끝 알림을 기다렸다. 종료 코드는 0이었다.

pre-commit의 검사마다 결과는 아래다.

- `ruff check`, `ruff format`: Passed.
- `checks`(`tools/run_checks.py`): Passed. 안의 검사는 check-ticket 0.8초, check-notes 0.9초, zizmor 2.3초, lint-imports 2.8초, check-instructions 7.6초, check-type-escapes 9.0초, pyright 43.7초, pyright-linux 44.0초, run-hooks 54.9초, pytest 593.9초, web-verify 674.9초였고 모두 Passed다.
- markdown tables, line separators, mutation tables, quotes(경고만 낸다), commit message: Passed.
- Skipped는 둘이다. canary specs와 constitution version이고 둘 다 `(no files to check)`였다. 이 커밋에 카나리아 명세도 헌법 파일도 없어서이고, 손으로 치지 않았다.

이 커밋은 제품 코드를 건드리지 않아 LLM 테스트(`-m llm` 계열), e2e, 사진 비교는 돌리지 않았다.

quotes 검사가 낸 경고 열둘은 하나씩 원문과 대 봤다.

- 일지 49줄. ADR 0064의 인용이 원문과 달랐다. ADR 0064의 63줄은 "미리 짓고 뜰 때 값만 바꿔 넣는"이고 일지는 "미리 지어 두고"로 적혀 있었다. 원문대로 고쳤다(앞 세션이 쓴 줄이다).
- 일지 "반영" 절의 첫 문단. 두 축의 지적에 이 세션이 붙인 이름을 따옴표로 적어 인용처럼 보였다. 따옴표를 떼고 풀어 적었다.
- 일지 30, 36, 37줄. 선택 화면의 라벨과 설명이고 원천이 대화라 저장소에 없다. 그대로 둔다.
- 일지 131, 132줄. 앞 세션이 셀프 리뷰에 넘기려고 적은 밀 주장이다. 131줄이 든 명세 문장은 이 세션이 "반영" 12에서 고쳐 지금 명세에 없다. 그때의 기록이라 그대로 둔다.
- 일지 176, 177, 203줄. 리뷰가 짚은 옛 명세 문장이고 이 세션이 "반영" 3, 4, 10에서 고쳐 지금 명세에 없다. 그대로 둔다.
- 명세 197줄. 위젯의 알림 문구다. `web/apps/widget/components/pages/WidgetScreen.tsx` 99~100줄을 읽었다. 제목이 "위젯 설정이 올바르지 않습니다."이고 본문이 "사이트 관리자에게 알려 주세요."라 화면에는 명세가 적은 대로 이어져 보이고, 소스에는 두 조각으로 나뉘어 있어 검사가 한 줄로 찾지 못했다. 그대로 둔다.
- 프로브 README 101줄. 프로브 첫 판이 붙였던 결과 이름이다. 첫 판은 커밋된 적이 없어 대 볼 원문이 없다. 그대로 둔다.

### 둘째 인계(커밋 뒤)

커밋 명령의 결과에 인계의 계기(`hook_handoff`)가 붙어 왔다. 세션 컨텍스트가 356,160 토큰으로 문턱 200,000을 넘은 채 단계 경계 `커밋 뒤`에 왔다는 알림이다. `.claude/skills/next-session/handoff.md`를 Read로 열어 읽은 직후 자동 압축이 왔다. 압축 뒤 요약으로 인계를 판정하던 중이었음을 알아 그 파일을 다시 열고 5(압축 뒤 이어 할 때)대로 이었다. 인계하지 않는 때 다섯에 들지 않았다. 커밋은 종료 코드 0으로 끝났고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`으로 시작해 지금 경계와 다르고, 이 세션이 쓴 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다.

이 세션의 제목은 `docs/widget-runtime-values-spec`이다. 넘기기 전에 `docs/widget-runtime-values-spec (인계함)`으로 바꾼다.

새 세션이 이어받는 상태는 아래다.

- 커밋 `8d074ba43`은 푸시하지 않았고 PR은 없다(`gh pr view docs/widget-runtime-values-spec --json state,number,url`이 "no pull requests found"로 끝났다).
- 이 일지는 커밋 뒤에 고친 채다("커밋과 pre-commit" 절, 이 절, 인용을 고친 두 줄). 새 세션이 이어 쓰고 커밋한다.
- 남은 차례: PR 직전 리뷰, 푸시와 PR, 봇 반영과 병합, 이 일지의 "다음" 절, 회고, 다음 지시문. 다음 지시문의 다음 단계는 이 명세를 티켓으로 나누는 일(`/to-tickets widget-runtime-values`)로 본다.
- PR 직전 리뷰에 밀 주장으로 넘길 것은 위 "반영"의 "고친 것" 열세 항목에 옮긴 원문이다. `coderabbit-review`가 부르는 명령에는 주장을 넘기는 인자가 없어, 그 서브에이전트가 돌면 넘기지 못하고 `bug-perf-review`가 돌 때만 브리프에 넣는다.
- PR은 면제 PR이다(브랜치 `docs/<slug>`, 가리키는 티켓 없음). 제목은 커밋 제목과 같게 `docs: 위젯이 뜰 때 값을 받는 명세와 프로브를 쓴다 (widget-runtime-values)`로 둘 생각이었다. 선례는 `docs: PostgreSQL을 들이는 명세와 프로브를 쓴다 (postgres-foundation) (#606)`이다.
- PR 본문의 "리뷰어 참고"에 적기로 한 것이 하나 있다. 명세 "받지 못했을 때"가 정한 것(값 파일을 받지 못하면 위젯이 닫힌 채 남는다)은 사용자에게 묻지 않고 명세가 정했다. 셀프 리뷰 명세 축이 Minor로 짚었고, 지시문이 다시 묻지 말라고 해 남겼다. 사용자가 티켓으로 나누기 전에 뒤집을 수 있다고 적는다.
- 이 세션의 스크래치 폴더(`wrv-run4`의 원본 기록 `raw.log`와 `results.jsonl`)는 저장소 밖이라 새 세션에서 보이지 않을 수 있다. 프로브 README의 실행 4 숫자는 그 원본과 대 봤고, 다시 내려면 프로브를 다시 돌린다.

앞 지시문이 "이 기능의 일은 아니지만" 알린 것(admin-login 05, PR #653의 봇 보류 하나)은 이번 인계 지시문에도 그대로 옮겼다.

낸 지시문은 아래다.

```
다음 작업: 기능 widget-runtime-values. 위젯 이미지를 미리 지어 두고 컨테이너가 뜰 때 사이트 파일의 허용 출처와 요청 글자 수 상한만 받게 해, 뜰 때마다 하던 빌드를 없앤다.
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다.
시작 프롬프트: /to-spec widget-runtime-values
브랜치: docs/widget-runtime-values-spec
모델: Fable 5.2 / xhigh. 2의 잇는 지시문. 그 값은 Fable 5.1이지만 지금 모델 메뉴에 없어 열 때 고를 수 있는 이름으로 적었다(대기열 model-menu-name-fable-5-1-stale의 임시 규칙).
읽을 것: docs/journal/2026-11-27-0407-widget-runtime-values-spec.md의 "둘째 인계(커밋 뒤)" 절과 "반영" 절
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰(두 축)와 반영, 프로브를 넓혀 다시 재기, 커밋까지 했고 남은 단계는 PR 직전 리뷰, 푸시와 PR, 봇 반영과 병합, 일지의 "다음" 절, 회고, 다음 지시문이다(일지 docs/journal/2026-11-27-0407-widget-runtime-values-spec.md). 그 커밋은 푸시하지 않았고 PR은 열지 않았다. 일지는 커밋 뒤에 더 쓴 채라 새 세션이 이어 쓰고 커밋한다. to-spec의 차례는 처음부터 밟지 않고, 사용자에게 다시 묻지 않으며, 명세를 다시 쓰지 않는다. PR 직전 리뷰에 넘길 밀 주장과 PR 본문의 리뷰어 참고에 적을 것은 그 일지의 "둘째 인계(커밋 뒤)" 절에 있다. 이 기능의 일은 아니지만 앞 지시문이 알린 것을 잇는다: admin-login 05(PR #653)의 봇 보류 하나가 병합된 일지 "다음"에 없고 PR 코멘트(issuecomment-7199113820)에만 있다. 관리 라우터의 public에 /health 외의 라우트가 붙는 것을 막는 시험이 없다는 지적이고, admin-login을 잇는 세션이 이어받는다.
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 주 체크아웃이 지금 origin/dev를 따라가 있는지는 이 세션이 보지 않았다.
이번 요청 범위: PR과 병합까지
```

넘기기 전의 차례를 밟았다. 제목을 `docs/widget-runtime-values-spec (인계함)`으로 바꿨고, 이 세션이 띄운 백그라운드 작업은 커밋 하나였는데 이미 끝나 멈출 것이 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/widget-runtime-values-spec`은 `is not locked`로 끝났다. 앞 세션이 풀어 둔 뒤 이 세션의 `EnterWorktree(path)`가 다시 잠그지 않은 것으로 보이고(어림), 절차대로 넘어갔다.

open-session을 부른다 2026-11-26T20:41:43Z

## 커밋 뒤에 이어받은 세션

둘째 인계로 연 새 세션이 이 절부터 쓴다. 세션 제목 `docs/widget-runtime-values-spec`, 모델 Fable 5.2. 첫 메시지는 위 "둘째 인계(커밋 뒤)" 절의 "낸 지시문"을 붙여 넣은 글이었고, 그 앞에 open-session이 붙이는 한 줄(`.claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다 … 인자: widget-runtime-values`)이 있었다. 사용자가 따로 더한 말은 없다.

- 제목을 브랜치 이름으로 바꾸고(앱이 지은 제목 "Widget runtime values 명세"가 묻지 않고 바뀌었다) `git worktree list`에서 이 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. `git status --short`는 이 일지 하나만 고친 채였고 HEAD는 `8d074ba43`이었다. 인계 절이 적은 그대로다.
- `git fetch origin` 뒤 `uv run python tools/sibling_overlap.py`는 "이 브랜치의 새 번호 없음", "번호 겹침 없음", "함께 고친 파일 없음"이었고 기준 브랜치 줄은 `origin/dev afba836` 그대로였다. 커밋 뒤로 dev에 새로 들어온 것이 없다.
- `list_sessions`에서 같은 기능을 맡은 다른 세션은 앞의 두 인계 세션뿐이었다. 직전 세션(`(인계함)`)은 `isRunning`이 참이었고 마지막 활동이 20:43:25Z였다. 이 세션을 연 턴을 마무리하는 중으로 봤다(어림).

### PR 직전 리뷰

서브에이전트 둘을 나란히 띄웠다. `coderabbit-review`(CodeRabbit CLI, 보안·버그·성능 축)와 `bug-perf-review`다. 뒤의 것은 CLI가 돌지 못할 때의 대체지만, CLI에는 밀 주장을 넘기는 인자가 없어(위 "둘째 인계(커밋 뒤)") 셀프 리뷰 반영으로 새로 쓴 문장 열세 항목을 근거와 대 보는 일을 맡기려고 함께 띄웠다. 선례는 postgres-foundation 명세의 PR #606이다(그 PR 본문의 체크리스트를 `gh pr view 606 --json title,body`로 읽었다). 두 브리프 모두 프로브를 다시 돌리지 말라고 했고, 기준은 `afba83679`다.

#### bug-perf-review의 보고

기준 `afba83679`, 범위의 파일 열아홉, 도구 호출 33번(보고의 첫 줄). 지적은 0건이었다. 보고를 줄여 옮긴다.

- 밀 주장 열세 항목이 모두 근거와 맞았다고 보고했다. 프로브는 돌리지 않고 `run.py`를 읽어 대 봤다고 적었다.
- 항목 1, 4. `run.py`의 `serves`가 페이지, 페이지 안 번들, 값 파일, 없는 경로의 `frame-ancestors`와 값 파일의 캐시 머리·내용의 종류·비지 않은 ETag, 글꼴의 다른 출처에 여는 머리, 페이지의 `s-maxage=31536000`을 단언하고, `reflect_round`가 다시 띄운 뒤 ETag가 달라지는 것을, `exits_round`에 `exit_code=1`을 준 세 자리가 종료 코드 1을 단언한다. 시간, 메모리, 크기, 끌 때의 143은 값으로만 적는다.
- 항목 2. 네 실행의 수가 명세, 프로브 README 둘, deploy-package 기능 계획 사이에서 같고 덧셈이 맞는다(32 + 10 + 11 + 37 = 90, 시간을 찍은 마흔 = 14 + 8 + 18, 쓰기 가능한 스물 = 12 + 8, 끄기 스물여덟 = 10 + 3 + 4 + 11). 옛 값(94.3, 0.62, 2.61)은 그 다섯 문서에 남아 있지 않다(Grep 0건).
- 항목 3, 5, 6, 8, 9, 10, 12, 13. `patch-config.mjs`와 `Dockerfile`, `start.ts`와 `next.config.ts`의 머리 주석, `deploy/standalone/compose.yaml`의 시작 유예(위젯만 300초, 공통 30초), release-image 명세의 인용, 옛 말이 남은 자리의 예, 두 기능 계획의 머리, 시험 파일 넷과 든 사례 이름, 네 ADR의 `(바뀜: ADR 0064)` 포인터가 명세의 문장과 맞았다. `git diff --name-only e7c53cba3 afba83679`의 스물일곱 파일 가운데 명세가 읽었다고 든 파일은 없었다.
- 서두의 수. 표 열한 행, "명세가 정했다" 서두 밖 열, "사용자가 골랐다" 본문 하나, "거부한 안:" 문단 일곱, 든 안 열아홉(5 + 4 + 1 + 2 + 3 + 2 + 2).
- 덧붙인 말 둘. 루트 `README.md`에는 "사이트 파일로 빌드"라는 글자는 없고 "위젯 빌드의 입력", "빌드 입력" 꼴만 있다. 명세 "받지 못했을 때"의 "거부한 안:" 문단은 둘째 안("받지 못하면 스스로 여러 번 다시 시도한다")을 안으로 읽어야 열아홉이고 아니면 열여덟이다.

덧붙인 말 둘을 명세와 대 봤고 고칠 것이 없었다. 명세가 든 찾는 말의 예에 "빌드의 입력"이 있어 루트 `README.md`의 "위젯 빌드의 입력"이 그 말에 맞는다(명세 246줄을 읽었다). "거부한 안:" 문단은 일곱 모두 안 한 문장 뒤에 까닭을 잇는 같은 꼴이고(명세 141, 202, 216줄을 읽었다), 그 꼴로 읽으면 "받지 못하면 스스로 여러 번 다시 시도한다"는 안이다.

#### coderabbit-review의 보고

CLI 0.7.5, `Plan: Free`, `Seat: not assigned`였고 리뷰는 끝까지 돌았다. 서브에이전트가 친 명령은 `coderabbit review --agent --base origin/dev --include-untracked`이고, 마지막 이벤트가 `{"type":"complete","status":"review_completed","findings":13}`, 종료 코드 0, 본 파일은 열아홉이었다(모두 서브에이전트의 보고에서 옮겼다). 지적 열셋은 모두 프로브 폴더(`.scratch/widget-runtime-values/probes/prebuilt_start/`)의 것이고 명세와 기능 계획과 일지의 지적은 없었다. 서브에이전트는 다섯을 직접 읽어 유효로, 여덟을 열어 보지 못해 보류로 넘겼고 오탐은 0이었다. 보고를 줄여 옮긴다.

1. (Major, 유효) `run.py:997`. 상태 확인의 대조 회차가 `starting`과 종료 코드 1만 보고, 아무도 듣지 않는 포트라서 실패했다는 표지(연결 거절)를 보지 않는다.
2. (Major, 유효) `run.py:994`. healthy 회차가 healthy와 마지막 종료 코드 0만 보고, 그 성공이 시작 유예 30초 안에 났는지를 보지 않는다.
3. (Major, 유효) `run.py:1169` 근처. 브라우저 섹션의 둘째 회차(사이트 파일을 바꾸고 다시 띄운 뒤)가 첫 회차가 통과했는지를 보지 않고 이어진다.
4. (Major, 보류) `run.py:1121`. 다른 출처 대조가 `"error" in page`만 봐서 연결 실패와 다른 출처 거절을 가르지 않는다.
5. (Major, 보류) `run.py:211`. 이미지를 `f"{REPO}:{target}"` 태그로 가리켜, 빌드 섹션 없이 돈 실행이 앞 빌드의 이미지를 쓸 수 있다.
6. (Major, 보류) `run.py:881`. 읽기 전용의 서는 회차와 링크 없는 이미지의 대조가 tmpfs와 링크 두 요인을 함께 바꾼다.
7. (Minor, 유효) `wait.mjs:17`. 기한을 시도 사이에서만 봐서 마지막 시도가 요청 제한 시간(2초)만큼 기한을 넘길 수 있다.
8. (Minor, 유효) `run.py:1137`. `free_port()`가 포트를 닫은 뒤 쓰는 사이에 다른 프로세스가 가져갈 수 있다.
9. (Minor, 보류) `run.py:671`. `raw.log`에 끝의 로그가 아니라 `until`이 받아 둔 첫 로그가 남는다.
10. (Minor, 보류) `run.py:653`. `du`의 종료 코드를 보지 않고 `.next`의 출력만 본다.
11. (Minor, 보류) `inspect.mjs:37`. 응답 머리의 값을 `startsWith`로 본다.
12. (Minor, 보류) `inspect.mjs:41`. 규칙의 경로를 `includes("runtime.json")`으로 봐서 `/not-runtime.json` 같은 경로도 맞는다.
13. (Minor, 보류) `inspect.mjs:46`. 32MiB를 넘는 파일을 찾기에서 빼고도 빌드 측정을 끝난 것으로 센다.

#### CodeRabbit의 지적을 근거와 대 본 것

열셋 모두 `run.py`, `inspect.mjs`, `wait.mjs`, `browser.mjs`, `fetch.mjs`, `entry.mjs`, `Dockerfile`의 그 자리를 Read로 열어 대 봤다. 서브에이전트가 열어 보지 못해 보류로 넘긴 여덟도 열었다. 오탐은 없었고, 열둘을 고치고 하나(8)는 까닭을 독스트링에 적고 남겼다. 심각도는 CLI가 매긴 것을 그대로 옮긴 것이고, 고친 뒤의 표지가 서는지는 아래 "실행 5"가 본다.

1. 맞다. `health_round`의 대조 회차는 상태 `starting`과 종료 코드 1만 단언했다. 확인 명령은 실패의 까닭을 찍지 않아(`()=>process.exit(1)`), 위젯이 서지 않아 난 실패와 그 포트를 아무도 듣지 않아 난 실패가 같은 결과였다. `.claude/rules/probes.md` 첫 항목(실패를 기대하는 탐침은 실패의 까닭을 본다)에 걸린다. 그 회차가 위젯의 첫 200(`first-ok`)과, 확인이 건 포트에 같은 컨테이너 안에서 건 요청의 연결 거절(`fetch.mjs`가 내는 `ECONNREFUSED`)을 함께 단언하게 고쳤다.
2. 맞다. 지켜보는 루프는 25초 안에 시작하지만 마지막 `docker inspect` 한 번이 늦게 돌아오면 30초 뒤에 본 healthy도 통과했다. healthy 회차가 띄우기 전부터 잰 시간이 30초보다 짧은 것도 단언하게 했다(컨테이너가 시작한 때보다 앞에서 재기 시작하므로 위쪽 어림이다).
3. 맞다. 둘째 회차는 컨테이너 이름이 있는지만 보고 이어졌다. 첫 회차가 표지를 보지 못했으면 둘째 회차의 "뒤바뀌었다"는 견줄 앞 상태가 없다. 첫 회차의 판정을 들고 가서, 측정이 아니면 둘째 회차도 측정 아님으로 센다.
4. 맞다. `browser.mjs`는 `fetch`가 던진 오류를 글자로만 적고(`String(error)`), 연결 실패와 다른 출처 거절이 같은 `TypeError`다. 같은 방문의 콘솔 오류 하나가 위젯 페이지의 주소와 "blocked by CORS policy"와 "No 'Access-Control-Allow-Origin' header"를 함께 드는 것을 단언하게 했다. 이 글자는 Chromium이 그렇게 찍는다고 아는 것이고, 실제로 그렇게 찍히는지는 실행 5가 본다.
5. 맞다. 이미지를 태그로 가리켜, 실행 도중 다른 실행이 같은 태그를 다시 지으면 한 실행 안에서 이미지가 바뀔 수 있었고, 어느 이미지를 쟀는지가 결과에 남지 않았다. 단계마다 처음 쓸 때 태그를 이미지 ID로 풀어 결과에 적고 그 뒤로는 그 ID로 가리키게 했다. `build` 섹션 없이 돈 실행이 앞 빌드의 이미지를 쓰는 것은 그대로이고(프로브 README가 그렇게 돈다고 적는다), 적힌 ID로 어느 이미지였는지 알 수 있다.
6. 맞다. 서는 회차는 링크 있는 이미지에 tmpfs를 주고, 링크 없는 이미지의 대조는 tmpfs도 주지 않아 두 요인이 함께 달랐다. 그 대조에 tmpfs를 줘서 링크 하나만 다르게 했다. `entry.mjs`는 두 파일을 앱 폴더 안의 경로에 쓰므로(그 파일의 `SERVED`, `VALUES`를 읽었다) 링크 없는 이미지는 tmpfs를 줘도 같은 까닭으로 끝날 것으로 봤고, 실행 5가 본다.
7. 맞다. 영향은 없었다. `until`의 제한 90초가 `wait.mjs`의 기한 120초보다 먼저 끝나 그 기한이 판정에 닿지 않는다(`run.py`의 `until`을 읽었다). 고치는 값이 작아 기한을 따로 도는 타이머로 옮겼다.
8. 남긴다. 부모 페이지의 포트는 사이트 파일의 허용 출처에 들어가야 해서 컨테이너를 띄우기 전에 정해야 하고, 그 포트를 여는 것은 뒤에 뜨는 `browser.mjs`다. 그 사이에 다른 프로세스가 포트를 가져가면 `browser.mjs`의 `listen`이나 `docker run -p`가 실패해 그 회차가 측정 아님이 된다(조용히 지나지 않는다. `browse`와 `start`를 읽었다). 그 까닭을 `section_browser`의 독스트링에 적었다.
9. 맞다. 판정에 쓰는 기록(`logs`)은 원본 기록에 남기지 않고, `until`이 첫 200 때 받아 둔 더 짧은 기록만 남겼다. 판정에 쓴 기록도 `raw.log`에 남기게 했다(`judged_logs`).
10. 맞다. 파이프 뒤라 `du`의 종료 코드가 보이지 않았고 `.next`라는 글만 봤다. `du`를 셸 없이 불러 종료 코드 0과 세 폴더 모두의 크기를 단언하게 했다.
11. 맞다. `startsWith`는 다른 지시어 뒤에 `frame-ancestors`가 오는 머리를 세지 않아, 그런 머리가 더 있어도 "정확히 하나"가 통과한다. 값에서 지시어 이름을 갈라 세게 했다.
12. 맞다. 규칙의 경로를 값 파일의 경로(`/widget/runtime.json`)와 같은지로 보게 하고, `run.py`가 그 규칙이 하나이고 `Access-Control-Allow-Origin: *` 하나만 다는 것까지 단언하게 했다. 지금 이미지의 모양은 `docker run --rm --entrypoint node wrv-img:image-inplace /probe/inspect.mjs manifest`로 손으로 봤다(규칙 하나, 그 경로, 그 머리 하나).
13. 맞다. 32MiB를 넘겨 훑지 않은 파일의 목록을 `inspect.mjs`가 내고 `run.py`가 빈 목록인 것을 단언하게 했다.

고친 뒤 `uv run python tools/rewrap_comments.py`, `uv run ruff format`, `uv run ruff check .scratch/widget-runtime-values`(All checks passed), `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`(오류 0)를 쳤다.

`inspect.mjs`와 `wait.mjs`는 이미지에 복사되는 파일이라 고친 판을 재려면 이미지를 다시 지어야 한다. 그리고 지금 남은 이미지는 03:56~04:01(한국 시각)에 지은 것이고(`docker image inspect -f '{{.Created}} {{.Id}}'`로 손으로 봤다), 이 브랜치가 origin/dev를 빨리 감기로 받은 것은 05:23이다(`git reflog --date=iso`). 받은 변경에 `web/packages/api-client/`가 들어 있어 다시 지으면 Next 빌드가 새로 돌 것으로 봤다(어림). 그래서 일곱 섹션 전체를 다시 돌린다.

#### 실행 5

고친 판으로 일곱 섹션 전체를 한 번에 돌렸다(`uv run python .scratch/widget-runtime-values/probes/prebuilt_start/run.py --sections build,start,reflect,readonly,sitefile,health,browser --rounds 3 --work <스크래치 폴더>`). 종료 코드 0, 측정 37회차, 측정 아님 0회차였다. 원본 기록의 처음과 끝 시각은 06:00:05와 06:03:28로 203초였다(`raw.log`를 손으로 봤다).

- 이미지가 다시 지어졌다. 빌드 식별자가 `zfC9XffWGHfNZNhDmSgH9`에서 `xOpdgCVqV4HvhKmSucRxT`로 바뀌었고, `run.py`가 적은 `image`의 ID는 `sha256:f823c11dbe90…`, `image-inplace`는 `sha256:02f56d0bd14c…`다(실행 전에는 `sha256:40be17c6de9f…`와 `sha256:e46f78a63b2d…`였다). `build` 단계는 25.7초였고 그 가운데 빌드를 부르는 `RUN` 한 줄이 22.4초였으며 의존성을 까는 층은 캐시에서 왔다(뒤의 둘은 `raw.log`를 손으로 봤다). 지금의 `web/`은 `afba83679`의 것과 같고(`git diff --stat afba83679 HEAD -- web`의 출력이 없었다), `e7c53cba3`과는 `packages/api-client`의 파일 둘이 다르다(`git diff --stat e7c53cba3 afba83679 -- web`).
- 새로 더한 표지가 첫 실행에서 모두 섰다. 결과를 보고 표지를 다시 고친 것은 없다.
  - `health`의 대조: 상태 `starting`, 남은 기록 다섯이 모두 종료 코드 1, 위젯의 첫 200이 기록에 있고(`served_3000=True`), 확인이 건 포트에 건 요청이 `ECONNREFUSED`였다.
  - `health`의 healthy 세 회차: 2.62초, 2.95초, 2.91초로 모두 30초보다 짧았다.
  - `browser`: 다른 출처 페이지의 콘솔에 "Access to fetch at 'http://127.0.0.1:50412/widget' from origin 'http://other.localhost:50411' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource."가 있었다(`cross_origin_page_cors=True`). 허용 출처 페이지의 콘솔에도 같은 꼴의 글이 있었다. 두 페이지가 모두 위젯 페이지를 다른 출처에서 `fetch`로 받아 보기 때문이다.
  - `readonly`의 `image-inplace` 대조는 tmpfs를 준 채로도 `/app/web/apps/widget/.next/routes-manifest.json`을 열다 `EROFS`로 끝났다.
  - `build`: 훑지 않고 넘긴 파일이 없었고(`skipped=[]`), 값 파일의 규칙은 `/widget/runtime.json`에 `Access-Control-Allow-Origin: *` 하나였으며, `du`는 종료 코드 0으로 `.next` 22, `public` 7, `node_modules` 480을 냈다.
- 회차마다 적은 값이 앞 네 실행의 범위를 다섯 군데에서 벗어났다. 첫 200까지의 시간은 열여섯 회차 0.67~1.96초로 위 끝이 1.78에서 1.96으로(256MiB로 제한한 회차다. 제한 없는 열다섯은 0.67~1.41초로 앞 범위 0.61~1.67초 안이다), 진입 단계는 0.010~0.036초로 위 끝이 0.029에서 0.036으로, 메모리 최고치는 제한 없는 열다섯 회차 88.8~93.9MiB로 아래 끝이 88.9에서 88.8로, 제한한 회차 77.7MiB로 아래 끝이 78.3에서 77.7로, healthy까지는 위 끝이 2.66에서 2.95로 움직였다. 끄기는 열한 회차 0.17~1.03초에 모두 종료 코드 143, Next의 `Ready in`은 140~399ms로 앞 범위 안이다. 이미지의 크기 셋(690.6, 881.9, 666.9MiB)과 `du`의 세 값은 앞 실행과 같았다.

요약 때 적어 둔 계획은 실행 5의 수를 앞 네 실행의 수에 합치지 않고 따로 적는 것이었다. 값이 앞 범위를 벗어났으므로 그 범위를 인용한 자리(명세의 첫 응답 시간, 메모리, healthy)를 고쳐야 했고, 인용하는 범위가 README에 있어야 해서 README에는 합친 범위와 따로 본 범위를 함께 적었다.

#### 반영(PR 직전 리뷰)

CodeRabbit CLI의 열셋 가운데 열둘을 고치고 하나(8)를 남겼다. `bug-perf-review`는 지적이 없었다. 고친 파일은 `run.py`, `inspect.mjs`, `wait.mjs`(프로브), 프로브 README 둘, 명세, deploy-package 기능 계획, 이 일지다.

고친 것. 새로 쓴 사실 문장은 원문을 옮긴다.

1. 프로브의 표지와 대조(위 "CodeRabbit의 지적을 근거와 대 본 것"의 1~7, 9~13)와 실행 5.
2. 프로브 README. "잰 판"에 두 빌드를 갈라 적었다. "근거의 종류"를 다섯 실행 127회차(32 + 10 + 11 + 37 + 37)로 고치고 한 문장을 더했다. 원문: "실행 5의 이미지는 앞 넷과 다른 빌드라(위 "잰 판"), 아래에서 범위를 합쳐 적는 자리에는 앞 네 실행의 범위와 실행 5의 범위도 따로 적는다." 결과 4의 결론을 고쳤다. 원문: "앞 네 실행의 `image-inplace` 대조는 tmpfs도 주지 않아, 서는 회차와 요인 둘(링크와 tmpfs)이 함께 달랐다. 실행 5는 그 대조에 서는 회차와 같은 tmpfs를 줘 링크 하나만 다르게 했고, 같은 `EROFS`로 끝났다. 그래서 읽기 전용 루트에서 서려면 tmpfs 폴더와 링크가 둘 다 있어야 한다." 결과 6과 7에 실행 5가 단언한 실패의 까닭을 적고, 앞 실행들은 그 까닭을 가르지 못했다고 적었다. "결과를 본 뒤 바꾼 것"에 "PR 직전 리뷰 뒤 고친 표지와 대조(실행 5)"를 더했고 끝은 이렇다. 원문: "다만 새 표지가 다른 까닭의 실패에서는 나지 않는다는 것을 따로 돌려 보지는 않았다. 연결 거절의 오류 번호와 콘솔의 CORS 글은 그 뜻으로 고른 것이다(어림)."
3. 다섯 실행을 합친 수로 고쳤다(명세, 프로브 README 둘, deploy-package 기능 계획). 첫 응답까지 0.61~1.96초(시간을 찍은 쉰여섯 회차: `start` 스물하나, `reflect` 열둘, `readonly`의 뜬 회차 스물셋), 메모리 최고치 77.7~95.6MiB(제한 없는 쉰세 회차 88.8~95.6MiB, 256MiB로 제한한 세 회차 77.7~81.6MiB), healthy까지 2.59~2.95초(아홉 회차), 끄기 0.16~1.16초(서른아홉 회차), 사이트 파일 A로 선 회차 스물하나, 다시 띄운 회차 열일곱, 읽기 전용 회차 스물셋과 쓰기 가능한 회차 서른. 앞 네 실행의 수는 README에 적혀 있던 것에 실행 5의 값을 손으로 더한 것이다(실행 5의 값은 작업 출력에서 읽었다. 앞 네 실행의 원본 기록은 다시 열지 않았다).
4. 명세 "명세 전의 확인"의 실행 수 문장. 원문: "다섯째 실행은 PR을 열기 전의 리뷰가 짚은 표지와 대조를 고친 뒤, 그 사이에 받은 origin/dev(`afba83679`)의 `web/`으로 이미지를 다시 지어 일곱 섹션 전체를 돌린 것이다(둘 다 프로브 README의 "결과를 본 뒤 바꾼 것"). 아래 표와 이 명세의 범위는 다섯 실행을 합친 것이고, 앞 네 실행과 다섯째 실행을 따로 본 범위는 프로브 README의 결과 2와 6에 있다."
5. 명세 "위젯 이미지"의 이미지를 짓는 시간. 원문: "이 PC에서 그 단계는 캐시 없이 64.2초와 73.8초였고, 의존성을 까는 층이 캐시에서 온 채 소스가 바뀌어 다시 돈 다섯째 실행에서는 25.7초였다(프로브 결과 1. 64.2초는 손으로 봤다. 세 값이 벌어진 까닭은 가르지 않았다)."

남긴 것과 이유.

- CodeRabbit 8(`free_port`가 고른 포트를 닫고 돌려준다). 부모 페이지의 포트가 사이트 파일에 먼저 들어가야 해서 미리 골라야 하고, 그 사이에 포트를 빼앗기면 그 회차가 측정 아님이 되어 종료 코드가 1이다. 까닭을 `section_browser`의 독스트링과 프로브 README에 적었다.

명세 서두의 수는 이 반영으로 바뀌지 않았다(표의 행, "명세가 정했다"와 "사용자가 골랐다" 표시, "거부한 안" 문단을 더하거나 빼지 않았다).

다시 돌린 명령. `uv run python tools/plan_table.py`(출력 없음, `.scratch/plan.md` 그대로), `uv run ruff check .`(All checks passed), `uv run ruff format --check .`(2693 files already formatted), `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`(오류 0), `uv run python tools/sibling_overlap.py`(번호 겹침 없음, 함께 고친 파일 없음. origin/dev는 `afba836` 그대로다), `git branch --show-current`(`docs/widget-runtime-values-spec`). 반영한 뒤 셀프 리뷰(`/code-review`)는 다시 돌리지 않았다. 고친 것이 PR 직전 리뷰의 지적을 따른 프로브의 표지와 그 결과의 수이고, PR의 봇 둘이 이 커밋을 본다. 손으로 치는 나머지 검사는 커밋의 pre-commit으로 갈음한다.

#### 둘째 커밋과 pre-commit

`git commit -F <메시지 파일>`이 커밋 `d92b8965b`를 만들었다(`docs: PR 직전 리뷰가 짚은 프로브의 표지와 대조를 고치고 다시 잰다 (widget-runtime-values)`, 파일 여덟). 명령은 백그라운드로 돌렸고 끝 알림을 기다렸다. 종료 코드는 0이었다.

- `ruff check`, `ruff format`: Passed.
- `checks`(`tools/run_checks.py`): Passed, 690.89초. 안의 검사는 check-ticket 0.9초, check-notes 1.7초, lint-imports 3.3초, zizmor 4.5초, check-instructions 15.0초, check-type-escapes 16.4초, pyright 54.2초, pyright-linux 55.0초, run-hooks 69.7초, pytest 655.2초, web-verify 689.3초였고 모두 Passed다.
- markdown tables, line separators, mutation tables, quotes(경고만 낸다), commit message: Passed.
- Skipped는 둘이다. canary specs와 constitution version이고 둘 다 `(no files to check)`였다. 손으로 치지 않았다.
- quotes 검사의 경고 둘은 원천이 저장소 밖이라 그대로 둔다. 일지 320줄은 앱이 지은 세션 제목이고, 389줄은 실행 5의 출력에 찍힌 Chromium의 콘솔 글이다.

이 커밋도 제품 코드를 건드리지 않아 LLM 테스트, e2e, 사진 비교는 돌리지 않았다.

커밋 명령의 결과에 인계의 계기가 붙어 왔다(세션 컨텍스트 237,854 토큰, 단계 경계 `커밋 뒤`). `.claude/skills/next-session/handoff.md`를 Read로 열어 대 봤고 넘기지 않았다. 이 세션의 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해, 인계로 연 세션이 넘겨받은 경계에 다시 온 것이다(그 파일의 1, 셋째 항목).

#### 푸시와 PR

`git fetch origin` 뒤에도 origin/dev는 `afba83679` 그대로였다. `git push -u origin docs/widget-runtime-values-spec`으로 두 커밋을 올리고 PR #654를 열었다(`gh pr create --base dev`, 제목은 첫 커밋의 제목과 같다. https://github.com/njh6803/agent-os/pull/654). 면제 PR이다(기능의 명세, 가리키는 티켓 없음).

- 본문은 PR 템플릿을 채웠다. 체크리스트의 PR 직전 리뷰 줄에 CLI가 돈 것(0.7.5, `Plan: Free`, `Seat: not assigned`, `--base origin/dev`, 파일 19, findings 13), 고친 열둘, 남긴 하나의 판정과 고치는 데 드는 값, `bug-perf-review`를 함께 돌린 까닭과 지적 0건을 적었다.
- "리뷰어 참고"에 셋을 적었다. 값 파일을 받지 못하면 위젯이 닫힌 채 남는다는 것은 사용자에게 묻지 않고 명세가 정했고 티켓으로 나누기 전에 뒤집을 수 있다는 것, 네 문서가 같은 측정의 수를 들고 다섯째 실행을 더한 셈은 손으로 했다는 것, 다섯째 실행에서 더한 두 표지가 다른 까닭의 실패에서는 나지 않는다는 것을 따로 돌려 보지 않았다는 것이다.
- 앱의 PR 감시는 이 세션에 묶였다(`get_status`가 `bound: true`, 검사는 통과 2, 대기 7, 건너뜀 2였다). `@coderabbitai review` 코멘트는 이 세션이 남기지 않았다(아래 인계).

### 셋째 인계(PR 연 뒤)

PR을 여는 명령의 결과에 인계의 계기(`hook_handoff`)가 붙어 왔다. 세션 컨텍스트가 295,183 토큰으로 문턱 200,000을 넘은 채 단계 경계 `PR 연 뒤`에 왔다는 알림이다. `handoff.md`의 인계하지 않는 때 다섯에 들지 않았다. PR은 열렸고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`로 시작해 지금 경계와 다르고, 이 세션이 쓴 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다.

이 세션의 제목은 `docs/widget-runtime-values-spec`이다. 넘기기 전에 `docs/widget-runtime-values-spec (인계함)`으로 바꾼다.

새 세션이 이어받는 상태는 아래다.

- 커밋 `d92b8965b`까지 푸시했고 PR #654가 열려 있다. 봇 회차는 시작하지 않았다. 첫 `@coderabbitai review` 코멘트와 `tools/wait_ci.py` 대기는 새 세션이 한다.
- 이 일지는 둘째 커밋 뒤에 고친 채다("둘째 커밋과 pre-commit", "푸시와 PR", 이 절). 새 세션이 이어 쓰고 봇 회차의 커밋에 싣는다.
- 남은 차례: 봇 회차 반영, 이 일지의 "다음" 절, 회고, 병합, 다음 지시문. 다음 지시문의 다음 단계는 이 명세를 티켓으로 나누는 일로 본다(명세 검토 `spec-reviewer` 뒤 `/to-tickets`).
- 봇이 수의 일치를 짚으면 대 볼 자리. 다섯 실행을 합친 수는 위 "반영(PR 직전 리뷰)"의 3에 한 줄로 모아 적었고, 실행 5만의 값은 위 "실행 5"에 있다. 실행 5의 원본 기록(`raw.log`, `results.jsonl`)은 이 세션의 스크래치 폴더(`wrv-run5`)에 있어 새 세션에서 보이지 않을 수 있다. 다시 내려면 프로브를 다시 돌린다(이미지가 남아 있으면 126초쯤이다).
- PR 직전 리뷰에서 남긴 하나(`free_port`가 고른 포트를 닫고 돌려주는 것)는 PR 체크리스트에 판정과 값을 적었다. 봇이 같은 자리를 다시 짚으면 그 줄을 근거로 판정한다.
- 주 체크아웃은 이 세션이 본 때 origin/dev보다 뒤처져 있었다(`tools/sibling_overlap.py`가 루트를 `e7c53cb`로 보였다). 당기지 않았다.

앞 지시문이 "이 기능의 일은 아니지만" 알린 것(admin-login 05, PR #653의 봇 보류 하나)은 이번 인계 지시문에도 그대로 옮겼다.

낸 지시문은 아래다.

```
다음 작업: 기능 widget-runtime-values. 위젯 이미지를 미리 지어 두고 컨테이너가 뜰 때 사이트 파일의 허용 출처와 요청 글자 수 상한만 받게 해, 뜰 때마다 하던 빌드를 없앤다.
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다.
시작 프롬프트: /to-spec widget-runtime-values
브랜치: docs/widget-runtime-values-spec
모델: Sonnet 5.5 / high. 2의 잇는 지시문.
읽을 것: docs/journal/2026-11-27-0407-widget-runtime-values-spec.md의 "셋째 인계(PR 연 뒤)" 절과 "반영(PR 직전 리뷰)" 절
이어받을 상태: 인계: PR 연 뒤. PR #654를 열었고 merge.md 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다(일지 docs/journal/2026-11-27-0407-widget-runtime-values-spec.md). 남은 단계는 봇 회차 반영, 일지의 "다음" 절, 회고, 병합, 다음 지시문이다. 일지는 둘째 커밋(d92b8965b) 뒤에 더 쓴 채라 새 세션이 이어 쓰고 봇 회차의 커밋에 싣는다. to-spec의 차례는 처음부터 밟지 않고, 사용자에게 다시 묻지 않으며, 명세를 다시 쓰지 않는다. 봇이 수의 일치나 PR 직전 리뷰에서 남긴 지적(free_port)을 짚을 때 대 볼 자리는 그 일지의 "셋째 인계(PR 연 뒤)" 절에 있다. 이 기능의 일은 아니지만 앞 지시문이 알린 것을 잇는다: admin-login 05(PR #653)의 봇 보류 하나가 병합된 일지 "다음"에 없고 PR 코멘트(issuecomment-7199113820)에만 있다. 관리 라우터의 public에 /health 외의 라우트가 붙는 것을 막는 시험이 없다는 지적이고, admin-login을 잇는 세션이 이어받는다.
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 주 체크아웃은 이 세션이 본 때 origin/dev보다 뒤처져 있었고 당기지 않았다.
이번 요청 범위: PR과 병합까지
```

넘기기 전의 차례를 밟았다. 제목을 `docs/widget-runtime-values-spec (인계함)`으로 바꿨고(앱이 묻지 않고 바꿨다), 이 세션이 띄운 백그라운드 작업은 실행 5와 커밋 둘이었는데 둘 다 끝나 멈출 것이 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/widget-runtime-values-spec`은 `is not locked`로 끝났고 절차대로 넘어갔다.

open-session을 부른다 2026-11-26T21:27:01Z

인계 못함 PR 연 뒤

`open-session`의 3(연다)에서 막혔다. `pwsh -NoProfile -File C:\project\agent\tools\open_session.ps1 -Action send -Folder C:\project\agent -PromptFile <파일>`을 PowerShell 도구로 치자 자동 모드의 권한 판정이 그 호출을 거부했다(사유로 찍힌 글은 `[Unsanctioned Communication]`이다). 스크립트는 돌지 않았고 새 세션은 생기지 않았다. 그 앞의 1(같은 제목으로 도는 다른 세션이 없다. `list_sessions`에서 도는 세션이 하나도 없었다)과 2(프롬프트 파일)는 지났다. 거부를 돌아가는 다른 길(`start_session` 등)은 쓰지 않았다. `handoff.md` 4의 "열기"대로 제목을 `docs/widget-runtime-values-spec`으로 되돌렸고, 멈춘 대기는 없었으며, 이 세션에서 다음 단계(`merge.md` 2의 봇 회차)를 잇는다. 위 "낸 지시문"은 쓰이지 않았다.

### PR 봇 회차 1

인계가 막힌 뒤 이 세션이 이었다. `@coderabbitai review` 코멘트를 21:28:08Z에 남겼고(issuecomment-7203755743), `gh pr checks 654`를 한 번 읽은 뒤 `uv run python tools/wait_ci.py 654`를 백그라운드로 걸고 턴을 끝냈다. 끝 알림으로 깨어나 `/pr-feedback 654`의 차례대로 읽었다. 이 PR의 첫 회차다.

#### 봇의 보고

- claude-review(21:25:47Z, issuecomment-7203718015): "지적 없음". 바뀐 파일 열아홉이 모두 `.scratch/`와 `docs/journal/`이고 `src/`, `sdk/`, `openapi.json`을 건드리지 않았다는 것, 제목에 느낌표가 없는 것이 맞다는 것을 본 범위로 적었다. 코멘트가 있고 본 범위를 적었으므로 리뷰 없는 초록이 아니다.
- CodeRabbit(21:34:42Z의 리뷰): "Actionable comments posted: 11". 인라인 코멘트 열하나를 `gh api repos/{owner}/{repo}/pulls/654/comments --paginate`로 모두 읽었다. Major 넷, Minor 일곱이고, 하나는 프로브 README의 문장, 열은 `run.py`다. 명세와 기능 계획과 일지의 지적은 없었다. `@coderabbitai review`에는 6초 뒤 "Review finished"라는 답이 달렸다(이미 본 커밋은 다시 보지 않는다는 안내가 함께 있었다).
- 검사는 모두 통과였고 `llm`만 건너뜀이었다(`gh pr checks 654`).

CodeRabbit의 지적을 심각도와 자리로 줄여 옮긴다(심각도는 봇이 매긴 것이다).

1. (Minor) 프로브 README 75줄. 읽기 전용 하나만 건 회차를 "compose가 web 컨테이너에 주는 꼴 그대로"라고 적었는데 그 회차도 `--network none`으로 떴다.
2. (Major) `run.py:237`. 이미지 ID를 읽지 못하면 태그로 띄워, 어느 이미지를 썼는지 적지 못한 회차가 측정으로 세어진다.
3. (Minor) `run.py:262`. 실행 끝의 지우기가 원본 기록(`raw.log`) 쓰기에 기대어, 쓰기가 실패하면 컨테이너와 볼륨이 남는다.
4. (Major) `run.py:322`. `docker logs`가 실패한 출력을 정상 기록과 같은 글로 돌려줘, 기록을 읽지 못하고도 "빌드 머리말이 없다"가 통과한다.
5. (Minor) `run.py:498`. 빌드 식별자를 단계 이름으로 기억해, 같은 실행에서 단계를 다시 지으면 새 이미지를 옛 식별자와 견준다.
6. (Minor) `run.py:627`. 지은 뒤 태그를 다시 풀어, 같은 Docker 데몬의 다른 실행이 그 사이에 옮긴 이미지를 집을 수 있다.
7. (Major) `run.py:639`(663, 688줄도). 이번 빌드가 실패해도 앞서 지어 둔 이미지가 남아 있으면 뒤의 검사가 그 이미지로 측정을 적는다.
8. (Minor) `run.py:718`. 첫 200을 내지 못한 컨테이너를 끄지 않고 돌아가, 뒤 회차가 그 컨테이너와 CPU와 메모리를 나눠 쓴다.
9. (Minor) `run.py:925`(933줄도). 읽기 전용으로 서는 회차는 네트워크를 끊는데 두 대조는 끊지 않아 요인 하나만 다른 비교가 아니다.
10. (Minor) `run.py:1039`. healthy를 본 시각이 지켜보는 25초 안인지를 판정에 쓰지 않는다.
11. (Major) `run.py:1059`(1065~1068줄도). 듣지 않는 포트 대조가 먼저 적힌 확인의 종료 코드와 나중에 따로 건 요청의 연결 거절을 묶어, 센 확인이 위젯의 첫 200 뒤에 돌았는지와 그 확인이 연결 거절을 받았는지를 알 수 없다.

#### 지적을 근거와 대 본 것

열하나 모두 그 자리를 Read로 열어 대 봤고 모두 맞았다. 첫 회차라 Minor도 지적마다 판단했고, 열하나를 모두 고쳤다(보류 없음). 봇의 코멘트 본문에 든 "고치는 프롬프트"는 따르지 않고 지적만 읽었다.

1. 맞다. `readonly_round`가 모든 갈래에 `--network none`을 줬다. 문장만 낮추지 않고 그 회차를 compose의 꼴대로 네트워크를 붙여 띄우게 했다. 회차마다 컨테이너 안의 `/sys/class/net`을 읽어, 네트워크를 붙인 회차는 `lo` 밖의 장치가 있고 끊은 회차는 `lo`뿐인 것을 표지로 단언한다. 회차 수는 그대로다.
2. 맞다. `image`가 조회에 실패하면 태그를 돌려줬다. 조회가 실패하면 예외를 던져 그 회차가 측정 아님이 되게 했다(`pin`).
3. 맞다. 실행 끝의 지우기(`sweep`)가 부르는 docker 호출을 원본 기록에 쓰지 않게 하고, 지운 수와 종료 코드는 화면에 찍는다.
4. 맞다. `logs`가 종료 코드를 든 채 돌아오게 하고, 판정에 쓰는 기록(`judged_logs`)은 종료 코드가 0이 아니면 예외를 던진다. "빌드 머리말이 없다"는 판정에는 그 기록에 첫 200의 줄이 있는 것도 더했다.
5. 맞다. 빌드 식별자를 이미지 ID마다 기억하고, 읽지 못한 값은 기억하지 않는다.
6. 맞다. `docker build --iidfile`로 빌드가 낸 ID를 바로 받아 쓴다. 이 PC의 Docker Desktop에서 그 파일의 값이 `docker image inspect`의 `.Id`와 같은 `sha256:` 꼴인 것은 시험 실행의 원본에서 봤다(손으로 봤다).
7. 맞다. 빌드를 부르기 전에 그 단계를 "이 실행에서 실패"로 적어 두고 성공해야 지운다. 그렇게 적힌 단계의 이미지를 찾으면 예외라, 뒤의 검사가 측정 아님이 된다.
8. 맞다. 회차가 띄운 컨테이너를 그 회차가 끝날 때(일찍 돌아가거나 예외로 끝나도) 지운다(`owned`, `owned_round`). `browser`는 두 회차가 같은 컨테이너를 이어 써서 섹션이 끝날 때 지운다.
9. 맞다. 두 대조에도 `--network none`을 줬다.
10. 맞다. 양성 판정을 healthy를 본 시각이 25초보다 짧은 것으로 좁혔다(`waited < HEALTH_WINDOW < START_PERIOD`).
11. 맞다. PR 직전 리뷰의 1번을 고치며 넣은 "따로 건 요청"의 틈을 짚은 것이다. 대조의 확인 명령이 실패의 오류 코드를 스스로 찍게 하고, Docker가 남긴 확인 기록(`.State.Health.Log`)에서 위젯의 첫 200보다 뒤에 시작한 확인이 하나 이상이고 그 확인이 모두 종료 코드 1과 `ECONNREFUSED`를 남긴 것을 단언한다. 따로 건 요청은 뺐다.

고친 뒤 `uv run python tools/rewrap_comments.py`는 종료 코드 1이었다(독스트링 두 곳은 감았고 코드 줄 하나를 "주석·독스트링 문단이 아니다"로 남겼다). 그 줄은 `uv run ruff format`이 감았고, `uv run ruff check .scratch/widget-runtime-values`(All checks passed)와 `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`(오류 0)가 통과했다.

#### 실행 6

고친 것은 `run.py`뿐이고 이미지에 복사되는 파일은 그대로라 이미지를 다시 짓지 않아도 됐다(프로브 `Dockerfile`의 `COPY` 줄을 읽었다). 다만 11번의 단언은 Docker가 남기는 확인 기록의 모양에 기대므로, 전체를 돌리기 전에 `--sections build,health --rounds 1`로 한 번 돌려 원본에서 그 모양을 봤다(06:53:53~06:54:32, 열한 회차 모두 측정. 결과에는 넣지 않았다). 기록의 `Start`는 나노초까지 든 시각이고 끝이 `Z`였으며, `Output`에 확인 명령이 찍은 글이 실렸다.

이어서 일곱 섹션 전체를 돌렸다(`--sections build,start,reflect,readonly,sitefile,health,browser --rounds 3`). 종료 코드 0, 측정 37회차, 측정 아님 0회차였고, 원본 기록의 처음과 끝 시각은 06:54:41과 06:56:42로 121초였다(`raw.log`를 손으로 봤다). 결과를 보고 표지를 다시 고친 것은 없다.

- 이미지는 실행 5와 같다. 층이 모두 캐시에서 와 `image`가 `sha256:f823c11dbe90…`, `image-inplace`가 `sha256:02f56d0bd14c…`, 빌드 식별자가 `xOpdgCVqV4HvhKmSucRxT` 그대로였다.
- 네트워크를 붙인 읽기 전용 회차: 장치가 `eth0 lo`였고 첫 200까지 0.65초, 메모리 최고치 92.8MiB였다. 이 꼴로 잰 것은 이 한 번이다.
- 두 대조는 네트워크를 끊고도 같은 `EROFS`로 끝났다.
- `health`의 대조: 위젯의 첫 200이 21:56:06.549Z였고, 남은 확인 다섯은 21:56:20.66Z~21:56:29.05Z에 시작해 모두 종료 코드 1과 `ECONNREFUSED`였다. 가장 이른 것이 첫 200의 약 14초 뒤다.
- healthy 세 회차는 2.58초, 2.59초, 2.59초였다. 좁힌 단언(25초)이 걸러 내는 회차는 만나지 못했다.
- 실행 끝의 지우기는 "sweep volume: 6개, exit=0"만 찍었다. 컨테이너는 회차마다 이미 지워져 있었다.
- 값이 앞 다섯 실행의 범위를 네 군데에서 벗어났다. 첫 200까지의 아래 끝이 0.61에서 0.60초로, 메모리 최고치의 위 끝이 95.6에서 96.2MiB로, healthy의 아래 끝이 2.59에서 2.58초로, Next의 `Ready in` 아래 끝이 126에서 119ms로 움직였다.

실패 쪽 길은 실행 6에서 나지 않아, 다섯을 손으로 한 번씩 일으켜 봤다(커밋하지 않은 `uv run python -c` 스크립트로 `run.py`의 함수를 불렀다. 손으로 봤다). 없는 태그를 ID로 푸는 것, 빌드가 실패했다고 적어 둔 단계의 이미지를 찾는 것, 없는 컨테이너의 판정용 기록을 읽는 것은 모두 기대한 문구의 `RuntimeError`였다. `sleep 300`으로 띄운 컨테이너는 `owned()` 안에서 하나였고 나온 뒤 없었다. 원본 기록의 폴더를 없는 경로로 바꿔 쓰기가 `FileNotFoundError`인 채로도 실행 끝의 지우기가 볼륨을 지웠다. 빌드가 실제로 실패하는 것, 같은 실행 안에서 단계를 다시 지은 뒤 빌드 식별자를 다시 읽는 것, `docker image inspect`나 `docker logs`가 시간 초과로 끝나는 것은 일으켜 보지 않았다(코드를 읽었다).

#### 반영(PR 봇 회차 1)

CodeRabbit의 열하나를 모두 고쳤고 남긴 것은 없다. claude-review는 지적이 없었다. 고친 파일은 `run.py`, 프로브 README 둘, 명세, deploy-package 기능 계획, 이 일지다.

1. 프로브의 표지와 대조와 정리(위 1~11)와 실행 6.
2. 프로브 README. 결과 1~7의 회차 수와 범위를 여섯 실행 164회차(32 + 10 + 11 + 37 + 37 + 37)로 고치고, 결과 4의 문장을 다시 썼다(읽기 전용 하나만 건 회차는 실행 3과 4와 5에서 네트워크도 끊은 채였고, 실행 6이 compose의 꼴대로 네트워크를 붙여 쟀으며 그 꼴로 잰 것은 한 번이다). "결과를 본 뒤 바꾼 것"에 "PR의 리뷰 봇이 짚은 뒤 고친 것(실행 6)"을 더해, 새로 넣은 단언과 길 가운데 실행 6이 실제로 지난 다섯, 손으로 일으켜 본 다섯, 일으켜 보지 않은 것을 갈라 적었다.
3. 여섯 실행을 합친 수로 고쳤다(명세, 프로브 README 둘, deploy-package 기능 계획). 첫 응답까지 0.60~1.96초(시간을 찍은 일흔두 회차: `start` 스물여덟, `reflect` 열여섯, `readonly`의 뜬 회차 스물여덟), 메모리 최고치 77.7~96.2MiB(제한 없는 예순여덟 회차 88.8~96.2MiB, 256MiB로 제한한 네 회차 77.7~81.6MiB), healthy까지 2.58~2.95초(열두 회차), 끄기 0.16~1.16초(쉰 회차), 사이트 파일 A로 선 회차 스물여덟, 다시 띄운 회차 스물둘, 읽기 전용 회차 스물여덟과 쓰기 가능한 회차 마흔. 앞 다섯 실행의 수는 README에 적혀 있던 것에 실행 6의 값을 손으로 더한 것이다(실행 6의 값은 `results.jsonl`에서 읽었다. 앞 실행의 원본 기록은 다시 열지 않았다).
4. 명세 "명세 전의 확인"의 실행 수 문장에 여섯째 실행을 더했고, "단독 compose의 위젯"의 읽기 전용 문장에 compose의 꼴대로 네트워크를 붙여 잰 것이 여섯째 실행의 한 번이라는 말을 더했다.

고친 뒤 옛 수(0.61~1.96, 77.7~95.6, 2.59~2.95, 127회차, 다섯 실행)를 명세, 프로브 README 둘, 두 기능 계획에서 Grep으로 찾아 0건이었다. 프로브 README의 실행마다 적은 범위에 남은 0.61~1.78, 88.9~95.6, 2.59~2.66은 앞 실행들의 값이라 그대로다. 명세 서두의 수는 이 반영으로 바뀌지 않았다.

PR 본문도 같은 수로 고쳤다(여섯 실행 164회차, 0.60~1.96초, 77.7~96.2MiB, 2.58~2.95초, 256MiB로 제한한 회차 넷, 층 캐시가 찬 채 126초와 121초). "리뷰어 참고"에 봇 첫 회차의 반영을 한 항목으로 더하고, 수의 일치와 새 표지의 한계를 여섯째 실행에 맞췄다.

다시 돌린 명령. `uv run ruff check .`(All checks passed), `uv run ruff format --check .`(2695 files already formatted), `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`(오류 0), `uv run python tools/sibling_overlap.py`(번호 겹침 없음, 함께 고친 파일 없음. origin/dev는 `afba836` 그대로다), `git branch --show-current`(`docs/widget-runtime-values-spec`), 아래 회고가 대기열 항목을 고친 뒤의 `uv run pytest -q tests/test_retro_queue_names.py`(10 passed). 손으로 치는 나머지 검사는 커밋의 pre-commit으로 갈음한다. 반영한 뒤 셀프 리뷰(`/code-review`)는 다시 돌리지 않았다. 고친 것이 봇의 지적을 따른 프로브의 표지와 그 결과의 수이고, 푸시하면 PR의 봇 둘이 이 커밋을 다시 본다.

## 회고

단계를 닫으며 돌렸다. 이 일지를 쓴 세 세션(명세를 쓴 세션, 셀프 리뷰와 첫 커밋의 세션, PR 직전 리뷰부터의 이 세션)을 함께 봤다. 앞의 둘은 인계로 끝나 회고를 돌리지 않았다.

후보는 열하나다. 승인 여덟(열린 항목에 회차를 더한 것 여섯, 새 항목 둘), 기각 셋이고 넘긴 것은 없다. 이 세션에서 반영한 것이 없어 harness 티켓을 쓰지 않았다. 만료할 항목은 작업 트리에서 없었다(`uv run python tools/queue_open_rows.py`의 "만료할 항목"이 "(없음)"이라 `--ref origin/dev`의 출력과 겹칠 것이 없다. `git fetch origin` 뒤 origin/dev는 `afba83679` 그대로였다). 새 훅·검사를 지금 반영하거나 다섯째 회차로 올린 것이 없어 `tools/hook_report.py`는 돌리지 않았다.

1. **새 프로브의 표지가 느슨해 리뷰 세 층이 차례로 잡았다.** 승인(회차로 세는 것. `.claude/rules/probes.md` 첫 항목과 셋째 항목을 어겨 리뷰가 잡았다). `run.py`는 `Rounds`를 쓰고 표지도 있었지만, 실패를 기대하는 대조가 상태와 종료 코드만 보았고, 측정이 아닌 회차가 측정으로 세어질 수 있는 길이 남아 있었다. 셀프 리뷰 표준 축이 Major 하나를, PR 직전 CodeRabbit CLI가 열셋(Major 여섯)을, PR의 CodeRabbit 첫 회차가 열하나(Major 넷)를 짚었다. PR 직전 리뷰의 1번을 고치며 넣은 표지(따로 건 요청의 연결 거절)는 가르려던 다른 해석 아래에서도 나는 관찰이라 봇이 다시 Major로 짚었다. 든 값은 세 번의 다시 재기(실행 4, 5, 6)와 그때마다의 문서 고침이다. → probe-round-marked-measured-unconditionally, 15회차.
2. **명세와 프로브 README가 프로브가 잰 것 밖으로 적었다(둘).** 승인(회차). 셀프 리뷰 표준 축의 Major는 프로브가 적기만 한 것을 측정으로 적은 것이고(위 "표준 축의 보고" 1), 봇 첫 회차의 1번은 네트워크를 끊고 돈 회차를 compose의 꼴 그대로라고 적은 것이다. 둘 다 `hook_probe_citing_doc`의 알림을 받아 근거 문장을 원본과 대 본 뒤에 남았다. → 0565, 4회차(179의 11회차).
3. **셋째 인계 열기가 자동 모드의 권한 판정에 거부됐다.** 승인(회차). 사유는 "Unsanctioned Communication"이었다. 같은 날 이 일지의 앞 두 인계 열기는 지나갔다. 인계하지 못한 이 세션은 그 뒤 자동 압축을 두 번 겪으며 봇 회차를 이었다. → open-session-send-denied-despite-allow-rule, 20회차.
4. **문서와 프로브만 든 커밋의 pre-commit이 11분 안팎 걸렸다.** 승인(회차). 첫 커밋은 pytest 593.9초와 web-verify 674.9초, 둘째 커밋은 한 바퀴 690.89초였다. 나란히 돈 다른 세션의 부하는 재지 않았다. 이 절을 싣는 셋째 커밋의 시간은 이 절을 쓸 때 알 수 없어 세지 않았다. → docs-only-commit-precommit-slow-again, 26회차.
5. **PR 직전 리뷰에 밀 주장을 넘길 길이 없었다.** 승인(회차). CLI가 돌아 셀프 리뷰 반영으로 새로 쓴 문장 열세 항목을 넘기지 못했고, `bug-perf-review`를 주장 검증 몫으로 함께 띄웠다(도구 호출 33번, 지적 0건). → cli-review-claims-path, 10회차.
6. **`coderabbit-review`가 지적 여덟을 그 줄을 열지 않고 넘겼다.** 승인(회차). 오탐으로 가르지 않고 열어 보지 못했다고 밝혀 보류로 넘겼고 수도 맞았다. 본 세션이 여덟을 모두 열었고 여덟 다 고칠 것이었다. → coderabbit-review-findings-judged-unopened, 3회차.
7. **봇의 인라인 코멘트 열한 건을 읽는 데 약 25.7K자가 실렸다.** 승인(사건: 그 글을 두 번 읽었다. 판정할 때와, 압축 뒤 이 일지로 옮길 때다. 층: 필요한 칸만 내는 도구. 더하는 것이라 대기한다. 되돌림: PR 하나). 만료된 0573이 같은 일을 2회차까지 셌다. → 새 항목 coderabbit-inline-size(0573의 3회차).
8. **여러 실행을 합친 수를 손으로 다시 세어 네 문서에 옮겼다.** 승인(사건: 첫 세션이 README의 수 셋을 원본과 다르게 적었다가 스스로 찾았고(위 "명세 전의 확인" 끝), 다시 잴 때마다 합친 범위와 회차 수를 손으로 더해 명세, 프로브 README 둘, 기능 계획에 옮긴 것이 세 번이다. 인계받은 세션은 앞 실행의 원본 기록을 열지 못했다. 층: 합친 범위를 스크립트가 내거나, 수를 한 곳에만 두고 나머지는 가리키게 한다. 더하는 것이라 대기한다. 되돌림: PR 하나). → 새 항목 probe-ranges-hand-merged-across-docs, 1회차.
9. **명세가 뒤집히는 시험 사례를 셋이라고 닫아 셌다**(위 "명세 축의 보고" 1). 기각. 닫힌 수 주장은 리뷰의 명세 축이 밀도록 둔 기준이고(닫힌 0020), 그 축이 Major로 잡아 제 몫을 했다. 검사로 옮길 꼴도 표준에 더할 새 기준도 아니다.
10. **첫 선택 화면의 설명이 든 사실을 코드에 대 보지 않은 채 올렸다**(위 "사용자에게 물은 것 하나"). 기각. 이미 있는 훅(`hook_choice_facts`)이 그 자리에서 막았고, 대 본 뒤 같은 질문으로 다시 올렸다.
11. **일지가 ADR 0064의 문장을 원문과 다르게 옮겼다**(위 "커밋과 pre-commit"). 기각. 이미 있는 검사(quotes)가 커밋에서 알렸고 원문대로 고쳤다.

일지에만 남기는 것. 봇의 코멘트를 줄이려던 `gh api … --jq`의 `gsub("\\s+"; " ")`가 "invalid escape sequence"로 실패해, 저장된 결과 파일을 Read로 읽었다(7의 글이 통째로 실린 까닭이다). Grep 도구의 glob에 `{…}/**/*.md` 꼴을 주자 맞는 것이 없다고 나와, 파일 경로를 직접 주어 다시 찾았다(까닭은 가르지 않았다). `인계 못함` 뒤에 인계의 계기가 다시 왔는지는 세지 않았다(이 세션은 그 뒤로 이 절을 싣는 커밋 전까지 커밋하지 않았다).

## 다음

PR #654(명세, 프로브 `prebuilt_start`, 받는 쪽 기능 계획 둘에 넘긴 것, 이 일지)를 병합하면 widget-runtime-values의 명세 단계가 끝난다.

- 주 체크아웃 미갱신: 루트는 dev. `git worktree list`의 첫 줄이 `C:/project/agent e7c53cba3 [dev]`이고 origin/dev(`afba83679`)보다 뒤처져 있다. 이 세션은 워크트리 세션이라 당기지 않았다. 다음 세션이 `tidy-checkouts`를 먼저 돈다.
- 이 PR은 명세 문서와 프로브뿐이라 로컬 모델 시험(`llm_local`)은 병합 조건의 범위에 들지 않는다. LLM 테스트, e2e, 사진 비교도 돌리지 않았다.
- 봇 첫 회차에서 뒤로 넘긴 일은 없다(CodeRabbit 열하나를 모두 고쳤고 claude-review는 지적이 없었다). 이 절을 쓴 뒤의 회차에서 보류한 것이 생기면 PR 코멘트에 지적마다 적는다.
- 다음 단계는 이 명세를 티켓으로 나누는 일이다. 사용자가 `/to-tickets .scratch/widget-runtime-values/spec.md`로 부르고(`next-session` 결정표), 그 직전에 서브에이전트 `spec-reviewer`로 명세를 한 번 본다.
- 티켓으로 나누기 전에 사용자가 뒤집을 수 있는 것 하나. 명세 "받지 못했을 때"는 위젯이 값 파일을 받지 못하면 기본 상한으로 열지 않고 닫힌 채 설정 오류 알림을 보이게 정했다. 사용자에게 묻지 않고 명세가 정한 것이고 PR 본문의 "리뷰어 참고"에도 적었다.
- 명세가 다른 기능에 넘긴 것은 받는 쪽 기능 계획 본문에 있다(`.scratch/site-limits-admin/plan.md`, `.scratch/deploy-package/plan.md`).
- 프로브에서 남긴 것. `browser` 섹션이 쓸 호스트 포트를 미리 고르는 것(`free_port`)은 까닭을 독스트링과 프로브 README에 적고 두었다. 표준 축의 baseline smell 셋(`run.py`의 이름과 되풀이)도 두었다. 재지 못한 것과 일으켜 보지 않은 실패 쪽 길은 프로브 README의 "재지 못한 것"과 "결과를 본 뒤 바꾼 것"에 있다.
- 프로브의 원본 기록(`raw.log`, `results.jsonl`)은 세션 스크래치 폴더에 있고 커밋하지 않았다. 다시 내려면 프로브를 다시 돌린다(이미지가 남아 있으면 2분쯤이다). Next의 판을 올리는 티켓은 이 프로브를 다시 돈다(프로브 README 표).
- 회고가 회차를 더한 항목 가운데 probe-round-marked-measured-unconditionally, 565, open-session-send-denied-despite-allow-rule, docs-only-commit-precommit-slow-again, cli-review-claims-path는 회차 5 이상이라 chore 계기다.
- 이 기능의 일은 아니지만 앞 지시문이 알린 것을 다음 지시문에 그대로 옮긴다. admin-login 05(PR #653)의 봇 보류 하나가 병합된 일지 "다음"에 없고 PR 코멘트(issuecomment-7199113820)에만 있다. 관리 라우터의 public에 /health 외의 라우트가 붙는 것을 막는 시험이 없다는 지적이고, admin-login을 잇는 세션이 이어받는다.
