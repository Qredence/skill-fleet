/**
 * Streaming client for consuming Server-Sent Events from the backend.
 * Handles thinking chunks, responses, and errors in real-time.
 */
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
export declare class StreamingClient {
    streamChat(options: StreamingOptions): Promise<void>;
    /**
     * Synchronous fallback that collects all streaming events.
     */
    getSyncChat(options: {
        apiUrl: string;
        message: string;
        context?: Record<string, any>;
    }): Promise<{
        thinking: string[];
        response: string;
        thinking_summary: string;
    }>;
}
