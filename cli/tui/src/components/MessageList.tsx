import { MessageItem } from "./MessageItem";
import type { ActivitySummary, HitlPrompt } from "../types";

type Theme = {
  border: string;
};

export type ChatMessage = {
  id: string;
  role: "system" | "user" | "assistant" | "hitl";
  content: string;
  createdAt: number;
  status: "streaming" | "done" | "pending_response";

  // HITL-specific data for inline interactive prompts
  hitlData?: {
    kind: "clarify" | "confirm" | "structure_fix" | "deep_understanding";
    prompt: HitlPrompt;
    answered?: boolean;
    answer?: Record<string, unknown>;
  };
};

type Props = {
  theme: Theme;
  messages: ChatMessage[];
  onHitlSubmit?: (messageId: string, payload: Record<string, unknown>) => void;
  activeHitlMessageId?: string | null;
  /** Activity summary for showing work-in-progress indicator */
  activity?: ActivitySummary;
};

export function MessageList({ theme, messages, onHitlSubmit, activeHitlMessageId, activity }: Props) {
  const lastIdx = messages.length - 1;
  return (
    <scrollbox
      flexGrow={1}
      border
      borderColor={theme.border}
      padding={1}
      stickyScroll
      stickyStart="bottom"
      viewportCulling
    >
      <box flexDirection="column" gap={1}>
        {messages.map((m, idx) => (
          <MessageItem
            key={m.id}
            message={m}
            onHitlSubmit={onHitlSubmit}
            focused={m.id === activeHitlMessageId}
            activity={activity}
            isLast={idx === lastIdx}
          />
        ))}
      </box>
    </scrollbox>
  );
}
