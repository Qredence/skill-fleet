import { useEffect, useState } from "react";
import type { ActivitySummary } from "../types";

type Theme = {
  accent: string;
  muted: string;
  border: string;
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

// Pulse frames for non-token activity (slower, subtler animation)
const PULSE_FRAMES = ["◐", "◓", "◑", "◒"];

// Waiting indicator for HITL states (attention-grabbing)
const WAITING_FRAMES = ["◉", "◎"];

// Statuses that indicate waiting for user input (HITL)
const HITL_WAITING_STATUSES = new Set([
  "pending_user_input",
  "pending_hitl",
  "pending_review",
]);

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
  const [pulseIdx, setPulseIdx] = useState(0);
  const [waitingIdx, setWaitingIdx] = useState(0);

  // Detect HITL waiting state
  const isWaitingForInput = status ? HITL_WAITING_STATUSES.has(status) : false;

  // Use activity.isActive for enhanced activity detection
  const showActivity = isStreaming || activity?.isActive;
  // Show token streaming animation (fast spinner) vs general activity (slower pulse)
  const hasTokens = activity?.hasRecentTokens ?? false;

  // Fast spinner for token streaming
  useEffect(() => {
    if (!showActivity || !hasTokens || isWaitingForInput) return;

    const interval = setInterval(() => {
      setSpinnerIdx((i) => (i + 1) % SPINNER_FRAMES.length);
    }, 80);

    return () => clearInterval(interval);
  }, [showActivity, hasTokens, isWaitingForInput]);

  // Slower pulse for general activity (no token_stream)
  useEffect(() => {
    if (!showActivity || hasTokens || isWaitingForInput) return;

    const interval = setInterval(() => {
      setPulseIdx((i) => (i + 1) % PULSE_FRAMES.length);
    }, 250);

    return () => clearInterval(interval);
  }, [showActivity, hasTokens, isWaitingForInput]);

  // Waiting animation for HITL states
  useEffect(() => {
    if (!isWaitingForInput) return;

    const interval = setInterval(() => {
      setWaitingIdx((i) => (i + 1) % WAITING_FRAMES.length);
    }, 500);

    return () => clearInterval(interval);
  }, [isWaitingForInput]);

  // Choose animation based on state
  const spinner = (() => {
    if (isWaitingForInput) return WAITING_FRAMES[waitingIdx] ?? "◉";
    if (!showActivity) return " ";
    if (hasTokens) return SPINNER_FRAMES[spinnerIdx] ?? "⠋";
    return PULSE_FRAMES[pulseIdx] ?? "◐";
  })();

  const icon = phase ? PHASE_ICONS[phase] || "●" : "●";

  const statusText = (() => {
    if (isWaitingForInput) return "Waiting for input";
    if (status === "completed") return "Done";
    if (status === "failed") return "Failed";
    if (status === "cancelled") return "Cancelled";
    if (hasTokens) return "Streaming...";
    if (activity?.isActive) return "Working...";
    return "Ready";
  })();

  // Show time since last event when activity instrumentation is available
  const timeSinceText = activity?.timeSinceLastEvent != null
    ? formatTimeSince(activity.timeSinceLastEvent)
    : "";

  // Format phase name with first letter capitalized
  const phaseName = phase ? phase.charAt(0).toUpperCase() + phase.slice(1) : "Idle";

  // Concise format for narrow terminals: "Phase → Module → Status"
  // When waiting for input, highlight with special styling
  const statusColor = isWaitingForInput
    ? theme.accent  // Highlight waiting state
    : showActivity
      ? theme.accent
      : theme.muted;

  return (
    <box flexDirection="row" gap={1} paddingLeft={1} paddingTop={0} paddingBottom={1}>
      <text fg={theme.accent}>
        {spinner} {icon}
      </text>
      <text fg={theme.muted}>
        {phaseName}
      </text>
      {module ? (
        <text fg={theme.muted}>
          → {module}
        </text>
      ) : null}
      <text fg={theme.border}>→</text>
      <text fg={statusColor}>
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
