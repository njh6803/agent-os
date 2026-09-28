"""ADR 0001 재측정용 임시 프로브. 측정이 끝나면 지운다."""

from typing import TypedDict, reveal_type

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    question: str
    answer: str


def ask_node(state: State) -> State:
    reply = interrupt({"question": state["question"]})
    return {"question": state["question"], "answer": str(reply)}


def done_node(state: State) -> State:
    return state


async def probe() -> None:
    # 1) StateGraph 만들기
    graph = StateGraph(State)
    reveal_type(graph)

    # 2) add_node / add_edge
    graph.add_node("ask", ask_node)
    graph.add_node("done", done_node)
    graph.add_edge(START, "ask")
    graph.add_edge("ask", "done")
    graph.add_edge("done", END)

    # 3) 체크포인터
    saver = InMemorySaver()
    reveal_type(saver)

    # 4) compile(checkpointer=...)
    app = graph.compile(checkpointer=saver)
    reveal_type(app)

    # 5) ainvoke 반환 타입
    config: RunnableConfig = {"configurable": {"thread_id": "run-1"}}
    first = await app.ainvoke({"question": "hi", "answer": ""}, config=config)
    reveal_type(first)
    answer_a: str = first["answer"]
    print(answer_a)

    # 6) Command(resume=...) 로 재개
    cmd = Command(resume="42")
    reveal_type(cmd)
    resumed = await app.ainvoke(cmd, config=config)
    answer_b: str = resumed["answer"]
    print(answer_b)

    # 7) astream 반환 타입
    async for chunk in app.astream(Command(resume="7"), config=config):
        reveal_type(chunk)
        print(chunk)

    # 8) 체크포인터 직접 조회
    state_snapshot = await app.aget_state(config)
    reveal_type(state_snapshot)
    print(state_snapshot.next)

    # 9) interrupt 반환 타입
    reveal_type(interrupt)
