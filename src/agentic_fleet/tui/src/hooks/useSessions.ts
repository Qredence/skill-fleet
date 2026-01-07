/**
 * Hook for managing session list UI state
 * Extracted from index.tsx to improve code organization
 */

import { useState, useEffect, useCallback } from "react";
import type { Session, Message } from "../types.ts";

export interface UseSessionsReturn {
  showSessionList: boolean;
  setShowSessionList: (show: boolean) => void;
  sessionFocusIndex: number;
  setSessionFocusIndex: React.Dispatch<React.SetStateAction<number>>;
  handleSessionActivate: () => void;
}

export interface UseSessionsOptions {
  recentSessions: Session[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  setCurrentSessionId: (id: string | null) => void;
}

/**
 * Manages session list overlay state and interactions
 */
export function useSessions(options: UseSessionsOptions): UseSessionsReturn {
  const { recentSessions, setMessages, setCurrentSessionId } = options;
  const [showSessionList, setShowSessionList] = useState(false);
  const [sessionFocusIndex, setSessionFocusIndex] = useState(0);

  const handleSessionActivate = useCallback(() => {
    const target = recentSessions[sessionFocusIndex];
    if (!target) return;
    const resumedMessages = target.messages.map((message) => ({ ...message }));
    resumedMessages.push({
      id: `${target.id}-resume-${Date.now()}`,
      role: "system",
      content: `Resumed session "${target.name}" (${target.messages.length} messages).`,
      timestamp: new Date(),
    });
    setMessages(resumedMessages);
    setCurrentSessionId(target.id);
    setShowSessionList(false);
  }, [
    recentSessions,
    sessionFocusIndex,
    setMessages,
    setCurrentSessionId,
    setShowSessionList,
  ]);

  // Reset focus index when session list opens
  useEffect(() => {
    if (showSessionList) {
      setSessionFocusIndex(0);
    }
  }, [showSessionList]);

  // Clamp focus index when sessions change
  useEffect(() => {
    if (!showSessionList) return;
    if (recentSessions.length === 0) {
      setSessionFocusIndex(0);
      return;
    }
    setSessionFocusIndex((prev) => Math.min(prev, recentSessions.length - 1));
  }, [showSessionList, recentSessions.length]);

  return {
    showSessionList,
    setShowSessionList,
    sessionFocusIndex,
    setSessionFocusIndex,
    handleSessionActivate,
  };
}

