/**
 * Prompt overlay component for user input and confirmations
 * Extracted from index.tsx to improve code organization
 */

import { TextAttributes } from "@opentui/core";
import type { Prompt } from "../types.ts";
import type { ThemeTokens } from "../themes.ts";

export interface PromptOverlayProps {
  prompt: Prompt;
  promptInputValue: string;
  onInputChange: (value: string) => void;
  onConfirm: () => void;
  promptSelectIndex: number;
  onSelectIndexChange: (index: number) => void;
  colors: ThemeTokens;
}

/**
 * Renders a prompt overlay for user input or confirmation
 */
export function PromptOverlay({
  prompt,
  promptInputValue,
  onInputChange,
  onConfirm,
  promptSelectIndex,
  onSelectIndexChange,
  colors,
}: PromptOverlayProps) {
  return (
    <box
      style={{
        position: "absolute",
        top: 7,
        left: 12,
        right: 12,
        backgroundColor: colors.bg.panel,
        border: true,
        borderColor: colors.border,
        padding: 2,
        zIndex: 200,
      }}
    >
      <box flexDirection="column" style={{ width: "100%" }}>
        <text
          content={prompt.message}
          style={{ fg: colors.text.secondary, marginBottom: 1 }}
        />
        {prompt.type === "input" ? (
          <box
            style={{
              border: true,
              borderColor: colors.border,
              backgroundColor: colors.bg.primary,
              paddingLeft: 1,
              paddingRight: 1,
              paddingTop: 1,
              paddingBottom: 1,
              marginTop: 1,
            }}
          >
            <input
              placeholder={prompt.placeholder || "Type and press Enter"}
              value={promptInputValue}
              onInput={onInputChange}
              onSubmit={onConfirm}
              focused={true}
              style={{
                flexGrow: 1,
                backgroundColor: colors.bg.primary,
                focusedBackgroundColor: colors.bg.primary,
              }}
            />
          </box>
        ) : prompt.type === "select" ? (
          <>
            <box
              style={{
                border: true,
                borderColor: colors.border,
                backgroundColor: colors.bg.primary,
                paddingLeft: 1,
                paddingRight: 1,
                paddingTop: 1,
                paddingBottom: 1,
                marginTop: 1,
              }}
            >
              <select
                options={prompt.options.map((option) => ({
                  ...option,
                  description: option.description || "",
                }))}
                selectedIndex={promptSelectIndex}
                focused={true}
                onChange={(index) => {
                  onSelectIndexChange(index);
                }}
                onSelect={(index, option) => {
                  onSelectIndexChange(index);
                  if (option) {
                    prompt.onSelect(option, index);
                  }
                }}
                style={{ height: 8 }}
              />
            </box>
            <text
              content="↑↓ choose · Enter select · Esc cancel"
              style={{
                fg: colors.text.dim,
                attributes: TextAttributes.DIM,
                marginTop: 1,
              }}
            />
          </>
        ) : (
          <text
            content="Press Enter to confirm · Esc to cancel"
            style={{
              fg: colors.text.dim,
              attributes: TextAttributes.DIM,
              marginTop: 1,
            }}
          />
        )}
      </box>
    </box>
  );
}
