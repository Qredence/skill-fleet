import type { KeyBinding } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { useEffect, useMemo, useState } from "react";
import type { HitlPrompt } from "../types";
import { MarkdownView } from "./MarkdownView";
import { Selector, type SelectorOption } from "./Selector";
import { ControlledTextarea } from "./ControlledTextarea";

type Theme = {
  background: string;
  panel: string;
  panelAlt: string;
  border: string;
  accent: string;
  text: string;
  muted: string;
  error: string;
};

// Only preview and validate are handled as modal dialogs now
// clarify, confirm, structure_fix, deep_understanding are inline
export type DialogKind = "preview" | "validate";

type Props = {
  theme: Theme;
  kind: DialogKind;
  prompt: HitlPrompt;
  onSubmit: (payload: Record<string, unknown>) => void;
  onClose: () => void;
};

export function InputDialog({ theme, kind, prompt, onSubmit, onClose }: Props) {
  const keyBindings = useMemo<KeyBinding[]>(
    () => [
      { name: "return", action: "submit" },
      { name: "enter", action: "submit" },
      { name: "return", shift: true, action: "newline" },
      { name: "enter", shift: true, action: "newline" },
    ],
    [],
  );

  const [action, setAction] = useState<string>("proceed");
  const [feedback, setFeedback] = useState<string>("");
  const [focus, setFocus] = useState<"action" | "feedback">("action");

  const textareaTheme = useMemo(
    () => ({ panelAlt: theme.panelAlt, text: theme.text, muted: theme.muted }),
    [theme.panelAlt, theme.text, theme.muted],
  );

  useEffect(() => {
    setAction("proceed");
    setFeedback("");
    setFocus("action");
  }, [kind]);

  useKeyboard((key) => {
    // Debug logging
    console.log("[InputDialog] key event:", key.name, "ctrl:", key.ctrl, "shift:", key.shift);

    const isEnter = key.name === "enter" || key.name === "return";
    if ((key.ctrl && key.name === "s") || (key.ctrl && isEnter)) {
      console.log("[InputDialog] Ctrl+S or Ctrl+Enter detected, submitting dialog");
      onSubmit({ action, feedback });
      return;
    }
    if (key.name === "escape") {
      onClose();
      return;
    }
    if (key.name === "tab") {
      setFocus((v) => (v === "action" ? "feedback" : "action"));
      return;
    }
  });

  const headerTitle = (() => {
    if (kind === "preview") return "Preview Skill";
    if (kind === "validate") return "Review Validation";
    return "Dialog";
  })();

  const content = (() => {
    if (kind === "preview") return prompt.content || "";
    if (kind === "validate") return (prompt.report || "") + (prompt.content ? `\n\n---\n\n${prompt.content}` : "");
    return "";
  })();

  const highlights = prompt.highlights?.length ? `\n\nHighlights:\n- ${prompt.highlights.join("\n- ")}` : "";
  const showHighlights = kind === "preview" && Boolean(highlights);

  const actionOptions: SelectorOption[] = (() => {
    if (kind === "preview") {
      return [
        { id: "proceed", label: "Proceed", description: "Continue to validation" },
        { id: "refine", label: "Refine", description: "Make modifications" },
        { id: "cancel", label: "Cancel", description: "Stop this job" },
      ];
    }
    if (kind === "validate") {
      return [
        { id: "proceed", label: "Proceed", description: "Accept and finish" },
        { id: "refine", label: "Refine", description: "Improve and re-validate" },
        { id: "cancel", label: "Cancel", description: "Stop this job" },
      ];
    }
    return [{ id: "proceed", label: "Proceed" }];
  })();

  const needsFeedback = action === "refine";
  const feedbackLabel = "Refinement request";

  const doSubmit = (act: string, fb: string) => {
    onSubmit({ action: act, feedback: fb });
  };

  const body = (
    <box flexDirection="column" gap={1}>
      <MarkdownView content={content + (showHighlights ? highlights : "")} />

      <text fg={theme.muted}>Action</text>
      <Selector
        mode="single"
        theme={theme}
        options={actionOptions}
        selectedId={action}
        focused={focus === "action"}
        onChange={setAction}
        onSelect={(id) => {
          setAction(id);
          if (id === "proceed" || id === "cancel") {
            doSubmit(id, "");
            return;
          }
          setFocus("feedback");
        }}
      />

      {needsFeedback ? (
        <box flexDirection="column" gap={1}>
          <text fg={theme.muted}>{feedbackLabel}</text>
          <ControlledTextarea
            theme={textareaTheme}
            value={feedback}
            onChange={setFeedback}
            onSubmit={() => doSubmit(action, feedback)}
            keyBindings={keyBindings}
            wrapText
            height={6}
            focused={focus === "feedback"}
            placeholder="Type your feedback..."
          />
        </box>
      ) : null}

      <text fg={theme.muted}>Enter confirm | Tab switch | Ctrl+S submit | Esc close</text>
    </box>
  );

  return (
    <box
      position="absolute"
      left={0}
      top={0}
      width="100%"
      height="100%"
      justifyContent="center"
      alignItems="center"
      backgroundColor="rgba(0,0,0,0.6)"
    >
      <box
        width={72}
        height={24}
        border
        borderStyle="double"
        borderColor={theme.border}
        backgroundColor={theme.panel}
        padding={2}
        flexDirection="column"
        gap={1}
      >
        <box flexDirection="row" justifyContent="space-between" alignItems="center">
          <text fg={theme.text}>
            <strong>{headerTitle}</strong>
          </text>
          <text fg={theme.muted}>{prompt.current_phase || ""}</text>
        </box>

        <scrollbox flexGrow={1} stickyScroll stickyStart="bottom" border borderColor={theme.border} padding={1}>
          {body}
        </scrollbox>
      </box>
    </box>
  );
}
