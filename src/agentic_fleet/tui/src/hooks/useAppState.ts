/**
 * Hook for managing core application state (messages, sessions, settings)
 * Consolidates related state management from index.tsx
 */

import { useState, useEffect, useMemo } from "react";
import type { Message, Session, AppSettings, CustomCommand } from "../types.ts";
import {
  loadSettings,
  loadSessions,
  loadCustomCommands,
  debouncedSaveSettings,
  debouncedSaveSessions,
  debouncedSaveCustomCommands,
} from "../storage.ts";

export interface UseAppStateReturn {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  sessions: Session[];
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
  currentSessionId: string | null;
  setCurrentSessionId: React.Dispatch<React.SetStateAction<string | null>>;
  settings: AppSettings;
  setSettings: React.Dispatch<React.SetStateAction<AppSettings>>;
  customCommands: CustomCommand[];
  setCustomCommands: React.Dispatch<React.SetStateAction<CustomCommand[]>>;
  recentSessions: Session[];
}

/**
 * Manages core application state including messages, sessions, settings, and custom commands
 */
export function useAppState(): UseAppStateReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>(() => loadSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings());
  const [customCommands, setCustomCommands] = useState<CustomCommand[]>(() =>
    loadCustomCommands()
  );

  const recentSessions = useMemo(() => {
    return [...sessions]
      .sort(
        (a, b) =>
          new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      )
      .slice(0, 5);
  }, [sessions]);

  // Save settings when changed (debounced to reduce file I/O)
  useEffect(() => {
    debouncedSaveSettings(settings);
  }, [settings]);

  // Save sessions when changed (debounced to reduce file I/O)
  useEffect(() => {
    debouncedSaveSessions(sessions);
  }, [sessions]);

  // Save custom commands when changed (debounced to reduce file I/O)
  useEffect(() => {
    debouncedSaveCustomCommands(customCommands);
  }, [customCommands]);

  // Save current session when messages change
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId
            ? { ...s, messages, updatedAt: new Date() }
            : s
        )
      );
    }
  }, [messages, currentSessionId]);

  return {
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
  };
}

