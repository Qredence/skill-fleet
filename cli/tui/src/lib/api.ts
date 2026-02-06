import type { CreateJobResponse, HitlPrompt, WorkflowEvent } from "./types";
import { getConfig } from "./config";

export function getApiUrl(): string {
  return getConfig().SKILL_FLEET_API_URL;
}

function getUserId(): string {
  return getConfig().SKILL_FLEET_USER_ID;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getUserId(),
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text || response.statusText}`);
  }

  return (await response.json()) as T;
}

export async function createSkillJob(
  task: string,
  userId: string,
): Promise<CreateJobResponse> {
  return await fetchJson<CreateJobResponse>("/api/v1/skills/", {
    method: "POST",
    body: JSON.stringify({
      task_description: task,
      user_id: userId,
      enable_hitl_confirm: true,
      enable_hitl_preview: true,
      enable_hitl_review: true,
      enable_token_streaming: true,
      auto_save_draft_on_preview_confirm: true,
    }),
  });
}

export async function fetchHitlPrompt(jobId: string): Promise<HitlPrompt> {
  return await fetchJson<HitlPrompt>(`/api/v1/hitl/${jobId}/prompt`);
}

export async function postHitlResponse(
  jobId: string,
  payload: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return await fetchJson(`/api/v1/hitl/${jobId}/response`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function* parseSseStream(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<string> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    while (true) {
      const separatorIndex = buffer.indexOf("\n\n");
      if (separatorIndex === -1) {
        break;
      }

      const chunk = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);

      const lines = chunk.split("\n");
      const dataLines = lines
        .map((line) => line.trim())
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.replace(/^data:\s?/, ""));

      if (!dataLines.length) {
        continue;
      }

      const data = dataLines.join("\n").trim();
      if (data === "[DONE]") {
        return;
      }

      yield data;
    }
  }
}

export async function streamJobEvents(
  jobId: string,
  onEvent: (event: WorkflowEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}/api/v1/skills/${jobId}/stream`, {
    method: "GET",
    headers: {
      Accept: "text/event-stream",
      "X-User-Id": getUserId(),
    },
    signal,
  });

  if (!response.ok || !response.body) {
    const text = await response.text();
    throw new Error(
      `Stream error ${response.status}: ${text || response.statusText}`,
    );
  }

  for await (const data of parseSseStream(response.body)) {
    try {
      const parsed = JSON.parse(data) as WorkflowEvent;
      onEvent(parsed);
    } catch (error) {
      onEvent({
        type: "error",
        message: `Failed to parse event: ${String(error)}`,
      });
    }
  }
}

export type StreamJobEventsOptions = {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  onReconnectStart?: (attemptNumber: number, delayMs: number) => void;
  onReconnectSuccess?: (attemptNumber: number) => void;
  onReconnectFailed?: (attemptNumber: number, error: unknown) => void;
};

/**
 * Stream job events with automatic reconnection and exponential backoff.
 *
 * Wraps streamJobEvents() with retry logic. On connection failure, will:
 * 1. Wait with exponential backoff (baseDelayMs * 2^attempt, capped at maxDelayMs)
 * 2. Fire onReconnectStart callback with attempt number and delay
 * 3. Attempt to reconnect up to maxRetries times
 * 4. Fire onReconnectSuccess if reconnection succeeds
 * 5. Fire onReconnectFailed and throw error if all retries exhausted
 *
 * @param jobId - Job ID to stream events from
 * @param onEvent - Event handler for workflow events
 * @param signal - AbortSignal to cancel streaming
 * @param options - Reconnection configuration
 * @throws Error after all retries are exhausted
 */
export async function streamJobEventsWithReconnect(
  jobId: string,
  onEvent: (event: WorkflowEvent) => void,
  signal?: AbortSignal,
  options?: StreamJobEventsOptions,
): Promise<void> {
  const {
    maxRetries = 5,
    baseDelayMs = 1000,
    maxDelayMs = 30000,
    onReconnectStart,
    onReconnectSuccess,
    onReconnectFailed,
  } = options ?? {};

  let attemptNumber = 0;
  let lastError: unknown = null;

  while (attemptNumber <= maxRetries) {
    try {
      await streamJobEvents(jobId, onEvent, signal);
      // Stream completed successfully
      if (attemptNumber > 0) {
        onReconnectSuccess?.(attemptNumber);
      }
      return;
    } catch (error) {
      // If aborted, don't retry
      if (signal?.aborted) {
        throw error;
      }

      lastError = error;
      attemptNumber++;

      if (attemptNumber > maxRetries) {
        onReconnectFailed?.(attemptNumber, error);
        throw error;
      }

      // Exponential backoff: baseDelayMs * 2^(attempt-1), capped at maxDelayMs
      const exponentialDelay = baseDelayMs * Math.pow(2, attemptNumber - 1);
      const delayMs = Math.min(exponentialDelay, maxDelayMs);

      onReconnectStart?.(attemptNumber, delayMs);

      // Wait before retry
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  // Should never reach here, but satisfy TypeScript
  throw lastError ?? new Error("Stream failed after all retries");
}

export type PromoteDraftOptions = {
  overwrite?: boolean;
  deleteDraft?: boolean;
  force?: boolean;
};

export type PromoteDraftResponse = {
  job_id: string;
  status: string;
  final_path: string;
};

export async function promoteDraft(
  jobId: string,
  options?: PromoteDraftOptions,
): Promise<PromoteDraftResponse> {
  const {
    overwrite = true,
    deleteDraft = false,
    force = false,
  } = options ?? {};
  return await fetchJson<PromoteDraftResponse>(
    `/api/v1/drafts/${jobId}/promote`,
    {
      method: "POST",
      body: JSON.stringify({
        overwrite,
        delete_draft: deleteDraft,
        force,
      }),
    },
  );
}
