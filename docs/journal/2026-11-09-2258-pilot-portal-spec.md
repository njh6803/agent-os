# pilot-portal 명세

브랜치 `docs/pilot-portal-spec`, 워크트리 `.claude/worktrees/pilot-portal-spec`. 앞 단계는 화면 디자인(일지 2026-11-09-1839)이고 이 세션은 to-spec 스킬로 명세를 쓴다.

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: pilot-portal
>
> 다음 작업: 기능 pilot-portal(위젯을 담는 질문 페이지가 로그인 없이 온 사람에게 사이트 토큰을 내, 포털이 없는 공개 데모와 배포 환경을 돕는다). 다음 단계: 명세. 이번 요청 범위: 명세까지(병합은 범위 밖). 어디서: 새 세션. 주 체크아웃 미갱신이면 Skill 도구로 tidy-checkouts를 먼저 돌고(사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 들어가 거기서 브랜치를 바꾼다. 시작 프롬프트: /to-spec pilot-portal. 브랜치: docs/pilot-portal-spec. 모델: Fable 5.1 / xhigh. 읽을 것: docs/journal/2026-11-09-1839-pilot-portal-screens.md의 "다음". 이어받을 상태: 명세를 쓰기 전에 사람에게 물을 네 가지(밀도, 라이트 기본 화면의 대화, 입력창 이름 "질문"과 용어집, ADR 0050의 "같은 알림이 붙은 비활성 로그인 단추")가 .scratch/pilot-portal/design/README.md "그림이 시작 프롬프트나 근거 문서와 다른 자리"에 있다. 위젯 문구 변경(422 오류 글 포함)과 TextField 이름표 숨기기는 명세가 정한다. 질문 페이지와 위젯(/widget/element.js)이 같은 출처여야 한다는 배치 전제는 release-image 설계 인터뷰가 정한다(PR 500 코멘트에만 있다). ADR 0050 첫 단락의 일반 명사 "포털"은 명세 때 ADR 문장을 손볼 때 함께 본다. 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다.

## 사람에게 물은 것

명세를 쓰기 전에 디자인 README가 넘긴 네 가지를 한 화면으로 물었다. 넷 모두 권한 쪽을 골랐다.

- **밀도.** 질문: 넓은 창(폭 768px 이상)에서 위젯 바깥 부품(사이트 고르는 상자, 고지 덮개의 글과 "확인하고 질문하기" 단추)의 크기를 어느 밀도로 둘까. 고른 답: "페이지 전체를 보통으로". 설명: 페이지 뿌리에 보통 표시(`data-density="regular"`)를 달아 넓은 창에서도 사이트 상자·덮개 단추·고지 글이 위젯 안 글자와 같은 크기로 보인다. 그림의 넓은 창 화면은 그 크기로 다시 봐야 한다. 고르지 않은 것: "그림대로 바깥은 촘촘"(관리 화면과 같은 규칙. 넓은 창에서 사이트 상자와 덮개 단추는 32px, 위젯 안만 40px).
- **라이트 기본 화면.** 질문: 밝은 기본 화면의 위젯 안을 어떤 모습으로 둘까. 시작 프롬프트는 "질문과 답이 한 번 오간 모습"이라 했는데 그림은 소개 글이 든 첫 화면이다. 고른 답: "그림 그대로 둔다". 설명: 확인 직후는 질문 전이라 소개가 든 첫 화면이 실제와 맞고, 오간 모습은 다크 화면과 고지 펼침 화면이 이미 보여 준다. 그림을 고치는 일이 없다. 고르지 않은 것: "오간 모습으로 다시 그린다"(ui-design 스킬로 라이트 기본 화면 두 장을 다시 그림).
- **입력창 이름.** 질문: 위젯 입력창을 화면 읽기 프로그램이 읽어 주는 이름을 무엇으로 둘까. 그림은 "질문"이고 용어집은 "요청(Request)"을 쓰며 "질문"을 피할 말로 둔다. 고른 답: "화면은 '질문', 개념어는 '요청'". 설명: 사람에게 보이는 글(입력창 이름, 단추, 고지)은 "질문"을 쓰고, 코드·문서·API의 개념어는 "요청"을 유지한다. 용어집의 요청 항목에 "사람에게 보이는 글에서는 질문이라 부른다"는 단서를 단다. 고르지 않은 것: "화면도 '요청'으로 맞춘다".
- **둘 다 사이트의 로그인 단추 곁 글.** 질문: 익명 질문도 로그인도 되는 사이트에서 눌리지 않는 "로그인하고 질문하기" 단추 곁에 무엇을 둘까. 그림은 글 한 줄, ADR 0050은 로그인 전용 사이트의 알림 상자와 같은 알림 부품. 고른 답: "그림대로 글 한 줄". 설명: 단추 곁에 작은 글 한 줄("로그인은 아직 제공하지 않습니다. 지금은 로그인 없이 질문할 수 있습니다.")만 둔다. 화면 작업 때 사람이 고른 문구이고, 익명 질문이 되는 화면에 알림 상자가 하나 더 서지 않는다. ADR 0050의 그 문장을 그림에 맞게 고친다. 고르지 않은 것: "ADR대로 알림 상자".

이어서 to-spec 2단계의 이음매를 한 화면으로 확인했다. 고른 답: "e2e 주, Vitest 보조". 설명: 주 이음매는 Playwright e2e다. 질문 페이지 서버·위젯 Next·serve·중계를 실제 프로세스로 띄우고 브라우저가 페이지를 열어 고지 확인, 질문과 답, 사이트 바꾸기, 로그인 화면을 본다(위젯 e2e의 준비 코드를 나눠 쓴다). 보조 이음매는 Vitest가 서버의 요청 처리기와 순수 함수를 node에서 부르는 것이다(설정 읽기와 사이트 파일 대조, 토큰 서명, 쿠키·Origin 판정, 페이지 데이터, CSP 헤더). ADR 0050이 적은 두 목록과 같은 모양이다. 고르지 않은 것: "Playwright e2e 하나만", "Vitest 주, e2e는 연기 하나".

## 프로브

ADR 0050 결정 "띄우기"가 어림이라 적은 조합을 `.scratch/pilot-portal/probes/node_ts_workspace.py`로 쟀다(여섯 묶음 스무 회차. 회차마다의 값과 근거의 종류, 결과를 본 뒤 바꾼 기준은 그 `README.md`). 같은 날 네 번 돌렸다. 첫 실행은 16회차 가운데 15회차 측정(`next_config_legacy`가 임시 폴더를 작업 디렉터리로 두어 측정 아님), 둘째는 갈래 둘을 더해 18회차 모두 측정, 셋째는 명세를 쓰며 더한 페이지 스크립트 묶음 두 회차(첫 판은 갈래 표지를 `ERR_INVALID_TYPESCRIPT_SYNTAX`로 적어 측정 아님 하나, 원본 stdout의 `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`로 고친 뒤 둘 다 측정), 넷째는 스무 회차 전체를 백그라운드로 돌려 모두 측정이었다. 결론(쟀다): pnpm 링크는 실제 경로로 풀려 `node_modules` 밖의 `.ts`로 읽히고(`--preserve-symlinks`와 `node_modules` 안은 거부), 상대 import는 확장자가 필요하며, `@agent-os/ui` 루트 진입점은 `.tsx` 때문에 읽히지 않고 서브패스와 `themes.ts`는 읽힌다. tsc는 nodenext·bundler 둘 다 서고 변이를 잡는다. 토큰 CSS는 Tailwind CLI로 0.67초에 지어지고 그림의 변수 27개가 모두 선언되며 유틸리티 122개가 함께 든다. 글꼴은 woff2 386개 5,853,912바이트. 위젯의 `next.config.ts`는 기본 길과 네이티브 길 모두 워크스페이스 `.ts`와 smol-toml을 읽고 기본 길의 상대 import는 작업 디렉터리 기준이다. 페이지 스크립트는 `stripTypeScriptTypes`로 벗겨 돌고 `enum`은 거부된다. 원본은 세션 스크래치패드의 `node_ts_raw_full.json`(커밋하지 않는다).

## 명세

`.scratch/pilot-portal/spec.md`를 mcp-http 서식으로 썼다. 서두의 수는 넘겨받은 것 열여섯, 사용자가 고른 것 다섯, 명세가 정한 것 스물다섯, 이력 둘, 거부한 안 서른여섯이다(첫 판은 거부한 안을 스물셋으로 적어 본문의 수와 어긋났고 "명세가 정했다" 목록에 절 넷이 빠져 있어 쓰자마자 고쳤다). 명세가 정한 큰 것: 앱 `web/apps/portal`과 패키지 둘(`@agent-os/site-file`, `@agent-os/e2e-stack`)과 `@agent-os/ui` 서브패스 둘(`./themes`, `./fonts`); 페이지 스크립트는 `.ts`로 두고 시작 때 벗김, 토큰 CSS는 시작 때 Tailwind CLI로 지어 메모리에서, 글꼴은 패키지 경로에서 바로; 설정 TOML의 칸(`[portal]` 다섯, `[[sites]]` 열); 끝점 표(확인 `acknowledgement`, 토큰 `token`, 로그인 사이트 403, `Origin` 403, 미확인 401); 쿠키 이름 `portal_anon` 하나와 접두 없음; 키 명령 `make-key`; 페이지의 접근성 역할과 포커스(확인 뒤 위젯 호스트), 다크 모드 스위치; 위젯 문구 넷과 TextField의 이름표 숨김 prop; CI 잡 `e2e-portal`과 마커 `llm_portal`; 티켓 묶음 A~E. 인용한 경로·토큰 변수·패턴은 모두 grep으로 실제 있음을 확인했다(`PLUGIN_NAME_PATTERN`은 플러그인 이름 패턴이라 "에이전트 이름"에서 "플러그인 이름"으로 고쳤다).

## 함께 고친 문서

- ADR 0050: `## 이력`과 이력 둘("띄우기의 어림을 잰 값으로 바꾸고 토큰 CSS와 페이지 스크립트는 시작 때 짓는다", "둘 다 사이트의 비활성 로그인 단추 곁은 알림이 아니라 글 한 줄이다"), 결정 "띄우기"의 "재기 전에는 어림이다."와 결정 "페이지"의 "같은 알림이 붙은 비활성 로그인 단추를 둔다." 뒤에 포인터, 첫 단락의 "포털"→"사이트"와 Consequences의 "포털 호스트"→"질문 페이지의 호스트" 낱말 고침(첫 이력의 "낱말" 문단에 적었다). `tools/check_adr_pointers.py` 초록. **이력 둘과 낱말 고침은 초안이고 아직 사용자 승인을 받지 않았다.** 명세 서두의 "이력은 둘이다" 문단과 이력 본문은 승인받은 것으로 적혀 있다. 승인 전에는 거짓이다.
- `CONTEXT.md` 요청 항목: "사람에게 보이는 글(위젯과 질문 페이지의 입력창 이름, 단추, 고지)에서는 질문이라 부른다" 단서와 _Avoid_의 "질문" 조건(domain-modeling 스킬을 불렀다).
- `docs/constitution/tech.md` 웹 행: "명세 전의 프로브가 재서 … 이력에 적는다"를 잰 결과와 이력 포인터로.
- 기능 계획: release-image(이미지의 `node_modules`에 Tailwind CLI와 글꼴, 질문 페이지·위젯 번들·최종 사용자 경로의 한 출처 전제와 PR 500 코멘트), portal-login(403 셋과 둘 다 사이트의 단추를 로그인 흐름으로), public-demo(`notice`·`report_url`, 링크는 하나라 두 보고서를 함께 두는 페이지), portal-admin·widget-appearance(칸은 명세 "질문 페이지 설정"), pilot-portal(제목과 본문의 "포털"→"위젯을 붙일 사이트"). `uv run python tools/plan_table.py`로 `.scratch/plan.md` 재생성.

## 검증

`uv run ruff check . && uv run ruff format --check .` 초록. `tools/check_md_tables.py`와 `tools/check_line_separators.py`를 고친 문서 열둘에 초록. `tools/check_adr_pointers.py` 초록. `tools/run_checks.py`는 백그라운드로 띄웠다가 인계로 멈췄다. 셀프 리뷰(`/code-review`)는 시작하지 않았다.

## 인계

세션 컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 와 `hook_handoff`의 계기를 받았다. 이 세션의 제목은 `docs/pilot-portal-spec`이었고 `docs/pilot-portal-spec (인계함)`으로 바꾼다. 커밋하지 않았다. 새 세션이 이 일지를 이어 쓴다. 낸 지시문:

```
다음 작업: 기능 pilot-portal(위젯을 담는 질문 페이지가 로그인 없이 온 사람에게 사이트 토큰을 내, 위젯을 붙일 사이트가 없는 공개 데모와 배포 환경을 돕는다). 명세 초안과 ADR 0050 이력 초안이 작업 트리에 있고, 셀프 리뷰부터 커밋·PR까지 잇는다.
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec pilot-portal
브랜치: docs/pilot-portal-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-09-2258-pilot-portal-spec.md의 "프로브"부터 "인계"까지(이 세션이 한 것과 승인받지 않은 것)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지는 docs/journal/2026-11-09-2258-pilot-portal-spec.md. ADR 0050의 이력 둘과 낱말 고침(첫 단락과 Consequences의 "포털")은 초안이라 아직 사용자 승인을 받지 않았다. 명세 서두의 "이력은 둘이다" 문단과 이력 본문이 승인받은 것으로 적혀 있으니, 셀프 리뷰를 반영한 뒤 AskUserQuestion으로 승인을 받고 그 뒤에 커밋한다(작업 규약 5). 반영 뒤 서두의 수를 다시 셀 때 거부한 안은 "거부한 안:"의 수에서 서두의 하나를 뺀 것이다. tools/run_checks.py는 인계로 멈춰 돌지 않았다. 프로브의 원본 JSON은 이 세션의 스크래치패드에 있어 새 세션이 보지 못하지만 프로브 README가 값을 옮겨 적었다.
확인할 선행 조건: 없음
이번 요청 범위: 명세까지(병합은 범위 밖. 병합은 이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 Read로 열어 따른다)
```

제목을 바꿨고, 백그라운드의 `tools/run_checks.py`를 멈췄고, 워크트리 잠금을 풀었다. open-session을 부른다 2026-11-09T14:43:35Z

## 셀프 리뷰 (새 세션, 2026-11-10)

인계 지시문대로 새 세션이 이 워크트리에 들어와 `/code-review origin/main`을 돌렸다. 범위는 기준 `9d789569`(origin/main이자 HEAD), 수정 10, 커밋 0, 미추적 4(명세, 프로브 README와 스크립트, 이 일지)다. 외부 근거(RFC 6265 5.3·5.4, draft-ietf-httpbis-rfc6265bis-19의 Strict와 `__Host-`)는 원문 txt를 curl로 세션 스크래치패드에 받아 grep으로 글자 그대로 발췌해 두 브리프에 실었다(WebFetch 요약은 근거가 아니다, `docs/agents/issue-tracker.md`). 두 축 모두 파일은 고치지 않았다.

### 표준 축(sonnet·high) 보고

1. **Major. 명세 105줄 쿠키 순서.** "상위 도메인 쿠키가 심어져도 그 사이트 경로의 쿠키가 먼저 온다"는 닫힌 주장에 반례가 있다. RFC 6265 5.4 발췌대로 경로 길이가 같으면 생성이 이른 쿠키가 먼저 간다. 형제 도메인이 `Path=/portal/sites/<이름>`을 그대로 주고 먼저 심으면 그것이 첫 쿠키가 되어 "첫 것을 쓴다"가 심은 값을 고른다. ADR 0050 Consequences가 이미 받아들인 한계와 어긋난다. 경로가 더 짧은 쿠키에만 맞는 말로 줄여야 한다.
2. **Major. ADR 0050 결정 "페이지"의 "짧은 고지는 위젯 곁에 늘 보인다."** 명세 125줄은 "짧은 고지는 위젯이 보일 때만 보인다"(상태 묻는 동안, 덮개가 있는 동안, 로그인 사이트에서는 숨김)이고 디자인 README도 같다. 이력도 포인터도 없다. `.claude/rules/adr.md`는 명세가 정한 것이 ADR 본문을 거짓으로 만들어도 같다고 한다.
3. **Major. 명세 13줄 "사용자가 승인했다(… 일지의 '승인')".** 일지에 "승인" 절이 없고 일지 스스로 "승인 전에는 거짓"이라 적었다.
4. **Minor. ADR 이력 1과 명세 55줄이 오류 코드를 잘못 적었다.** 프로브를 다시 돌리니 `strip_root_index`는 `ERR_MODULE_NOT_FOUND`(`…/atoms/Button`)이고 `ERR_UNKNOWN_FILE_EXTENSION`은 `.tsx` 파일을 직접 가리킨 `strip_tsx_file`에서 난다. 결론(읽히지 않는다)은 같다.
5. **Minor. 명세 122줄 "`<`는 `<`로 이스케이프한다".** 바이트를 확인하니 같은 글자라 아무것도 정하지 않는다.
6. **Minor. 측정 규칙(to-spec 3단계)과 어림 넷.** `./themes` 서브패스, site-file 패키지에서 smol-toml이 풀리는 것, `@agent-os/ui/fonts.css` 자기 참조, Tailwind CLI를 서버가 자식으로 띄우는 것을 재지 않고 묶음 A에 미뤘다. 또 프로브는 Windows 10만 쟀는데(README에만 적혔다) 배포 이미지는 Linux이고 명세와 ADR 이력에는 그 단서가 없다.
7. **Minor. 근거 종류가 섞였다.** 53줄 "링크를 거쳐 pnpm 스토어로"는 절반이 `ls -la`로 손으로 본 것인데 "쟀다"로 적혔다. 53줄 `next_config_*`는 site-file 패키지 대신 `@agent-os/ui/contrast`로 잰 것인데 명세에 "대리"가 없다. 60줄 "nodenext를 고른 까닭"은 근거 종류가 없다. 61줄 ExperimentalWarning은 원본 JSON이 커밋되지 않았고 재현하니 한 줄이 아니라 두 줄이다. 5줄 "`web/node_modules`의 … next 16.3.6"은 위치가 틀렸다(`web/node_modules`에는 next가 없고, node와 pnpm은 node_modules 안에 있지 않다).
8. **Minor. ADR 포인터 1 자리.** "재기 전에는 어림이다." 바로 뒤에 달았는데 이력이 함께 바꾼 "걸림돌은 셋이다 … 같은 프로브가 본다."는 포인터 뒤에 있다. 묶음에 하나라는 규칙은 지켰다.
9. **Minor. "낱말" 본문 편집.** `adr.md`의 "본문의 다른 글자는 고치지 않는다"와 글자 그대로는 어긋난다. 선례가 없으니 ADR 승인 때 확인을 받는 편이 낫다.
10. **Minor. 받는 쪽이 없는 배치 요건.** "믿을 수 없는 하위 도메인이 없는 도메인"이 명세 (15)에만 있고 release-image·public-demo·deploy-package 계획과 Out of Scope에 없다.
11. **Minor. 용어.** 새 `_Avoid_`는 "질문"을 개념어로 피하라는데 명세가 e2e 설명에서 요청의 뜻으로 "질문 하나를 보내"(178줄), "첫 질문"(124줄)을 쓰고 용어집의 고지·고지 확인 항목도 "질문이"라 쓴다. "요청 처리기"와 "요청 로그"는 HTTP 요청이라 용어집 요청(실행의 입력)과 겹친다.
12. **Minor. 경로.** 명세가 `GET /portal`의 302를 더했는데 ADR은 프록시 전달 규칙을 `= /`와 `/portal/` 둘로 못박았다. 프록시로는 그 경로가 닿지 않는다.
13. **Minor. 구현 파일 경로.** to-spec의 "구현 파일의 경로와 코드 조각은 적지 않는다"에 비해 `tools/fonts.ts`, `token.ts`, `stack.ts`, `site.ts`, `element-site.ts`, `next.config.ts` 등이 많다.
14. **Nit.** README "같은 날 두 번 돌렸다"가 뒤의 셋째·넷째 실행과 어긋난다. README `--group` 목록에 `pagescript`가 빠졌다. 프로브는 27·122·386을 출력만 하고 단언하지 않는다. "0.67초"는 재실행에서 0.34초였다. 129줄 인용 "페이지 하나에서 클라이언트가 바꿔 끼운다"는 사용자 원답("…가 위젯을 바꿔 끼운다")과 다르다. "지킬 것"은 shadow root가 공개 표면이 아니라고 직접 말하지 않는다. RFC 6265bis의 draft 번호를 적지 않았다. CONTEXT 요청 정의의 괄호 예시에 안내와 오류 글이 없다.

주장 검증에서 맞은 것: 서두 수 넷(넘겨받은 것 16, 고른 것 5, 이력 2, "거부한 안:" 37에서 서두 1을 뺀 36. "스물다섯"은 쉼표 목록 25개), 프로브 재실행 20회차 모두 측정과 값 전부, 인용 원문(EMBED.md 문구와 `tokenProvider` 꼴, CSP, `start.ts` 루프백 문구, `PLUGIN_NAME_PATTERN`, 디자인 README "14파일 33줄"은 14파일 재현·줄 수 36), 코드를 읽었다는 주장 전부(`themes.ts`, `fonts.ts`, e2e 파일 이름과 `upstreamOf`, 사이트 파일 모델의 칸, `addopts`, `ui/package.json`, Next 서버 파일 글롭 넷, `REQUIRED_CLAIMS`에 `nbf` 없음, CI `verify.needs`), 잔존 "포털" 0, `plan_table.py --check` 0, 받는 기능 계획 다섯의 절 이름과 Blocked by(넷 직접, public-demo는 release-image를 거치는 간접), RFC 발췌 대조(5.3 이름·도메인·경로, 5.4 SHOULD, Strict, `__Host-`).

### 명세 축(상속) 보고

- (a) 누락·부분. **[Minor] `site-file` 패키지의 인터페이스 변경을 적지 않았다.** 지금 `SiteEntry`는 `place·origins·requestChars`만 들고 `siteFileInput`은 `{allowedOrigins, requestChars}`만 돌려주는데, 시작 검사가 쓸 발급자·열 에이전트·공개 키(kid, pem)·audience를 내게 넓히는 결정이 없다. **[Minor] 3단계 측정 규칙.** 어림 넷 가운데 셋은 실패해도 고칠 길이 하나라 결정이 바뀌지 않지만 넷째(Tailwind CLI를 자식으로 띄우기)는 실패하면 ADR이 거부한 `dist/theme.css`로 되돌아갈 수 있어 명세 자리에서 재야 한다. ADR 이력 "자식 프로세스로 돌려 … 0.67초다(쟀다)"는 띄우기까지 쟀다고 읽히는데 프로브는 CLI를 바로 돌렸다. **[Nit]** public-demo의 `**Blocked by:**`에 pilot-portal이 없고 release-image를 거치는 간접 고리를 명세가 적지 않았다. **[Nit] 용어 신호.** "덮개", "짧은 고지"/"고지 전문"을 세 문서가 같은 뜻으로 쓰는데 용어집 고지 항목이 두 꼴을 가르지 않는다. **[Nit]** 그림의 뼈대 `aria-label="고지 확인 여부를 묻는 중"`이 명세 125줄에 없다.
- (b) 요청하지 않은 범위. **[Nit]** 97줄 로그인 사이트의 세 끝점 403은 ADR이 토큰 끝점만 말한 것을 넓혔으나 비워 둘 수 없는 자리라 지금의 "명세가 정했다" 표시로 충분하다. **[Nit]** 71줄 "짧은 고지는 사이트가 바꾸지 못한다"는 어디에도 없는 새 결정이고 거부한 안에 까닭은 있다.
- (c) 어긋난 구현. **[Major]** 122줄 "`<`는 `<`로 이스케이프한다"는 뜻이 서지 않는다. 189줄로 보아 `<`를 뜻한 오타다. **[Minor]** 87줄 `GET /portal` 302와 147줄 중계의 `/portal`은 ADR 결정 "경로"의 프록시 규칙(`= /`와 `/portal/` 둘) 밖이라 운영에서는 프록시의 404다. **[Minor]** 193줄 사이트 하나의 둘째 인스턴스는 시작 검사 "`public_origin`이 허용 출처에 든다"에 걸려 픽스처 사이트 파일에 그 출처가 없으면 뜨지 않는데 적지 않았다. **[Minor]** ADR Consequences 머리 "**위젯은 바뀌지 않는다.**"를 명세가 위젯 문구·TextField·`next.config.ts`·시작 래퍼·e2e 준비를 바꾸며 220줄이 대 보지 않았다. **[한 줄]** 13줄 승인 문장은 승인 전인 지금 거짓이다. **[Nit]** 사용자 답 "그림의 넓은 창 화면은 그 크기로 다시 봐야 한다"에 대응하는 자리가 없다.
- 주장 검증에서 틀렸거나 확인하지 못한 것: `<` 오타, README "같은 날 두 번 돌렸다"(닫힌 수), ADR 이력 "자식 프로세스로 … (쟀다)", 76줄 "서버의 pydantic 모델과 같은 규칙"(모양 판정은 같지만 읽어 내는 값은 둘뿐), 215줄의 어림 넷. 맞은 것 44(ADR 0050 대 명세 7, 사용자 답 다섯, 수락 셋, 받는 기능 계획 다섯, EMBED.md 넷, RFC 네 문장, 잔존 "포털" 0 등).

범위 한 줄: base `9d789569`, 수정 10, 커밋 0, 미추적 4. 표준 축 14건(Major 3, Minor 10, Nit 묶음 1), 가장 심각한 것은 ADR 결정 "페이지"의 짧은 고지 문장이 명세와 모순인데 이력·포인터가 없는 것. 명세 축 13건(Major 1, Minor 6, Nit 5, 알려진 상태 1), 가장 심각한 것은 `<` 이스케이프 문장.

### 판정과 반영

근거를 먼저 봤다. ADR 0050 결정 "띄우기"의 포인터 뒤 문장, Consequences "한계가 하나 더 있다"의 형제 도메인 수용, 결정 "페이지"의 "짧은 고지는 위젯 곁에 늘 보인다." 원문, 일지 2026-11-09-1410 81줄의 사용자 원답, 프로브 `theme_css_build`의 표지 로직, `@agent-os/ui`의 exports, EMBED.md "지킬 것"의 공개 표면 목록, `site-file.ts`의 `SiteEntry`·`siteFileInput`, node가 찍는 `ExperimentalWarning`(`node -e`로 다시 봐 두 줄). 반영은 지적마다 아래와 같다.

- **고친 것.** 표준 1(쿠키 순서를 같은 경로의 생성 순서까지 적고 형제 도메인 한계를 ADR Consequences로 돌림). 표준 2(ADR 0050 이력 셋째 "짧은 고지는 위젯이 보일 때만 보인다"와 그 문장 뒤 포인터. 명세 서두 "이력은 셋"). 표준 3·명세 (c) 한 줄(승인 뒤 문장을 사실로 두고 이 일지에 "승인" 절). 표준 4(명세 55줄과 ADR 이력 1의 오류 코드를 `strip_root_index`는 `ERR_MODULE_NOT_FOUND`, `.tsx`는 `ERR_UNKNOWN_FILE_EXTENSION`으로). 표준 5·명세 (c) Major(`<`로). 표준 6·명세 (a) 둘째(프로브에 회차 넷을 더해 전체를 다시 돌렸다. 아래 "프로브 둘째 판". Windows만 쟀다는 단서를 명세와 ADR 이력에). 표준 7(근거 종류 다섯 자리를 가름). 표준 10(release-image 기능 계획 본문과 명세 Out of Scope에 배치 요건). 표준 11(개념어 자리의 "질문"을 "요청"으로, "요청 처리기"를 "HTTP 요청 처리기"로, "요청 로그"를 "접근 로그"로. 용어집 고지 항목은 사람에게 보이는 글의 서술이라 그대로). 표준 12·명세 (c) `/portal`(표의 행과 중계 규칙에서 빼고 거부한 안으로). 표준 14의 Nit 모두(README 실행 횟수와 `--group` 목록, 시간을 범위로, 129줄 인용을 원답으로, "지킬 것" 문장을 목록 기준으로, bis draft-19 명시, CONTEXT 괄호 예시에 안내·오류 글). 명세 (a) 첫째(`site-file`이 내는 모델의 칸을 "앱과 패키지"에 적고 시작 검사 문장을 맞춤). 명세 (a) Nit 셋(public-demo 간접 고리, 용어집 고지 항목에 전문과 짧은 줄 한 문장, 뼈대 `aria-label`). 명세 (c) 둘째 인스턴스의 출처(픽스처 사이트 파일에 함께 든다). 명세 (c) "위젯은 바뀌지 않는다"(Further Notes에 대 본 문장. 그 문단은 쿠키·토큰 흐름의 이야기라 포인터는 달지 않는다). 명세 (c) 넓은 창 그림 대 보기(묶음 C와 "모양"에).
- **남긴 것과 이유.** 표준 8(포인터 자리): 묶음에 하나라는 규칙대로이고 규칙이 묶음의 앞뒤를 정하지 않는다. 표준 9("낱말" 본문 편집): 승인 질문에 포함해 사용자가 판정한다. 표준 13(구현 파일 경로): 옮기는 기존 파일의 이름은 테스트 선례 경로처럼 티켓이 그 파일을 찾아야 해 두고, 새 파일의 경로는 적지 않았다. 표준 14의 "27·122·386을 단언하지 않는다": 그 수는 결론의 표지가 아니라 적어 두는 값이고, 표지(지시문 0, 그림의 변수 모두 선언, `@import` 양성 대조)는 단언한다. 명세 (b) 둘: 보고 스스로 지금 표시로 충분하다고 했다. 프로브 `_last_json`·`package_version`의 pyright 경고는 첫 판부터 있던 것이고 `.scratch`는 pyright 범위 밖이다.
- **다시 돌린 명령.** 아래 "검증 (새 세션)"에 적는다.

### 프로브 둘째 판 (2026-11-10)

셀프 리뷰 표준 6과 명세 (a) 둘째가 짚은 어림 넷 가운데, 틀리면 결정이 바뀌는 둘(Tailwind CLI를 node가 자식으로 띄워 메모리에 읽는 길, 글꼴 도우미가 옮겨 갈 패키지 안에서 `@agent-os/ui/fonts.css`를 자기 참조로 푸는 것)과 `nodenext`를 고른 까닭(확장자 없는 상대 import를 막는가)을 회차 넷으로 더했다. `tsc_nodenext_extensionless`(표지 `extensionless.ts(줄,칸): error TS2835`), `tsc_bundler_extensionless`(종료 0, 오류 없음, `--listFiles` 목록에 그 파일. 파일이 프로그램에 들었는데도 지난 것과 보지 않아 지난 것을 가르는 갈래), `theme_css_build_child`(자식 종료 0, 지운 뒤 파일 없음, 바로 돌린 것과 같은 바이트), `fonts_css_self_reference`(푼 경로가 `src/styles/fonts.css`, export 지도에 없는 서브패스는 `ERR_PACKAGE_PATH_NOT_EXPORTED`). 더하며 결함 하나를 봤다. tsc 묶음이 strip 묶음이 쓴 입구 파일에 기대 `--group tsc`만으로는 파일을 찾지 못했을 모양이라, 입구 둘을 `entry_subpath_file`·`entry_themes_file`로 빼 두 묶음이 함께 쓰게 했다(코드를 읽었다. 그 모양으로 돌린 적은 없다). 다섯째 실행은 여섯 묶음 스물네 회차 모두 측정, 측정 아님 0, 종료 코드 0이었다. 원본(`node_ts_raw_5.json`)과 로그는 이 세션의 스크래치패드에 있어 커밋하지 않았고 README가 값을 옮겨 적었다. 값: tsc 여섯 회차 0.8~1.0초, `nodenext`의 확장자 없는 import는 `TS2835`로 빨갛고 `bundler`는 지남. `theme_css_build` 0.36초 29,569바이트(앞 실행 0.31·0.67초), `theme_css_build_child` 자식 0.31초·node 전체 0.38초·같은 29,569바이트·지운 뒤 없음. `fonts_css_self_reference` 경로 `web/packages/ui/src/styles/fonts.css`와 `ERR_PACKAGE_PATH_NOT_EXPORTED`. 나머지 스무 회차의 판정은 앞 실행과 같았다. 남은 어림은 둘(`./themes` 서브패스 그 이름, `site-file`에서 `smol-toml` 풀기)이고 틀려도 결정이 바뀌지 않아 묶음 A의 첫 일로 두었다(명세 Further Notes). 편집 뒤 `tools/rewrap_comments.py`와 `ruff format`으로 감았고 ruff 초록. 반영 뒤 서두의 수를 다시 셌다. 거부한 안은 서른일곱(`grep -o "거부한 안:" | wc -l`이 38이고 서두의 하나를 뺐다), 명세가 정한 것 스물여섯은 절 제목의 괄호와 하나씩 대 봐 "앱과 패키지"의 괄호에 `site-file` 모델의 칸을 더하고 괄호가 한 항목을 더 잘게 적기도 한다는 단서를 서두에 붙였다. 이력은 셋이다.

### 검증 (새 세션)

`uv run python tools/check_adr_pointers.py` 초록. `tools/check_md_tables.py`와 `tools/check_line_separators.py`를 고친 문서 일곱(명세, 프로브 README, ADR 0050, `CONTEXT.md`, release-image 기능 계획, `.scratch/plan.md`, 이 일지)과 프로브 `.py`에 초록. `uv run ruff check .`와 `uv run ruff format --check .` 초록. `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 다시 만들고 `--check` 초록. `uv run python tools/run_checks.py`(백그라운드) 종료 0. check-ticket·lint-imports·zizmor·check-instructions·check-type-escapes·pyright·pyright-linux·run-hooks·pytest(348.7초)·web-verify(477.2초) 모두 Passed이고 Skipped 없음. ruff 둘은 러너에 없어 따로 쳤다(위). 커밋 직전의 손으로 치는 다섯은 그 커밋의 pre-commit 결과로 갈음한다. `uv run python tools/sibling_overlap.py`는 처음에 헌법 파일(`docs/constitution/tech.md` 웹 행)을 고치고 판을 올리지 않았다고 1로 끝나, `docs/constitution/README.md`의 판을 3.0.74에서 3.0.76으로 올렸다(형제 PR #503이 3.0.75를 먼저 가져갔고 그 사이 main에 병합됐다. 문구 수정이라 patch). 다시 돌려 0이고 번호 겹침 없음. origin/main이 `9d789569`에서 `3cb40736`(PR #503)으로 움직여 `git diff --name-only HEAD...origin/main`을 대 봤고, 이 브랜치가 이름으로 든 파일 가운데 겹치는 것은 헌법 둘(`docs/constitution/README.md`, `tech.md`)뿐이다. 커밋 뒤 origin/main을 합친다.

### 승인 (2026-11-10)

작업 규약 5대로 셀프 리뷰를 반영한 뒤 AskUserQuestion으로 ADR 0050의 이력 셋과 낱말 고침을 물었다. 첫 질문은 ADR 0050에 더한 이력 셋(2026-11-09 "띄우기의 어림을 잰 값으로 바꾸고 토큰 CSS와 페이지 스크립트는 시작 때 짓는다", 2026-11-09 "둘 다 사이트의 비활성 로그인 단추 곁은 알림이 아니라 글 한 줄이다", 2026-11-10 "짧은 고지는 위젯이 보일 때만 보인다")을 그대로 남겨도 되는가였고, 이력마다 화면에서 무엇이 바뀌는지(토큰 CSS와 페이지 스크립트를 서버가 켜질 때 만들어 메모리에서 냄, 누를 수 없는 로그인 단추 옆의 글 한 줄, 짧은 고지를 상태를 묻는 동안과 덮개 동안과 로그인 사이트에서 숨김)를 풀어 적었다.

> 사용자: 셋 다 남긴다(설명: "ADR 0050에 이력 셋과 표시 셋이 그대로 남고, 명세 서두의 '셋 다 사용자가 승인했다'가 사실이 됩니다. 이대로 커밋합니다.")

둘째 질문은 첫 단락의 "위젯을 붙일 포털이나"를 "위젯을 붙일 사이트나"로, Consequences "위젯은 바뀌지 않는다"의 "포털 호스트"를 "질문 페이지의 호스트"로 고친 것을 그대로 두는가였다(ADR 규칙은 포인터를 달 때 본문의 다른 글자를 고치지 않는 것이 기본이라 물었다).

> 사용자: 고친 대로 둔다(설명: "두 자리가 '사이트'와 '질문 페이지의 호스트'로 남고, 첫 이력의 '낱말' 문단이 그 고침을 기록합니다.")

그래서 명세 서두의 "셋 다 … 사용자가 승인했다"와 ADR 0050의 이력 셋·포인터 셋·낱말 고침 둘은 그대로 커밋한다.
