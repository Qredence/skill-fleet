/**
 * Hook for managing input mode and suggestions
 * Handles command/mention detection and suggestion generation
 */

import { useState, useEffect } from "react";
import type { InputMode, UISuggestion, CustomCommand } from "../types.ts";
import { fuzzyMatch } from "../suggest.ts";
import {
  BUILT_IN_COMMANDS,
  getBuiltInDescription,
  MENTIONS,
} from "../commands.ts";

const MAX_VISIBLE_SUGGESTIONS = 8;

export interface UseInputModeReturn {
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  inputMode: InputMode;
  suggestions: UISuggestion[];
  selectedSuggestionIndex: number;
  setSelectedSuggestionIndex: React.Dispatch<React.SetStateAction<number>>;
  suggestionScrollOffset: number;
  showSuggestionPanel: boolean;
  inputAreaMinHeight: number;
  inputAreaPaddingTop: number;
}

export interface UseInputModeOptions {
  customCommands: CustomCommand[];
}

/**
 * Manages input mode state and suggestion generation
 */
export function useInputMode(
  options: UseInputModeOptions
): UseInputModeReturn {
  const { customCommands } = options;
  const [input, setInput] = useState("");
  const [inputMode, setInputMode] = useState<InputMode>("chat");
  const [suggestions, setSuggestions] = useState<UISuggestion[]>([]);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);
  const [suggestionScrollOffset, setSuggestionScrollOffset] = useState(0);

  // Command / mention detection + fuzzy suggestions
  useEffect(() => {
    if (input.startsWith("/")) {
      setInputMode("command");
      const query = input.slice(1);
      const customKeys = new Set(customCommands.map((c) => c.name));
      const items = [
        ...BUILT_IN_COMMANDS.map((c) => ({
          key: c.name,
          description: c.description,
          keywords: c.keywords,
          requiresValue: c.requiresValue,
        })),
        ...customCommands.map((c) => ({
          key: c.name,
          description: c.description,
        })),
      ];
      const matches = fuzzyMatch(query, items, items.length);
      const mapped: UISuggestion[] = matches.map((m) => ({
        label: m.key,
        description:
          m.description ||
          (customKeys.has(m.key)
            ? "Custom command"
            : getBuiltInDescription(m.key) || ""),
        kind: customKeys.has(m.key) ? "custom-command" : "command",
        score: m.score,
        keywords: m.keywords,
        requiresValue: m.requiresValue,
      }));
      setSuggestions(mapped);
      setSelectedSuggestionIndex(0);
      setSuggestionScrollOffset(0);
    } else if (input.startsWith("@")) {
      setInputMode("mention");
      const query = input.slice(1);
      const items = MENTIONS.map((m) => ({
        key: m.name,
        description: m.description,
      }));
      const matches = fuzzyMatch(query, items, items.length);
      const mapped: UISuggestion[] = matches.map((m) => ({
        label: m.key,
        description: m.description,
        kind: "mention",
        score: m.score,
        keywords: m.keywords,
      }));
      setSuggestions(mapped);
      setSelectedSuggestionIndex(0);
      setSuggestionScrollOffset(0);
    } else {
      setInputMode("chat");
      setSuggestions([]);
      setSelectedSuggestionIndex(0);
      setSuggestionScrollOffset(0);
    }
  }, [input, customCommands]);

  // Update scroll offset when selected index changes
  useEffect(() => {
    if (selectedSuggestionIndex < suggestionScrollOffset) {
      setSuggestionScrollOffset(selectedSuggestionIndex);
    } else if (
      selectedSuggestionIndex >=
      suggestionScrollOffset + MAX_VISIBLE_SUGGESTIONS
    ) {
      setSuggestionScrollOffset(
        selectedSuggestionIndex - MAX_VISIBLE_SUGGESTIONS + 1
      );
    }
  }, [selectedSuggestionIndex, suggestionScrollOffset]);

  // Clamp scroll offset when suggestions change
  useEffect(() => {
    const maxOffset = Math.max(0, suggestions.length - MAX_VISIBLE_SUGGESTIONS);
    setSuggestionScrollOffset((prev) => Math.min(prev, maxOffset));
  }, [suggestions.length]);

  const showSuggestionPanel = inputMode !== "chat";
  const inputAreaMinHeight = showSuggestionPanel ? 9 : 4;
  const inputAreaPaddingTop = showSuggestionPanel ? 1 : 0;

  return {
    input,
    setInput,
    inputMode,
    suggestions,
    selectedSuggestionIndex,
    setSelectedSuggestionIndex,
    suggestionScrollOffset,
    showSuggestionPanel,
    inputAreaMinHeight,
    inputAreaPaddingTop,
  };
}
