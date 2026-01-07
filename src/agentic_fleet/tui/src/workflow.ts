import { parseSSEStream } from "./sse.ts";
import { formatRequestInfoForDisplay } from "./af.ts";
import { info as logInfo, error as logError } from "./logger.ts";

export interface WorkflowStartParams {
  baseUrl: string;
  model: string;
  input: string;
  conversation?: string | { id: string };
  foundryEndpoint?: string;
  onDelta: (text: string) => void;
  onError: (err: Error) => void;
  onDone: () => void;
}

export async function startWorkflow(params: WorkflowStartParams) {
  const { baseUrl, model, input, conversation, foundryEndpoint, onDelta, onError, onDone } = params;
  try {
    logInfo("workflow:start", { baseUrl, model });
    const url = `${baseUrl.replace(/\/$/, "")}/v1/responses`;
    const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "text/event-stream" };
    if (foundryEndpoint) {
      headers["x-foundry-endpoint"] = foundryEndpoint;
    }
    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({ model, input, stream: true, ...(conversation ? { conversation } : {}) }),
    });
    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status} ${res.statusText}${text ? ` - ${text}` : ""}`);
    }
    const reader = res.body.getReader();
    await parseSSEStream(reader, {
      onDelta,
      onError,
      onTraceComplete: (payload) => {
        const formatted = formatRequestInfoForDisplay(payload);
        if (formatted) onDelta(formatted);
      },
    });
    onDone();
  } catch (err: any) {
    logError("workflow:error", { error: String(err) });
    onError(err instanceof Error ? err : new Error(String(err)));
    onDone();
  }
}

export interface WorkflowContinueParams {
  baseUrl: string;
  entityId: string;
  input: string;
  foundryEndpoint?: string;
  onDelta: (text: string) => void;
  onError: (err: Error) => void;
  onDone: () => void;
}

export async function continueWorkflow(params: WorkflowContinueParams) {
  const { baseUrl, entityId, input, foundryEndpoint, onDelta, onError, onDone } = params;
  try {
    logInfo("workflow:continue", { baseUrl, entityId });
    const url = `${baseUrl.replace(/\/$/, "")}/v1/workflows/${encodeURIComponent(entityId)}/send_responses`;
    const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "text/event-stream" };
    if (foundryEndpoint) {
      headers["x-foundry-endpoint"] = foundryEndpoint;
    }
    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({ input, stream: true }),
    });
    if (!res.ok || !res.body) {
      const text = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status} ${res.statusText}${text ? ` - ${text}` : ""}`);
    }
    const reader = res.body.getReader();
    await parseSSEStream(reader, {
      onDelta,
      onError,
      onTraceComplete: (payload) => {
        const formatted = formatRequestInfoForDisplay(payload);
        if (formatted) onDelta(formatted);
      },
    });
    onDone();
  } catch (err: any) {
    logError("workflow:error", { error: String(err) });
    onError(err instanceof Error ? err : new Error(String(err)));
    onDone();
  }
}
