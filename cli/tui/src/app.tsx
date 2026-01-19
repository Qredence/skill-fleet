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

import React, { useEffect, useState } from "react";
import { Box, Text } from "ink";
import { ChatTab } from "./tabs/chat-tab";

interface AppProps {
  apiUrl: string;
  userId?: string;
}

type TabName = "chat" | "skills" | "jobs" | "optimization";

const TABS: TabName[] = ["chat", "skills", "jobs", "optimization"];
const TAB_NAMES: Record<TabName, string> = {
  chat: "💬 Chat",
  skills: "📚 Skills",
  jobs: "⚙️ Jobs",
  optimization: "🚀 Optimize",
};

export const App: React.FC<AppProps> = ({ apiUrl, userId = "default" }) => {
  const [activeTab, setActiveTab] = useState<TabName>("chat");
  const [showHelp, setShowHelp] = useState(false);

  // Handle keyboard input for tab switching
  useEffect(() => {
    const handleKeyPress = (key: string) => {
      // Ctrl+Tab: next tab
      if (key === "\x09") {
        const currentIdx = TABS.indexOf(activeTab);
        const nextIdx = (currentIdx + 1) % TABS.length;
        setActiveTab(TABS[nextIdx]);
        return;
      }

      // Ctrl+Shift+Tab: previous tab (not standard but nice to have)
      if (key === "\x1b[Z") {
        const currentIdx = TABS.indexOf(activeTab);
        const prevIdx = (currentIdx - 1 + TABS.length) % TABS.length;
        setActiveTab(TABS[prevIdx]);
        return;
      }

      // Alt+1-4: Jump to specific tab
      if (key >= "1" && key <= "4") {
        const idx = parseInt(key) - 1;
        if (idx < TABS.length) {
          setActiveTab(TABS[idx]);
        }
      }

      // ?: Toggle help
      if (key === "?") {
        setShowHelp(!showHelp);
      }
    };

    // This would require proper stdin handling in a real app
    // For now, we'll use process.stdin if available
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(true);
      process.stdin.on("data", (buf) => {
        handleKeyPress(buf.toString());
      });
    }

    return () => {
      if (process.stdin.isTTY) {
        process.stdin.setRawMode(false);
      }
    };
  }, [activeTab, showHelp]);

  return (
    <Box flexDirection="column" width={100} height={30}>
      {/* Header */}
      <Box
        flexDirection="column"
        marginBottom={1}
        paddingX={2}
        borderStyle="round"
        borderColor="cyan"
      >
        <Text color="cyan" bold fontSize={16}>
          🚀 Skills Fleet TUI
        </Text>
        <Text color="gray" fontSize={10}>
          Real-time skill creation & optimization with streaming responses
        </Text>
      </Box>

      {/* Tab Navigation */}
      <Box flexDirection="row" marginBottom={1} paddingX={2}>
        {TABS.map((tab) => (
          <Box
            key={tab}
            marginRight={3}
            borderStyle={activeTab === tab ? "round" : undefined}
            borderColor={activeTab === tab ? "green" : undefined}
            paddingX={activeTab === tab ? 1 : 0}
          >
            <Text
              color={activeTab === tab ? "green" : "gray"}
              bold={activeTab === tab}
            >
              {TAB_NAMES[tab]}
            </Text>
          </Box>
        ))}
      </Box>

      {/* Tab Divider */}
      <Box
        width={100}
        marginBottom={1}
        borderStyle="horizontal"
        borderColor="gray"
      />

      {/* Tab Content */}
      <Box flexDirection="column" flexGrow={1} marginBottom={1}>
        {activeTab === "chat" && (
          <ChatTab apiUrl={apiUrl} isActive={activeTab === "chat"} />
        )}

        {activeTab === "skills" && (
          <Box flexDirection="column" paddingX={2}>
            <Text color="blue" bold>
              📚 Skills Manager
            </Text>
            <Text color="gray" marginTop={1}>
              [Coming soon - Browse, validate, and promote skills]
            </Text>
            <Text color="gray" marginTop={2}>
              Commands: /list, /validate, /promote, /delete
            </Text>
          </Box>
        )}

        {activeTab === "jobs" && (
          <Box flexDirection="column" paddingX={2}>
            <Text color="blue" bold>
              ⚙️ Job Monitor
            </Text>
            <Text color="gray" marginTop={1}>
              [Coming soon - Monitor running optimization jobs]
            </Text>
            <Text color="gray" marginTop={2}>
              Commands: /status, /cancel, /results
            </Text>
          </Box>
        )}

        {activeTab === "optimization" && (
          <Box flexDirection="column" paddingX={2}>
            <Text color="blue" bold>
              🚀 Optimization Control
            </Text>
            <Text color="gray" marginTop={1}>
              [Coming soon - Configure and run optimizers]
            </Text>
            <Text color="gray" marginTop={2}>
              Commands: /optimize, /list-optimizers, /configure
            </Text>
          </Box>
        )}
      </Box>

      {/* Help Section */}
      {showHelp && (
        <Box flexDirection="column" marginBottom={1} paddingX={2} borderStyle="round" borderColor="yellow">
          <Text color="yellow" bold>
            ⌨️ Keyboard Shortcuts
          </Text>
          <Text color="yellow">Tab / Ctrl+Tab : Switch tabs</Text>
          <Text color="yellow">Alt+1-4 : Jump to tab</Text>
          <Text color="yellow">? : Toggle this help</Text>
          <Text color="yellow">Ctrl+C : Exit</Text>
        </Box>
      )}

      {/* Footer */}
      <Box
        width={100}
        marginTop={1}
        paddingX={2}
        borderStyle="horizontal"
        borderColor="gray"
      >
        <Text color="gray" fontSize={9}>
          API: {apiUrl} | User: {userId} | Press ? for help | Ctrl+C to exit
        </Text>
      </Box>
    </Box>
  );
};
