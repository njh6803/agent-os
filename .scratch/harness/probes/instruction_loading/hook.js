// InstructionsLoaded 훅. 받은 페이로드를 첫 인자의 파일에 한 줄씩 덧붙인다.
const fs = require("fs");
let data = "";
process.stdin.on("data", (chunk) => (data += chunk));
process.stdin.on("end", () => {
  fs.appendFileSync(process.argv[2], data.replace(/\r?\n/g, " ").trim() + "\n");
});
