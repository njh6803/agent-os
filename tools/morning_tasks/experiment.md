# 실험 보고 (매주 월요일 10:15)

먼저 `common.md`를 따른다. 이 보고는 "티켓을 어떻게 쪼갤까"에 답한다.

## 메모

`<보고 폴더>/<어제>.experiment.notes.json`.

```json
{
 "heads": {"experiment": {"conclusion": "수락 조건이 여섯을 넘는 티켓에서 인계가 나기 시작했다.", "decide": []}},
 "blocks": {
  "experiment.tickets": {"conclusion": "수락 조건이 여섯을 넘는 티켓에서 인계가 났다", "so_what": "여섯 이하로 쪼개면 한 세션에 들 것이다 *(가설)*", "todo": "없음"}
 },
 "prs": {}
}
```

- **블록.** 이 보고로 가는 표와 볼 것은 이렇다.
  - `experiment.ticket_sizes` 크기 무리별 중앙값: 인계 중앙값이 커지는 무리.
  - `experiment.tickets` 티켓마다: 인계가 나기 시작하는 수락 조건 수·글자 수.
  표본이 작으면 단정하지 않고 `*(가설)*`을 붙인다.
- **이름.** 이 보고의 표에 나온 PR마다 이름과 내용을 쓴다.

그리기는 `common.md`의 "그리기와 보고"를 `--report experiment`로 따른다.
