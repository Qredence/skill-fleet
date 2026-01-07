export type PendingRequest = {
  requestId: string;
  sourceExecutorId: string;
  prompt: string;
  conversation: { role: string; author_name?: string | null; text: string }[];
};

interface ConversationMessage {
  role: string;
  author_name?: string | null;
  text: string;
}

interface RequestInfoPayload {
  data?: {
    trace_type?: string;
    event_type?: string;
    data?: {
      request_info?: {
        request_id?: string;
        source_executor_id?: string;
        data?: {
          prompt?: string;
          conversation?: unknown[];
        };
      };
    };
    request_info?: {
      request_id?: string;
      source_executor_id?: string;
      data?: {
        prompt?: string;
        conversation?: unknown[];
      };
    };
  };
  request_info?: {
    request_id?: string;
    source_executor_id?: string;
    data?: {
      prompt?: string;
      conversation?: unknown[];
    };
  };
}

export function parseRequestInfoEvent(payload: unknown): PendingRequest | null {
  try {
    const p = payload as RequestInfoPayload;
    const data = p?.data;
    if (data?.trace_type !== "workflow_info" || data?.event_type !== "RequestInfoEvent") return null;
    const ri = data?.data?.request_info || p?.request_info;
    if (!ri?.request_id) return null;
    
    const conversation = Array.isArray(ri.data?.conversation) 
      ? ri.data.conversation.filter((m): m is ConversationMessage => {
          if (typeof m !== 'object' || m === null) return false;
          const { role, text } = m as ConversationMessage;
          return typeof role === 'string' && typeof text === 'string';
        })
      : [];
    
    return {
      requestId: ri.request_id,
      sourceExecutorId: ri.source_executor_id || "",
      prompt: ri.data?.prompt || "",
      conversation,
    };
  } catch {
    return null;
  }
}

/**
 * Format RequestInfoEvent data as a readable inline message for display.
 * Consolidates duplicate formatting logic from streaming functions.
 */
export function formatRequestInfoForDisplay(payload: unknown): string | null {
  try {
    const p = payload as RequestInfoPayload;
    const data = p?.data;
    if (
      data?.trace_type === "workflow_info" &&
      data?.event_type === "RequestInfoEvent"
    ) {
      const ri = data?.data?.request_info || p?.request_info;
      if (ri?.request_id) {
        const prompt = ri.data?.prompt || "";
        const conversation = Array.isArray(ri.data?.conversation) 
          ? ri.data.conversation.filter((m): m is ConversationMessage => 
              typeof m === 'object' && m !== null && 
              typeof (m as ConversationMessage).role === 'string' && 
              typeof (m as ConversationMessage).text === 'string'
            )
          : [];
        let inlineText = prompt;
        if (conversation.length > 0) {
          inlineText += "\n\nRecent messages:";
          conversation.slice(-5).forEach((m) => {
            inlineText += `\n- ${m.author_name || m.role}: ${m.text}`;
          });
        }
        return inlineText ? "\n\n" + inlineText : null;
      }
    }
  } catch {
    // Ignore parse errors
  }
  return null;
}
