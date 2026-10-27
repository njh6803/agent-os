// 사진 비교 흔들림 프로브(harness 티켓 016)가 함께 쓰는 PNG 읽기. 깊이 8, 색 유형 2(RGB)·6(RGBA), 인터레이스 없음만
// 읽고 나머지는 던진다. Playwright 의 스크린샷과 toHaveScreenshot 의 실제·정답·차이 그림이 이 꼴이다(ci_diff.mjs 가
// 세 실행의 그림 아홉을 모두 이것으로 읽었다). 필터 다섯(None, Sub, Up, Average, Paeth)을 푼다.
import { readFileSync } from "node:fs";
import { inflateSync } from "node:zlib";

/**
 * 경로나 이미 읽은 바이트를 받는다(changed_baselines.mjs 는 `git show` 의 출력을 넘긴다).
 * @param {string | Buffer} source
 * @param {string} [label] 오류에 적을 이름. 경로를 받으면 그 경로다
 * @returns {{ width: number, height: number, rgba: Buffer }}
 */
export function readPng(source, label = typeof source === "string" ? source : "<바이트>") {
  const png = typeof source === "string" ? readFileSync(source) : source;
  const idat = [];
  let header = null;
  for (let at = 8; at < png.length; at += 12 + png.readUInt32BE(at)) {
    const size = png.readUInt32BE(at);
    const type = png.toString("ascii", at + 4, at + 8);
    if (type === "IHDR") header = png.subarray(at + 8, at + 8 + size);
    else if (type === "IDAT") idat.push(png.subarray(at + 8, at + 8 + size));
  }
  if (header === null) throw new Error(`IHDR 가 없다: ${label}`);
  const width = header.readUInt32BE(0);
  const height = header.readUInt32BE(4);
  const depth = header[8];
  const colorType = header[9];
  if (depth !== 8 || (colorType !== 2 && colorType !== 6) || header[12] !== 0) {
    throw new Error(`깊이 8·RGB(A)·인터레이스 없음이 아니다: ${label}`);
  }
  const channels = colorType === 6 ? 4 : 3;
  const stride = width * channels;
  const raw = inflateSync(Buffer.concat(idat));
  const out = Buffer.alloc(width * height * 4);
  let previous = Buffer.alloc(stride);
  for (let y = 0; y < height; y += 1) {
    const filter = raw[y * (stride + 1)];
    const line = Buffer.from(raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)));
    for (let x = 0; x < stride; x += 1) {
      const left = x >= channels ? line[x - channels] : 0;
      const up = previous[x];
      const upLeft = x >= channels ? previous[x - channels] : 0;
      let add = 0;
      if (filter === 1) add = left;
      else if (filter === 2) add = up;
      else if (filter === 3) add = (left + up) >> 1;
      else if (filter === 4) {
        const p = left + up - upLeft;
        const pa = Math.abs(p - left);
        const pb = Math.abs(p - up);
        const pc = Math.abs(p - upLeft);
        add = pa <= pb && pa <= pc ? left : pb <= pc ? up : upLeft;
      } else if (filter !== 0) throw new Error(`모르는 필터 ${filter}: ${label}`);
      line[x] = (line[x] + add) & 0xff;
    }
    for (let x = 0; x < width; x += 1) {
      for (let c = 0; c < 4; c += 1) {
        out[(y * width + x) * 4 + c] = c < channels ? line[x * channels + c] : 255;
      }
    }
    previous = line;
  }
  return { width, height, rgba: out };
}

/** 두 그림에서 RGBA 가 하나라도 다른 픽셀. 크기가 다르면 던진다. */
export function differingPixels(a, b) {
  if (a.width !== b.width || a.height !== b.height) {
    throw new Error(`크기가 다르다: ${a.width}×${a.height}, ${b.width}×${b.height}`);
  }
  const found = [];
  for (let i = 0; i < a.width * a.height; i += 1) {
    const pa = [...a.rgba.subarray(i * 4, i * 4 + 4)];
    const pb = [...b.rgba.subarray(i * 4, i * 4 + 4)];
    if (pa.some((value, c) => value !== pb[c])) {
      found.push({ x: i % a.width, y: Math.floor(i / a.width), a: pa, b: pb });
    }
  }
  return found;
}
