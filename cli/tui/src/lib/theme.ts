/**
 * Shared theme constants for the TUI.
 *
 * All colors use hex notation (OpenTUI does not support rgba/hsla).
 * Import this in components instead of duplicating THEME objects.
 */
export const THEME = {
  background: "#000000",
  panel: "#0a0a0a",
  panelAlt: "#121212",
  border: "#2a2a2a",
  accent: "#22c55e",
  text: "#e5e5e5",
  muted: "#737373",
  error: "#ef4444",
  success: "#22c55e",
} as const;

export type Theme = typeof THEME;

/**
 * Subset of THEME used by most leaf components (no background/success).
 */
export type ComponentTheme = Pick<
  Theme,
  "panel" | "panelAlt" | "border" | "accent" | "text" | "muted" | "error"
>;
