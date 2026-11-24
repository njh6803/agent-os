// 접속 확인의 결과 중 행에 보이는 것. 요청 함수(`api/connection`)와 훅(`hooks/queries/connection`)과 행의 한 줄
// (`components/molecules/ConnectionLine`)이 함께 쓴다. molecules 는 `api` 를 import 하지 못해 이 종류의 모양을 따로 둔다.

/** 행에 보일 결과. 응답을 기다리는 중은 결과가 없는 것(`undefined`)이다. */
export type ConnectionResult =
  | { readonly state: "reached" }
  | { readonly state: "unreached"; readonly reason: string }
  /** 확인 요청 자체가 실패했다. 붙었는지 아닌지 모른다. */
  | { readonly state: "failed"; readonly message: string };

/** 눌러서 한 확인의 결과와 그 시각. */
export interface PressedResult {
  readonly result: ConnectionResult;
  /** 성공과 붙지 못함은 응답이 온 시각이고, 요청이 실패했으면 누른 시각이다. */
  readonly at: Date;
}
