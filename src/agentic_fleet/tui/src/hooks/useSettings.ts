/**
 * Hook for managing settings UI state and interactions
 * Extracted from index.tsx to improve code organization
 */

import { useState, useMemo, useCallback } from "react";
import type { AppSettings, Prompt } from "../types.ts";
import { applyProviderDefaults } from "../llm/providerDefaults.ts";

export interface UseSettingsReturn {
  showSettingsMenu: boolean;
  setShowSettingsMenu: (show: boolean) => void;
  settingsFocusIndex: number;
  setSettingsFocusIndex: React.Dispatch<React.SetStateAction<number>>;
  settingsSections: Array<{
    title: string;
    items: Array<{
      id: string;
      label: string;
      value: string;
      description: string;
      type: "text" | "toggle" | "info";
      onActivate: () => void;
    }>;
  }>;
  flatSettingsItems: Array<{ onActivate?: () => void }>;
  handleSettingsItemActivate: () => void;
  openSettingPrompt: (options: {
    title: string;
    currentValue?: string;
    placeholder?: string;
    onSubmit: (value: string | undefined) => void;
  }) => void;
}

export interface UseSettingsOptions {
  settings: AppSettings;
  setSettings: React.Dispatch<React.SetStateAction<AppSettings>>;
  setPrompt: (prompt: Prompt | null) => void;
}

/**
 * Manages settings menu state and interactions
 */
export function useSettings(options: UseSettingsOptions): UseSettingsReturn {
  const { settings, setSettings, setPrompt } = options;
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [settingsFocusIndex, setSettingsFocusIndex] = useState(0);

  type StringSettingKey = keyof Pick<
    AppSettings,
    "model" | "endpoint" | "apiKey" | "afBridgeBaseUrl" | "afModel" | "provider"
  >;

  const setStringSetting = useCallback(
    (key: StringSettingKey, value: string | undefined) => {
      setSettings((prev) => ({ ...prev, [key]: value }));
    },
    [setSettings]
  );

  const openSettingPrompt = useCallback(
    (options: {
      title: string;
      currentValue?: string;
      placeholder?: string;
      onSubmit: (value: string | undefined) => void;
    }) => {
      setPrompt({
        type: "input",
        message: options.title,
        defaultValue: options.currentValue || "",
        placeholder: options.placeholder,
        onConfirm: (val: string) => {
          const trimmed = val.trim();
          options.onSubmit(trimmed ? trimmed : undefined);
          setPrompt(null);
        },
        onCancel: () => setPrompt(null),
      });
    },
    [setPrompt]
  );

  const settingsSections = useMemo<UseSettingsReturn["settingsSections"]>(() => {
    const workflowEnabled = settings.workflow?.enabled ?? false;
    const maskedKey = settings.apiKey
      ? "***" + settings.apiKey.slice(-4)
      : "Not set";
    return [
      {
        title: "Core API",
        items: [
          {
            id: "provider",
            label: "Provider",
            value: settings.provider || "Auto",
            description: "openai | azure | litellm | custom (default: litellm)",
            type: "text" as const,
            onActivate: () =>
              openSettingPrompt({
                title: "Enter provider (openai, azure, litellm, custom)",
                currentValue: settings.provider,
                placeholder: "litellm",
                onSubmit: (value) =>
                  setSettings((prev) => applyProviderDefaults(prev, value)),
              }),
          },
          {
            id: "model",
            label: "Model",
            value: settings.model || "Not set",
            description: "Default model (from LITELLM_MODELS if set)",
            type: "text" as const,
            onActivate: () =>
              openSettingPrompt({
                title: "Enter default model",
                currentValue: settings.model,
                placeholder: "openai/gpt-4o-mini",
                onSubmit: (value) => setStringSetting("model", value),
              }),
          },
          {
            id: "endpoint",
            label: "Endpoint",
            value: settings.endpoint || "Not set",
            description: "Base URL for OpenAI-compatible Responses API",
            type: "text" as const,
            onActivate: () =>
              openSettingPrompt({
                title: "Enter API endpoint base URL",
                currentValue: settings.endpoint,
                placeholder: "http://localhost:4000/v1",
                onSubmit: (value) => setStringSetting("endpoint", value),
              }),
          },
          {
            id: "apiKey",
            label: "API Key",
            value: maskedKey,
            description: "Stored locally at ~/.qlaw-cli/qlaw_settings.json",
            type: "text" as const,
            onActivate: () =>
              openSettingPrompt({
                title: "Enter API key",
                currentValue: settings.apiKey,
                placeholder: "sk-...",
                onSubmit: (value) => setStringSetting("apiKey", value),
              }),
          },
        ],
      },
      {
        title: "Providers",
        items: [
          {
            id: "useLitellmEnv",
            label: "Apply LiteLLM env defaults",
            value: "Use LITELLM_*",
            description: "Sets endpoint/model/key from LITELLM_* and clears OpenAI defaults",
            type: "info" as const,
            onActivate: () => setSettings((prev) => applyProviderDefaults(prev, "litellm")),
          },
          {
            id: "useOpenaiEnv",
            label: "Apply OpenAI env defaults",
            value: "Use OPENAI_*",
            description: "Sets endpoint/model/key from OPENAI_* and clears LiteLLM defaults",
            type: "info" as const,
            onActivate: () => setSettings((prev) => applyProviderDefaults(prev, "openai")),
          },
          {
            id: "clearOverrides",
            label: "Clear API overrides",
            value: "Reset",
            description: "Clears endpoint/model/key so env defaults apply on next launch",
            type: "info" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                endpoint: undefined,
                model: undefined,
                apiKey: undefined,
              })),
          },
        ],
      },
      {
        title: "UI",
        items: [
          {
            id: "theme",
            label: "Theme",
            value: settings.theme === "dark" ? "Dark" : settings.theme === "light" ? "Light" : "Dracula",
            description: "Cycle through dark → light → dracula themes",
            type: "toggle" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                theme: prev.theme === "dark" ? "light" : prev.theme === "light" ? "dracula" : "dark",
              })),
          },
          {
            id: "timestamps",
            label: "Timestamps",
            value: settings.showTimestamps ? "Shown" : "Hidden",
            description: "Toggle message timestamps",
            type: "toggle" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                showTimestamps: !prev.showTimestamps,
              })),
          },
          {
            id: "autoscroll",
            label: "Auto-scroll",
            value: settings.autoScroll ? "Enabled" : "Disabled",
            description: "Scroll to bottom when streaming",
            type: "toggle" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                autoScroll: !prev.autoScroll,
              })),
          },
        ],
      },
      {
        title: "Coding Agent",
        items: [
          {
            id: "toolsEnabled",
            label: "Tools",
            value: settings.tools?.enabled ? "Enabled" : "Disabled",
            description: "Allow tool calls (permissions via /tools perm)",
            type: "toggle" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                tools: {
                  ...(prev.tools || {}),
                  enabled: !(prev.tools?.enabled ?? false),
                },
              })),
          },
          {
            id: "toolsAutoApprove",
            label: "Auto-approve",
            value: settings.tools?.autoApprove ? "Enabled" : "Disabled",
            description: "Auto-run safe tools (read/list); write/run still prompt",
            type: "toggle" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                tools: {
                  ...(prev.tools || {}),
                  autoApprove: !(prev.tools?.autoApprove ?? false),
                },
              })),
          },
        ],
      },
      {
        title: "Agent Framework",
        items: [
          {
            id: "afBridgeBaseUrl",
            label: "Bridge URL",
            value: settings.afBridgeBaseUrl || "Not set",
            description: "FastAPI bridge for agent-framework workflows",
            type: "text" as const,
            onActivate: () =>
              openSettingPrompt({
                title: "Enter Agent Framework bridge base URL",
                currentValue: settings.afBridgeBaseUrl,
                placeholder: "http://127.0.0.1:8081",
                onSubmit: (value) => setStringSetting("afBridgeBaseUrl", value),
              }),
          },
          {
            id: "afModel",
            label: "AF Model",
            value: settings.afModel || settings.model || "Not set",
            description: "Workflow / fleet identifier exposed by the bridge",
            type: "text" as const,
            onActivate: () =>
              openSettingPrompt({
                title: "Enter Agent Framework model identifier",
                currentValue: settings.afModel,
                placeholder: "multi_tier_support",
                onSubmit: (value) => setStringSetting("afModel", value),
              }),
          },
          {
            id: "workflowEnabled",
            label: "Workflow mode",
            value: workflowEnabled ? "Enabled" : "Disabled",
            description: "When enabled, workflow mode stays active by default",
            type: "toggle" as const,
            onActivate: () =>
              setSettings((prev) => ({
                ...prev,
                workflow: {
                  ...(prev.workflow || {}),
                  enabled: !(prev.workflow?.enabled ?? false),
                },
              })),
          },
        ],
      },
    ];
  }, [settings, openSettingPrompt, setSettings, setStringSetting]);

  const flatSettingsItems = useMemo<UseSettingsReturn["flatSettingsItems"]>(
    () => settingsSections.flatMap((section) => section.items),
    [settingsSections]
  );

  const handleSettingsItemActivate = useCallback(() => {
    const target = flatSettingsItems[settingsFocusIndex];
    if (target?.onActivate) {
      target.onActivate();
    }
  }, [flatSettingsItems, settingsFocusIndex]);

  return {
    showSettingsMenu,
    setShowSettingsMenu,
    settingsFocusIndex,
    setSettingsFocusIndex,
    settingsSections,
    flatSettingsItems,
    handleSettingsItemActivate,
    openSettingPrompt,
  };
}
