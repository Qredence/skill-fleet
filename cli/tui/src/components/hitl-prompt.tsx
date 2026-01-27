/**
 * HITL Prompt Component
 *
 * Renders Human-in-the-Loop prompts for different interaction types:
 * - clarify: Multiple choice or free-text questions
 * - confirm: Confirm understanding summary with proceed/revise/cancel
 * - preview: Preview generated content with proceed/revise/cancel
 * - validate: Review validation report with proceed/revise/cancel
 * - deep_understanding: WHY questions about user's problem/goals
 * - tdd_red/green/refactor: TDD workflow phases
 */

import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";
import SelectInput from "ink-select-input";

/** Structured question option from API */
export interface QuestionOption {
  id: string;
  label: string;
  description?: string;
}

/** Question type from API */
export type QuestionType = "boolean" | "single" | "multi" | "text";

/** Structured question from API */
export interface StructuredQuestion {
  text: string;
  question_type?: QuestionType;
  options?: QuestionOption[];
  allows_multiple?: boolean;
  allows_other?: boolean;
  rationale?: string;
}

/** HITL prompt data from API */
export interface HITLPromptData {
  status: string;
  type: string | null;
  current_phase?: string;
  progress_message?: string;

  // Clarification
  questions?: StructuredQuestion[];
  rationale?: string;

  // Confirmation
  summary?: string;
  path?: string;
  key_assumptions?: string[];

  // Preview
  content?: string;
  highlights?: string[];

  // Validation
  report?: string;
  passed?: boolean;

  // Deep understanding
  question?: string;
  current_understanding?: string;
  readiness_score?: number;

  // TDD phases
  test_requirements?: string;
  acceptance_criteria?: string[];
  failing_test?: string;
  refactor_opportunities?: string[];

  // Results
  error?: string;
  draft_path?: string;
  validation_score?: number;
}

export interface HITLPromptProps {
  prompt: HITLPromptData;
  onSubmit: (response: Record<string, any>) => void;
  onCancel?: () => void;
}

interface ActionItem {
  label: string;
  value: string;
}

/**
 * Main HITL Prompt Component
 */
export const HITLPrompt: React.FC<HITLPromptProps> = ({
  prompt,
  onSubmit,
  onCancel,
}) => {
  const [textInput, setTextInput] = useState("");
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(
    new Set(),
  );
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});

  // Handle escape key for cancel
  useInput((input, key) => {
    if (key.escape && onCancel) {
      onCancel();
    }
  });

  // Render based on interaction type
  switch (prompt.type) {
    case "clarify":
      return (
        <ClarifyPrompt
          questions={prompt.questions || []}
          rationale={prompt.rationale}
          currentIndex={currentQuestionIndex}
          answers={answers}
          textInput={textInput}
          selectedOptions={selectedOptions}
          onTextChange={setTextInput}
          onOptionToggle={(id) => {
            const newSet = new Set(selectedOptions);
            if (newSet.has(id)) {
              newSet.delete(id);
            } else {
              newSet.add(id);
            }
            setSelectedOptions(newSet);
          }}
          onNextQuestion={() => {
            const questions = prompt.questions || [];
            const currentQ = questions[currentQuestionIndex];

            // Save current answer
            const newAnswers = { ...answers };
            if (currentQ?.options && selectedOptions.size > 0) {
              newAnswers[`q${currentQuestionIndex}`] =
                Array.from(selectedOptions);
            } else if (textInput.trim()) {
              newAnswers[`q${currentQuestionIndex}`] = textInput.trim();
            }
            setAnswers(newAnswers);

            // Reset for next question
            setTextInput("");
            setSelectedOptions(new Set());

            if (currentQuestionIndex < questions.length - 1) {
              setCurrentQuestionIndex(currentQuestionIndex + 1);
            } else {
              // All questions answered - submit
              onSubmit({ answers: { response: newAnswers } });
            }
          }}
        />
      );

    case "confirm":
      return (
        <ConfirmPrompt
          summary={prompt.summary || ""}
          path={prompt.path}
          assumptions={prompt.key_assumptions}
          onAction={(action) => onSubmit({ action })}
        />
      );

    case "preview":
      return (
        <PreviewPrompt
          content={prompt.content || ""}
          highlights={prompt.highlights}
          onAction={(action, feedback) => onSubmit({ action, feedback })}
        />
      );

    case "validate":
      return (
        <ValidationPrompt
          report={prompt.report || ""}
          passed={prompt.passed}
          score={prompt.validation_score}
          onAction={(action, feedback) => onSubmit({ action, feedback })}
        />
      );

    case "deep_understanding":
      return (
        <DeepUnderstandingPrompt
          question={prompt.question || ""}
          currentUnderstanding={prompt.current_understanding}
          readinessScore={prompt.readiness_score}
          textInput={textInput}
          onTextChange={setTextInput}
          onSubmit={(answer, problem, goals) =>
            onSubmit({ action: "proceed", answer, problem, goals })
          }
          onCancel={() => onSubmit({ action: "cancel" })}
        />
      );

    case "tdd_red":
    case "tdd_green":
    case "tdd_refactor":
      return (
        <TDDPrompt
          phase={prompt.type}
          testRequirements={prompt.test_requirements}
          acceptanceCriteria={prompt.acceptance_criteria}
          failingTest={prompt.failing_test}
          refactorOpportunities={prompt.refactor_opportunities}
          onAction={(action, feedback) => onSubmit({ action, feedback })}
        />
      );

    default:
      // Unknown type - show generic prompt
      return (
        <Box flexDirection="column" paddingX={1}>
          <Text color="yellow">⚠️ Unknown HITL type: {prompt.type}</Text>
          <Text color="gray">Status: {prompt.status}</Text>
          {prompt.progress_message && (
            <Text color="cyan">{prompt.progress_message}</Text>
          )}
        </Box>
      );
  }
};

/**
 * Clarification questions prompt
 */
interface ClarifyPromptProps {
  questions: StructuredQuestion[];
  rationale?: string;
  currentIndex: number;
  answers: Record<string, string | string[]>;
  textInput: string;
  selectedOptions: Set<string>;
  onTextChange: (text: string) => void;
  onOptionToggle: (id: string) => void;
  onNextQuestion: () => void;
}

const ClarifyPrompt: React.FC<ClarifyPromptProps> = ({
  questions,
  rationale,
  currentIndex,
  textInput,
  selectedOptions,
  onTextChange,
  onOptionToggle,
  onNextQuestion,
}) => {
  const question = questions[currentIndex];

  if (!question) {
    return (
      <Box>
        <Text color="yellow">No questions to answer</Text>
      </Box>
    );
  }

  const hasOptions = question.options && question.options.length > 0;
  const questionType = question.question_type || "text";
  const allowsOther = question.allows_other !== false; // default true

  // Build options list with optional "Other" choice
  const optionsWithOther = hasOptions
    ? [
        ...question.options!.map((opt) => ({
          label: selectedOptions.has(opt.id)
            ? `✓ ${opt.label}`
            : `  ${opt.label}`,
          value: opt.id,
        })),
        ...(allowsOther
          ? [{ label: "  ✏️ Other: type your own", value: "__other__" }]
          : []),
      ]
    : [];

  // Get hint text based on question type
  const getHintText = () => {
    switch (questionType) {
      case "boolean":
        return "(Yes/No)";
      case "single":
        return "(Select one)";
      case "multi":
        return "(Select multiple with Enter, then Tab to continue)";
      default:
        return "(Type your answer)";
    }
  };

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="cyan"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text color="cyan" bold>
          🤔 Question {currentIndex + 1}/{questions.length}
        </Text>
      </Box>

      {rationale && (
        <Box marginBottom={1}>
          <Text color="gray" italic>
            {rationale}
          </Text>
        </Box>
      )}

      <Box marginBottom={1}>
        <Text color="white" wrap="wrap">
          {question.text}
        </Text>
      </Box>

      {hasOptions ? (
        <Box flexDirection="column">
          <Text color="gray" dimColor>
            {getHintText()}
          </Text>
          <SelectInput
            items={optionsWithOther}
            onSelect={(item) => {
              if (item.value === "__other__") {
                // Switch to text input mode - clear options and use text
                onTextChange("");
                // For now, just proceed with empty to trigger text mode
                // In a full implementation, we'd track a "showOtherInput" state
              } else if (question.allows_multiple) {
                onOptionToggle(item.value);
              } else {
                // Single select - immediately proceed
                onNextQuestion();
              }
            }}
          />
          {question.allows_multiple && selectedOptions.size > 0 && (
            <Box marginTop={1}>
              <Text color="green">
                Press Tab to continue with {selectedOptions.size} selected
              </Text>
            </Box>
          )}
        </Box>
      ) : (
        <Box flexDirection="column">
          <Box flexDirection="row" gap={1}>
            <Text color="blue">&gt;</Text>
            <TextInput
              value={textInput}
              onChange={onTextChange}
              onSubmit={onNextQuestion}
              placeholder="Type your answer..."
            />
          </Box>
          <Text color="gray" dimColor>
            Press Enter to continue
          </Text>
        </Box>
      )}
    </Box>
  );
};

/**
 * Confirmation prompt (summary review)
 */
interface ConfirmPromptProps {
  summary: string;
  path?: string;
  assumptions?: string[];
  onAction: (action: "proceed" | "revise" | "cancel") => void;
}

const ConfirmPrompt: React.FC<ConfirmPromptProps> = ({
  summary,
  path,
  assumptions,
  onAction,
}) => {
  const items: ActionItem[] = [
    { label: "✅ Proceed - This looks correct", value: "proceed" },
    { label: "✏️  Revise - I want to make changes", value: "revise" },
    { label: "❌ Cancel - Start over", value: "cancel" },
  ];

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="green"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text color="green" bold>
          📋 Please Confirm Understanding
        </Text>
      </Box>

      <Box marginBottom={1} flexDirection="column">
        <Text color="white" wrap="wrap">
          {summary}
        </Text>
      </Box>

      {path && (
        <Box marginBottom={1}>
          <Text color="cyan">
            📁 Taxonomy Path: <Text bold>{path}</Text>
          </Text>
        </Box>
      )}

      {assumptions && assumptions.length > 0 && (
        <Box flexDirection="column" marginBottom={1}>
          <Text color="yellow" bold>
            Key Assumptions:
          </Text>
          {assumptions.map((a, i) => (
            <Text key={i} color="yellow">
              • {a}
            </Text>
          ))}
        </Box>
      )}

      <Box marginTop={1}>
        <SelectInput
          items={items}
          onSelect={(item) =>
            onAction(item.value as "proceed" | "revise" | "cancel")
          }
        />
      </Box>
    </Box>
  );
};

/**
 * Preview prompt (content review)
 */
interface PreviewPromptProps {
  content: string;
  highlights?: string[];
  onAction: (
    action: "proceed" | "revise" | "cancel",
    feedback?: string,
  ) => void;
}

const PreviewPrompt: React.FC<PreviewPromptProps> = ({
  content,
  highlights,
  onAction,
}) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  const items: ActionItem[] = [
    { label: "✅ Approve - Generate the skill", value: "proceed" },
    { label: "✏️  Revise - Provide feedback", value: "revise" },
    { label: "❌ Cancel - Discard and start over", value: "cancel" },
  ];

  if (showFeedback) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="yellow"
        paddingX={2}
        paddingY={1}
      >
        <Text color="yellow" bold>
          ✏️ Provide Feedback
        </Text>
        <Text color="gray" dimColor>
          What would you like to change?
        </Text>
        <Box marginTop={1} flexDirection="row" gap={1}>
          <Text color="blue">&gt;</Text>
          <TextInput
            value={feedback}
            onChange={setFeedback}
            onSubmit={() => onAction("revise", feedback)}
            placeholder="Describe your changes..."
          />
        </Box>
      </Box>
    );
  }

  // Truncate content for display
  const maxLines = 15;
  const lines = content.split("\n");
  const truncated = lines.length > maxLines;
  const displayContent = truncated
    ? lines.slice(0, maxLines).join("\n") + "\n... (truncated)"
    : content;

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="blue"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text color="blue" bold>
          👁️ Preview Generated Content
        </Text>
      </Box>

      {highlights && highlights.length > 0 && (
        <Box flexDirection="column" marginBottom={1}>
          <Text color="cyan" bold>
            Highlights:
          </Text>
          {highlights.map((h, i) => (
            <Text key={i} color="cyan">
              ✨ {h}
            </Text>
          ))}
        </Box>
      )}

      <Box
        borderStyle="single"
        borderColor="gray"
        paddingX={1}
        marginBottom={1}
        flexDirection="column"
      >
        <Text color="white" wrap="wrap">
          {displayContent}
        </Text>
      </Box>

      <SelectInput
        items={items}
        onSelect={(item) => {
          if (item.value === "revise") {
            setShowFeedback(true);
          } else {
            onAction(item.value as "proceed" | "cancel");
          }
        }}
      />
    </Box>
  );
};

/**
 * Validation report prompt
 */
interface ValidationPromptProps {
  report: string;
  passed?: boolean;
  score?: number;
  onAction: (
    action: "proceed" | "revise" | "cancel",
    feedback?: string,
  ) => void;
}

const ValidationPrompt: React.FC<ValidationPromptProps> = ({
  report,
  passed,
  score,
  onAction,
}) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  const statusColor = passed ? "green" : "red";
  const statusIcon = passed ? "✅" : "❌";

  const items: ActionItem[] = passed
    ? [
        { label: "✅ Save - Promote to taxonomy", value: "proceed" },
        { label: "✏️  Revise - Make improvements", value: "revise" },
        { label: "❌ Cancel - Discard", value: "cancel" },
      ]
    : [
        { label: "✏️  Revise - Fix issues", value: "revise" },
        { label: "🔄 Retry - Run validation again", value: "proceed" },
        { label: "❌ Cancel - Discard", value: "cancel" },
      ];

  if (showFeedback) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="yellow"
        paddingX={2}
        paddingY={1}
      >
        <Text color="yellow" bold>
          ✏️ Provide Revision Instructions
        </Text>
        <Box marginTop={1} flexDirection="row" gap={1}>
          <Text color="blue">&gt;</Text>
          <TextInput
            value={feedback}
            onChange={setFeedback}
            onSubmit={() => onAction("revise", feedback)}
            placeholder="What should be fixed..."
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={statusColor}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1} flexDirection="row" gap={2}>
        <Text color={statusColor} bold>
          {statusIcon} Validation {passed ? "Passed" : "Failed"}
        </Text>
        {score !== undefined && (
          <Text color="gray">Score: {(score * 100).toFixed(1)}%</Text>
        )}
      </Box>

      <Box
        borderStyle="single"
        borderColor="gray"
        paddingX={1}
        marginBottom={1}
        flexDirection="column"
      >
        <Text color="white" wrap="wrap">
          {report}
        </Text>
      </Box>

      <SelectInput
        items={items}
        onSelect={(item) => {
          if (item.value === "revise") {
            setShowFeedback(true);
          } else {
            onAction(item.value as "proceed" | "cancel");
          }
        }}
      />
    </Box>
  );
};

/**
 * Deep Understanding prompt (WHY questions)
 */
interface DeepUnderstandingPromptProps {
  question: string;
  currentUnderstanding?: string;
  readinessScore?: number;
  textInput: string;
  onTextChange: (text: string) => void;
  onSubmit: (answer: string, problem?: string, goals?: string[]) => void;
  onCancel: () => void;
}

const DeepUnderstandingPrompt: React.FC<DeepUnderstandingPromptProps> = ({
  question,
  currentUnderstanding,
  readinessScore,
  textInput,
  onTextChange,
  onSubmit,
  onCancel,
}) => {
  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="magenta"
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1} flexDirection="row" gap={2}>
        <Text color="magenta" bold>
          🔍 Deep Understanding
        </Text>
        {readinessScore !== undefined && (
          <Text color="gray">
            Readiness: {(readinessScore * 100).toFixed(0)}%
          </Text>
        )}
      </Box>

      {currentUnderstanding && (
        <Box
          marginBottom={1}
          borderStyle="single"
          borderColor="gray"
          paddingX={1}
        >
          <Text color="gray" wrap="wrap">
            Current understanding: {currentUnderstanding}
          </Text>
        </Box>
      )}

      <Box marginBottom={1}>
        <Text color="white" wrap="wrap">
          {question}
        </Text>
      </Box>

      <Box flexDirection="row" gap={1}>
        <Text color="blue">&gt;</Text>
        <TextInput
          value={textInput}
          onChange={onTextChange}
          onSubmit={() => onSubmit(textInput)}
          placeholder="Share your thoughts..."
        />
      </Box>

      <Box marginTop={1}>
        <Text color="gray" dimColor>
          Press Enter to answer • Escape to skip/cancel
        </Text>
      </Box>
    </Box>
  );
};

/**
 * TDD Workflow prompt
 */
interface TDDPromptProps {
  phase: string;
  testRequirements?: string;
  acceptanceCriteria?: string[];
  failingTest?: string;
  refactorOpportunities?: string[];
  onAction: (
    action: "proceed" | "revise" | "cancel",
    feedback?: string,
  ) => void;
}

const TDDPrompt: React.FC<TDDPromptProps> = ({
  phase,
  testRequirements,
  acceptanceCriteria,
  failingTest,
  refactorOpportunities,
  onAction,
}) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  const phaseConfig: Record<
    string,
    { icon: string; color: string; title: string }
  > = {
    tdd_red: {
      icon: "🔴",
      color: "red",
      title: "RED Phase - Write Failing Tests",
    },
    tdd_green: {
      icon: "🟢",
      color: "green",
      title: "GREEN Phase - Make Tests Pass",
    },
    tdd_refactor: {
      icon: "🔵",
      color: "blue",
      title: "REFACTOR Phase - Clean Up",
    },
  };

  const config = phaseConfig[phase] || {
    icon: "⚪",
    color: "white",
    title: phase,
  };

  const items: ActionItem[] = [
    { label: "✅ Proceed - Continue to next step", value: "proceed" },
    { label: "✏️  Revise - Make changes", value: "revise" },
    { label: "❌ Cancel - Stop TDD workflow", value: "cancel" },
  ];

  if (showFeedback) {
    return (
      <Box
        flexDirection="column"
        borderStyle="round"
        borderColor="yellow"
        paddingX={2}
        paddingY={1}
      >
        <Text color="yellow" bold>
          ✏️ TDD Revision
        </Text>
        <Box marginTop={1} flexDirection="row" gap={1}>
          <Text color="blue">&gt;</Text>
          <TextInput
            value={feedback}
            onChange={setFeedback}
            onSubmit={() => onAction("revise", feedback)}
            placeholder="What should change..."
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor={config.color as any}
      paddingX={2}
      paddingY={1}
    >
      <Box marginBottom={1}>
        <Text color={config.color as any} bold>
          {config.icon} {config.title}
        </Text>
      </Box>

      {testRequirements && (
        <Box marginBottom={1}>
          <Text color="white" wrap="wrap">
            📝 {testRequirements}
          </Text>
        </Box>
      )}

      {acceptanceCriteria && acceptanceCriteria.length > 0 && (
        <Box flexDirection="column" marginBottom={1}>
          <Text color="cyan" bold>
            Acceptance Criteria:
          </Text>
          {acceptanceCriteria.map((c, i) => (
            <Text key={i} color="cyan">
              ☐ {c}
            </Text>
          ))}
        </Box>
      )}

      {failingTest && (
        <Box
          marginBottom={1}
          borderStyle="single"
          borderColor="red"
          paddingX={1}
        >
          <Text color="red" wrap="wrap">
            ❌ Failing: {failingTest}
          </Text>
        </Box>
      )}

      {refactorOpportunities && refactorOpportunities.length > 0 && (
        <Box flexDirection="column" marginBottom={1}>
          <Text color="blue" bold>
            Refactoring Opportunities:
          </Text>
          {refactorOpportunities.map((r, i) => (
            <Text key={i} color="blue">
              🔧 {r}
            </Text>
          ))}
        </Box>
      )}

      <SelectInput
        items={items}
        onSelect={(item) => {
          if (item.value === "revise") {
            setShowFeedback(true);
          } else {
            onAction(item.value as "proceed" | "cancel");
          }
        }}
      />
    </Box>
  );
};

export default HITLPrompt;
