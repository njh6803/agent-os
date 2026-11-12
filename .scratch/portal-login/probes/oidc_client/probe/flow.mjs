// 실행 프로브. 후보마다 OIDC 인가 코드 흐름 한 바퀴를 `apps/portal/testing/round.ts` 로 돌린다. 회차마다 node 프로세스
// 하나이고, node 가 `.ts` 를 타입만 벗겨 바로 돌린다(빌드 없음).
//
// 돌리기: node probe/flow.mjs [--group <묶음>]...   (묶음: good, fault, callback, provider, insecure, transport, tls)
// 산출물: out/flow/summary.json, out/flow/raw.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 묶음
//   good       고장 없는 흐름. 후보 변형 여섯 x 가짜 서버 ㄱ(직접 만든 것). `http://127.0.0.1` 발급자, http 허용을 켠다.
//   fault      가짜 서버 ㄱ이 ID 토큰에 고장 하나를 심는다(여덟 가지). 변형 여섯이 그 토큰을 받고 거부하는지 본다.
//   callback   돌아온 요청의 주소를 바꾼다(남의 state, error 응답). 변형 셋.
//   provider   가짜 서버 ㄴ(oidc-provider)으로 고장 없는 흐름. 변형 셋.
//   insecure   http 허용을 끈 채 `http://127.0.0.1` 발급자. 변형 셋.
//   transport  라이브러리의 HTTP 를 `node:http` 의 `request` 로 바꿔 끼운다(customFetch). 변형 셋.
//   tls        사설 인증 기관이 낸 인증서로 `https://127.0.0.1` 발급자. `NODE_EXTRA_CA_CERTS` 를 준 것과 안 준 것.
//              openssl 로 인증서를 out/tls/ 에 만든다. openssl 이 없으면 이 묶음의 회차는 모두 측정이 아니다.
//
// 변형: 가-기본(openid-client 기본), 가-서명(enableNonRepudiationChecks), 나-기본(oauth4webapi 만, 서명 검증을 부르지
//   않는다), 나-자체서명(validateApplicationLevelSignature), 나-jose(jose 의 jwtVerify), 다(직접 구현).
//
// 측정이 아닌 회차(.claude/rules/probes.md). 종료 코드나 "거부됐다"만으로 맺지 않는다. 회차마다 재려는 상황이 났다는
// 표지를 가짜 서버의 기록(`idpLog`)과 전역 `fetch` 를 센 수에서 본다.
//   good·provider  서버가 인가 요청을 PKCE·state·nonce 와 함께 한 번 받았고, 토큰 끝점이 code_verifier 를 맞춰 봤다.
//                  결과(받아들임과 `sub` 가 서버가 정한 무작위 계정과 같은지)는 따로 적는다.
//   fault          서버가 고장을 심은 토큰을 실제로 한 번 내줬다(`faultyTokens` 1). 그래야 그 뒤의 거부나 받아들임이
//                  그 고장에 대한 것이다. 고장마다 적어도 한 변형이 거부해야 그 고장이 실제로 틀린 토큰이라는
//                  양성 대조가 선다. 어느 변형도 거부하지 않은 고장이 있으면 그 고장의 회차는 측정이 아니다.
//   callback       브라우저 왕복이 끝나(인가 요청 한 번) 바꾼 주소가 `finish` 에 들어갔다(거부면 단계가 finish).
//   insecure       발급자가 `http:` 이고 http 허용이 꺼진 채로 돌았다. 거부면 서버가 설정 문서 요청을 받지 않았어야
//                  라이브러리가 보내기 전에 막은 것이다(받았다면 다른 까닭의 거부라 따로 적는다).
//   transport      서버에 요청이 닿았다. 결과로 `nodeFetchCalls` 와 전역 `fetch` 호출 수를 적는다.
//   tls            발급자가 `https:` 다. 인증 기관을 준 회차의 양성 대조는 안 준 회차가 TLS 검증 오류로 거부되는 것이다.
// 회차가 JSON 한 줄을 내지 못했거나, node 가 24 가 아니거나, 전역 `fetch` 를 센 줄이 없거나, 회차의 환경(인증 기관을
// 줬는지, 시스템 인증 기관 저장소를 켜는 변수가 샜는지)이 뜻한 것과 다르면 그 회차도 측정이 아니다.
// 측정이 아닌 회차가 하나라도 있으면 종료 코드 1.
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "flow");
const TLS = join(ROOT, "out", "tls");
const ROUND = join(ROOT, "apps", "portal", "testing", "round.ts");
const COUNT_FETCH = pathToFileURL(join(ROOT, "probe", "count-fetch.mjs")).href;

const VARIANTS = {
  "가-기본": ["--client", "openid-client", "--signature", "default"],
  "가-서명": ["--client", "openid-client", "--signature", "verify"],
  "나-기본": ["--client", "oauth4webapi", "--signature", "default"],
  "나-자체서명": ["--client", "oauth4webapi", "--signature", "oauth4webapi"],
  "나-jose": ["--client", "oauth4webapi", "--signature", "jose"],
  다: ["--client", "hand", "--signature", "verify"],
};
const ALL = Object.keys(VARIANTS);
const PRIMARY = ["가-서명", "나-jose", "다"];
const TOKEN_FAULTS = [
  "bad_signature",
  "wrong_issuer",
  "wrong_audience",
  "expired",
  "wrong_nonce",
  "missing_nonce",
  "alg_none",
  "alg_hs256",
];
const TLS_ERROR_CODES = [
  "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
  "SELF_SIGNED_CERT_IN_CHAIN",
  "DEPTH_ZERO_SELF_SIGNED_CERT",
  "UNABLE_TO_GET_ISSUER_CERT_LOCALLY",
];

const requested = process.argv.flatMap((arg, at) => (arg === "--group" ? [process.argv[at + 1]] : []));
const wants = (group) => requested.length === 0 || requested.includes(group);

/** 오류와 그 원인 사슬에서 이름·코드·메시지를 한 줄로 편다. */
function flatten(error) {
  const chain = [];
  for (let at = error; at !== null && at !== undefined; at = at.cause) {
    chain.push(`${at.name}${at.code === null ? "" : `[${at.code}]`}: ${at.message}`);
  }
  return chain;
}
const codesOf = (error) => {
  const codes = [];
  for (let at = error; at !== null && at !== undefined; at = at.cause) {
    if (at.code !== null) codes.push(at.code);
  }
  return codes;
};

function run(id, group, variant, args, extraEnv = {}) {
  const env = { ...process.env, ...extraEnv };
  // 부모의 환경에 든 값이 회차에 새지 않게 한다. 인증 기관은 회차가 준 것만 쓰고, 인증 기관 저장소는 node 의 기본
  // (묶여 온 목록)으로 둔다. 재던 세션의 환경에는 `NODE_USE_SYSTEM_CA=1` 이 있었다(첫 실행들은 그 값을 물려받았다).
  if (extraEnv.NODE_EXTRA_CA_CERTS === undefined) delete env.NODE_EXTRA_CA_CERTS;
  delete env.NODE_TLS_REJECT_UNAUTHORIZED;
  delete env.NODE_OPTIONS;
  delete env.NODE_USE_SYSTEM_CA;
  const started = Date.now();
  const child = spawnSync(process.execPath, ["--import", COUNT_FETCH, ROUND, ...VARIANTS[variant], ...args], {
    cwd: ROOT,
    env,
    encoding: "utf8",
    timeout: 90_000,
    maxBuffer: 16 * 1024 * 1024,
  });
  const lines = (child.stdout ?? "").trim().split(/\r?\n/).filter((line) => line !== "");
  let result = null;
  try {
    result = JSON.parse(lines.at(-1) ?? "");
  } catch {
    result = null;
  }
  const counted = /\[count-fetch\] global fetch calls: (\d+)/.exec(child.stderr ?? "");
  const stderrLines = (child.stderr ?? "").split(/\r?\n/).filter((line) => line !== "" && !line.startsWith("[count-fetch]"));
  return {
    id,
    group,
    variant,
    args,
    caGiven: extraEnv.NODE_EXTRA_CA_CERTS !== undefined,
    exit: child.status,
    seconds: (Date.now() - started) / 1000,
    result,
    globalFetchCalls: counted === null ? null : Number(counted[1]),
    stderrLines,
  };
}

/** 회차가 낸 것에서 공통 표지를 본다. 어긋난 것의 목록을 돌려준다. */
function commonProblems(round) {
  const problems = [];
  if (round.result === null) return [`JSON 한 줄을 내지 못했다(종료 ${String(round.exit)}): ${round.stderrLines.slice(-3).join(" / ")}`];
  if (!/^v24\./.test(round.result.node)) problems.push(`node 가 24 가 아니다: ${round.result.node}`);
  if (round.globalFetchCalls === null) problems.push("전역 fetch 를 센 줄이 없다");
  if (round.result.extraCaGiven !== round.caGiven) problems.push("회차의 NODE_EXTRA_CA_CERTS 가 뜻한 것과 다르다");
  if (round.result.systemCaGiven !== false) problems.push("회차에 NODE_USE_SYSTEM_CA 가 샜다");
  return problems;
}

const reachedTokenExchange = (log) => log.authorize === 1 && log.authorizeComplete === 1 && log.token === 1 && log.pkceVerified === 1;

function judge(round) {
  const problems = commonProblems(round);
  if (round.result === null) return problems;
  const { result } = round;
  const log = result.idpLog;
  switch (round.group) {
    case "good":
    case "provider":
      if (!reachedTokenExchange(log)) problems.push(`흐름이 토큰 교환까지 가지 않았다: ${JSON.stringify(log)}`);
      break;
    case "fault":
      if (log.faultyTokens !== 1) problems.push(`고장을 심은 토큰이 나가지 않았다: ${JSON.stringify(log)}`);
      break;
    case "callback":
      if (log.authorizeComplete !== 1) problems.push("브라우저 왕복이 끝나지 않았다");
      if (result.outcome === "rejected" && result.stage !== "finish") problems.push(`finish 가 아닌 단계에서 거부됐다: ${result.stage}`);
      break;
    case "insecure":
      if (result.issuerScheme !== "http:" || result.insecure !== "deny") problems.push("http 발급자와 허용 끔의 조합이 아니다");
      break;
    case "transport":
      if (result.transport !== "node-http" || log.discovery < 1) problems.push("node-http 길로 서버에 닿지 않았다");
      break;
    case "tls":
      if (result.issuerScheme !== "https:") problems.push("발급자가 https 가 아니다");
      break;
    default:
      problems.push(`모르는 묶음: ${round.group}`);
  }
  return problems;
}

function makeCertificates() {
  rmSync(TLS, { recursive: true, force: true, maxRetries: 5 });
  mkdirSync(TLS, { recursive: true });
  // 설정을 여기서 다 적어 openssl 의 기본 설정 파일에 기대지 않는다. 첫 판은 기본 설정 위에 `-addext` 로 확장을 더해
  // 인증 기관 인증서에 basicConstraints 가 두 번 들어갔고, 인증 기관을 준 회차까지 TLS 검증 오류로 거부됐다.
  writeFileSync(
    join(TLS, "ca.cnf"),
    "[req]\ndistinguished_name=dn\nx509_extensions=v3_ca\nprompt=no\n[dn]\nCN=OIDC Probe Private CA\n[v3_ca]\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\n",
  );
  writeFileSync(join(TLS, "server.cnf"), "[req]\ndistinguished_name=dn\nprompt=no\n[dn]\nCN=127.0.0.1\n");
  writeFileSync(
    join(TLS, "server.ext"),
    "subjectAltName=IP:127.0.0.1,DNS:localhost\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nauthorityKeyIdentifier=keyid\n",
  );
  const steps = [
    ["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "ca.key", "-out", "ca.crt", "-days", "2", "-config", "ca.cnf"],
    ["req", "-newkey", "rsa:2048", "-nodes", "-keyout", "server.key", "-out", "server.csr", "-config", "server.cnf"],
    ["x509", "-req", "-in", "server.csr", "-CA", "ca.crt", "-CAkey", "ca.key", "-CAcreateserial", "-out", "server.crt", "-days", "2", "-extfile", "server.ext"],
  ];
  for (const step of steps) {
    const done = spawnSync("openssl", step, { cwd: TLS, encoding: "utf8" });
    if (done.status !== 0) return `openssl ${step[0]} 이 실패했다: ${done.error?.message ?? done.stderr}`;
  }
  // 인증서 사슬이 맞는지는 openssl 로 먼저 본다. 이것이 서야 node 회차의 TLS 오류가 사슬 탓이 아니다.
  const verified = spawnSync("openssl", ["verify", "-CAfile", "ca.crt", "server.crt"], { cwd: TLS, encoding: "utf8" });
  if (verified.status !== 0 || !/server\.crt: OK/.test(verified.stdout)) {
    return `openssl verify 가 사슬을 받지 않았다: ${verified.stdout}${verified.stderr}`;
  }
  const version = spawnSync("openssl", ["version"], { encoding: "utf8" });
  return existsSync(join(TLS, "server.crt")) ? { version: version.stdout.trim(), verify: verified.stdout.trim() } : "인증서가 생기지 않았다";
}

function main() {
  rmSync(OUT, { recursive: true, force: true, maxRetries: 5 });
  mkdirSync(OUT, { recursive: true });
  const rounds = [];
  const push = (...args) => {
    const round = run(...args);
    rounds.push(round);
    process.stderr.write(`${round.id} ${round.result?.outcome ?? "결과 없음"} (${round.seconds.toFixed(1)}초)\n`);
  };

  if (wants("good")) for (const variant of ALL) push(`good/${variant}`, "good", variant, []);
  if (wants("fault")) {
    for (const fault of TOKEN_FAULTS) for (const variant of ALL) push(`fault/${fault}/${variant}`, "fault", variant, ["--fault", fault]);
  }
  if (wants("callback")) {
    for (const callback of ["state_mismatch", "error"]) for (const variant of PRIMARY) push(`callback/${callback}/${variant}`, "callback", variant, ["--callback", callback]);
  }
  if (wants("provider")) for (const variant of PRIMARY) push(`provider/${variant}`, "provider", variant, ["--idp", "oidc-provider"]);
  if (wants("insecure")) for (const variant of PRIMARY) push(`insecure/${variant}`, "insecure", variant, ["--insecure", "deny"]);
  if (wants("transport")) {
    for (const variant of ["가-서명", "나-자체서명", "나-jose"]) push(`transport/${variant}`, "transport", variant, ["--transport", "node-http"]);
  }
  let tls = null;
  if (wants("tls")) {
    tls = makeCertificates();
    const ca = { NODE_EXTRA_CA_CERTS: join(TLS, "ca.crt") };
    const args = ["--tls", TLS, "--insecure", "deny"];
    for (const variant of PRIMARY) {
      push(`tls/ca/${variant}`, "tls", variant, args, ca);
      push(`tls/no-ca/${variant}`, "tls", variant, args);
    }
    for (const variant of ["가-서명", "나-jose"]) {
      push(`tls/ca/node-http/${variant}`, "tls", variant, [...args, "--transport", "node-http"], ca);
      push(`tls/no-ca/node-http/${variant}`, "tls", variant, [...args, "--transport", "node-http"]);
    }
  }

  const notMeasured = [];
  for (const round of rounds) {
    const problems = judge(round);
    if (typeof tls === "string" && round.group === "tls") problems.push(tls);
    if (problems.length > 0) notMeasured.push({ id: round.id, problems });
  }
  // 고장의 양성 대조: 고장마다 적어도 한 변형이 거부해야 한다.
  for (const fault of TOKEN_FAULTS) {
    const ofFault = rounds.filter((round) => round.group === "fault" && round.args[1] === fault && round.result !== null);
    if (ofFault.length > 0 && !ofFault.some((round) => round.result.outcome === "rejected")) {
      notMeasured.push({ id: `fault/${fault}`, problems: ["어느 변형도 거부하지 않아 이 고장이 틀린 토큰인지 서지 않았다"] });
    }
  }
  // TLS 의 양성 대조: 인증 기관을 주지 않은 회차가 TLS 검증 오류로 거부돼야 한다.
  for (const round of rounds.filter((item) => item.group === "tls" && !item.caGiven && item.result !== null)) {
    const codes = round.result.outcome === "rejected" ? codesOf(round.result.error) : [];
    if (!codes.some((code) => TLS_ERROR_CODES.includes(code))) {
      notMeasured.push({ id: round.id, problems: [`인증 기관 없이 TLS 검증 오류가 나지 않았다: ${round.result.outcome} ${codes.join(",")}`] });
    }
  }

  const rows = rounds.map((round) => ({
    id: round.id,
    outcome: round.result?.outcome ?? null,
    subMatches: round.result?.subMatches ?? null,
    stage: round.result?.stage ?? null,
    error: round.result?.outcome === "rejected" ? flatten(round.result.error) : null,
    idpLog: round.result?.idpLog ?? null,
    nodeFetchCalls: round.result?.nodeFetchCalls ?? null,
    globalFetchCalls: round.globalFetchCalls,
    caGiven: round.caGiven,
    stderrLineCount: round.stderrLines.length,
    stderrHead: round.stderrLines.slice(0, 12).map((line) => line.slice(0, 240)),
    seconds: round.seconds,
  }));
  const summary = {
    probe: "flow",
    node: process.version,
    groups: requested.length === 0 ? "all" : requested,
    rounds: rounds.length,
    measured: rounds.length - new Set(notMeasured.map((item) => item.id).filter((id) => rounds.some((round) => round.id === id))).size,
    notMeasured,
    tls,
    rows,
  };
  writeFileSync(join(OUT, "raw.json"), JSON.stringify(rounds, null, 2));
  writeFileSync(join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
  for (const row of rows) {
    const detail = row.outcome === "rejected" ? `${row.stage}: ${row.error?.[0] ?? ""}` : `sub 일치 ${String(row.subMatches)}`;
    console.log(`${row.id}\t${String(row.outcome)}\t${detail}\tjwks=${String(row.idpLog?.jwks)} token=${String(row.idpLog?.token)} 전역fetch=${String(row.globalFetchCalls)} nodeFetch=${String(row.nodeFetchCalls)}`);
  }
  console.log(JSON.stringify({ probe: "flow", node: process.version, rounds: rounds.length, notMeasured }));
  if (notMeasured.length > 0) process.exit(1);
}

main();
