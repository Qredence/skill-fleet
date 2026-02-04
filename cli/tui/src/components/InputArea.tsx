import type { KeyBinding } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { useMemo, useRef, useCallback } from "react";
import { ControlledTextarea } from "./ControlledTextarea";

type Theme = {
  panel: string;
  border: string;
  muted: string;
  text: string;
  accent: string;
};

type Props = {
  theme: Theme;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  focused: boolean;
  disabled: boolean;
};

export function InputArea({ theme, value, onChange, onSubmit, focused, disabled }: Props) {
  const textareaTheme = useMemo(
    () => ({ panelAlt: theme.panel, text: theme.text, muted: theme.muted }),
    [theme.panel, theme.text, theme.muted],
  );

  // Track if we just submitted to prevent double-firing
  const justSubmittedRef = useRef(false);

  const doSubmit = useCallback(() => {
    if (justSubmittedRef.current || disabled) return;
    justSubmittedRef.current = true;
    setTimeout(() => {
      justSubmittedRef.current = false;
    }, 100);
    onSubmit();
  }, [onSubmit, disabled]);

  // Handle keyboard at the InputArea level
  // This ensures we catch Enter key even if textarea's keybindings don't work
  useKeyboard((key) => {
    // Only handle when InputArea is focused and not disabled
    if (!focused || disabled) return;

    const isEnter = key.name === "enter" || key.name === "return";

    // Shift+Enter = newline (don't submit)
    if (isEnter && key.shift) {
      return;
    }

    // Enter without shift = submit
    if (isEnter) {
      doSubmit();
      return;
    }
  });

  // Keep keybindings for Shift+Enter newline behavior in the textarea
  const keyBindings = useMemo<KeyBinding[]>(
    () => [
      { name: "return", action: "submit" },
      { name: "enter", action: "submit" },
      { name: "return", ctrl: true, action: "submit" },
      { name: "enter", ctrl: true, action: "submit" },
      { name: "return", shift: true, action: "newline" },
      { name: "enter", shift: true, action: "newline" },
    ],
    [],
  );

  return (
    <box
      flexDirection="column"
      gap={0}
      padding={1}
      backgroundColor={theme.panel}
      border
      borderColor={theme.border}
      height={6}
    >
      <text fg={theme.muted}>
        <span fg={theme.accent}>Prompt</span>
        <span fg={theme.muted}> | Enter send | Shift+Enter newline</span>
      </text>

      <ControlledTextarea
        theme={textareaTheme}
        value={value}
        onChange={onChange}
        onSubmit={doSubmit}
        keyBindings={keyBindings}
        height={3}
        wrapText
        focused={focused && !disabled}
        placeholder={disabled ? "Waiting..." : "Describe the skill you want to create..."}
      />
    </box>
  );
}
