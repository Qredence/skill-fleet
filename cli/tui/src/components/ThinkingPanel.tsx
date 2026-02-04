type Theme = {
  panel: string;
  border: string;
  muted: string;
};

type Props = {
  theme: Theme;
  lines: string[];
};

export function ThinkingPanel({ theme, lines }: Props) {
  return (
    <box width={42} flexDirection="column" backgroundColor={theme.panel} border borderColor={theme.border} padding={1} gap={1}>
      <text fg={theme.muted}>
        <strong>Thinking</strong> <span fg={theme.muted}>(Ctrl+T)</span>
      </text>
      <scrollbox flexGrow={1} stickyScroll stickyStart="bottom" border borderColor={theme.border} padding={1} viewportCulling>
        <box flexDirection="column" gap={0}>
          {lines.map((line, idx) => (
            <text key={`${idx}_${line.slice(0, 20)}`} fg={theme.muted}>
              {line}
            </text>
          ))}
        </box>
      </scrollbox>
    </box>
  );
}
