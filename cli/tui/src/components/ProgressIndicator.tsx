import { useEffect, useState } from "react";

type Theme = {
  accent: string;
  muted: string;
  border: string;
};

/**
 * Activity summary from AppShell instrumentation.
 */
export type ActivitySummary = {
  lastEventAt: number | null;
  lastTokenAt: number | null;
  lastStatusAt: number | null;
  isActive: boolean;
  timeSinceLastEvent: number | null;
};

type Props = {
  theme: Theme;
  phase?: string;
  module?: string;
  status?: string;
  isStreaming: boolean;
  activity?: ActivitySummary;
};

const PHASE_ICONS: Record<string, string> = {
  understanding: "🔍",
  generation: "✨",
  validation: "✓",
  planning: "📋",
  completed: "✅",
  failed: "❌",
};

const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

/**
 * Format time since last event in human-readable form.
 */
function formatTimeSince(ms: number | null): string {
  if (ms === null) return "";
  if (ms < 1000) return "<1s";
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${seconds % 60}s`;
}

export function ProgressIndicator({ theme, phase, module, status, isStreaming, activity }: Props) {
  const [spinnerIdx, setSpinnerIdx] = useState(0);

  // Use activity.isActive for enhanced activity detection
  const showActivity = isStreaming || activity?.isActive;

  useEffect(() => {
    if (!showActivity) return;

    const interval = setInterval(() => {
      setSpinnerIdx((i) => (i + 1) % SPINNER_FRAMES.length);
    }, 80);

    return () => clearInterval(interval);
  }, [showActivity]);

  const spinner = showActivity ? SPINNER_FRAMES[spinnerIdx] : " ";
  const icon = phase ? PHASE_ICONS[phase] || "●" : "●";

  const statusText = (() => {
    if (status === "completed") return "Done";
    if (status === "failed") return "Failed";
    if (status === "cancelled") return "Cancelled";
    if (isStreaming) return "Streaming...";
    if (activity?.isActive) return "Working...";
    return "Ready";
  })();

  // Show time since last event when activity instrumentation is available
  const timeSinceText = activity?.timeSinceLastEvent != null
    ? formatTimeSince(activity.timeSinceLastEvent)
    : "";

  return (
    <box flexDirection="row" gap={1} paddingLeft={1} paddingTop={0} paddingBottom={1}>
      <text fg={theme.accent}>
        {spinner} {icon}
      </text>
      <text fg={theme.muted}>
        {phase ? phase.charAt(0).toUpperCase() + phase.slice(1) : "Idle"}
      </text>
      {module ? (
        <text fg={theme.muted}>
          → {module}
        </text>
      ) : null}
      <text fg={theme.border}>|</text>
      <text fg={showActivity ? theme.accent : theme.muted}>
        {statusText}
      </text>
      {timeSinceText ? (
        <>
          <text fg={theme.border}>|</text>
          <text fg={theme.muted}>
            last: {timeSinceText}
          </text>
        </>
      ) : null}
    </box>
  );
}
