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

export const DARK: ThemeTokens = {
  bg: {
    primary: "#1A1A1A",
    secondary: "#232323",
    panel: "#2A2A2A",
    hover: "#333333",
  },
  text: {
    primary: "#FFFFFF",
    secondary: "#B8B8B8",
    tertiary: "#888888",
    dim: "#666666",
    accent: "#D4A574",
  },
  border: "#3A3A3A",
  success: "#7AC47A",
  error: "#E57373",
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
