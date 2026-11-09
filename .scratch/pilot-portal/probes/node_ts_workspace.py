"""질문 페이지가 node 로 `.ts` 를 빌드 없이 돌릴 때, 워크스페이스 패키지와 디자인 시스템의 토큰
CSS·글꼴을 그대로 읽을 수 있는지를 소비 지점(실행, 타입 검사, Next 설정 파일)까지 잰다. ADR 0050
"띄우기"가 명세 전에 재라고 넘긴 조합이다.

실행 자리. `web/apps/widget/` 안에 임시 폴더를 만들고 거기서 `.ts` 입구를 node 로 돌린다. 그
자리에서 풀리는 `node_modules` 가 위젯의 것이라 `@agent-os/*` 는 pnpm 의 심볼릭
링크(`../../../../packages/<이름>`)로, `smol-toml`·`openapi-fetch` 같은 의존성은 `.pnpm` 스토어로
풀린다. 질문 페이지 앱도 `web/apps/` 아래 같은 깊이에 서므로 링크의 모양이 같다. 여섯 묶음을 잰다.

1. 타입 벗기기(`strip_*`).
   - `strip_subpath`(양성): `@agent-os/ui/contrast` 를 패키지 이름으로 읽어 `MODES` 를 받는다.
     표지는 출력 JSON 의 `modes` 가 `["light", "dark"]` 인 것이고, `require.resolve` 가 낸 실제
     경로에 `node_modules` 가 드는지도 적는다.
   - `strip_preserve_symlinks`(갈래): 같은 입구를 `--preserve-symlinks` 로 돌린다. 링크를 풀지
     않으면 경로가 `node_modules` 아래라 node 가 타입 벗기기를 거부한다는 해석을, 링크와 무관하게
     읽힌다는 해석과 가른다. 표지는 JSON 이 나오거나 `ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING`
     이 나오는 것이다.
   - `strip_inside_node_modules`(대조): 임시 폴더 안 `node_modules/probe-ts-pkg/index.ts` 를 읽는다.
     표지는 `ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING`.
   - `strip_root_index`(대조): `@agent-os/ui` 의 `.` 진입점(`src/index.ts`)을 읽는다. 표지는
     `ERR_MODULE_NOT_FOUND` 나 `ERR_UNKNOWN_FILE_EXTENSION` 이고 어느 것이었는지와 걸린 지정자를
     적는다.
   - `strip_tsx_file`(대조): `.tsx` 파일 하나를 확장자까지 적어 읽는다. 표지는
     `ERR_UNKNOWN_FILE_EXTENSION`.
   - `strip_themes_file`(양성): `src/themes.ts` 를 상대 경로로 읽어
     `THEMES`·`DEFAULT_THEME`·`MODES`·`DENSITIES` 를 받는다. 그 파일을 서브패스 export 로 열었을 때
     읽히는지의 대리다(export 지도를 지나는 길은 `strip_subpath` 가 잰다).
   - `strip_package_dep`(양성): `api-client` 의 `clients.ts` 를 상대 경로로 읽는다. 그 파일의 값
     import 는 `openapi-fetch` 하나이고(`./generated/openapi` 는 `import type` 이라 벗겨진다), 그
     의존성이 어디서 풀리는지 적는다. 사이트 파일 읽기를 패키지로 옮겼을 때 `smol-toml` 이 풀리는
     길과 같다.
   - `strip_api_client_root`(대조): `@agent-os/api-client` 를 패키지 이름으로 읽는다. 그 진입점의
     상대 import 에 확장자가 없어 표지는 `ERR_MODULE_NOT_FOUND` 다.
2. 타입 검사(`tsc_*`). 양성 입구 둘(`strip_subpath`·`strip_themes_file` 의 것)과 변이 하나를
   `moduleResolution` 두 갈래(`nodenext`, 위젯 tsconfig 와 같은 `bundler`)로 tsc `--noEmit` 에
   넣는다. 깨끗한 판은 종료 0 과 `error TS` 없음, 변이(`MODES[0]` 을 `number` 에 대입)는 `TS2322` 가
   표지다. 변이가 양성 대조다. `clients.ts` 의 입구는 넣지 않는다. 그 패키지는 제 tsconfig 로
   검사하고, 질문 페이지가 그 파일을 import 하지 않는다. 확장자 없는 상대 import(`extensionless.ts`
   가 `themes` 를 `.ts` 없이 든다)도 두 갈래에 넣는다. `nodenext` 는 `TS2835` 로 막고(표지는 그
   파일 이름이 붙은 그 코드), `bundler` 는 지난다(표지는 종료 0 과 `--listFiles` 목록에 그 파일이 든
   것. 파일이 프로그램에 들었는데도 오류가 없어야 "지난다"다). 명세가 `nodenext` 를 고른 까닭(node
   가 실제로 푸는 규칙을 타입 검사가 같이 강제한다)의 근거이고, `nodenext` 회차가 양성 대조,
   `bundler` 회차가 갈래다. 두 묶음이 함께 쓰는 양성 입구 둘은 `entry_subpath_file` 과
   `entry_themes_file` 이 쓰므로 `--group tsc` 만 돌려도 선다(첫 판은 strip 묶음이 쓴 파일에 기대
   `--group tsc` 만으로는 파일을 찾지 못했다).
3. 디자인 토큰 CSS(`theme_css_build`). 패키지 `build` 의 둘째
   명령(`tailwindcss -i src/styles/theme.css -o …`)을 임시 폴더로 돌려, 산출에 Tailwind
   지시문(`@theme`·`@import`·`@source`·`@apply`)이 남는지, 화면 그림(`design/pp-page.dc.html`)이
   `var(--…)` 로 읽는 변수가 모두 선언되는지, 어떤 `@layer` 가 들고 클래스 선택자가 몇 개인지,
   크기와 걸린 시간을 적는다. 원본에 그 지시문이 있는 것이 양성 대조다. 같은 명령을 node 프로세스가
   `child_process.spawnSync` 로 자식으로 띄워 산출 파일을 메모리에 읽고 지우는
   회차(`theme_css_build_child`)를 더 둔다. 질문 페이지 서버가 시작 때 하는 모양이다. 표지는 자식의
   종료 0, 지운 뒤 파일이 없는 것, 읽은 글이 바로 돌린 회차와 같은 바이트이고 같은 변수 판정을
   지나는 것이다.
4. 글꼴(`fonts_files`). 위젯의 `tools/fonts.ts` 를 그대로 읽어 글꼴 CSS 가 가리키는 woff2 파일 수와
   크기, `@font-face` 수를 받는다. 글꼴 CSS 원본의 `@import "@fontsource/…"` 수가 양성 대조다.
   옮겨 갈 자리의 자기 참조(`fonts_css_self_reference`)도 잰다. `web/packages/ui/` 안 임시 폴더의
   `.ts` 가 `createRequire(import.meta.url).resolve("@agent-os/ui/fonts.css")` 로 패키지 자신의
   서브패스를 푼다(위젯의 `tools/fonts.ts` 가 하는 일을 패키지 안에서 하는 것). 표지는 푼 경로가 그
   패키지의 `src/styles/fonts.css` 인 것이고, 갈래로 export 지도에 없는 서브패스가
   `ERR_PACKAGE_PATH_NOT_EXPORTED` 로 거부되는 것을 함께 본다. 그래야 푼 길이 다른 `node_modules` 가
   아니라 자기 `package.json` 의 export 지도다.
5. Next 설정(`next_config_*`). 임시 폴더의 `next.config.ts` 가 `@agent-os/ui/contrast`, `smol-toml`,
   이웃 `./local.ts` 를 import 하고, `next build` 가 설정을 읽는 함수(`next/dist/server/config.js`
   의 `loadConfig`)로 읽는다. 표지는 `env` 에 세 값이 그대로 실린 것이다.
   - `next_config_legacy`(양성): 기본 길(SWC 로 CJS 로 옮기고 `require.extensions` 에 `.ts` 훅을
     건 뒤 `requireFromString` 으로 평가하는 `handleCJS`)을, 위젯의 `tools/start.ts` 가 next 를
     부르기 전에 `process.chdir(APP)` 하듯 작업 디렉터리를 설정 파일의 폴더로 두고 돌린다.
   - `next_config_legacy_other_cwd_missing`(갈래): 같은 길을 작업 디렉터리만 임시 폴더로 옮겨
     돌린다. 표지는 stderr 의 `Cannot find module './local.ts'` 다.
   - `next_config_legacy_other_cwd_decoy`(갈래): 그 임시 폴더에 다른 값(`local-from-cwd`)을 내는
     `local.ts` 를 두고 다시 돌린다. 표지는 `PROBE_LOCAL` 이 그 값인 것이다. 기본 길의 상대 import
     가 설정 파일의 폴더가 아니라 작업 디렉터리를 기준으로 풀린다는 해석을, 상대 `.ts` import 자체가
     안 된다는 해석과 가른다. 까닭은 `requireFromString` 이 `new Module(filename)` 에 `_compile`
     만 불러 `filename` 이 `null` 로 남고(Next 의 `require-hook.js` 를 읽었다), node 의 CJS 로더가
     `filename` 없는 부모의 상대 요청에 기준 폴더 `['.']` 를 돌려주기 때문이다(node 24.19.0 의
     `Module._resolveLookupPaths` 를 `toString()` 으로 읽었고, 같은 모양의 `Module` 에 그 함수를
     불러 `filename` 이 `null` 이고 결과가 `["."]` 인 것을 손으로 봤다. 명령은 README).
   - `next_config_native_other_cwd`(대조): `__NEXT_NODE_NATIVE_TS_LOADER_ENABLED=true` 의 node
     네이티브 길을 임시 폴더에서 돌린다. ESM `import()` 라 작업 디렉터리와 무관하게 설정 파일 곁의
     `local.ts` 를 읽는다. Next 가 대체 길로 떨어지면 그 변수를 `false` 로 바꾸므로 끝난 뒤의 값도
     적는다.
6. 페이지 스크립트(`page_script_*`). 브라우저는 `.ts` 를 읽지 못하므로, 서버가 시작 때
   `node:module` 의 `stripTypeScriptTypes` 로 타입만 벗겨 내주는 길이 서는지 본다.
   - `page_script_strip`(양성): 타입 별칭과 주석이 든 스크립트를 `strip` 모드로 벗긴 뒤
     `vm.runInThisContext` 로 돌린다. 표지는 돌린 결과(전역에 둔 라벨 글)가 기대와 같고 산출에 타입
     주석과 `type` 선언이 남지 않은 것이다. 줄 수가 원본과 같은지도 적는다.
   - `page_script_strip_enum`(갈래): 지울 수 없는 문법(`enum`)을 같은 모드로 벗긴다. 표지는
     `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` 로 거부되거나 산출 글이 나오는 것이다. 거부되면 기준
     tsconfig 의 `erasableSyntaxOnly` 와 같은 선이다. 첫 판은 표지를 `ERR_INVALID_TYPESCRIPT_SYNTAX`
     로 적었고 첫 실행의 원본이 낸 코드가 `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` 라 그 코드로 고쳤다
     (틀린 문법이 아니라 지원하지 않는 문법의 코드다. 결과를 본 뒤 바꾼 기준이고 README 에 적었다).

하위 프로세스는 모두 스스로 끝나는 명령이라 끝난 뒤 출력을 한 번에 받는다(`subprocess.run`, 제한
시간 있음). 끝나기 전에 출력을 이어 읽지 않으므로 `tools/probe_kit.py` 의 `LineReader` 는 쓰지
않는다. stderr 는 표지(오류 코드)를 읽어야 해서 버리지 않고 받는다.

못 보는 것. 이 PC(Windows)만 쟀다. 질문 페이지 앱 자체(제 `package.json` 과 의존성)는 만들지 않고
위젯 폴더의 링크 모양으로 대신했다. Next 는 `next build` 전체가 아니라 설정을 읽는 함수만 돌렸다.
CSS 짓기의 시간은 실행마다 회차 하나씩 잰 값이다(README 가 범위를 적는다). 자기 참조 회차는 임시
폴더를 디자인 시스템 패키지 안에 만들었다 지울 뿐 그 패키지의 파일은 건드리지 않고, 글꼴 도우미를
실제로 옮긴 파일이 도는지는 재지 않는다. e2e 준비 코드를 패키지로 옮기는 모양은 재지 않는다.

돌리는 명령은 같은 폴더의 `README.md` 에 있다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

WEB = ROOT / "web"
WIDGET = WEB / "apps" / "widget"
UI = WEB / "packages" / "ui"
API_CLIENT = WEB / "packages" / "api-client"
DESIGN_PAGE = ROOT / ".scratch" / "pilot-portal" / "design" / "pp-page.dc.html"
TSC = WEB / "node_modules" / "typescript" / "lib" / "tsc.js"
TAILWIND = UI / "node_modules" / "@tailwindcss" / "cli" / "dist" / "index.mjs"
NODE_TIMEOUT = 180.0
TOOL_TIMEOUT = 600.0
NATIVE_FLAG = "__NEXT_NODE_NATIVE_TS_LOADER_ENABLED"
EXPECTED_MODES = ["light", "dark"]
EXPECTED_THEMES = ["guncheong", "nokcheong", "jacho", "jjokbit"]
NM_STRIP = "ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING"
DIRECTIVES = re.compile(r"^\s*@(theme|import|source|apply)\b", re.MULTILINE)
CSS_VAR_USE = re.compile(r"var\((--[a-z0-9-]+)")
CSS_VAR_DECL = re.compile(r"(--[a-z0-9-]+)\s*:")
LAYER_DECL = re.compile(r"^@layer ([a-z]+) \{", re.MULTILINE)
CLASS_SELECTOR = re.compile(r"^\s*\.[a-z][a-z0-9_\\:-]*\s*[,{]", re.MULTILINE)
UTILITIES = ("flex", "shadow-float", "text-body", "gap-3", "text-small")


@dataclass(frozen=True)
class Run:
    """하위 프로세스 한 번. `code` 가 None 이면 제한 시간을 넘겨 끊었다."""

    argv: tuple[str, ...]
    cwd: str
    code: int | None
    stdout: str
    stderr: str
    seconds: float

    def as_dict(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "cwd": self.cwd,
            "code": self.code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "seconds": round(self.seconds, 3),
        }


def _text(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def run(
    argv: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    unset: tuple[str, ...] = (),
    timeout: float = NODE_TIMEOUT,
) -> Run:
    merged = {**os.environ, **(env or {})}
    for name in unset:
        merged.pop(name, None)
    started = time.monotonic()
    try:
        done = subprocess.run(
            argv, cwd=cwd, env=merged, capture_output=True, timeout=timeout, check=False
        )
        code: int | None = done.returncode
        out, err = _text(done.stdout), _text(done.stderr)
    except subprocess.TimeoutExpired as expired:
        code = None
        out, err = _text(expired.stdout), _text(expired.stderr)
    return Run(tuple(argv), str(cwd), code, out, err, time.monotonic() - started)


def _last_json(stdout: str) -> dict[str, object] | None:
    """stdout 의 마지막 `{` 로 시작하는 줄을 JSON 으로 푼다. 입구가 찍는 한 줄이다."""
    for raw_line in reversed(stdout.splitlines()):
        line = raw_line.strip()
        if line.startswith("{"):
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) else None
    return None


def _error_code(stderr: str) -> str | None:
    found = re.search(r"\b(ERR_[A-Z_]+)\b", stderr)
    return found.group(1) if found else None


def _missing_specifier(stderr: str) -> str | None:
    """`ERR_MODULE_NOT_FOUND` 의 지정자나 `ERR_UNKNOWN_FILE_EXTENSION` 의 확장자."""
    found = re.search(r"Cannot find module '([^']+)'", stderr)
    if found:
        return found.group(1)
    found = re.search(r'Unknown file extension "([^"]+)"', stderr)
    return found.group(1) if found else None


def rel(target: Path, start: Path) -> str:
    return Path(os.path.relpath(target, start)).as_posix()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def package_version(package_json: Path) -> str:
    try:
        parsed = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "?"
    version = parsed.get("version") if isinstance(parsed, dict) else None
    return version if isinstance(version, str) else "?"


@dataclass
class Probe:
    """회차들이 나눠 쓰는 자리. 임시 폴더, 회차 셈, 원본 기록, 사람이 읽을 세부 줄."""

    node: str
    tmp: Path
    rounds: Rounds = field(default_factory=Rounds)
    raw: dict[str, object] = field(default_factory=dict[str, object])
    details: list[str] = field(default_factory=list[str])

    def node_run(
        self,
        label: str,
        args: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        unset: tuple[str, ...] = (),
        timeout: float = NODE_TIMEOUT,
    ) -> Run:
        result = run([self.node, *args], cwd or self.tmp, env=env, unset=unset, timeout=timeout)
        self.raw[label] = result.as_dict()
        return result

    def detail(self, label: str, text: str) -> None:
        self.details.append(f"{label}: {text}")


def entry_json_round(
    probe: Probe,
    label: str,
    entry: Path,
    expect: Callable[[dict[str, object]], str | None],
    *,
    node_flags: list[str] | None = None,
) -> None:
    """입구를 돌려 JSON 한 줄을 받는 양성 회차. `expect` 는 JSON 이 표지와 맞으면 결과 글을, 아니면
    None."""
    with probe.rounds.round(label) as current:
        result = probe.node_run(label, [*(node_flags or []), str(entry)])
        parsed = _last_json(result.stdout) if result.code == 0 else None
        verdict = expect(parsed) if parsed is not None else None
        if verdict is None:
            probe.detail(label, f"종료 {result.code}, stderr 머리: {result.stderr.strip()[:300]!r}")
            return
        probe.detail(label, f"{verdict} ({result.seconds:.1f}초)")
        current.mark(measured=True, result=verdict)


def failure_round(
    probe: Probe,
    label: str,
    entry: Path,
    codes: tuple[str, ...],
    specifier: str | None = None,
) -> None:
    """실패를 기대하는 대조 회차. 표지는 기대한 오류 코드 가운데 하나가 stderr 에 있는 것이고,
    `specifier` 를 주면 찾지 못한 지정자(구분자를 `/` 로 맞춘 것)에 그 조각까지 있어야 한다. 패키지
    자체가 없어도 `ERR_MODULE_NOT_FOUND` 는 나므로, 확장자 없는 상대 import 에서 막히는 것을 재는
    회차는 그 지정자를 표지에 둔다(PR #504 의 CodeRabbit 이 짚었다)."""
    with probe.rounds.round(label) as current:
        result = probe.node_run(label, [str(entry)])
        code = _error_code(result.stderr)
        where = _missing_specifier(result.stderr)
        normalized = (where or "").replace("\\", "/")
        wrong_specifier = specifier is not None and specifier not in normalized
        if result.code == 0 or code not in codes or wrong_specifier:
            probe.detail(
                label,
                f"기대한 코드 {codes} 나 지정자 조각 {specifier!r} 이 아님. 종료 {result.code}, "
                f"코드 {code}, 지정자 {where!r}, stderr 머리: {result.stderr.strip()[:300]!r}",
            )
            return
        verdict = f"거부 {code}" + (f" ({where})" if where else "")
        probe.detail(label, verdict)
        current.mark(measured=True, result=verdict)


def entry_subpath_file(tmp: Path) -> Path:
    """`@agent-os/ui/contrast` 를 패키지 이름으로 읽는 양성 입구. strip 과 tsc 묶음이 함께 쓴다."""
    subpath = tmp / "entry_subpath.ts"
    write(
        subpath,
        "\n".join(
            [
                'import { createRequire } from "node:module";',
                'import { MODES } from "@agent-os/ui/contrast";',
                "const modes: readonly string[] = MODES;",
                "const requireResolve: string = createRequire(import.meta.url).resolve(",
                '  "@agent-os/ui/contrast",',
                ");",
                "console.log(",
                "  JSON.stringify({",
                "    modes,",
                '    metaResolve: import.meta.resolve("@agent-os/ui/contrast"),',
                "    requireResolve,",
                "  }),",
                ");",
                "",
            ]
        ),
    )
    return subpath


def entry_themes_file(tmp: Path) -> Path:
    """`src/themes.ts` 를 확장자 있는 상대 경로로 읽는 양성 입구. strip 과 tsc 묶음이 함께 쓴다."""
    themes = tmp / "entry_themes.ts"
    ui_src = rel(UI / "src", tmp)
    write(
        themes,
        "\n".join(
            [
                f'import {{ DEFAULT_THEME, DENSITIES, MODES, THEMES }} from "{ui_src}/themes.ts";',
                "console.log(",
                "  JSON.stringify({",
                "    themes: THEMES.map((entry) => entry.key),",
                "    defaultTheme: DEFAULT_THEME,",
                "    modes: MODES,",
                "    densities: DENSITIES,",
                "  }),",
                ");",
                "",
            ]
        ),
    )
    return themes


def strip_rounds(probe: Probe) -> None:
    tmp = probe.tmp
    ui_src = rel(UI / "src", tmp)
    api_src = rel(API_CLIENT / "src", tmp)
    subpath = entry_subpath_file(tmp)

    def expect_modes(parsed: dict[str, object]) -> str | None:
        if parsed.get("modes") != EXPECTED_MODES:
            return None
        resolved = str(parsed.get("requireResolve", ""))
        inside = "node_modules" in resolved.replace("\\", "/")
        return "읽힘, 실제 경로 node_modules " + ("안" if inside else "밖")

    entry_json_round(probe, "strip_subpath", subpath, expect_modes)

    with probe.rounds.round("strip_preserve_symlinks") as current:
        result = probe.node_run("strip_preserve_symlinks", ["--preserve-symlinks", str(subpath)])
        parsed = _last_json(result.stdout) if result.code == 0 else None
        code = _error_code(result.stderr)
        if parsed is not None and parsed.get("modes") == EXPECTED_MODES:
            verdict = "읽힘(링크를 풀지 않아도)"
        elif result.code != 0 and code == NM_STRIP:
            verdict = f"거부 {code}(링크를 풀지 않으면 node_modules 안)"
        else:
            probe.detail(
                "strip_preserve_symlinks",
                f"표지 없음. 종료 {result.code}, 코드 {code}, "
                f"stderr 머리: {result.stderr.strip()[:300]!r}",
            )
            return
        probe.detail("strip_preserve_symlinks", verdict)
        current.mark(measured=True, result=verdict)

    fake = tmp / "node_modules" / "probe-ts-pkg"
    write(
        fake / "package.json",
        json.dumps({"name": "probe-ts-pkg", "type": "module", "exports": {".": "./index.ts"}}),
    )
    write(fake / "index.ts", 'export const MODES: readonly string[] = ["light", "dark"];\n')
    inside = tmp / "entry_inside_nm.ts"
    write(
        inside,
        'import { MODES } from "probe-ts-pkg";\nconsole.log(JSON.stringify({ modes: MODES }));\n',
    )
    failure_round(probe, "strip_inside_node_modules", inside, (NM_STRIP,))

    root = tmp / "entry_root.ts"
    write(
        root,
        'import { THEMES } from "@agent-os/ui";\n'
        "console.log(JSON.stringify({ themes: THEMES.map((entry) => entry.key) }));\n",
    )
    failure_round(
        probe, "strip_root_index", root, ("ERR_MODULE_NOT_FOUND", "ERR_UNKNOWN_FILE_EXTENSION")
    )

    tsx = tmp / "entry_tsx.ts"
    write(
        tsx,
        f'import {{ Button }} from "{ui_src}/components/atoms/Button.tsx";\n'
        "console.log(JSON.stringify({ button: typeof Button }));\n",
    )
    failure_round(probe, "strip_tsx_file", tsx, ("ERR_UNKNOWN_FILE_EXTENSION",))

    themes = entry_themes_file(tmp)

    def expect_themes(parsed: dict[str, object]) -> str | None:
        ok = (
            parsed.get("themes") == EXPECTED_THEMES
            and parsed.get("defaultTheme") == "nokcheong"
            and parsed.get("modes") == EXPECTED_MODES
            and parsed.get("densities") == ["compact", "regular"]
        )
        return "읽힘, 테마 넷·모드 둘·밀도 둘" if ok else None

    entry_json_round(probe, "strip_themes_file", themes, expect_themes)

    dep = tmp / "entry_dep.ts"
    write(
        dep,
        "\n".join(
            [
                'import { createRequire } from "node:module";',
                f'import {{ createWidgetClient }} from "{api_src}/clients.ts";',
                f'const clients: string = import.meta.resolve("{api_src}/clients.ts");',
                'const openapiFetch: string = createRequire(clients).resolve("openapi-fetch");',
                "console.log(JSON.stringify({ client: typeof createWidgetClient, openapiFetch }));",
                "",
            ]
        ),
    )

    def expect_dep(parsed: dict[str, object]) -> str | None:
        if parsed.get("client") != "function":
            return None
        resolved = str(parsed.get("openapiFetch", "")).replace("\\", "/")
        if "/packages/api-client/node_modules/" in resolved:
            where = "패키지 자신의 node_modules"
        elif "/.pnpm/openapi-fetch" in resolved:
            where = "pnpm 스토어(.pnpm)의 실제 경로"
        else:
            where = "다른 자리"
        return f"읽힘, 의존성은 {where}"

    entry_json_round(probe, "strip_package_dep", dep, expect_dep)

    api_root = tmp / "entry_api_root.ts"
    write(
        api_root,
        'import { createWidgetClient } from "@agent-os/api-client";\n'
        "console.log(JSON.stringify({ client: typeof createWidgetClient }));\n",
    )
    failure_round(
        probe,
        "strip_api_client_root",
        api_root,
        ("ERR_MODULE_NOT_FOUND",),
        specifier="packages/api-client/src/clients",
    )


def tsc_verdict(resolution: str, variant: str, code: int | None, output: str) -> str | None:
    """회차의 표지. 깨끗한 판은 종료 0 과 오류 없음, 변이는 그 파일의 `TS2322`, 확장자 없는 import
    는 `nodenext` 에서 그 파일의 `TS2835`, `bundler` 에서 종료 0 과 `--listFiles` 목록에 그 파일."""
    failed = code not in (0, None)
    clean = code == 0 and "error TS" not in output
    if variant == "clean":
        return "tsc 0, 오류 없음" if clean else None
    if variant == "mutated":
        hit = re.search(r"mutated\.ts\(\d+,\d+\): error TS2322", output)
        return "변이가 TS2322 로 빨감" if failed and hit else None
    if resolution == "nodenext":
        hit = re.search(r"extensionless\.ts\(\d+,\d+\): error TS2835", output)
        return "확장자 없는 import 가 TS2835 로 빨감" if failed and hit else None
    listed = "extensionless.ts" in output
    return "확장자 없는 import 가 지남(--listFiles 에 그 파일)" if clean and listed else None


def tsc_rounds(probe: Probe) -> None:
    tmp = probe.tmp
    entry_subpath_file(tmp)
    entry_themes_file(tmp)
    write(
        tmp / "mutated.ts",
        'import { MODES } from "@agent-os/ui/contrast";\n'
        "const wrong: number = MODES[0];\nconsole.log(wrong);\n",
    )
    write(
        tmp / "extensionless.ts",
        f'import {{ MODES }} from "{rel(UI / "src", tmp)}/themes";\nconsole.log(MODES.length);\n',
    )
    resolutions = {
        "nodenext": {"module": "nodenext", "moduleResolution": "nodenext"},
        "bundler": {"module": "esnext", "moduleResolution": "bundler"},
    }
    clean_files = ["entry_subpath.ts", "entry_themes.ts"]
    variants: tuple[tuple[str, list[str], list[str]], ...] = (
        ("clean", clean_files, []),
        ("mutated", [*clean_files, "mutated.ts"], []),
        ("extensionless", [*clean_files, "extensionless.ts"], ["--listFiles"]),
    )
    for name, options in resolutions.items():
        for variant, files, extra in variants:
            label = f"tsc_{name}_{variant}"
            config = tmp / f"tsconfig.{name}.{variant}.json"
            write(
                config,
                json.dumps(
                    {
                        "extends": rel(WEB / "tsconfig.base.json", tmp),
                        "compilerOptions": {
                            "target": "es2024",
                            "lib": ["es2024"],
                            **options,
                            "allowImportingTsExtensions": True,
                            "types": ["node"],
                            "noEmit": True,
                        },
                        "files": files,
                    },
                    indent=2,
                ),
            )
            with probe.rounds.round(label) as current:
                result = probe.node_run(
                    label, [str(TSC), "-p", str(config), *extra], cwd=WEB, timeout=TOOL_TIMEOUT
                )
                output = result.stdout + result.stderr
                verdict = tsc_verdict(name, variant, result.code, output)
                if verdict is None:
                    probe.detail(
                        label, f"표지 없음. 종료 {result.code}, 출력 머리: {output[:300]!r}"
                    )
                    continue
                probe.detail(label, f"{verdict} ({result.seconds:.1f}초)")
                current.mark(measured=True, result=verdict)


def mockup_variables() -> list[str]:
    """화면 그림이 `var(--…)` 로 읽는 변수 이름. 정렬했다."""
    return sorted(set(CSS_VAR_USE.findall(DESIGN_PAGE.read_text(encoding="utf-8"))))


@dataclass(frozen=True)
class DirectBuild:
    """바로 돌린 회차의 산출. 자식 회차가 같은 내용인지 sha256 으로 대 본다. 바이트 수가 같아도
    내용이 다를 수 있다(PR #504 의 CodeRabbit 이 짚었다)."""

    bytes: int
    sha256: str


def theme_css_rounds(probe: Probe) -> None:
    direct = theme_css_direct_round(probe)
    theme_css_child_round(probe, direct)


def theme_css_direct_round(probe: Probe) -> DirectBuild | None:
    """Tailwind CLI 를 바로 돌린다. 측정이면 산출의 바이트 수와 sha256 을 돌려준다."""
    label = "theme_css_build"
    out_css = probe.tmp / "theme.css"
    source = UI / "src" / "styles" / "theme.css"
    with probe.rounds.round(label) as current:
        raw_directives = DIRECTIVES.findall(source.read_text(encoding="utf-8"))
        result = probe.node_run(
            label,
            [str(TAILWIND), "-i", "src/styles/theme.css", "-o", str(out_css)],
            cwd=UI,
            timeout=TOOL_TIMEOUT,
        )
        if result.code != 0 or not out_css.exists():
            probe.detail(label, f"짓기 실패. 종료 {result.code}, stderr: {result.stderr[:300]!r}")
            return None
        built = out_css.read_text(encoding="utf-8")
        left = DIRECTIVES.findall(built)
        declared = set(CSS_VAR_DECL.findall(built))
        used = mockup_variables()
        missing = [name for name in used if name not in declared]
        utilities = {
            name: re.search(rf"^\s*\.{re.escape(name)}\s*\{{", built, re.MULTILINE) is not None
            for name in UTILITIES
        }
        summary = {
            "rawDirectives": len(raw_directives),
            "leftDirectives": left,
            "bytes": len(built.encode("utf-8")),
            "sha256": hashlib.sha256(built.encode("utf-8")).hexdigest(),
            "seconds": round(result.seconds, 2),
            "declaredVariables": len(declared),
            "usedByMockup": used,
            "missingForMockup": missing,
            "layers": LAYER_DECL.findall(built),
            "classSelectors": len(CLASS_SELECTOR.findall(built)),
            "utilities": utilities,
            "bodySizeDeclared": "--body-size" in declared,
        }
        probe.raw[f"{label}.summary"] = summary
        probe.detail(label, json.dumps(summary, ensure_ascii=False))
        if not raw_directives or left or "--body-size" not in declared:
            return None
        covered = len(used) - len(missing)
        verdict = f"지시문 {len(raw_directives)}→0, 그림의 변수 {covered}/{len(used)} 선언"
        current.mark(measured=True, result=verdict)
        encoded = built.encode("utf-8")
        return DirectBuild(bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest())
    return None


def theme_css_child_round(probe: Probe, direct: DirectBuild | None) -> None:
    """node 프로세스가 Tailwind CLI 를 자식으로 띄워 산출을 메모리에 읽고 파일을 지운다. 질문 페이지
    서버가 시작 때 하는 모양이다. 표지는 자식의 종료 0, 지운 뒤 파일 없음, 바로 돌린 회차와 같은
    sha256(바이트 수만 같은 것은 표지가 아니다), 같은 변수 판정이다."""
    label = "theme_css_build_child"
    script = probe.tmp / "css_child.mjs"
    out_css = probe.tmp / "theme-child.css"
    write(
        script,
        "\n".join(
            [
                'import { spawnSync } from "node:child_process";',
                'import { existsSync, readFileSync, unlinkSync } from "node:fs";',
                "const [, , cli, cwd, out] = process.argv;",
                "const started = performance.now();",
                "const child = spawnSync(",
                "  process.execPath,",
                '  [cli, "-i", "src/styles/theme.css", "-o", out],',
                '  { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },',
                ");",
                "const seconds = (performance.now() - started) / 1000;",
                'let css = "";',
                "if (child.status === 0 && existsSync(out)) {",
                '  css = readFileSync(out, "utf8");',
                "  unlinkSync(out);",
                "}",
                "console.log(",
                "  JSON.stringify({",
                "    status: child.status,",
                "    signal: child.signal,",
                "    seconds: Math.round(seconds * 100) / 100,",
                "    removed: !existsSync(out),",
                "    stderr: (child.stderr ?? '').slice(0, 300),",
                "    css,",
                "  }),",
                ");",
                "",
            ]
        ),
    )
    with probe.rounds.round(label) as current:
        result = probe.node_run(
            label, [str(script), str(TAILWIND), str(UI), str(out_css)], timeout=TOOL_TIMEOUT
        )
        parsed = _last_json(result.stdout) if result.code == 0 else None
        if parsed is None:
            probe.detail(label, f"종료 {result.code}, stderr 머리: {result.stderr.strip()[:300]!r}")
            return
        css = parsed.get("css")
        css_text = css if isinstance(css, str) else ""
        left = DIRECTIVES.findall(css_text)
        declared = set(CSS_VAR_DECL.findall(css_text))
        used = mockup_variables()
        missing = [name for name in used if name not in declared]
        encoded = css_text.encode("utf-8")
        child_bytes = len(encoded)
        child_sha256 = hashlib.sha256(encoded).hexdigest()
        summary = {
            "status": parsed.get("status"),
            "removed": parsed.get("removed"),
            "childSeconds": parsed.get("seconds"),
            "totalSeconds": round(result.seconds, 2),
            "bytes": child_bytes,
            "sha256": child_sha256,
            "directBytes": direct.bytes if direct is not None else None,
            "directSha256": direct.sha256 if direct is not None else None,
            "leftDirectives": left,
            "missingForMockup": missing,
            "bodySizeDeclared": "--body-size" in declared,
        }
        probe.raw[f"{label}.summary"] = summary
        probe.detail(label, json.dumps(summary, ensure_ascii=False))
        same_as_direct = direct is not None and child_sha256 == direct.sha256
        if parsed.get("status") != 0 or parsed.get("removed") is not True or not css_text:
            return
        if left or missing or "--body-size" not in declared or not same_as_direct:
            return
        verdict = (
            f"자식이 지은 {child_bytes}바이트를 메모리에 읽고 파일을 지움, "
            "바로 돌린 것과 sha256 이 같음"
        )
        current.mark(measured=True, result=verdict)


def fonts_rounds(probe: Probe) -> None:
    fonts_files_round(probe)
    fonts_self_reference_round(probe)


def fonts_self_reference_round(probe: Probe) -> None:
    """디자인 시스템 패키지 안의 `.ts` 가 `@agent-os/ui/fonts.css` 를 자기 참조로 푸는지 본다. 임시
    폴더를 그 패키지 안에 만들었다 지우고 패키지의 파일은 건드리지 않는다. 표지는 푼 경로가 그
    패키지의 `src/styles/fonts.css` 인 것과, export 지도에 없는 서브패스가
    `ERR_PACKAGE_PATH_NOT_EXPORTED` 로 거부되는 것(푼 길이 자기 export 지도라는 갈래)이다."""
    label = "fonts_css_self_reference"
    nest = Path(tempfile.mkdtemp(prefix=".probe-node-ts-", dir=UI))
    try:
        script = nest / "fonts_self.ts"
        write(
            script,
            "\n".join(
                [
                    'import { createRequire } from "node:module";',
                    "const req = createRequire(import.meta.url);",
                    'const fontsCss: string = req.resolve("@agent-os/ui/fonts.css");',
                    "let missingCode: string | null = null;",
                    "try {",
                    '  req.resolve("@agent-os/ui/__probe_missing__.css");',
                    "} catch (error) {",
                    '  missingCode = error instanceof Error && "code" in error',
                    "    ? String(error.code)",
                    "    : String(error);",
                    "}",
                    "console.log(JSON.stringify({ fontsCss, missingCode }));",
                    "",
                ]
            ),
        )
        with probe.rounds.round(label) as current:
            result = probe.node_run(label, [str(script)], cwd=nest)
            parsed = _last_json(result.stdout) if result.code == 0 else None
            if parsed is None:
                probe.detail(
                    label, f"종료 {result.code}, stderr 머리: {result.stderr.strip()[:300]!r}"
                )
                return
            resolved = str(parsed.get("fontsCss", "")).replace("\\", "/")
            expected = (UI / "src" / "styles" / "fonts.css").resolve().as_posix()
            missing_code = parsed.get("missingCode")
            probe.detail(label, json.dumps(parsed, ensure_ascii=False))
            if resolved.lower() != expected.lower():
                return
            if missing_code != "ERR_PACKAGE_PATH_NOT_EXPORTED":
                return
            verdict = (
                "패키지 안에서 @agent-os/ui/fonts.css 가 자기 export 지도로 풀림, "
                "없는 서브패스는 ERR_PACKAGE_PATH_NOT_EXPORTED"
            )
            current.mark(measured=True, result=verdict)
    finally:
        shutil.rmtree(nest, ignore_errors=True)


def fonts_files_round(probe: Probe) -> None:
    label = "fonts_files"
    script = probe.tmp / "fonts_probe.mjs"
    write(
        script,
        "\n".join(
            [
                'import { readFileSync, statSync } from "node:fs";',
                'import { pathToFileURL } from "node:url";',
                "const [, , fontsTs, fontsCss] = process.argv;",
                "const tools = await import(pathToFileURL(fontsTs).href);",
                "const files = tools.fontFiles();",
                "const faces = tools.fontFaces();",
                "let bytes = 0;",
                "for (const file of files) bytes += statSync(file).size;",
                'const css = readFileSync(fontsCss, "utf8");',
                'const importRe = /@import\\s+"[^"]+"/g;',
                "const imports = (css.match(importRe) ?? []).length;",
                "console.log(",
                "  JSON.stringify({",
                "    files: files.length,",
                "    bytes,",
                "    faces: faces.length,",
                "    families: [...new Set(faces.map((face) => face.family))],",
                "    cssImports: imports,",
                "  }),",
                ");",
                "",
            ]
        ),
    )
    with probe.rounds.round(label) as current:
        result = probe.node_run(
            label,
            [
                str(script),
                str(WIDGET / "tools" / "fonts.ts"),
                str(UI / "src" / "styles" / "fonts.css"),
            ],
        )
        parsed = _last_json(result.stdout) if result.code == 0 else None
        if parsed is None:
            probe.detail(label, f"종료 {result.code}, stderr 머리: {result.stderr.strip()[:300]!r}")
            return
        files = parsed.get("files")
        faces = parsed.get("faces")
        imports = parsed.get("cssImports")
        ok = (
            isinstance(files, int)
            and files > 0
            and isinstance(faces, int)
            and faces > 0
            and isinstance(imports, int)
            and imports > 0
        )
        probe.detail(label, json.dumps(parsed, ensure_ascii=False))
        if not ok:
            return
        verdict = f"woff2 {files}개, @font-face {faces}개, 원본 @import {imports}개"
        current.mark(measured=True, result=verdict)


def next_config_rounds(probe: Probe) -> None:
    app = probe.tmp / "nextapp"
    write(app / "local.ts", 'export const LOCAL: string = "local-ok";\n')
    write(
        app / "next.config.ts",
        "\n".join(
            [
                'import type { NextConfig } from "next";',
                'import { MODES } from "@agent-os/ui/contrast";',
                'import { parse } from "smol-toml";',
                'import { LOCAL } from "./local.ts";',
                "",
                'const parsed = parse("answer = 42");',
                "const config: NextConfig = {",
                "  env: {",
                '    PROBE_MODES: MODES.join(","),',
                "    PROBE_LOCAL: LOCAL,",
                '    PROBE_TOML: String(parsed["answer"]),',
                "  },",
                "};",
                "export default config;",
                "",
            ]
        ),
    )
    runner = probe.tmp / "load_next_config.mjs"
    write(
        runner,
        "\n".join(
            [
                "const dir = process.argv[2];",
                'const configModule = await import("next/dist/server/config.js");',
                "const loadConfig = configModule.default?.default ?? configModule.default;",
                'const constants = await import("next/dist/shared/lib/constants.js");',
                "const phase =",
                "  constants.PHASE_PRODUCTION_BUILD ?? constants.default?.PHASE_PRODUCTION_BUILD;",
                "const config = await loadConfig(phase, dir);",
                "console.log(",
                "  JSON.stringify({",
                "    phase,",
                "    env: config.env ?? null,",
                f'    nativeFlag: process.env["{NATIVE_FLAG}"] ?? null,',
                "  }),",
                ");",
                "",
            ]
        ),
    )
    legacy_env = {"NEXT_TELEMETRY_DISABLED": "1"}
    native_env = {"NEXT_TELEMETRY_DISABLED": "1", NATIVE_FLAG: "true"}
    expected = {"PROBE_MODES": "light,dark", "PROBE_LOCAL": "local-ok", "PROBE_TOML": "42"}
    from_cwd = {**expected, "PROBE_LOCAL": "local-from-cwd"}

    def load(label: str, cwd: Path, env: dict[str, str], unset: tuple[str, ...]) -> Run:
        return probe.node_run(
            label, [str(runner), str(app)], cwd=cwd, env=env, unset=unset, timeout=TOOL_TIMEOUT
        )

    def env_round(
        label: str, cwd: Path, env: dict[str, str], unset: tuple[str, ...], want: dict[str, str]
    ) -> None:
        with probe.rounds.round(label) as current:
            result = load(label, cwd, env, unset)
            parsed = _last_json(result.stdout) if result.code == 0 else None
            if parsed is None or parsed.get("env") != want:
                probe.detail(
                    label,
                    f"표지 없음. 종료 {result.code}, stdout 끝: {result.stdout.strip()[-300:]!r}, "
                    f"stderr 머리: {result.stderr.strip()[:500]!r}",
                )
                return
            flag = parsed.get("nativeFlag")
            local = want["PROBE_LOCAL"]
            verdict = f"env 세 값 그대로(PROBE_LOCAL={local}), 끝난 뒤 {NATIVE_FLAG}={flag!r}"
            probe.detail(label, f"{verdict} ({result.seconds:.1f}초)")
            current.mark(measured=True, result=verdict)

    # 양성: `next build` 를 앱 폴더에서 치는 모양. 작업 디렉터리가 설정 파일의 폴더다.
    env_round("next_config_legacy", app, legacy_env, (NATIVE_FLAG,), expected)
    # 갈래 1: 작업 디렉터리를 설정 파일의 폴더 밖으로 옮기면 `./local.ts` 를 찾지 못한다.
    label = "next_config_legacy_other_cwd_missing"
    with probe.rounds.round(label) as current:
        result = load(label, probe.tmp, legacy_env, (NATIVE_FLAG,))
        marker = "Cannot find module './local.ts'"
        if result.code == 0 or marker not in result.stderr:
            probe.detail(
                label,
                f"표지 없음. 종료 {result.code}, stderr 머리: {result.stderr.strip()[:500]!r}",
            )
        else:
            verdict = f"거부 MODULE_NOT_FOUND ({marker})"
            probe.detail(label, verdict)
            current.mark(measured=True, result=verdict)
    # 갈래 2: 그 작업 디렉터리에 다른 값을 내는 `local.ts` 를 두면 그것을 읽는다(독스트링 5).
    write(probe.tmp / "local.ts", 'export const LOCAL: string = "local-from-cwd";\n')
    env_round("next_config_legacy_other_cwd_decoy", probe.tmp, legacy_env, (NATIVE_FLAG,), from_cwd)
    # 대조: node 네이티브 길은 작업 디렉터리와 무관하게 설정 파일 곁의 것을 읽는다.
    env_round("next_config_native_other_cwd", probe.tmp, native_env, (), expected)


def page_script_rounds(probe: Probe) -> None:
    """브라우저가 받을 페이지 스크립트를 `.ts` 로 두고 서버가 시작 때 `node:module` 의
    `stripTypeScriptTypes` 로 타입만 벗겨 내줄 수 있는지(독스트링 6)."""
    tmp = probe.tmp
    page = tmp / "page_script.ts"
    write(
        page,
        "\n".join(
            [
                "type Site = { name: string; heading: string };",
                'const sites: Site[] = [{ name: "calc-demo", heading: "계산 도우미" }];',
                "function label(site: Site): string {",
                "  return `${site.heading} (${site.name})`;",
                "}",
                "const first: Site | undefined = sites[0];",
                'globalThis.__probeLabel = first === undefined ? "" : label(first);',
                "",
            ]
        ),
    )
    runner = tmp / "entry_strip_api.ts"
    write(
        runner,
        "\n".join(
            [
                'import { readFileSync } from "node:fs";',
                'import { stripTypeScriptTypes } from "node:module";',
                'import { runInThisContext } from "node:vm";',
                'const source: string = readFileSync(process.argv[2], "utf-8");',
                'const stripped: string = stripTypeScriptTypes(source, { mode: "strip" });',
                "runInThisContext(stripped);",
                "console.log(",
                "  JSON.stringify({",
                "    annotationsLeft: /: (string|Site)\\b|type Site/.test(stripped),",
                '    sameLineCount: stripped.split("\\n").length === source.split("\\n").length,',
                "    label: globalThis.__probeLabel,",
                "  }),",
                ");",
                "",
            ]
        ),
    )

    def expect_stripped(parsed: dict[str, object]) -> str | None:
        if parsed.get("label") != "계산 도우미 (calc-demo)" or parsed.get("annotationsLeft"):
            return None
        lines = "줄 수 같음" if parsed.get("sameLineCount") else "줄 수 다름"
        return f"벗겨져 돌았음, 주석 잔존 없음, {lines}"

    with probe.rounds.round("page_script_strip") as current:
        result = probe.node_run("page_script_strip", [str(runner), str(page)])
        parsed = _last_json(result.stdout) if result.code == 0 else None
        verdict = expect_stripped(parsed) if parsed is not None else None
        if verdict is None:
            probe.detail(
                "page_script_strip",
                f"종료 {result.code}, stderr 머리: {result.stderr.strip()[:300]!r}",
            )
        else:
            probe.detail("page_script_strip", f"{verdict} ({result.seconds:.1f}초)")
            current.mark(measured=True, result=verdict)

    # 갈래: 지울 수 없는 문법(enum)은 `strip` 모드가 거절하는지. 거절하면 기준 tsconfig 의
    # `erasableSyntaxOnly` 가 막는 문법과 같은 선이고, 받아들이면 그 선이 다르다.
    enum_runner = tmp / "entry_strip_enum.ts"
    write(
        enum_runner,
        "\n".join(
            [
                'import { stripTypeScriptTypes } from "node:module";',
                "let outcome: { code: string } | { stripped: string };",
                "try {",
                '  const source: string = "enum Mode { Light }";',
                '  outcome = { stripped: stripTypeScriptTypes(source, { mode: "strip" }) };',
                "} catch (error: unknown) {",
                "  const code: unknown = (error as { code?: unknown }).code;",
                '  outcome = { code: typeof code === "string" ? code : String(error) };',
                "}",
                "console.log(JSON.stringify(outcome));",
                "",
            ]
        ),
    )

    def expect_enum(parsed: dict[str, object]) -> str | None:
        code = parsed.get("code")
        if code == "ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX":
            return f"거부 {code}"
        stripped = parsed.get("stripped")
        if isinstance(stripped, str):
            return f"받아들임(산출 {stripped.strip()!r})"
        return None

    entry_json_round(probe, "page_script_strip_enum", enum_runner, expect_enum)


GROUPS: dict[str, Callable[[Probe], None]] = {
    "strip": strip_rounds,
    "tsc": tsc_rounds,
    "css": theme_css_rounds,
    "fonts": fonts_rounds,
    "next": next_config_rounds,
    "pagescript": page_script_rounds,
}


def environment(node: str) -> dict[str, str]:
    version = run([node, "--version"], ROOT, timeout=30).stdout.strip()
    feature = run([node, "-p", "process.features.typescript"], ROOT, timeout=30).stdout.strip()
    widget_modules = WIDGET / "node_modules"
    return {
        "node": version,
        "process.features.typescript": feature,
        "pnpm(packageManager)": str(
            json.loads((WEB / "package.json").read_text(encoding="utf-8")).get("packageManager")
        ),
        "typescript": package_version(WEB / "node_modules" / "typescript" / "package.json"),
        "next": package_version(widget_modules / "next" / "package.json"),
        "smol-toml": package_version(widget_modules / "smol-toml" / "package.json"),
        "@tailwindcss/cli": package_version(
            UI / "node_modules" / "@tailwindcss" / "cli" / "package.json"
        ),
        "tailwindcss": package_version(UI / "node_modules" / "tailwindcss" / "package.json"),
        "platform": sys.platform,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="node 가 .ts 워크스페이스 패키지를 바로 읽는지 잰다"
    )
    parser.add_argument(
        "--group",
        action="append",
        choices=sorted(GROUPS),
        help="돌릴 묶음(여러 번). 주지 않으면 전부",
    )
    parser.add_argument(
        "--raw", type=Path, help="회차마다의 명령·종료 코드·출력 원본을 쓸 JSON 경로"
    )
    args = parser.parse_args(argv)
    node = shutil.which("node")
    if node is None:
        print("node 를 찾지 못했다", file=sys.stderr)
        return 2
    if not WIDGET.joinpath("node_modules").is_dir():
        print(
            f"{WIDGET / 'node_modules'} 가 없다. web 에서 pnpm install 을 먼저 돈다",
            file=sys.stderr,
        )
        return 2
    env = environment(node)
    print("환경: " + ", ".join(f"{key} {value}" for key, value in env.items()))
    tmp = Path(tempfile.mkdtemp(prefix=".probe-node-ts-", dir=WIDGET))
    probe = Probe(node=node, tmp=tmp)
    probe.raw["environment"] = env
    try:
        for name in args.group or list(GROUPS):
            GROUPS[name](probe)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for line in probe.details:
        print(line)
    if args.raw is not None:
        args.raw.parent.mkdir(parents=True, exist_ok=True)
        args.raw.write_text(
            json.dumps(probe.raw, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
        )
        print(f"원본: {args.raw}")
    print(probe.rounds.summary())
    return probe.rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
