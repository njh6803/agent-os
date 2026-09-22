# 2026-09-22 · 인터럽트 06: 프로세스보다 오래 산다

인터럽트 슬라이스의 마지막 티켓. `/implement`로 새 세션에서 시작했고 브랜치는
`feature/06-prove-it-outlives-the-process`. 이 티켓은 기능을 더하지 않는다. `src/`가 한 줄도
바뀌지 않았고 산출물은 테스트 하나다. 01~05가 만든 것이 **실제로 존재하는지**를 실물로 재고
슬라이스를 닫는다.

> 사용자: "다음 작업: .scratch/interrupts/issues/06-prove-it-outlives-the-process.md. 실제 CLI
> 프로세스가 승인 대상에서 멈추고 끝난 뒤 다른 프로세스가 같은 실행을 재개해 끝까지 간다 —
> 일시정지가 프로세스보다 오래 사는 것을 실물로 재고 슬라이스를 닫는다 … 이번 요청 범위: PR과
> 병합까지"

## 한 것

- **`llm` 마커 e2e 하나.** `tests/test_main.py`의 마지막 테스트다. 임시 디렉터리에 plugins를
  차리고 실제 CLI 프로세스를 **둘** 띄운다. 첫째는 승인 대상 앞에서 종료 코드 3으로 끝나고,
  둘째는 첫 프로세스의 표준 출력이 안내한 명령 그대로 재개해 0으로 끝난다. `subprocess.run`이
  종료를 기다리므로 둘째가 뜰 때 첫째는 이미 죽어 있다 — 그것이 이 테스트가 증명하는 전부다.
- **`gatedcalc` 픽스처.** 도구를 고르는 것이 게이트도 에이전트도 아니라 실제 모델인 유일한
  픽스처다. `calc`와 달리 `fixture` stdio 서버(`tests/adapters/mcp_fixture_server.py`)를 쓰고
  `add`가 승인 대상이다. Node도 네트워크 도구도 필요 없다.
- **`_cli(argv, cwd)`.** 실제 CLI 프로세스를 띄우는 자리가 둘이 되어 한 곳으로 모았다.
  `PYTHONUTF8` 강제(CLAUDE.md 환경 함정)가 한 군데에만 있게 된다.
- **`_gated_manifest(name)`.** 같은 꼬리의 매니페스트가 셋이 되어 셀프 리뷰가 뽑아냈다.

## 반증으로 이빨을 쟀다

이 티켓에는 red가 없었다. 재개는 05까지 다 만들어져 있으므로 테스트를 쓰자마자 초록이었다.
초록으로 시작하는 테스트는 "무엇을 재는지"를 스스로 증명하지 않으므로, 손으로 프로브를 돌려
**깨뜨려 봤다**. 같은 `run_id`를 다른 트레이스 디렉터리로 재개하면 종료 코드 1, `그런 실행이
없다`. 재개가 프로세스 안의 잔여 상태가 아니라 디스크의 트레이스에서만 온다는 뜻이고, 그래서
초록이 공짜가 아니다.

트레이스 한 파일의 실물은 이렇게 남았다.

```
run_started
llm_called      prompt="계산 요청이다. 반드시 add 도구로 …"
run_paused      tool=add                     ← 여기서 프로세스 1이 죽는다
approval_granted approver=User               ← 프로세스 2가 시작한다
run_resumed
tool_called     tool=add ok=True
llm_called      prompt=""
run_finished
```

ADR 0009가 예측한 모양 그대로다. `llm_called`가 둘인데 `prompt`가 찬 것은 첫째뿐이다 — 재생된
첫 턴은 **다시 쓰이지 않았고**, 빈 프롬프트의 둘째는 재개 뒤 루프의 둘째 턴이다. 첫 프로세스에
`tool_called`가 없는 것도 같은 결이다. 게이트는 도구 앞에서 멈췄고 `add`는 승인 뒤 다른
프로세스에서 한 번만 불렸다.

## 셀프 리뷰

두 축이 Major 2(양쪽 다 "일지 없음"과 "체크박스"), Minor 3, 스멜 2를 냈다. 앞의 둘은 이 문서와
티켓이 지금 닫는다. 고친 것 넷.

- **진단이 죽어 있었다.** Spec 축의 가장 좋은 지적이다. `_guidance(paused.stdout)`가 단언보다
  먼저 돌아서, 첫 프로세스가 멈추지 못하면 `next(...)`의 StopIteration이 터지고 의도한
  `assert ..., paused.stderr`는 영영 돌지 않는다. 가장 흔한 실패 모드에서 원인을 못 본다.
  일시정지 단언을 안내 줄을 읽기 **전**으로 올렸다.
- **`run_started`가 한 번인지 보지 않았다.** `types[0]`만 봐서 둘째 프로세스가 `run_started`를
  다시 내도 통과했다. "재개는 새 실행이 아니라 같은 실행"이 이 e2e가 잴 수 있는 주장인데 빠져
  있었다. `count() == 1`.
- 매니페스트 꼬리의 세 번째 사본(Duplicated Code)을 `_gated_manifest`로, 사실이 아닌 주석
  ("calc와 같고 …" — 실제로는 프롬프트도 mcp 서버도 다르다)을 프롬프트가 강제형인 **이유**로
  바꿨다.

남긴 것: `.scratch/plan.md`의 `PR #29~#37`은 아직 없는 번호다(두 축이 다 짚었다). 다음 PR 번호가
#37인 것을 `gh`로 확인하고 적었고, 어긋나면 병합 전에 고친다. 모델이 `add`를 두 번 부르면 재개가
다시 멈춰 빨개지는 흔들림은 `llm` e2e 고유의 위험이라 막지 않는다 — 그때 보이라고 stderr를
단언 메시지에 실었다.

## 검사

`pytest` 221 passed·3 deselected(기본 스위트는 네트워크 없이 돌고 이 테스트는 `-m "not llm"`이
자동으로 뺀다), `uv run --env-file .env pytest -m llm` 3 passed, `ruff` check·format 통과,
`pyright` 52파일 0 errors(`filesAnalyzed`로 먼저 확인), `lint-imports` 3 kept.

## 슬라이스가 닫혔다

`interrupts` 티켓 여섯이 전부 done이고 `.scratch/plan.md`의 Status를 done으로 바꿨다. 남은 것은
`requires_approval` 한 줄로 걸리는 승인 게이트, 트레이스 재생으로 이어 가는 `resume()`,
`agent-os resume <id> --approve | --deny --reason`, 그리고 형식 2 트레이스 하나에 담기는 실행의
전모다. 포트는 다섯 그대로이고 체크포인터라는 부품은 생기지 않았다.

## 회고

05가 남긴 후보를 이 세션이 그대로 따랐다. **일지를 code-review 뒤에 썼다.** 리뷰 결과가 일지에
들어갔고 retro 훅이 이중으로 돌지 않았다. `implement` 스킬에 한 줄로 못 박는 것은 여전히 승인
대기다.

## 다음

- 프론티어는 둘이다. `http-channel`과 `admin-api`. `resume()`이 core 함수라 HTTP 채널이 같은
  것을 부르고, `TraceStore.read`는 `admin-api`의 `/traces`가 재사용한다. 둘 다 이 슬라이스가
  깔아 둔 자리 위에 선다.
- 후속 후보 그대로: `sdk`의 `ApprovalDenied.reason`에 `min_length=1`(계약 변경이라 ADR 0009
  이력과 승인이 필요하다), `tests/core/test_run.py`의 `_run`이 `plugins`를 주면 첫 인자를 버리는
  것, `_reject_masked_args`가 `Exception`인 것.
- 열린 문제 셋(마스킹 범위)과 `ctx.now()`의 두 번째 재개 문제는 ADR 0009 이력에 그대로 있다.
  승인이 두 번 끼는 실행이 실제로 생길 때 연다.
- 워크트리 `.claude/worktrees/`의 옛 둘은 여전히 사람이 지운다.
