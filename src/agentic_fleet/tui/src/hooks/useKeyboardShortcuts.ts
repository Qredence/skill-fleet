/**
 * Hook for managing keyboard shortcuts and navigation
 * Extracted from index.tsx to improve code organization
 */

import { useCallback } from "react";
import { useKeyboard, useRenderer } from "@opentui/react";
import type { KeySpec, Action, InputMode, Prompt, UISuggestion } from "../types.ts";
import type { AppSettings } from "../types.ts";

export interface KeyboardShortcutsContext {
  // Overlay states
  showSessionList: boolean;
  setShowSessionList: (show: boolean) => void;
  showSettingsMenu: boolean;
  setShowSettingsMenu: (show: boolean) => void;
  prompt: Prompt | null;
  setPrompt: (prompt: Prompt | null) => void;
  setPromptInputValue: (value: string) => void;

  // Session list navigation
  recentSessions: Array<{ id: string }>;
  sessionFocusIndex: number;
  setSessionFocusIndex: React.Dispatch<React.SetStateAction<number>>;
  handleSessionActivate: () => void;

  // Settings menu navigation
  settingsSections: Array<{ items: Array<{ onActivate?: () => void }> }>;
  flatSettingsItems: Array<{ onActivate?: () => void }>;
  settingsFocusIndex: number;
  setSettingsFocusIndex: React.Dispatch<React.SetStateAction<number>>;
  handleSettingsItemActivate: () => void;

  // Suggestions navigation
  suggestions: UISuggestion[];
  selectedSuggestionIndex: number;
  setSelectedSuggestionIndex: React.Dispatch<React.SetStateAction<number>>;
  inputMode: InputMode;
  setInput: (value: string) => void;

  // Mode and messages
  mode: "standard" | "workflow";
  setMode: (mode: "standard" | "workflow") => void;
  setMessages: React.Dispatch<React.SetStateAction<import("../types.ts").Message[]>>;

  // Settings for keybindings
  settings: AppSettings;
}

/**
 * Manages keyboard shortcuts and navigation
 */
export function useKeyboardShortcuts(
  context: KeyboardShortcutsContext
): void {
  const renderer = useRenderer();

  const matchKey = useCallback((key: { name: string; ctrl?: boolean; alt?: boolean; shift?: boolean }, spec: KeySpec) => {
    return (
      key.name === spec.name &&
      !!key.ctrl === !!spec.ctrl &&
      !!key.alt === !!spec.alt &&
      !!key.shift === !!spec.shift
    );
  }, []);

  const keyFor = useCallback(
    (action: Action): KeySpec[] => context.settings.keybindings[action] || [],
    [context.settings.keybindings]
  );

  useKeyboard((key) => {
    // Session list overlay navigation
    if (context.showSessionList) {
      if (key.name === "escape") {
        context.setShowSessionList(false);
        return;
      }
      if (context.recentSessions.length > 0) {
        if (key.name === "down" || (key.name === "tab" && !key.shift)) {
          context.setSessionFocusIndex((prev) => (prev + 1) % context.recentSessions.length);
          return;
        }
        if (key.name === "up" || (key.name === "tab" && key.shift)) {
          context.setSessionFocusIndex(
            (prev) => (prev - 1 + context.recentSessions.length) % context.recentSessions.length
          );
          return;
        }
      }
      if (key.name === "enter" || key.name === "return") {
        context.handleSessionActivate();
        return;
      }
      // Block other keystrokes while overlay is focused
      return;
    }

    // Prompt overlay handling
    if (context.prompt) {
      if (key.name === "escape") {
        context.prompt.onCancel?.();
        context.setPrompt(null);
        context.setPromptInputValue("");
        return;
      }
      if (key.name === "enter" && context.prompt.type === "confirm") {
        context.prompt.onConfirm();
        context.setPrompt(null);
        context.setPromptInputValue("");
        return;
      }
      // For input/select prompts, let the component handle Enter
      if (context.prompt.type === "input" || context.prompt.type === "select") {
        return; // component will handle enter via onSubmit/onSelect
      }
    }

    // Settings overlay navigation
    if (context.showSettingsMenu) {
      if (key.name === "escape") {
        context.setShowSettingsMenu(false);
        return;
      }
      if (context.settingsSections.length > 0) {
        let cursor = 0;
        const ranges = context.settingsSections.map((section) => {
          const start = cursor;
          const end = cursor + section.items.length - 1;
          cursor += section.items.length;
          return { start, end };
        });
        const activeSectionIndex = ranges.findIndex(
          (r) => context.settingsFocusIndex >= r.start && context.settingsFocusIndex <= r.end
        );
        if (key.name === "left" || key.name === "right") {
          if (ranges.length > 0) {
            const delta = key.name === "left" ? -1 : 1;
            const current = activeSectionIndex >= 0 ? activeSectionIndex : 0;
            const next = (current + delta + ranges.length) % ranges.length;
            const target = ranges[next];
            if (target) {
              context.setSettingsFocusIndex(target.start);
              return;
            }
          }
        }
      }
      if (context.flatSettingsItems.length > 0) {
        if (key.name === "down" || (key.name === "tab" && !key.shift)) {
          context.setSettingsFocusIndex(
            (prev) => (prev + 1) % context.flatSettingsItems.length
          );
          return;
        }
        if (key.name === "up" || (key.name === "tab" && key.shift)) {
          context.setSettingsFocusIndex(
            (prev) =>
              (prev - 1 + context.flatSettingsItems.length) % context.flatSettingsItems.length
          );
          return;
        }
      }
      if (
        key.name === "enter" ||
        key.name === "return" ||
        key.name === "space"
      ) {
        context.handleSettingsItemActivate();
        return;
      }
    }

    // Suggestions navigation via keybindings
    if (context.suggestions.length > 0) {
      const nextSpecs = keyFor("nextSuggestion");
      const prevSpecs = keyFor("prevSuggestion");
      const autoSpecs = keyFor("autocomplete");

      if (nextSpecs.some((s) => matchKey(key, s))) {
        context.setSelectedSuggestionIndex((prev) =>
          prev < context.suggestions.length - 1 ? prev + 1 : 0
        );
        return;
      }
      if (prevSpecs.some((s) => matchKey(key, s))) {
        context.setSelectedSuggestionIndex((prev) =>
          prev > 0 ? prev - 1 : context.suggestions.length - 1
        );
        return;
      }
      if (autoSpecs.some((s) => matchKey(key, s))) {
        const sel = context.suggestions[context.selectedSuggestionIndex];
        if (!sel) return;
        if (context.inputMode === "command") context.setInput(`/${sel.label}`);
        else if (context.inputMode === "mention") context.setInput(`@${sel.label}`);
        return;
      }
    }

    // Close overlays with Escape
    if (key.name === "escape") {
      if (context.showSessionList) {
        context.setShowSessionList(false);
        return;
      }
      if (context.showSettingsMenu) {
        context.setShowSettingsMenu(false);
        return;
      }
      renderer?.stop();
      return;
    }

    // Toggle debug console with Ctrl+K
    if (key.ctrl && key.name === "k") {
      renderer?.toggleDebugOverlay();
      renderer?.console.toggle();
      return;
    }

    // Toggle mode with Ctrl+M
    if (key.ctrl && key.name === "m") {
      const newMode = context.mode === "standard" ? "workflow" : "standard";
      if (context.setMode) {
        context.setMode(newMode);
      }
      context.setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "system",
          content: `Mode toggled to: ${newMode}`,
          timestamp: new Date(),
        },
      ]);
      return;
    }

    // Exit with Ctrl+C
    if (key.ctrl && key.name === "c") {
      renderer?.stop();
      return;
    }
  });
}
