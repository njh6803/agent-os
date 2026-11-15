// 관리 화면의 루프백 판정. 시작 래퍼의 바인딩 호스트와 설정의 상류 호스트가 같은 거부 표를 지난다.
// 규칙은 `serve` 와 같다(src/agent_os/main.py 의 LOOPBACK_HOSTS, tests/test_main.py 의 두 선례). 상류는 하나를 더
// 좁혀 127.0.0.1 만 받는다. Next 가 IPv6 리터럴 목적지를 컴파일하지 못한다(ADR 0011 의 2026-09-30 이력).
// 두 판정이 래퍼와 설정 파일에 이어져 있는지는 start.test.ts 와 ../next.config.test.ts 가 잰다.

import { describe, expect, test } from "vitest";
import { CASES, expectSignals, nameOf } from "../testing/container-network.ts";
import {
  bindingProblem,
  CONTAINER_NETWORK_ENV,
  type ContainerNetwork,
  IMAGE_MARKER,
  upstreamProblem,
} from "./loopback.ts";

// 예외가 꺼진 입력. 표지 파일도 환경 변수도 없다.
const OUTSIDE: ContainerNetwork = { imageMarker: false, env: undefined };

// 허용되는 것과 거부되는 것. 기댓값을 리터럴로 적는다. 허용 목록을 도는 단언은 그 목록이 비는 날 조용히 통과한다.
const ALLOWED = ["127.0.0.1", "::1"];
const REFUSED = [
  "0.0.0.0",
  "::",
  // 이름은 ::1 로도 풀릴 수 있어 루프백이라는 보장이 없다(tests/test_main.py 의 선례)
  "localhost",
  "192.168.0.10",
  "admin.example",
];

/** URL 에 호스트를 넣는다. IPv6 는 대괄호로 싼다. */
function origin(host: string): string {
  return host.includes(":") ? `http://[${host}]:8000` : `http://${host}:8000`;
}

function problem(found: string | null): string {
  if (found === null) {
    throw new Error("거부되지 않았다");
  }
  return found;
}

describe("관리 화면이 설 호스트", () => {
  for (const host of ALLOWED) {
    test(`${host} 는 받는다`, () => {
      expect(bindingProblem(host, "3000", OUTSIDE)).toBeNull();
    });
  }

  for (const host of REFUSED) {
    test(`${host} 는 구성 오류이고 진단이 허용되는 두 주소와 SSH 포트 포워딩을 말한다`, () => {
      const found = problem(bindingProblem(host, "3000", OUTSIDE));

      expect(found).toContain(host);
      expect(found).toContain("127.0.0.1");
      expect(found).toContain("::1");
      expect(found.toLowerCase()).toContain("ssh -l");
    });
  }

  test("SSH 포트 포워딩 안내는 관리 화면이 설 포트를 싣는다", () => {
    expect(bindingProblem("0.0.0.0", "3100", OUTSIDE)).toContain("ssh -L 3100:127.0.0.1:3100");
  });
});

describe("관리 화면이 넘기는 상류", () => {
  test("127.0.0.1 은 받는다", () => {
    expect(upstreamProblem("http://127.0.0.1:8100", OUTSIDE)).toBeNull();
  });

  for (const host of REFUSED) {
    test(`${host} 는 구성 오류이고 진단이 127.0.0.1 과 SSH 포트 포워딩을 말한다`, () => {
      const found = problem(upstreamProblem(origin(host), OUTSIDE));

      expect(found).toContain(host);
      expect(found).toContain("127.0.0.1");
      expect(found.toLowerCase()).toContain("ssh -l");
    });
  }

  test("::1 은 루프백이어도 구성 오류이고 serve 를 127.0.0.1 에 세우라고 안내한다", () => {
    // Next 16.3.6 의 rewrites 는 목적지 호스트를 경로 틀로 컴파일해 [::1] 에서 요청마다 500 이었다(ADR 0011 의
    // 2026-09-30 이력). 요청 때 드러날 것을 설정을 읽을 때 막는다.
    const found = problem(upstreamProblem("http://[::1]:8000", OUTSIDE));

    expect(found).toContain("::1");
    expect(found).toContain("--host 127.0.0.1");
  });

  test("줄여 쓴 IPv4 는 URL 이 127.0.0.1 로 정규화해 받는다", () => {
    // 판정은 URL 파서가 정규화한 호스트를 본다. 127.1 은 127.0.0.1 과 같은 주소다.
    expect(upstreamProblem("http://127.1:8100", OUTSIDE)).toBeNull();
  });

  for (const value of [
    "127.0.0.1:8000",
    "https://127.0.0.1:8000",
    "http://127.0.0.1:8000/api",
    "http://127.0.0.1:8000/?a=1",
    "http://user:secret@127.0.0.1:8000",
    "http://127.0.0.1:8000#x",
  ]) {
    test(`http 출처 하나가 아닌 ${value} 는 구성 오류다`, () => {
      expect(upstreamProblem(value, OUTSIDE)).toContain("AGENT_OS_UPSTREAM");
    });
  }

  test("계정을 실은 상류의 진단은 그 비밀번호를 싣지 않는다", () => {
    // 원칙 V: 로그에 비밀번호를 싣지 않는다. 구성 오류는 터미널과 CI 로그에 남는다.
    expect(problem(upstreamProblem("http://user:secret@127.0.0.1:8000", OUTSIDE))).not.toContain(
      "secret",
    );
  });
});

// 컨테이너 네트워크 예외. 사례 표(tests/fixtures/container_network/cases.json)를 파이썬의 tests/test_main.py 와 위젯, 위젯
// 미리보기 페이지의 시험이 함께 읽는다. 표지 파일을 실제로 읽는 길은 이미지를 띄우는 시험(release-image 07·08·09)이 본다.
describe("컨테이너 네트워크 예외의 사례 표", () => {
  test("표가 판정의 종류를 모두 갖고 있고 이름과 자리가 코드의 것과 같다", () => {
    expect(new Set(CASES.binding.map(({ verdict }) => verdict))).toEqual(
      new Set(["ok", ...Object.keys(CASES.bindingSignals)]),
    );
    expect(new Set(CASES.upstream.map(({ verdict }) => verdict))).toEqual(
      new Set(["ok", ...Object.keys(CASES.upstreamSignals)]),
    );
    expect(CASES.envName).toBe(CONTAINER_NETWORK_ENV);
    expect(CASES.markerPath).toBe(IMAGE_MARKER);
  });

  for (const item of CASES.binding) {
    test(`듣는 주소: ${nameOf(item)}`, () => {
      const found = bindingProblem(item.host, "3000", {
        imageMarker: item.marker,
        env: item.env,
      });

      if (item.verdict === "ok") {
        expect(found).toBeNull();
      } else {
        expectSignals(problem(found), CASES.bindingSignals, item);
      }
    });
  }

  for (const item of CASES.upstream) {
    test(`상류: ${nameOf(item)}`, () => {
      const found = upstreamProblem(`http://${item.host}:8000`, {
        imageMarker: item.marker,
        env: item.env,
      });

      if (item.verdict === "ok") {
        expect(found).toBeNull();
      } else {
        expectSignals(problem(found), CASES.upstreamSignals, item);
      }
    });
  }
});
