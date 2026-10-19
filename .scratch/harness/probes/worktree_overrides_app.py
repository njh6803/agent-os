"""데스크톱 앱 세션에서 `tools/hook_worktree_skill_overrides.py` 가 워크트리 스킬 사본의 경로를 단
이름을 끄는지, 그 세션의 기록으로 판정한다(대기열 274).

`worktree_skill_listing.py` 는 `claude -p` 로만 재서 앱이 묶은 판을 보지 못한다. 앱 세션은
스크립트로 띄울 수 없어, 이 프로브는 판정만 하고 절차는 세션과 사람이 손으로 한다.
1. 앱에서 주 체크아웃을 연 세션이 `EnterWorktree(name)` 으로 새 워크트리에 들어간다. 훅이 주
   체크아웃의 `.claude/settings.local.json` 에 그 워크트리의 키를 적는다. 둘째 회차는 다른 앱
   세션이 그 워크트리에 `EnterWorktree(path)` 로 다시 들어갔고, 키는 이미 있었다. 다시 들어가는
   회차는 앞 회차의 `late-check` 를 지운 뒤에 들어간다. 남아 있으면 훅이 들어갈 때 그 키도 적어
   양성 대조가 깨진다(훅의 `updated` 를 임시 폴더로 불러 봤다).
2. 세션이 워크트리 안에 새 스킬 `.claude/skills/late-check/SKILL.md` 를 만든다. 들어간 뒤 생긴
   스킬이라 훅의 키에 없다(양성 대조).
3. 세션이 도구 호출을 몇 번 더 하고, 만든 것만으로 `late-check` 가 든 목록이 생기지 않았는지
   본다(이 프로브를 기준 줄을 기록의 줄 수보다 크게 주어 돌리면 모든 목록이 `listings_before` 에
   담긴다. 거기에 `late-check` 가 없어야 하고, 있으면 `not_measured_because` 가 그렇다고 적는다).
   그리고 기록의 줄 수를 기준 줄로 적는다.
4. 워크트리 세션은 주 체크아웃 파일을 고치지 못하므로, 사람이 주 체크아웃의 스킬 파일 하나를
   고쳐(끝에 빈 줄을 더한다. 둘째 회차는 첫 회차가 더한 빈 줄을 지웠다) 저장하고 메시지를 보낸다.
5. 세션이 이 프로브를 돌린다. 추가분은 사람 메시지가 아니라 그 뒤의 도구 결과에 붙기도 하므로(둘째
   회차는 메시지 뒤 첫 도구 결과 셋 다음에 붙었다), `not_measured_because` 가 기준 줄 뒤 목록에
   `late-check` 가 없다고 하면 도구 호출을 한 번 더 한 뒤 다시 돌린다. 끝나면 `late-check` 를 지우고
   사람이 편집을 되돌린다.

기록의 자리: 앱 세션은 `EnterWorktree` 뒤 기록 파일을 워크트리 이름의 프로젝트 폴더
(`~/.claude/projects/<주 체크아웃 폴더>--claude-worktrees-<워크트리>/<세션 ID>.jsonl`)로 옮겼고,
옮긴 파일에 첫 목록부터 세션 전체가 있었다(2026-10-19 손으로 봤다).

표지: 기준 줄 뒤의 `skill_listing` 첨부에 `late-check` 가 있다. 목록이 워크트리 사본을 다시 훑었을
때만 실린다. 기준 줄 앞의 첨부에 이미 실렸으면 목록이 사람의 편집 전에 워크트리를 다시 훑은
것이라, 기준 줄 뒤의 목록을 그 편집이 낳았다고 볼 수 없어 측정이 아니다.
추가분이 늘어난 이름만 담는 것도 아니다(2026-10-19 첫 회차의 378번째 줄과 둘째 회차의 235번째
줄에 첫 목록의 이름 넷이 맨 이름으로 다시 들었다). 이름의 꼴은 둘을 다 받는다. 첫 판은 경로를 단
이름(`.claude/worktrees/<워크트리>:late-check`)만 표지로 보아 "측정 아님"을 냈는데, 원본을 보니 그
회차에서 앱 2.1.299 는 주 체크아웃에 같은 이름의 스킬이 있는 사본 열하나에 경로를 달았고, 이름이
겹치지 않는 `late-check` 는 맨 이름으로 실었다(둘째 회차도 같았지만 같은 워크트리의 같은 스킬이라,
이름을 다는 규칙으로 일반화하지 않는다). 훅의 키(그 워크트리 접두의 `"off"`)가 없어도 측정이 아니다.
목록은 추가분(`isInitial` 거짓)이든 아니든 모두 보고, 출력의 목록마다 `isInitial` 이 참인지를
싣는다. 세션 도중에도 `isInitial` 이 참인 목록이 붙는다. 둘째 회차에서는 사람 메시지에 그런
목록(첫 목록과 같은 이름 72개, 경로를 단 이름과 `late-check` 없음)이 붙은 뒤 다음 도구 결과에
추가분이 붙었다. 그런 목록에 경로를 단 이름이 실려도 모델에게 보이고, 기준 줄 앞의 그런 목록에
`late-check` 가 실려도 편집 전에 다시 훑은 것이다. 첫 판은 추가분만 보아 둘 다 놓쳤다(셀프 리뷰).

판정: 측정이고 기준 줄 뒤 목록에 훅의 키 이름이 하나도 없으면 통과, 있으면 실패. 설정 파일에서는
그 워크트리 접두의 `skillOverrides` 키만 꺼내고 다른 값은 찍지 않는다. 결과는 JSON 한 줄이다.

못 보는 것:
- 원인. 실패해도 이 판정은 왜 키가 먹지 않았는지 가르지 않는다(세션이 주 체크아웃이 아닌 자리의
  local 을 읽는다, 그 판이 경로를 단 키를 맞추지 않는다, 바꿔 끼운 파일을 설정 감시가 보지 못한다).
  기록에 남은 첨부만 본다. 회차는 둘이고 둘 다 같은 워크트리다(`late-check` 없이 남은 셋째 기록은
  측정이 아니다, README 행).
- 목록이 워크트리를 다시 훑게 한 것. 표지는 다시 훑었다는 것만 보이고, 그것이 주 체크아웃의
  변경인지 들어간 뒤 생긴 `late-check` 인지는 가르지 않는다.
- 측정 때의 키. 셋째 인자는 판정할 때 읽는다. 워크트리를 지운 뒤 다른 `EnterWorktree` 에서 훅이 그
  워크트리의 키를 걷으면(훅 독스트링) 주 체크아웃의 local 로는 "훅의 키가 없다"가 된다. 그래서
  2026-10-19 첫 회차의 키는 주 체크아웃의 local 에서 그 워크트리 접두의 키만 꺼내
  `worktree_overrides_app_keys.json` 으로 옮겨 두었다(그 회차의 판정 뒤, 같은 날). 둘째 회차는 같은
  워크트리라 그 파일로 판정해도 주 체크아웃의 local 로 판정한 결과와 같았다.

돌리는 법: `uv run --no-project python .scratch/harness/probes/worktree_overrides_app.py` 에 인자
넷(기록 jsonl, 워크트리 이름, 훅의 키를 담은 설정 JSON(주 체크아웃의 `.claude/settings.local.json`
이나 그 키를 옮긴 스냅샷), 기준 줄)을 준다. 표준 라이브러리만 쓴다. 종료 코드: 0 측정이다, 1 측정이
아니다(출력의 JSON 한 줄이 함께 나온다), 2 인자가 넷이 아니다. 파일을 읽지 못하면 트레이스백과 함께
1이라, 1 은 JSON 한 줄이 있을 때만 측정 아님이다.
"""

import json
import sys

if len(sys.argv) != 5:
    print("인자: <기록 jsonl> <워크트리 이름> <설정 JSON> <기준 줄>", file=sys.stderr)
    sys.exit(2)
transcript, worktree, settings_path, base = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
prefix = f".claude/worktrees/{worktree}:"
late_names = {"late-check", prefix + "late-check"}

with open(settings_path, encoding="utf-8") as f:
    settings = json.load(f)
overrides = settings.get("skillOverrides") if isinstance(settings, dict) else None
hooked = sorted(
    k
    for k, v in (overrides.items() if isinstance(overrides, dict) else [])
    if k.startswith(prefix) and v == "off"
)

versions: set[str] = set()
before: list[tuple[int, bool, list[str]]] = []
after: list[tuple[int, str, bool, list[str]]] = []
with open(transcript, encoding="utf-8") as f:
    for no, line in enumerate(f, 1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        version = obj.get("version")
        if isinstance(version, str):
            versions.add(version)
        att = obj.get("attachment")
        if not isinstance(att, dict) or att.get("type") != "skill_listing":
            continue
        initial = att.get("isInitial") is True
        names = [n for n in att.get("names", []) if isinstance(n, str)]
        if no > base:
            after.append((no, str(obj.get("timestamp")), initial, names))
        else:
            before.append((no, initial, names))

after_names = [n for _, _, _, ns in after for n in ns]
late_before = any(late_names & set(ns) for _, _, ns in before)
late_after = bool(late_names & set(after_names))
leaked = sorted(set(after_names) & set(hooked))
measured = bool(after) and late_after and bool(hooked) and not late_before
reasons = []
if not hooked:
    reasons.append("훅의 키가 없다")
if not after:
    reasons.append("기준 줄 뒤 목록이 없다")
elif not late_after:
    reasons.append("기준 줄 뒤 목록에 late-check 가 없다")
if late_before:
    reasons.append("late-check 가 기준 줄 앞 목록에 이미 실렸다")
result = {
    "version": sorted(versions),
    "worktree": worktree,
    "hooked": len(hooked),
    "listings_before": before,
    "listings_after": after,
    "leaked": leaked,
    "measured": measured,
    "verdict": ("통과" if not leaked else "실패") if measured else "측정 아님",
    "not_measured_because": reasons,
}
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if measured else 1)
