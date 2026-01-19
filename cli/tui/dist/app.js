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
    // Handle keyboard input for tab switching
    useEffect(() => {
        const handleKeyPress = (key) => {
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
    return (React.createElement(Box, { flexDirection: "column", width: 100, height: 30 },
        React.createElement(Box, { flexDirection: "column", marginBottom: 1, paddingX: 2 },
            React.createElement(Text, { color: "cyan", bold: true }, "\uD83D\uDE80 Skills Fleet TUI"),
            React.createElement(Text, { color: "gray" }, "Real-time skill creation & optimization with streaming responses")),
        React.createElement(Box, { flexDirection: "row", marginBottom: 1, paddingX: 2 }, TABS.map((tab) => (React.createElement(Box, { key: tab, marginRight: 3, borderStyle: activeTab === tab ? "round" : undefined, borderColor: activeTab === tab ? "green" : undefined, paddingX: activeTab === tab ? 1 : 0 },
            React.createElement(Text, { color: activeTab === tab ? "green" : "gray", bold: activeTab === tab }, TAB_NAMES[tab]))))),
        React.createElement(Box, { marginBottom: 1 },
            React.createElement(Text, { color: "gray" }, "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")),
        React.createElement(Box, { flexDirection: "column", flexGrow: 1, marginBottom: 1 },
            activeTab === "chat" && (React.createElement(ChatTab, { apiUrl: apiUrl, isActive: activeTab === "chat" })),
            activeTab === "skills" && (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
                React.createElement(Text, { color: "blue", bold: true }, "\uD83D\uDCDA Skills Manager"),
                React.createElement(Text, { color: "gray" }, "[Coming soon - Browse, validate, and promote skills]"),
                React.createElement(Text, { color: "gray" }, "Commands: /list, /validate, /promote, /delete"))),
            activeTab === "jobs" && (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
                React.createElement(Text, { color: "blue", bold: true }, "\u2699\uFE0F Job Monitor"),
                React.createElement(Text, { color: "gray" }, "[Coming soon - Monitor running optimization jobs]"),
                React.createElement(Text, { color: "gray" }, "Commands: /status, /cancel, /results"))),
            activeTab === "optimization" && (React.createElement(Box, { flexDirection: "column", paddingX: 2 },
                React.createElement(Text, { color: "blue", bold: true }, "\uD83D\uDE80 Optimization Control"),
                React.createElement(Text, { color: "gray" }, "[Coming soon - Configure and run optimizers]"),
                React.createElement(Text, { color: "gray" }, "Commands: /optimize, /list-optimizers, /configure")))),
        showHelp && (React.createElement(Box, { flexDirection: "column", marginBottom: 1, paddingX: 2 },
            React.createElement(Text, { color: "yellow", bold: true }, "\u2328\uFE0F Keyboard Shortcuts"),
            React.createElement(Text, { color: "yellow" }, "Tab / Ctrl+Tab : Switch tabs"),
            React.createElement(Text, { color: "yellow" }, "Alt+1-4 : Jump to tab"),
            React.createElement(Text, { color: "yellow" }, "? : Toggle this help"),
            React.createElement(Text, { color: "yellow" }, "Ctrl+C : Exit"))),
        React.createElement(Box, { marginTop: 1, paddingX: 2 },
            React.createElement(Text, { color: "gray" },
                "API: ",
                apiUrl,
                " | User: ",
                userId,
                " | Press ? for help | Ctrl+C to exit"))));
};
//# sourceMappingURL=app.js.map