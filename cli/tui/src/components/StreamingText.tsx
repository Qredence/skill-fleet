import { useEffect, useState } from "react";

const CURSOR_FRAMES = ["▌", "▐", "░", "▒"];
const TYPING_CHARS = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"];

type Theme = {
  accent: string;
  muted: string;
};

type Props = {
  theme: Theme;
  content: string;
  isStreaming: boolean;
  showCursor?: boolean;
  typingEffect?: boolean;
};

export function StreamingText({
  theme,
  content,
  isStreaming,
  showCursor = true,
  typingEffect = true,
}: Props) {
  const [cursorIdx, setCursorIdx] = useState(0);
  const [typingIdx, setTypingIdx] = useState(0);

  // Animated cursor when streaming
  useEffect(() => {
    if (!isStreaming || !showCursor) return;

    const interval = setInterval(() => {
      setCursorIdx((i) => (i + 1) % CURSOR_FRAMES.length);
    }, 120);

    return () => clearInterval(interval);
  }, [isStreaming, showCursor]);

  // Typing effect animation
  useEffect(() => {
    if (!isStreaming || !typingEffect) return;

    const interval = setInterval(() => {
      setTypingIdx((i) => (i + 1) % TYPING_CHARS.length);
    }, 60);

    return () => clearInterval(interval);
  }, [isStreaming, typingEffect]);

  const cursor = isStreaming && showCursor ? (
    <span fg={theme.accent}>{CURSOR_FRAMES[cursorIdx]}</span>
  ) : null;

  // Add subtle typing indicator at end when streaming
  const typingIndicator = isStreaming && typingEffect ? (
    <span fg={theme.muted}>{TYPING_CHARS[typingIdx]}</span>
  ) : null;

  return (
    <text>
      {content}
      {typingIndicator}
      {cursor}
    </text>
  );
}
