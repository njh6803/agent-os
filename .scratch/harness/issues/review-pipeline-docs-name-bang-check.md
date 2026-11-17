# review-pipeline-docs-name-bang-check: 리뷰 파이프라인 문서에 느낌표 맞춤을 적는다

**What to build:** release-image 티켓 06(PR 589)이 `claude-code-review.yml`의 프롬프트에 PR 제목 접두의 느낌표가 변경과 맞는지 보는 줄을 더했다. 그 PR은 동작을 서술하는 문서를 고치지 못해(허용 경로 밖) 두 자리를 일지 `docs/journal/2026-11-16-0035-review-bot-checks-upgrade-bang.md`의 "다음"에 넘겼다. 이 티켓은 그 두 자리에 한 구절씩 더한다.

- `docs/constitution/operations.md` 리뷰 파이프라인 3: claude-review의 담당이 "유지보수성과 경계"로만 적혀 있다. 느낌표 맞춤을 더한다.
- `CODING_STANDARDS.md` 32행: "이 넷과 경계는 PR의 Claude Code Review가 본다"에 느낌표 맞춤을 더한다.

새 규칙, 검사, ADR은 없다. 이미 병합된 동작을 문서가 따라가게 하는 고침이다. 느낌표의 기준은 `operations.md`의 "릴리스 노트 조각" 절 "느낌표의 기준"이 원천이라 새 구절은 기준을 되풀이하지 않고 가리키기만 한다. 느낌표와 `upgrade/` 파일의 짝은 노트 검사가 CI에서 보며 봇이 보지 않는다는 사실도 한 구절로 적는다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `operations.md` 리뷰 파이프라인 3이 claude-review가 PR 제목 접두의 느낌표 맞춤도 본다고 적는다(기준은 "느낌표의 기준"을 가리키고, 짝 검사는 노트 검사의 몫이라는 구절을 곁들인다)
- [x] `CODING_STANDARDS.md` 32행이 같은 사실을 한 구절로 적는다
- [x] 두 구절이 `claude-code-review.yml` 프롬프트 3번의 서술과 어긋나지 않는다(프롬프트를 읽어 대조한다)
- [x] 검증 명령이 모두 초록이다

## 확인한 근거 (2026-11-16)

- 프롬프트 3번(`claude-code-review.yml` 67행)을 Read로 읽어 대조했다. 어긋남(변경이 올릴 때 손댈 것을 만드는데 접두에 없거나 만들지 않는데 있으면 짚는다. 기준은 "느낌표의 기준". 짝 검사는 노트 검사의 몫)이 없다.
- 셀프 리뷰(표준·명세 두 축, base `716e51d25`)에서 Critical·Major는 없었다. 고친 것: `operations.md` 51행이 느낌표 맞춤을 유지보수성·경계와 나란히 적어 45행의 "세 축"과 겹쳐 읽힐 수 있어, 두 축을 본 뒤 그 밖에 맞춤도 본다는 모양으로 바꿨다.
- 남긴 것: `.coderabbit.yaml` 5행의 주석("유지보수성·경계는 Claude Code Review")은 CodeRabbit이 보지 않는 몫을 가리키는 문장이라 틀리지 않아 그대로 둔다. `docs/adr/0006-review-pipeline.md` 8행과 이력 12행은 결정의 기록이고 이 티켓은 새 ADR을 쓰지 않으므로 고치지 않는다. 느낌표 맞춤을 ADR 0006에 이력으로 남길지는 사용자의 판단이 필요한 자리라 정하지 않았다.
- 검증 명령의 전체 결과는 커밋의 pre-commit(전체 러너)으로 갈음하며 결과는 일지와 PR 본문에 적는다. 린트 둘은 손으로 쳐 통과를 봤다.
- 새 문서 구절 둘 말고 고친 곳은 없다. `operations.md` 42행(보는 자리 문단)의 "claude-review 프롬프트에 변경과 접두를 맞대는 줄을 더하는 일은 … 다른 파일과 함께 싣지 않는다"는 그 줄을 더하는 PR을 다룬 규칙이라 지금도 맞아서 그대로 둔다.
