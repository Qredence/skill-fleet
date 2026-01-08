// @ts-nocheck
/** @jsxImportSource @opentui/react */
import React from "react";
import { useUI } from "../../hooks/useUI";
import { SKILLS_FLEET_THEME } from "../../themes";
import { bold } from "@opentui/core";

interface AppShellProps {
  children: React.ReactNode; 
  artifactPane: React.ReactNode; 
  statusProps: any; 
}

export function AppShell({ children, artifactPane, statusProps }: AppShellProps) {
  const { showArtifact } = useUI();
  const colors = SKILLS_FLEET_THEME;

  return (
    <box
      width="100%"
      height="100%"
      flexDirection="column"
      backgroundColor={colors.bg.primary}
    >
      {/* Integrated Header */}
      <box
        style={{
          height: 3,
          backgroundColor: colors.bg.secondary,
          border: true,
          borderColor: colors.border,
          justifyContent: "center",
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <box flexDirection="row">
           <text content="SK" style={{ fg: colors.text.accent, attributes: bold }} />
           <text content="STANDARD" style={{ fg: colors.text.primary, attributes: bold }} />
           <text content="ET" style={{ fg: colors.text.accent, attributes: bold }} />
        </box>
      </box>

      {/* Main Split Area */}
      <box flexGrow={1} flexDirection="row">
        {/* Left Pane (Chat) */}
        <box
          width={showArtifact ? "70%" : "100%"}
          height="100%"
          flexDirection="column"
          borderRight={showArtifact} 
          borderColor={colors.border}
          padding={1}
        >
          {children}
        </box>

        {/* Right Pane (Artifacts) */}
        {showArtifact && (
          <box width="30%" height="100%" flexDirection="column" padding={1}>
            {artifactPane}
          </box>
        )}
      </box>

      {/* Integrated Footer */}
      <box 
        style={{ 
            height: 3, 
            backgroundColor: colors.bg.secondary, 
            border: true, 
            borderColor: colors.border,
            paddingLeft: 2,
            paddingRight: 2,
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between"
        }}
      >
        <text 
            content={`Mode: Standard • deepinfra • ${statusProps.settings?.model || 'Gemini'} • Theme: dark`} 
            style={{ fg: colors.text.dim }} 
        />
        <text content="/help for tips" style={{ fg: colors.text.dim }} />
      </box>
    </box>
  );
}
