/**
 * HITL Action Keywords
 *
 * Centralized keywords for HITL (Human-In-The-Loop) intent detection.
 * These keywords are used to parse user responses for action prompts
 * (proceed, revise, cancel).
 *
 * This ensures the UI stays in sync if the backend changes accepted keywords.
 * In the future, these can be fetched from the API's HITL configuration endpoint.
 */

export interface ActionKeywords {
  proceed: string[];
  revise: string[];
  cancel: string[];
}

/**
 * Default HITL action keywords
 *
 * These keywords are matched case-insensitively against user input.
 * The order matters: keywords are checked in the order they appear.
 */
export const HITL_ACTION_KEYWORDS: ActionKeywords = {
  proceed: [
    "proceed",
    "yes",
    "ok",
    "okay",
    "continue",
    "approve",
    "accept",
    "save",
    "y",
  ],
  revise: ["revise", "change", "edit", "modify", "fix", "update"],
  cancel: ["cancel", "abort", "stop", "quit", "no", "n"],
};

/**
 * Detect action from user input using configured keywords
 *
 * @param input - User input text
 * @param keywords - Action keywords to match against (defaults to HITL_ACTION_KEYWORDS)
 * @returns Detected action: "proceed", "revise", or "cancel"
 *
 * @example
 * const action = detectAction("yes please");
 * // Returns: "proceed"
 *
 * const action = detectAction("i want to change this");
 * // Returns: "revise"
 */
export function detectAction(
  input: string,
  keywords: ActionKeywords = HITL_ACTION_KEYWORDS
): "proceed" | "revise" | "cancel" {
  const lowerInput = input.toLowerCase();

  // Check in priority order: revise -> cancel -> proceed (default)
  // Use word boundary matching to avoid false positives (e.g., "y" in "maybe")
  const priorityOrder: Array<"revise" | "cancel" | "proceed"> = [
    "revise",
    "cancel",
    "proceed",
  ];

  for (const action of priorityOrder) {
    const keywordList = keywords[action];
    if (
      keywordList.some((kw) =>
        // Match whole word boundaries or substring for common words
        // e.g., match "yes" but not "y" in "maybe"
        new RegExp(`\\b${kw}\\b`, "i").test(lowerInput)
      )
    ) {
      return action;
    }
  }

  // Default to proceed if no keywords match
  return "proceed";
}

/**
 * Get help text for HITL actions
 *
 * Provides user-friendly guidance on what keywords to use.
 *
 * @param keywords - Action keywords to display (defaults to HITL_ACTION_KEYWORDS)
 * @returns Help text formatted for display
 *
 * @example
 * console.log(getHITLHelpText());
 * // Outputs:
 * // Proceed: yes, ok, continue, save
 * // Revise: change, edit, modify
 * // Cancel: no, quit, abort
 */
export function getHITLHelpText(
  keywords: ActionKeywords = HITL_ACTION_KEYWORDS
): string {
  return (
    `Proceed: ${keywords.proceed.slice(0, 4).join(", ")} (and more)` +
    `\nRevise: ${keywords.revise.join(", ")}` +
    `\nCancel: ${keywords.cancel.join(", ")}`
  );
}

/**
 * Check if a keyword is valid for a specific action
 *
 * @param keyword - Keyword to check
 * @param action - Action to check against
 * @param keywords - Action keywords to check (defaults to HITL_ACTION_KEYWORDS)
 * @returns True if keyword matches the action
 *
 * @example
 * isValidKeyword("yes", "proceed");
 * // Returns: true
 *
 * isValidKeyword("no", "proceed");
 * // Returns: false
 */
export function isValidKeyword(
  keyword: string,
  action: "proceed" | "revise" | "cancel",
  keywords: ActionKeywords = HITL_ACTION_KEYWORDS
): boolean {
  return keywords[action].includes(keyword.toLowerCase());
}
