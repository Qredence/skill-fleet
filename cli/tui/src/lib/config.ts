/**
 * Environment configuration with runtime validation.
 * Validates and provides typed access to environment variables.
 */

/**
 * Expected environment variables for the TUI.
 */
export interface TuiEnv {
  /** API URL for the Skill Fleet backend */
  SKILL_FLEET_API_URL: string;
  /** User ID for job creation */
  SKILL_FLEET_USER_ID: string;
}

const DEFAULT_API_URL = "http://localhost:8000";
const DEFAULT_USER_ID = "default";

/**
 * Sanitize user ID to prevent terminal escape sequences.
 * Only allows alphanumeric, dash, underscore; max 64 chars.
 */
export function sanitizeUserId(input: string): string {
  const sanitized = input.replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 64);
  return sanitized || DEFAULT_USER_ID;
}

/**
 * Validate and normalize API URL.
 * Removes trailing slash and ensures it's a valid URL.
 */
export function validateApiUrl(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) return DEFAULT_API_URL;

  const normalized = trimmed.replace(/\/$/, "");

  // Basic URL validation
  try {
    if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(normalized)) {
      const withScheme = `http://${normalized}`;
      new URL(withScheme);
      return withScheme;
    }
    new URL(normalized);
    return normalized;
  } catch {
    console.warn(`Invalid API URL "${input}", using default: ${DEFAULT_API_URL}`);
    return DEFAULT_API_URL;
  }
}

/**
 * Get validated environment configuration.
 * Falls back to defaults for missing or invalid values.
 */
export function getEnvConfig(): TuiEnv {
  const rawApiUrl = process.env.SKILL_FLEET_API_URL || DEFAULT_API_URL;
  const rawUserId = process.env.SKILL_FLEET_USER_ID || DEFAULT_USER_ID;

  return {
    SKILL_FLEET_API_URL: validateApiUrl(rawApiUrl),
    SKILL_FLEET_USER_ID: sanitizeUserId(rawUserId),
  };
}

/**
 * Singleton instance of validated environment config.
 * Use this for consistent access throughout the app.
 */
let _envConfig: TuiEnv | null = null;

export function getConfig(): TuiEnv {
  if (!_envConfig) {
    _envConfig = getEnvConfig();
  }
  return _envConfig;
}
