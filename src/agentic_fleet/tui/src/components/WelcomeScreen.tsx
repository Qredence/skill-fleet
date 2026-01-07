import { TextAttributes } from "@opentui/core";
import type { ThemeTokens } from "../themes";

interface WelcomeScreenProps {
  cwd: string;
  colors: ThemeTokens;
}

export function WelcomeScreen({ cwd, colors }: WelcomeScreenProps) {
  return (
    <box
      flexDirection="column"
      style={{
        width: "100%",
        alignItems: "flex-start",
        justifyContent: "flex-start",
        paddingTop: 2,
      }}
    >
      <text
        content="QLAW CLI - Qredence"
        style={{
          fg: colors.text.accent,
          attributes: TextAttributes.BOLD,
          marginBottom: 1,
        }}
      />
      <text
        content="Your AI-powered terminal assistant"
        style={{ fg: colors.text.secondary, marginBottom: 2 }}
      />

      <box style={{ flexDirection: "row" }}>
        <box
          flexDirection="column"
          style={{
            border: true,
            borderColor: colors.border,
            padding: 1,
            width: 40,
          }}
        >
          <text
            content="Quick Start"
            style={{
              fg: colors.text.primary,
              attributes: TextAttributes.BOLD,
              marginBottom: 1,
            }}
          />
          <text
            content="/help - View commands"
            style={{ fg: colors.text.secondary }}
          />
          <text
            content="@file - Reference files"
            style={{ fg: colors.text.secondary }}
          />
          <text
            content="Ctrl+M - Toggle Workflow"
            style={{ fg: colors.text.secondary }}
          />
        </box>
      </box>
    </box>
  );
}
