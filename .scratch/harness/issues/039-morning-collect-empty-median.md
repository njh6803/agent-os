# 039: 아침 수집이 자동 압축이나 사람이 열지 않은 세션이 없는 날에도 요약을 만든다

**What to build:** 2026-11-03 09:00의 종합 아침 보고가 2026-11-02를 수집하다 `tools/morning_collect.py`의 `_summary_piece`에서 `statistics.StatisticsError: no median for empty data`로 종료 1이 되어, 그날의 수집 JSON·시트·보고가 하나도 생기지 않았다. 그 함수는 요약 줄을 붙일 때 `(compact if before else "")`, `(first if headless else "")`로 빈 목록을 거르려 했지만, 붙일 글 `compact`·`first`를 그보다 앞에서 `statistics.median(before)`·`statistics.median(headless)`로 무조건 만들어 거르기가 소용없었다(트레이스백의 줄이 1152인 것을 읽었다). `before`는 자동 압축 가운데 직전 컨텍스트를 아는 것만 모으므로, 자동 압축이 없는 날에도, 있어도 컨텍스트 기록이 모두 없는 날에도 빈다(대기열 553이 10-31에 본 것은 뒤의 갈래다). 11-02는 앞의 갈래다. 고친 코드로 다시 모은 `<보고 폴더>/2026-11-02.data.json`의 `token:auto_compactions`가 0이었다(환산 비용 `metric:cost`는 $12.86, 손으로 봤다). 중앙값을 그 목록이 비지 않았을 때만 구하게 고치고, 두 목록이 빈 기간과 한쪽만 빈 기간으로 요약을 만드는 시험을 더한다.

**대기열:** 553

**Status:** done

## 수용 기준

- [x] 자동 압축이 없고 사람이 열지 않은 세션도 없는 기간으로 `summary_piece`(고치며 시험에서 부르려고 `_summary_piece`에서 공개했다)를 불러도 예외 없이 요약이 나오고, 그 줄에 중앙값 괄호가 붙지 않는다
- [x] 위 시험이 고치기 전 코드에서 빨갛다
- [x] 2026-11-02 수집이 종료 0으로 끝난다
- [x] 검증 명령이 모두 초록이다
