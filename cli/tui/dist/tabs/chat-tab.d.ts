/**
 * Chat Tab Component for Skills Fleet TUI
 *
 * Features:
 * - Real-time streaming of assistant responses
 * - Thinking/reasoning display (colored output)
 * - Intent detection and action suggestions
 * - Command parsing (/optimize, /list, /validate, etc.)
 */
import React from "react";
interface ChatTabProps {
    apiUrl: string;
    isActive: boolean;
}
export declare const ChatTab: React.FC<ChatTabProps>;
export {};
