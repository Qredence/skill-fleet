type Theme = {
  panel: string;
  border: string;
  muted: string;
};

type Props = {
  theme: Theme;
  left: string;
  right: string;
};

export function Footer({ theme, left, right }: Props) {
  return (
    <box
      flexDirection="row"
      justifyContent="space-between"
      alignItems="center"
      padding={1}
      backgroundColor={theme.panel}
      border
      borderColor={theme.border}
    >
      <text fg={theme.muted}>{left}</text>
      <text fg={theme.muted}>{right}</text>
    </box>
  );
}
