import type { InputMode } from "./types.ts";

export function getSuggestionFooter(inputMode: InputMode): string {
  if (inputMode === "command") return "↑↓ navigate · tab autocomplete · enter run";
  if (inputMode === "mention") return "↑↓ navigate · tab autocomplete · enter insert";
  return "";
}

export function getInputPlaceholder(inputMode: InputMode, mode: "standard" | "workflow"): string {
  if (inputMode === "command") return "Type a command name…";
  if (inputMode === "mention") return "Select a mention type…";
  return mode === "workflow"
    ? "Guide your agents… (type / for commands • @ for context)"
    : "Ask a question… (type / for commands • @ for context)";
}

export function getInputHint(inputMode: InputMode): string {
  if (inputMode === "command") return "↩ enter to run • tab autocomplete • esc cancel";
  if (inputMode === "mention") return "↑↓ choose mention • tab autocomplete • enter insert";
  return "enter send • shift+enter newline • esc clear";
}
