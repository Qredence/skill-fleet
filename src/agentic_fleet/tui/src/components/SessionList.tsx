import { TextAttributes } from "@opentui/core";
import type { Session } from "../types";
import type { ThemeTokens } from "../themes";

interface SessionListProps {
  sessions: Session[];
  recentSessions: Session[];
  focusIndex: number;
  colors: ThemeTokens;
}

export function SessionList({
  sessions,
  recentSessions,
  focusIndex,
  colors,
}: SessionListProps) {
  return (
    <box
      style={{
        position: "absolute",
        top: 5,
        left: 10,
        right: 10,
        maxHeight: 20,
        backgroundColor: colors.bg.panel,
        border: true,
        borderColor: colors.border,
        padding: 2,
        zIndex: 100,
      }}
    >
      <box flexDirection="column" style={{ width: "100%" }}>
        <text
          content="Recent Sessions"
          style={{
            fg: colors.text.accent,
            attributes: TextAttributes.BOLD,
            marginBottom: 1,
          }}
        />
        <box style={{ marginBottom: 1 }}>
          <input
            placeholder="Search sessions…"
            focused={true}
            style={{
              backgroundColor: colors.bg.secondary,
              textColor: colors.text.primary,
              placeholderColor: colors.text.dim,
            }}
          />
        </box>
        {recentSessions.length === 0 ? (
          <text
          content="No saved sessions yet. Start chatting to build history."
          style={{ fg: colors.text.tertiary }}
          />
        ) : (
          recentSessions.map((session, idx) => {
            const isSelected = idx === focusIndex;
            return (
              <box
                key={session.id}
                flexDirection="column"
                style={{
                  marginTop: 1,
                  padding: 1,
                  border: true,
                  borderColor: isSelected ? colors.text.accent : colors.border,
                  backgroundColor: isSelected
                    ? colors.bg.hover
                    : colors.bg.panel,
                }}
              >
                <text
                  content={session.name}
                  style={{
                    fg: colors.text.primary,
                    attributes: isSelected ? TextAttributes.BOLD : 0,
                  }}
                />
                <text
                  content={`${
                    session.messages.length
                  } messages · Updated ${new Date(
                    session.updatedAt
                  ).toLocaleString()}`}
                  style={{
                    fg: colors.text.secondary,
                    attributes: TextAttributes.DIM,
                    marginTop: 1,
                  }}
                />
              </box>
            );
          })
        )}
        <text
          content={"\n↑↓ select · enter resume · r rename · d delete · esc close"}
          style={{
            fg: colors.text.dim,
            attributes: TextAttributes.DIM,
            marginTop: 1,
          }}
        />
        {sessions.length > 5 && (
          <text
            content="Showing latest 5 sessions · Use /sessions for full list"
            style={{
              fg: colors.text.tertiary,
              attributes: TextAttributes.DIM,
              marginTop: 1,
            }}
          />
        )}
      </box>
    </box>
  );
}
