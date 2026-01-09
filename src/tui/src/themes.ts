export type ThemeName = "dark" | "light" | "dracula";

export interface ThemeTokens {
  bg: {
    primary: string;
    secondary: string;
    panel: string;
    hover: string;
  };
  text: {
    primary: string;
    secondary: string;
    tertiary: string;
    dim: string;
    accent: string;
  };
  border: string;
  success: string;
  error: string;
}

export const SKILLS_FLEET_THEME: ThemeTokens = {
  bg: {
    primary: "#1E1E1E", // Main background (Dark Gray like VS Code)
    secondary: "#252526", // Sidebar/Panel background
    panel: "#252526", // Popups/Command Palette
    hover: "#2A2D2E", // List item hover
  },
  text: {
    primary: "#CCCCCC", // Main text
    secondary: "#C586C0", // Secondary text (used for some headers/labels) - using Purple for contrast
    tertiary: "#858585", // Meta text
    dim: "#606060", // Dim text
    accent: "#D7BA7D", // Gold/Orange accent
  },
  border: "#454545",
  success: "#89D185", // Green
  error: "#F48771", // Red
};

export const DARK: ThemeTokens = {
  bg: {
    primary: "#1E1E1E",
    secondary: "#252526",
    panel: "#252526",
    hover: "#2A2D2E",
  },
  text: {
    primary: "#CCCCCC",
    secondary: "#9CDCFE", // Light Blue
    tertiary: "#858585",
    dim: "#606060",
    accent: "#D7BA7D",
  },
  border: "#454545",
  success: "#89D185",
  error: "#F48771",
};

export const LIGHT: ThemeTokens = {
  bg: {
    primary: "#FFFFFF",
    secondary: "#F7F7F7",
    panel: "#F2F2F2",
    hover: "#EAEAEA",
  },
  text: {
    primary: "#1A1A1A",
    secondary: "#333333",
    tertiary: "#555555",
    dim: "#777777",
    accent: "#C47C3A",
  },
  border: "#DDDDDD",
  success: "#2E7D32",
  error: "#C62828",
};

export const DRACULA: ThemeTokens = {
  bg: {
    primary: "#282A36",
    secondary: "#2E3141",
    panel: "#343746",
    hover: "#3D4052",
  },
  text: {
    primary: "#F8F8F2",
    secondary: "#E2E2DC",
    tertiary: "#CFCFC9",
    dim: "#9EA0A6",
    accent: "#BD93F9",
  },
  border: "#44475A",
  success: "#50FA7B",
  error: "#FF5555",
};

export function getTheme(name: ThemeName): ThemeTokens {
  if (name === "light") return LIGHT;
  if (name === "dracula") return DRACULA;
  return DARK;
}
