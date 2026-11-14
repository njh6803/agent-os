# raw-replacement-char-in-tracked-text: U+FFFD의 이스케이프 글을 적으려던 자리에 날것 U+FFFD가 들어 저장소 파일에 남았는데, 날것 문자를 잡는 검사가 U+FFFD를 보지 않는다

**상태:** 열림
**어디로:** `tools/check_line_separators.py`와 `tools/hook_line_separators.py`: 추적하는 텍스트 파일에 든 날것 U+FFFD도 잡는다. 0022·0052·0160이 날것으로 저장된 줄 구분 문자와 `.py`의 공백·서식 문자를 잡게 한 것과 같은 종류의 틈이다. 거짓 양성(그 글자를 일부러 다루는 시험 자료)은 독스트링의 못 보는 것에 적고 시험으로 고정한다
**승인:** 자체 승인 2026-11-13, 2회차, 일지 2026-11-13-2106-ds-bundle-escape-replacement-char.md. ADR 불필요

사건: 앞 세션이 대기열 항목 `ds-upload-replacement-char-rejected`의 어디로 줄에 이스케이프 글 대신 날것 U+FFFD를 적었다(1회차). 이 세션은 도구 인자에 적은 6글자 이스케이프 글이 도구에서 풀려, 시험·주석·독스트링·티켓·일지 다섯 파일에 날것 U+FFFD가 들었다(2회차). 둘 다 셀프 리뷰가 잡았고, 그사이 어느 검사도 알리지 않았다.
