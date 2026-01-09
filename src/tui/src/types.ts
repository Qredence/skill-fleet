export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export interface Session {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export type ThemeName = "dark" | "light" | "dracula";
export type LlmProvider = "openai" | "azure" | "litellm" | "custom";
export type PermissionMode = "allow" | "ask" | "deny";

export type Action = "nextSuggestion" | "prevSuggestion" | "autocomplete";

export interface KeySpec {
  name: string; // e.g. "up", "down", "tab", "k"
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
}

export interface AppSettings {
  apiKey?: string;
  endpoint?: string;
  model?: string;
  provider?: LlmProvider | string;
  theme: ThemeName;
  showTimestamps: boolean;
  autoScroll: boolean;
  version: number;
  keybindings: Record<Action, KeySpec[]>;
  // Agent Framework bridge settings
  afBridgeBaseUrl?: string;
  afModel?: string;
  foundryEndpoint?: string;
  workflow?: {
    enabled?: boolean;
    defaultAgents?: {
      coder?: string;
      planner?: string;
      reviewer?: string;
      judge?: string;
    };
    keybindings?: {
      toggleMode?: KeySpec[];
      start?: KeySpec[];
      pause?: KeySpec[];
      resume?: KeySpec[];
    };
    options?: {
      maxSteps?: number;
      judgeThreshold?: number;
    };
  };
  tools?: {
    enabled?: boolean;
    autoApprove?: boolean;
    maxFileBytes?: number;
    maxDirEntries?: number;
    maxOutputChars?: number;
    maxSteps?: number;
    permissions?: {
      read_file?: PermissionMode;
      list_dir?: PermissionMode;
      write_file?: PermissionMode;
      run_command?: PermissionMode;
      external_directory?: PermissionMode;
      doom_loop?: PermissionMode;
    };
  };
}

export interface CustomCommand {
  id: string;
  name: string;
  description: string;
  command: string;
}

export type WorkflowStep = "understand" | "plan" | "initialize" | "edit" | "package" | "validate";
export type StepStatus = "pending" | "running" | "completed" | "failed";

export interface WorkflowState {
  steps: Record<WorkflowStep, StepStatus>;
  activeStep: WorkflowStep | null;
  currentIteration: number;
  maxIterations: number;
  qualityScore?: number;
}

export type InputMode = "chat" | "command" | "mention" | "settings-menu";

export type PaneType = "chat" | "artifact";
export type ArtifactMode = "none" | "catalog" | "preview" | "report" | "log";

export interface UIState {
  activePane: PaneType;
  artifactMode: ArtifactMode;
  showArtifact: boolean;
  leftPaneWidth: number | string; // e.g. "50%"
}

export type UISuggestion = {
  label: string;
  description?: string;
  kind: "command" | "custom-command" | "mention";
  score?: number;
  // Optional keywords to improve fuzzy matching relevance.
  keywords?: string[];
  requiresValue?: boolean;
};

export type PromptSelectOption = {
  name: string;
  description?: string;
  value?: string;
};

export type Prompt =
  | {
      type: "confirm";
      message: string;
      onConfirm: () => void;
      onCancel?: () => void;
    }
  | {
      type: "select";
      message: string;
      options: PromptSelectOption[];
      selectedIndex?: number;
      onSelect: (option: PromptSelectOption, index: number) => void;
      onCancel?: () => void;
    }
  | {
      type: "input";
      message: string;
      defaultValue?: string;
      placeholder?: string;
      onConfirm: (value: string) => void;
      onCancel?: () => void;
    };
