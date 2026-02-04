type Theme = {
  panel: string;
  border: string;
  muted: string;
  accent?: string;
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
  left: string;
  right: string;
  activity?: ActivitySummary;
};

/**
 * Format a timestamp as a relative time string.
 */
function formatLastUpdate(timestamp: number | null): string {
  if (timestamp === null) return "";
  const now = Date.now();
  const diff = now - timestamp;
  if (diff < 1000) return "just now";
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  return `${Math.floor(diff / 60000)}m ago`;
}

export function Footer({ theme, left, right, activity }: Props) {
  // Build activity indicator if available
  const activityIndicator = activity?.lastEventAt
    ? `[${activity.isActive ? "●" : "○"} ${formatLastUpdate(activity.lastEventAt)}]`
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
