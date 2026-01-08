// @ts-nocheck
import { TextAttributes, RGBA, SyntaxStyle, type ScrollBoxRenderable } from "@opentui/core";
import { useEffect, useRef, useState } from "react";
import type { Message } from "../../types";
import type { ThemeTokens } from "../../themes";

export interface MessageListProps {
  messages: Message[];
  isProcessing: boolean;
  spinnerFrame: string;
  colors: ThemeTokens;
  scrollTop: number; // Kept for compatibility but unused
}

type Segment =
  | { type: "text"; content: string }
  | { type: "code"; content: string; lang: string };

function splitIntoSegments(content: string): Segment[] {
  const segments: Segment[] = [];
  const regex = /```(\w+)?(?:\n|\s)([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index);
      if (text.trim()) segments.push({ type: "text", content: text });
    }
    const lang = match[1] ? match[1] : "plaintext";
    segments.push({ type: "code", content: match[2] || "", lang });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    const text = content.slice(lastIndex);
    if (text.trim()) segments.push({ type: "text", content: text });
  }

  if (segments.length === 0) {
    segments.push({ type: "text", content });
  }

  return segments;
}

const STICKY_THRESHOLD_ROWS = 3;

export function MessageList({
  messages,
  isProcessing,
  spinnerFrame,
  colors,
}: MessageListProps) {
  const scrollboxRef = useRef<ScrollBoxRenderable | null>(null);
  const [isSticky, setIsSticky] = useState(true);

  const syntaxStyle = SyntaxStyle.fromStyles({
    keyword: { fg: RGBA.fromHex("#ff6b6b"), bold: true },
    string: { fg: RGBA.fromHex("#51cf66") },
    comment: { fg: RGBA.fromHex("#868e96"), italic: true },
    number: { fg: RGBA.fromHex("#ffd43b") },
    default: { fg: RGBA.fromHex(colors.text.primary) },
  });

  // Auto-stick when near bottom
  useEffect(() => {
    const sb = scrollboxRef.current;
    if (!sb) return;
    if (isSticky) {
      // Use fallback if scrollToEnd is missing (API variance)
      if ('scrollToEnd' in sb && typeof sb.scrollToEnd === 'function') {
          (sb as any).scrollToEnd();
      } else if ('scrollTo' in sb) {
          // Fallback: estimate height or use max int
          (sb as any).scrollTo({ top: 999999 });
      }
    }
  }, [messages, isSticky, isProcessing, spinnerFrame]);

  // Attach scroll handler to toggle stickiness
  useEffect(() => {
    const sb = scrollboxRef.current;
    if (!sb) return;

    const onScroll = () => {
      // API Compatibility Check
      // Older/Newer versions might have different names.
      // We check if methods exist before calling.
      if (!('getTotalRows' in sb) || !('getViewportTopRow' in sb)) return;

      const totalRows = (sb as any).getTotalRows();
      const topRow = (sb as any).getViewportTopRow();
      const viewportRows = (sb as any).getViewportRowCount();
      
      const bottomVisible = topRow + viewportRows;
      const dist = Math.max(0, totalRows - bottomVisible);
      
      setIsSticky(dist <= STICKY_THRESHOLD_ROWS);
    };

    sb.on("scroll", onScroll);
    return () => {
      sb.off("scroll", onScroll);
    };
  }, []);

  return (
    // @ts-ignore - Scrollbox JSX element
    <scrollbox
      ref={scrollboxRef}
      style={{
        width: "100%",
        height: "100%",
        border: false,
        scrollbarOptions: {
            showArrows: true,
            trackOptions: { foregroundColor: colors.text.dim, backgroundColor: colors.bg.secondary },
        },
      }}
      contentOptions={{
          backgroundColor: "transparent"
      }}
      viewportOptions={{
          backgroundColor: "transparent"
      }}
      focused // Ensure it captures keyboard scrolling if focused
    >
      {messages.map((message, index) => {
        const isUser = message.role === "user";
        const isSystem = message.role === "system";

        if (isSystem) {
          return (
            // @ts-ignore
            <box
              key={message.id}
              style={{ marginBottom: 1, justifyContent: "flex-start", flexShrink: 0, width: "100%" }}
            >
              <text
                content={`[ ${message.content} ]`}
                style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
              />
            </box>
          );
        }

        return (
          // @ts-ignore
          <box
            key={message.id}
            flexDirection="column"
            style={{
              marginBottom: 1,
              alignItems: "flex-start",
              flexShrink: 0,
              width: "100%"
            }}
          >
          {/* @ts-ignore */}
          <box
            style={{
              backgroundColor: isUser ? colors.bg.hover : "transparent",
              padding: isUser ? 0 : 1,
              border: isUser,
              borderColor: colors.border,
              width: "100%"
            }}
          >
            {/* @ts-ignore */}
            <box flexDirection="column" style={{ width: "100%" }}>
              {splitIntoSegments(message.content).map((seg, idx) => {
                if (seg.type === "code") {
                  return (
                    // @ts-ignore
                    <box key={`${message.id}-code-${idx}`} style={{ marginBottom: 1 }}>
                      <code content={seg.content} filetype={seg.lang} syntaxStyle={syntaxStyle} />
                    </box>
                  );
                }
                return (
                  <text
                    key={`${message.id}-text-${idx}`}
                    content={seg.content}
                    style={{ fg: isUser ? colors.text.primary : colors.text.secondary }}
                  />
                );
              })}
            </box>
          </box>
            <text
              content={
                isUser
                  ? "You"
                  : `Assistant ${
                      isProcessing && index === messages.length - 1
                        ? spinnerFrame
                        : ""
                    }`
              }
              style={{
                fg: colors.text.dim,
                attributes: TextAttributes.DIM,
                marginTop: 0,
              }}
            />
          </box>
        );
      })}
    </scrollbox>
  );
}
