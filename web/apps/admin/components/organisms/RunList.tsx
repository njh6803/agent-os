import Link from "next/link";
import { useId, useState } from "react";
import type { RunRow, RunStatus } from "../../api/traces";
import { useRunList } from "../../hooks/queries/traces";
import { ReadSection } from "./ReadSection";

/**
 * 실행 상태의 이름과 거르기의 차례. 이름은 용어집의 말이다. 결말 없음은 "지금 돌고 있다"가 아니라 끝내지 못하고 사라진
 * 실행과 구분되지 않는다는 뜻이라 "실행 중"으로 부르지 않는다(스토리 26, ADR 0021). `Record` 라서 계약에 상태가 늘거나
 * 줄면 여기가 컴파일에서 깨진다.
 */
const STATUS_NAMES = {
  paused: "일시정지",
  finished: "끝남",
  failed: "실패",
  unfinished: "결말 없음",
} as const satisfies Record<RunStatus, string>;

/** 거르기의 값. null 은 전부다. */
type Filter = RunStatus | null;

/** 전부와 상태 넷. 상태는 STATUS_NAMES 에 적은 차례다. */
const FILTERS: readonly (readonly [Filter, string])[] = [
  [null, "전부"],
  ...Object.keys(STATUS_NAMES)
    .filter(isRunStatus)
    .map((status) => [status, STATUS_NAMES[status]] as const),
];

function isRunStatus(value: string): value is RunStatus {
  return Object.hasOwn(STATUS_NAMES, value);
}

/**
 * 실행 목록(`GET /traces`). 행은 서버가 준 순서 그대로다(스토리 23). 화면이 다시 정렬하지 않는다. 상태 넷과 전부로
 * 거르고(스토리 24), 다음 쪽이 있으면 더 본다(스토리 25). 새로 고침과 실패의 표시는 읽기 골격(`ReadSection`)이다.
 * 거르기는 실패 중에도 남는다.
 */
export function RunList() {
  const [status, setStatus] = useState<Filter>(null);
  const { data, error, isValidating, mutate, setSize } = useRunList(status);

  return (
    <ReadSection
      heading="실행"
      data={data}
      error={error}
      isValidating={isValidating}
      onRefresh={() => {
        void mutate();
      }}
      placeholder="실행 목록을 불러오는 중이다"
      above={<StatusFilter value={status} onChange={setStatus} />}
    >
      {(pages) => {
        const rows = pages.flatMap((page) => page.runs);
        const nextCursor = pages.at(-1)?.next_cursor ?? null;
        return (
          <>
            {rows.length === 0 ? (
              <p>실행이 없다</p>
            ) : (
              <ol>
                {rows.map((row) => (
                  <Row key={row.run_id} row={row} />
                ))}
              </ol>
            )}
            {nextCursor === null ? null : (
              <button
                type="button"
                disabled={isValidating}
                onClick={() => {
                  void setSize((size) => size + 1);
                }}
              >
                더 보기
              </button>
            )}
          </>
        );
      }}
    </ReadSection>
  );
}

interface StatusFilterProps {
  readonly value: Filter;
  readonly onChange: (value: Filter) => void;
}

function StatusFilter({ value, onChange }: StatusFilterProps) {
  const name = useId();
  return (
    <fieldset>
      <legend>상태</legend>
      {FILTERS.map(([filter, label]) => (
        <label key={label}>
          <input
            type="radio"
            name={name}
            checked={value === filter}
            onChange={() => {
              onChange(filter);
            }}
          />
          {label}
        </label>
      ))}
    </fieldset>
  );
}

/**
 * 행 하나. 실행 요약이거나 읽을 수 없는 트레이스다. 둘 다 그 실행을 여는 링크를 둔다. 열면 요약이 싣지 않는 이벤트를
 * 보고, 읽을 수 없는 트레이스는 그 이유를 서버의 봉투로 본다. 멈춘 실행은 상태를 두드러지게 해 바로 알아본다.
 */
function Row({ row }: { readonly row: RunRow }) {
  return (
    <li>
      <Link href={`/runs/${encodeURIComponent(row.run_id)}`}>{row.run_id}</Link>{" "}
      {"reason" in row ? (
        <span>읽을 수 없는 트레이스: {row.reason}</span>
      ) : (
        <>
          {row.status === "paused" ? (
            <strong>{STATUS_NAMES.paused}</strong>
          ) : (
            <span>{STATUS_NAMES[row.status]}</span>
          )}{" "}
          <span>
            에이전트 {row.agent} · 주체 {row.principal} · 시작 {row.started_at} · 마지막{" "}
            {row.last_at}
          </span>
        </>
      )}
    </li>
  );
}
