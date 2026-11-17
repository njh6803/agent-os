# release-digest-compare-reads-registry-tag: 판 내기의 이미지 대조 단계가 올린 digest를 환경 변수가 아니라 레지스트리 해시 태그에서 읽는다

**What to build:** 판 내기 워크플로(`.github/workflows/release.yml`)의 첫 실제 실행(실행 43997051472, 병합 커밋 `a1a25bd25`, 2026-11-17)이 잡 `build`의 단계 `시험한 이미지와 올린 이미지 대조`에서 `An error occurred trying to start process '/usr/bin/bash' … Argument list too long`으로 죽었다(`gh run view 43997051472 --log-failed`로 읽었다). 이미지 올리기까지는 성공했고 잡 `publish`는 건너뛰었다. 그 단계는 bake 액션의 `metadata` 출력(이미지 넷의 digest와 출처 증명 `mode=max`에 든 GitHub 컨텍스트 전체)을 환경 변수 `METADATA`로 받았다. 실패 로그는 289,756바이트였고(`gh run view 43997051472 --log-failed | wc -c`), 그 가운데 이 변수의 출력은 `METADATA: {` 줄부터 끝까지 줄 접두(`build<탭>단계 이름<탭>`)를 떼고 185,618바이트였다(같은 명령을 `awk`·`sed`로 걸러 센 값이다). 리눅스는 환경 변수 하나를 128KiB(131,072바이트)까지만 받는다고 본다(커널의 문자열 상한 `MAX_ARG_STRLEN`에서 끌어낸 어림이고 이 러너에서 재지 않았다). 운영 문서의 실패 표(`docs/constitution/operations.md`)는 이 단계의 원인이 저장소 안이면 핫픽스로 가라고 정한다.

고침은 둘이다.

- 단계가 올린 색인의 digest를 `steps.push.outputs.metadata`가 아니라 방금 올린 커밋 해시 태그(`<이름공간>/<저장소>:sha-<커밋 해시>`)에서 `docker buildx imagetools inspect --format '{{.Manifest.Digest}}'`로 읽는다. 해시 태그는 이 실행이 바로 앞 단계에서 올린 이름이고 동시 실행 묶음이 한 번에 하나만 돌게 한다. 다만 태그는 가변이라 올린 직후 읽기까지 Docker Hub 쓰기 권한자가 덮어쓸 수 있는 창이 있고, 그 경우는 뒤의 설정 해시 대조가 막는다. 조회 자체가 실패하면 `::error::`로 닫힌 채 실패한다. 뒤의 대조(색인 → linux/amd64 매니페스트 → 설정 해시)와 출력 형식(`out/release.json`, 단계 출력)은 그대로다.
- 같은 모양(단계 출력을 통째로 환경 변수에 싣기)이 다시 들지 않게 `tests/tools/test_release_workflow.py`가 워크플로에서 `${{ steps.<id>.outputs.metadata }}`를 쓰는 줄을 막는다. 이 이름 하나만 막고, 다른 큰 출력이나 `toJSON`으로 감싼 길은 못 본다(시험 독스트링에 적었다).

이 PR은 판을 다시 내는 길이다. 번호 태그를 붙이기 전의 실패라 레지스트리에는 해시 태그만 남았고(`docker buildx imagetools inspect`로 네 저장소 모두 해시 태그가 있음을 손으로 봤다), 이 핫픽스의 병합이 같은 번호(`0.1.0-rc.1`)로 판을 낸다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 실패하는 시험을 먼저 썼다: 고치기 전 `uv run pytest tests/tools/test_release_workflow.py`가 이 저장소의 워크플로를 읽는 시험 하나만 `METADATA: ${{ steps.push.outputs.metadata }}`가 남았다며 빨갰고 변이 시험 둘은 초록이었다(1 failed, 2 passed)
- [x] 워크플로의 단계가 해시 태그에서 digest를 읽고, `repo=` 줄이 한 번만 든다(해시 태그 조회에 쓰려고 `digest=` 앞으로 옮겼고 뒤의 옛 자리는 지웠다)
- [x] 고친 단계 본문을 이 PC에서 올라간 이미지 넷(`njh6803/agent-os-{runtime,admin,widget,widget-test-page}:sha-a1a25bd…`)으로 돌렸고 종료 0, `out/release.json`이 이미지 넷의 색인 digest를 담았다. 위젯의 값 `sha256:3d6f6404…`은 실패한 실행 로그의 메타데이터 `containerimage.digest`와 같았다(손으로 돌렸다. 시험한 쪽 값은 이 PC에 없어 올린 쪽 값으로 `tested.txt`를 채웠으므로 이 실행은 구문과 부속 명령과 출력 모양만 증명하고, 시험한 이미지와 올린 이미지가 같은지 가르는 판정은 증명하지 못한다)
- [x] 위반을 잡는 변이 시험과 잡지 않는 사례를 시험으로 고정했다: 환경 변수 줄에 `${{ steps.push.outputs.metadata }}`가 있으면 잡고, 작은 출력(`steps.plan.outputs.number`)은 잡지 않는다
- [x] 못 한 것을 적었다: 이 단계 뒤의 `아티팩트 올리기`와 잡 `publish` 전체는 이번 실행에서 한 번도 돌지 못했으므로, 이 PR이 병합된 뒤의 실제 판 내기가 처음 돌린다
- [x] 검증 명령이 모두 초록이다: 이 변경이 닿는 몫(`ruff check`, `ruff format --check`, 시험 두 파일)은 손으로 쳐서 초록이었고, 나머지 게이트(`tools/run_checks.py`가 묶는 pytest 전체·pyright·lint-imports·web, 지침 검사)는 이 티켓을 싣는 커밋의 pre-commit 결과로 갈음한다. e2e와 사진 비교는 이 변경이 닿지 않아 CI에 맡긴다
