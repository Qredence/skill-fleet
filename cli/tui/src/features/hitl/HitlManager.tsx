import { useState } from "react";
import type { HitlPrompt } from "../../lib/types";

type HitlKind =
  | "clarify"
  | "confirm"
  | "structure_fix"
  | "deep_understanding"
  | "tdd_red"
  | "tdd_green"
  | "tdd_refactor";

type Props = {
  prompt: HitlPrompt;
  focused: boolean;
  onSubmit: (payload: Record<string, unknown>) => void;
};

function HitlConfirm({ prompt, focused, onSubmit }: Props) {
  const [action, setAction] = useState(
    prompt.validation_passed ? "proceed" : "revise",
  );

  const options = [
    { name: "Proceed", description: "Continue", value: "proceed" },
    { name: "Revise", description: "Make changes", value: "revise" },
  ];

  return (
    <box flexDirection="column" gap={1}>
      <text fg="#e5e5e5">{prompt.content || "Please confirm:"}</text>
      <select
        options={options}
        selectedIndex={action === "proceed" ? 0 : 1}
        height={3}
        focused={focused}
        onSelect={(_, opt) => {
          if (opt?.value) {
            onSubmit({ action: opt.value, summary: `Action: ${opt.value}` });
          }
        }}
      />
      <text fg="#737373">Enter to select</text>
    </box>
  );
}

function HitlClarify({ prompt, focused, onSubmit }: Props) {
  const questions = prompt.questions || [];
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string[]>>({});

  const q = questions[index];
  if (!q) return <text>No questions</text>;

  const isMulti = q.allows_multiple ?? false;
  const selectedIds = answers[index] || [];

  const options =
    q.options?.map((o) => ({
      name: o.label,
      description: o.description || "",
      value: o.id,
    })) || [];

  return (
    <box flexDirection="column" gap={1}>
      <text fg="#737373">
        [{index + 1}/{questions.length}]
      </text>
      <text fg="#e5e5e5">{q.text}</text>
      {q.rationale ? <text fg="#737373">{q.rationale}</text> : null}

      <select
        options={options}
        selectedIndex={options.findIndex((o) => o.value === selectedIds[0])}
        height={Math.min(8, options.length)}
        focused={focused}
        onSelect={(_, opt) => {
          if (!opt?.value) return;

          const newAnswers = isMulti
            ? selectedIds.includes(opt.value)
              ? selectedIds.filter((id) => id !== opt.value)
              : [...selectedIds, opt.value]
            : [opt.value];

          setAnswers({ ...answers, [index]: newAnswers });

          if (!isMulti) {
            if (index < questions.length - 1) {
              setIndex(index + 1);
            } else {
              onSubmit({
                answers: answers,
                summary: `Answered ${questions.length} questions`,
              });
            }
          }
        }}
      />

      {isMulti && selectedIds.length > 0 ? (
        <text fg="#22c55e">Selected: {selectedIds.length} items</text>
      ) : null}

      <text fg="#737373">
        {isMulti ? "Enter toggle | Tab submit" : "Enter to select"}
      </text>
    </box>
  );
}

export function HitlManager({ prompt, focused, onSubmit }: Props) {
  const kind = (prompt.type || "confirm") as HitlKind;

  switch (kind) {
    case "confirm":
      return <HitlConfirm prompt={prompt} focused={focused} onSubmit={onSubmit} />;
    case "clarify":
      return <HitlClarify prompt={prompt} focused={focused} onSubmit={onSubmit} />;
    default:
      return (
        <box flexDirection="column" gap={1}>
          <text fg="#e5e5e5">{prompt.content || "Please respond:"}</text>
          <text fg="#737373">Press Tab then Enter to continue</text>
        </box>
      );
  }
}
