/**
 * Main Ink.js TUI Application for Skills Fleet
 *
 * Features:
 * - Tabbed interface (Chat, Skills, Jobs, Optimization)
 * - Real-time streaming of assistant responses
 * - Thinking/reasoning visualization
 * - Intent detection and command execution
 * - Real-time job monitoring
 */
import React from "react";
interface AppProps {
    apiUrl: string;
    userId?: string;
}
export declare const App: React.FC<AppProps>;
export {};
