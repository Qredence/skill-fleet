import type { ActivitySummary } from "../types";

type Theme = {
  panel: string;
  border: string;
  muted: string;
  accent?: string;
};

type Props = {
  theme: Theme;
  left: string;
  right: string;
  activity?: ActivitySummary;
  /** Current time in ms - pass to trigger re-renders for relative time display */
  currentTime?: number;
};

/**
 * Format a timestamp as a relative time string.
 */
function formatLastUpdate(timestamp: number | null, now: number): string {
  if (timestamp === null) return "";
  const diff = now - timestamp;
  if (diff < 1000) return "just now";
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  return `${Math.floor(diff / 60000)}m ago`;
}

export function Footer({ theme, left, right, activity, currentTime }: Props) {
  const now = currentTime ?? Date.now();
  // Build activity indicator if available
  const activityIndicator = activity?.lastEventAt
    ? `[${activity.isActive ? "●" : "○"} ${formatLastUpdate(activity.lastEventAt, now)}]`
    : "";

  return (
    <box
      flexDirection="row"
      justifyContent="space-between"
      alignItems="center"
      paddingLeft={1}
      paddingRight={1}
      paddingTop={0}
      paddingBottom={0}
    >
      <text fg={theme.muted}>{left}</text>
      <box flexDirection="row" gap={2}>
        {activityIndicator ? (
          <text fg={activity?.isActive ? theme.accent ?? theme.muted : theme.muted}>
            {activityIndicator}
          </text>
        ) : null}
        <text fg={theme.muted}>{right}</text>
      </box>
    </box>
  );
}
