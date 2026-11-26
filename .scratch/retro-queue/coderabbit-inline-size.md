# coderabbit-inline-size: 만료된 0573을 잇는다. PR의 CodeRabbit 인라인 코멘트 열한 건을 읽는 데 약 25.7K자가 컨텍스트에 실렸고, 압축 뒤 일지로 옮기느라 같은 글을 한 번 더 읽었다

**상태:** 열림
**어디로:** `tools/pr_review_comments.py`: PR 번호를 받아 봇 인라인 코멘트마다 심각도, 파일:줄, 지적의 첫 단락들과 제안 diff만 내고 아이콘 태그와 AI 프롬프트 블록과 주석 표지는 뺀다(0573의 처방이다). 새 도구라 문턱은 다섯 번째 반복이고 그 전에는 회차를 센다. 반영하면 `.claude/skills/pr-feedback/SKILL.md`의 명령 표와 `next-session` `merge.md` 2의 반영 줄이 이 도구를 가리킨다
**승인:** 자체 승인 2026-11-27, 0573의 3회차(0573은 2회차로 2026-11-20에 만료했다), 일지 2026-11-27-0407-widget-runtime-values-spec.md. ADR 불필요

(widget-runtime-values 명세 PR 654의 봇 첫 회차다. `gh api repos/{owner}/{repo}/pulls/654/comments --paginate`의 결과가 커서 도구 결과 파일로 저장됐고, 그 파일을 Read로 읽은 한 번이 약 25,744자였다(큰 결과 알림이 적은 수다). 코멘트마다 지적의 본문은 서너 문단인데 아이콘의 `<picture>` 태그, 같은 지적을 다시 적은 "Prompt to fix issue" 블록, 주석 표지가 함께 왔다. 판단에는 심각도, 파일:줄, 지적의 본문이면 충분했다.)
