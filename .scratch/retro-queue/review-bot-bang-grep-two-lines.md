# review-bot-bang-grep-two-lines: 리뷰 봇 프롬프트(`.github/workflows/claude-code-review.yml` 67행)는 "느낌표의 기준"을 Grep으로 찾으면 줄 하나가 걸리고 그 줄은 길어 내용이 생략된다고 적었지만, 실제로는 `docs/constitution/operations.md`의 두 줄이 걸리고 이 PC의 Grep 도구는 그 문단의 줄을 내용까지 보였다

**상태:** 열림
**어디로:** `.github/workflows/claude-code-review.yml` 67행의 Grep 안내. 찾는 글자를 그 문단의 굵은 머리(`**느낌표의 기준.**`)로 좁히거나, 걸린 줄 가운데 그 문단을 고르라고 고쳐 쓴다. 이 파일은 다른 파일과 함께 싣지 않으므로(`docs/constitution/operations.md` 48행), 같은 67행의 "판을 올릴 때"를 바꾸는 판 계열 PR(대기열 `glossary-plain-names-left`)과 한 PR로 묶는다. 고쳐 쓴 안내는 그 PR이 병합된 뒤의 다음 PR에서 리뷰 봇이 그 문단을 읽고 "느낌표:" 줄을 내는지로 본다
**승인:** 자체 승인 2026-11-18, 1회차, 일지 2026-11-18-2145-rename-review-bot-note-section.md. ADR 불필요

걸리는 두 줄은 46행(그 문단)과 94행(그 문단을 가리키는 리뷰 파이프라인 3)이다. 이 세션의 Grep 도구로는 46행이 내용까지 나오고 94행만 `[Omitted long matching line]`으로 나왔다. 안내대로 생략된 줄을 고르면 가리키는 줄을 연다. CI의 Claude Code 판으로는 보지 않았다. PR 607의 두 회차에서 봇은 그래도 "느낌표: 맞음"을 냈으므로 손상은 없었다. 틀린 사실의 고침이라 사건 하나로 반영하는 종류이고(retro 4단계), 이 파일을 다시 바꾸는 PR을 따로 내야 해서 이 세션에서 반영하지 않았다.
