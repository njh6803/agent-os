// 훅 로그를 "파일 | 종류 | load_reason | cwd | 계기·부모·glob" 한 줄씩으로 줄인다. 경로는 탐침 트리 기준으로 줄인다.
const lines = require("fs").readFileSync(process.argv[2], "utf8").split("\n").filter(Boolean);
const short = (p) => {
  const at = p ? p.lastIndexOf("memprobe") : -1;
  return at < 0 ? p || "" : p.slice(at + "memprobe".length) || ".";
};
for (const line of lines) {
  const o = JSON.parse(line);
  if (o.marker) {
    console.log("== " + o.marker);
    continue;
  }
  const extra = [];
  if (o.trigger_file_path) extra.push("trigger=" + short(o.trigger_file_path));
  if (o.parent_file_path) extra.push("parent=" + short(o.parent_file_path));
  if (o.globs) extra.push("globs=" + JSON.stringify(o.globs));
  console.log([short(o.file_path), o.memory_type, o.load_reason, "cwd=" + short(o.cwd), extra.join(" ")].join(" | "));
}
