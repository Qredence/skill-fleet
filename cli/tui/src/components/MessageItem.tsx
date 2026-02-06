import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { stripAnsiEscapes } from "../utils/sanitize";
import { MarkdownView } from "./MarkdownView";
import { Streamdown } from "./Streamdown";
import { HitlMessage } from "./HitlMessage";
import { StreamingText } from "./StreamingText";
import type { ChatMessage } from "./MessageList";
import type { ActivitySummary } from "../types";

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
  /** Activity summary for showing work-in-progress indicator on last message */
  activity?: ActivitySummary;
  /** Whether this is the last message in the list (used for activity indicator) */
  isLast?: boolean;
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

// Pulse frames for activity indicator (when working but not streaming tokens)
const PULSE_FRAMES = ["◐", "◓", "◑", "◒"];

export const MessageItem = memo(function MessageItem({
  message,
  onHitlSubmit,
  focused = false,
  activity,
  isLast = false,
}: Props) {
  const style = ROLE[message.role];
  const isStreaming = message.status === "streaming";
  const isStreamingAssistant = message.role === "assistant" && isStreaming;

  // Show activity pulse on the last assistant message when working but not streaming tokens
  const showActivityPulse =
    isLast &&
    message.role === "assistant" &&
    !isStreaming &&
    activity?.isActive &&
    !activity?.hasRecentTokens;

  const [pulseIdx, setPulseIdx] = useState(0);

  useEffect(() => {
    if (!showActivityPulse) return;

    const interval = setInterval(() => {
      setPulseIdx((i) => (i + 1) % PULSE_FRAMES.length);
    }, 250);

    return () => clearInterval(interval);
  }, [showActivityPulse]);

  // Dynamic title with streaming or activity indicator
  const title = (() => {
    if (isStreamingAssistant) return `${style.label} ●`;
    if (showActivityPulse)
      return `${style.label} ${PULSE_FRAMES[pulseIdx] ?? "◐"}`;
    return style.label;
  })();

  // Sanitize AI-generated content to prevent terminal escape sequence injection
  const safeContent = useMemo(
    () => stripAnsiEscapes(message.content),
    [message.content],
  );

  const handleHitlSubmit = useCallback(
    (payload: Record<string, unknown>) => {
      if (onHitlSubmit) {
        onHitlSubmit(message.id, payload);
      }
    },
    [onHitlSubmit, message.id],
  );

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
    <box flexDirection="column" paddingLeft={1} gap={0}>
      <text fg={isStreaming ? "#22c55e" : style.fg}>{title}</text>
      <box flexDirection="column" paddingTop={0} paddingBottom={1}>
        {isStreamingAssistant ? (
          <>
            <Streamdown content={safeContent} streaming />
            <StreamingText
              theme={THEME}
              content=""
              isStreaming={true}
              showCursor={true}
              typingEffect={false}
            />
          </>
        ) : (
          <MarkdownView content={safeContent} streaming={false} />
        )}
      </box>
    </box>
  );
});
