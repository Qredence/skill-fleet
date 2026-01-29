import React, { useState, useCallback, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import SelectInput from "ink-select-input";
import {
  StreamingClient,
  ThinkingChunk,
  ResponseChunk,
} from "../streaming-client.js";
import { CommandExecutor } from "../commands/executor.js";
import { HITLPrompt } from "./hitl-prompt.js";
import { useHitl } from "../hooks/use-hitl.js";
import { useHitlConfig } from "../hooks/use-hitl-config.js";
import { addKnownJob } from "../utils/state-store.js";
import { detectAction } from "../utils/hitl-keywords.js";
import { Header } from "./Header.js";
import { MessageList } from "./MessageList.js";
import { InputArea } from "./InputArea.js";
import { CommandOverlay } from "./CommandOverlay.js";

interface Message {
  id: string;
  role: "user" | "assistant" | "thinking" | "system";
  content: string;
  step?: number;
  thinking_type?: string;
  timestamp?: string;
}

interface ChatLayoutProps {
  apiUrl: string;
}

interface MainMenuOption {
  key: string;
  label: string;
  value: string;
  description: string;
}

const MAIN_MENU_OPTIONS: MainMenuOption[] = [
  {
    key: "create",
    label: "🎯 Create Skill",
    value: "create",
    description: "Create a new skill with guided workflow",
  },
  {
    key: "list",
    label: "📚 List Skills",
    value: "list",
    description: "Browse existing skills in the taxonomy",
  },
  {
    key: "optimize",
    label: "🚀 Optimize",
    value: "optimize",
    description: "Optimize DSPy workflow prompts",
  },
  {
    key: "evaluate",
    label: "📊 Evaluate",
    value: "evaluate",
    description: "Evaluate skill quality",
  },
];

function formatThinkingChunk(chunk: ThinkingChunk): string {
  const icons: Record<string, string> = {
    thought: "💭",
    reasoning: "🤔",
    internal: "⚙️",
    thinking: "💡",
    step: "▶️",
  };
  const icon = icons[chunk.type] || "•";
  // Just return content for now, styling handled in MessageList
  return chunk.content;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({ apiUrl }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showMainMenu, setShowMainMenu] = useState(true);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [showThinking, setShowThinking] = useState(true);
  const [showOverlay, setShowOverlay] = useState(false);

  // Fetch HITL configuration from API (stays in sync with backend)
  const { keywords: hitlKeywords } = useHitlConfig({
    apiUrl,
    enabled: true,
  });

  // Toggle thinking with T
  useInput((input, key) => {
    if (input.toLowerCase() === "t" && !showOverlay && key.ctrl === false) {
      // Only toggle if not typing in input?
      // Actually checking raw input might conflict with text input.
      // Better to rely on command /think
    }

    if (key.escape) {
      setShowOverlay(false);
      // Return to main menu if no active job
      if (!activeJobId && !isLoading) {
        setShowMainMenu(true);
      }
    }
  });

  const hitl = useHitl({
    apiUrl,
    jobId: activeJobId,
    enabled: activeJobId !== null,
    pollInterval: 1500,
    onComplete: (result) => {
      addMessage(
        "system",
        `✅ Job completed! Draft saved to: ${result.draft_path || "unknown"}`,
      );
      setActiveJobId(null);
      setShowMainMenu(true);
    },
    onError: (error) => {
      addMessage("system", `❌ Job failed: ${error}`);
      setActiveJobId(null);
      setShowMainMenu(true);
    },
    onPrompt: (prompt) => {
      // Add a message indicating what kind of input is expected
      const typeMessages: Record<string, string> = {
        clarify: "🤔 Clarification needed - please answer the question above",
        confirm: "📋 Please confirm the understanding (proceed/revise/cancel)",
        preview: "👁️ Review the preview (proceed/revise/cancel)",
        validate: "✅ Review validation (proceed/revise/cancel)",
        deep_understanding: "🔍 Please share more details about your goals",
      };
      const msg =
        typeMessages[prompt.type || ""] || `⏳ HITL prompt (${prompt.type})`;
      addMessage("system", msg);
    },
  });

  const streamingClient = new StreamingClient();
  const commandExecutor = new CommandExecutor({
    apiUrl,
    onProgress: (msg) => {
      addMessage("thinking", `⏳ ${msg}`);
    },
  });

  const getNextMessageId = useCallback((prefix: string = "msg") => {
    const hasCryptoRandomUUID =
      typeof globalThis !== "undefined" &&
      typeof (globalThis as any).crypto !== "undefined" &&
      typeof (globalThis as any).crypto.randomUUID === "function";

    const uniquePart = hasCryptoRandomUUID
      ? (globalThis as any).crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    return `${prefix}-${uniquePart}`;
  }, []);

  const addMessage = (role: Message["role"], content: string) => {
    const id = getNextMessageId(role === "thinking" ? "think" : "msg");
    setMessages((prev) => [
      ...prev,
      {
        id,
        role,
        content,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
  };

  const handleHitlSubmit = useCallback(
    async (response: Record<string, any>) => {
      const success = await hitl.submitResponse(response);
      if (success) {
        addMessage("system", "✓ Response submitted, continuing...");
      }
    },
    [hitl],
  );

  const handleCommandSelect = (item: { label: string; value: string }) => {
    setShowOverlay(false);
    setInput(item.value + " "); // Add space for args
  };

  const handleMainMenuSelect = async (item: {
    label: string;
    value: string;
  }) => {
    setShowMainMenu(false);

    switch (item.value) {
      case "create":
        addMessage(
          "system",
          "🎯 What skill would you like to create? Describe what you need:",
        );
        break;
      case "list":
        addMessage("system", "📚 Fetching skills...");
        await handleCommand("/list");
        break;
      case "optimize":
        addMessage("system", "🚀 Starting optimization workflow...");
        await handleCommand("/optimize");
        break;
      case "evaluate":
        addMessage(
          "system",
          "📊 Enter skill path to evaluate (e.g., skills/python/async):",
        );
        break;
    }
  };

  const handleSubmit = async (value: string) => {
    if (!value.trim() || isLoading) return;
    const msg = value.trim();

    // Command
    if (msg.startsWith("/")) {
      if (msg === "/think") {
        setShowThinking(!showThinking);
        addMessage(
          "system",
          `Thinking display ${!showThinking ? "ON" : "OFF"}`,
        );
        setInput("");
        return;
      }
      if (msg === "/clear") {
        setMessages([]);
        setInput("");
        return;
      }
      await handleCommand(msg);
      return;
    }

    // If there's an active HITL prompt waiting for input, route to HITL response
    if (hitl.isWaitingForInput && hitl.prompt) {
      addMessage("user", msg);
      setInput("");
      setIsLoading(true);

      // Determine response format based on prompt type
      let response: Record<string, any>;

      if (hitl.prompt.type === "clarify") {
        // For clarify prompts, send as answer text
        response = { answers: { response: msg } };
      } else if (
        hitl.prompt.type === "confirm" ||
        hitl.prompt.type === "preview" ||
        hitl.prompt.type === "validate"
      ) {
        // For action prompts, detect user intent using API-configured keywords
        // This ensures the UI stays in sync if the backend changes accepted keywords
        const action = detectAction(msg, hitlKeywords);

        if (action === "revise") {
          response = { action: "revise", feedback: msg };
        } else {
          response = { action };
        }
      } else {
        // Generic response
        response = { answers: { response: msg } };
      }

      const success = await hitl.submitResponse(response);
      if (success) {
        addMessage("system", "✓ Response submitted, continuing...");
      } else {
        addMessage("system", "❌ Failed to submit response");
      }
      setIsLoading(false);
      return;
    }

    await handleStreamingChat(msg);
  };

  const handleCommand = async (command: string) => {
    addMessage("user", command);
    setInput("");
    setIsLoading(true);

    try {
      const result = await commandExecutor.execute(command);
      addMessage("assistant", result.message);

      if (result.jobId) {
        setActiveJobId(result.jobId);
        addKnownJob(result.jobId);
        hitl.startPolling(result.jobId);
      }
    } catch (error) {
      addMessage(
        "assistant",
        `❌ Command failed: ${error instanceof Error ? error.message : String(error)}`,
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleStreamingChat = async (message: string) => {
    addMessage("user", message);
    setInput("");
    setIsLoading(true);

    try {
      // Detect if this is a skill creation request
      const skillKeywords = [
        "create skill",
        "make skill",
        "build skill",
        "new skill",
        "i want",
        "i need",
        "skill for",
      ];
      const isSkillRequest = skillKeywords.some((kw) =>
        message.toLowerCase().includes(kw),
      );

      if (isSkillRequest) {
        // Route to skill creation workflow (HITL-enabled)
        addMessage("system", "🚀 Starting skill creation workflow...");

        try {
          const response = await fetch(`${apiUrl}/api/v1/skills/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              task_description: message,
              user_id: "default",
            }),
          });

          if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
          }

          const data = (await response.json()) as {
            job_id?: string;
            status?: string;
          };

          if (data.job_id) {
            setActiveJobId(data.job_id);
            addKnownJob(data.job_id);
            hitl.startPolling(data.job_id);
            addMessage(
              "system",
              `✅ Job created: ${data.job_id}\n⏳ Waiting for HITL prompts...`,
            );
          }
        } catch (error) {
          addMessage(
            "assistant",
            `❌ Failed to create skill: ${error instanceof Error ? error.message : String(error)}`,
          );
        }

        setIsLoading(false);
        return;
      }

      // Otherwise, use generic streaming chat
      let assistantMessage = "";

      await streamingClient.streamChat({
        apiUrl,
        message,
        onThinking: (chunk: ThinkingChunk) => {
          setMessages((prev) => {
            const newId = getNextMessageId("think");
            return [
              ...prev,
              {
                id: newId,
                role: "thinking",
                content: chunk.content, // Raw content for parser
                thinking_type: chunk.type,
                timestamp: new Date().toLocaleTimeString(),
              },
            ];
          });
        },
        onResponse: (chunk: ResponseChunk) => {
          assistantMessage += chunk.content;
          setMessages((prev) => {
            const updated = [...prev];
            const lastAss = updated
              .reverse()
              .find((m) => m.role === "assistant");
            if (lastAss) {
              lastAss.content = assistantMessage;
            } else {
              // Create new if not found (shouldn't happen usually if we init one)
              updated.unshift({
                id: getNextMessageId(),
                role: "assistant",
                content: assistantMessage,
                timestamp: new Date().toLocaleTimeString(),
              });
            }
            return updated.reverse();
          });
        },
        onError: (err) => addMessage("assistant", `Error: ${err}`),
        onComplete: () => setIsLoading(false),
      });

      if (!assistantMessage) {
        // If interaction was purely thinking or empty
        // Ensure we have an assistant message?
      }
    } catch (error) {
      addMessage("assistant", `Error: ${error}`);
      setIsLoading(false);
    }
  };

  // Filter messages based on thinking mode
  const visibleMessages = messages.filter(
    (m) => showThinking || m.role !== "thinking",
  );
  const showHitl = hitl.isWaitingForInput && hitl.prompt;

  return (
    <Box flexDirection="column" height="100%" paddingX={0}>
      <Header explainMode={showThinking} />

      <MessageList messages={visibleMessages} />

      {showMainMenu && !isLoading && (
        <Box
          flexDirection="column"
          borderStyle="round"
          borderColor="cyan"
          padding={1}
          marginBottom={1}
        >
          <Text bold color="cyan">
            🛠️ Skill Fleet - What would you like to do?
          </Text>
          <Text dimColor>
            Use ↑↓ to navigate, Enter to select, Esc to return here
          </Text>
          <Box marginTop={1}>
            <SelectInput
              items={MAIN_MENU_OPTIONS}
              onSelect={handleMainMenuSelect}
              itemComponent={({ isSelected, label }) => (
                <Text color={isSelected ? "cyan" : undefined} bold={isSelected}>
                  {isSelected ? "❯ " : "  "}
                  {label}
                </Text>
              )}
            />
          </Box>
        </Box>
      )}

      {showHitl && hitl.prompt && (
        <Box borderStyle="single" borderColor="yellow" padding={1}>
          <HITLPrompt
            prompt={hitl.prompt}
            onSubmit={handleHitlSubmit}
            onCancel={() => {}}
          />
        </Box>
      )}

      {showOverlay && <CommandOverlay onSelect={handleCommandSelect} />}

      <InputArea
        input={input}
        onChange={(val) => {
          setInput(val);
          if (val === "/") setShowOverlay(true);
          // Simple heuristic: if backspace removed /, close overlay
          if (showOverlay && !val.startsWith("/")) setShowOverlay(false);
        }}
        onSubmit={handleSubmit}
        isReady={!isLoading}
      />
    </Box>
  );
};
