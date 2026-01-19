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

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import { ChatTab } from "./tabs/chat-tab.js";
import { SkillsTab } from "./tabs/skills-tab.js";
import { JobsTab } from "./tabs/jobs-tab.js";
import { OptimizationTab } from "./tabs/optimization-tab.js";

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

  // Handle keyboard input for tab switching using Ink's useInput
  useInput((input, key) => {
    // Tab: next tab
    if (key.tab) {
      const currentIdx = TABS.indexOf(activeTab);
      const nextIdx = (currentIdx + 1) % TABS.length;
      setActiveTab(TABS[nextIdx]);
      return;
    }

    // Shift+Tab: previous tab
    if (key.shift && key.tab) {
      const currentIdx = TABS.indexOf(activeTab);
      const prevIdx = (currentIdx - 1 + TABS.length) % TABS.length;
      setActiveTab(TABS[prevIdx]);
      return;
    }

    // Number keys (1-4): Jump to specific tab
    if (input >= "1" && input <= "4") {
      const idx = parseInt(input) - 1;
      if (idx < TABS.length) {
        setActiveTab(TABS[idx]);
      }
      return;
    }

    // ?: Toggle help
    if (input === "?") {
      setShowHelp(!showHelp);
      return;
    }

    // Escape: Close help
    if (key.escape && showHelp) {
      setShowHelp(false);
    }
  });

  return (
    <Box flexDirection="column" height="100%" paddingY={1}>
      {/* Header */}
      <Box flexDirection="column" paddingX={2}>
        <Text color="cyan" bold>
          🚀 Skills Fleet TUI
        </Text>
        <Text color="gray">
          Real-time skill creation & optimization with streaming responses
        </Text>
      </Box>

      {/* Tab Navigation */}
      <Box flexDirection="row" marginBottom={1} paddingX={2}>
        {TABS.map((tab, idx) => (
          <Box
            key={tab}
            marginRight={2}
            borderStyle={activeTab === tab ? "round" : undefined}
            borderColor={activeTab === tab ? "green" : undefined}
            paddingX={activeTab === tab ? 1 : 0}
          >
            <Text
              color={activeTab === tab ? "green" : "gray"}
              bold={activeTab === tab}
            >
              {activeTab === tab ? "" : `${idx + 1}:`}{TAB_NAMES[tab]}
            </Text>
          </Box>
        ))}
      </Box>

      {/* Tab Navigation Hint */}
      <Box marginBottom={1} paddingX={2}>
        <Text color="gray" dimColor>
          Tab to switch • 1-4 to jump • ? for help
        </Text>
      </Box>

      {/* Tab Content - Fills available space */}
      <Box flexDirection="column" flexGrow={1} overflow="hidden" marginY={1}>
        <ChatTab apiUrl={apiUrl} isActive={activeTab === "chat"} />
        <SkillsTab apiUrl={apiUrl} isActive={activeTab === "skills"} />
        <JobsTab apiUrl={apiUrl} isActive={activeTab === "jobs"} />
        <OptimizationTab
          apiUrl={apiUrl}
          isActive={activeTab === "optimization"}
          onOptimize={(optimizer, trainset) => {
            // Switch to jobs tab to monitor
            setActiveTab("jobs");
          }}
        />
      </Box>

      {/* Help Section */}
      {showHelp && (
        <Box flexDirection="column" marginBottom={1} paddingX={2} borderStyle="round" borderColor="yellow">
          <Text color="yellow" bold>
            ⌨️ Keyboard Shortcuts
          </Text>
          <Text color="yellow">Tab          : Next tab</Text>
          <Text color="yellow">Shift+Tab    : Previous tab</Text>
          <Text color="yellow">1-4          : Jump to specific tab</Text>
          <Text color="yellow">?            : Toggle this help</Text>
          <Text color="yellow">Esc          : Close help</Text>
          <Text color="yellow">Ctrl+C       : Exit application</Text>
        </Box>
      )}

      {/* Footer */}
      <Box paddingX={2} paddingY={1}>
        <Text color="gray" wrap="truncate-end">
          API: {apiUrl} | User: {userId} | Press ? for help | Ctrl+C to exit
        </Text>
      </Box>
    </Box>
  );
};
