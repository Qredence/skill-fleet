/**
 * Main Ink.js TUI Application for Skills Fleet
 *
 * Features:
 * - Unified Chat Interface (Qlaus-style)
 * - Real-time streaming
 * - Slash commands
 */

import React from "react";
import { Box } from "ink";
import { ChatLayout } from "./components/ChatLayout.js";

interface AppProps {
  apiUrl: string;
  userId?: string;
}

export const App: React.FC<AppProps> = ({ apiUrl, userId = "default" }) => {
  return (
    <Box flexDirection="column" height="100%">
      <ChatLayout apiUrl={apiUrl} />
    </Box>
  );
};
