import { useEffect, useState } from "react";

type Theme = {
  panel: string;
  border: string;
  muted: string;
  accent: string;
};

type Props = {
  theme: Theme;
  lines: string[];
  isActive?: boolean;
};

const ACTIVITY_FRAMES = ["○", "◔", "◑", "◕", "●"];

export function ThinkingPanel({ theme, lines, isActive = false }: Props) {
  const [activityIdx, setActivityIdx] = useState(0);

  // Activity indicator animation when thinking is happening
  useEffect(() => {
    if (!isActive) {
      setActivityIdx(0);
      return;
    }

    const interval = setInterval(() => {
      setActivityIdx((i) => (i + 1) % ACTIVITY_FRAMES.length);
    }, 100);

    return () => clearInterval(interval);
  }, [isActive]);

  const activityIndicator = isActive ? (
    <text fg={theme.accent}>{ACTIVITY_FRAMES[activityIdx]}</text>
  ) : (
    <text fg={theme.muted}>○</text>
  );

  return (
    <box width={45} flexDirection="column" paddingLeft={1} paddingRight={1}>
      <box flexDirection="row" justifyContent="space-between">
        <text fg={theme.muted}>
          Thinking (Ctrl+T)
        </text>
        {activityIndicator}
      </box>
      <scrollbox flexGrow={1} stickyScroll stickyStart="bottom" paddingTop={1} viewportCulling>
        <box flexDirection="column" gap={0}>
          {lines.length === 0 ? (
            <text fg={theme.muted}>waiting...</text>
          ) : (
            lines.map((line, idx) => (
              <text key={`${idx}_${line.slice(0, 20)}`} fg={theme.muted}>
                {line}
              </text>
            ))
          )}
        </box>
      </scrollbox>
    </box>
  );
}
