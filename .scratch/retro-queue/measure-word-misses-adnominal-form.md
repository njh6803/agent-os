# measure-word-misses-adnominal-form: 일지가 손으로 `wc -c`를 쳐서 본 값을 "잰 값"으로 적었는데, `hook_measure_word`의 측정 낱말에 관형형 "잰"이 없어 알리지 않는다

**상태:** 열림
**어디로:** `tools/hook_measure_word.py`의 `MEASURE_WORDS`: 관형형 `잰`을 더한다. 거짓 양성(`잰걸음`)은 독스트링의 못 보는 것에 적고 시험으로 고정하며, `tools/hook_payloads.toml`에 발동하는 입력과 발동하지 말아야 할 입력을 하나씩 더한다
**승인:** 자체 승인 2026-11-13, 1회차, 일지 2026-11-13-2106-ds-bundle-escape-replacement-char.md. ADR 불필요

`MEASURE_WORDS`가 `쟀다`·`재니`·`실측` 셋뿐인 것은 커밋 `fa5505823`의 `tools/hook_measure_word.py` 98행을 읽어 봤다. 그 줄은 셀프 리뷰 명세 축이 잡았다.
