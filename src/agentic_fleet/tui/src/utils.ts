/**
 * Utility functions for terminal and common operations
 */

// Counter for fallback ID generation to ensure uniqueness within the same millisecond
let idCounter = 0;

/**
 * Generates a unique ID using crypto.randomUUID() if available,
 * otherwise falls back to a timestamp + counter + random combination
 */
export function generateUniqueId(): string {
  // Try to use crypto.randomUUID() if available (Node.js 14.17+, Bun, modern browsers)
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    try {
      return crypto.randomUUID();
    } catch {
      // Fall through to fallback if randomUUID fails
    }
  }

  // Fallback: timestamp + counter + random component for uniqueness
  const timestamp = Date.now();
  const counter = ++idCounter;
  const random = Math.random().toString(36).substring(2, 11);
  return `${timestamp}-${counter}-${random}`;
}

/**
 * Gets terminal dimensions, with fallback to defaults
 * Note: This function is synchronous and uses defaults if dimensions can't be detected
 */
export function getTerminalDimensions(): { width: number; height: number } {
  let terminalWidth = process.stdout.columns || 80;
  let terminalHeight = process.stdout.rows || 24;

  // If dimensions are already available, use them
  if (process.stdout.columns && process.stdout.rows) {
    return { width: terminalWidth, height: terminalHeight };
  }

  // Try to get dimensions from stty synchronously (fallback to defaults if fails)
  // Only attempt on Unix-like systems (not Windows)
  if (process.platform !== "win32") {
    try {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const { execSync } = require("child_process");
      const size = execSync("stty size", {
        encoding: "utf-8",
        stdio: ["inherit", "pipe", "ignore"],
      })
        .trim()
        .split(" ");
      if (size.length === 2 && size[0] && size[1]) {
        terminalHeight = parseInt(size[0], 10) || 24;
        terminalWidth = parseInt(size[1], 10) || 80;
      }
    } catch {
      // Use defaults - this is fine for non-interactive contexts
    }
  }

  return { width: terminalWidth, height: terminalHeight };
}

/**
 * Creates a stdout stream with dimensions, wrapping if needed
 */
export function createStdoutWithDimensions(): NodeJS.WriteStream {
  const { width, height } = getTerminalDimensions();

  if (process.stdout.columns && process.stdout.rows) {
    return process.stdout;
  }

  return Object.assign(Object.create(process.stdout), {
    columns: width,
    rows: height,
    isTTY: process.stdout.isTTY ?? true,
    write: process.stdout.write.bind(process.stdout),
    end: process.stdout.end.bind(process.stdout),
  });
}

/**
 * Debounces a function - delays execution until after wait milliseconds have elapsed
 * since the last time it was invoked. Useful for reducing frequent operations like saves.
 * @param fn Function to debounce
 * @param wait Milliseconds to wait before executing
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function debounced(...args: Parameters<T>) {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, wait);
  };
}

