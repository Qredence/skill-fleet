import { useCallback, useReducer } from "react";
import type { WorkflowEvent } from "../../lib/types";

type JobStatus =
  | "idle"
  | "running"
  | "pending_user_input"
  | "pending_hitl"
  | "pending_review"
  | "completed"
  | "failed"
  | "cancelled";

type JobState = {
  id: string | null;
  status: JobStatus;
  phase: string;
  module: string;
  thinking: string[];
  isStreaming: boolean;
};

type JobAction =
  | { type: "CREATE"; id: string }
  | { type: "STATUS_CHANGE"; status: JobStatus }
  | { type: "PHASE_CHANGE"; phase: string }
  | { type: "MODULE_CHANGE"; module: string }
  | { type: "ADD_THINKING"; line: string }
  | { type: "SET_STREAMING"; streaming: boolean }
  | { type: "COMPLETE" }
  | { type: "RESET" };

const initialState: JobState = {
  id: null,
  status: "idle",
  phase: "",
  module: "",
  thinking: [],
  isStreaming: false,
};

const MAX_THINKING_LINES = 1200;

function jobReducer(state: JobState, action: JobAction): JobState {
  switch (action.type) {
    case "CREATE":
      return { ...initialState, id: action.id, status: "running" };
    case "STATUS_CHANGE":
      return { ...state, status: action.status };
    case "PHASE_CHANGE":
      return { ...state, phase: action.phase };
    case "MODULE_CHANGE":
      return { ...state, module: action.module };
    case "ADD_THINKING":
      return {
        ...state,
        thinking: [...state.thinking, action.line].slice(-MAX_THINKING_LINES),
      };
    case "SET_STREAMING":
      return { ...state, isStreaming: action.streaming };
    case "COMPLETE":
      return { ...state, isStreaming: false };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

export function useJobManager() {
  const [state, dispatch] = useReducer(jobReducer, initialState);

  const createJob = useCallback((id: string) => {
    dispatch({ type: "CREATE", id });
  }, []);

  const handleEvent = useCallback((event: WorkflowEvent) => {
    switch (event.type) {
      case "status":
        dispatch({ type: "STATUS_CHANGE", status: event.status as JobStatus });
        break;
      case "phase_start":
      case "phase_end":
        if (event.phase) {
          dispatch({ type: "PHASE_CHANGE", phase: event.phase });
        }
        dispatch({
          type: "ADD_THINKING",
          line: `${event.type}: ${event.message || ""}`,
        });
        break;
      case "module_start":
      case "module_end":
        if (event.data?.module) {
          dispatch({
            type: "MODULE_CHANGE",
            module: String(event.data.module),
          });
        }
        dispatch({
          type: "ADD_THINKING",
          line: `${event.type}: ${event.message || ""}`,
        });
        break;
      case "reasoning":
      case "progress":
        dispatch({
          type: "ADD_THINKING",
          line: `${event.message || ""}${event.data?.reasoning ? `\n${event.data.reasoning}` : ""}`,
        });
        break;
      case "token_stream":
        dispatch({ type: "SET_STREAMING", streaming: true });
        break;
      case "error":
        dispatch({ type: "STATUS_CHANGE", status: "failed" });
        dispatch({
          type: "ADD_THINKING",
          line: `Error: ${event.message || ""}`,
        });
        break;
      case "complete":
        dispatch({ type: "COMPLETE" });
        break;
    }
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const isWaitingForInput =
    state.status === "pending_user_input" ||
    state.status === "pending_hitl" ||
    state.status === "pending_review";

  const isTerminal =
    state.status === "completed" ||
    state.status === "failed" ||
    state.status === "cancelled";

  return {
    state,
    createJob,
    handleEvent,
    reset,
    isWaitingForInput,
    isTerminal,
  };
}
