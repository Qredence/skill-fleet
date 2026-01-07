export function getCliUsage(): string {
  return [
    "Usage: qlaw [options]",
    "",
    "Options:",
    "  --help       Show this help",
    "  --version    Show version",
    "  --status     Print configuration summary",
    "",
    "Run without options to launch the interactive TUI.",
  ].join("\n");
}

export function formatCliStatus(settings: {
  theme: string;
  autoScroll: boolean;
  model?: string;
  provider?: string;
  endpoint?: string;
  apiKey?: string;
  afBridgeBaseUrl?: string;
  afModel?: string;
  workflow?: { enabled?: boolean };
  tools?: { enabled?: boolean };
}): string {
  const redacted = settings.apiKey ? "****" + String(settings.apiKey).slice(-4) : "(not set)";
  return [
    `Theme: ${settings.theme}`,
    `Auto-scroll: ${settings.autoScroll ? "Enabled" : "Disabled"}`,
    `Model: ${settings.model ?? "(not set)"}`,
    `Provider: ${settings.provider ?? "Auto"}`,
    `Endpoint: ${settings.endpoint ?? "(not set)"}`,
    `API Key: ${redacted}`,
    `Tools: ${settings.tools?.enabled ? "Enabled" : "Disabled"}`,
    `AF Bridge: ${settings.afBridgeBaseUrl ?? "(not set)"}`,
    `AF Model: ${settings.afModel ?? "(not set)"}`,
    `Workflow Mode: ${settings.workflow?.enabled ? "Enabled" : "Disabled"}`,
  ].join("\n");
}
