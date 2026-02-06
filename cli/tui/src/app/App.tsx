import { useCallback, useEffect, useState } from "react";
import { createRoot, useKeyboard, useRenderer } from "@opentui/react";
import { createCliRenderer } from "@opentui/core";
import type { HitlPrompt, WorkflowEvent } from "../lib/types";
import { createSkillJob, postHitlResponse, fetchHitlPrompt } from "../lib/api";
import { THEME } from "../lib/theme";
import { useJobManager } from "../features/job/JobManager";
import { useStreamHandler } from "../features/job/StreamHandler";
import { ChatView } from "../features/chat/ChatView";
import { HitlManager } from "../features/hitl/HitlManager";

type Message = {
  id: string;
  role: "system" | "user" | "assistant" | "hitl";
  content: string;
  status: "streaming" | "done";
};

function makeId(prefix: string): string {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`;
}

function App() {
  const renderer = useRenderer();
  const { state: jobState, createJob, handleEvent, isWaitingForInput, isTerminal } = useJobManager();
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: makeId("m"),
      role: "system",
      content: "Skill Fleet TUI - Ready",
      status: "done",
    },
  ]);
  const [hitlPrompt, setHitlPrompt] = useState<HitlPrompt | null>(null);
  const [focusedArea, setFocusedArea] = useState<"chat" | "hitl">("chat");

  const streamState = useStreamHandler(
    jobState.id,
    useCallback(
      (event: WorkflowEvent) => {
        handleEvent(event);

        if (event.type === "token_stream") {
          const chunk = String(event.data?.chunk || event.message || "");
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && last.status === "streaming") {
              return [
                ...prev.slice(0, -1),
                { ...last, content: last.content + chunk },
              ];
            }
            return [
              ...prev,
              {
                id: makeId("m"),
                role: "assistant",
                content: chunk,
                status: "streaming",
              },
            ];
          });
        }

        if (
          event.type === "status" &&
          (event.status === "pending_user_input" ||
            event.status === "pending_hitl" ||
            event.status === "pending_review")
        ) {
          if (jobState.id) {
            fetchHitlPrompt(jobState.id).then((prompt) => {
              setHitlPrompt(prompt);
              setFocusedArea("hitl");
            });
          }
        }
      },
      [handleEvent, jobState.id]
    )
  );

  const handleSubmit = useCallback(async () => {
    const task = inputValue.trim();
    if (!task || task.length < 3) return;

    if (isTerminal) {
      setMessages([
        {
          id: makeId("m"),
          role: "system",
          content: "─── Starting new session ───",
          status: "done",
        },
        { id: makeId("m"), role: "user", content: task, status: "done" },
      ]);
      setInputValue("");
    } else {
      setMessages((prev) => [
        ...prev,
        { id: makeId("m"), role: "user", content: task, status: "done" },
      ]);
      setInputValue("");
    }

    try {
      const response = await createSkillJob(task, "default");
      if (response.job_id) {
        createJob(response.job_id);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: makeId("m"),
            role: "system",
            content: `Error: ${response.error || "Failed to create job"}`,
            status: "done",
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId("m"),
          role: "system",
          content: `Error: ${err}`,
          status: "done",
        },
      ]);
    }
  }, [inputValue, isTerminal, createJob]);

  const handleHitlSubmit = useCallback(
    async (payload: Record<string, unknown>) => {
      if (!jobState.id || !hitlPrompt) return;

      try {
        await postHitlResponse(jobState.id, payload);
        setHitlPrompt(null);
        setFocusedArea("chat");
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            id: makeId("m"),
            role: "system",
            content: `Failed to submit: ${err}`,
            status: "done",
          },
        ]);
      }
    },
    [jobState.id, hitlPrompt]
  );

  useKeyboard((key) => {
    const isEnter = key.name === "enter" || key.name === "return";

    if (key.name === "escape") {
      if (hitlPrompt) {
        setHitlPrompt(null);
        setFocusedArea("chat");
      } else {
        renderer.destroy();
      }
    }
    if (key.name === "tab" && hitlPrompt) {
      setFocusedArea((v) => (v === "chat" ? "hitl" : "chat"));
    }
    // Ctrl+C to exit
    if (key.ctrl && key.name === "c") {
      renderer.destroy();
    }
  });

  return (
    <box
      flexDirection="column"
      width="100%"
      height="100%"
      backgroundColor={THEME.background}
      padding={1}
    >
      <box flexDirection="column" flexGrow={1}>
        <ChatView
          messages={messages}
          inputValue={inputValue}
          onInputChange={setInputValue}
          onSubmit={handleSubmit}
          isDisabled={isWaitingForInput || (!isTerminal && !!jobState.id)}
          disabledReason={
            isWaitingForInput
              ? "waiting for input"
              : jobState.id
                ? "job running"
                : undefined
          }
          focused={focusedArea === "chat"}
        />

        {hitlPrompt ? (
          <box
            border
            borderColor={THEME.border}
            backgroundColor={THEME.panel}
            padding={1}
            marginTop={1}
          >
            <HitlManager
              prompt={hitlPrompt}
              focused={focusedArea === "hitl"}
              onSubmit={handleHitlSubmit}
            />
          </box>
        ) : null}
      </box>

      <box flexDirection="row" gap={2} marginTop={1}>
        <text fg={THEME.muted}>
          {jobState.id
            ? `[${jobState.id}] ${jobState.phase || "idle"}`
            : "No job"}
        </text>
        {streamState.status === "reconnecting" ? (
          <text fg={THEME.error}>
            Reconnecting... ({streamState.attemptNumber})
          </text>
        ) : null}
      </box>
    </box>
  );
}

export async function main() {
  const renderer = await createCliRenderer();
  createRoot(renderer).render(<App />);
}
