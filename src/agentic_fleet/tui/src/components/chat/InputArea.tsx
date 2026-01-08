// @ts-nocheck
/** @jsxImportSource @opentui/react */
import { TextAttributes } from "@opentui/core";
import type { ThemeTokens } from "../../themes";
import type { InputMode } from "../../types";

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
            inputMode === "command" ? "| " : inputMode === "mention" ? "@" : "| "
          }
          style={{
            fg: colors.text.accent, 
            attributes: TextAttributes.BOLD,
            marginRight: 1,
          }}
        />
        <input
          placeholder={placeholder}
          value={input}
          onInput={(e) => {
              // OpenTUI input event might pass a string directly or an event object
              const val = typeof e === 'string' ? e : e?.target?.value;
              onInput(val);
          }}
          onSubmit={onSubmit}
          focused={isFocused && !isProcessing}
          style={{
            flexGrow: 1,
            height: 2,
            minHeight: 2,
            backgroundColor: "transparent",
            textColor: "#FFFFFF", 
            placeholderColor: colors.text.dim,
            cursorColor: colors.text.accent,
          }}
        />
      </box>
      <box style={{ marginTop: 0, justifyContent: "space-between" }}>
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
