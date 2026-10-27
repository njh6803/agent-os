"""파일럿 첫 실행의 결과 커밋에 고친 환경(허용 목록의 USERNAME 등, B 설정의 env)으로 게이트만
다시 돈다.

모델 세션은 띄우지 않는다. 회차마다 새 회차 폴더에 B 클론을 짓고, 옛 회차 클론에서 결과 커밋을
가져와 `check_result`를 부른다. 게이트 묶음은 러너처럼 `has_gate_file`로 고른다.

인자: <저장소 루트> <과제 목록> <기록 폴더> <옛 회차 뿌리> <새 뿌리> <설정 폴더> <기록 이름>...
"""

import json
import os
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1])
sys.path.insert(0, str(repo))

from tools.rerun_files import read_task_list  # noqa: E402
from tools.rerun_gates import (  # noqa: E402
    GATE_ARGV,
    OLD_GATE_ARGV,
    check_result,
    has_gate_file,
)
from tools.rerun_round import build_clone, create_round_dir, session_env  # noqa: E402

tasks = {t.task_id: t for t in read_task_list(Path(sys.argv[2])).tasks}
records, old_root, new_root, config = (Path(a) for a in sys.argv[3:7])
source = Path(
    subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout.strip()
).parent

for name in sys.argv[7:]:
    rec = json.loads((records / f"{name}.json").read_text(encoding="utf-8"))
    task = tasks[rec["task_id"]]
    commit = rec["outcome"]["commit"]
    place = create_round_dir(new_root, task.task_id, rec["arm"], rec["round_no"])
    build_clone(source, task.base, task.merge, place)
    old_clone = old_root / rec["round_dir_name"] / "clone"
    subprocess.run(
        ["git", "-C", str(place.clone), "fetch", "-q", str(old_clone), commit],
        check=True,
        timeout=600,
    )
    env = session_env(os.environ, config_dir=str(config), round_dir=place)
    new_gates = has_gate_file(source, task.base, env)
    checked = check_result(
        place,
        source=source,
        commit=commit,
        task=task,
        env=env,
        out=lambda line: print("  알림:", line),
        gates=GATE_ARGV if new_gates else OLD_GATE_ARGV,
    )
    gates = [
        (" ".join(g.command.split()[-2:]), g.exit_code, g.timed_out) for g in checked.gates or ()
    ]
    print(name, place.name)
    print("  준비 실패:", checked.setup_failure)
    print("  게이트:", gates)
    print("  숨은 시험:", checked.hidden)
    sys.stdout.flush()
