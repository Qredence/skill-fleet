import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkflowEvent } from "../../lib/types";
import { streamJobEventsWithReconnect } from "../../lib/api";

export type StreamStatus =
  | "idle"
  | "connected"
  | "reconnecting"
  | "failed";

type StreamState = {
  status: StreamStatus;
  attemptNumber: number;
  delayMs: number;
  error?: string;
};

export function useStreamHandler(
  jobId: string | null,
  onEvent: (event: WorkflowEvent) => void,
) {
  const [state, setState] = useState<StreamState>({
    status: "idle",
    attemptNumber: 0,
    delayMs: 0,
  });
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Cleanup previous stream
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setState({ status: "connected", attemptNumber: 0, delayMs: 0 });

    streamJobEventsWithReconnect(jobId, onEvent, abortRef.current.signal, {
      maxRetries: 5,
      baseDelayMs: 1000,
      maxDelayMs: 30000,
      onReconnectStart: (attempt, delay) => {
        setState({
          status: "reconnecting",
          attemptNumber: attempt,
          delayMs: delay,
        });
      },
      onReconnectSuccess: () => {
        setState({ status: "connected", attemptNumber: 0, delayMs: 0 });
      },
      onReconnectFailed: (attempt, error) => {
        setState({
          status: "failed",
          attemptNumber: attempt,
          delayMs: 0,
          error: String(error),
        });
      },
    }).catch((err) => {
      setState({
        status: "failed",
        attemptNumber: 0,
        delayMs: 0,
        error: String(err),
      });
    });

    return () => {
      abortRef.current?.abort();
    };
  }, [jobId, onEvent]);

  return state;
}
