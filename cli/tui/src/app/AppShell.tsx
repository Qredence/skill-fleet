import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useKeyboard, useRenderer } from "@opentui/react";
import type { HitlPrompt, WorkflowEvent } from "../types";
import {
  createSkillJob,
  fetchHitlPrompt,
  getApiUrl,
  postHitlResponse,
  streamJobEvents,
} from "../api";
import { InputArea } from "../components/InputArea";
import { InputDialog, type DialogKind } from "../components/InputDialog";
import { MessageList, type ChatMessage } from "../components/MessageList";
import { ThinkingPanel } from "../components/ThinkingPanel";
import { ProgressIndicator } from "../components/ProgressIndicator";
import { Footer } from "../components/Footer";

const THEME = {
  background: "#000000",
  panel: "#0a0a0a",
  panelAlt: "#121212",
  border: "#2a2a2a",
  accent: "#22c55e",  // Green accent for activity
  text: "#e5e5e5",
  muted: "#737373",
  error: "#ef4444",
  success: "#22c55e",
};

const HITL_STATUSES = new Set(["pending_user_input", "pending_hitl", "pending_review"]);
const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled", "pending_review"]);

function nowMs(): number {
  return Date.now();
}

function makeId(prefix: string): string {
  try {
    return `${prefix}_${crypto.randomUUID()}`;
  } catch {
    return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`;
  }
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

function sanitizeUserId(input: string): string {
  // Allow only alphanumeric, dash, underscore; max 64 chars
  // This prevents terminal escape sequences and other control characters
  const sanitized = input.replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 64);
  return sanitized || "default";
}

type JobState = {
  id: string;
  status: string;
  phase: string;
  module: string;
};

/**
 * Activity instrumentation for tracking streaming/event activity.
 * Used to provide responsive UI feedback during all event types.
 */
export type ActivitySummary = {
  lastEventAt: number | null;
  lastTokenAt: number | null;
  lastStatusAt: number | null;
  isActive: boolean;
  timeSinceLastEvent: number | null;
};

type DialogState = {
  kind: DialogKind;
  prompt: HitlPrompt;
  openedAt: number;
};

export function AppShell() {
  const renderer = useRenderer();
  const apiUrl = getApiUrl();

  const streamAbortRef = useRef<AbortController | null>(null);
  const lastHitlOpenRef = useRef<number>(0);
  const jobRef = useRef<JobState | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: makeId("m"),
      role: "system",
      content:
        "Skill Fleet TUI - Ready",
      createdAt: nowMs(),
      status: "done",
    },
  ]);

  const [composerText, setComposerText] = useState("");
  const [userId, setUserId] = useState(
    sanitizeUserId(process.env.SKILL_FLEET_USER_ID || "default")
  );
  const [job, setJob] = useState<JobState | null>(null);
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [activeHitlMessageId, setActiveHitlMessageId] = useState<string | null>(null);

  const [thinkingOpen, setThinkingOpen] = useState(false);
  const [thinkingLines, setThinkingLines] = useState<string[]>([]);

  // Track if we're actively receiving streaming data for visual feedback
  const [isStreamingActive, setIsStreamingActive] = useState(false);
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Activity instrumentation: track timestamps for different event types
  const [lastEventAt, setLastEventAt] = useState<number | null>(null);
  const [lastTokenAt, setLastTokenAt] = useState<number | null>(null);
  const [lastStatusAt, setLastStatusAt] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState<number>(nowMs());

  // Update current time periodically for "time since last event" display
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(nowMs());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Compute activity summary for child components
  const activity: ActivitySummary = useMemo(() => {
    const timeSinceLastEvent = lastEventAt ? currentTime - lastEventAt : null;
    // Consider activity "active" if we received an event in the last 3 seconds
    const isActive = timeSinceLastEvent !== null && timeSinceLastEvent < 3000;
    return {
      lastEventAt,
      lastTokenAt,
      lastStatusAt,
      isActive,
      timeSinceLastEvent,
    };
  }, [lastEventAt, lastTokenAt, lastStatusAt, currentTime]);

  useEffect(() => {
    jobRef.current = job;
  }, [job]);

  const composerDisabled = Boolean(dialog) || Boolean(activeHitlMessageId) || (job != null && !TERMINAL_STATUSES.has(job.status));

  const footerLeft = useMemo(() => {
    if (!job) return "Enter send | Shift+Enter newline | Ctrl+T thinking | Esc exit";
    const pieces: string[] = [];
    pieces.push(`Job ${job.id}`);
    if (job.phase) pieces.push(`phase=${job.phase}`);
    if (job.module) pieces.push(`module=${job.module}`);
    if (job.status) pieces.push(`status=${job.status}`);
    return pieces.join(" | ");
  }, [job]);

  const footerRight = useMemo(() => {
    if (dialog) return "Dialog: Enter confirm | Ctrl+S submit";
    if (!job) return `API ${apiUrl}`;
    return `API ${apiUrl}`;
  }, [apiUrl, dialog, job]);

  const ensureStreamingAssistantMessage = useCallback((chunk: string) => {
    if (!chunk) return;

    // Mark streaming as active for visual feedback
    setIsStreamingActive(true);
    if (streamingTimeoutRef.current) {
      clearTimeout(streamingTimeoutRef.current);
    }
    // Clear active state after 500ms of no new chunks
    streamingTimeoutRef.current = setTimeout(() => {
      setIsStreamingActive(false);
    }, 500);

    setMessages((prev) => {
      const next = [...prev];
      const existingIndex = next.findIndex((m) => m.role === "assistant" && m.status === "streaming");
      if (existingIndex >= 0) {
        const cur = next[existingIndex]!;
        next[existingIndex] = { ...cur, content: cur.content + chunk };
        return next.slice(-250);
      }

      next.push({
        id: makeId("m"),
        role: "assistant",
        content: chunk,
        createdAt: nowMs(),
        status: "streaming",
      });
      return next.slice(-250);
    });
  }, []);

  const finalizeStreamingAssistantMessage = useCallback(() => {
    setMessages((prev) =>
      prev.map((m) => (m.role === "assistant" && m.status === "streaming" ? { ...m, status: "done" } : m)),
    );
  }, []);

  const appendThinking = useCallback((line: string) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    setThinkingLines((prev) => [...prev, trimmed].slice(-1200));
  }, []);

  const maybeOpenHitl = useCallback(async (jobId: string) => {
    const now = Date.now();
    // Throttle to avoid opening the same dialog repeatedly while stream polls.
    if (now - lastHitlOpenRef.current < 500) return;
    lastHitlOpenRef.current = now;

    const prompt = await fetchHitlPrompt(jobId);
    const kind = (prompt.type || "clarify") as DialogKind;

    // Inline types: clarify, confirm, structure_fix, deep_understanding
    const inlineTypes = new Set(["clarify", "confirm", "structure_fix", "deep_understanding"]);

    if (inlineTypes.has(kind)) {
      // Check if we already have an unanswered HITL message - prevent duplicates
      const messageId = makeId("hitl");
      let shouldSetActive = false;

      setMessages((prev) => {
        const hasPendingHitl = prev.some(
          (m) => m.role === "hitl" && m.hitlData && !m.hitlData.answered
        );
        if (hasPendingHitl) {
          // Don't add duplicate - already have a pending HITL
          return prev;
        }

        // Check if this prompt is identical to the most recent HITL message
        // This prevents creating duplicate messages when the backend hasn't processed the answer yet
        const lastHitlMessage = [...prev].reverse().find((m) => m.role === "hitl" && m.hitlData);
        if (lastHitlMessage?.hitlData) {
          const lastPrompt = lastHitlMessage.hitlData.prompt;
          const lastQuestions = JSON.stringify(lastPrompt.questions || []);
          const newQuestions = JSON.stringify(prompt.questions || []);
          const lastSummary = lastPrompt.summary || lastPrompt.question || "";
          const newSummary = prompt.summary || prompt.question || "";

          // If questions and summary match, this is the same prompt - don't duplicate
          if (lastQuestions === newQuestions && lastSummary === newSummary) {
            return prev;
          }
        }

        // Mark that we should set this as active after the state update
        shouldSetActive = true;

        // Create an inline HITL message
        return [
          ...prev,
          {
            id: messageId,
            role: "hitl",
            content: prompt.summary || prompt.question || "Please respond",
            createdAt: nowMs(),
            status: "pending_response",
            hitlData: {
              kind: kind as "clarify" | "confirm" | "structure_fix" | "deep_understanding",
              prompt,
              answered: false,
            },
          },
        ]
      });

      // Set active HITL message ID after the message is added
      // This is done outside setMessages to follow React patterns
      if (shouldSetActive) {
        setActiveHitlMessageId(messageId);
      }
    } else {
      // Modal types: preview, validate
      setDialog({ kind, prompt, openedAt: nowMs() });
    }
  }, []);

  const handleStreamEvent = useCallback((event: WorkflowEvent) => {
    const type = asString(event.type);
    const currentJob = jobRef.current;
    const eventTime = nowMs();

    // Record activity timestamp for all events
    setLastEventAt(eventTime);

    if (type === "status") {
      const status = asString(event.status);
      setLastStatusAt(eventTime);
      setJob((prev) => {
        if (!prev) return prev;
        return { ...prev, status: status || prev.status };
      });
      if (currentJob && HITL_STATUSES.has(status)) {
        void maybeOpenHitl(currentJob.id);
      }
      if (TERMINAL_STATUSES.has(status)) {
        finalizeStreamingAssistantMessage();
      }
      return;
    }

    if (type === "hitl_pause") {
      if (currentJob) void maybeOpenHitl(currentJob.id);
      return;
    }

    if (type === "phase_start" || type === "phase_end") {
      const phase = asString(event.phase);
      setJob((prev) => (prev ? { ...prev, phase: phase || prev.phase } : prev));
      appendThinking(`${type}: ${asString(event.message)}`);
      return;
    }

    if (type === "module_start" || type === "module_end") {
      const moduleName = asString(event.data?.module);
      setJob((prev) => (prev ? { ...prev, module: moduleName || prev.module } : prev));
      appendThinking(`${type}: ${asString(event.message)}`);
      return;
    }

    if (type === "reasoning" || type === "progress") {
      const msg = asString(event.message);
      const reasoning = asString(event.data?.reasoning);
      const detail = reasoning ? `${msg}\n${reasoning}` : msg;
      appendThinking(detail);
      return;
    }

    if (type === "token_stream") {
      const chunk = asString(event.data?.chunk) || asString(event.message);
      setLastTokenAt(eventTime);
      ensureStreamingAssistantMessage(chunk);
      return;
    }

    if (type === "error") {
      const msg = asString(event.message);
      setMessages((prev) => [
        ...prev,
        { id: makeId("m"), role: "system", content: `Error: ${msg}`, createdAt: nowMs(), status: "done" },
      ]);
      finalizeStreamingAssistantMessage();
      return;
    }

    if (type === "complete") {
      finalizeStreamingAssistantMessage();
      return;
    }
  }, [finalizeStreamingAssistantMessage]);

  useEffect(() => {
    if (!job) return;

    streamAbortRef.current?.abort();
    const controller = new AbortController();
    streamAbortRef.current = controller;

    void streamJobEvents(job.id, handleStreamEvent, controller.signal).catch((err) => {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId("m"),
          role: "system",
          content: `Stream error: ${asString(err)}`,
          createdAt: nowMs(),
          status: "done",
        },
      ]);
    });

    return () => controller.abort();
  }, [job?.id, handleStreamEvent]);

  useKeyboard((key) => {
    if (key.ctrl && key.name === "t") {
      setThinkingOpen((v) => !v);
      return;
    }
    if (key.name === "escape") {
      renderer.destroy();
      return;
    }
  });

  const startJob = useCallback(async () => {
    const task = composerText.trim();
    if (task.length < 3) return;

    setMessages((prev) => [
      ...prev,
      { id: makeId("m"), role: "user", content: task, createdAt: nowMs(), status: "done" },
    ]);
    setComposerText("");
    setThinkingLines([]);

    const response = await createSkillJob(task, userId);
    const jobId = asString(response.job_id);
    if (!jobId) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId("m"),
          role: "system",
          content: `Failed to create job: ${asString(response.error)}`,
          createdAt: nowMs(),
          status: "done",
        },
      ]);
      return;
    }

    setJob({ id: jobId, status: "running", phase: "", module: "" });
  }, [composerText, userId]);

  const submitHitl = useCallback(async (payload: Record<string, unknown>) => {
    if (!job) return;
    await postHitlResponse(job.id, payload);
    setDialog(null);
  }, [job]);

  const submitInlineHitl = useCallback(async (messageId: string, payload: Record<string, unknown>) => {
    if (!job) return;

    // Mark the message as answered with the response
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId && m.hitlData
          ? {
              ...m,
              status: "done" as const,
              hitlData: {
                ...m.hitlData,
                answered: true,
                answer: payload,
              },
            }
          : m,
      ),
    );

    // Clear active HITL message
    setActiveHitlMessageId(null);

    // Submit to backend
    await postHitlResponse(job.id, payload);

    // Check if backend has a new HITL prompt waiting (common in multi-round flows)
    // Use longer delay to allow backend to process the response first
    setTimeout(() => {
      void maybeOpenHitl(job.id);
    }, 1500);
  }, [job, maybeOpenHitl]);

  const layoutThinking = thinkingOpen ? (
    <ThinkingPanel
      theme={THEME}
      lines={thinkingLines}
      isActive={isStreamingActive || Boolean(job && !TERMINAL_STATUSES.has(job.status))}
    />
  ) : null;

  // Check if any message is currently streaming
  const hasStreamingMessage = messages.some((m) => m.status === "streaming");

  return (
    <box flexDirection="column" width="100%" height="100%" backgroundColor={THEME.background}>
      <box flexDirection="row" flexGrow={1}>
        <box
          flexDirection="column"
          flexGrow={1}
        >
          <MessageList
            theme={THEME}
            messages={messages}
            onHitlSubmit={submitInlineHitl}
            activeHitlMessageId={activeHitlMessageId}
          />

          {job ? (
            <ProgressIndicator
              theme={THEME}
              phase={job.phase}
              module={job.module}
              status={job.status}
              isStreaming={hasStreamingMessage || isStreamingActive}
              activity={activity}
            />
          ) : null}

          <InputArea
            theme={THEME}
            value={composerText}
            onChange={setComposerText}
            onSubmit={startJob}
            focused={!dialog && !activeHitlMessageId}
            disabled={composerDisabled}
          />
        </box>

        {layoutThinking}
      </box>

      <Footer theme={THEME} left={footerLeft} right={footerRight} activity={activity} />

      {dialog ? (
        <InputDialog
          key={`${dialog.kind}_${dialog.openedAt}`}
          theme={THEME}
          kind={dialog.kind}
          prompt={dialog.prompt}
          onSubmit={submitHitl}
          onClose={() => setDialog(null)}
        />
      ) : null}

    </box>
  );
}
