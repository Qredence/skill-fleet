import { TextAttributes, RGBA, SyntaxStyle } from "@opentui/core";
import type { Message } from "../types";
import type { ThemeTokens } from "../themes";

interface MessageListProps {
  messages: Message[];
  isProcessing: boolean;
  spinnerFrame: string;
  colors: ThemeTokens;
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

export function MessageList({
  messages,
  isProcessing,
  spinnerFrame,
  colors,
}: MessageListProps) {
  const syntaxStyle = SyntaxStyle.fromStyles({
    keyword: { fg: RGBA.fromHex("#ff6b6b"), bold: true },
    string: { fg: RGBA.fromHex("#51cf66") },
    comment: { fg: RGBA.fromHex("#868e96"), italic: true },
    number: { fg: RGBA.fromHex("#ffd43b") },
    default: { fg: RGBA.fromHex(colors.text.primary) },
  });
  return (
    <box
      flexDirection="column"
      style={{
        width: "100%",
        flexGrow: 1,
        justifyContent: "flex-end",
        paddingLeft: 1,
        paddingRight: 1,
        paddingTop: 0,
        paddingBottom: 0,
      }}
    >
      {messages.map((message, index) => {
        const isUser = message.role === "user";
        const isSystem = message.role === "system";

        if (isSystem) {
          return (
            <box
              key={message.id}
              style={{ marginBottom: 1, justifyContent: "flex-start" }}
            >
              <text
                content={`[ ${message.content} ]`}
                style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
              />
            </box>
          );
        }

        return (
          <box
            key={message.id}
            flexDirection="column"
            style={{
              marginBottom: 1,
              alignItems: "flex-start",
            }}
          >
          <box
            style={{
              backgroundColor: isUser ? colors.bg.hover : "transparent",
              padding: isUser ? 0 : 1,
              border: isUser,
              borderColor: colors.border,
            }}
          >
            <box flexDirection="column" style={{ width: "100%" }}>
              {splitIntoSegments(message.content).map((seg, idx) => {
                if (seg.type === "code") {
                  return (
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
    </box>
  );
}
