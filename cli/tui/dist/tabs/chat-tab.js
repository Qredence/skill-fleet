/**
 * Chat Tab Component for Skills Fleet TUI
 *
 * Features:
 * - Real-time streaming of assistant responses
 * - Thinking/reasoning display (colored output)
 * - Intent detection and action suggestions
 * - Command parsing (/optimize, /list, /validate, etc.)
 */
import React, { useState } from "react";
import { Box, Text } from "ink";
import TextInput from "ink-text-input";
import { StreamingClient } from "../streaming-client.js";
import { CommandExecutor } from "../commands/executor.js";
/**
 * Format thinking content with colors
 */
function formatThinkingChunk(chunk) {
    const icons = {
        thought: "💭",
        reasoning: "🤔",
        internal: "⚙️",
        thinking: "💡",
        step: "▶️",
    };
    const icon = icons[chunk.type] || "•";
    return `${icon} [${chunk.type}] ${chunk.content}`;
}
export const ChatTab = ({ apiUrl, isActive }) => {
    const [input, setInput] = useState("");
    const [messageIdCounter, setMessageIdCounter] = useState(1); // Start at 1 to avoid conflict with welcome-0
    const [messages, setMessages] = useState([
        {
            id: "welcome-0",
            role: "assistant",
            content: "Welcome to Skills Fleet TUI! 🚀\nType your request (e.g., 'optimize my last skill' or '/help') and I'll assist you.\nI'll show you my thinking process as I generate responses.",
        },
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const streamingClient = new StreamingClient();
    const commandExecutor = new CommandExecutor({
        apiUrl,
        onProgress: (msg) => {
            setMessages((prev) => [
                ...prev,
                { id: `progress-${Date.now()}`, role: "thinking", content: `⏳ ${msg}` },
            ]);
        },
    });
    const getNextMessageId = () => {
        const id = `msg-${messageIdCounter}`;
        setMessageIdCounter(messageIdCounter + 1);
        return id;
    };
    const handleSubmit = async (message) => {
        if (!message.trim() || isLoading)
            return;
        // Check if it's a command
        if (message.startsWith('/')) {
            return await handleCommand(message);
        }
        // Otherwise, use streaming assistant
        return await handleStreamingChat(message);
    };
    const handleCommand = async (command) => {
        // Add user command
        setMessages((prev) => [
            ...prev,
            { id: getNextMessageId(), role: "user", content: command },
        ]);
        setInput("");
        setIsLoading(true);
        setSuggestions([]);
        try {
            const result = await commandExecutor.execute(command);
            setMessages((prev) => [
                ...prev,
                {
                    id: getNextMessageId(),
                    role: "assistant",
                    content: result.message,
                },
            ]);
            // Generate context-aware suggestions
            if (result.jobId) {
                setSuggestions([`/status ${result.jobId}`, '/list', '/help']);
            }
            else if (command.startsWith('/list')) {
                setSuggestions(['/validate skills/...', '/optimize', '/help']);
            }
            else {
                setSuggestions(['/list', '/optimize', '/help']);
            }
            setIsLoading(false);
        }
        catch (error) {
            setMessages((prev) => [
                ...prev,
                {
                    id: getNextMessageId(),
                    role: "assistant",
                    content: `❌ Command failed: ${error instanceof Error ? error.message : String(error)}`,
                },
            ]);
            setIsLoading(false);
        }
    };
    const handleStreamingChat = async (message) => {
        // Add user message
        setMessages((prev) => [
            ...prev,
            { id: getNextMessageId(), role: "user", content: message },
        ]);
        setInput("");
        setIsLoading(true);
        setSuggestions([]);
        try {
            let assistantMessage = "";
            const thinkingSteps = [];
            await streamingClient.streamChat({
                apiUrl,
                message,
                onThinking: (chunk) => {
                    // Add thinking chunk to messages
                    setMessages((prev) => [
                        ...prev,
                        {
                            id: `think-${Date.now()}-${Math.random()}`,
                            role: "thinking",
                            content: formatThinkingChunk(chunk),
                            step: chunk.step,
                            thinking_type: chunk.type,
                        },
                    ]);
                    thinkingSteps.push(chunk.content);
                },
                onResponse: (chunk) => {
                    // Accumulate response chunks
                    assistantMessage += chunk.content;
                    // Update last assistant message with accumulated content
                    setMessages((prev) => {
                        const updated = [...prev];
                        const lastAssistant = updated.reverse().find((m) => m.role === "assistant");
                        if (lastAssistant) {
                            lastAssistant.content = assistantMessage;
                        }
                        return updated.reverse();
                    });
                },
                onError: (error) => {
                    setMessages((prev) => [
                        ...prev,
                        { id: getNextMessageId(), role: "assistant", content: `❌ Error: ${error}` },
                    ]);
                },
                onComplete: () => {
                    // Generate suggestions based on message
                    generateSuggestions(message);
                    setIsLoading(false);
                },
            });
            // Add final assistant message if empty
            if (!assistantMessage) {
                setMessages((prev) => [
                    ...prev,
                    {
                        id: getNextMessageId(),
                        role: "assistant",
                        content: "Got your message! How can I help with your skills?",
                    },
                ]);
            }
        }
        catch (error) {
            setMessages((prev) => [
                ...prev,
                {
                    id: getNextMessageId(),
                    role: "assistant",
                    content: `❌ Failed to process message: ${error instanceof Error ? error.message : String(error)}`,
                },
            ]);
            setIsLoading(false);
        }
    };
    const generateSuggestions = (message) => {
        const lowerMsg = message.toLowerCase();
        const suggested = [];
        // Keyword-based suggestions
        if (lowerMsg.includes("optimize") ||
            lowerMsg.includes("improve") ||
            lowerMsg.includes("run")) {
            suggested.push("/optimize reflection_metrics trainset_v4.json");
            suggested.push("/status");
        }
        else if (lowerMsg.includes("create") ||
            lowerMsg.includes("new skill")) {
            suggested.push("Describe your skill in more detail");
            suggested.push("/validate");
        }
        else if (lowerMsg.includes("list") ||
            lowerMsg.includes("show skills")) {
            suggested.push("/list --filter python");
            suggested.push("/list --filter optimization");
        }
        else if (lowerMsg.includes("validate")) {
            suggested.push("/validate skills/python/async");
            suggested.push("/promote <job_id>");
        }
        // Always suggest help
        if (suggested.length === 0) {
            suggested.push("/help");
            suggested.push("/list");
        }
        setSuggestions(suggested.slice(0, 3));
    };
    if (!isActive) {
        return null;
    }
    // Calculate visible height (approximate)
    const maxMessages = 15;
    const visibleMessages = messages.slice(-maxMessages);
    return (React.createElement(Box, { flexDirection: "column", width: 80, height: 24 },
        React.createElement(Box, { flexDirection: "column", marginBottom: 1, flexGrow: 1, overflowY: "hidden" }, visibleMessages.map((msg) => {
            let prefix = "";
            let color = "cyan";
            if (msg.role === "user") {
                prefix = "You: ";
                color = "cyan";
            }
            else if (msg.role === "thinking") {
                color = "gray";
                prefix = "";
            }
            else if (msg.role === "assistant") {
                prefix = "Assistant: ";
                color = "green";
            }
            return (React.createElement(Box, { key: msg.id, flexDirection: "column", marginBottom: 1 },
                React.createElement(Text, { color: color },
                    prefix,
                    msg.content)));
        })),
        suggestions.length > 0 && !isLoading && (React.createElement(Box, { flexDirection: "column", marginBottom: 1, borderStyle: "single", borderColor: "yellow", paddingX: 1 },
            React.createElement(Text, { color: "yellow", bold: true }, "\uD83D\uDCA1 Suggested next steps:"),
            suggestions.map((sugg, idx) => (React.createElement(Text, { key: `suggestion-${idx}-${sugg.substring(0, 10)}`, color: "yellow" },
                "\u2022 ",
                sugg))))),
        isLoading && (React.createElement(Box, { marginBottom: 1 },
            React.createElement(Text, { color: "blue" }, "\u23F3 Processing..."))),
        React.createElement(Box, { flexDirection: "row", paddingX: 1 },
            React.createElement(Text, { color: "blue" }, "> "),
            React.createElement(TextInput, { value: input, onChange: setInput, onSubmit: handleSubmit, placeholder: "Type your request..." })),
        React.createElement(Box, { marginTop: 1 },
            React.createElement(Text, { color: "gray" }, "Commands: /help, /optimize, /list, /validate, /status, /promote"))));
};
//# sourceMappingURL=chat-tab.js.map