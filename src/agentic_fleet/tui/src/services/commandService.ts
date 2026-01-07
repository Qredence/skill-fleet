/**
 * Command service for executing commands
 * Extracted from index.tsx to improve code organization
 */

import type {
  Message,
  Session,
  AppSettings,
  CustomCommand,
} from "../types.ts";
import type { CommandContext, CommandResult } from "../commandHandlers.ts";
import {
  handleClearCommand,
  handleHelpCommand,
  handleModelCommand,
  handleProviderCommand,
  handleEndpointCommand,
  handleApiKeyCommand,
  handleSettingsCommand,
  handleSessionsCommand,
  handleStatusCommand,
  handleTerminalSetupCommand,
  handleCommandsCommand,
  handleThemeCommand,
  handleExportCommand,
  handleExitCommand,
  handlePwdCommand,
  handleCwdCommand,
  handleUnknownCommand,
  handleModeCommand,
  handleWorkflowCommand,
  handleAgentsCommand,
  handleRunCommand,
  handleContinueCommand,
  handleJudgeCommand,
  handleAfBridgeCommand,
  handleAfModelCommand,
  handleKeybindingsCommand,
  handleToolsCommand,
  handleLoginCommand,
  handleFoundryEndpointCommand,
  handleAgentCommand,
} from "../commandHandlers.ts";

export interface CommandServiceContext {
  settings: AppSettings;
  sessions: Session[];
  messages: Message[];
  customCommands: CustomCommand[];
  currentSessionId: string | null;
  setSettings: (settings: AppSettings | ((prev: AppSettings) => AppSettings)) => void;
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  setPrompt: (prompt: import("../types.ts").Prompt | null) => void;
  setPromptInputValue: (value: string) => void;
  setShowSettingsMenu: (show: boolean) => void;
  setShowSessionList: (show: boolean) => void;
  setMode?: (mode: "standard" | "workflow") => void;
  stop?: () => void;
}

/**
 * Execute a command with the given arguments
 */
export async function executeCommand(
  command: string,
  args: string | undefined,
  context: CommandServiceContext
): Promise<CommandResult> {
  const cmd = command.toLowerCase();
  const commandContext: CommandContext = {
    settings: context.settings,
    sessions: context.sessions,
    messages: context.messages,
    customCommands: context.customCommands,
    currentSessionId: context.currentSessionId,
    setSettings: context.setSettings,
    setMessages: context.setMessages,
    setPrompt: context.setPrompt,
    setPromptInputValue: context.setPromptInputValue,
    setShowSettingsMenu: context.setShowSettingsMenu,
    setShowSessionList: context.setShowSessionList,
    setMode: context.setMode,
    stop: context.stop,
  };

  switch (cmd) {
    case "clear":
      return handleClearCommand(commandContext, args);
    case "help":
      return handleHelpCommand();
    case "model":
      return handleModelCommand(args, commandContext);
    case "provider":
      return handleProviderCommand(args, commandContext);
    case "endpoint":
      return handleEndpointCommand(args, commandContext);
    case "api-key":
      return handleApiKeyCommand(args, commandContext);
    case "af-bridge":
      return handleAfBridgeCommand(args, commandContext);
    case "af-model":
      return handleAfModelCommand(args, commandContext);
    case "foundry-endpoint":
      return handleFoundryEndpointCommand(args, commandContext);
    case "login":
      return handleLoginCommand(commandContext);
    case "agent":
      return handleAgentCommand(args, commandContext);
    case "keybindings":
      return handleKeybindingsCommand(args, commandContext);
    case "tools":
      return handleToolsCommand(args, commandContext);
    case "settings":
      return handleSettingsCommand(args, commandContext);
    case "sessions":
      return handleSessionsCommand(commandContext);
    case "status":
      return handleStatusCommand(commandContext);
    case "terminal-setup":
      return handleTerminalSetupCommand();
    case "commands":
      return handleCommandsCommand(commandContext);
    case "theme":
      return handleThemeCommand(commandContext);
    case "export":
      return handleExportCommand(commandContext);
    case "exit":
    case "quit":
      commandContext.stop = context.stop;
      return handleExitCommand(commandContext);
    case "pwd":
      return handlePwdCommand();
    case "cwd":
      return handleCwdCommand(args);
    case "mode":
      return handleModeCommand(args, commandContext);
    case "workflow":
      return handleWorkflowCommand();
    case "agents":
      return handleAgentsCommand();
    case "run":
      return handleRunCommand();
    case "continue":
      return handleContinueCommand();
    case "judge":
      return handleJudgeCommand();
    default:
      return handleUnknownCommand(cmd, commandContext);
  }
}
