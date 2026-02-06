import { useEffect, useRef } from "react";
import type { TextareaRenderable, KeyBinding } from "@opentui/core";
import { THEME } from "../../lib/theme";

type Message = {
  id: string;
  role: "system" | "user" | "assistant" | "hitl";
  content: string;
  status: "streaming" | "done";
};

type Props = {
  messages: Message[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  isDisabled: boolean;
  disabledReason?: string;
  focused: boolean;
};

function MessageItem({ message }: { message: Message }) {
  const colors = {
    system: THEME.muted,
    user: THEME.text,
    assistant: THEME.text,
    hitl: THEME.accent,
  };

  return (
    <box flexDirection="column" gap={0}>
      <text fg={colors[message.role]}>{message.content}</text>
      {message.status === "streaming" ? (
        <text fg={THEME.muted}>▌</text>
      ) : null}
    </box>
  );
}

// Key bindings for textarea: Shift+Enter inserts newline, Enter submits
const KEY_BINDINGS: KeyBinding[] = [
  { name: "return", shift: true, action: "newline" },
  { name: "enter", shift: true, action: "newline" },
  { name: "return", action: "submit" },
  { name: "enter", action: "submit" },
];

export function ChatView({
  messages,
  inputValue,
  onInputChange,
  onSubmit,
  isDisabled,
  disabledReason,
  focused,
}: Props) {
  const textareaRef = useRef<TextareaRenderable>(null);

  useEffect(() => {
    const current = textareaRef.current?.plainText ?? "";
    if (current !== inputValue) {
      textareaRef.current?.setText(inputValue);
    }
  }, [inputValue]);

  return (
    <box flexDirection="column" flexGrow={1} gap={1}>
      <scrollbox flexGrow={1} border borderColor={THEME.border} padding={1}>
        <box flexDirection="column" gap={1}>
          {messages.map((m) => (
            <MessageItem key={m.id} message={m} />
          ))}
        </box>
      </scrollbox>

      <box flexDirection="column" gap={0}>
        <textarea
          ref={textareaRef}
          initialValue={inputValue}
          placeholder={
            isDisabled
              ? disabledReason || "Waiting..."
              : "Describe skill to create..."
          }
          height={3}
          focused={focused && !isDisabled}
          backgroundColor={THEME.panel}
          textColor={THEME.text}
          placeholderColor={THEME.muted}
          keyBindings={isDisabled ? [] : KEY_BINDINGS}
          onContentChange={() => {
            const text = textareaRef.current?.plainText ?? "";
            onInputChange(text);
          }}
          onSubmit={() => {
            if (!isDisabled) {
              onSubmit();
            }
          }}
        />
        <box flexDirection="row" gap={2}>
          <text fg={THEME.muted}>Enter send | Shift+Enter newline</text>
          {isDisabled && disabledReason ? (
            <text fg={THEME.muted}>| ⏸ {disabledReason}</text>
          ) : null}
        </box>
      </box>
    </box>
  );
}
