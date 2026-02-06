import type { KeyEvent } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { useMemo, useState } from "react";

export type SelectorOption = {
  id: string;
  label: string;
  description?: string | null;
};

type Theme = {
  text: string;
  muted: string;
  accent: string;
  border: string;
  panel: string;
};

type SingleProps = {
  mode: "single";
  theme: Theme;
  options: SelectorOption[];
  selectedId: string | null;
  onChange: (id: string) => void;
  onSelect?: (id: string) => void;
  focused: boolean;
  height?: number;
};

type MultiProps = {
  mode: "multi";
  theme: Theme;
  options: SelectorOption[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  onConfirm?: (ids: string[]) => void;
  focused: boolean;
  height?: number;
};

export function Selector(props: SingleProps | MultiProps) {
  if (props.mode === "single") {
    const { options, selectedId, onChange, onSelect, focused, height } = props;
    const selectedIndex = Math.max(
      0,
      options.findIndex((o) => o.id === selectedId),
    );
    const selectOptions = useMemo(
      () =>
        options.map((o) => ({
          name: o.label,
          description: o.description || "",
          value: o.id,
        })),
      [options],
    );

    return (
      <select
        options={selectOptions}
        selectedIndex={selectedIndex}
        height={height ?? Math.min(8, Math.max(3, options.length))}
        focused={focused}
        onChange={(_idx, opt) => {
          const id = (opt?.value as string | undefined) || "";
          if (id) onChange(id);
        }}
        onSelect={(_idx, opt) => {
          const id = (opt?.value as string | undefined) || "";
          if (id) {
            onChange(id);
            if (onSelect) onSelect(id);
          }
        }}
      />
    );
  }

  const { options, selectedIds, onChange, onConfirm, focused, height } = props;
  const [cursor, setCursor] = useState(0);

  const visibleHeight = height ?? Math.min(10, Math.max(3, options.length));
  const scrollStart = Math.max(0, Math.min(cursor - Math.floor(visibleHeight / 2), Math.max(0, options.length - visibleHeight)));
  const windowed = options.slice(scrollStart, scrollStart + visibleHeight);

  const toggle = (id: string) => {
    const set = new Set(selectedIds);
    if (set.has(id)) set.delete(id);
    else set.add(id);
    onChange(Array.from(set));
  };

  useKeyboard((key: KeyEvent) => {
    if (!focused) return;
    if (key.name === "up") {
      setCursor((v) => Math.max(0, v - 1));
      return;
    }
    if (key.name === "down") {
      setCursor((v) => Math.min(options.length - 1, v + 1));
      return;
    }
    if (key.name === "space") {
      const opt = options[cursor];
      if (opt) toggle(opt.id);
      return;
    }
    const isEnter = key.name === "enter" || key.name === "return";
    if (isEnter) {
      if (onConfirm) onConfirm(selectedIds);
    }
  });

  return (
    <box flexDirection="column" gap={0}>
      {windowed.map((opt, idx) => {
        const absoluteIndex = scrollStart + idx;
        const isCursor = absoluteIndex === cursor;
        const checked = selectedIds.includes(opt.id);
        const mark = checked ? "●" : "○";
        const cursorMark = isCursor ? "→" : " ";
        const line = `${cursorMark} ${mark} ${opt.label}`;

        return (
          <text key={opt.id} fg={isCursor ? props.theme.accent : props.theme.text}>
            {line}
          </text>
        );
      })}
      <text fg={props.theme.muted}>↑↓ move | space toggle | enter done</text>
    </box>
  );
}
