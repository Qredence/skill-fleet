// @ts-nocheck
/** @jsxImportSource @opentui/react */
import { TextAttributes } from "@opentui/core";
import { SKILLS_FLEET_THEME } from "../../themes";
import type { WorkflowState, WorkflowStep, StepStatus } from "../../types";

interface WorkflowDashboardProps {
  state: WorkflowState;
}

const STEPS: { id: WorkflowStep; label: string }[] = [
  { id: "understand", label: "Understand" },
  { id: "plan", label: "Plan" },
  { id: "initialize", label: "Initialize" },
  { id: "edit", label: "Edit Content" },
  { id: "package", label: "Package Skill" },
  { id: "validate", label: "Validate" },
];

export function WorkflowDashboard({ state }: WorkflowDashboardProps) {
  const colors = SKILLS_FLEET_THEME;

  const getStatusIcon = (status: StepStatus) => {
    switch (status) {
      case "pending": return "○";
      case "running": return "⠋"; // Animation handled by parent usually, but static char here
      case "completed": return "●";
      case "failed": return "✖";
      default: return "○";
    }
  };

  const getStatusColor = (status: StepStatus) => {
    switch (status) {
      case "pending": return colors.text.dim;
      case "running": return colors.text.accent;
      case "completed": return colors.success;
      case "failed": return colors.error;
      default: return colors.text.dim;
    }
  };

  return (
    <box flexDirection="column" flexGrow={1} padding={1}>
      <box
        style={{
          border: true, // Use standard border
          height: 3, // Simulate header height
          borderColor: colors.border,
          paddingBottom: 0,
          marginBottom: 1,
          flexDirection: "column",
        }}
      >
        <text
          content="SKILL CREATION STATUS"
          style={{ fg: colors.text.secondary, attributes: TextAttributes.BOLD }}
        />
      </box>

      {/* Progress Stats */}
      <box style={{ marginBottom: 1, justifyContent: "space-between" }}>
        <text
          content={`Iteration: ${state.currentIteration}/${state.maxIterations}`}
          style={{ fg: colors.text.primary }}
        />
        {state.qualityScore !== undefined && (
          <text
            content={`Quality: ${state.qualityScore.toFixed(2)}`}
            style={{ fg: colors.text.accent }}
          />
        )}
      </box>

      {/* Steps List */}
      <box flexDirection="column">
        {STEPS.map((step) => {
          const status = state.steps[step.id] || "pending";
          const isActive = state.activeStep === step.id;
          const color = getStatusColor(status);
          const icon = getStatusIcon(status);

          return (
            <box
              key={step.id}
              style={{
                flexDirection: "row",
                height: 1,
                marginBottom: 0,
                backgroundColor: isActive ? colors.bg.hover : "transparent",
              }}
            >
              <text
                content={` ${icon} `}
                style={{ fg: color, attributes: TextAttributes.BOLD }}
              />
              <text
                content={step.label}
                style={{
                  fg: status === "completed" ? colors.text.primary : color,
                  attributes: isActive ? TextAttributes.BOLD : 0,
                }}
              />
            </box>
          );
        })}
      </box>
    </box>
  );
}
