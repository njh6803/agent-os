# precommit-cheap-checks-after-slow: **pre-commit이 몇 초짜리 변이 표 검사를 약 11분짜리 병렬 검사 뒤에 돌려, 낡은 표 원문 때문에 빨개질 커밋도 그 11분을 쓴 뒤에야 멈춘다**(answer-markdown 03의 첫 커밋 시도가 변이 표 넷의 원문이 낡아 `check-mutations`에서 멈췄다. 성공한 두 번째 시도에서 병렬 검사가 688.8초였고, 설정의 훅 순서가 병렬 검사 다음이 변이 표 검사라 첫 시도도 같은 순서로 돌았을 것으로 본다. 첫 시도의 걸린 시간은 재지 않았다)

**상태:** 열림
**어디로:** `.pre-commit-config.yaml`: `check-mutations`를 `parallel-checks` 앞(ruff 둘 뒤)으로 옮긴다. 파일을 고친 ruff 뒤에 색인을 본다는 조건은 그대로다. 같은 꼴의 값싼 검사(`check-md-tables`, `check-line-separators`)도 앞으로 옮겨도 되는지 함께 보고, 순서를 지키는 저장소 상태 시험을 둔다
**승인:** 자체 승인 2026-11-14, 1회차(고침), 일지 2026-11-14-0126-widget-renders-answers-as-markdown.md. ADR 불필요(검사는 그대로이고 순서만 바꾼다. 반영할 때 ADR 0005와 0035의 이력과 어긋나지 않는지 본다)
