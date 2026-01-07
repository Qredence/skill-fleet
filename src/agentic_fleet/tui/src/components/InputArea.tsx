import { TextAttributes } from "@opentui/core";
import type { ThemeTokens } from "../themes";
import type { InputMode } from "../types";

interface InputAreaProps {
  input: string;
  inputMode: InputMode;
  isProcessing: boolean;
  isFocused: boolean;
  placeholder: string;
  hint: string;
  colors: ThemeTokens;
  onInput: (val: string) => void;
  onSubmit: () => void;
}

export function InputArea({
  input,
  inputMode,
  isProcessing,
  isFocused,
  placeholder,
  hint,
  colors,
  onInput,
  onSubmit,
}: InputAreaProps) {
  const borderColor =
    inputMode === "command"
      ? colors.text.accent
      : inputMode === "mention"
      ? colors.text.tertiary
      : colors.border;

  return (
    <box
      style={{
        border: false,
        paddingTop: 0,
        paddingBottom: 0,
        paddingLeft: 0,
        paddingRight: 0,
        flexDirection: "column",
        flexShrink: 0,
      }}
    >
      <box style={{ flexDirection: "row", alignItems: "center", height: 2 }}>
        <text
          content={
            inputMode === "command" ? "/" : inputMode === "mention" ? "@" : "> "
          }
          style={{
            fg: borderColor,
            attributes: TextAttributes.BOLD,
            marginRight: 1,
          }}
        />
        <input
          placeholder={placeholder}
          value={input}
          onInput={onInput}
          onSubmit={onSubmit}
          focused={isFocused && !isProcessing}
          style={{
            flexGrow: 1,
            height: 2,
            minHeight: 2,
            backgroundColor: "transparent",
            focusedBackgroundColor: "transparent",
            textColor: colors.text.primary,
            focusedTextColor: colors.text.primary,
            placeholderColor: colors.text.dim,
            cursorColor: borderColor,
          }}
        />
      </box>
      <box style={{ marginTop: 0.5, justifyContent: "space-between" }}>
        <text
          content={hint}
          style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
        />
        {isProcessing && (
          <text content="Processing..." style={{ fg: colors.text.accent }} />
        )}
      </box>
    </box>
  );
}
