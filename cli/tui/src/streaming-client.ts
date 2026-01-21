/**
 * Streaming client for consuming Server-Sent Events from the backend.
 * Handles thinking chunks, responses, and errors in real-time.
 *
 * Uses eventsource-parser for robust SSE parsing with proper event buffering.
 */

import { createParser, type EventSourceMessage } from "eventsource-parser";

export interface ThinkingChunk {
  type: "thinking" | "reasoning" | "thought" | "internal" | "step";
  content: string;
  step?: number;
}

export interface ResponseChunk {
  type: "response" | "complete";
  content: string;
}

export type StreamEvent = ThinkingChunk | ResponseChunk;

export interface StreamingOptions {
  apiUrl: string;
  message: string;
  context?: Record<string, any>;
  onThinking?: (chunk: ThinkingChunk) => void;
  onResponse?: (chunk: ResponseChunk) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

/**
 * Stream chat response with real-time thinking/response chunks.
 *
 * Usage:
 * ```typescript
 * const client = new StreamingClient();
 * await client.streamChat({
 *   apiUrl: "http://localhost:8000",
 *   message: "Create a skill for JSON parsing",
 *   onThinking: (chunk) => console.log("Thinking:", chunk),
 *   onResponse: (chunk) => console.log("Response:", chunk),
 *   onComplete: () => console.log("Done!")
 * });
 * ```
 */
export class StreamingClient {
  private maxRetries: number = 3;
  private retryDelayMs: number = 1000;

  async streamChat(options: StreamingOptions): Promise<void> {
    const {
      apiUrl,
      message,
      context,
      onThinking,
      onResponse,
      onError,
      onComplete,
    } = options;

    const url = `${apiUrl}/api/v1/chat/stream`;
    let retries = 0;

    while (retries <= this.maxRetries) {
      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({ message, context }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();

        // Create SSE parser with proper event handling
        const parser = createParser({
          onEvent: (event: EventSourceMessage) => {
            // Handle event
            const eventType = event.event || "message";
            const data = event.data;

            if (!data || data.trim() === "") {
              // Empty data for complete event
              if (eventType === "complete" && onComplete) {
                onComplete();
              }
              return;
            }

            try {
              const parsed = JSON.parse(data);

              switch (eventType) {
                case "thinking":
                  if (onThinking) {
                    onThinking(parsed as ThinkingChunk);
                  }
                  break;
                case "response":
                  if (onResponse) {
                    onResponse(parsed as ResponseChunk);
                  }
                  break;
                case "error":
                  if (onError) {
                    onError(
                      typeof parsed === "string"
                        ? parsed
                        : JSON.stringify(parsed),
                    );
                  }
                  break;
                case "complete":
                  if (onComplete) {
                    onComplete();
                  }
                  break;
                default:
                  // Unknown event type, log for debugging
                  console.debug(`Unknown SSE event type: ${eventType}`, parsed);
              }
            } catch (parseError) {
              // JSON parse failed - might be plain text error
              if (eventType === "error" && onError) {
                onError(data);
              } else {
                console.error("Failed to parse SSE data:", data, parseError);
              }
            }
          },
        });

        // Read stream and feed to parser
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // Stream ended - trigger complete if not already done
            break;
          }

          // Feed chunk to parser
          const chunk = decoder.decode(value, { stream: true });
          parser.feed(chunk);
        }

        // Successful completion - no retry needed
        return;
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);

        // Check if retryable (network errors, not HTTP errors)
        const isRetryable =
          errorMsg.includes("fetch") ||
          errorMsg.includes("network") ||
          errorMsg.includes("ECONNREFUSED");

        if (isRetryable && retries < this.maxRetries) {
          retries++;
          console.warn(
            `SSE connection failed, retrying (${retries}/${this.maxRetries})...`,
          );
          await new Promise((resolve) =>
            setTimeout(resolve, this.retryDelayMs * retries),
          );
          continue;
        }

        // Non-retryable or max retries exceeded
        if (onError) {
          onError(errorMsg);
        }
        throw error;
      }
    }
  }

  /**
   * Synchronous fallback that collects all streaming events.
   */
  async getSyncChat(options: {
    apiUrl: string;
    message: string;
    context?: Record<string, any>;
  }): Promise<{
    thinking: string[];
    response: string;
    thinking_summary: string;
  }> {
    const { apiUrl, message, context } = options;

    const response = await fetch(`${apiUrl}/api/v1/chat/sync`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, context }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json() as Promise<{
      thinking: string[];
      response: string;
      thinking_summary: string;
    }>;
  }
}
