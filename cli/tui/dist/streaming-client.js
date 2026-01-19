/**
 * Streaming client for consuming Server-Sent Events from the backend.
 * Handles thinking chunks, responses, and errors in real-time.
 */
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
    async streamChat(options) {
        const { apiUrl, message, context, onThinking, onResponse, onError, onComplete, } = options;
        const url = `${apiUrl}/api/v1/chat/stream`;
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message, context }),
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            // Parse SSE response
            const reader = response.body?.getReader();
            if (!reader)
                throw new Error("No response body");
            const decoder = new TextDecoder();
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                // Keep the last incomplete line in buffer
                buffer = lines.pop() || "";
                for (const line of lines) {
                    if (line.startsWith("event:")) {
                        const eventType = line.substring(6).trim();
                        // Try to read the data line
                        const nextIdx = lines.indexOf(line) + 1;
                        if (nextIdx < lines.length && lines[nextIdx].startsWith("data:")) {
                            const dataLine = lines[nextIdx];
                            const dataStr = dataLine.substring(5).trim();
                            if (!dataStr) {
                                // Empty data line for complete event
                                if (eventType === "complete" && onComplete) {
                                    onComplete();
                                }
                                continue;
                            }
                            try {
                                const data = JSON.parse(dataStr);
                                if (eventType === "thinking" && onThinking) {
                                    onThinking(data);
                                }
                                else if (eventType === "response" && onResponse) {
                                    onResponse(data);
                                }
                                else if (eventType === "error" && onError) {
                                    onError(data);
                                }
                                else if (eventType === "complete" && onComplete) {
                                    onComplete();
                                }
                            }
                            catch (e) {
                                console.error("Failed to parse stream data:", dataStr, e);
                            }
                        }
                    }
                }
            }
            // Process any remaining buffer
            if (buffer.trim()) {
                try {
                    if (buffer.startsWith("event:")) {
                        // Handle remaining event
                        const eventType = buffer.substring(6).split("\n")[0].trim();
                        if (eventType === "complete" && onComplete) {
                            onComplete();
                        }
                    }
                }
                catch (e) {
                    console.error("Failed to process remaining buffer:", buffer);
                }
            }
        }
        catch (error) {
            const errorMsg = error instanceof Error ? error.message : String(error);
            if (onError) {
                onError(errorMsg);
            }
            throw error;
        }
    }
    /**
     * Synchronous fallback that collects all streaming events.
     */
    async getSyncChat(options) {
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
        return response.json();
    }
}
//# sourceMappingURL=streaming-client.js.map