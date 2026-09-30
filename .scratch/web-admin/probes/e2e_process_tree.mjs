// 티켓 05: e2e 가 띄우는 두 프로세스를 `ChildProcess.kill()` 하나로 거둘 수 있는지 잰다. 결정은 하지 않고 결과만 낸다.
//   node .scratch/web-admin/probes/e2e_process_tree.mjs      (저장소 루트에서. 앱을 먼저 빌드해 둔다)
//
// e2e 는 운영체제별 명령(taskkill, 프로세스 그룹)에 기대지 않는다(티켓 05). 그래서 띄운 프로세스가 자식을 두지 않거나,
// 자식을 두더라도 부모가 죽을 때 함께 죽어야 kill() 하나로 끝난다. 재는 것은 둘이다.
//   next   시작 래퍼(tools/start.ts start)가 next CLI 를 같은 프로세스에서 부르고, next start 가 서버를 자식으로 띄우지
//          않는가(04 는 next dev 만 쟀다. next dev 는 서버를 자식으로 띄운다)
//   serve  가상 환경의 파이썬(`uv run python -c "import sys; print(sys.executable)"`)으로 띄운 serve 가 kill() 한 번에
//          포트를 놓는가. 윈도우의 가상 환경 python.exe 는 기반 인터프리터를 자식으로 띄우는 런처일 수 있다
// 자식 목록은 윈도우에서 PowerShell(Get-CimInstance), 그 밖에서 ps 로 본다. 측정용일 뿐 e2e 는 이것을 쓰지 않는다.
// 판정은 kill() 뒤 포트에 새 연결이 거절되는가와, 처음에 본 자식이 모두 사라졌는가다.
// 포트 3931(관리 화면)이 비어 있어야 한다. serve 는 --port 0 으로 띄워 기동 줄에서 포트를 읽는다. 약 20초.
// 종료 코드: 둘 다 kill() 하나로 거둬지면 0, 아니면 1.
// 2026-09-30 결과(윈도우, Node 24.19.0, Next 16.3.6, Python 3.12 uv 가상 환경): 둘 다 거둬졌다. 종료 0.
//   next start(래퍼)의 자식은 conhost.exe 하나다. 서버를 자식으로 띄우지 않는다.
//   serve 는 .venv\Scripts\python.exe 가 기반 인터프리터 python.exe 를 자식으로 띄웠고, 런처를 kill() 하자 그 자식도
//   함께 죽었다. 두 포트 모두 kill() 뒤 연결이 거절됐고 남은 프로세스가 없었다.

import { spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdtempSync, rmSync } from "node:fs";
import { connect } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = process.cwd();
const APP = join(ROOT, "web", "apps", "admin");
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function children(pid) {
  if (process.platform === "win32") {
    const out = spawnSync(
      "powershell",
      [
        "-NoProfile",
        "-Command",
        `Get-CimInstance Win32_Process -Filter "ParentProcessId=${pid}" | ForEach-Object { "$($_.ProcessId) $($_.Name)" }`,
      ],
      { encoding: "utf-8" },
    );
    return out.stdout.split(/\r?\n/).filter(Boolean);
  }
  const out = spawnSync("ps", ["-o", "pid=,comm=", "--ppid", String(pid)], { encoding: "utf-8" });
  return out.stdout.split("\n").map((line) => line.trim()).filter(Boolean);
}

function alive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function refused(port) {
  return new Promise((resolve) => {
    const socket = connect({ host: "127.0.0.1", port });
    socket.once("connect", () => {
      socket.destroy();
      resolve(false);
    });
    socket.once("error", () => resolve(true));
  });
}

async function until(predicate, label) {
  for (let i = 0; i < 120; i += 1) {
    const value = await predicate();
    if (value) return value;
    await sleep(250);
  }
  throw new Error(`${label} 에 닿지 못했다`);
}

async function measure(label, child, port) {
  const tree = children(child.pid);
  const grandchildren = tree.flatMap((line) => children(Number(line.split(" ")[0])));
  child.kill();
  await new Promise((resolve) => child.once("exit", resolve));
  await sleep(1000);
  const portFreed = await refused(port);
  const survivors = [...tree, ...grandchildren].filter((line) => alive(Number(line.split(" ")[0])));
  const ok = portFreed && survivors.length === 0;
  console.log(
    `${ok ? "거둬짐" : "남음  "}  ${label}: 자식 [${tree.join(", ")}] 손자 [${grandchildren.join(", ")}]` +
      ` kill() 뒤 포트 ${portFreed ? "닫힘" : "열림"}, 남은 프로세스 [${survivors.join(", ")}]`,
  );
  return ok;
}

const results = [];

// next start(래퍼)
{
  const port = 3931;
  const child = spawn(process.execPath, [join(APP, "tools", "start.ts"), "start", "--port", String(port)], {
    cwd: APP,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
    stdio: "ignore",
    windowsHide: true,
  });
  await until(async () => !(await refused(port)), "관리 화면");
  results.push(await measure("next start(래퍼)", child, port));
}

// serve(가상 환경의 파이썬)
{
  const python = spawnSync("uv", ["run", "python", "-c", "import sys; print(sys.executable)"], {
    cwd: ROOT,
    encoding: "utf-8",
  }).stdout.trim();
  const work = mkdtempSync(join(tmpdir(), "e2e-tree-"));
  const child = spawn(python, ["-m", "agent_os.main", "serve", "--port", "0", "--traces", join(work, "t")], {
    cwd: work,
    env: {
      ...process.env,
      PYTHONUTF8: "1",
      AGENT_OS_ADMIN_TOKEN: randomBytes(16).toString("hex"),
      AGENT_OS_CHANNEL_TOKEN: randomBytes(16).toString("hex"),
    },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  let log = "";
  child.stdout.on("data", (chunk) => (log += chunk));
  child.stderr.on("data", (chunk) => (log += chunk));
  const port = await until(() => {
    const found = /Uvicorn running on http:\/\/127\.0\.0\.1:(\d+)/.exec(log);
    return found === null ? null : Number(found[1]);
  }, "serve 의 기동 줄");
  console.log(`serve 의 인터프리터: ${python}`);
  results.push(await measure("serve(가상 환경 python)", child, port));
  rmSync(work, { recursive: true, force: true });
}

process.exit(results.every(Boolean) ? 0 : 1);
