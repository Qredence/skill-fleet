import { memo, useCallback } from "react";
import { MarkdownView } from "./MarkdownView";
import { Streamdown } from "./Streamdown";
import { HitlMessage } from "./HitlMessage";
import type { ChatMessage } from "./MessageList";

const ROLE = {
  system: { label: "SYSTEM", fg: "#737373", border: "#2a2a2a", bg: "#0a0a0a" },
  user: { label: "YOU", fg: "#e5e5e5", border: "#2a2a2a", bg: "#0a0a0a" },
  assistant: { label: "AI", fg: "#e5e5e5", border: "#2a2a2a", bg: "#0a0a0a" },
  hitl: { label: "QUESTION", fg: "#ffffff", border: "#2a2a2a", bg: "#0a0a0a" },
} as const;

type Props = {
  message: ChatMessage;
  onHitlSubmit?: (messageId: string, payload: Record<string, unknown>) => void;
  focused?: boolean;
};

const THEME = {
  background: "#000000",
  panel: "#0a0a0a",
  panelAlt: "#121212",
  border: "#2a2a2a",
  accent: "#ffffff",
  text: "#e5e5e5",
  muted: "#737373",
  error: "#ef4444",
};

export const MessageItem = memo(function MessageItem({ message, onHitlSubmit, focused = false }: Props) {
  const style = ROLE[message.role];
  const title = message.status === "streaming" && message.role === "assistant" ? `${style.label} (streaming)` : style.label;
  const isStreamingAssistant = message.role === "assistant" && message.status === "streaming";

  const handleHitlSubmit = useCallback((payload: Record<string, unknown>) => {
    if (onHitlSubmit) {
      onHitlSubmit(message.id, payload);
    }
  }, [onHitlSubmit, message.id]);

  // Handle HITL interactive messages
  if (message.role === "hitl" && message.hitlData) {
    return (
      <HitlMessage
        theme={THEME}
        kind={message.hitlData.kind}
        prompt={message.hitlData.prompt}
        answered={message.hitlData.answered}
        answer={message.hitlData.answer}
        onSubmit={handleHitlSubmit}
        focused={focused}
      />
    );
  }

  return (
    <box flexDirection="column" border borderColor={style.border} backgroundColor={style.bg} padding={1} gap={0}>
      <text fg={style.fg}>
        <strong>{title}</strong>
      </text>
      <box flexDirection="column" paddingTop={0}>
        {isStreamingAssistant ? (
          <Streamdown content={message.content} streaming />
        ) : (
          <MarkdownView content={message.content} streaming={false} />
        )}
      </box>
    </box>
  );
});
