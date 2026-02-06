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
import { getConfig } from "../config";
import { InputArea } from "../components/InputArea";
import { InputDialog, type DialogKind } from "../components/InputDialog";
import { MessageList, type ChatMessage, type MessageListHandle } from "../components/MessageList";
import { ThinkingPanel } from "../components/ThinkingPanel";
import { ProgressIndicator } from "../components/ProgressIndicator";
import { Footer } from "../components/Footer";
import { useActivityTracking } from "../hooks/useActivityTracking";

// Duration to show the "jumped to bottom" indicator
const JUMP_INDICATOR_DURATION_MS = 1200;

/**
 * Maximum number of messages to retain in the chat history.
 * When this limit is exceeded, oldest messages are silently removed.
 * This prevents memory issues during long sessions while keeping
 * the most recent context visible.
 *
 * Note: Old messages are removed without notification to the user.
 * Consider adding a visual indicator if this becomes confusing.
 */
const MAX_MESSAGE_HISTORY = 250;

/**
 * Maximum number of thinking lines to retain in the thinking panel.
 */
const MAX_THINKING_LINES = 1200;

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

type JobState = {
  id: string;
  status: string;
  phase: string;
  module: string;
};

type DialogState = {
  kind: DialogKind;
  prompt: HitlPrompt;
  openedAt: number;
};

export function AppShell() {
  const renderer = useRenderer();
  const config = getConfig();
  const apiUrl = getApiUrl();

  const streamAbortRef = useRef<AbortController | null>(null);
  const lastHitlOpenRef = useRef<number>(0);
  const jobRef = useRef<JobState | null>(null);
  const messageListRef = useRef<MessageListHandle>(null);
  const jumpIndicatorTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Ref to hold latest stream event handler to avoid re-subscription on callback changes
  const handleStreamEventRef = useRef<(event: WorkflowEvent) => void>(() => {});

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
  const [userId] = useState(config.SKILL_FLEET_USER_ID);
  const [job, setJob] = useState<JobState | null>(null);
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [activeHitlMessageId, setActiveHitlMessageId] = useState<string | null>(null);

  const [thinkingOpen, setThinkingOpen] = useState(false);
  const [thinkingLines, setThinkingLines] = useState<string[]>([]);
  const [showJumpedToBottom, setShowJumpedToBottom] = useState(false);
  const [jobError, setJobError] = useState<string | null>(null);
  const [staleConnectionWarning, setStaleConnectionWarning] = useState<string | null>(null);

  // Track last sequence number for stale detection
  const lastSequenceRef = useRef<number | null>(null);

  // Track if we're actively receiving streaming data for visual feedback
  const [isStreamingActive, setIsStreamingActive] = useState(false);
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hitlRecheckTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Activity instrumentation: track timestamps for different event types
  const {
    activity,
    currentTime,
    setLastEventAt,
    setLastTokenAt,
    setLastStatusAt,
  } = useActivityTracking();

  // Cleanup timeout refs on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (streamingTimeoutRef.current) clearTimeout(streamingTimeoutRef.current);
      if (hitlRecheckTimeoutRef.current) clearTimeout(hitlRecheckTimeoutRef.current);
      if (jumpIndicatorTimeoutRef.current) clearTimeout(jumpIndicatorTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    jobRef.current = job;
  }, [job]);

  const composerDisabled = Boolean(dialog) || Boolean(activeHitlMessageId) || (job != null && !TERMINAL_STATUSES.has(job.status));

  // Detect if job is in HITL waiting state
  const isWaitingForInput = job ? HITL_STATUSES.has(job.status) : false;

  // Compute disabled reason for InputArea
  const inputDisabledReason = useMemo(() => {
    if (dialog) return "answering dialog";
    if (activeHitlMessageId) return "responding to question";
    if (job && isWaitingForInput) return "waiting for your answer";
    if (job && !TERMINAL_STATUSES.has(job.status)) return "job running";
    return undefined;
  }, [activeHitlMessageId, dialog, isWaitingForInput, job]);

  const footerLeft = useMemo(() => {
    // Show stale connection warning if present
    if (staleConnectionWarning) {
      return staleConnectionWarning;
    }

    if (!job) return "Enter send | Shift+Enter newline | Ctrl+T thinking | Esc exit";

    // When waiting for HITL input, show prominent message
    if (HITL_STATUSES.has(job.status)) {
      return `[${job.id}] ⚠ WAITING FOR INPUT - respond to continue`;
    }

    // Concise format: Job ID → Phase → Status
    const parts: string[] = [`[${job.id}]`];
    if (job.phase) parts.push(job.phase);
    if (job.module) parts.push(`→ ${job.module}`);
    if (job.status && !TERMINAL_STATUSES.has(job.status)) {
      parts.push(`(${job.status})`);
    } else if (job.status) {
      parts.push(`✓ ${job.status}`);
    }
    return parts.join(" ");
  }, [job, staleConnectionWarning]);

  const footerRight = useMemo(() => {
    if (dialog) return "Dialog: Enter confirm | Ctrl+S submit";
    if (isWaitingForInput) return "↑ Answer above to continue";
    if (!job) return `API ${apiUrl}`;
    return `API ${apiUrl}`;
  }, [apiUrl, dialog, isWaitingForInput, job]);

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
        return next.slice(-MAX_MESSAGE_HISTORY);
      }

      next.push({
        id: makeId("m"),
        role: "assistant",
        content: chunk,
        createdAt: nowMs(),
        status: "streaming",
      });
      return next.slice(-MAX_MESSAGE_HISTORY);
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
    setThinkingLines((prev) => [...prev, trimmed].slice(-MAX_THINKING_LINES));
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

    // Detect stale connections via sequence gaps (ignore heartbeats and meta-events with sequence -1)
    if (typeof event.sequence === "number" && event.sequence > 0) {
      if (lastSequenceRef.current !== null && event.sequence !== lastSequenceRef.current + 1) {
        const gap = event.sequence - (lastSequenceRef.current + 1);
        setStaleConnectionWarning(`⚠ Stale connection: ${gap} event(s) missed`);
        // Auto-clear warning after 3 seconds
        setTimeout(() => setStaleConnectionWarning(null), 3000);
      }
      lastSequenceRef.current = event.sequence;
    }

    // Keep isStreamingActive "hot" for any WorkflowEvent, not just token_stream
    // This provides responsive UI feedback during non-token events (progress, phase, module, etc.)
    setIsStreamingActive(true);
    if (streamingTimeoutRef.current) {
      clearTimeout(streamingTimeoutRef.current);
    }
    // Clear active state after 2s of no events (longer window for non-token activity)
    streamingTimeoutRef.current = setTimeout(() => {
      setIsStreamingActive(false);
    }, 2000);

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
  }, [appendThinking, ensureStreamingAssistantMessage, finalizeStreamingAssistantMessage, maybeOpenHitl]);

  // Keep the ref updated with the latest handler
  useEffect(() => {
    handleStreamEventRef.current = handleStreamEvent;
  }, [handleStreamEvent]);

  useEffect(() => {
    if (!job) return;

    streamAbortRef.current?.abort();
    const controller = new AbortController();
    streamAbortRef.current = controller;

    // Use ref-based handler to avoid re-subscription when callbacks change
    const stableHandler = (event: WorkflowEvent) => {
      handleStreamEventRef.current(event);
    };

    void streamJobEvents(job.id, stableHandler, controller.signal).catch((err) => {
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
  }, [job?.id]); // Only re-subscribe when job ID changes

  // Helper to show jump-to-bottom indicator with auto-hide
  const showJumpIndicator = useCallback(() => {
    setShowJumpedToBottom(true);
    if (jumpIndicatorTimeoutRef.current) {
      clearTimeout(jumpIndicatorTimeoutRef.current);
    }
    jumpIndicatorTimeoutRef.current = setTimeout(() => {
      setShowJumpedToBottom(false);
    }, JUMP_INDICATOR_DURATION_MS);
  }, []);

  useKeyboard((key) => {
    // Core navigation shortcuts (always active)
    if (key.ctrl && key.name === "t") {
      setThinkingOpen((v) => !v);
      return;
    }
    if (key.name === "escape") {
      renderer.destroy();
      return;
    }

    // Scroll navigation (works without stealing focus from input)
    // PageUp / Ctrl+U: scroll up half-page
    if (key.name === "pageup" || (key.ctrl && key.name === "u")) {
      messageListRef.current?.scrollPageUp();
      return;
    }

    // PageDown / Ctrl+D: scroll down half-page
    if (key.name === "pagedown" || (key.ctrl && key.name === "d")) {
      messageListRef.current?.scrollPageDown();
      return;
    }

    // End: jump to bottom with visual confirmation
    if (key.name === "end") {
      messageListRef.current?.scrollToBottom();
      showJumpIndicator();
      return;
    }

    // Home: jump to top
    if (key.name === "home") {
      messageListRef.current?.scrollToTop();
      return;
    }

    // Shift+G: jump to bottom (vim-style, Shift to avoid conflict with text input)
    if (key.shift && key.name === "g") {
      messageListRef.current?.scrollToBottom();
      showJumpIndicator();
      return;
    }

    // Shift+g (lowercase g with shift): also jump to bottom
    // gg would be nice for top, but conflicts with typing
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
    setJobError(null);
    setStaleConnectionWarning(null);
    lastSequenceRef.current = null;

    try {
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
      setJobError(null);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [
        ...prev,
        {
          id: makeId("m"),
          role: "system",
          content: `Failed to create job: ${errMsg}`,
          createdAt: nowMs(),
          status: "done",
        },
      ]);
      setJobError(errMsg);
    }
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
    // Clear any existing recheck timeout to avoid duplicates
    if (hitlRecheckTimeoutRef.current) {
      clearTimeout(hitlRecheckTimeoutRef.current);
    }
    const currentJobId = job.id;
    hitlRecheckTimeoutRef.current = setTimeout(() => {
      hitlRecheckTimeoutRef.current = null; // Clear ref after execution to prevent stale cleanup
      void maybeOpenHitl(currentJobId);
    }, 1500);
  }, [job, maybeOpenHitl]);

  const layoutThinking = thinkingOpen ? (
    <ThinkingPanel
      theme={THEME}
      lines={thinkingLines}
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
            ref={messageListRef}
            theme={THEME}
            messages={messages}
            onHitlSubmit={submitInlineHitl}
            activeHitlMessageId={activeHitlMessageId}
            activity={activity}
            showJumpedToBottom={showJumpedToBottom}
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
            disabledReason={inputDisabledReason}
            error={jobError || undefined}
          />
        </box>

        {layoutThinking}
      </box>

      <Footer theme={THEME} left={footerLeft} right={footerRight} activity={activity} currentTime={currentTime} />

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

      {staleConnectionWarning ? (
        <box
          position="absolute"
          bottom={2}
          left={2}
          width={staleConnectionWarning.length + 2}
          height={1}
          backgroundColor={THEME.error}
        >
          <text fg="#ffffff">{staleConnectionWarning}</text>
        </box>
      ) : null}

    </box>
  );
}
