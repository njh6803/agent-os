# 토큰 사용 측정 프로브

ADR 0033(토큰 사용 방침)이 드는 수를 낸 프로브다. 하위 명령, 표지, 시간 창의 뜻, 못 보는 것은 `measure.py` 독스트링이
원천이다. 비용은 `../session_cost/costs.py`의 단가표(Claude Code의 셈)로 환산한 달러다. 같은 세션 기록이 폴더 둘에 겹쳐
있어 하위 명령마다 겹침을 걸렀다. 모델 호출은 응답 ID(`split`·`idle`·`simulate`. 한 응답의 여러 줄은 출력 토큰이 가장 큰
줄의 usage를 쓴다), 도구 호출은 그 ID(`plugins`), 압축은 압축 경계 기록의 uuid(`compactions`), 세션 단위의 셈은 세션
ID(`reads`·`rereads`)로 한 번만 센다. 설계 인터뷰(일지 2026-10-15-18) 도중에는 세션 스크래치패드의 스크립트로 근사
가중치(입력 1, 캐시 읽기 0.1, 캐시 쓰기 1.25, 출력 5)를 써서 겹침을 거르지 않고 셌다. 그래서 인터뷰 중에 말한 수는 이
폴더의 수와 다르다.

돌리는 법(저장소 루트에서, `compactions` 말고는 시간 인자가 꼭 있어야 한다):

```bash
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py split 24
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py idle 72
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py simulate 72
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py compactions
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py reads 48
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py plugins 336
PYTHONUTF8=1 uv run python .scratch/harness/probes/token_usage/measure.py rereads 72
```

## 결과 (2026-10-15, 이 PC의 `~/.claude/projects/`, 시각은 UTC)

PR 직전 버그 리뷰를 반영한 판으로 돌렸다. 모든 하위 명령이 표지를 지나 0으로 끝났다.

**split 24**(13:46): 모델 호출 2,721회, 환산 비용 $423.91(단가표 밖 0회).

| 갈래 | 비중 |
|---|--:|
| 메인 세션 | 87.0% |
| 서브에이전트 | 13.0% |
| 메인 세션 Opus 5.5 `xhigh` | 45.6% |
| 메인 세션 Fable 5.1 `high` | 16.6% |
| 서브에이전트 Opus 5.5 `xhigh` | 7.7% |
| 메인 세션 Opus 5.5 `medium` | 7.2% |
| 서브에이전트 Sonnet 5.5 `high` | 1.5% |
| 서브에이전트 Sonnet 5.5 `xhigh` | 0.9% |
| 서브에이전트 general-purpose(유형) | 11.5% |
| 서브에이전트 bug-perf-review(유형) | 1.1% |
| 이 저장소(워크트리 포함) | 100.0% |

**idle 72**(13:46): 메인 세션 모델 호출 13,076회, $1,711.70. 세션 컨텍스트가 5만 토큰을 넘는 호출 가운데 직전 호출과의
간격이 0~5분이면 11,465회 중 4회, 5~10분 339회 중 0회, 10~30분 54회 중 1회, 30~60분 7회 중 0회, 60분 이상이면 30회
중 30회가 세션 컨텍스트 절반 이상을 캐시에 다시 썼다. 캐시 쓰기는 5분 TTL 1,263만 토큰, 1시간 TTL 4,968만 토큰이었다.
60분 이상 쉰 뒤의 캐시 쓰기 비용은 $132.99(7.8%)이다. `wait_ci` 백그라운드 실행 66회 뒤 2분 넘게 쉬고 깨어난 호출
65회는 대기 중앙값 4.3분, 최대 419.3분이었고, 세션 컨텍스트 절반 이상을 다시 쓴 호출은 2회, 비용은 $15.79(0.92%)였다.
"깨어난 호출"은 실행 뒤 간격이 2분을 넘은 첫 호출이고, 그 직전 기록이 대기 완료 알림인지는 짝지어 보지 않았다.

**simulate 72**(13:46): 창 안에서 시작해 모델 호출이 둘 이상인 메인 세션 522개(창 앞에서 시작한 22개는 뺐다). 시작
컨텍스트는 중앙값 30,002 토큰, 사분위 17,497~47,876. 압축 뒤 세션 컨텍스트를 시작 컨텍스트에 요약 2만과 다시 읽기 3만을
더한 값으로 두고, 압축하지 않는 시뮬레이션의 합과 견준 어림이다.

| 자동 압축 지점 | 세션당 압축 | 읽은 세션 컨텍스트 절감률 |
|--:|--:|--:|
| 150,000 | 3.3 | 61% |
| 200,000 | 0.6 | 60% |
| 300,000 | 0.2 | 50% |
| 400,000 | 0.1 | 41% |
| 500,000 | 0.1 | 33% |

**compactions**(10:45): 압축 17건(포크한 세션에 복사된 같은 압축과 임시 폴더의 시험 세션을 뺐다). 수동 4건을 빼면
모두 자동이었고 압축 전 96.7만~100.2만 토큰에서 일어났다. 압축 뒤 첫 세션 컨텍스트는 7.7만~15만 토큰(뒤 호출이 없던
1건 제외), 요약은 9천~2.3만 자였다. 17건 가운데 12건 뒤에 세션은 117~341번 더 호출했다. 압축 뒤 30호출 안의 Read는
0~15회, 그중 압축 전에 읽은 파일을 다시 읽은 것은 0~8회였다. 압축 뒤 첫 사람 입력(도구 결과와 시스템 알림은 건너뛴다)의
출처는 사람 7건, 스킬 재주입 4건, 앱 알림 2건, 세션 간 메시지 1건, 없음 3건이었다. 사람 7건은 다음 단계 지시 5건
("넘어가", "커밋해줘", "CI 끝났어" 등)과 질문·새 요청 2건이었고, 압축 전의 맥락을 다시 설명한 글은 없었다(입력 글을
읽은 판단이다). 압축이 작업 품질에 준 영향은 재지 않았다.

**reads 48**(13:47): 메인 세션 167개, 모델 호출 4,427회. 무게 비중은 Bash 결과 17.1%, Read 결과 13.7%, 스킬 목록
첨부 12.4%, 사람 입력 6.0%, Edit 입력 5.6%, 지연 도구 목록 첨부 5.0%, 중첩 메모리 첨부 4.1%, Write 입력 3.9%였다.
무게가 큰 단일 항목은 `tools/canary.py` 읽기(1.20%), `uv run python tools/sibling_overlap.py`(0.78%),
`git -c core.longpaths=true worktree list`(0.64%) 순이었다.

**plugins 336**(13:47): 이 저장소 기록 2,475개. 스킬 호출 1,556회 가운데 플러그인 스킬은 `anthropic-skills` 4회뿐이었다.
MCP는 `plugin_github_github`이 27회였고 Playwright 두 벌과 `sequential-thinking`은 0회였다. 창 안에서 가장 큰 첫 스킬
목록(Claude Code 2.1.281)은 29,218자였고, `example-skills` 3,804자, `slack` 3,208자, `document-skills` 3,051자,
`cowork-plugin-management` 725자, `skill-creator` 351자, `claude-hud` 203자, `code-review` 54자를 차지했다.

**rereads 72**(13:47): 메인 세션 585개(모든 프로젝트), Read 2,502회 1,553만 자. 작업 트리를 바꾸는 git 명령 345회 뒤의
읽기는 빼고 센 다시 읽기 후보는 62회 51.6만 자로 Read 글자의 3.3%였다. 그 가운데 24.5만 자(47%)가 주 체크아웃의
`tools/tidy_checkouts.py` 하나였다. 다시 읽기 후보는 낭비라는 판정이 아니다. 긴 세션 컨텍스트에서 앞의 내용을 정확히
짚으려고 다시 읽은 것도 든다.
