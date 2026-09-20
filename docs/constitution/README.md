# Agent OS 헌법

세 파일로 나뉜다. 로드 시점이 다르기 때문이다.

- [principles.md](principles.md): 원칙 다섯과 거버넌스. `CLAUDE.md`가 임포트해 항상 실린다.
- [tech.md](tech.md): 언어, 도구, 의존성. 의존성을 더하거나 스택을 바꿀 때 읽는다.
- [operations.md](operations.md): 검증, LLM 테스트, 가드레일, 브랜치, 리뷰 파이프라인, 이슈, 환경 규약. 커밋·병합·리뷰·트래커를 만질 때 읽는다.

디렉터리별 규칙(포트, 어댑터, sdk와 플러그인, 테스트)은 헌법이 아니라 `.claude/rules/*.md`에 있고 해당 파일을 열 때만 실린다. 현재 트리는 `README.md`, 미래 배치와 첫 슬라이스의 범위는 `.scratch/plan.md`에 있다.

**Version**: 2.3.1 | **Ratified**: 2026-09-19 | **Last Amended**: 2026-09-21 (ADR 0001~0006). 2.1.0은 원격·CI·PR을 첫날부터로 바꾼 것, 2.2.0은 리뷰 파이프라인 절 추가, 2.2.1은 CodeRabbit PR 리뷰를 빼고 CLI만 남긴 것, 2.3.0은 거버넌스에 "ADR은 결정 단위" 문장을 더하고(절 추가라 minor) 2.1.0~2.2.1을 ADR 0005·0006으로 소급한 것, 2.3.1은 공개 전환 뒤 CodeRabbit PR 리뷰를 다시 켠 것

2.0.0은 파일 분할이다. 원칙 I~V의 문구는 1.6.0과 같다. 1.x 이력은 git과 `docs/journal/`에 있다.
