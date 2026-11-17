# probe-parallel-launch-outside-round: 회차를 한꺼번에 띄우는 파이썬 프로브가 띄우기를 `Rounds.round` 밖에서 해, 한 회차의 세션이 뜨지 못하면 함께 띄운 다른 회차의 원본까지 잃을 수 있었다

**상태:** 열림
**어디로:** `tools/probe_kit.py`나 `.claude/rules/probes.md` 첫 항목: 회차를 한꺼번에 띄우는 프로브가 띄우기의 예외를 회차마다 따로 받게 하는 길을 둔다(작업을 넘기면 회차마다 결과나 예외를 돌려주는 도우미, 또는 "띄우는 함수는 예외를 던지지 않고 까닭을 돌려준다"는 한 문장). 어느 쪽인지는 반영하는 chore가 정한다
**승인:** 자체 승인 2026-11-18, 0339의 9회차, 일지 2026-11-17-2031-plain-words-in-written-artifacts.md. ADR 불필요

`.scratch/harness/probes/plain_words_reach/`의 `loading.py`와 `scope.py`는 `Rounds`를 쓰지만, 회차의 `claude -p` 세션은 `ThreadPoolExecutor`의 `pool.map`으로 한꺼번에 띄우고 그 결과를 다 모은 뒤에야 원본을 저장하고 `rounds.round`로 들어갔다. 띄우는 함수 `run`은 제한 시간 초과만 받았다. 그래서 한 회차가 프로세스를 띄우지 못해 `OSError`가 나면 `list(pool.map(...))`이 그 예외로 끝나, 이미 끝난 다른 회차의 원본도 저장되지 않는다. 0339가 `Rounds.round`에 둔 "예외로 끝난 회차는 측정 아님으로 세고 앞뒤 회차를 잃지 않는다"는 길이, 띄우기가 `round` 밖에 있으면 닿지 않는 꼴이다. 셀프 리뷰 두 축과 PR 직전 CodeRabbit CLI를 지났고 PR의 CodeRabbit 봇이 Minor로 잡았다(2026-11-18, PR 603). 두 `run`이 `OSError`를 받아 까닭 한 줄을 돌려주게 고쳤고, 고친 판과 고치기 전 판에 없는 실행 파일 이름을 넣어 앞의 것은 까닭 한 줄을 돌려주고 뒤의 것은 `FileNotFoundError`로 끝나는 것을 손으로 봤다(세션 스크래치의 스크립트). 실제로 원본을 잃은 실행은 없었다. 같은 꼴이 다른 프로브에 더 있는지는 세지 않았다.
