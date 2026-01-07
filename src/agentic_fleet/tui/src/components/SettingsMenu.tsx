import { TextAttributes } from "@opentui/core";
import type { ThemeTokens } from "../themes";

export type SettingPanelItem = {
  id: string;
  label: string;
  value: string;
  description?: string;
  type: "text" | "toggle" | "info";
  onActivate?: () => void;
};

export type SettingSection = { title: string; items: SettingPanelItem[] };

interface SettingsMenuProps {
  sections: SettingSection[];
  focusIndex: number;
  colors: ThemeTokens;
}

export function SettingsMenu({
  sections,
  focusIndex,
  colors,
}: SettingsMenuProps) {
  const flatItems = sections.flatMap((section) => section.items);
  const selectedItem = flatItems[focusIndex];
  let rangeCursor = 0;
  const sectionRanges = sections.map((section) => {
    const start = rangeCursor;
    const end = rangeCursor + section.items.length - 1;
    rangeCursor += section.items.length;
    return { start, end };
  });
  const rawActiveIndex = sectionRanges.findIndex(
    (r) => focusIndex >= r.start && focusIndex <= r.end
  );
  const activeSectionIndex = rawActiveIndex >= 0 ? rawActiveIndex : 0;
  const activeSection = sections[activeSectionIndex];
  const activeRange = sectionRanges[activeSectionIndex] || { start: 0, end: -1 };
  const activeItems = activeSection?.items || [];
  const localFocusIndex = Math.max(0, focusIndex - activeRange.start);
  const listHeight = 14;
  const detailWidth = 34;

  return (
    <box
      style={{
        position: "absolute",
        top: 5,
        left: 10,
        right: 10,
        maxHeight: 25,
        backgroundColor: colors.bg.panel,
        border: true,
        borderColor: colors.border,
        padding: 2,
        zIndex: 100,
      }}
    >
      <box flexDirection="column" style={{ width: "100%" }}>
        <text
          content="Settings"
          style={{
            fg: colors.text.accent,
            attributes: TextAttributes.BOLD,
            marginBottom: 1,
          }}
        />
        <box style={{ flexDirection: "row", gap: 2, marginBottom: 1 }}>
          {sections.map((s, idx) => (
            <box
              key={`tab-${s.title}`}
              style={{
                border: true,
                borderColor: idx === activeSectionIndex ? colors.text.accent : colors.border,
                backgroundColor: idx === activeSectionIndex ? colors.bg.hover : colors.bg.panel,
                paddingLeft: 1,
                paddingRight: 1,
                height: 1,
              }}
            >
              <text content={s.title} style={{ fg: colors.text.primary }} />
            </box>
          ))}
        </box>
        <text
          content="↑↓ item · ←→ section · Enter edit/toggle · Esc close"
          style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
        />
        <box style={{ flexDirection: "row", gap: 2, marginTop: 1 }}>
          <scrollbox
            style={{
              flexGrow: 1,
              height: listHeight,
              border: true,
              borderColor: colors.border,
              padding: 1,
              backgroundColor: colors.bg.panel,
            }}
          >
            {activeSection && (
              <text
                content={activeSection.title}
                style={{
                  fg: colors.text.secondary,
                  attributes: TextAttributes.BOLD,
                  marginBottom: 1,
                }}
              />
            )}
            {activeItems.length === 0 && (
              <text
                content="No settings available."
                style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
              />
            )}
            {activeItems.map((item, idx) => {
              const isSelected = localFocusIndex === idx;
              return (
                <box
                  key={item.id}
                  flexDirection="column"
                  style={{
                    marginTop: idx === 0 ? 0 : 1,
                    padding: 1,
                    border: true,
                    borderColor: isSelected ? colors.text.accent : colors.border,
                    backgroundColor: isSelected ? colors.bg.hover : colors.bg.panel,
                  }}
                >
                  <box style={{ justifyContent: "space-between" }}>
                    <text
                      content={item.label}
                      style={{
                        fg: colors.text.primary,
                        attributes: isSelected ? TextAttributes.BOLD : 0,
                      }}
                    />
                    <text
                      content={item.value}
                      style={{ fg: colors.text.secondary }}
                    />
                  </box>
                  {item.description && (
                    <text
                      content={item.description}
                      style={{
                        fg: colors.text.tertiary,
                        attributes: TextAttributes.DIM,
                        marginTop: 1,
                      }}
                    />
                  )}
                </box>
              );
            })}
          </scrollbox>
          <box
            flexDirection="column"
            style={{
              width: detailWidth,
              height: listHeight,
              border: true,
              borderColor: colors.border,
              padding: 1,
              backgroundColor: colors.bg.panel,
            }}
          >
            <text
              content="Details"
              style={{
                fg: colors.text.secondary,
                attributes: TextAttributes.BOLD,
                marginBottom: 1,
              }}
            />
            {selectedItem ? (
              <>
                <text
                  content={selectedItem.label}
                  style={{ fg: colors.text.primary, attributes: TextAttributes.BOLD }}
                />
                <text
                  content={`Value: ${selectedItem.value}`}
                  style={{ fg: colors.text.secondary, marginTop: 1 }}
                />
                {selectedItem.description && (
                  <text
                    content={selectedItem.description}
                    style={{ fg: colors.text.tertiary, marginTop: 1 }}
                  />
                )}
                <text
                  content={
                    selectedItem.type === "toggle"
                      ? "Enter to toggle"
                      : selectedItem.type === "info"
                      ? "Enter to run"
                      : "Enter to edit"
                  }
                  style={{ fg: colors.text.dim, attributes: TextAttributes.DIM, marginTop: 1 }}
                />
              </>
            ) : (
              <text
                content="No setting selected."
                style={{ fg: colors.text.dim, attributes: TextAttributes.DIM }}
              />
            )}
          </box>
        </box>
        <text
          content={
            "\nTip: /keybindings set <action> <binding> to update suggestion keys.\nUse /af-bridge + /af-model to point workflow mode at a new agent-framework bridge."
          }
          style={{
            fg: colors.text.dim,
            attributes: TextAttributes.DIM,
            marginTop: 2,
          }}
        />
      </box>
    </box>
  );
}
