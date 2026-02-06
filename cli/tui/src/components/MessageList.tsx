import { forwardRef, memo, useImperativeHandle, useRef } from "react";
import type { ScrollBoxRenderable } from "@opentui/core";
import { MessageItem } from "./MessageItem";
import type { ActivitySummary, HitlPrompt } from "../types";

type Theme = {
  border: string;
  accent?: string;
};

export type ChatMessage = {
  id: string;
  role: "system" | "user" | "assistant" | "hitl";
  content: string;
  createdAt: number;
  status: "streaming" | "done" | "pending_response";

  // HITL-specific data for inline interactive prompts
  hitlData?: {
    kind:
      | "clarify"
      | "confirm"
      | "structure_fix"
      | "deep_understanding"
      | "tdd_red"
      | "tdd_green"
      | "tdd_refactor";
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
  /** Visual indicator that we jumped to bottom */
  showJumpedToBottom?: boolean;
};

/** Imperative handle for scroll control from parent */
export type MessageListHandle = {
  scrollUp: (lines?: number) => void;
  scrollDown: (lines?: number) => void;
  scrollPageUp: () => void;
  scrollPageDown: () => void;
  scrollToTop: () => void;
  scrollToBottom: () => void;
};

// Default scroll amount for page/half-page scrolling
const PAGE_SCROLL_LINES = 20;
const HALF_PAGE_SCROLL_LINES = 10;

export const MessageList = memo(
  forwardRef<MessageListHandle, Props>(function MessageList(
    {
      theme,
      messages,
      onHitlSubmit,
      activeHitlMessageId,
      activity,
      showJumpedToBottom,
    },
    ref,
  ) {
    const scrollboxRef = useRef<ScrollBoxRenderable>(null);

    useImperativeHandle(
      ref,
      () => ({
        scrollUp: (lines = HALF_PAGE_SCROLL_LINES) => {
          scrollboxRef.current?.scrollBy(-lines);
        },
        scrollDown: (lines = HALF_PAGE_SCROLL_LINES) => {
          scrollboxRef.current?.scrollBy(lines);
        },
        scrollPageUp: () => {
          scrollboxRef.current?.scrollBy(-PAGE_SCROLL_LINES);
        },
        scrollPageDown: () => {
          scrollboxRef.current?.scrollBy(PAGE_SCROLL_LINES);
        },
        scrollToTop: () => {
          scrollboxRef.current?.scrollTo(0);
        },
        scrollToBottom: () => {
          // Scroll to the maximum scroll position (content height)
          const box = scrollboxRef.current;
          if (box) {
            box.scrollTo(box.scrollHeight);
          }
        },
      }),
      [],
    );

    const lastIdx = messages.length - 1;
    return (
      <box flexDirection="column" flexGrow={1} position="relative">
        <scrollbox
          ref={scrollboxRef}
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

        {/* Visual confirmation when jumping to bottom */}
        {showJumpedToBottom ? (
          <box
            position="absolute"
            bottom={2}
            left={0}
            right={0}
            justifyContent="center"
            alignItems="center"
          >
            <box
              backgroundColor={theme.accent || "#22c55e"}
              paddingLeft={2}
              paddingRight={2}
            >
              <text fg="#000000">
                <strong>↓ Jumped to bottom</strong>
              </text>
            </box>
          </box>
        ) : null}
      </box>
    );
  }),
);
