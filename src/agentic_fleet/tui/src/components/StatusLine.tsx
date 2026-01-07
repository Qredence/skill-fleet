/**
 * Status line component showing current mode, theme, and processing status
 * Extracted from index.tsx to improve code organization
 */

import { TextAttributes } from "@opentui/core";
import type { InputMode, AppSettings } from "../types.ts";
import type { ThemeTokens } from "../themes.ts";

export interface StatusLineProps {
  isProcessing: boolean;
  elapsedSec: number;
  mode: "standard" | "workflow";
  settings: AppSettings;
  inputMode: InputMode;
  suggestionFooter: string;
  colors: ThemeTokens;
}

/**
 * Renders the status line at the bottom of the input area
 */
export function StatusLine({
  isProcessing,
  elapsedSec,
  mode,
  settings,
  inputMode,
  suggestionFooter,
  colors,
}: StatusLineProps) {
  const providerLabel = settings.provider || "auto";
  const modelLabel = settings.model || "not set";
  const toolsLabel = settings.tools?.enabled ? "tools on" : "tools off";
  const leftContent = (() => {
    if (isProcessing)
      return `Warping... (esc to interrupt · ${elapsedSec}s)`;
    if (inputMode !== "chat") return suggestionFooter;
    const bridgePart =
      mode === "workflow"
        ? settings.afBridgeBaseUrl
          ? `Workflow • AF ${settings.afModel || settings.model || "model"}`
          : "Workflow • AF bridge not set"
        : `Standard • ${providerLabel} • ${modelLabel}`;
    return `Mode: ${bridgePart} • Theme: ${settings.theme} • ${toolsLabel} • /help for tips`;
  })();

  const rightContent = isProcessing
    ? "Streaming..."
    : mode === "workflow"
    ? "@agents enabled"
    : "";

  return (
    <box style={{ justifyContent: "space-between", alignItems: "center", marginTop: 0 }}>
      <text
        content={leftContent}
        style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
      />
      <text
        content={rightContent}
        style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
      />
    </box>
  );
}
