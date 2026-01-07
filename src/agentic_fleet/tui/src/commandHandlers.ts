import type {
  Message,
  Session,
  AppSettings,
  CustomCommand,
  ThemeName,
  Prompt,
  PromptSelectOption,
  Action,
  KeySpec,
} from "./types.ts";
import { generateUniqueId } from "./utils.ts";
import { defaultKeybindings } from "./storage.ts";
import { listAgents } from "./api.ts";
import { applyProviderDefaults } from "./llm/providerDefaults.ts";
import { parseModelList } from "./llm/models.ts";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const CUSTOM_SELECT_VALUE = "__custom__";
const AUTO_SELECT_VALUE = "__auto__";
const TOOL_PERMISSION_MAP: Record<string, string> = {
  read: "read_file",
  read_file: "read_file",
  list: "list_dir",
  list_dir: "list_dir",
  write: "write_file",
  write_file: "write_file",
  run: "run_command",
  run_command: "run_command",
  external: "external_directory",
  external_directory: "external_directory",
  doom: "doom_loop",
  doom_loop: "doom_loop",
};

function dedupeSelectOptions(options: PromptSelectOption[]): PromptSelectOption[] {
  const seen = new Set<string>();
  const deduped: PromptSelectOption[] = [];
  for (const option of options) {
    const key = option.name.trim();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    deduped.push(option);
  }
  return deduped;
}

function selectIndexForValue(options: PromptSelectOption[], value?: string): number {
  if (!value) return 0;
  const idx = options.findIndex((opt) => opt.value === value || opt.name === value);
  return idx >= 0 ? idx : 0;
}

function buildModelSelectOptions(settings: AppSettings): PromptSelectOption[] {
  const options: PromptSelectOption[] = [];
  const envModels = parseModelList(process.env.LITELLM_MODELS);
  if (settings.model) {
    options.push({ name: settings.model, description: "Current value", value: settings.model });
  }
  if (envModels.length > 0) {
    envModels.forEach((model) => {
      options.push({
        name: model,
        description: "From LITELLM_MODELS",
        value: model,
      });
    });
  }
  if (process.env.LITELLM_MODEL) {
    options.push({
      name: process.env.LITELLM_MODEL,
      description: "From LITELLM_MODEL",
      value: process.env.LITELLM_MODEL,
    });
  }
  if (process.env.OPENAI_MODEL) {
    options.push({
      name: process.env.OPENAI_MODEL,
      description: "From OPENAI_MODEL",
      value: process.env.OPENAI_MODEL,
    });
  }
  options.push({ name: "Custom…", description: "Type a custom model name", value: CUSTOM_SELECT_VALUE });
  return dedupeSelectOptions(options);
}

function buildEndpointSelectOptions(settings: AppSettings): PromptSelectOption[] {
  const options: PromptSelectOption[] = [];
  if (settings.endpoint) {
    options.push({ name: settings.endpoint, description: "Current value", value: settings.endpoint });
  }
  if (process.env.LITELLM_BASE_URL) {
    options.push({
      name: process.env.LITELLM_BASE_URL,
      description: "From LITELLM_BASE_URL",
      value: process.env.LITELLM_BASE_URL,
    });
  }
  if (process.env.OPENAI_BASE_URL) {
    options.push({
      name: process.env.OPENAI_BASE_URL,
      description: "From OPENAI_BASE_URL",
      value: process.env.OPENAI_BASE_URL,
    });
  }
  options.push({ name: "https://api.openai.com/v1", description: "OpenAI default", value: "https://api.openai.com/v1" });
  options.push({ name: "Custom…", description: "Type a custom endpoint", value: CUSTOM_SELECT_VALUE });
  return dedupeSelectOptions(options);
}

function buildApiKeySelectOptions(): PromptSelectOption[] {
  const options: PromptSelectOption[] = [];
  if (process.env.LITELLM_API_KEY) {
    options.push({
      name: "Use LITELLM_API_KEY",
      description: "Apply the LiteLLM API key from env",
      value: process.env.LITELLM_API_KEY,
    });
  }
  if (process.env.OPENAI_API_KEY) {
    options.push({
      name: "Use OPENAI_API_KEY",
      description: "Apply the OpenAI API key from env",
      value: process.env.OPENAI_API_KEY,
    });
  }
  options.push({ name: "Custom…", description: "Type a custom API key", value: CUSTOM_SELECT_VALUE });
  return dedupeSelectOptions(options);
}

function buildAfBridgeSelectOptions(settings: AppSettings): PromptSelectOption[] {
  const options: PromptSelectOption[] = [];
  if (settings.afBridgeBaseUrl) {
    options.push({
      name: settings.afBridgeBaseUrl,
      description: "Current value",
      value: settings.afBridgeBaseUrl,
    });
  }
  if (process.env.AF_BRIDGE_BASE_URL) {
    options.push({
      name: process.env.AF_BRIDGE_BASE_URL,
      description: "From AF_BRIDGE_BASE_URL",
      value: process.env.AF_BRIDGE_BASE_URL,
    });
  }
  options.push({
    name: "http://127.0.0.1:8081",
    description: "Local bridge default",
    value: "http://127.0.0.1:8081",
  });
  options.push({ name: "Custom…", description: "Type a custom bridge URL", value: CUSTOM_SELECT_VALUE });
  return dedupeSelectOptions(options);
}

function buildAfModelSelectOptions(settings: AppSettings): PromptSelectOption[] {
  const options: PromptSelectOption[] = [];
  if (settings.afModel) {
    options.push({ name: settings.afModel, description: "Current value", value: settings.afModel });
  }
  if (process.env.AF_MODEL) {
    options.push({ name: process.env.AF_MODEL, description: "From AF_MODEL", value: process.env.AF_MODEL });
  }
  options.push({
    name: "multi_tier_support",
    description: "Default bridge workflow",
    value: "multi_tier_support",
  });
  options.push({ name: "Custom…", description: "Type a custom workflow ID", value: CUSTOM_SELECT_VALUE });
  return dedupeSelectOptions(options);
}

export interface CommandContext {
  settings: AppSettings;
  sessions: Session[];
  messages: Message[];
  customCommands: CustomCommand[];
  currentSessionId: string | null;
  setSettings: (settings: AppSettings | ((prev: AppSettings) => AppSettings)) => void;
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  setPrompt: (prompt: Prompt | null) => void;
  setPromptInputValue: (value: string) => void;
  setShowSettingsMenu: (show: boolean) => void;
  setShowSessionList: (show: boolean) => void;
  setMode?: (mode: "standard" | "workflow") => void;
  stop?: () => void;
}

export interface CommandResult {
  systemMessage?: Message;
  shouldReturn?: boolean;
}

export function handleClearCommand(
  context: CommandContext,
  args?: string
): CommandResult {
  const { messages, setMessages } = context;
  const confirm = (args || "").trim().toLowerCase();
  if (messages.length === 0) {
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: "Nothing to clear",
        timestamp: new Date(),
      },
    };
  }
  if (confirm === "confirm" || confirm === "!" || confirm === "yes") {
    setMessages([]);
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: "Conversation cleared",
        timestamp: new Date(),
      },
    };
  }
  return {
    systemMessage: {
      id: generateUniqueId(),
      role: "system",
      content: "To clear, run: /clear confirm",
      timestamp: new Date(),
    },
  };
}

export function handleHelpCommand(): CommandResult {
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Help
general
  /help                Show help
  /clear [confirm]     Clear messages
  /status              Show status
  /theme               Toggle theme
  /terminal-setup      Configure terminal keys
settings
  /settings            Open settings panel
  /keybindings [...]   View or edit keybindings
ai
  /provider <name>     Set provider (openai/azure/litellm/custom)
  /model <name>        Set model
  /endpoint <url>      Set API base URL
  /api-key <key>       Set API key
  /tools [args]        Toggle tool execution (on/off/auto, perm ...)
  /af-bridge <url>     Set Agent Framework bridge
  /af-model <name>     Set Agent Framework model
foundry
  /login               Login to Azure
  /foundry-endpoint    Set Foundry Project Endpoint
  /agent               List and select Foundry Agent
workflow
  /mode <standard|workflow>  Switch mode
  /workflow            Workflow controls
  /agents              Show agents
  /run                 Start workflow
  /continue            Continue workflow
  /judge               Invoke judge
mentions
  @context  @file <path>  @code <snippet>  @docs <topic>
  @coder @planner @reviewer @judge`,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleModeCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  const desired = (args || "").trim().toLowerCase();
  let target: "standard" | "workflow" | null = null;
  if (desired === "standard" || desired === "workflow") {
    target = desired as any;
  }
  if (context.setMode) {
    if (target) {
      context.setMode(target);
    } else {
      // Toggle when no explicit arg provided
      // Fall back to a system message when mode state isn't known
      // Note: UI will reflect current mode in status bar
      context.setMode("workflow");
    }
  }
  const msg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Mode ${target ? "set" : "toggled"} to: ${target || "workflow"}`,
    timestamp: new Date(),
  };
  return { systemMessage: msg };
}

export function handleWorkflowCommand(): CommandResult {
  const msg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Workflow controls: Use /run to start, /continue to resume, /agents to view roles, and /judge to decide.`,
    timestamp: new Date(),
  };
  return { systemMessage: msg };
}

export function handleAgentsCommand(): CommandResult {
  const msg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Agents configured: coder, planner, reviewer, judge. Customize via settings (to be added).`,
    timestamp: new Date(),
  };
  return { systemMessage: msg };
}

export function handleRunCommand(): CommandResult {
  const msg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Starting workflow. Type your prompt and submit in workflow mode (use /mode workflow).`,
    timestamp: new Date(),
  };
  return { systemMessage: msg };
}

export function handleContinueCommand(): CommandResult {
  const msg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Continuing workflow. Provide follow-up input or use mentions like @reviewer or @judge.`,
    timestamp: new Date(),
  };
  return { systemMessage: msg };
}

export function handleJudgeCommand(): CommandResult {
  const msg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Judge agent ready. Summarize options and the judge will decide.`,
    timestamp: new Date(),
  };
  return { systemMessage: msg };
}

function handleSettingCommand(
  settingKey: "model" | "provider" | "endpoint" | "apiKey" | "afBridgeBaseUrl" | "afModel" | "foundryEndpoint",
  promptMessage: string,
  confirmationFormatter: (value: string) => string,
  args: string | undefined,
  context: CommandContext,
  options?: {
    shouldMaskValue?: boolean;
    placeholder?: string;
    applyValue?: (value: string, context: CommandContext) => void;
    selectOptions?: PromptSelectOption[];
  }
): CommandResult {
  const { settings, setMessages, setPrompt } = context;
  const val = args?.trim();
  const applyValue =
    options?.applyValue ||
    ((value: string, ctx: CommandContext) => {
      ctx.setSettings((prev) => ({ ...prev, [settingKey]: value }));
    });

  if (val) {
    applyValue(val, context);
    const systemMsg: Message = {
      id: generateUniqueId(),
      role: "system",
      content: confirmationFormatter(val),
      timestamp: new Date(),
    };
    return { systemMessage: systemMsg };
  }

  const storedValue = settings[settingKey];
  const displayValue = storedValue || "Not set";
  const masked =
    options?.shouldMaskValue && typeof displayValue === "string"
      ? displayValue
        ? "***" + displayValue.slice(-4)
        : "Not set"
      : displayValue;

  const openInputPrompt = () => {
    if (!setPrompt) return;
    const defaultValue =
      options?.shouldMaskValue || typeof storedValue !== "string"
        ? ""
        : storedValue;
    setPrompt({
      type: "input",
      message: `${promptMessage} (current: ${masked})`,
      defaultValue,
      placeholder: options?.placeholder || "Type and press Enter",
      onConfirm: (value: string) => {
        const trimmed = value.trim();
        if (trimmed) {
          applyValue(trimmed, context);
          if (setMessages) {
            const systemMsg: Message = {
              id: generateUniqueId(),
              role: "system",
              content: confirmationFormatter(trimmed),
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, systemMsg]);
          }
        }
        setPrompt(null);
      },
      onCancel: () => setPrompt(null),
    });
  };

  if (setPrompt && options?.selectOptions && options.selectOptions.length > 0) {
    const selectedIndex = selectIndexForValue(options.selectOptions, storedValue);
    setPrompt({
      type: "select",
      message: `${promptMessage} (current: ${masked})`,
      options: options.selectOptions,
      selectedIndex,
      onSelect: (option) => {
        if (option.value === CUSTOM_SELECT_VALUE) {
          openInputPrompt();
          return;
        }
        const resolvedValue = option.value ?? option.name;
        if (resolvedValue) {
          applyValue(resolvedValue, context);
          if (setMessages) {
            const systemMsg: Message = {
              id: generateUniqueId(),
              role: "system",
              content: confirmationFormatter(resolvedValue),
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, systemMsg]);
          }
        }
        setPrompt(null);
      },
      onCancel: () => setPrompt(null),
    });
    return { shouldReturn: true };
  }

  openInputPrompt();
  return { shouldReturn: true };

}

export function handleModelCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "model",
    "Select model:",
    (v) => `Model set to: ${v}`,
    args,
    context,
    { placeholder: "openai/gpt-4o-mini", selectOptions: buildModelSelectOptions(context.settings) }
  );
}

export function handleProviderCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "provider",
    "Select provider:",
    (v) =>
      v === AUTO_SELECT_VALUE
        ? "Provider set to: Auto (detect)"
        : `Provider set to: ${v} (defaults updated when available)`,
    args,
    context,
    {
      placeholder: "litellm",
      selectOptions: [
        { name: "Auto (detect)", description: "Let qlaw-cli infer the provider", value: AUTO_SELECT_VALUE },
        { name: "openai", description: "OpenAI Responses API", value: "openai" },
        { name: "azure", description: "Azure OpenAI", value: "azure" },
        { name: "litellm", description: "LiteLLM proxy (OpenAI-compatible)", value: "litellm" },
        { name: "custom", description: "Custom OpenAI-compatible provider", value: "custom" },
      ],
      applyValue: (value, ctx) => {
        if (value === AUTO_SELECT_VALUE) {
          ctx.setSettings((prev) => ({ ...prev, provider: undefined }));
          return;
        }
        ctx.setSettings((prev) => applyProviderDefaults(prev, value));
      },
    }
  );
}

export function handleEndpointCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "endpoint",
    "Select API endpoint base URL:",
    (v) => `Endpoint set to: ${v}`,
    args,
    context,
    { placeholder: "http://localhost:4000/v1", selectOptions: buildEndpointSelectOptions(context.settings) }
  );
}

export function handleApiKeyCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "apiKey",
    "Select API key:",
    () => "API key updated.",
    args,
    context,
    { shouldMaskValue: true, placeholder: "sk-...", selectOptions: buildApiKeySelectOptions() }
  );
}

export function handleSettingsCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  const { settings, setShowSettingsMenu } = context;
  const mode = (args || "").trim().toLowerCase();
  const shouldOpenPanel = mode === "panel" || mode === "menu" || mode === "ui" || mode === "open";
  if (shouldOpenPanel) {
    setShowSettingsMenu(true);
  }
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Settings
Model:        ${settings.model || "Not set"}
Provider:     ${settings.provider || "Auto"}
Endpoint:     ${settings.endpoint || "Not set"}
API Key:      ${settings.apiKey ? "***" + settings.apiKey.slice(-4) : "Not set"}
Theme:        ${settings.theme}
Timestamps:   ${settings.showTimestamps ? "Shown" : "Hidden"}
Auto-scroll:  ${settings.autoScroll ? "Enabled" : "Disabled"}
Tools:        ${settings.tools?.enabled ? "Enabled" : "Disabled"}
Agent Bridge: ${settings.afBridgeBaseUrl || "Not set"}
AF Model:     ${settings.afModel || "Not set"}
Workflow:     ${settings.workflow?.enabled ? "Enabled" : "Disabled"}

Use /provider, /model, /endpoint, /api-key, /theme, /keybindings, /tools, /af-bridge, /af-model to change values
Type "/settings panel" to open the interactive menu`,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleToolsCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  const { settings, setSettings } = context;
  const trimmed = (args || "").trim().toLowerCase();

  if (!trimmed) {
    const status = settings.tools?.enabled ? "Enabled" : "Disabled";
    const auto = settings.tools?.autoApprove ? "Enabled" : "Disabled";
    const perms = settings.tools?.permissions || {};
    const permSummary = [
      `read_file=${perms.read_file || "allow"}`,
      `list_dir=${perms.list_dir || "allow"}`,
      `write_file=${perms.write_file || "ask"}`,
      `run_command=${perms.run_command || "ask"}`,
      `external_directory=${perms.external_directory || "ask"}`,
      `doom_loop=${perms.doom_loop || "ask"}`,
    ].join(" ");
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `Tools: ${status}\nAuto-approve: ${auto}\nPermissions: ${permSummary}\nUsage: /tools on|off|auto [on|off]\n       /tools perm <tool> <allow|ask|deny>`,
        timestamp: new Date(),
      },
    };
  }

  const parts = trimmed.split(/\s+/);
  const sub = parts[0] || "";

  if (sub === "perm" || sub === "permission") {
    const rawTool = parts[1];
    const rawMode = parts[2];
    if (!rawTool || !rawMode) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: "Usage: /tools perm <tool> <allow|ask|deny>",
          timestamp: new Date(),
        },
      };
    }
    const toolKey = TOOL_PERMISSION_MAP[rawTool];
    if (!toolKey) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: `Unknown tool: ${rawTool}`,
          timestamp: new Date(),
        },
      };
    }
    if (!["allow", "ask", "deny"].includes(rawMode)) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: "Mode must be allow, ask, or deny.",
          timestamp: new Date(),
        },
      };
    }
    setSettings((prev) => ({
      ...prev,
      tools: {
        ...(prev.tools || {}),
        permissions: {
          ...(prev.tools?.permissions || {}),
          [toolKey]: rawMode,
        },
      },
    }));
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `Permission set: ${toolKey}=${rawMode}`,
        timestamp: new Date(),
      },
    };
  }

  if (sub === "on" || sub === "enable" || sub === "enabled") {
    setSettings((prev) => ({
      ...prev,
      tools: { ...(prev.tools || {}), enabled: true },
    }));
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: "Tools enabled.",
        timestamp: new Date(),
      },
    };
  }

  if (sub === "off" || sub === "disable" || sub === "disabled") {
    setSettings((prev) => ({
      ...prev,
      tools: { ...(prev.tools || {}), enabled: false },
    }));
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: "Tools disabled.",
        timestamp: new Date(),
      },
    };
  }

  if (sub === "auto") {
    const desired = parts[1] || "toggle";
    const nextValue =
      desired === "on"
        ? true
        : desired === "off"
        ? false
        : !(settings.tools?.autoApprove ?? false);
    setSettings((prev) => ({
      ...prev,
      tools: { ...(prev.tools || {}), autoApprove: nextValue },
    }));
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `Auto-approve ${nextValue ? "enabled" : "disabled"}.`,
        timestamp: new Date(),
      },
    };
  }

  return {
    systemMessage: {
      id: generateUniqueId(),
      role: "system",
      content: "Usage: /tools on|off|auto [on|off]",
      timestamp: new Date(),
    },
  };
}

export function handleAfBridgeCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "afBridgeBaseUrl",
    "Select Agent Framework bridge base URL:",
    (v) => `Agent Framework bridge URL set to: ${v}`,
    args,
    context,
    { selectOptions: buildAfBridgeSelectOptions(context.settings) }
  );
}

export function handleAfModelCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "afModel",
    "Select Agent Framework model identifier:",
    (v) => `Agent Framework model set to: ${v}`,
    args,
    context,
    { selectOptions: buildAfModelSelectOptions(context.settings) }
  );
}

export function handleFoundryEndpointCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  return handleSettingCommand(
    "foundryEndpoint",
    "Enter Foundry Endpoint URL:",
    (v) => `Foundry Endpoint set to: ${v}`,
    args,
    context
  );
}

export async function handleLoginCommand(context: CommandContext): Promise<CommandResult> {
    const { setMessages } = context;
    const msg: Message = { id: generateUniqueId(), role: "system", content: "Initiating Azure login via browser...", timestamp: new Date() };
    setMessages((prev) => [...prev, msg]);

    try {
        const { stdout } = await execAsync("az login");
        return {
            systemMessage: {
                id: generateUniqueId(),
                role: "system",
                content: `Login successful.\n${stdout}`,
                timestamp: new Date()
            }
        };
    } catch (e: unknown) {
        let errorMessage: string;
        if (e instanceof Error) {
            errorMessage = e.message;
        } else {
            errorMessage = String(e);
        }
        return {
            systemMessage: {
                id: generateUniqueId(),
                role: "system",
                content: `Login failed: ${errorMessage}. Ensure Azure CLI is installed (az).`,
                timestamp: new Date()
            }
        };
    }
}

export async function handleAgentCommand(
    args: string | undefined,
    context: CommandContext
): Promise<CommandResult> {
    const { settings, setSettings, setPrompt, setMessages } = context;
    const bridgeUrl = settings.afBridgeBaseUrl;
    const foundryEndpoint = settings.foundryEndpoint;

    if (!bridgeUrl) {
         return { systemMessage: { id: generateUniqueId(), role: "system", content: "Error: Bridge URL not set (/af-bridge)", timestamp: new Date() } };
    }
    if (!foundryEndpoint) {
         return { systemMessage: { id: generateUniqueId(), role: "system", content: "Error: Foundry Endpoint not set (/foundry-endpoint)", timestamp: new Date() } };
    }

    try {
        const msg: Message = { id: generateUniqueId(), role: "system", content: "Fetching agents...", timestamp: new Date() };
        setMessages((prev) => [...prev, msg]);

        const agents = await listAgents(bridgeUrl, foundryEndpoint);

        if (agents.length === 0) {
            return { systemMessage: { id: generateUniqueId(), role: "system", content: "No agents found.", timestamp: new Date() } };
        }

        const listStr = agents.map((a, i) => `${i + 1}. ${a.name} (${a.model}) - ID: ${a.id}`).join("\n");

        setPrompt({
            type: "input",
            message: "Enter Agent ID (from above):",
            onConfirm: (val) => {
                const selected = val.trim();
                if (selected) {
                    setSettings(prev => ({ ...prev, afModel: selected, mode: "workflow" }));
                    const confirmMsg: Message = {
                         id: generateUniqueId(), role: "system", content: `Agent set to: ${selected}. Switched to Workflow mode.`, timestamp: new Date()
                    };
                    setMessages(prev => [...prev, confirmMsg]);
                    setPrompt(null);
                }
            },
            onCancel: () => setPrompt(null)
        });

        return {
            systemMessage: {
                id: generateUniqueId(),
                role: "system",
                content: `Foundry Agents:\n${listStr}`,
                timestamp: new Date()
            }
        };

    } catch (e: unknown) {
        let errorMsg = "Unknown error";
        if (typeof e === "object" && e !== null && "message" in e && typeof (e as { message?: unknown }).message === "string") {
            errorMsg = (e as { message: string }).message;
        } else if (typeof e === "string") {
            errorMsg = e;
        }
        return { systemMessage: { id: generateUniqueId(), role: "system", content: `Error fetching agents: ${errorMsg}`, timestamp: new Date() } };
    }
}

const ACTION_LABELS: Record<Action, string> = {
  nextSuggestion: "Next suggestion",
  prevSuggestion: "Previous suggestion",
  autocomplete: "Autocomplete",
};

function formatKeySpec(spec: KeySpec): string {
  const parts: string[] = [];
  if (spec.ctrl) parts.push("Ctrl");
  if (spec.alt) parts.push("Alt");
  if (spec.shift) parts.push("Shift");
  const normalized = spec.name || "";
  const titleCase =
    normalized.length <= 1
      ? normalized.toUpperCase()
      : `${normalized.charAt(0).toUpperCase()}${normalized.slice(1)}`;
  const nameLabel = titleCase || normalized;
  parts.push(nameLabel);
  return parts.join("+");
}

function cloneKeybindings(bindings: Record<Action, KeySpec[]>): Record<Action, KeySpec[]> {
  const entries = Object.entries(bindings).map(([action, specs]) => [action, specs.map((spec) => ({ ...spec }))]);
  return Object.fromEntries(entries) as Record<Action, KeySpec[]>;
}

function parseKeySpec(input: string): KeySpec | null {
  const parts = input
    .split("+")
    .map((p) => p.trim().toLowerCase())
    .filter(Boolean);
  if (parts.length === 0) return null;
  const spec: KeySpec = { name: "" } as KeySpec;
  for (const part of parts) {
    if (part === "ctrl" || part === "control") {
      spec.ctrl = true;
      continue;
    }
    if (part === "alt" || part === "option") {
      spec.alt = true;
      continue;
    }
    if (part === "shift") {
      spec.shift = true;
      continue;
    }
    if (!spec.name) {
      spec.name = part;
    } else {
      return null;
    }
  }
  return spec.name ? spec : null;
}

export function handleKeybindingsCommand(
  args: string | undefined,
  context: CommandContext
): CommandResult {
  const { settings, setSettings } = context;
  const trimmed = (args || "").trim();

  if (!trimmed) {
    const summary = (Object.keys(ACTION_LABELS) as Action[])
      .map((action) => {
        const bindings = settings.keybindings[action] || [];
        const formatted = bindings.length > 0 ? bindings.map(formatKeySpec).join(", ") : "(not set)";
        return `${ACTION_LABELS[action]} (${action}): ${formatted}`;
      })
      .join("\n");
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `Keybindings\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n${summary}\n\nUse /keybindings set <action> <binding> (e.g., /keybindings set nextSuggestion ctrl+n)\nUse /keybindings reset to restore defaults`,
        timestamp: new Date(),
      },
    };
  }

  const parts = trimmed.split(/\s+/);
  const subcommandRaw = parts.shift() ?? "";
  const subcommand = subcommandRaw.toLowerCase();

  if (subcommand === "reset") {
    setSettings((prev) => ({
      ...prev,
      keybindings: cloneKeybindings(defaultKeybindings),
    }));
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: "Keybindings reset to defaults",
        timestamp: new Date(),
      },
    };
  }

  if (subcommand === "set") {
    const actionName = parts.shift();
    if (!actionName) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: `Usage: /keybindings set <action> <binding>\nActions: ${Object.keys(ACTION_LABELS).join(", ")}`,
          timestamp: new Date(),
        },
      };
    }
    const action = actionName as Action;
    if (!ACTION_LABELS[action]) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: `Unknown action: ${actionName}\nActions: ${Object.keys(ACTION_LABELS).join(", ")}`,
          timestamp: new Date(),
        },
      };
    }
    const bindingString = parts.join(" ").trim();
    if (!bindingString) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: "Provide a binding, e.g., ctrl+n or shift+tab",
          timestamp: new Date(),
        },
      };
    }

    const combos = bindingString
      .split(",")
      .map((token) => token.trim())
      .filter(Boolean)
      .map((token) => parseKeySpec(token))
      .filter((spec): spec is KeySpec => !!spec);

    if (combos.length === 0) {
      return {
        systemMessage: {
          id: generateUniqueId(),
          role: "system",
          content: "Invalid binding. Use format ctrl+k or shift+tab, separate multiples with commas.",
          timestamp: new Date(),
        },
      };
    }

    setSettings((prev) => ({
      ...prev,
      keybindings: {
        ...prev.keybindings,
        [action]: combos,
      },
    }));

    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `${ACTION_LABELS[action]} updated to: ${combos.map(formatKeySpec).join(", ")}`,
        timestamp: new Date(),
      },
    };
  }

  return {
    systemMessage: {
      id: generateUniqueId(),
      role: "system",
      content: `Unknown keybindings command: ${subcommand}. Use /keybindings set|reset`,
      timestamp: new Date(),
    },
  };
}

export function handleSessionsCommand(
  context: CommandContext
): CommandResult {
  const { sessions, setShowSessionList } = context;
  setShowSessionList(true);
  let content: string;
  if (sessions.length === 0) {
    content = `Sessions\nNo saved sessions yet. Start a conversation to create one.`;
  } else {
    const summary = sessions
      .slice(-5)
      .map(
        (s, idx) => `${idx + 1}. ${s.name} (${s.messages.length} msgs, ${new Date(s.updatedAt).toLocaleDateString()})`
      )
      .join("\n");
    content = `Sessions\nOverlay opened. Use ↑↓ then Enter to resume.\n${summary}${sessions.length > 5 ? "\n…plus more (showing latest 5)" : ""}`;
  }
  return {
    systemMessage: { id: generateUniqueId(), role: "system", content, timestamp: new Date() },
  };
}

export function handleStatusCommand(
  context: CommandContext
): CommandResult {
  const { settings, sessions, messages, customCommands } = context;
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Current Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model:        ${settings.model || "Not set"}
Provider:     ${settings.provider || "Auto"}
Endpoint:     ${settings.endpoint || "Not set"}
API Key:      ${settings.apiKey ? "***" + settings.apiKey.slice(-4) : "Not set"}
Theme:        ${settings.theme}
Timestamps:   ${settings.showTimestamps ? "Shown" : "Hidden"}
Auto-scroll:  ${settings.autoScroll ? "Enabled" : "Disabled"}
Tools:        ${settings.tools?.enabled ? "Enabled" : "Disabled"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sessions:     ${sessions.length} saved
Messages:     ${messages.length} in current chat
Custom Cmds:  ${customCommands.length} defined`,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleTerminalSetupCommand(): CommandResult {
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Terminal Keybindings Setup:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For multiline input support:

VS Code / Cursor / Windsurf:
  Add to keybindings.json:
  {
    "key": "shift+enter",
    "command": "workbench.action.terminal.sendSequence",
    "args": { "text": "\\n" }
  }

Windows Terminal:
  Add to settings.json:
  {
    "command": { "action": "sendInput", "input": "\\n" },
    "keys": "shift+enter"
  }

Current shortcuts:
  Ctrl+C / Esc  - Exit
  Ctrl+K        - Toggle debug console`,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleCommandsCommand(
  context: CommandContext
): CommandResult {
  const { customCommands } = context;
  let content: string;
  
  if (customCommands.length === 0) {
    content = `Custom Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No custom commands defined yet.

To add a command, use:
/commands add <name> <description> <command>

Example:
/commands add git-status "Show git status" "git status"`;
  } else {
    const cmdList = customCommands
      .map(
        (c, i) =>
          `${i + 1}. /${c.name}\n   ${c.description}\n   → ${c.command}`
      )
      .join("\n\n");
    content = `Custom Commands:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n${cmdList}\n\nUse: /commands remove <name>`;
  }
  
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleThemeCommand(
  context: CommandContext
): CommandResult {
  const { settings, setSettings } = context;
  const order: ThemeName[] = ["dark", "light", "dracula"];
  const idx = order.indexOf(settings.theme as ThemeName);
  const next = idx === -1 ? "dark" : order[(idx + 1) % order.length];
  const newTheme: ThemeName = next as ThemeName;
  setSettings((prev) => ({ ...prev, theme: newTheme }));
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Theme changed to: ${newTheme}`,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleExportCommand(
  context: CommandContext
): CommandResult {
  const { messages, settings, currentSessionId } = context;
  const exportData = {
    session: {
      id: currentSessionId || "current",
      exportedAt: new Date().toISOString(),
    },
    messages,
    settings,
  };
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content: `Chat export:\n${JSON.stringify(exportData, null, 2)}`,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}

export function handleUnknownCommand(
  command: string,
  context: CommandContext
): CommandResult {
  const { customCommands } = context;
  const customCmd = customCommands.find((c) => c.name === command.toLowerCase());
  
  let content: string;
  if (customCmd) {
    content = `Executing: ${customCmd.command}\n(Custom command execution not yet implemented)`;
  } else {
    content = `Unknown command: /${command}\nType /help for available commands`;
  }
  
  const systemMsg: Message = {
    id: generateUniqueId(),
    role: "system",
    content,
    timestamp: new Date(),
  };
  return { systemMessage: systemMsg };
}
export function handleExitCommand(context: CommandContext): CommandResult {
  context.stop?.();
  return { shouldReturn: true };
}

export function handlePwdCommand(): CommandResult {
  const path = process.cwd().replace(process.env.HOME || "", "~");
  return {
    systemMessage: {
      id: generateUniqueId(),
      role: "system",
      content: `cwd: ${path}`,
      timestamp: new Date(),
    },
  };
}

export function handleCwdCommand(args: string | undefined): CommandResult {
  const dest = (args || "").trim();
  if (!dest) {
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: "Usage: /cwd <directory>",
        timestamp: new Date(),
      },
    };
  }
  try {
    process.chdir(dest);
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `Changed directory to ${process.cwd()}`,
        timestamp: new Date(),
      },
    };
  } catch (e: any) {
    return {
      systemMessage: {
        id: generateUniqueId(),
        role: "system",
        content: `Failed to change directory: ${e?.message || e}`,
        timestamp: new Date(),
      },
    };
  }
}
