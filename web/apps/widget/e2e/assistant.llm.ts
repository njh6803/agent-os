// 위젯의 실제 모델 e2e(base-agent 티켓 06). 위젯에서 기본 에이전트 `assistant` 에게 등록된 문서에 근거가 있는 질문을 보내면
// 화면의 답에 문서 제목, "출처", 갱신일이 보인다. 문서는 감싸는 파이썬 시험(tests/test_widget_llm.py)이 띄운 가짜 문서 검색
// 서버의 표본이다(tests/fake_doc_search_server.py 의 육아휴직 업무편람, 갱신일 2026-10-01). 그 표본을 고치면 아래 낱말도 고친다.
// 트레이스에 `llm_called` 와 성공한 `search` 가 있는지는 감싸는 시험이 본다.
//
// 화면의 단언은 정해 둔 낱말이 보이는지로만 한다. 화면의 글이 `run_finished` 의 출력과 글자 그대로 같은지는 보지 않고,
// `[1]` 같은 대괄호 번호도 넣지 않는다. 위젯이 답을 마크다운으로 그려(answer-markdown, ADR 0053) 기호가 빠지고 번호가
// 위첨자가 되어도 깨지지 않게 하려는 것이다. 승인 카드를 실제 모델과 함께 누르는 장면은 두지 않는다.

import { ASSISTANT_AGENT } from "@agent-os/e2e-stack";
import { expect, test } from "@playwright/test";
import { askAgent } from "./llm-ask";

const QUESTION = "육아휴직은 최대 몇 년까지 쓸 수 있어?";
const TITLE = "육아휴직 업무편람";
const SOURCES = "출처";
const UPDATED = "2026-10-01";

test("기본 에이전트가 위젯에서 받은 질문에 출처를 붙여 실제 모델로 답한다", async ({
  page,
}, info) => {
  const output = await askAgent(page, info, ASSISTANT_AGENT, QUESTION);

  for (const word of [TITLE, SOURCES, UPDATED]) {
    await expect(output, `화면의 답에 "${word}" 가 없다`).toContainText(word);
  }
});
