import type { CreateJobResponse, HitlPrompt, WorkflowEvent } from "./types";

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiUrl(): string {
  const raw = process.env.SKILL_FLEET_API_URL || DEFAULT_API_URL;
  return raw.replace(/\/$/, "");
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
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
    headers: { Accept: "text/event-stream" },
    signal,
  });

  if (!response.ok || !response.body) {
    const text = await response.text();
    throw new Error(`Stream error ${response.status}: ${text || response.statusText}`);
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
