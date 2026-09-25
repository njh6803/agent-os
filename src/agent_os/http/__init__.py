"""HTTP 표면의 공용 배관. 채널과 관리가 같이 쓴다(ADR 0016).

에러 봉투와 상태 코드 표(`errors`), 라우트가 쓰는 에러 문서와 경로 변환기(`routes`), fail-closed
인증(`auth`). 채널과 관리와 `server` 가 이것을 import 하고, 이것은 core 와 sdk 만 import 한다.
어댑터는 이것을 import 하지 않는다 — HTTP 표면이 아니다.

**이름이 표준 라이브러리 `http` 와 같다.** 절대 import(`agent_os.http`)로는 부딪치지 않지만,
`src/agent_os/` 안의 파일을 스크립트로 실행하면 파이썬이 그 디렉터리를 `sys.path` 첫머리에 두어 이
패키지가 표준 라이브러리 자리에 들어온다. 그대로 두면 한참 뒤 `No module named 'http.client'` 로
죽어 원인이 보이지 않으므로, 여기서 알아채고 처방을 말하며 막는다. 이 층의 이름이 만든 문제라 이
층이 소유한다(ADR 0016 의 2026-09-25 이력).
"""

if __name__ != "agent_os.http":
    raise ImportError(
        f"agent_os.http 가 표준 라이브러리 http 자리에 {__name__!r} 로 import 됐다. "
        "src/agent_os 안의 파일을 스크립트로 실행하면 그 디렉터리가 sys.path 첫머리에 선다. "
        "agent-os 나 python -m agent_os.main 으로 실행한다"
    )
