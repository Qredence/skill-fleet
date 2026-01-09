import type { AppSettings } from "../types.ts";

export function buildToolSystemPrompt(settings: AppSettings): string | null {
  if (!settings.tools?.enabled) return null;

  return [
    "You are a coding agent. Use tools when they help answer the request.",
    "To request tool execution, reply with a fenced JSON block using the 'tool' label.",
    "Format:",
    "```tool",
    "{\"tool\": \"read_file\", \"args\": {\"path\": \"path/to/file\"}}",
    "```",
    "You may also pass an array: {\"tools\":[{...}, {...}]}",
    "Available tools: read_file, list_dir, write_file, run_command.",
    "run_command executes shell commands and is dangerous; only request it when explicitly necessary.",
    "Only request tools you need to complete the task.",
  ].join("\n");
}
