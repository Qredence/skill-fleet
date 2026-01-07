/**
 * Streaming service for handling AI response streams
 * Extracted from index.tsx to improve code organization
 */

import type { Message, AppSettings } from "../types.ts";
import { resolveLlmConfig, getAuthHeader, resolveResponsesUrl } from "../llm/config.ts";
import { buildResponsesInput } from "../llm/input.ts";
import { parseSSEStream } from "../sse.ts";
import { formatRequestInfoForDisplay } from "../af.ts";

export interface StreamingCallbacks {
  onDelta: (text: string) => void;
  onError: (err: Error) => void;
  onDone: () => void;
}

/**
 * Stream response from OpenAI Responses API
 */
export async function streamResponseFromOpenAI(params: {
  history: Message[];
  settings: AppSettings;
  callbacks: StreamingCallbacks;
}): Promise<void> {
  const { history, settings, callbacks } = params;
  const { onDelta, onError, onDone } = callbacks;

  const config = resolveLlmConfig(settings);
  if (!config) {
    onError(
      new Error("Missing endpoint, API key, or model. Configure /provider, /endpoint, /api-key, and /model.")
    );
    onDone();
    return;
  }

  try {
    const authHeaders = getAuthHeader(config);
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...authHeaders,
    };

    const res = await fetch(resolveResponsesUrl(config), {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: config.model,
        input: buildResponsesInput(history),
        stream: true,
      }),
    });

    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => "");
      throw new Error(
        `HTTP ${res.status} ${res.statusText}${text ? ` - ${text}` : ""}`
      );
    }

    const reader = res.body.getReader();
    await parseSSEStream(reader, {
      onDelta,
      onError,
      onTraceComplete: (payload) => {
        const formatted = formatRequestInfoForDisplay(payload);
        if (formatted) {
          onDelta(formatted);
        }
      },
    });

    onDone();
  } catch (err: unknown) {
    onError(err instanceof Error ? err : new Error(String(err)));
    onDone();
  }
}
