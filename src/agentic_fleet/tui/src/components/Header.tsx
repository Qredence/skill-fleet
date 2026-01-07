import { TextAttributes } from "@opentui/core";
import type { ThemeTokens } from "../themes";

interface HeaderProps {
  mode: "standard" | "workflow";
  bridgeUrl?: string;
  colors: ThemeTokens;
}

export function Header({ mode, bridgeUrl, colors }: HeaderProps) {
  const isWorkflow = mode === "workflow";
  const statusColor = isWorkflow
    ? bridgeUrl
      ? colors.success
      : colors.error
    : colors.text.dim;
  const statusText = isWorkflow
    ? bridgeUrl
      ? "CONNECTED"
      : "DISCONNECTED"
    : "STANDALONE";

  return (
    <box
      style={{
        height: 4,
        backgroundColor: colors.bg.panel,
        border: true,
        borderColor: colors.border,
        paddingLeft: 2,
        paddingRight: 2,
        justifyContent: "space-between",
        alignItems: "center",
        flexShrink: 0,
      }}
    >
      <box flexDirection="column">
        <text
          content="QLAW CLI"
          style={{ fg: colors.text.accent, attributes: TextAttributes.BOLD }}
        />
        <text
          content="QLAW CLI"
          style={{ fg: colors.text.tertiary, attributes: TextAttributes.DIM }}
        />
      </box>

      <box flexDirection="column" alignItems="flex-end">
        <box>
          <text content="MODE: " style={{ fg: colors.text.dim }} />
          <text
            content={mode.toUpperCase()}
            style={{ fg: colors.text.primary, attributes: TextAttributes.BOLD }}
          />
        </box>
        {isWorkflow && (
          <box>
            <text content="STATUS: " style={{ fg: colors.text.dim }} />
            <text content={statusText} style={{ fg: statusColor }} />
          </box>
        )}
      </box>
    </box>
  );
}
