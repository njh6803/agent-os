# 02: 위젯 관리 서버의 계약에서 만든 화면용 클라이언트 패키지가 서고, 공개 경로를 자격 증명 없이 부른다

**What to build:** web 작업공간에 생성 클라이언트 패키지 `web/packages/widget-admin-client`(패키지 이름 `@agent-os/widget-admin-client`)가 선다. 01이 커밋한 계약 파일 `widget-admin/openapi.json`에서 타입을 생성해 커밋하고, 생성물이 계약과 어긋나면 `pnpm -C web verify`가 빨개진다(사용자 이야기 41의 생성 클라이언트 몫). 패키지는 공개 경로용 팩토리 하나를 낸다. 위젯 출처의 기준 주소를 받아 클라이언트를 짓고, 그 클라이언트로 `/widget-settings/<이름>`을 부르면 요청에 자격 증명이 실리지 않고 머리도 더해지지 않는다(2. 위젯이 다른 출처의 답을 읽으려면 요청이 그래야 한다). portal-admin은 이 패키지에 클라이언트 둘을 더한다(32). 앱이 이 패키지 밖에서 `openapi-fetch`를 직접 import하거나 패키지의 안쪽 파일을 import하면 ESLint가 막는다. 이 기능에는 팩토리를 부르는 앱이 아직 없다. 위젯이 widget-login-state에서, 위젯 관리 화면과 위젯 테스트 페이지가 portal-admin에서 부른다.

사용자가 이 패키지를 01에서 떼는 "4장"을 골랐다(일지 `docs/journal/2026-11-24-2305-widget-admin-server-tickets.md`의 "사용자에게 물은 것 하나"). 그 팩토리를 부르는 화면이 뒤 기능에서야 생겨, 떼어도 깨지는 것이 없다.

근거는 명세 `.scratch/widget-admin-server/spec.md`의 "계약 파일과 생성 클라이언트"(패키지, 팩토리, ESLint 네 자리, web 이미지 셋의 매니페스트 줄), "응답 머리"의 자격 증명과 preflight(브라우저가 다른 출처에 본 요청을 보내기 전에 먼저 보내는 `OPTIONS` 물음. 위젯 관리 서버는 이 물음에 답하지 않으므로 위젯의 요청이 그 물음을 일으키지 않아야 한다) 항목, "문서와 하네스"에서 생성 클라이언트의 변경이 싣는 것, "티켓을 나눌 때 함께 둘 것"의 둘째다. 결정은 ADR 0064 결정 "위젯 관리 서버"다. 이 티켓의 "명세 검토"와 그 번호(S7, S8 같은 것)는 일지 `docs/journal/2026-11-24-2305-widget-admin-server-tickets.md`의 "명세 검토" 절을 가리킨다.

**Blocked by:** 01(위젯 관리 서버가 둘째 설치 묶음으로 서고, 표에 넣은 위젯 설정이 `/widget-settings/<사이트 이름>`에서 토큰 없이 읽힌다). 03과 나란히 돌 수 있다. 두 티켓이 함께 고치는 파일은 루트 `README.md`뿐이고 절이 다르다(파일 목록으로 판단한 것이고 돌려 보지는 않았다).

**Status:** done

### 패키지와 생성물

- [x] `web/packages/widget-admin-client`가 `web/packages/api-client`와 같은 꼴로 계약 파일에서 타입을 생성해 커밋한다. 생성물이 계약과 같은지를 api-client와 같은 자리에서 본다. 생성물도 타입 우회 판정에서 빼지 않는다(원칙 III)
- [x] 의존성은 `openapi-fetch` 하나이고 판은 api-client와 같은 글자로 적는다. `pnpm-lock.yaml`의 변경을 함께 싣는다
- [x] 생성 타입에서 `schema_version`이 빠지지 않는 수이고 리터럴로 좁혀지지 않는지 본다. 판 표시를 견주는 비교가 typescript-eslint의 `no-unnecessary-condition`에 걸리지 않게 하려는 것이다(명세 "판 표시", 명세 검토 B2). 글의 칸과 고르는 값의 칸이 빠지지 않는 칸으로 나오는지도 본다(명세 "답의 모양")

### 공개 경로용 팩토리

- [x] 팩토리 하나가 위젯 출처의 기준 주소를 받아 `openapi-fetch` 클라이언트를 짓고, 모든 요청에 `credentials: "omit"`을 싣고, 머리를 더하지 않는다(명세 "계약 파일과 생성 클라이언트")
- [x] 그 팩토리의 시험은 가짜 `fetch`로 `/widget-settings/<이름>` 요청의 메서드, 주소, 자격 증명, 머리를 본다. 머리에 `Content-Type`도 `Accept`도 없다(명세 "응답 머리"의 preflight 항목이 `openapi-fetch` 0.17.0의 코드를 읽은 것을 이 시험이 실제로 본다)

### 판정자와 이미지

- [x] `web/eslint.config.mjs`에서 api-client 하나만 가리키는 네 자리에 이 패키지를 더한다. `openapi-fetch`의 import를 그 패키지 안에서만 푸는 규칙, 생성 클라이언트를 패키지 이름으로만 import하게 하는 안쪽 import 규칙, 층 경계 둘(atoms·molecules가 막는 대상과 organisms·templates가 막는 대상)이다(명세 검토 S7)
- [x] `web/eslint.config.test.ts`에 규칙마다 이 패키지에서는 지나가고 앱이나 막힌 층에서는 그 규칙으로 걸리는 사례를 붙인다(`.claude/rules/web-workspace.md`의 ESLint 항목). 사례를 먼저 쓰고, 네 자리를 고치기 전에 그 사례가 빨간 것을 본다(원칙 II)
- [x] web 이미지 셋(`deploy/images/admin.Dockerfile`, `widget.Dockerfile`, `portal.Dockerfile`)의 매니페스트 단계에 이 패키지의 `package.json` 줄을 더한다. `tests/tools/test_web_images_manifests.py`가 초록이다(명세 검토 S8)

### 문서

- [x] 루트 `README.md`의 트리에 `web/packages/widget-admin-client`를 더한다
- [x] 생성 클라이언트를 하나로 적은 문장 셋을 두 계약 파일과 두 생성 클라이언트를 말하게 고친다. `docs/constitution/operations.md` pre-commit 절의 web 항목(생성물 최신성을 "루트 `openapi.json`에서 다시 생성한 결과"로 적는다), `docs/constitution/tech.md` 표의 웹 칸(`packages/api-client`만 든다), 루트 `README.md` 트리의 `web/tools` 줄(생성 도구의 설명)이다. 생성과 최신성 검사의 명령 이름이 바뀌면 그 이름도 고친다. 헌법의 판을 patch로 올리고, 판은 커밋 직전의 `tools/sibling_overlap.py`가 낸 형제의 가장 높은 판보다 높게 고른다(명세 "문서와 하네스", ADR 0038의 선례)
- [x] `.claude/rules/web-workspace.md`는 api-client를 이름으로 들지 않아 고치지 않는다(명세 "문서와 하네스"). 이 티켓이 그 파일에 판단 기준을 더하게 되면 새 세션에서 불러 본다(작업 규약 3)

### 마지막 티켓이면

- [x] (이 티켓은 마지막이 아니다. 2026-11-25 병합 직전 `git fetch origin` 뒤 origin/dev에서 03과 04가 `ready-for-agent`이고 이 티켓이 닫혀도 둘이 열려 있어 끝 줄도 기능 단락도 싣지 않는다.) 이 티켓과 04 가운데 늦게 병합하는 쪽이 이 기능의 마지막 티켓이다. 이 티켓이 늦으면 병합 직전에 `git fetch origin` 뒤 기준 브랜치를 합치고 저장소 상태 시험(`test_이_저장소의_…`)을 돌린 뒤, 이 티켓을 닫는 커밋이 기능 계획 `.scratch/widget-admin-server/plan.md`에 `**끝:**` 줄을 적고 기능 단락 `docs/release-notes/features/widget-admin-server.md`를 싣는다(`docs/agents/issue-tracker.md`의 "끝 줄을 적는 때"와 "나란히 돈 마지막 티켓 둘")

### 검증

- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [x] web 이미지 셋의 짓는 파일을 고치므로 단독 배포 e2e를 로컬에서 돌린다(`CLAUDE.md` 검증 명령의 계기). 사진 비교와 위젯·관리 화면·위젯 테스트 페이지의 e2e는 이 티켓이 앱을 고치지 않아 계기에 들지 않는다. 계기에 드는 파일을 고치게 되면 그 명령을 친다
