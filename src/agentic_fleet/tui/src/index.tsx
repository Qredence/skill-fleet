#!/usr/bin/env bun
import { createCliRenderer } from "@opentui/core";
import { createRoot, useRenderer } from "@opentui/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getTheme } from "./themes.ts";
import type { Message, Prompt } from "./types.ts";
import { loadSettings } from "./storage.ts";
import { useAppState } from "./hooks/useAppState.ts";
import { useInputMode } from "./hooks/useInputMode.ts";
import { useStreaming } from "./hooks/useStreaming.ts";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts.ts";
import { useSettings } from "./hooks/useSettings.ts";
import { useSessions } from "./hooks/useSessions.ts";
import { executeCommand } from "./services/commandService.ts";
import { formatMessageWithMentionsAsync } from "./mentionHandlers.ts";
import { createStdoutWithDimensions, generateUniqueId } from "./utils.ts";
import { buildToolSystemPrompt } from "./tools/prompt.ts";
import {
  executeToolCall,
  formatToolResult,
  parseToolCalls,
  type ToolCall,
} from "./tools/index.ts";
import { resolveToolPermission } from "./tools/permissions.ts";
import { SessionList } from "./components/SessionList.tsx";
import { SettingsMenu } from "./components/SettingsMenu.tsx";
import { MessageList } from "./components/MessageList.tsx";
import { InputArea } from "./components/InputArea.tsx";
import { WelcomeScreen } from "./components/WelcomeScreen.tsx";
import { SuggestionList } from "./components/SuggestionList.tsx";
import { getSuggestionFooter, getInputPlaceholder, getInputHint } from "./uiHelpers.ts";
import { PromptOverlay } from "./components/PromptOverlay.tsx";
import { StatusLine } from "./components/StatusLine.tsx";

const MAX_VISIBLE_SUGGESTIONS = 8;

function App() {
  const renderer = useRenderer();
  const scrollBoxRef = useRef<any>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showNewMessagesIndicator, setShowNewMessagesIndicator] = useState(false);
  const initialLoadDoneRef = useRef(false);

  // Core application state
  const appState = useAppState();
  const {
    messages,
    setMessages,
    sessions,
    setSessions,
    currentSessionId,
    setCurrentSessionId,
    settings,
    setSettings,
    customCommands,
    setCustomCommands,
    recentSessions,
  } = appState;

  // Input mode and suggestions
  const inputMode = useInputMode({ customCommands });
  const {
    input,
    setInput,
    inputMode: currentInputMode,
    suggestions,
    selectedSuggestionIndex,
    setSelectedSuggestionIndex,
    suggestionScrollOffset,
    showSuggestionPanel,
    inputAreaMinHeight,
    inputAreaPaddingTop,
  } = inputMode;

  // Streaming state
  const streaming = useStreaming();
  const {
    isProcessing,
    spinnerFrame,
    elapsedSec,
    streamResponse,
  } = streaming;

  // Mode state
  const [mode, setMode] = useState<"standard" | "workflow">("standard");

  // Prompt state
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [promptInputValue, setPromptInputValue] = useState("");
  const [promptSelectIndex, setPromptSelectIndex] = useState(0);

  // Tool execution queue
  const [toolQueue, setToolQueue] = useState<ToolCall[] | null>(null);
  const [toolQueueIndex, setToolQueueIndex] = useState(0);
  const toolResultsRef = useRef<string[]>([]);
  const toolStepRef = useRef(0);
  const toolSignatureCountsRef = useRef<Record<string, number>>({});

  const messagesRef = useRef<Message[]>(messages);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const appendSystemMessage = useCallback(
    (content: string) => {
      setMessages((prev) => [
        ...prev,
        { id: generateUniqueId(), role: "system", content, timestamp: new Date() },
      ]);
    },
    [setMessages]
  );

  const continueWithToolResults = useCallback(() => {
    if (toolResultsRef.current.length === 0) return;
    if (isProcessing) return;
    if (mode === "workflow") {
      appendSystemMessage("Tool loop is currently only supported in standard mode.");
      toolResultsRef.current = [];
      return;
    }

    const maxSteps = settings.tools?.maxSteps ?? 4;
    if (toolStepRef.current >= maxSteps) {
      appendSystemMessage("Max tool steps reached. Please continue manually.");
      toolResultsRef.current = [];
      return;
    }

    toolStepRef.current += 1;
    const toolSummary = toolResultsRef.current.join("\n\n");
    toolResultsRef.current = [];

    const toolPrompt = buildToolSystemPrompt(settings);
    const toolSystemMessage: Message | null = toolPrompt
      ? {
          id: generateUniqueId(),
          role: "system",
          content: toolPrompt,
          timestamp: new Date(),
        }
      : null;

    const toolResultsMessage: Message = {
      id: generateUniqueId(),
      role: "system",
      content: `Tool results:\n${toolSummary}`,
      timestamp: new Date(),
    };

    const continueMessage: Message = {
      id: generateUniqueId(),
      role: "user",
      content:
        "Continue using the tool results above. If more tools are needed, request them.",
      timestamp: new Date(),
    };

    const assistantMessageId = generateUniqueId();
    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantPlaceholder]);

    const historyForApi = [
      ...(toolSystemMessage ? [toolSystemMessage] : []),
      ...messagesRef.current.filter(
        (m) =>
          !(
            m.role === "system" &&
            (m.content.startsWith("Tool ") || m.content.startsWith("Skipped tool"))
          )
      ),
      toolResultsMessage,
      continueMessage,
    ];

    streamResponse({
      messages: historyForApi,
      userInput: continueMessage.content,
      mode: "standard",
      settings,
      assistantMessageId,
      onMessageUpdate: setMessages,
      onComplete: (id) => {
        const assistant = messagesRef.current.find((m) => m.id === id);
        const toolCalls = parseToolCalls(assistant?.content || "");
        if (toolCalls.length === 0) return;
        if (!settings.tools?.enabled) {
          appendSystemMessage(
            `Tool calls detected (${toolCalls.length}). Enable with /tools on or Settings → Coding Agent.`
          );
          return;
        }
        setToolQueue(toolCalls);
        setToolQueueIndex(0);
      },
    });
  }, [appendSystemMessage, isProcessing, mode, settings, streamResponse, setMessages]);

  useEffect(() => {
    if (!toolQueue || toolQueueIndex >= toolQueue.length) {
      if (toolQueue && toolQueueIndex >= toolQueue.length) {
        setToolQueue(null);
      }
      return;
    }

    if (prompt) return;

    const call = toolQueue[toolQueueIndex]!;
    const toolOptions = {
      cwd: process.cwd(),
      maxFileBytes: settings.tools?.maxFileBytes ?? 120_000,
      maxDirEntries: settings.tools?.maxDirEntries ?? 250,
      maxOutputChars: settings.tools?.maxOutputChars ?? 12_000,
    };

    const runTool = async () => {
      const result = await executeToolCall(call, toolOptions);
      toolResultsRef.current.push(formatToolResult(result));
      appendSystemMessage(formatToolResult(result));
      setToolQueueIndex((i) => i + 1);
    };

    const signature = JSON.stringify({ tool: call.tool, args: call.args || {} });
    const count = (toolSignatureCountsRef.current[signature] || 0) + 1;
    toolSignatureCountsRef.current[signature] = count;

    const permission = resolveToolPermission({
      settings,
      call,
      cwd: toolOptions.cwd,
      isDoomLoop: count >= 3,
    });

    if (permission.mode === "deny") {
      appendSystemMessage(`Skipped tool: ${call.tool} (${permission.reason || "denied"})`);
      setToolQueueIndex((i) => i + 1);
      return;
    }

    if (permission.mode === "allow") {
      void runTool();
      return;
    }

    const argsObject = call.args || {};
    const hasArgs = Object.keys(argsObject).length > 0;
    let argsPreview = hasArgs ? JSON.stringify(argsObject, null, 2) : "no arguments";
    const MAX_PREVIEW_LENGTH = 200;
    if (argsPreview.length > MAX_PREVIEW_LENGTH) {
      argsPreview = argsPreview.slice(0, MAX_PREVIEW_LENGTH) + "…";
    }
    const permissionMessage =
      `Allow tool "${call.tool}" to run?\n` +
      `cwd: ${toolOptions.cwd}\n` +
      `args: ${argsPreview}`;

    setPrompt({
      type: "confirm",
      message: permissionMessage,
      onConfirm: () => {
        void runTool();
        setPrompt(null);
      },
      onCancel: () => {
        appendSystemMessage(`Skipped tool: ${call.tool}`);
        setToolQueueIndex((i) => i + 1);
        setPrompt(null);
      },
    });
  }, [
    toolQueue,
    toolQueueIndex,
    prompt,
    settings.tools,
    appendSystemMessage,
  ]);

  useEffect(() => {
    if (!toolQueue && toolQueueIndex > 0 && !prompt) {
      setToolQueueIndex(0);
      continueWithToolResults();
    }
  }, [toolQueue, toolQueueIndex, prompt, continueWithToolResults]);

  // Settings management
  const settingsHook = useSettings({
    settings,
    setSettings,
    setPrompt,
  });
  const {
    showSettingsMenu,
    setShowSettingsMenu,
    settingsFocusIndex,
    setSettingsFocusIndex,
    settingsSections,
    flatSettingsItems,
    handleSettingsItemActivate,
  } = settingsHook;

  // Sessions management
  const sessionsHook = useSessions({
    recentSessions,
    setMessages,
    setCurrentSessionId,
  });
  const {
    showSessionList,
    setShowSessionList,
    sessionFocusIndex,
    setSessionFocusIndex,
    handleSessionActivate,
  } = sessionsHook;

  // Theme
  const COLORS = useMemo(() => getTheme(settings.theme), [settings.theme]);

  // Initialize prompt input value when prompt opens
  useEffect(() => {
    if (prompt && prompt.type === "input") {
      setPromptInputValue(prompt.defaultValue || "");
      setPromptSelectIndex(0);
    } else if (prompt && prompt.type === "select") {
      setPromptSelectIndex(prompt.selectedIndex ?? 0);
    } else if (!prompt) {
      setPromptInputValue("");
      setPromptSelectIndex(0);
    }
  }, [prompt]);

  // Auto-scroll behavior: initial load and on append when near bottom
  useEffect(() => {
    if (!scrollBoxRef.current || messages.length === 0) return;
    if (!settings.autoScroll) return;
    const last = messages[messages.length - 1];
    const isInitial = !initialLoadDoneRef.current;
    const shouldScroll = isInitial || isAtBottom;
    if (shouldScroll) {
      setTimeout(() => { scrollBoxRef.current?.scrollToBottom?.(); }, 0);
      setShowNewMessagesIndicator(false);
      initialLoadDoneRef.current = true;
    } else {
      setShowNewMessagesIndicator(true);
    }
  }, [messages, settings.autoScroll, isAtBottom]);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    showSessionList,
    setShowSessionList,
    showSettingsMenu,
    setShowSettingsMenu,
    prompt,
    setPrompt,
    setPromptInputValue,
    recentSessions,
    sessionFocusIndex,
    setSessionFocusIndex,
    handleSessionActivate,
    settingsSections,
    flatSettingsItems,
    settingsFocusIndex,
    setSettingsFocusIndex,
    handleSettingsItemActivate,
    suggestions,
    selectedSuggestionIndex,
    setSelectedSuggestionIndex,
    inputMode: currentInputMode,
    setInput,
    mode,
    setMode,
    setMessages,
    settings,
  });

  // Command execution
  const handleExecuteCommand = useCallback(
    async (command: string, args?: string) => {
      const result = await executeCommand(command, args, {
        settings,
        sessions,
        messages,
        customCommands,
        currentSessionId,
        setSettings,
        setMessages,
        setPrompt,
        setPromptInputValue,
        setShowSettingsMenu,
        setShowSessionList,
        setMode,
        stop: () => renderer?.stop(),
      });

      if (result.shouldReturn) {
        return;
      }

      if (result.systemMessage) {
        setMessages((prev) => [...prev, result.systemMessage!]);
      }
    },
    [
      settings,
      sessions,
      messages,
      customCommands,
      currentSessionId,
      setSettings,
      setMessages,
      setPrompt,
      setPromptInputValue,
      setShowSettingsMenu,
      setShowSessionList,
      setMode,
      renderer,
    ]
  );

  // Input submission handler
  const handleSubmit = useCallback(async () => {
    if (isProcessing) return;

    // If suggestions are visible, select the highlighted suggestion
    if (
      suggestions.length > 0 &&
      (currentInputMode === "command" || currentInputMode === "mention")
    ) {
      const selected = suggestions[selectedSuggestionIndex];
      if (currentInputMode === "command" && selected) {
        handleExecuteCommand(selected.label, "");
        setInput("");
        return;
      } else if (currentInputMode === "mention" && selected) {
        setInput(`@${selected.label} `);
        return;
      }
    }

    const rawInput = input.trim();
    if (!rawInput) return;

    toolStepRef.current = 0;
    toolSignatureCountsRef.current = {};
    toolResultsRef.current = [];

    // Handle commands entered manually
    if (input.startsWith("/")) {
      const parts = input.slice(1).split(" ");
      const cmd = parts[0];
      const args = parts.slice(1).join(" ");
      if (cmd) {
        handleExecuteCommand(cmd, args);
      }
      setInput("");
      return;
    }

    // Format message with mentions if present
    const userMessage: Message = {
      id: generateUniqueId(),
      role: "user",
      content: rawInput,
      timestamp: new Date(),
    };

    // Prepare assistant message placeholder to stream into
    const assistantMessageId = generateUniqueId();
    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    // Update UI immediately
    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setInput("");

    const formattedInput = await formatMessageWithMentionsAsync(rawInput, {
      cwd: process.cwd(),
      maxFileBytes: settings.tools?.maxFileBytes ?? 120_000,
    });
    const apiUserMessage: Message = { ...userMessage, content: formattedInput };
    const toolPrompt = buildToolSystemPrompt(settings);
    const toolSystemMessage: Message | null = toolPrompt
      ? {
          id: generateUniqueId(),
          role: "system",
          content: toolPrompt,
          timestamp: new Date(),
        }
      : null;
    const historyForApi = toolSystemMessage
      ? [toolSystemMessage, ...messages, apiUserMessage]
      : [...messages, apiUserMessage];

    // Stream response
    streamResponse({
      messages: historyForApi,
      userInput: rawInput,
      mode,
      settings,
      assistantMessageId,
      onMessageUpdate: setMessages,
      onComplete: (id) => {
        const assistant = messagesRef.current.find((m) => m.id === id);
        const toolCalls = parseToolCalls(assistant?.content || "");
        if (toolCalls.length === 0) return;
        if (!settings.tools?.enabled) {
          appendSystemMessage(
            `Tool calls detected (${toolCalls.length}). Enable with /tools on or Settings → Coding Agent.`
          );
          return;
        }
        setToolQueue(toolCalls);
        setToolQueueIndex(0);
      },
    });
  }, [
    isProcessing,
    suggestions,
    selectedSuggestionIndex,
    currentInputMode,
    input,
    handleExecuteCommand,
    setInput,
    setMessages,
    messages,
    mode,
    settings,
    streamResponse,
    appendSystemMessage,
  ]);

  // Computed values
  const showWelcome = messages.length === 0;

  const suggestionFooter = useMemo(() => getSuggestionFooter(currentInputMode), [currentInputMode]);

  const inputPlaceholder = useMemo(() => getInputPlaceholder(currentInputMode, mode), [currentInputMode, mode]);

  const inputHint = useMemo(() => getInputHint(currentInputMode), [currentInputMode]);

  return (
    <box
      flexDirection="column"
      flexGrow={1}
      style={{ backgroundColor: COLORS.bg.primary }}
    >
      {/* Header removed */}

      {/* Main Content Area */}
      <scrollbox
        ref={scrollBoxRef}
        stickyScroll
        stickyStart="bottom"
        verticalScrollbarOptions={{
          onChange: () => {
            try {
              const el = scrollBoxRef.current;
              const d = (el?.scrollHeight ?? 0) - (el?.scrollTop ?? 0) - (el?.viewportHeight ?? 0);
              setIsAtBottom(d <= 2);
              if (d <= 2) setShowNewMessagesIndicator(false);
            } catch {}
          },
        }}
        style={{
          flexGrow: 1,
          paddingLeft: 1,
          paddingRight: 1,
          paddingTop: 1,
          paddingBottom: 1,
          backgroundColor: COLORS.bg.primary,
        }}
      >
        {showWelcome ? (
          <WelcomeScreen
            cwd={process.cwd().replace(process.env.HOME || "", "~")}
            colors={COLORS}
          />
        ) : (
          <MessageList
            messages={messages}
            isProcessing={isProcessing}
            spinnerFrame={spinnerFrame}
            colors={COLORS}
          />
        )}
      </scrollbox>

      {/* Session List Overlay */}
      {showSessionList && (
        <SessionList
          sessions={sessions}
          recentSessions={recentSessions}
          focusIndex={sessionFocusIndex}
          colors={COLORS}
        />
      )}

      {/* Prompt Overlay */}
      {prompt && (
        <PromptOverlay
          prompt={prompt}
          promptInputValue={promptInputValue}
          onInputChange={setPromptInputValue}
          onConfirm={() => {
            if (prompt.type !== "input") return;
            prompt.onConfirm(promptInputValue);
            setPromptInputValue("");
          }}
          promptSelectIndex={promptSelectIndex}
          onSelectIndexChange={setPromptSelectIndex}
          colors={COLORS}
        />
      )}

      {/* Settings Menu */}
      {showSettingsMenu && (
        <SettingsMenu
          sections={settingsSections}
          focusIndex={settingsFocusIndex}
          colors={COLORS}
        />
      )}

      {/* Input Area */}
      <box
        style={{
          backgroundColor: "transparent",
          border: false,
          paddingLeft: 0,
          paddingRight: 0,
          paddingTop: 0,
          paddingBottom: 0,
          flexDirection: "column",
          minHeight: 1.5,
          flexShrink: 0,
        }}
      >
        {showNewMessagesIndicator && settings.autoScroll && (
          <box style={{ justifyContent: "flex-end", paddingLeft: 1, paddingRight: 1 }}>
            <box
              style={{
                backgroundColor: COLORS.bg.hover,
                border: true,
                borderColor: COLORS.border,
                paddingLeft: 1,
                paddingRight: 1,
                paddingTop: 0,
                paddingBottom: 0,
              }}
            >
              <text content="New messages" style={{ fg: COLORS.text.secondary }} />
              <text content="  •  " style={{ fg: COLORS.text.dim }} />
              <text
                content="Scroll to bottom"
                style={{ fg: COLORS.text.primary }}
              />
            </box>
          </box>
        )}
        {/* Command/Mention Suggestions Dropdown */}
        {showSuggestionPanel && (
          <SuggestionList
            suggestions={suggestions}
            selectedIndex={selectedSuggestionIndex}
            scrollOffset={suggestionScrollOffset}
            inputMode={currentInputMode}
            input={input}
            colors={COLORS}
            maxVisible={MAX_VISIBLE_SUGGESTIONS}
          />
        )}

        {/* Input Field */}
        <InputArea
          input={input}
          inputMode={currentInputMode}
          isProcessing={isProcessing}
          isFocused={!showSettingsMenu && !showSessionList && !prompt}
          placeholder={inputPlaceholder}
          hint={inputHint}
          colors={COLORS}
          onInput={setInput}
          onSubmit={handleSubmit}
        />

        {/* Status Line */}
        <StatusLine
          isProcessing={isProcessing}
          elapsedSec={elapsedSec}
          mode={mode}
          settings={settings}
          inputMode={currentInputMode}
          suggestionFooter={suggestionFooter}
          colors={COLORS}
        />
      </box>
    </box>
  );
}

// Setup terminal with dimensions
const stdoutWithDimensions = createStdoutWithDimensions();

const argv = process.argv.slice(2);
const has = (flag: string) => argv.includes(flag);
if (has("--version")) {
  console.log("0.1.5");
  process.exit(0);
}
if (has("--help")) {
  console.log(
    [
      "Usage: qlaw [options]",
      "",
      "Options:",
      "  --help       Show this help",
      "  --version    Show version",
      "  --status     Print configuration summary",
      "",
      "Run without options to launch the interactive TUI.",
    ].join("\n")
  );
  process.exit(0);
}
if (has("--status")) {
  const s = loadSettings();
  const redacted = s.apiKey ? "****" + String(s.apiKey).slice(-4) : "(not set)";
  console.log(
    [
      `Theme: ${s.theme}`,
      `Auto-scroll: ${s.autoScroll ? "Enabled" : "Disabled"}`,
      `Model: ${s.model ?? "(not set)"}`,
      `Endpoint: ${s.endpoint ?? "(not set)"}`,
      `API Key: ${redacted}`,
      `AF Bridge: ${s.afBridgeBaseUrl ?? "(not set)"}`,
      `AF Model: ${s.afModel ?? "(not set)"}`,
      `Workflow Mode: ${s.workflow?.enabled ? "Enabled" : "Disabled"}`,
    ].join("\n")
  );
  process.exit(0);
}
try {
  const renderer = await createCliRenderer({ stdout: stdoutWithDimensions });
  createRoot(renderer).render(<App />);
} catch (e) {
  console.error("Failed to start qlaw-cli:", e instanceof Error ? e.message : e);
  process.exit(1);
}
