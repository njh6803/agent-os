// design-system 시각 회귀 프로브: 판을 고정한 Playwright Linux Docker 이미지에서 따로 두 번 찍은 사진이 픽셀까지 같은지,
// 그리고 같은 표본을 Windows 호스트의 chromium 으로 찍은 사진과 얼마나 다른지 잰다. 저장소 루트에서 돈다.
//   node .scratch/design-system/probes/visual_docker/run.mjs <pretendard 패키지 폴더> --work <작업 폴더>
//        [--pull] [--image mcr.microsoft.com/playwright:v1.63.0-noble]
// <pretendard 패키지 폴더>는 font_shadow 와 같은 자리(`npm pack pretendard@1.3.9` 를 저장소 밖에서 푼 `package/`)다.
// <작업 폴더>는 저장소 밖(스크래치)에 둔다. 사진과 결과 JSON 은 거기에만 쓰고 저장소에는 넣지 않는다.
// Playwright 는 저장소 web/apps/admin 에 깔린 @playwright/test 와 그 의존(playwright, playwright-core)을 작업 폴더의
// node_modules 로 실체 복사해(pnpm 링크를 풀어) 컨테이너와 호스트가 같은 파일을 쓴다(`pnpm -C web install` 뒤).
// --pull 이면 `docker pull` 을 재고(이미지가 이미 있으면 확인만 하므로 첫 실행에서만 받는 시간이다), 없으면 이미지가 이미
// 있어야 한다. `docker manifest inspect` 로 층 크기를 레지스트리에 묻는다(받지 않는다).
//
// 하는 일
//   준비   작업 폴더에 probe/(playwright.config.mjs, capture.spec.mjs), site/(index.html, Pretendard Regular·Bold woff2),
//          node_modules/ 를 새로 만든다. out/ 은 지우고 다시 만든다
//   이미지 pull 시간·층마다 Already exists / Pull complete, 매니페스트의 압축 층 크기 합, `docker image inspect` 의 Size
//   실행   A: 컨테이너, 정답(toHaveScreenshot baseline)을 out/A/baseline 에 쓴다
//          B: 새 컨테이너, A 의 정답과 toHaveScreenshot 으로 비교한다
//          H1, H2: Windows 호스트(같은 node_modules, %LOCALAPPDATA%\ms-playwright 의 빌드), A 의 정답과 비교한다
//          컨테이너는 `docker run --rm --init --ipc=host --network none` 이고 작업 폴더를 /work 에 bind 한다.
//          실행마다 벽시계 시간을 잰다
//   비교   쌍(A·B, A·H1, H1·H2)마다 구성표(light, dark)·사진(page, 영역 일곱)마다 PNG 를 디코드해 RGBA 가 하나라도 다른
//          픽셀을 센다. 크기가 다르면 겹친 자리의 다른 픽셀 + 겹치지 않은 자리 전부를 다르다고 센다(비율의 분모는 큰 쪽
//          너비 × 큰 쪽 높이). 다른 픽셀을 글자(양쪽의 글자 사각형을 1px 넓힌 안)·영역(도형)·배경으로 가르고, 채널 차이
//          최댓값의 분포(1–2, 3–8, 9–32, 33 이상)와 다른 자리의 외곽 상자를 낸다. 다른 픽셀이 있으면 차이 그림을
//          out/diff/<쌍>/<구성표>/<사진>.png 로 쓴다. 디코더는 이 파일에 손으로 짰고, 사진마다 playwright-core 가 싣고
//          있는 pngjs 로도 읽어 RGBA 가 같은지(decoderAgrees) 대조한다. 파일 바이트가 같은지(bytesEqual)도 따로 본다.
//          제목·버튼의 글자열 폭과 요소 폭(capture.spec.mjs 의 WIDTH_TARGETS)을 쌍의 두 실행에서 나란히 둔다
//   toHaveScreenshot  B, H1, H2 의 run-<구성표>.json 에 든 세 설정의 통과·실패를 센다
// 결과는 <작업 폴더>/result.json 이고 stdout 에는 요약을 낸다.

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { release } from "node:os";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { crc32, deflateSync, inflateSync } from "node:zlib";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, "..", "..", "..", "..");
// capture.spec.mjs 의 REGIONS 와 같다(그 파일은 Playwright 러너가 불러야 해서 import 하지 않는다).
const REGIONS = ["text-web", "text-system", "box-border", "box-shadow", "box-ring", "box-gradient", "buttons"];
const SHOTS = ["page", ...REGIONS];
const SCHEMES = ["light", "dark"];
const PAIRS = [
  ["A", "B"],
  ["A", "H1"],
  ["H1", "H2"],
];

const args = process.argv.slice(2);
const option = (name) => {
  const i = args.indexOf(name);
  return i === -1 ? null : args[i + 1];
};
const positional = args.filter((arg, i) => !arg.startsWith("--") && !["--work", "--image"].includes(args[i - 1]));
const pkg = resolve(positional[0] ?? ".");
const workOption = option("--work");
const image = option("--image") ?? "mcr.microsoft.com/playwright:v1.63.0-noble";
const pull = args.includes("--pull");
if (workOption === null) {
  console.error("--work <작업 폴더> 가 필요하다(저장소 밖)");
  process.exit(2);
}
const work = resolve(workOption);
if (!relative(REPO, work).startsWith("..")) {
  console.error(`작업 폴더가 저장소 안이다: ${work}`);
  process.exit(2);
}
const fontDir = join(pkg, "dist", "web", "static", "woff2");
if (!existsSync(join(fontDir, "Pretendard-Regular.woff2"))) {
  console.error(`Pretendard 패키지 폴더가 아니다: ${pkg}`);
  process.exit(2);
}

function sh(command, commandArgs, options = {}) {
  const started = Date.now();
  const result = spawnSync(command, commandArgs, { encoding: "utf-8", maxBuffer: 64 * 1024 * 1024, ...options });
  return {
    status: result.status,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
    error: result.error === undefined ? null : String(result.error),
    ms: Date.now() - started,
  };
}
const tail = (text, count = 30) => text.split(/\r?\n/).filter((line) => line.trim() !== "").slice(-count);

// ---------- 준비 ----------
function copyPackage(from, to) {
  // pnpm 의 실체 폴더를 복사한다. 패키지 안의 node_modules(.bin 링크)는 뺀다.
  cpSync(from, to, {
    recursive: true,
    dereference: true,
    filter: (source) => !relative(from, source).split(sep).includes("node_modules"),
  });
}

function prepare() {
  for (const sub of ["probe", "site", "node_modules", "out"]) {
    rmSync(join(work, sub), { recursive: true, force: true });
  }
  mkdirSync(join(work, "probe"), { recursive: true });
  mkdirSync(join(work, "site", "fonts"), { recursive: true });
  mkdirSync(join(work, "out"), { recursive: true });
  for (const file of ["playwright.config.mjs", "capture.spec.mjs"]) {
    cpSync(join(HERE, file), join(work, "probe", file));
  }
  cpSync(join(HERE, "site", "index.html"), join(work, "site", "index.html"));
  for (const weight of ["Regular", "Bold"]) {
    cpSync(join(fontDir, `Pretendard-${weight}.woff2`), join(work, "site", "fonts", `Pretendard-${weight}.woff2`));
  }
  const admin = createRequire(join(REPO, "web", "apps", "admin", "package.json"));
  const testDir = realpathSync(dirname(admin.resolve("@playwright/test/package.json")));
  const playwrightDir = realpathSync(
    dirname(createRequire(join(testDir, "package.json")).resolve("playwright/package.json")),
  );
  const coreDir = realpathSync(
    dirname(createRequire(join(playwrightDir, "package.json")).resolve("playwright-core/package.json")),
  );
  const packages = { "@playwright/test": testDir, playwright: playwrightDir, "playwright-core": coreDir };
  const copied = {};
  for (const [name, from] of Object.entries(packages)) {
    copyPackage(from, join(work, "node_modules", ...name.split("/")));
    copied[name] = {
      from: relative(REPO, from).split(sep).join("/"),
      version: JSON.parse(readFileSync(join(from, "package.json"), "utf-8")).version,
    };
  }
  const nativeFiles = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(path);
      } else if (entry.name.endsWith(".node")) {
        nativeFiles.push(relative(work, path));
      }
    }
  };
  walk(join(work, "node_modules"));
  return { packages: copied, nativeFiles };
}

// ---------- 이미지 ----------
function imageExists() {
  return sh("docker", ["image", "inspect", image]).status === 0;
}

function pullImage(manifestLayers) {
  const existedBefore = imageExists();
  const result = sh("docker", ["pull", image]);
  const layers = {};
  for (const line of `${result.stdout}\n${result.stderr}`.split(/\r?\n/)) {
    const match = /^([0-9a-f]{12}): (.+)$/.exec(line.trim());
    if (match !== null) {
      layers[match[1]] = match[2];
    }
  }
  const downloaded = (manifestLayers ?? [])
    .filter((layer) => (layers[layer.digest.slice("sha256:".length, "sha256:".length + 12)] ?? "") === "Pull complete")
    .reduce((acc, layer) => acc + layer.size, 0);
  return {
    existedBefore,
    status: result.status,
    ms: result.ms,
    layers,
    downloadedCompressedBytes: manifestLayers === null ? null : downloaded,
    outputTail: tail(`${result.stdout}\n${result.stderr}`, 4),
  };
}

function manifestInfo() {
  const result = sh("docker", ["manifest", "inspect", "-v", image]);
  if (result.status !== 0) {
    return { error: tail(result.stderr, 3).join(" ") };
  }
  const parsed = JSON.parse(result.stdout);
  const entries = Array.isArray(parsed) ? parsed : [parsed];
  const entry = entries.find(
    (candidate) =>
      candidate.Descriptor?.platform?.os === "linux" && candidate.Descriptor?.platform?.architecture === "amd64",
  );
  if (entry === undefined) {
    return { error: "linux/amd64 매니페스트가 없다", platforms: entries.map((candidate) => candidate.Descriptor?.platform) };
  }
  const manifest = entry.OCIManifest ?? entry.SchemaV2Manifest;
  const layers = manifest.layers.map((layer) => ({ digest: layer.digest, size: layer.size }));
  return {
    ref: entry.Ref,
    platforms: entries.map((candidate) => {
      const platform = candidate.Descriptor?.platform;
      return platform === undefined ? null : `${platform.os}/${platform.architecture}`;
    }),
    layers,
    compressedLayerBytes: layers.reduce((acc, layer) => acc + layer.size, 0),
    configBytes: manifest.config.size,
  };
}

function inspectImage() {
  const result = sh("docker", ["image", "inspect", image]);
  if (result.status !== 0) {
    return null;
  }
  const info = JSON.parse(result.stdout)[0];
  return {
    id: info.Id,
    repoDigests: info.RepoDigests,
    created: info.Created,
    os: info.Os,
    architecture: info.Architecture,
    sizeBytes: info.Size,
    env: info.Config?.Env ?? [],
  };
}

// ---------- 실행 ----------
function runContainer(label, mode) {
  mkdirSync(join(work, "out", label), { recursive: true });
  const result = sh("docker", [
    "run",
    "--rm",
    "--init",
    "--ipc=host",
    "--network",
    "none",
    "--mount",
    `type=bind,source=${work},target=/work`,
    "-e",
    "VISUAL_SITE=/work/site",
    "-e",
    `VISUAL_OUT=/work/out/${label}`,
    "-e",
    "VISUAL_BASELINE=/work/out/A/baseline",
    "-e",
    `VISUAL_MODE=${mode}`,
    "-w",
    "/work/probe",
    image,
    "node",
    "/work/node_modules/@playwright/test/cli.js",
    "test",
    "-c",
    "/work/probe/playwright.config.mjs",
  ]);
  return { label, where: "container", mode, status: result.status, ms: result.ms, outputTail: tail(`${result.stdout}\n${result.stderr}`) };
}

function runHost(label, mode) {
  mkdirSync(join(work, "out", label), { recursive: true });
  const result = sh(
    process.execPath,
    [join(work, "node_modules", "@playwright", "test", "cli.js"), "test", "-c", join(work, "probe", "playwright.config.mjs")],
    {
      cwd: join(work, "probe"),
      env: {
        ...process.env,
        VISUAL_SITE: join(work, "site"),
        VISUAL_OUT: join(work, "out", label),
        VISUAL_BASELINE: join(work, "out", "A", "baseline"),
        VISUAL_MODE: mode,
      },
    },
  );
  return { label, where: "host", mode, status: result.status, ms: result.ms, outputTail: tail(`${result.stdout}\n${result.stderr}`) };
}

// ---------- PNG ----------
const SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) {
    return a;
  }
  return pb <= pc ? b : c;
}

// 8비트, 인터레이스 없음, 색 형식 2(RGB)·6(RGBA)만 읽는다. 다른 형식이면 멈춘다.
function decodePng(buffer) {
  if (!buffer.subarray(0, 8).equals(SIGNATURE)) {
    throw new Error("PNG 서명이 아니다");
  }
  let pos = 8;
  let header = null;
  const idat = [];
  const chunks = [];
  while (pos < buffer.length) {
    const length = buffer.readUInt32BE(pos);
    const type = buffer.toString("latin1", pos + 4, pos + 8);
    const data = buffer.subarray(pos + 8, pos + 8 + length);
    chunks.push(type);
    if (type === "IHDR") {
      header = {
        width: data.readUInt32BE(0),
        height: data.readUInt32BE(4),
        bitDepth: data[8],
        colorType: data[9],
        interlace: data[12],
      };
    } else if (type === "IDAT") {
      idat.push(data);
    } else if (type === "IEND") {
      break;
    }
    pos += 12 + length;
  }
  if (header === null || header.bitDepth !== 8 || header.interlace !== 0 || ![2, 6].includes(header.colorType)) {
    throw new Error(`읽지 않는 PNG 형식: ${JSON.stringify(header)}`);
  }
  const { width, height } = header;
  const channels = header.colorType === 6 ? 4 : 3;
  const stride = width * channels;
  const raw = inflateSync(Buffer.concat(idat));
  const rgba = Buffer.alloc(width * height * 4);
  let previous = Buffer.alloc(stride);
  for (let y = 0; y < height; y += 1) {
    const start = y * (stride + 1);
    const filter = raw[start];
    const line = Buffer.from(raw.subarray(start + 1, start + 1 + stride));
    for (let x = 0; x < stride; x += 1) {
      const a = x >= channels ? line[x - channels] : 0;
      const b = previous[x];
      const c = x >= channels ? previous[x - channels] : 0;
      let add;
      if (filter === 0) {
        add = 0;
      } else if (filter === 1) {
        add = a;
      } else if (filter === 2) {
        add = b;
      } else if (filter === 3) {
        add = (a + b) >> 1;
      } else if (filter === 4) {
        add = paeth(a, b, c);
      } else {
        throw new Error(`알 수 없는 PNG 필터 ${String(filter)}`);
      }
      line[x] = (line[x] + add) & 0xff;
    }
    for (let x = 0; x < width; x += 1) {
      const target = (y * width + x) * 4;
      rgba[target] = line[x * channels];
      rgba[target + 1] = line[x * channels + 1];
      rgba[target + 2] = line[x * channels + 2];
      rgba[target + 3] = channels === 4 ? line[x * channels + 3] : 255;
    }
    previous = line;
  }
  return { width, height, rgba, colorType: header.colorType, chunks: [...new Set(chunks)] };
}

function encodePng(width, height, rgba) {
  const chunk = (type, data) => {
    const length = Buffer.alloc(4);
    length.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type, "latin1"), data]);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(body));
    return Buffer.concat([length, body, crc]);
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = 6;
  const raw = Buffer.alloc((width * 4 + 1) * height);
  for (let y = 0; y < height; y += 1) {
    rgba.copy(raw, y * (width * 4 + 1) + 1, y * width * 4, (y + 1) * width * 4);
  }
  return Buffer.concat([SIGNATURE, chunk("IHDR", header), chunk("IDAT", deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
}

// ---------- 비교 ----------
const sha256 = (buffer) => createHash("sha256").update(buffer).digest("hex");
// 위 디코더를 playwright-core 가 싣고 있는 pngjs(utilsBundle 의 PNG)와 사진마다 대조한다. 둘의 RGBA 가 하나라도 다르면
// 그 사진의 decoderAgrees 가 false 다.
let pngjs = null;
function pngjsRead(buffer) {
  pngjs ??= createRequire(join(work, "node_modules", "playwright-core", "package.json"))(
    "playwright-core/lib/utilsBundle",
  ).PNG;
  return pngjs.sync.read(buffer);
}
function decoderAgrees(buffer, decoded) {
  const other = pngjsRead(buffer);
  return other.width === decoded.width && other.height === decoded.height && Buffer.compare(other.data, decoded.rgba) === 0;
}

// 실패한 실행은 결과 파일을 남기지 않는다. 그 실행은 null 로 두고 뒤의 비교가 건너뛰어, result.json 은 언제나 쓰인다.
function readRun(label, scheme) {
  const path = join(work, "out", label, `run-${scheme}.json`);
  return existsSync(path) ? JSON.parse(readFileSync(path, "utf-8")) : null;
}

// 사진 좌표계로 옮긴 글자 사각형(1px 넓힘)과 영역 상자
function layout(run, shot) {
  const origin = shot === "page" ? { x: 0, y: 0 } : run.geometry.regions[shot];
  const move = (rect, grow) => ({
    x0: Math.floor(rect.x - origin.x) - grow,
    y0: Math.floor(rect.y - origin.y) - grow,
    x1: Math.ceil(rect.x - origin.x + rect.width) + grow,
    y1: Math.ceil(rect.y - origin.y + rect.height) + grow,
  });
  const regions =
    shot === "page"
      ? Object.entries(run.geometry.regions).map(([name, rect]) => ({ name, ...move(rect, 0) }))
      : [{ name: shot, x0: -1e9, y0: -1e9, x1: 1e9, y1: 1e9 }];
  return { text: run.geometry.textRects.map((rect) => move(rect, 1)), regions };
}

const inside = (rect, x, y) => x >= rect.x0 && x < rect.x1 && y >= rect.y0 && y < rect.y1;

function compareShot(pair, scheme, shot, runs) {
  const [left, right] = pair;
  const leftPath = join(work, "out", left, scheme, `${shot}.png`);
  const rightPath = join(work, "out", right, scheme, `${shot}.png`);
  const leftBytes = readFileSync(leftPath);
  const rightBytes = readFileSync(rightPath);
  const a = decodePng(leftBytes);
  const b = decodePng(rightBytes);
  const width = Math.max(a.width, b.width);
  const height = Math.max(a.height, b.height);
  const layouts = [layout(runs[left], shot), layout(runs[right], shot)];
  const where = { text: 0, background: 0 };
  const shapes = {};
  const delta = { "1-2": 0, "3-8": 0, "9-32": 0, "33+": 0, size: 0 };
  let diff = 0;
  let box = null;
  const picture = Buffer.alloc(width * height * 4);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const inA = x < a.width && y < a.height;
      const inB = x < b.width && y < b.height;
      const target = (y * width + x) * 4;
      let maxDelta = 0;
      if (inA && inB) {
        const ia = (y * a.width + x) * 4;
        const ib = (y * b.width + x) * 4;
        for (let channel = 0; channel < 4; channel += 1) {
          maxDelta = Math.max(maxDelta, Math.abs(a.rgba[ia + channel] - b.rgba[ib + channel]));
        }
        const gray = Math.round(0.299 * a.rgba[ia] + 0.587 * a.rgba[ia + 1] + 0.114 * a.rgba[ia + 2]);
        const faded = 255 - Math.round((255 - gray) * 0.3);
        picture[target] = faded;
        picture[target + 1] = faded;
        picture[target + 2] = faded;
        picture[target + 3] = 255;
      }
      const sizeOnly = !(inA && inB);
      if (maxDelta === 0 && !sizeOnly) {
        continue;
      }
      diff += 1;
      box =
        box === null
          ? { x0: x, y0: y, x1: x, y1: y }
          : { x0: Math.min(box.x0, x), y0: Math.min(box.y0, y), x1: Math.max(box.x1, x), y1: Math.max(box.y1, y) };
      picture[target] = 255;
      picture[target + 1] = sizeOnly ? 160 : 0;
      picture[target + 2] = 0;
      picture[target + 3] = 255;
      if (sizeOnly) {
        delta.size += 1;
      } else if (maxDelta <= 2) {
        delta["1-2"] += 1;
      } else if (maxDelta <= 8) {
        delta["3-8"] += 1;
      } else if (maxDelta <= 32) {
        delta["9-32"] += 1;
      } else {
        delta["33+"] += 1;
      }
      if (layouts.some((item) => item.text.some((rect) => inside(rect, x, y)))) {
        where.text += 1;
        continue;
      }
      const region = layouts[0].regions.find((rect) => inside(rect, x, y)) ?? layouts[1].regions.find((rect) => inside(rect, x, y));
      if (region === undefined) {
        where.background += 1;
      } else {
        shapes[region.name] = (shapes[region.name] ?? 0) + 1;
      }
    }
  }
  if (diff > 0) {
    const dir = join(work, "out", "diff", `${left}-${right}`, scheme);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, `${shot}.png`), encodePng(width, height, picture));
  }
  return {
    shot,
    sizes: [`${String(a.width)}x${String(a.height)}`, `${String(b.width)}x${String(b.height)}`],
    pngColorTypes: [a.colorType, b.colorType],
    decoderAgrees: decoderAgrees(leftBytes, a) && decoderAgrees(rightBytes, b),
    bytesEqual: sha256(leftBytes) === sha256(rightBytes),
    diffPixels: diff,
    totalPixels: width * height,
    ratio: diff / (width * height),
    where: { ...where, shapes },
    maxChannelDelta: delta,
    diffBox: box,
  };
}

// ---------- 실행 ----------
const startedAt = new Date().toISOString();
const prepared = prepare();
const manifest = manifestInfo();
const pulled = pull ? pullImage(manifest.layers ?? null) : null;
if (pulled !== null) {
  // 뒤가 실패해도 받은 시간이 남게 바로 낸다(이미지가 생기면 다음 --pull 은 확인만 한다).
  console.log(`pull ${JSON.stringify(pulled)}`);
}
if (!imageExists()) {
  console.error(`이미지가 없다: ${image} (--pull 을 준다)`);
  process.exit(2);
}
const inspected = inspectImage();

const runs = [runContainer("A", "baseline"), runContainer("B", "compare"), runHost("H1", "compare"), runHost("H2", "compare")];
for (const run of runs) {
  console.log(`== ${run.label} ${run.where} ${run.mode} status=${String(run.status)} ${String(run.ms)}ms`);
  if (run.status !== 0) {
    console.log(run.outputTail.join("\n"));
  }
}

const facts = {};
for (const scheme of SCHEMES) {
  facts[scheme] = {};
  for (const run of runs) {
    facts[scheme][run.label] = readRun(run.label, scheme);
  }
}

// 같은 요소의 글자열 폭·요소 폭을 쌍의 두 실행에서 나란히 둔다(차이 = 오른쪽 - 왼쪽)
function compareWidths(pair, scheme) {
  const [left, right] = pair.map((label) => facts[scheme][label].geometry.widths);
  return Object.fromEntries(
    Object.keys(left).map((selector) => [
      selector,
      {
        text: [left[selector].text, right[selector].text],
        textDelta: Math.round((right[selector].text - left[selector].text) * 100) / 100,
        box: [left[selector].box, right[selector].box],
        boxDelta: Math.round((right[selector].box - left[selector].box) * 100) / 100,
      },
    ]),
  );
}

const comparisons = {};
for (const pair of PAIRS) {
  const name = pair.join("-");
  comparisons[name] = {};
  for (const scheme of SCHEMES) {
    const missing = pair.filter((label) => facts[scheme][label] === null);
    comparisons[name][scheme] =
      missing.length > 0
        ? { skipped: `실행 결과 없음: ${missing.join(", ")}` }
        : {
            widths: compareWidths(pair, scheme),
            shots: SHOTS.map((shot) => compareShot(pair, scheme, shot, facts[scheme])),
          };
  }
}

const toHaveScreenshot = {};
for (const run of runs.filter((item) => item.mode === "compare")) {
  toHaveScreenshot[run.label] = {};
  for (const scheme of SCHEMES) {
    for (const check of facts[scheme][run.label]?.checks ?? []) {
      const bucket = (toHaveScreenshot[run.label][check.variant] ??= { pass: 0, fail: 0, failures: [] });
      if (check.pass) {
        bucket.pass += 1;
      } else {
        bucket.fail += 1;
        bucket.failures.push(`${check.name}: ${check.message}`);
      }
    }
  }
}

// run-*.json 에서 판정에 쓰는 사실만 옮긴다(글자 사각형 같은 큰 재료는 out/ 의 원본에 있다)
const runFacts = Object.fromEntries(
  runs.map((run) => {
    const any = SCHEMES.map((scheme) => facts[scheme][run.label]).find((item) => item !== null);
    if (any === undefined) {
      return [run.label, { ...run, result: "없음" }];
    }
    const per = (pick) => Object.fromEntries(SCHEMES.map((scheme) => [scheme, facts[scheme][run.label] === null ? null : pick(facts[scheme][run.label])]));
    return [
      run.label,
      {
        ...run,
        platform: any.platform,
        node: any.node,
        packages: any.packages,
        browser: any.browser,
        executablePath: any.executablePath,
        browsersPath: any.browsersPath,
        linux: any.linux,
        documentSize: per((item) => item.geometry.documentSize),
        focus: per((item) => item.focus),
        external: SCHEMES.flatMap((scheme) => facts[scheme][run.label]?.external ?? []),
        platformFonts: per((item) => item.platformFonts),
        timing: per((item) => item.timing),
      },
    ];
  }),
);

const result = {
  measuredAt: startedAt,
  orchestrator: { node: process.version, os: `${process.platform} ${release()}` },
  image,
  manifest: { ...manifest, layers: undefined, layerCount: manifest.layers?.length ?? null },
  pull: pulled,
  imageInspect: inspected,
  prepared,
  runs: runFacts,
  comparisons,
  toHaveScreenshot,
};
writeFileSync(join(work, "result.json"), `${JSON.stringify(result, null, 2)}\n`);

// ---------- 요약 ----------
console.log(`image ${image} id=${inspected.id} size=${String(inspected.sizeBytes)} compressed=${String(manifest.compressedLayerBytes)}`);
if (pulled !== null) {
  console.log(
    `pull existedBefore=${String(pulled.existedBefore)} status=${String(pulled.status)} ${String(pulled.ms)}ms downloaded=${String(pulled.downloadedCompressedBytes)} layers=${JSON.stringify(pulled.layers)}`,
  );
}
console.log(`packages ${JSON.stringify(prepared.packages)} native=${String(prepared.nativeFiles.length)}`);
for (const [label, run] of Object.entries(runFacts)) {
  if (run.result === "없음") {
    console.log(`${label} 결과 없음 status=${String(run.status)}`);
    continue;
  }
  console.log(`${label} ${run.browser.product} ${run.platform} node=${run.node} exe=${run.executablePath}`);
  console.log(`  fonts ${JSON.stringify(run.platformFonts.light)}`);
  console.log(`  size ${JSON.stringify(run.documentSize)} focus ${JSON.stringify(run.focus.light)} external=${String(run.external.length)}`);
}
for (const [name, byScheme] of Object.entries(comparisons)) {
  for (const [scheme, compared] of Object.entries(byScheme)) {
    if ("skipped" in compared) {
      console.log(`${name} ${scheme} 건너뜀 (${compared.skipped})`);
      continue;
    }
    const { widths, shots } = compared;
    const moved = Object.entries(widths).filter(([, item]) => item.textDelta !== 0 || item.boxDelta !== 0);
    console.log(
      `${name} ${scheme} widths ${moved.length === 0 ? "같다" : moved.map(([selector, item]) => `${selector} text ${item.text.join("→")} box ${item.box.join("→")}`).join("; ")}`,
    );
    for (const item of shots) {
      console.log(
        `${name} ${scheme} ${item.shot} ${item.sizes.join("/")} decoderAgrees=${String(item.decoderAgrees)} bytesEqual=${String(item.bytesEqual)} diff=${String(item.diffPixels)}/${String(item.totalPixels)} (${(item.ratio * 100).toFixed(3)}%) where=${JSON.stringify(item.where)} delta=${JSON.stringify(item.maxChannelDelta)}`,
      );
    }
  }
}
for (const [label, variants] of Object.entries(toHaveScreenshot)) {
  for (const [variant, bucket] of Object.entries(variants)) {
    console.log(`toHaveScreenshot ${label} ${variant} pass=${String(bucket.pass)} fail=${String(bucket.fail)}`);
    for (const failure of bucket.failures.slice(0, 3)) {
      console.log(`  ${failure}`);
    }
  }
}
