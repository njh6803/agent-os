# 030: 설계 인터뷰와 명세 칸을 Fable 5.1 / xhigh로 바꾼다

**What to build:** 사용자가 "설계 인터뷰와, 명세 작성에 사용할 모델을 Fable5.1 xhigh으로 바꿔죠."라고 정했다. `next-session` 결정표의 설계 인터뷰 줄(`/grill-with-docs`)과 명세 줄(`/to-spec`)의 "모델" 칸을 `Opus 5.5 / xhigh`에서 `Fable 5.1 / xhigh`로 바꾼다. 절차는 `docs/model-selection.md` 4절 순서의 3·4·7단계다. 시험 세션에서 사용 크레딧 동의가 첫 턴을 멈추면 칸을 바꾸지 않고 사용자에게 보고한다(ADR 0029 이력 2026-10-13). 측정 없이 계열을 바꾸므로 ADR 0029에 이력을 쌓아 사용자 승인을 받는다. 셀프 리뷰 뒤 사용자가 "이어받아도 Fable 로"를 골라, 결정표의 끊는 줄과 "같은 주제가 남았다" 줄, `handoff.md`의 인계 줄도 설계·명세면 `Fable 5.1 / xhigh`를 따르게 한다(PR 반영·병합만 남은 때는 `Sonnet 5.5 / high` 그대로).

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `claude-fable-5-1`의 단가가 `costs.py`와 `tools/token_report.py`의 `PRICES`에 있다
- [x] `Fable 5.1 / xhigh` 모델 줄로 연 시험 세션의 `get_session`이 모델과 레벨을 그대로 보였고, 크레딧 동의가 첫 턴을 멈추지 않았다
- [x] 결정표의 두 칸이 `Fable 5.1 / xhigh`이고 `tests/tools/test_open_session.py`의 결정표 테스트가 초록이다
- [x] 끊는 줄, "같은 주제가 남았다" 줄, `handoff.md` 인계 줄이 설계·명세면 `Fable 5.1 / xhigh`다
- [x] ADR 0029 이력이 사용자의 승인을 받았다
- [x] 바꾼 스킬을 새 세션에서 불러 확인했다
- [x] 검증 명령이 모두 초록이다
