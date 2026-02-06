/**
 * Sanitize content before rendering to prevent terminal escape sequence injection.
 *
 * AI-generated content may contain ANSI escape codes (CSI sequences, OSC commands,
 * etc.) that could manipulate the terminal — e.g. moving the cursor, clearing the
 * screen, or changing the window title.
 *
 * This module strips such sequences so that only safe text reaches the renderer.
 */

/**
 * Regex matching ANSI escape sequences:
 *  - CSI (Control Sequence Introducer): ESC [ ... final_byte
 *  - OSC (Operating System Command): ESC ] ... ST
 *  - Simple two-byte sequences: ESC + single char
 *  - Raw C0/C1 control chars except \n, \r, \t (which are valid in text)
 */
const ANSI_ESCAPE_RE =
  // biome-ignore lint: regex is intentionally complex for security
  /(\x1B\[[0-9;]*[A-Za-z]|\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)|\x1B[^[\]()]|[\x00-\x08\x0B\x0C\x0E-\x1F\x7F])/g;

/**
 * Strip ANSI/terminal escape sequences from a string.
 *
 * Preserves `\n`, `\r`, and `\t` since those are legitimate whitespace.
 */
export function stripAnsiEscapes(input: string): string {
  if (!input) return input;
  return input.replace(ANSI_ESCAPE_RE, "");
}
