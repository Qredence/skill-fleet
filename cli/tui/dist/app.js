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
const TABS = ["chat", "skills", "jobs", "optimization"];
const TAB_NAMES = {
    chat: "💬 Chat",
    skills: "📚 Skills",
    jobs: "⚙️ Jobs",
    optimization: "🚀 Optimize",
};
export const App = ({ apiUrl, userId = "default" }) => {
    const [activeTab, setActiveTab] = useState("chat");
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
    return (React.createElement(Box, { flexDirection: "column", width: 100, height: 30 },
        React.createElement(Box, { flexDirection: "column", marginBottom: 1, paddingX: 2 },
            React.createElement(Text, { color: "cyan", bold: true }, "\uD83D\uDE80 Skills Fleet TUI"),
            React.createElement(Text, { color: "gray" }, "Real-time skill creation & optimization with streaming responses")),
        React.createElement(Box, { flexDirection: "row", marginBottom: 1, paddingX: 2 }, TABS.map((tab, idx) => (React.createElement(Box, { key: tab, marginRight: 2, borderStyle: activeTab === tab ? "round" : undefined, borderColor: activeTab === tab ? "green" : undefined, paddingX: activeTab === tab ? 1 : 0 },
            React.createElement(Text, { color: activeTab === tab ? "green" : "gray", bold: activeTab === tab },
                activeTab === tab ? "" : `${idx + 1}:`,
                TAB_NAMES[tab]))))),
        React.createElement(Box, { marginBottom: 1, paddingX: 2 },
            React.createElement(Text, { color: "gray", dimColor: true }, "Tab to switch \u2022 1-4 to jump \u2022 ? for help")),
        React.createElement(Box, { marginBottom: 1 },
            React.createElement(Text, { color: "gray" }, "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")),
        React.createElement(Box, { flexDirection: "column", flexGrow: 1, marginBottom: 1 },
            React.createElement(ChatTab, { apiUrl: apiUrl, isActive: activeTab === "chat" }),
            React.createElement(SkillsTab, { apiUrl: apiUrl, isActive: activeTab === "skills" }),
            React.createElement(JobsTab, { apiUrl: apiUrl, isActive: activeTab === "jobs" }),
            React.createElement(OptimizationTab, { apiUrl: apiUrl, isActive: activeTab === "optimization", onOptimize: (optimizer, trainset) => {
                    // Switch to jobs tab to monitor
                    setActiveTab("jobs");
                } })),
        showHelp && (React.createElement(Box, { flexDirection: "column", marginBottom: 1, paddingX: 2, borderStyle: "round", borderColor: "yellow" },
            React.createElement(Text, { color: "yellow", bold: true }, "\u2328\uFE0F Keyboard Shortcuts"),
            React.createElement(Text, { color: "yellow" }, "Tab          : Next tab"),
            React.createElement(Text, { color: "yellow" }, "Shift+Tab    : Previous tab"),
            React.createElement(Text, { color: "yellow" }, "1-4          : Jump to specific tab"),
            React.createElement(Text, { color: "yellow" }, "?            : Toggle this help"),
            React.createElement(Text, { color: "yellow" }, "Esc          : Close help"),
            React.createElement(Text, { color: "yellow" }, "Ctrl+C       : Exit application"))),
        React.createElement(Box, { marginTop: 1, paddingX: 2 },
            React.createElement(Text, { color: "gray" },
                "API: ",
                apiUrl,
                " | User: ",
                userId,
                " | Press ? for help | Ctrl+C to exit"))));
};
//# sourceMappingURL=app.js.map