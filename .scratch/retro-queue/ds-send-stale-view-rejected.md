# ds-send-stale-view-rejected: 0529의 4회차. 디자인 시스템 올리기의 보내기가 "You haven't viewed the latest version of this artifact"로 두 번 거부되었고, `SKILL.md` "보내기"대로 확인부터 다시 해도 같은 거부가 났다. `read`에 `url`만 준 페이지 읽기 뒤에 받아들여졌다

**상태:** 열림
**어디로:** `.claude/skills/sync-design-system/SKILL.md`의 "보내기"와 `import.md` 3(0529의 어디로를 잇는다): 보내기 전에 그 대화에서 페이지 읽기(`read`에 `url`만)를 한 번 하고, 그 거부 문구는 확인부터 다시 하는 거부와 가른다. 확인이 깨끗한데도 그 문구로 거부되면 페이지를 읽고 확인을 한 번 더 한 뒤 보낸다. 새 세션에서 그 길로 거부가 나지 않는지 본다
**승인:** 자체 승인 2026-11-13, 4회차(0529의 4회차. 0529는 3회차로 2026-11-12에 만료됐다), 일지 2026-11-13-2106-ds-bundle-escape-replacement-char.md. ADR 불필요. 스킬의 틀린 사실(그 거부를 사람이 바꾼 파일을 보낸 때로만 적는다)을 고치는 고침이다

이번에는 아티팩트 종류의 페이지 파일(`artifact-type/app.css`, `artifact-type/app.js`)이 판을 올린 뒤였고, `paths`를 준 읽기를 여러 번 했는데도 거부되었다. 원인을 `paths` 읽기로 보는 것은 0529와 같은 어림이다.
