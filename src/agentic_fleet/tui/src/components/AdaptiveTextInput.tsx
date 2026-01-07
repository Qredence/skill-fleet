import { TextAttributes, type TextareaRenderable } from "@opentui/core";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useKeyboard, useOnResize, useRenderer, useTerminalDimensions } from "@opentui/react";
import type { ThemeTokens } from "../themes";

export interface AdaptiveTextInputProps {
  value: string;
  onChange: (val: string) => void;
  colors: ThemeTokens;
  maxLines?: number; // default 8
  width?: number | string; // default "100%"
  paddingV?: number; // default 1 (≈8px)
  paddingH?: number; // default 2 (≈12px)
  onFocusNext?: () => void;
  onFocusPrev?: () => void;
}

/**
 * Compute number of lines after wrapping content to a given width (in columns).
 * Includes explicit newlines and long-word breaking.
 */
export function computeLineCount(content: string, columns: number): number {
  const col = Math.max(1, columns);
  const lines = content.split("\n");
  let count = 0;
  for (const line of lines) {
    if (line.length === 0) {
      count += 1;
      continue;
    }
    // Break long unbreakable words using wrap on columns
    const chunks = Math.ceil(line.length / col);
    count += chunks;
  }
  return Math.max(1, count);
}

function sanitizeInput(raw: string): string {
  // Remove control chars except newline, normalize spaces
  return raw.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "");
}

export function AdaptiveTextInput({
  value,
  onChange,
  colors,
  maxLines = 8,
  width = "100%",
  paddingV = 1,
  paddingH = 2,
  onFocusNext,
  onFocusPrev,
}: AdaptiveTextInputProps) {
  const renderer = useRenderer();
  const { width: termWidth } = useTerminalDimensions();
  const [content, setContent] = useState<string>(value);
  const textareaRef = useRef<TextareaRenderable>(null);
  const [debounceTimer, setDebounceTimer] = useState<number | null>(null);

  // Estimate container columns
  const containerCols = useMemo(() => {
    // If width is number, use that; if percentage, approximate using terminal width
    const base = typeof width === "number" ? width : Math.floor(termWidth * 0.98);
    const inner = Math.max(1, (base as number) - paddingH * 2);
    return inner;
  }, [width, termWidth, paddingH]);

  // Compute dynamic height based on content and constraints
  const lineCount = useMemo(() => computeLineCount(content, containerCols), [content, containerCols]);
  const clampedLines = Math.min(Math.max(1, lineCount), maxLines);

  // Announce line count changes for screen reader-style feedback
  useEffect(() => {
    try {
      renderer.console.show();
      console.log(`Textbox lines: ${clampedLines}`);
    } catch {}
  }, [clampedLines, renderer]);

  // Debounced input handler
  const applyChange = useCallback(
    (next: string) => {
      if (debounceTimer) clearTimeout(debounceTimer);
      const h = setTimeout(() => {
        const sanitized = sanitizeInput(next);
        setContent(sanitized);
        onChange(sanitized);
      }, 100);
      setDebounceTimer(h as unknown as number);
    },
    [debounceTimer, onChange]
  );

  useOnResize(() => {
    // Recompute based on new terminal width
    setContent((prev) => prev);
  });

  useKeyboard((key) => {
    if (key.name === "tab" && !key.shift) {
      onFocusNext?.();
    } else if (key.name === "tab" && key.shift) {
      onFocusPrev?.();
    }
    // After key processing, read current text and update
    setTimeout(() => {
      const text = textareaRef.current?.plainText ?? content;
      applyChange(text);
    }, 0);
  });

  const showMaxIndicator = lineCount > maxLines;
  const borderColor = "#CCCCCC";

  const widthStyle: number | "auto" | `${number}%` =
    typeof width === "number"
      ? width
      : `${Math.max(1, parseInt(String(width), 10) || 100)}%`;

  return (
    <box
      style={{
        border: true,
        borderColor: borderColor,
        backgroundColor: colors.bg.secondary,
        paddingTop: paddingV,
        paddingBottom: paddingV,
        paddingLeft: paddingH,
        paddingRight: paddingH,
        flexDirection: "column",
        flexShrink: 0,
        width: widthStyle,
      }}
    >
      <textarea
        placeholder="Type..."
        initialValue={content}
        focused={true}
        ref={textareaRef}
        style={{
          height: clampedLines,
          minHeight: 1,
          backgroundColor: colors.bg.secondary,
          textColor: colors.text.primary,
          cursorColor: colors.border,
          overflow: showMaxIndicator ? "hidden" : "visible",
        }}
      />
      <box style={{ justifyContent: "space-between", marginTop: 1 }}>
        <text
          content={`Lines: ${clampedLines}/${maxLines}`}
          style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
        />
        {showMaxIndicator && (
          <text content="…" style={{ fg: colors.text.tertiary, attributes: TextAttributes.DIM }} />
        )}
      </box>
    </box>
  );
}
