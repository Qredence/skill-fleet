/**
 * useHitl Hook
 *
 * Manages Human-in-the-Loop interactions for a specific job:
 * - Polls GET /api/v1/hitl/{job_id}/prompt for pending prompts
 * - Submits responses via POST /api/v1/hitl/{job_id}/response
 * - Tracks HITL state and provides callbacks
 */

import { useState, useEffect, useCallback, useRef } from "react";
import type { HITLPromptData } from "../components/hitl-prompt.js";

export interface UseHitlOptions {
  /** API base URL */
  apiUrl: string;
  /** Job ID to monitor */
  jobId: string | null;
  /** Polling interval in ms (default: 1500) */
  pollInterval?: number;
  /** Whether polling is enabled */
  enabled?: boolean;
  /** Callback when job completes */
  onComplete?: (result: any) => void;
  /** Callback when job fails */
  onError?: (error: string) => void;
  /** Callback when HITL prompt is received */
  onPrompt?: (prompt: HITLPromptData) => void;
}

export interface UseHitlReturn {
  /** Current HITL prompt data (null if not waiting for input) */
  prompt: HITLPromptData | null;
  /** Whether we're currently polling */
  isPolling: boolean;
  /** Whether we're waiting for user input */
  isWaitingForInput: boolean;
  /** Current job status */
  status: string | null;
  /** Current phase */
  currentPhase: string | null;
  /** Progress message */
  progressMessage: string | null;
  /** Error message if any */
  error: string | null;
  /** Submit a response to the current HITL prompt */
  submitResponse: (response: Record<string, any>) => Promise<boolean>;
  /** Start polling for a job */
  startPolling: (jobId: string) => void;
  /** Stop polling */
  stopPolling: () => void;
  /** Manually refresh prompt */
  refresh: () => Promise<void>;
}

/**
 * Hook for managing HITL interactions with a job
 */
export function useHitl(options: UseHitlOptions): UseHitlReturn {
  const {
    apiUrl,
    jobId: initialJobId,
    pollInterval = 1500,
    enabled = true,
    onComplete,
    onError,
    onPrompt,
  } = options;

  const [jobId, setJobId] = useState<string | null>(initialJobId);
  const [prompt, setPrompt] = useState<HITLPromptData | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs to avoid stale closures in intervals
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  // Track the last seen prompt to avoid duplicate onPrompt callbacks
  const lastPromptRef = useRef<string | null>(null);

  /**
   * Fetch current HITL prompt from API
   */
  const fetchPrompt = useCallback(async (): Promise<HITLPromptData | null> => {
    if (!jobId) return null;

    try {
      const response = await fetch(`${apiUrl}/api/v1/hitl/${jobId}/prompt`);

      if (!response.ok) {
        if (response.status === 404) {
          // Job not found - might be completed and cleaned up
          return null;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = (await response.json()) as HITLPromptData;
      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      return null;
    }
  }, [apiUrl, jobId]);

  /**
   * Process a prompt response and update state
   */
  const processPrompt = useCallback(
    (data: HITLPromptData | null) => {
      if (!data) {
        setPrompt(null);
        return;
      }

      setStatus(data.status);
      setCurrentPhase(data.current_phase || null);
      setProgressMessage(data.progress_message || null);
      setError(data.error || null);

      // Check terminal states
      if (data.status === "completed") {
        setPrompt(null);
        setIsPolling(false);
        isPollingRef.current = false;
        // Reset last prompt ref on completion
        lastPromptRef.current = null;
        if (onComplete) {
          onComplete({
            draft_path: data.draft_path,
            validation_score: data.validation_score,
          });
        }
        return;
      }

      if (data.status === "failed") {
        setPrompt(null);
        setIsPolling(false);
        isPollingRef.current = false;
        // Reset last prompt ref on failure
        lastPromptRef.current = null;
        if (onError) {
          onError(data.error || "Job failed");
        }
        return;
      }

      // Check if waiting for HITL input
      if (data.status === "pending_hitl" && data.type) {
        // Generate a unique key for this prompt to detect changes
        const promptKey = `${data.type}_${JSON.stringify({
          summary: data.summary,
          content: data.content,
          questions: data.questions,
        })}`;

        // Only call onPrompt if this is a new prompt or the prompt changed
        if (lastPromptRef.current !== promptKey) {
          lastPromptRef.current = promptKey;
          if (onPrompt) {
            onPrompt(data);
          }
        }

        // Always update the prompt state (for rendering)
        setPrompt(data);
      } else {
        // Job is running but not waiting for input
        setPrompt(null);
        // Reset last prompt ref when not waiting
        lastPromptRef.current = null;
      }
    },
    [onComplete, onError, onPrompt],
  );

  /**
   * Manual refresh
   */
  const refresh = useCallback(async () => {
    const data = await fetchPrompt();
    processPrompt(data);
  }, [fetchPrompt, processPrompt]);

  /**
   * Start polling for a specific job
   */
  const startPolling = useCallback((newJobId: string) => {
    // Stop existing polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    setJobId(newJobId);
    setIsPolling(true);
    isPollingRef.current = true;
    setError(null);
    setPrompt(null);
  }, []);

  /**
   * Stop polling
   */
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
    isPollingRef.current = false;
  }, []);

  /**
   * Submit response to current HITL prompt
   */
  const submitResponse = useCallback(
    async (response: Record<string, any>): Promise<boolean> => {
      if (!jobId) {
        setError("No job ID to respond to");
        return false;
      }

      try {
        const res = await fetch(`${apiUrl}/api/v1/hitl/${jobId}/response`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(response),
        });

        if (!res.ok) {
          const errorData = (await res
            .json()
            .catch(() => ({}) as Record<string, string>)) as Record<
            string,
            string
          >;
          throw new Error(errorData.detail || `HTTP ${res.status}`);
        }

        const result = (await res.json()) as {
          status: string;
          detail?: string;
        };

        if (result.status === "accepted") {
          // Clear prompt immediately - job will resume
          setPrompt(null);
          // Trigger immediate poll to get updated state
          setTimeout(refresh, 100);
          return true;
        } else {
          // Response was ignored (probably stale)
          setError(result.detail || "Response was ignored");
          return false;
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        setError(errorMsg);
        return false;
      }
    },
    [apiUrl, jobId, refresh],
  );

  /**
   * Polling effect
   */
  useEffect(() => {
    if (!enabled || !jobId || !isPolling) {
      return;
    }

    // Initial fetch
    refresh();

    // Set up polling interval
    pollIntervalRef.current = setInterval(async () => {
      if (!isPollingRef.current) return;

      const data = await fetchPrompt();
      processPrompt(data);
    }, pollInterval);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [
    enabled,
    jobId,
    isPolling,
    pollInterval,
    fetchPrompt,
    processPrompt,
    refresh,
  ]);

  /**
   * Update jobId when prop changes
   */
  useEffect(() => {
    if (initialJobId !== jobId) {
      setJobId(initialJobId);
      if (initialJobId) {
        startPolling(initialJobId);
      } else {
        stopPolling();
      }
    }
  }, [initialJobId, jobId, startPolling, stopPolling]);

  return {
    prompt,
    isPolling,
    isWaitingForInput: prompt !== null && status === "pending_hitl",
    status,
    currentPhase,
    progressMessage,
    error,
    submitResponse,
    startPolling,
    stopPolling,
    refresh,
  };
}

export default useHitl;
