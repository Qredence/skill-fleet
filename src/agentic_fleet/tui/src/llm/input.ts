import type { Message } from "../types.ts";

// Build a plain-text prompt from history for broad compatibility with proxies
export function buildResponsesInput(history: Message[]): string {
  const lines: string[] = [];
  for (const m of history) {
    const role =
      m.role === "assistant"
        ? "Assistant"
        : m.role === "system"
        ? "System"
        : "User";
    lines.push(`${role}: ${m.content}`);
  }
  lines.push("Assistant:");
  return lines.join("\n\n");
}
