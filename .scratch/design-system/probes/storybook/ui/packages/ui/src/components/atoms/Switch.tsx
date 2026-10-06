import type { ChangeEvent } from "react";

export interface SwitchProps {
  label: string;
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

/** `role="switch"` 인 체크박스. 상태는 체크박스의 checked 가 들고 보조 기술에는 켜짐·꺼짐으로 읽힌다. */
export function Switch({ label, checked, defaultChecked, disabled, onCheckedChange }: SwitchProps) {
  const change = (event: ChangeEvent<HTMLInputElement>): void => {
    onCheckedChange?.(event.target.checked);
  };
  return (
    <label className="inline-flex items-center gap-2 text-sm text-text">
      <input
        type="checkbox"
        role="switch"
        className="peer sr-only"
        checked={checked}
        defaultChecked={defaultChecked}
        disabled={disabled}
        onChange={change}
      />
      <span
        aria-hidden="true"
        className="relative h-6 w-11 rounded-full border border-border bg-surface peer-checked:border-accent peer-checked:bg-accent peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent peer-disabled:opacity-50 after:absolute after:top-[3px] after:left-[3px] after:size-4 after:rounded-full after:bg-text peer-checked:after:translate-x-5 peer-checked:after:bg-on-accent"
      />
      {label}
    </label>
  );
}
