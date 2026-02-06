import type { KeyBinding } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { useEffect, useMemo, useState } from "react";
import type { HitlPrompt, StructuredQuestion } from "../types";
import { stripAnsiEscapes } from "../utils/sanitize";
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
  kind:
    | "clarify"
    | "confirm"
    | "structure_fix"
    | "deep_understanding"
    | "tdd_red"
    | "tdd_green"
    | "tdd_refactor";
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
  if (qt === "multiple_select" || qt === "multi_select" || qt === "checkbox")
    return "multi";

  // Default to single select for all other cases with options
  return "single";
}

function defaultAnswer(): ClarifyAnswer {
  return { selectedOptionIds: [], otherText: "", freeText: "" };
}

function buildClarifySummary(
  questions: StructuredQuestion[],
  answers: Record<number, ClarifyAnswer>,
): string {
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
    if (selectedLabels.length)
      lines.push(`- Selected: ${selectedLabels.join(", ")}`);
    if (a.otherText.trim()) lines.push(`- Other: ${a.otherText.trim()}`);
    if (a.freeText.trim()) lines.push(`- Answer: ${a.freeText.trim()}`);
    lines.push("");
  }
  return lines.join("\n").trim();
}

export function HitlMessage({
  theme,
  kind,
  prompt,
  answered,
  answer,
  onSubmit,
  focused,
}: Props) {
  // Sanitize all AI-generated prompt text to prevent terminal escape injection
  const safePrompt = useMemo<HitlPrompt>(
    () => ({
      ...prompt,
      summary: prompt.summary
        ? stripAnsiEscapes(prompt.summary)
        : prompt.summary,
      path: prompt.path ? stripAnsiEscapes(prompt.path) : prompt.path,
      question: prompt.question
        ? stripAnsiEscapes(prompt.question)
        : prompt.question,
      current_skill_name: prompt.current_skill_name
        ? stripAnsiEscapes(prompt.current_skill_name)
        : prompt.current_skill_name,
      current_description: prompt.current_description
        ? stripAnsiEscapes(prompt.current_description)
        : prompt.current_description,
      key_assumptions: prompt.key_assumptions?.map(stripAnsiEscapes),
      structure_issues: prompt.structure_issues?.map(stripAnsiEscapes),
      structure_warnings: prompt.structure_warnings?.map(stripAnsiEscapes),
      // TDD fields
      test_requirements: prompt.test_requirements
        ? stripAnsiEscapes(prompt.test_requirements)
        : prompt.test_requirements,
      acceptance_criteria: prompt.acceptance_criteria?.map(stripAnsiEscapes),
      rationalizations_identified:
        prompt.rationalizations_identified?.map(stripAnsiEscapes),
      failing_test: prompt.failing_test
        ? stripAnsiEscapes(prompt.failing_test)
        : prompt.failing_test,
      test_location: prompt.test_location
        ? stripAnsiEscapes(prompt.test_location)
        : prompt.test_location,
      minimal_implementation_hint: prompt.minimal_implementation_hint
        ? stripAnsiEscapes(prompt.minimal_implementation_hint)
        : prompt.minimal_implementation_hint,
      refactor_opportunities:
        prompt.refactor_opportunities?.map(stripAnsiEscapes),
      code_smells: prompt.code_smells?.map(stripAnsiEscapes),
      coverage_report: prompt.coverage_report
        ? stripAnsiEscapes(prompt.coverage_report)
        : prompt.coverage_report,
      questions: prompt.questions?.map((q) => ({
        ...q,
        text: stripAnsiEscapes(q.text),
        rationale: q.rationale ? stripAnsiEscapes(q.rationale) : q.rationale,
        options: q.options?.map((o) => ({
          ...o,
          label: stripAnsiEscapes(o.label),
          description: o.description
            ? stripAnsiEscapes(o.description)
            : o.description,
        })),
      })),
    }),
    [prompt],
  );

  const keyBindings = useMemo<KeyBinding[]>(
    () => [
      { name: "return", action: "submit" },
      { name: "enter", action: "submit" },
      { name: "return", shift: true, action: "newline" },
      { name: "enter", shift: true, action: "newline" },
    ],
    [],
  );

  const questions = (safePrompt.questions || []) as StructuredQuestion[];

  const [clarifyIndex, setClarifyIndex] = useState(0);
  const [clarifyAnswers, setClarifyAnswers] = useState<
    Record<number, ClarifyAnswer>
  >({});
  const [clarifyFocus, setClarifyFocus] = useState<
    "options" | "submit" | "other" | "freeText"
  >("options");

  const [action, setAction] = useState<string>("proceed");
  const [feedback, setFeedback] = useState<string>("");
  const [focus, setFocus] = useState<"action" | "feedback">("action");

  // Deep understanding enriched fields
  const [duAnswer, setDuAnswer] = useState<string>("");
  const [duProblem, setDuProblem] = useState<string>("");
  const [duGoals, setDuGoals] = useState<string>("");
  const [duFocus, setDuFocus] = useState<
    "answer" | "problem" | "goals" | "action"
  >("answer");

  const [structureFixName, setStructureFixName] = useState<string>(
    safePrompt.current_skill_name || "",
  );
  const [structureFixDesc, setStructureFixDesc] = useState<string>(
    safePrompt.current_description || "",
  );
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
    setDuAnswer("");
    setDuProblem("");
    setDuGoals("");
    setDuFocus("answer");
    setStructureFixName(safePrompt.current_skill_name || "");
    setStructureFixDesc(safePrompt.current_description || "");
    setStructureFixAccept("yes");
  }, [kind, safePrompt.current_skill_name, safePrompt.current_description]);

  useKeyboard((key) => {
    if (!focused) return;

    // Handle Back for clarify questions
    if (kind === "clarify" && (key.name === "b" || key.name === "B")) {
      if (clarifyIndex > 0) {
        setClarifyIndex((v) => Math.max(0, v - 1));
        setClarifyFocus("options");
      }
      return;
    }

    // Handle Enter on Submit button for clarify questions
    if (
      kind === "clarify" &&
      (key.name === "return" || key.name === "enter") &&
      clarifyFocus === "submit"
    ) {
      const q = questions[clarifyIndex];
      if (!q) return;

      const answer = clarifyAnswers[clarifyIndex] || defaultAnswer();
      const isLast = clarifyIndex >= questions.length - 1;

      // Submit the current answer
      const nextAnswers = { ...clarifyAnswers, [clarifyIndex]: answer };
      setClarifyAnswers(nextAnswers);

      if (isLast) {
        const summary = buildClarifySummary(questions, nextAnswers);
        onSubmit({
          answers: { response: summary },
          structured_answers: nextAnswers,
          summary,
        });
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
      if (kind === "deep_understanding") {
        setDuFocus((v) => {
          if (v === "answer") return "problem";
          if (v === "problem") return "goals";
          if (v === "goals") return "action";
          return "answer";
        });
        return;
      }
      setFocus((v) => (v === "action" ? "feedback" : "action"));
      return;
    }
  });

  // If already answered, show the collapsed summary
  if (answered && answer) {
    return (
      <box flexDirection="column" gap={0} paddingLeft={1} paddingBottom={1}>
        <text fg={theme.muted}>→ Answered</text>
        <MarkdownView
          content={String(answer.summary || "Response submitted")}
        />
      </box>
    );
  }

  const body = (() => {
    if (kind === "clarify") {
      const q = questions[clarifyIndex];
      if (!q) {
        return (
          <box flexDirection="column" gap={0} paddingLeft={1}>
            <text fg={theme.text}>No questions.</text>
          </box>
        );
      }

      const mode = getQuestionMode(q);
      const answer = clarifyAnswers[clarifyIndex] || defaultAnswer();

      // Convert to OpenTUI select format
      const selectOptions =
        q.options?.map((o, idx) => ({
          name: `${idx + 1}. ${o.label}`,
          description: o.description || "",
          value: o.id,
        })) || [];

      const canBack = clarifyIndex > 0;
      const isLast = clarifyIndex >= questions.length - 1;

      // Handle selection and advance
      const handleSelect = (idx: number, opt: { value?: unknown } | null) => {
        const id = String(opt?.value || "");
        if (!id) return;

        const newAnswer = {
          ...answer,
          selectedOptionIds:
            mode === "multi"
              ? answer.selectedOptionIds.includes(id)
                ? answer.selectedOptionIds.filter((x) => x !== id)
                : [...answer.selectedOptionIds, id]
              : [id],
        };

        const nextAnswers = { ...clarifyAnswers, [clarifyIndex]: newAnswer };
        setClarifyAnswers(nextAnswers);

        // For single select, advance on selection
        if (mode === "single") {
          if (isLast) {
            const summary = buildClarifySummary(questions, nextAnswers);
            onSubmit({
              answers: { response: summary },
              structured_answers: nextAnswers,
              summary,
            });
          } else {
            setClarifyIndex((v) => Math.min(questions.length - 1, v + 1));
          }
        }
      };

      const selectedIndex = selectOptions.findIndex(
        (o) => o.value === answer.selectedOptionIds[0],
      );

      // Render selected options summary for clarity
      const selectedSummary =
        mode === "multi" && answer.selectedOptionIds.length > 0
          ? `Selected: ${answer.selectedOptionIds
              .map((id) => q.options?.find((o) => o.id === id)?.label || id)
              .join(", ")}`
          : null;

      return (
        <box flexDirection="column" gap={0} paddingLeft={1} paddingBottom={1}>
          {/* Header */}
          <text fg={theme.muted}>
            [{clarifyIndex + 1}/{questions.length}]
          </text>

          {/* Question */}
          <box paddingTop={1}>
            <text fg={theme.text}>{q.text}</text>
          </box>

          {q.rationale ? <text fg={theme.muted}>{q.rationale}</text> : null}

          {/* Options - use native select */}
          <box paddingTop={1}>
            <select
              options={selectOptions}
              selectedIndex={selectedIndex >= 0 ? selectedIndex : 0}
              height={Math.min(10, selectOptions.length + 1)}
              focused={focused && clarifyFocus === "options"}
              onSelect={handleSelect}
              onChange={(idx, opt) => {
                // For multi-select, toggle on change
                if (mode === "multi") {
                  const id = String(opt?.value || "");
                  if (id) {
                    const newIds = answer.selectedOptionIds.includes(id)
                      ? answer.selectedOptionIds.filter((x) => x !== id)
                      : [...answer.selectedOptionIds, id];
                    setClarifyAnswers((prev) => ({
                      ...prev,
                      [clarifyIndex]: { ...answer, selectedOptionIds: newIds },
                    }));
                  }
                }
              }}
            />
          </box>

          {q.allows_other ? (
            <box paddingTop={1}>
              <input
                value={answer.otherText}
                placeholder="Other..."
                onInput={(v) => {
                  setClarifyAnswers((prev) => ({
                    ...prev,
                    [clarifyIndex]: { ...answer, otherText: v },
                  }));
                }}
                onChange={(v) => {
                  setClarifyAnswers((prev) => ({
                    ...prev,
                    [clarifyIndex]: { ...answer, otherText: v },
                  }));
                }}
                backgroundColor={theme.panelAlt}
                textColor={theme.text}
                placeholderColor={theme.muted}
                focused={focused && clarifyFocus === "other"}
              />
            </box>
          ) : null}

          {/* Show selected options for multi-select */}
          {selectedSummary ? (
            <box paddingTop={1}>
              <text fg={theme.accent}>{selectedSummary}</text>
            </box>
          ) : null}

          {/* Control row: visual indicators of navigation options */}
          <box flexDirection="row" gap={1} paddingTop={1}>
            {canBack ? (
              <text fg={clarifyFocus === "submit" ? theme.accent : theme.muted}>
                {clarifyFocus === "submit" ? "[← Back (b)]" : "(b) back"}
              </text>
            ) : null}
            {!isLast ? (
              <text fg={clarifyFocus === "submit" ? theme.accent : theme.muted}>
                {clarifyFocus === "submit" ? "[Next → (tab)]" : "(tab) next"}
              </text>
            ) : (
              <text fg={clarifyFocus === "submit" ? theme.accent : theme.muted}>
                {clarifyFocus === "submit"
                  ? "[✓ Submit (enter)]"
                  : "(enter) submit"}
              </text>
            )}
          </box>

          {/* Context-aware help line */}
          <box flexDirection="row" gap={1} paddingTop={1}>
            {clarifyFocus === "options" && (
              <>
                <text fg={theme.muted}>↑↓ navigate</text>
                <text fg={theme.muted}>enter select</text>
                {mode === "multi" && <text fg={theme.muted}>space toggle</text>}
              </>
            )}
            {clarifyFocus === "submit" && (
              <>
                <text fg={theme.muted}>enter confirm</text>
                <text fg={theme.muted}>tab focus</text>
              </>
            )}
            {clarifyFocus === "other" && (
              <>
                <text fg={theme.muted}>type input</text>
                <text fg={theme.muted}>tab next</text>
              </>
            )}
          </box>
        </box>
      );
    }

    if (kind === "structure_fix") {
      const issues = safePrompt.structure_issues || [];
      const warnings = safePrompt.structure_warnings || [];
      const issueText = issues.length
        ? `Issues:\n- ${issues.join("\n- ")}`
        : "";
      const warnText = warnings.length
        ? `Warnings:\n- ${warnings.join("\n- ")}`
        : "";

      const acceptOptions: SelectorOption[] = [
        {
          id: "yes",
          label: "Accept suggestions",
          description: "Apply suggested fixes where available",
        },
        {
          id: "no",
          label: "Edit manually",
          description: "Provide your own values",
        },
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
            focused={
              focused && structureFixAccept === "no" && focus === "feedback"
            }
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
            focused={
              focused && structureFixAccept === "no" && focus === "feedback"
            }
            placeholder="description"
          />

          <text fg={theme.muted}>Enter confirm | Tab switch</text>
        </box>
      );
    }

    // TDD Red: Write failing tests
    if (kind === "tdd_red") {
      const requirements =
        safePrompt.test_requirements || "Write failing tests.";
      const acceptance = safePrompt.acceptance_criteria || [];
      const checklist = safePrompt.checklist_items || [];
      const rationalizations = safePrompt.rationalizations_identified || [];

      const tddRedOptions: SelectorOption[] = [
        {
          id: "proceed",
          label: "Tests fail as expected",
          description: "Ready to continue",
        },
        {
          id: "revise",
          label: "Revise requirements",
          description: "Change what needs testing",
        },
        { id: "cancel", label: "Cancel", description: "Stop this job" },
      ];

      return (
        <box flexDirection="column" gap={1}>
          <text fg="#ef4444">🔴 TDD Red Phase: Write Failing Tests</text>
          <MarkdownView content={requirements} />

          {acceptance.length > 0 ? (
            <box flexDirection="column" gap={0}>
              <text fg={theme.muted}>Acceptance criteria:</text>
              {acceptance.map((c, i) => (
                <text key={`ac-${i}`} fg={theme.text}>
                  {" "}
                  {i + 1}. {String(c)}
                </text>
              ))}
            </box>
          ) : null}

          {checklist.length > 0 ? (
            <box flexDirection="column" gap={0}>
              <text fg={theme.muted}>Checklist:</text>
              {checklist.map((item, i) => {
                const text =
                  typeof item === "string"
                    ? item
                    : (item as { text: string }).text;
                const done =
                  typeof item === "object" && item !== null
                    ? (item as { done?: boolean }).done
                    : false;
                return (
                  <text key={`cl-${i}`} fg={theme.text}>
                    {" "}
                    {done ? "☑" : "☐"} {text}
                  </text>
                );
              })}
            </box>
          ) : null}

          {rationalizations.length > 0 ? (
            <box flexDirection="column" gap={0}>
              <text fg="#eab308">Rationalizations detected:</text>
              {rationalizations.map((r, i) => (
                <text key={`rat-${i}`} fg="#eab308">
                  {" "}
                  ⚠️ {String(r)}
                </text>
              ))}
            </box>
          ) : null}

          <text fg={theme.muted}>Action</text>
          <Selector
            mode="single"
            theme={theme}
            options={tddRedOptions}
            selectedId={action}
            focused={focused && focus === "action"}
            onChange={setAction}
            onSelect={(id) => {
              setAction(id);
              if (id === "proceed" || id === "cancel") {
                onSubmit({ action: id, summary: `Action: ${id}` });
                return;
              }
              setFocus("feedback");
            }}
          />

          {action === "revise" ? (
            <box flexDirection="column" gap={1}>
              <text fg={theme.muted}>What should change?</text>
              <ControlledTextarea
                theme={textareaTheme}
                value={feedback}
                onChange={setFeedback}
                onSubmit={() =>
                  onSubmit({
                    action,
                    feedback,
                    summary: feedback || `Action: ${action}`,
                  })
                }
                wrapText
                height={5}
                focused={focused && focus === "feedback"}
                placeholder="Type your feedback..."
              />
            </box>
          ) : null}

          <text fg={theme.muted}>Enter confirm | Tab switch</text>
        </box>
      );
    }

    // TDD Green: Make tests pass
    if (kind === "tdd_green") {
      const failingTest = safePrompt.failing_test || "";
      const testLocation = safePrompt.test_location || "";
      const hint = safePrompt.minimal_implementation_hint || "";

      const parts: string[] = [];
      if (failingTest) parts.push(`**Failing Test:** ${failingTest}`);
      if (testLocation) parts.push(`**Location:** ${testLocation}`);
      if (hint) parts.push(`**Hint:** ${hint}`);
      const greenContent =
        parts.join("\n\n") ||
        "Make the failing tests pass with minimal implementation.";

      const tddGreenOptions: SelectorOption[] = [
        {
          id: "proceed",
          label: "All tests pass",
          description: "Ready to continue",
        },
        {
          id: "revise",
          label: "Need adjustment",
          description: "Change approach",
        },
        { id: "cancel", label: "Cancel", description: "Stop this job" },
      ];

      return (
        <box flexDirection="column" gap={1}>
          <text fg="#22c55e">🟢 TDD Green Phase: Make Tests Pass</text>
          <MarkdownView content={greenContent} />

          <text fg={theme.muted}>Action</text>
          <Selector
            mode="single"
            theme={theme}
            options={tddGreenOptions}
            selectedId={action}
            focused={focused && focus === "action"}
            onChange={setAction}
            onSelect={(id) => {
              setAction(id);
              if (id === "proceed" || id === "cancel") {
                onSubmit({ action: id, summary: `Action: ${id}` });
                return;
              }
              setFocus("feedback");
            }}
          />

          {action === "revise" ? (
            <box flexDirection="column" gap={1}>
              <text fg={theme.muted}>What needs adjustment?</text>
              <ControlledTextarea
                theme={textareaTheme}
                value={feedback}
                onChange={setFeedback}
                onSubmit={() =>
                  onSubmit({
                    action,
                    feedback,
                    summary: feedback || `Action: ${action}`,
                  })
                }
                wrapText
                height={5}
                focused={focused && focus === "feedback"}
                placeholder="Type your feedback..."
              />
            </box>
          ) : null}

          <text fg={theme.muted}>Enter confirm | Tab switch</text>
        </box>
      );
    }

    // TDD Refactor: Clean up code
    if (kind === "tdd_refactor") {
      const opportunities = safePrompt.refactor_opportunities || [];
      const smells = safePrompt.code_smells || [];
      const coverage = safePrompt.coverage_report || "";

      const refactorParts: string[] = [];
      if (coverage) refactorParts.push(`**Coverage:** ${coverage}`);
      if (opportunities.length) {
        refactorParts.push("**Refactor opportunities:**");
        refactorParts.push(...opportunities.map((o) => `  • ${o}`));
      }
      if (smells.length) {
        refactorParts.push("**Code smells:**");
        refactorParts.push(...smells.map((s) => `  ⚠️  ${s}`));
      }
      const refactorContent = refactorParts.join("\n") || "Ready to refactor.";

      const tddRefactorOptions: SelectorOption[] = [
        {
          id: "proceed",
          label: "Code refactored",
          description: "Clean and tested",
        },
        { id: "skip", label: "Skip refactoring", description: "Move on" },
        {
          id: "revise",
          label: "Need more work",
          description: "Still refactoring",
        },
        { id: "cancel", label: "Cancel", description: "Stop this job" },
      ];

      return (
        <box flexDirection="column" gap={1}>
          <text fg="#3b82f6">🔵 TDD Refactor Phase: Clean Up Code</text>
          <MarkdownView content={refactorContent} />

          <text fg={theme.muted}>Action</text>
          <Selector
            mode="single"
            theme={theme}
            options={tddRefactorOptions}
            selectedId={action}
            focused={focused && focus === "action"}
            onChange={setAction}
            onSelect={(id) => {
              setAction(id);
              const mappedAction = id === "skip" ? "proceed" : id;
              if (mappedAction === "proceed" || mappedAction === "cancel") {
                onSubmit({ action: mappedAction, summary: `Action: ${id}` });
                return;
              }
              setFocus("feedback");
            }}
          />

          {action === "revise" ? (
            <box flexDirection="column" gap={1}>
              <text fg={theme.muted}>What still needs work?</text>
              <ControlledTextarea
                theme={textareaTheme}
                value={feedback}
                onChange={setFeedback}
                onSubmit={() =>
                  onSubmit({
                    action,
                    feedback,
                    summary: feedback || `Action: ${action}`,
                  })
                }
                wrapText
                height={5}
                focused={focused && focus === "feedback"}
                placeholder="Type your feedback..."
              />
            </box>
          ) : null}

          <text fg={theme.muted}>Enter confirm | Tab switch</text>
        </box>
      );
    }

    // Deep understanding: enriched with answer + problem + goals (matches CLI)
    if (kind === "deep_understanding") {
      const duQuestion = safePrompt.question || "Answer the question.";
      const duResearch = safePrompt.research_performed || [];
      const duCurrent = safePrompt.current_understanding || "";
      const duReadiness = safePrompt.readiness_score;

      const duActionOptions: SelectorOption[] = [
        {
          id: "proceed",
          label: "Answer & Continue",
          description: "Submit your answer",
        },
        {
          id: "skip",
          label: "Skip Question",
          description: "Skip this question",
        },
        { id: "cancel", label: "Cancel", description: "Stop this job" },
      ];

      const handleDuSubmit = () => {
        const goalsArray = duGoals
          .split(",")
          .map((g) => g.trim())
          .filter(Boolean);
        onSubmit({
          action: "proceed",
          answer: duAnswer,
          problem: duProblem,
          goals: goalsArray,
          summary: duAnswer || "Answered",
        });
      };

      return (
        <box flexDirection="column" gap={1}>
          {duCurrent ? (
            <box flexDirection="column" gap={0}>
              <text fg={theme.muted}>Current understanding:</text>
              <MarkdownView content={duCurrent} />
            </box>
          ) : null}

          {duResearch.length > 0 ? (
            <box flexDirection="column" gap={0}>
              <text fg={theme.muted}>Research performed:</text>
              {duResearch.map((r, i) => (
                <text key={`res-${i}`} fg={theme.text}>
                  {" "}
                  • {String(r)}
                </text>
              ))}
            </box>
          ) : null}

          {duReadiness != null ? (
            <text fg={theme.muted}>
              Readiness: {Number(duReadiness).toFixed(2)} (target 0.80)
            </text>
          ) : null}

          <MarkdownView content={duQuestion} />

          <text fg={theme.muted}>Your answer</text>
          <ControlledTextarea
            theme={textareaTheme}
            value={duAnswer}
            onChange={setDuAnswer}
            onSubmit={handleDuSubmit}
            wrapText
            height={4}
            focused={focused && duFocus === "answer"}
            placeholder="Type your answer..."
          />

          <text fg={theme.muted}>What problem are you solving? (optional)</text>
          <ControlledTextarea
            theme={textareaTheme}
            value={duProblem}
            onChange={setDuProblem}
            onSubmit={handleDuSubmit}
            wrapText
            height={3}
            focused={focused && duFocus === "problem"}
            placeholder="Describe the problem..."
          />

          <text fg={theme.muted}>Goals (comma-separated, optional)</text>
          <ControlledTextarea
            theme={textareaTheme}
            value={duGoals}
            onChange={setDuGoals}
            onSubmit={handleDuSubmit}
            wrapText
            height={2}
            focused={focused && duFocus === "goals"}
            placeholder="goal1, goal2, ..."
          />

          <Selector
            mode="single"
            theme={theme}
            options={duActionOptions}
            selectedId="proceed"
            focused={focused && duFocus === "action"}
            onChange={() => {}}
            onSelect={(id) => {
              if (id === "cancel") {
                onSubmit({ action: "cancel", summary: "Cancelled" });
              } else if (id === "skip") {
                onSubmit({ action: "proceed", summary: "Skipped" });
              } else {
                handleDuSubmit();
              }
            }}
          />

          <text fg={theme.muted}>Tab cycle fields | Enter submit</text>
        </box>
      );
    }

    // Confirm (generic fallback for confirm and any unknown types)
    const content = (() => {
      if (kind === "confirm") {
        const parts: string[] = [];
        if (safePrompt.summary) parts.push(safePrompt.summary);
        if (safePrompt.path)
          parts.push(`\n\nProposed path:\n${safePrompt.path}`);
        if (safePrompt.key_assumptions?.length)
          parts.push(
            `\n\nAssumptions:\n- ${safePrompt.key_assumptions.join("\n- ")}`,
          );
        return parts.join("\n");
      }
      return "";
    })();

    const actionOptions: SelectorOption[] = (() => {
      if (kind === "confirm") {
        return [
          {
            id: "proceed",
            label: "Proceed",
            description: "Looks good, continue",
          },
          {
            id: "revise",
            label: "Revise",
            description: "Change the plan/assumptions",
          },
          { id: "cancel", label: "Cancel", description: "Stop this job" },
        ];
      }
      return [{ id: "proceed", label: "Proceed" }];
    })();

    const needsFeedback = action === "revise";

    const doSubmit = (act: string, fb: string) => {
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
            <text fg={theme.muted}>Revision notes</text>
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
    <box flexDirection="column" gap={1} paddingLeft={1} paddingBottom={1}>
      <text fg={theme.muted}>
        {kind === "clarify"
          ? "? Clarification"
          : kind === "confirm"
            ? "> Confirm"
            : kind === "structure_fix"
              ? "> Fix Structure"
              : kind === "tdd_red"
                ? "🔴 TDD Red"
                : kind === "tdd_green"
                  ? "🟢 TDD Green"
                  : kind === "tdd_refactor"
                    ? "🔵 TDD Refactor"
                    : "> Question"}
      </text>
      {body}
    </box>
  );
}
