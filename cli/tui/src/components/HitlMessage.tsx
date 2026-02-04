import type { KeyBinding } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { useEffect, useMemo, useState } from "react";
import type { HitlPrompt, StructuredQuestion } from "../types";
import { MarkdownView } from "./MarkdownView";
import { Selector, type SelectorOption } from "./Selector";
import { ControlledTextarea } from "./ControlledTextarea";

type Theme = {
  panel: string;
  panelAlt: string;
  border: string;
  accent: string;
  text: string;
  muted: string;
  error: string;
};

type ClarifyAnswer = {
  selectedOptionIds: string[];
  otherText: string;
  freeText: string;
};

type Props = {
  theme: Theme;
  kind: "clarify" | "confirm" | "structure_fix" | "deep_understanding";
  prompt: HitlPrompt;
  answered?: boolean;
  answer?: Record<string, unknown>;
  onSubmit: (payload: Record<string, unknown>) => void;
  focused: boolean;
};

function getQuestionMode(q: StructuredQuestion): "single" | "multi" | "text" {
  const hasOptions = (q.options?.length ?? 0) > 0;
  if (!hasOptions) return "text";

  // Only use multi mode if explicitly set
  // Check allows_multiple strictly (must be true, not just truthy)
  if (q.allows_multiple === true) return "multi";

  // Check question_type only if it explicitly says "multiple_choice" or similar multi indicators
  const qt = String(q.question_type || "").toLowerCase();
  if (qt === "multiple_select" || qt === "multi_select" || qt === "checkbox") return "multi";

  // Default to single select for all other cases with options
  return "single";
}

function defaultAnswer(): ClarifyAnswer {
  return { selectedOptionIds: [], otherText: "", freeText: "" };
}

function buildClarifySummary(questions: StructuredQuestion[], answers: Record<number, ClarifyAnswer>): string {
  const lines: string[] = [];
  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    if (!q) continue;
    const a = answers[i];
    if (!a) continue;

    lines.push(`Q${i + 1}: ${q.text}`);

    const opts = q.options || [];
    const selectedLabels = opts
      .filter((o) => a.selectedOptionIds.includes(o.id))
      .map((o) => o.label);
    if (selectedLabels.length) lines.push(`- Selected: ${selectedLabels.join(", ")}`);
    if (a.otherText.trim()) lines.push(`- Other: ${a.otherText.trim()}`);
    if (a.freeText.trim()) lines.push(`- Answer: ${a.freeText.trim()}`);
    lines.push("");
  }
  return lines.join("\n").trim();
}

export function HitlMessage({ theme, kind, prompt, answered, answer, onSubmit, focused }: Props) {
  const keyBindings = useMemo<KeyBinding[]>(
    () => [
      { name: "return", action: "submit" },
      { name: "enter", action: "submit" },
      { name: "return", shift: true, action: "newline" },
      { name: "enter", shift: true, action: "newline" },
    ],
    [],
  );

  const questions = (prompt.questions || []) as StructuredQuestion[];

  const [clarifyIndex, setClarifyIndex] = useState(0);
  const [clarifyAnswers, setClarifyAnswers] = useState<Record<number, ClarifyAnswer>>({});
  const [clarifyFocus, setClarifyFocus] = useState<"options" | "submit" | "other" | "freeText">("options");

  const [action, setAction] = useState<string>("proceed");
  const [feedback, setFeedback] = useState<string>("");
  const [focus, setFocus] = useState<"action" | "feedback">("action");

  const [structureFixName, setStructureFixName] = useState<string>(prompt.current_skill_name || "");
  const [structureFixDesc, setStructureFixDesc] = useState<string>(prompt.current_description || "");
  const [structureFixAccept, setStructureFixAccept] = useState<string>("yes");

  const textareaTheme = useMemo(
    () => ({ panelAlt: theme.panelAlt, text: theme.text, muted: theme.muted }),
    [theme.panelAlt, theme.text, theme.muted],
  );

  useEffect(() => {
    setClarifyIndex(0);
    setClarifyAnswers({});
    setClarifyFocus("options");
    setAction("proceed");
    setFeedback("");
    setFocus("action");
    setStructureFixName(prompt.current_skill_name || "");
    setStructureFixDesc(prompt.current_description || "");
    setStructureFixAccept("yes");
  }, [kind, prompt.current_skill_name, prompt.current_description]);

  useKeyboard((key) => {
    if (!focused) return;

    // Handle Back for clarify questions
    if (kind === "clarify" && (key.name === "b" || key.name === "B")) {
      if (clarifyIndex > 0) {
        setClarifyIndex((v) => Math.max(0, v - 1));
      }
      return;
    }

    // Handle Space on Submit button for clarify questions
    if (kind === "clarify" && key.name === "space" && clarifyFocus === "submit") {
      const q = questions[clarifyIndex];
      if (!q) return;

      const mode = getQuestionMode(q);
      const answer = clarifyAnswers[clarifyIndex] || defaultAnswer();
      const isLast = clarifyIndex >= questions.length - 1;

      // Submit the current answer
      const nextAnswers = { ...clarifyAnswers, [clarifyIndex]: answer };
      setClarifyAnswers(nextAnswers);

      if (isLast) {
        const summary = buildClarifySummary(questions, nextAnswers);
        onSubmit({ answers: { response: summary }, structured_answers: nextAnswers, summary });
      } else {
        setClarifyIndex((v) => Math.min(questions.length - 1, v + 1));
        setClarifyFocus("options");
      }
      return;
    }

    if (key.name === "tab") {
      if (kind === "clarify") {
        const q = questions[clarifyIndex];
        const mode = q ? getQuestionMode(q) : "single";

        // Tab cycle: options → submit → other (if exists) → freeText (if text mode) → back to options
        if (clarifyFocus === "options") {
          setClarifyFocus("submit");
        } else if (clarifyFocus === "submit") {
          if (q?.allows_other) {
            setClarifyFocus("other");
          } else if (mode === "text") {
            setClarifyFocus("freeText");
          } else {
            setClarifyFocus("options");
          }
        } else if (clarifyFocus === "other") {
          if (mode === "text") {
            setClarifyFocus("freeText");
          } else {
            setClarifyFocus("options");
          }
        } else {
          setClarifyFocus("options");
        }
        return;
      }
      setFocus((v) => (v === "action" ? "feedback" : "action"));
      return;
    }
  });

  // If already answered, show the collapsed summary
  if (answered && answer) {
    return (
      <box flexDirection="column" gap={1} padding={1} backgroundColor={theme.panelAlt} border borderColor={theme.border}>
        <text fg={theme.muted}>
          <strong>✓ Answered</strong>
        </text>
        <MarkdownView content={String(answer.summary || "Response submitted")} />
      </box>
    );
  }

  const body = (() => {
    if (kind === "clarify") {
      const q = questions[clarifyIndex];
      if (!q) {
        return (
          <box flexDirection="column" gap={1}>
            <text fg={theme.text}>No questions.</text>
          </box>
        );
      }

      const mode = getQuestionMode(q);
      const answer = clarifyAnswers[clarifyIndex] || defaultAnswer();
      const opts: SelectorOption[] =
        q.options?.map((o) => ({ id: o.id, label: o.label, description: o.description || null })) || [];

      const canBack = clarifyIndex > 0;
      const isLast = clarifyIndex >= questions.length - 1;

      const singleSelector = (
        <>
          <Selector
            mode="single"
            theme={theme}
            options={opts}
            selectedId={answer.selectedOptionIds[0] || null}
            focused={focused && clarifyFocus === "options"}
            onChange={(id) => {
              setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, selectedOptionIds: [id] } }));
            }}
            onSelect={(id) => {
              // Just update the selection, don't auto-advance
              setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, selectedOptionIds: [id] } }));
            }}
          />

          {/* Submit button */}
          <box
            border
            borderColor={clarifyFocus === "submit" ? theme.accent : theme.border}
            backgroundColor={clarifyFocus === "submit" ? theme.panelAlt : theme.panel}
            padding={1}
            onMouseDown={() => {
              const nextAnswers = { ...clarifyAnswers, [clarifyIndex]: answer };
              setClarifyAnswers(nextAnswers);
              if (isLast) {
                const summary = buildClarifySummary(questions, nextAnswers);
                onSubmit({ answers: { response: summary }, structured_answers: nextAnswers, summary });
              } else {
                setClarifyIndex((v) => Math.min(questions.length - 1, v + 1));
                setClarifyFocus("options");
              }
            }}
          >
            <text fg={clarifyFocus === "submit" ? theme.accent : theme.text}>
              {isLast ? "→ Submit" : "→ Next"}
            </text>
          </box>
        </>
      );

      const multiSelector = (
        <>
          <Selector
            mode="multi"
            theme={theme}
            options={opts}
            selectedIds={answer.selectedOptionIds}
            focused={focused && clarifyFocus === "options"}
            onChange={(ids) => {
              setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, selectedOptionIds: ids } }));
            }}
            onConfirm={(ids) => {
              // Just update the selection, don't auto-advance
              setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, selectedOptionIds: ids } }));
            }}
          />

          {/* Submit button */}
          <box
            border
            borderColor={clarifyFocus === "submit" ? theme.accent : theme.border}
            backgroundColor={clarifyFocus === "submit" ? theme.panelAlt : theme.panel}
            padding={1}
            onMouseDown={() => {
              const nextAnswers = { ...clarifyAnswers, [clarifyIndex]: answer };
              setClarifyAnswers(nextAnswers);
              if (isLast) {
                const summary = buildClarifySummary(questions, nextAnswers);
                onSubmit({ answers: { response: summary }, structured_answers: nextAnswers, summary });
              } else {
                setClarifyIndex((v) => Math.min(questions.length - 1, v + 1));
                setClarifyFocus("options");
              }
            }}
          >
            <text fg={clarifyFocus === "submit" ? theme.accent : theme.text}>
              {isLast ? "→ Submit" : "→ Next"}
            </text>
          </box>
        </>
      );

      const textAnswer = (
        <ControlledTextarea
          theme={textareaTheme}
          value={answer.freeText}
          onChange={(v) => {
            setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, freeText: v } }));
          }}
          onSubmit={() => {
            if (isLast) {
              const summary = buildClarifySummary(questions, clarifyAnswers);
              onSubmit({ answers: { response: summary }, structured_answers: clarifyAnswers, summary });
            } else {
              setClarifyIndex((v) => Math.min(questions.length - 1, v + 1));
              setClarifyFocus("options");
            }
          }}
          keyBindings={keyBindings}
          height={5}
          wrapText
          focused={focused && clarifyFocus === "freeText"}
          placeholder="Type your answer..."
        />
      );

      const otherField = q.allows_other ? (
        <input
          value={answer.otherText}
          placeholder="Other..."
          onInput={(v) => {
            setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, otherText: v } }));
          }}
          onChange={(v) => {
            setClarifyAnswers((prev) => ({ ...prev, [clarifyIndex]: { ...answer, otherText: v } }));
          }}
          backgroundColor={theme.panelAlt}
          textColor={theme.text}
          placeholderColor={theme.muted}
          focused={focused && clarifyFocus === "other"}
        />
      ) : null;

      const selectorBlock =
        mode === "single" ? singleSelector : mode === "multi" ? multiSelector : textAnswer;

      return (
        <box flexDirection="column" gap={1}>
          <text fg={theme.accent}>
            {`Question ${clarifyIndex + 1}/${questions.length}`}
          </text>
          <MarkdownView content={q.text} />
          {q.rationale ? <MarkdownView content={q.rationale} /> : null}
          {selectorBlock}
          {otherField}
          <box flexDirection="row" gap={1} justifyContent="space-between" alignItems="center">
            <text fg={theme.muted}>Arrows navigate | Space submit | Tab focus</text>
            <box flexDirection="row" gap={1}>
              {canBack ? (
                <text fg={theme.accent}>[B]ack</text>
              ) : null}
              <text fg={theme.accent}>{isLast ? "[Space] Submit" : "[Space] Next"}</text>
            </box>
          </box>
        </box>
      );
    }

    if (kind === "structure_fix") {
      const issues = prompt.structure_issues || [];
      const warnings = prompt.structure_warnings || [];
      const issueText = issues.length ? `Issues:\n- ${issues.join("\n- ")}` : "";
      const warnText = warnings.length ? `Warnings:\n- ${warnings.join("\n- ")}` : "";

      const acceptOptions: SelectorOption[] = [
        { id: "yes", label: "Accept suggestions", description: "Apply suggested fixes where available" },
        { id: "no", label: "Edit manually", description: "Provide your own values" },
      ];

      return (
        <box flexDirection="column" gap={1}>
          {issueText ? <MarkdownView content={issueText} /> : null}
          {warnText ? <MarkdownView content={warnText} /> : null}

          <text fg={theme.muted}>Accept suggested fixes?</text>
          <Selector
            mode="single"
            theme={theme}
            options={acceptOptions}
            selectedId={structureFixAccept}
            focused={focused && focus === "action"}
            onChange={setStructureFixAccept}
            onSelect={(id) => {
              setStructureFixAccept(id);
              setFocus("feedback");
            }}
          />

          <text fg={theme.muted}>Skill name</text>
          <input
            value={structureFixName}
            onInput={setStructureFixName}
            onChange={setStructureFixName}
            placeholder="skill name"
            backgroundColor={theme.panelAlt}
            textColor={theme.text}
            placeholderColor={theme.muted}
            focused={focused && structureFixAccept === "no" && focus === "feedback"}
          />

          <text fg={theme.muted}>Description</text>
          <ControlledTextarea
            theme={textareaTheme}
            value={structureFixDesc}
            onChange={setStructureFixDesc}
            onSubmit={() => {
              onSubmit({
                skill_name: structureFixName,
                description: structureFixDesc,
                accept_suggestions: structureFixAccept === "yes",
                summary: `Fixed structure: ${structureFixName}`,
              });
            }}
            height={5}
            wrapText
            focused={focused && structureFixAccept === "no" && focus === "feedback"}
            placeholder="description"
          />

          <text fg={theme.muted}>Enter confirm | Tab switch</text>
        </box>
      );
    }

    const content = (() => {
      if (kind === "confirm") {
        const parts: string[] = [];
        if (prompt.summary) parts.push(prompt.summary);
        if (prompt.path) parts.push(`\n\nProposed path:\n${prompt.path}`);
        if (prompt.key_assumptions?.length) parts.push(`\n\nAssumptions:\n- ${prompt.key_assumptions.join("\n- ")}`);
        return parts.join("\n");
      }
      if (kind === "deep_understanding") return prompt.question || "Answer the question.";
      return "";
    })();

    const actionOptions: SelectorOption[] = (() => {
      if (kind === "confirm") {
        return [
          { id: "proceed", label: "Proceed", description: "Looks good, continue" },
          { id: "revise", label: "Revise", description: "Change the plan/assumptions" },
          { id: "cancel", label: "Cancel", description: "Stop this job" },
        ];
      }
      if (kind === "deep_understanding") {
        return [
          { id: "proceed", label: "Proceed", description: "Continue" },
          { id: "cancel", label: "Cancel", description: "Stop this job" },
        ];
      }
      return [{ id: "proceed", label: "Proceed" }];
    })();

    const needsFeedback = action === "revise";
    const feedbackLabel = action === "revise" ? "Revision notes" : "Your answer";

    const doSubmit = (act: string, fb: string) => {
      if (kind === "deep_understanding") {
        onSubmit({ action: act, answer: fb, summary: fb || `Action: ${act}` });
        return;
      }
      onSubmit({ action: act, feedback: fb, summary: fb || `Action: ${act}` });
    };

    return (
      <box flexDirection="column" gap={1}>
        <MarkdownView content={content} />

        <text fg={theme.muted}>Action</text>
        <Selector
          mode="single"
          theme={theme}
          options={actionOptions}
          selectedId={action}
          focused={focused && focus === "action"}
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
              focused={focused && focus === "feedback"}
              placeholder="Type your feedback..."
            />
          </box>
        ) : null}

        <text fg={theme.muted}>Enter confirm | Tab switch</text>
      </box>
    );
  })();

  return (
    <box flexDirection="column" gap={1} padding={1} backgroundColor={theme.panel} border borderColor={theme.border}>
      <text fg={theme.accent}>
        <strong>
          {kind === "clarify" ? "❓ Clarification" :
           kind === "confirm" ? "✓ Confirm" :
           kind === "structure_fix" ? "🔧 Fix Structure" :
           "💭 Deep Understanding"}
        </strong>
      </text>
      {body}
    </box>
  );
}
