/**
 * Hook for managing streaming responses
 * Handles OpenAI and Agent Framework streaming logic
 */

import { useState, useEffect, useMemo } from "react";
import type { Message, AppSettings } from "../types.ts";
import { streamResponseFromOpenAI } from "../services/streamingService.ts";
import { startWorkflow } from "../workflow.ts";

const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

export interface UseStreamingReturn {
  isProcessing: boolean;
  requestStartAt: number | null;
  spinnerIndex: number;
  spinnerFrame: string;
  elapsedSec: number;
  streamResponse: (params: {
    messages: Message[];
    userInput: string;
    mode: "standard" | "workflow";
    settings: AppSettings;
    assistantMessageId: string;
    onMessageUpdate: (updater: (prev: Message[]) => Message[]) => void;
    onComplete?: (assistantMessageId: string) => void;
  }) => void;
}

/**
 * Manages streaming response state and logic
 */
export function useStreaming(): UseStreamingReturn {
  const [isProcessing, setIsProcessing] = useState(false);
  const [requestStartAt, setRequestStartAt] = useState<number | null>(null);
  const [spinnerIndex, setSpinnerIndex] = useState(0);

  // Streaming spinner animation
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | undefined;
    if (isProcessing) {
      intervalId = setInterval(
        () => setSpinnerIndex((i) => (i + 1) % SPINNER_FRAMES.length),
        80
      );
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isProcessing]);

  const spinnerFrame = SPINNER_FRAMES[spinnerIndex] || "";

  const elapsedSec = useMemo(() => {
    if (!requestStartAt || !isProcessing) return 0;
    return Math.max(0, Math.floor((Date.now() - requestStartAt) / 1000));
  }, [requestStartAt, isProcessing]);

  const streamResponse = (params: {
    messages: Message[];
    userInput: string;
    mode: "standard" | "workflow";
    settings: AppSettings;
    assistantMessageId: string;
    onMessageUpdate: (updater: (prev: Message[]) => Message[]) => void;
    onComplete?: (assistantMessageId: string) => void;
  }) => {
    const {
      messages,
      userInput,
      mode,
      settings,
      assistantMessageId,
      onMessageUpdate,
      onComplete,
    } = params;

    setIsProcessing(true);
    setRequestStartAt(Date.now());

    // Route based on AF bridge configuration
    const useAf =
      mode === "workflow" &&
      !!settings.afBridgeBaseUrl &&
      !!(settings.afModel || settings.model);

    if (useAf) {
      const modelId = settings.afModel || settings.model || "workflow";
      startWorkflow({
        baseUrl: settings.afBridgeBaseUrl!,
        model: modelId,
        conversation: undefined,
        input: userInput,
        onDelta: (chunk) => {
          onMessageUpdate((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, content: m.content + chunk }
                : m
            )
          );
        },
        onError: (err) => {
          onMessageUpdate((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, content: m.content + `\n\n[Error] ${err.message}` }
                : m
            )
          );
        },
        onDone: () => {
          setIsProcessing(false);
          onComplete?.(assistantMessageId);
        },
      });
    } else {
      // Stream from OpenAI Responses API
      streamResponseFromOpenAI({
        history: messages,
        settings,
        callbacks: {
          onDelta: (chunk) => {
            onMessageUpdate((prev) =>
              prev.map((m) =>
                m.id === assistantMessageId
                  ? { ...m, content: m.content + chunk }
                  : m
              )
            );
          },
          onError: (err) => {
            onMessageUpdate((prev) =>
              prev.map((m) =>
                m.id === assistantMessageId
                  ? { ...m, content: m.content + `\n\n[Error] ${err.message}` }
                  : m
              )
            );
          },
          onDone: () => {
            setIsProcessing(false);
            onComplete?.(assistantMessageId);
          },
        },
      });
    }
  };

  return {
    isProcessing,
    requestStartAt,
    spinnerIndex,
    spinnerFrame,
    elapsedSec,
    streamResponse,
  };
}
